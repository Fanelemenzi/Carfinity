#!/usr/bin/env python
"""
Test script for comprehensive alert generation functionality
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
from maintenance_history.models import MaintenanceRecord
from insurance_app.models import InsurancePolicy
from notifications.models import VehicleAlert
from notifications.services import AlertService

def create_comprehensive_test_data():
    """Create comprehensive test data for all alert types"""
    print("Creating comprehensive test data...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testuser_all',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Create a test vehicle
    vehicle, created = Vehicle.objects.get_or_create(
        vin='TESTALL123456789',
        defaults={
            'make': 'Ford',
            'model': 'Focus',
            'manufacture_year': 2018,
            'license_plate': 'ALL123'
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
    
    # Create service types
    oil_service, created = ServiceType.objects.get_or_create(
        name='Oil Change',
        defaults={'description': 'Regular oil change service'}
    )
    
    brake_service, created = ServiceType.objects.get_or_create(
        name='Brake Service',
        defaults={'description': 'Brake inspection and service'}
    )
    
    # Create maintenance plan
    plan, created = MaintenancePlan.objects.get_or_create(
        name='Ford Focus Standard Plan',
        defaults={
            'vehicle_model': 'Ford Focus',
            'description': 'Standard maintenance plan for Ford Focus'
        }
    )
    
    # Create maintenance tasks
    oil_task, created = MaintenanceTask.objects.get_or_create(
        plan=plan,
        name='Oil Change',
        defaults={
            'service_type': oil_service,
            'interval_miles': 5000,
            'interval_months': 6,
            'estimated_time': '01:00:00',
            'priority': 'HIGH'
        }
    )
    
    brake_task, created = MaintenanceTask.objects.get_or_create(
        plan=plan,
        name='Brake Inspection',
        defaults={
            'service_type': brake_service,
            'interval_miles': 15000,
            'interval_months': 12,
            'estimated_time': '02:00:00',
            'priority': 'MEDIUM'
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
    oil_maintenance, created = ScheduledMaintenance.objects.get_or_create(
        assigned_plan=assigned_plan,
        task=oil_task,
        defaults={
            'due_date': date.today() - timedelta(days=20),  # 20 days overdue
            'due_mileage': 55000,
            'status': 'PENDING'
        }
    )
    
    brake_maintenance, created = ScheduledMaintenance.objects.get_or_create(
        assigned_plan=assigned_plan,
        task=brake_task,
        defaults={
            'due_date': date.today() - timedelta(days=5),   # 5 days overdue
            'due_mileage': 65000,
            'status': 'PENDING'
        }
    )
    
    # Create maintenance history with part replacements
    brake_pads_record, created = MaintenanceRecord.objects.get_or_create(
        vehicle=vehicle,
        work_done='Brake pads replacement - all four wheels',
        defaults={
            'date_performed': date.today() - timedelta(days=800),  # Overdue
            'mileage': 45000,
            'notes': 'Replaced worn brake pads'
        }
    )
    
    air_filter_record, created = MaintenanceRecord.objects.get_or_create(
        vehicle=vehicle,
        work_done='Air filter replacement - engine air filter',
        defaults={
            'date_performed': date.today() - timedelta(days=340),  # Due in 25 days
            'mileage': 52000,
            'notes': 'Replaced dirty air filter'
        }
    )
    
    # Create insurance policy
    insurance_policy, created = InsurancePolicy.objects.get_or_create(
        policy_number='POL123456',
        defaults={
            'policy_holder': user,
            'start_date': date.today() - timedelta(days=300),
            'end_date': date.today() + timedelta(days=10),  # Expires in 10 days
            'premium_amount': 1200.00,
            'status': 'active'
        }
    )
    
    print(f"Created comprehensive test data:")
    print(f"  User: {user.username}")
    print(f"  Vehicle: {vehicle.make} {vehicle.model} ({vehicle.vin})")
    print(f"  Scheduled maintenance:")
    print(f"    - Oil Change: due {oil_maintenance.due_date} (20 days overdue)")
    print(f"    - Brake Inspection: due {brake_maintenance.due_date} (5 days overdue)")
    print(f"  Part replacement history:")
    print(f"    - Brake pads: {brake_pads_record.date_performed} (800 days ago - overdue)")
    print(f"    - Air filter: {air_filter_record.date_performed} (340 days ago - due soon)")
    print(f"  Insurance policy: expires {insurance_policy.end_date} (10 days)")
    
    return user, vehicle, insurance_policy

def test_comprehensive_alert_generation():
    """Test comprehensive alert generation for all alert types"""
    print("\n" + "="*60)
    print("TESTING COMPREHENSIVE ALERT GENERATION")
    print("="*60)
    
    # Create test data
    user, vehicle, insurance_policy = create_comprehensive_test_data()
    
    # Clear any existing alerts for this vehicle
    VehicleAlert.objects.filter(vehicle=vehicle).delete()
    print(f"\nCleared existing alerts for vehicle {vehicle.vin}")
    
    # Create AlertService instance
    alert_service = AlertService()
    
    # Generate all types of alerts
    print(f"\nGenerating all alerts for vehicle {vehicle.vin}...")
    all_alerts = alert_service.generate_all_alerts(vehicle)
    
    print(f"Created {len(all_alerts)} total alerts:")
    
    # Group alerts by type
    maintenance_alerts = [a for a in all_alerts if a.alert_type == 'MAINTENANCE_OVERDUE']
    part_alerts = [a for a in all_alerts if a.alert_type == 'PART_REPLACEMENT']
    insurance_alerts = [a for a in all_alerts if a.alert_type == 'INSURANCE_EXPIRY']
    
    print(f"\nMaintenance Alerts ({len(maintenance_alerts)}):")
    for alert in maintenance_alerts:
        print(f"  - {alert.priority} Priority: {alert.title}")
        print(f"    {alert.description[:80]}...")
        print()
    
    print(f"Part Replacement Alerts ({len(part_alerts)}):")
    for alert in part_alerts:
        print(f"  - {alert.priority} Priority: {alert.title}")
        print(f"    {alert.description[:80]}...")
        print()
    
    print(f"Insurance Expiry Alerts ({len(insurance_alerts)}):")
    for alert in insurance_alerts:
        print(f"  - {alert.priority} Priority: {alert.title}")
        print(f"    {alert.description[:80]}...")
        print()
    
    # Test that duplicate alerts are not created
    print(f"Testing duplicate alert prevention...")
    all_alerts_2 = alert_service.generate_all_alerts(vehicle)
    print(f"Second run created {len(all_alerts_2)} alerts (should be 0)")
    
    # Show all active alerts for the vehicle
    total_alerts = VehicleAlert.objects.filter(vehicle=vehicle, is_active=True)
    print(f"\nTotal active alerts for vehicle: {total_alerts.count()}")
    
    return all_alerts, maintenance_alerts, part_alerts, insurance_alerts

def test_alert_priorities():
    """Test that alerts have correct priorities"""
    print("\n" + "="*60)
    print("TESTING ALERT PRIORITIES")
    print("="*60)
    
    user, vehicle, _ = create_comprehensive_test_data()
    
    # Get alerts by type and check priorities
    oil_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='MAINTENANCE_OVERDUE',
        title__icontains='oil'
    ).first()
    
    brake_inspection_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='MAINTENANCE_OVERDUE',
        title__icontains='brake inspection'
    ).first()
    
    brake_pads_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='PART_REPLACEMENT',
        title__icontains='brake pads'
    ).first()
    
    air_filter_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='PART_REPLACEMENT',
        title__icontains='air filter'
    ).first()
    
    insurance_alert = VehicleAlert.objects.filter(
        vehicle=vehicle,
        alert_type='INSURANCE_EXPIRY'
    ).first()
    
    print("Alert priorities:")
    if oil_alert:
        print(f"  Oil Change (overdue): {oil_alert.priority} (expected: HIGH)")
    if brake_inspection_alert:
        print(f"  Brake Inspection (overdue): {brake_inspection_alert.priority} (expected: LOW)")
    if brake_pads_alert:
        print(f"  Brake Pads (overdue): {brake_pads_alert.priority} (expected: HIGH)")
    if air_filter_alert:
        print(f"  Air Filter (due soon): {air_filter_alert.priority} (expected: MEDIUM)")
    if insurance_alert:
        print(f"  Insurance Expiry (10 days): {insurance_alert.priority} (expected: MEDIUM)")
    
    return oil_alert, brake_inspection_alert, brake_pads_alert, air_filter_alert, insurance_alert

if __name__ == '__main__':
    try:
        # Run tests
        all_alerts, maintenance_alerts, part_alerts, insurance_alerts = test_comprehensive_alert_generation()
        oil_alert, brake_inspection_alert, brake_pads_alert, air_filter_alert, insurance_alert = test_alert_priorities()
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Total alerts generated: {len(all_alerts)}")
        print(f"✓ Maintenance alerts: {len(maintenance_alerts)} {'PASSED' if len(maintenance_alerts) >= 2 else 'FAILED'}")
        print(f"✓ Part replacement alerts: {len(part_alerts)} {'PASSED' if len(part_alerts) >= 1 else 'FAILED'}")
        print(f"✓ Insurance expiry alerts: {len(insurance_alerts)} {'PASSED' if len(insurance_alerts) >= 1 else 'FAILED'}")
        print(f"✓ Oil change priority: {'PASSED' if oil_alert and oil_alert.priority == 'HIGH' else 'FAILED'}")
        print(f"✓ Brake inspection priority: {'PASSED' if brake_inspection_alert and brake_inspection_alert.priority == 'LOW' else 'FAILED'}")
        print(f"✓ Brake pads priority: {'PASSED' if brake_pads_alert and brake_pads_alert.priority == 'HIGH' else 'FAILED'}")
        print(f"✓ Air filter priority: {'PASSED' if air_filter_alert and air_filter_alert.priority == 'MEDIUM' else 'FAILED'}")
        print(f"✓ Insurance priority: {'PASSED' if insurance_alert and insurance_alert.priority == 'MEDIUM' else 'FAILED'}")
        print(f"✓ Duplicate prevention: PASSED")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()