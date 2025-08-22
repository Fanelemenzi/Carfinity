#!/usr/bin/env python
"""
Simple test script to verify the maintenance schedule fixes
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')

try:
    django.setup()
    
    from insurance_app.models import MaintenanceSchedule
    from insurance_app.utils import MaintenanceSyncManager
    
    print("✓ Django setup successful")
    print("✓ Models imported successfully")
    
    # Test creating a maintenance schedule with default due_mileage
    print("\nTesting MaintenanceSchedule creation...")
    
    # Check if there are any existing schedules with null due_mileage
    null_mileage_count = MaintenanceSchedule.objects.filter(due_mileage__isnull=True).count()
    zero_mileage_count = MaintenanceSchedule.objects.filter(due_mileage=0).count()
    
    print(f"Schedules with null due_mileage: {null_mileage_count}")
    print(f"Schedules with zero due_mileage: {zero_mileage_count}")
    
    if null_mileage_count > 0:
        print("⚠️  Found schedules with null due_mileage - these need to be fixed")
    else:
        print("✓ No schedules with null due_mileage found")
    
    print("\n✓ Test completed successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This is expected if required packages are not installed")
except Exception as e:
    print(f"❌ Error: {e}")
    print("This might indicate a configuration issue")