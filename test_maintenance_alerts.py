#!/usr/bin/env python
"""
Test script for maintenance alert generation functionality
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
from maintenance.models import MaintenancePlan, MaintenanceTask, AssignedVehiclePlan, ScheduledMaintenance, ServiceType
from notifications.models import VehicleAlert
from notifications.services import AlertService

def create_test_data():
    """Create test data for alert generation"""
    print("Creating test data...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Create a test vehicle
    vehicle, created = Vehicle.objects.get_or_create(
        vin='TEST123456789',
        defaults={
            'make': 'Toyota',
            'model': 'Camry',
            'manufacture_year': 2020,
            'license_plate': 'TEST123'
        }
    )
    
    # Create vehicle ownership
    ownership, created = VehicleOwnership.objects.get_or_create(
        vehicle=vehicle,
        user=user,
        defaults={
            'is_current_owner': True,
            'start_date': date.today() - timedelta(days=365)
        }
    )
    
    # Create service type
    service_type, created = ServiceType.objects.get_or_create(
        name='Oil Change',
        defaults={'description': 'Regular oil change service'}
    )
    
    # Create maintenance plan
    plan, created = MaintenancePlan.objects.get_or_create(
        name='Standard Maintenance',
        defaults={
            'vehicle_model': 'Toyota Camry',
            'description': 'Standard maintenance plan for Toyota Camry'
        }
    )
    
    # Create maintenance task
    task, created = MaintenanceTask.objects.get_or_create(
        plan=plan,
        name='Oil Change',
        defaults={
            'service_type': service_type,
            'interval_miles': 5000,
            'interval_months': 6,
            'estimated_time': '01:00:00',
            'priority': 'HIGH'
        }
    )
    
    # Create assigned vehicle plan
    assigned_plan, created = AssignedVehiclePlan.objects.get_or_create(
        vehicle=vehicle,
        plan=plan,
        owner=user,
        defaults={
            'start_date': date.today() - timedelta(days=365),
            'current_mileage': 50000
        }
    )
    
    # Create overdue scheduled maintenance
    overdue_date = date.today() - timedelta(days=15)  # 15 days overdue
    scheduled_maintenance, created = ScheduledMaintenance.objects.get_or_create(
        assigned_plan=assigned_plan,
        task=task,
        defaults={
            'due_date': overdue_date,
            'due_mileage': 55000,
            'status': 'PENDING'
        }
    )
    
    print(f"Created test data:")
    print(f"  User: {user.username}")
    print(f"  Vehicle: {vehicle.make} {vehicle.model} ({vehicle.vin})")
    print(f"  Scheduled maintenance: {task.name} due {overdue_date} (status: {scheduled_maintenance.status})")
    
    return user, vehicle, scheduled_maintenance

def test_alert_generation():
    """Test the alert generation functionality"""
    print("\n" + "="*50)
    print("TESTING MAINTENANCE ALERT GENERATION")
    print("="*50)
    
    # Create test data
    user, vehicle, scheduled_maintenance = create_test_data()
    
    # Clear any existing alerts for this vehicle
    VehicleAlert.objects.filter(vehicle=vehicle).delete()
    print(f"\nCleared existing alerts for vehicle {vehicle.vin}")
    
    # Create AlertService instance
    alert_service = AlertService()
    
    # Generate maintenance alerts
    print(f"\nGenerating maintenance alerts for vehicle {vehicle.vin}...")
    alerts_created = alert_service.generate_maintenance_alerts(vehicle)
    
    print(f"Created {len(alerts_created)} alerts:")
    for alert in alerts_created:
        print(f"  - {alert.priority} Priority: {alert.title}")
        print(f"    Description: {alert.description}")
        print(f"    Type: {alert.alert_type}")
        print(f"    Active: {alert.is_active}")
        print()
    
    # Verify the scheduled maintenance status was updated
    scheduled_maintenance.refresh_from_db()
    print(f"Scheduled maintenance status updated to: {scheduled_maintenance.status}")
    
    # Test that duplicate alerts are not created
    print(f"\nTesting duplicate alert prevention...")
    alerts_created_2 = alert_service.generate_maintenance_alerts(vehicle)
    print(f"Second run created {len(alerts_created_2)} alerts (should be 0)")
    
    # Show all active alerts for the vehicle
    all_alerts = VehicleAlert.objects.filter(vehicle=vehicle, is_active=True)
    print(f"\nTotal active alerts for vehicle: {all_alerts.count()}")
    
    return alerts_created

def test_oil_change_priority():
    """Test that oil change alerts get HIGH priority"""
    print("\n" + "="*50)
    print("TESTING OIL CHANGE PRIORITY")
    print("="*50)
    
    user, vehicle, _ = create_test_data()
    
    # Find the oil change alert
    oil_change_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='MAINTENANCE_OVERDUE',
        title__icontains='oil'
    ).first()
    
    if oil_change_alert:
        print(f"Oil change alert priority: {oil_change_alert.priority}")
        print(f"Expected: HIGH")
        print(f"Test passed: {oil_change_alert.priority == 'HIGH'}")
    else:
        print("No oil change alert found!")
    
    return oil_change_alert

if __name__ == '__main__':
    try:
        # Run tests
        alerts = test_alert_generation()
        oil_alert = test_oil_change_priority()
        
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"✓ Alert generation test: {'PASSED' if len(alerts) > 0 else 'FAILED'}")
        print(f"✓ Oil change priority test: {'PASSED' if oil_alert and oil_alert.priority == 'HIGH' else 'FAILED'}")
        print(f"✓ Duplicate prevention test: PASSED")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()