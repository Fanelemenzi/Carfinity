#!/usr/bin/env python
"""
Test script to verify Vehicle model property methods
"""
import os
import sys
import django
from datetime import datetime, date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from vehicles.models import Vehicle
from maintenance_history.models import MaintenanceRecord, Inspection
from django.contrib.auth.models import User

def test_vehicle_properties():
    """Test the new Vehicle model property methods"""
    print("Testing Vehicle model property methods...")
    
    # Get or create a test vehicle
    vehicle, created = Vehicle.objects.get_or_create(
        vin='TEST123456789',
        defaults={
            'make': 'Toyota',
            'model': 'Camry',
            'manufacture_year': 2020
        }
    )
    
    if created:
        print(f"Created test vehicle: {vehicle.vin}")
    else:
        print(f"Using existing vehicle: {vehicle.vin}")
    
    # Test current_mileage property
    print(f"\nCurrent mileage: {vehicle.current_mileage}")
    print(f"Mileage last updated: {vehicle.mileage_last_updated}")
    
    # Test health_score property
    print(f"Health score: {vehicle.health_score}")
    
    # Test health_status property
    print(f"Health status: {vehicle.health_status}")
    
    # Test last_inspection_date property
    print(f"Last inspection date: {vehicle.last_inspection_date}")
    
    print("\n✅ All property methods executed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_vehicle_properties()
        print("\n🎉 Task 1 implementation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error testing properties: {e}")
        sys.exit(1)