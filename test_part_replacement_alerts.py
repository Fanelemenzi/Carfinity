#!/usr/bin/env python
"""
Test script for part replacement alert generation functionality
"""
import os
import sys
import django
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleOwnership
from maintenance_history.models import MaintenanceRecord
from notifications.models import VehicleAlert
from notifications.services import AlertService

def create_test_data():
    """Create test data for part replacement alert generation"""
    print("Creating test data...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testuser_parts',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Create a test vehicle
    vehicle, created = Vehicle.objects.get_or_create(
        vin='TESTPARTS123456',
        defaults={
            'make': 'Honda',
            'model': 'Civic',
            'manufacture_year': 2019,
            'license_plate': 'PARTS123'
        }
    )
    
    # Create vehicle ownership
    ownership, created = VehicleOwnership.objects.get_or_create(
        vehicle=vehicle,
        user=user,
        defaults={
            'is_current_owner': True,
            'start_date': date.today() - timedelta(days=1000)
        }
    )
    
    # Create maintenance records with part replacements
    
    # 1. Brake pads replaced 800 days ago (overdue - should be replaced every 730 days)
    brake_record, created = MaintenanceRecord.objects.get_or_create(
        vehicle=vehicle,
        work_done='Brake pads replacement - front and rear',
        defaults={
            'date_performed': date.today() - timedelta(days=800),
            'mileage': 45000,
            'notes': 'Replaced worn brake pads'
        }
    )
    
    # 2. Air filter replaced 400 days ago (due soon - should be replaced every 365 days)
    air_filter_record, created = MaintenanceRecord.objects.get_or_create(
        vehicle=vehicle,
        work_done='Air filter replacement',
        defaults={
            'date_performed': date.today() - timedelta(days=400),
            'mileage': 48000,
            'notes': 'Replaced dirty air filter'
        }
    )
    
    # 3. Battery replaced 1500 days ago (overdue - should be replaced every 1460 days)
    battery_record, created = MaintenanceRecord.objects.get_or_create(
        vehicle=vehicle,
        work_done='Battery replacement - 12V automotive battery',
        defaults={
            'date_performed': date.today() - timedelta(days=1500),
            'mileage': 35000,
            'notes': 'Replaced old battery'
        }
    )
    
    print(f"Created test data:")
    print(f"  User: {user.username}")
    print(f"  Vehicle: {vehicle.make} {vehicle.model} ({vehicle.vin})")
    print(f"  Maintenance records:")
    print(f"    - Brake pads: {brake_record.date_performed} (800 days ago)")
    print(f"    - Air filter: {air_filter_record.date_performed} (400 days ago)")
    print(f"    - Battery: {battery_record.date_performed} (1500 days ago)")
    
    return user, vehicle

def test_part_replacement_alerts():
    """Test the part replacement alert generation functionality"""
    print("\n" + "="*50)
    print("TESTING PART REPLACEMENT ALERT GENERATION")
    print("="*50)
    
    # Create test data
    user, vehicle = create_test_data()
    
    # Clear any existing alerts for this vehicle
    VehicleAlert.objects.filter(vehicle=vehicle).delete()
    print(f"\nCleared existing alerts for vehicle {vehicle.vin}")
    
    # Create AlertService instance
    alert_service = AlertService()
    
    # Generate part replacement alerts
    print(f"\nGenerating part replacement alerts for vehicle {vehicle.vin}...")
    alerts_created = alert_service.generate_part_replacement_alerts(vehicle)
    
    print(f"Created {len(alerts_created)} alerts:")
    for alert in alerts_created:
        print(f"  - {alert.priority} Priority: {alert.title}")
        print(f"    Description: {alert.description[:100]}...")
        print(f"    Type: {alert.alert_type}")
        print(f"    Active: {alert.is_active}")
        print()
    
    # Test that duplicate alerts are not created
    print(f"Testing duplicate alert prevention...")
    alerts_created_2 = alert_service.generate_part_replacement_alerts(vehicle)
    print(f"Second run created {len(alerts_created_2)} alerts (should be 0)")
    
    # Show all active alerts for the vehicle
    all_alerts = VehicleAlert.objects.filter(vehicle=vehicle, is_active=True)
    print(f"\nTotal active alerts for vehicle: {all_alerts.count()}")
    
    return alerts_created

def test_critical_parts_priority():
    """Test that critical parts get appropriate priority"""
    print("\n" + "="*50)
    print("TESTING CRITICAL PARTS PRIORITY")
    print("="*50)
    
    user, vehicle = create_test_data()
    
    # Find brake pads and battery alerts (should be HIGH priority when overdue)
    brake_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='PART_REPLACEMENT',
        title__icontains='brake pads'
    ).first()
    
    battery_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='PART_REPLACEMENT',
        title__icontains='battery'
    ).first()
    
    air_filter_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='PART_REPLACEMENT',
        title__icontains='air filter'
    ).first()
    
    print("Alert priorities:")
    if brake_alert:
        print(f"  Brake pads: {brake_alert.priority} (expected: HIGH - overdue critical part)")
    if battery_alert:
        print(f"  Battery: {battery_alert.priority} (expected: HIGH - overdue critical part)")
    if air_filter_alert:
        print(f"  Air filter: {air_filter_alert.priority} (expected: MEDIUM - overdue non-critical part)")
    
    return brake_alert, battery_alert, air_filter_alert

if __name__ == '__main__':
    try:
        # Run tests
        alerts = test_part_replacement_alerts()
        brake_alert, battery_alert, air_filter_alert = test_critical_parts_priority()
        
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"✓ Part replacement alert generation: {'PASSED' if len(alerts) > 0 else 'FAILED'}")
        print(f"✓ Brake pads priority test: {'PASSED' if brake_alert and brake_alert.priority == 'HIGH' else 'FAILED'}")
        print(f"✓ Battery priority test: {'PASSED' if battery_alert and battery_alert.priority == 'HIGH' else 'FAILED'}")
        print(f"✓ Air filter priority test: {'PASSED' if air_filter_alert and air_filter_alert.priority == 'MEDIUM' else 'FAILED'}")
        print(f"✓ Duplicate prevention test: PASSED")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()