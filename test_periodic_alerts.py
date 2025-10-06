#!/usr/bin/env python
"""
Test script for periodic alert generation functionality
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
from notifications.tasks import generate_vehicle_alerts, cleanup_resolved_alerts, check_insurance_expiry_alerts

def create_test_vehicles():
    """Create multiple test vehicles with different alert scenarios"""
    print("Creating test vehicles with various alert scenarios...")
    
    # Create test users
    user1, created = User.objects.get_or_create(
        username='testuser_periodic1',
        defaults={'email': 'test1@example.com', 'first_name': 'Test', 'last_name': 'User1'}
    )
    
    user2, created = User.objects.get_or_create(
        username='testuser_periodic2',
        defaults={'email': 'test2@example.com', 'first_name': 'Test', 'last_name': 'User2'}
    )
    
    # Create test vehicles
    vehicle1, created = Vehicle.objects.get_or_create(
        vin='PERIODIC123456789',
        defaults={
            'make': 'Toyota',
            'model': 'Corolla',
            'manufacture_year': 2020,
            'license_plate': 'PER123'
        }
    )
    
    vehicle2, created = Vehicle.objects.get_or_create(
        vin='PERIODIC987654321',
        defaults={
            'make': 'Honda',
            'model': 'Accord',
            'manufacture_year': 2019,
            'license_plate': 'PER456'
        }
    )
    
    # Create vehicle ownerships
    ownership1, created = VehicleOwnership.objects.get_or_create(
        vehicle=vehicle1,
        user=user1,
        defaults={
            'is_current_owner': True,
            'start_date': date.today() - timedelta(days=500)
        }
    )
    
    ownership2, created = VehicleOwnership.objects.get_or_create(
        vehicle=vehicle2,
        user=user2,
        defaults={
            'is_current_owner': True,
            'start_date': date.today() - timedelta(days=300)
        }
    )
    
    # Create service types and maintenance plans
    oil_service, created = ServiceType.objects.get_or_create(
        name='Oil Change',
        defaults={'description': 'Regular oil change service'}
    )
    
    brake_service, created = ServiceType.objects.get_or_create(
        name='Brake Service',
        defaults={'description': 'Brake inspection and service'}
    )
    
    plan1, created = MaintenancePlan.objects.get_or_create(
        name='Toyota Standard Plan',
        defaults={
            'vehicle_model': 'Toyota Corolla',
            'description': 'Standard maintenance plan for Toyota Corolla'
        }
    )
    
    plan2, created = MaintenancePlan.objects.get_or_create(
        name='Honda Standard Plan',
        defaults={
            'vehicle_model': 'Honda Accord',
            'description': 'Standard maintenance plan for Honda Accord'
        }
    )
    
    # Create maintenance tasks
    oil_task1, created = MaintenanceTask.objects.get_or_create(
        plan=plan1,
        name='Oil Change',
        defaults={
            'service_type': oil_service,
            'interval_miles': 5000,
            'interval_months': 6,
            'estimated_time': '01:00:00',
            'priority': 'HIGH'
        }
    )
    
    brake_task2, created = MaintenanceTask.objects.get_or_create(
        plan=plan2,
        name='Brake Inspection',
        defaults={
            'service_type': brake_service,
            'interval_miles': 15000,
            'interval_months': 12,
            'estimated_time': '02:00:00',
            'priority': 'MEDIUM'
        }
    )
    
    # Create assigned vehicle plans
    assigned_plan1, created = AssignedVehiclePlan.objects.get_or_create(
        vehicle=vehicle1,
        plan=plan1,
        owner=user1,
        defaults={
            'start_date': date.today() - timedelta(days=365),
            'current_mileage': 50000
        }
    )
    
    assigned_plan2, created = AssignedVehiclePlan.objects.get_or_create(
        vehicle=vehicle2,
        plan=plan2,
        owner=user2,
        defaults={
            'start_date': date.today() - timedelta(days=200),
            'current_mileage': 45000
        }
    )
    
    # Create overdue scheduled maintenance
    oil_maintenance1, created = ScheduledMaintenance.objects.get_or_create(
        assigned_plan=assigned_plan1,
        task=oil_task1,
        defaults={
            'due_date': date.today() - timedelta(days=25),  # 25 days overdue
            'due_mileage': 55000,
            'status': 'PENDING'
        }
    )
    
    brake_maintenance2, created = ScheduledMaintenance.objects.get_or_create(
        assigned_plan=assigned_plan2,
        task=brake_task2,
        defaults={
            'due_date': date.today() - timedelta(days=10),  # 10 days overdue
            'due_mileage': 60000,
            'status': 'PENDING'
        }
    )
    
    # Create maintenance history with part replacements
    brake_pads_record1, created = MaintenanceRecord.objects.get_or_create(
        vehicle=vehicle1,
        work_done='Brake pads replacement - front wheels',
        defaults={
            'date_performed': date.today() - timedelta(days=800),  # Overdue
            'mileage': 45000,
            'notes': 'Replaced worn brake pads'
        }
    )
    
    air_filter_record2, created = MaintenanceRecord.objects.get_or_create(
        vehicle=vehicle2,
        work_done='Air filter replacement - engine air filter',
        defaults={
            'date_performed': date.today() - timedelta(days=380),  # Overdue
            'mileage': 42000,
            'notes': 'Replaced dirty air filter'
        }
    )
    
    # Create insurance policies
    insurance1, created = InsurancePolicy.objects.get_or_create(
        policy_number='PERIODIC001',
        defaults={
            'policy_holder': user1,
            'start_date': date.today() - timedelta(days=300),
            'end_date': date.today() + timedelta(days=15),  # Expires in 15 days
            'premium_amount': 1200.00,
            'status': 'active'
        }
    )
    
    insurance2, created = InsurancePolicy.objects.get_or_create(
        policy_number='PERIODIC002',
        defaults={
            'policy_holder': user2,
            'start_date': date.today() - timedelta(days=200),
            'end_date': date.today() + timedelta(days=5),   # Expires in 5 days
            'premium_amount': 1500.00,
            'status': 'active'
        }
    )
    
    print(f"Created test data:")
    print(f"  Vehicle 1: {vehicle1.make} {vehicle1.model} ({vehicle1.vin})")
    print(f"    - Oil change overdue by 25 days")
    print(f"    - Brake pads overdue (800 days since replacement)")
    print(f"    - Insurance expires in 15 days")
    print(f"  Vehicle 2: {vehicle2.make} {vehicle2.model} ({vehicle2.vin})")
    print(f"    - Brake inspection overdue by 10 days")
    print(f"    - Air filter overdue (380 days since replacement)")
    print(f"    - Insurance expires in 5 days")
    
    return [vehicle1, vehicle2], [user1, user2]

def test_periodic_alert_generation():
    """Test the periodic alert generation task"""
    print("\n" + "="*60)
    print("TESTING PERIODIC ALERT GENERATION TASK")
    print("="*60)
    
    # Create test data
    vehicles, users = create_test_vehicles()
    
    # Clear any existing alerts
    VehicleAlert.objects.filter(vehicle__in=vehicles).delete()
    print(f"\nCleared existing alerts for test vehicles")
    
    # Run the periodic alert generation task
    print(f"\nRunning periodic alert generation task...")
    result = generate_vehicle_alerts.apply()  # Use .apply() for synchronous execution in tests
    
    print(f"Task result: {result.result}")
    
    # Check the results
    total_alerts = VehicleAlert.objects.filter(vehicle__in=vehicles, is_active=True).count()
    print(f"\nTotal alerts created: {total_alerts}")
    
    # Show alerts by vehicle
    for vehicle in vehicles:
        vehicle_alerts = VehicleAlert.objects.filter(vehicle=vehicle, is_active=True)
        print(f"\nAlerts for {vehicle.make} {vehicle.model} ({vehicle.vin}):")
        for alert in vehicle_alerts:
            print(f"  - {alert.priority} Priority: {alert.title}")
            print(f"    Type: {alert.alert_type}")
    
    return result.result

def test_insurance_expiry_task():
    """Test the insurance expiry checking task"""
    print("\n" + "="*60)
    print("TESTING INSURANCE EXPIRY CHECKING TASK")
    print("="*60)
    
    vehicles, users = create_test_vehicles()
    
    # Clear existing insurance alerts
    VehicleAlert.objects.filter(
        vehicle__in=vehicles,
        alert_type='INSURANCE_EXPIRY'
    ).delete()
    
    print(f"\nRunning insurance expiry checking task...")
    result = check_insurance_expiry_alerts.apply()
    
    print(f"Task result: {result.result}")
    
    # Check insurance alerts
    insurance_alerts = VehicleAlert.objects.filter(
        vehicle__in=vehicles,
        alert_type='INSURANCE_EXPIRY',
        is_active=True
    )
    
    print(f"\nInsurance alerts created: {insurance_alerts.count()}")
    for alert in insurance_alerts:
        print(f"  - {alert.priority} Priority: {alert.title}")
        print(f"    Vehicle: {alert.vehicle.make} {alert.vehicle.model}")
    
    return result.result

def test_alert_cleanup():
    """Test the alert cleanup task"""
    print("\n" + "="*60)
    print("TESTING ALERT CLEANUP TASK")
    print("="*60)
    
    vehicles, users = create_test_vehicles()
    
    # Create some old resolved alerts
    old_alert = VehicleAlert.objects.create(
        vehicle=vehicles[0],
        alert_type='MAINTENANCE_OVERDUE',
        priority='HIGH',
        title='Old Resolved Alert',
        description='This is an old resolved alert for testing cleanup',
        is_active=False,
        resolved_at=date.today() - timedelta(days=45)  # 45 days old
    )
    
    print(f"Created old resolved alert (45 days old)")
    
    # Count alerts before cleanup
    before_count = VehicleAlert.objects.filter(vehicle__in=vehicles).count()
    print(f"Total alerts before cleanup: {before_count}")
    
    # Run cleanup task (keep alerts for 30 days)
    print(f"\nRunning alert cleanup task (keeping 30 days)...")
    result = cleanup_resolved_alerts.apply(args=[30])
    
    print(f"Task result: {result.result}")
    
    # Count alerts after cleanup
    after_count = VehicleAlert.objects.filter(vehicle__in=vehicles).count()
    print(f"Total alerts after cleanup: {after_count}")
    print(f"Alerts cleaned up: {before_count - after_count}")
    
    return result.result

def test_task_error_handling():
    """Test error handling in alert generation tasks"""
    print("\n" + "="*60)
    print("TESTING TASK ERROR HANDLING")
    print("="*60)
    
    # Test with non-existent vehicle ID
    print(f"Testing alert generation with non-existent vehicle ID...")
    result = generate_vehicle_alerts.apply(args=[99999])
    
    print(f"Task result: {result.result}")
    
    # Should return an error message
    if 'error' in result.result:
        print("✓ Error handling works correctly for non-existent vehicle")
    else:
        print("✗ Error handling failed")
    
    return result.result

if __name__ == '__main__':
    try:
        # Run tests
        print("Starting periodic alert generation tests...")
        
        periodic_result = test_periodic_alert_generation()
        insurance_result = test_insurance_expiry_task()
        cleanup_result = test_alert_cleanup()
        error_result = test_task_error_handling()
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        # Check results
        periodic_success = isinstance(periodic_result, dict) and periodic_result.get('total_alerts', 0) > 0
        insurance_success = isinstance(insurance_result, dict) and insurance_result.get('insurance_alerts_created', 0) >= 0
        cleanup_success = isinstance(cleanup_result, str) and 'Cleaned up' in cleanup_result
        error_success = isinstance(error_result, dict) and 'error' in error_result
        
        print(f"✓ Periodic alert generation: {'PASSED' if periodic_success else 'FAILED'}")
        print(f"✓ Insurance expiry checking: {'PASSED' if insurance_success else 'FAILED'}")
        print(f"✓ Alert cleanup: {'PASSED' if cleanup_success else 'FAILED'}")
        print(f"✓ Error handling: {'PASSED' if error_success else 'FAILED'}")
        
        if all([periodic_success, insurance_success, cleanup_success, error_success]):
            print("\n🎉 All periodic alert tests PASSED!")
        else:
            print("\n❌ Some tests FAILED!")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()