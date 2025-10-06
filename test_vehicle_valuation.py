#!/usr/bin/env python
"""
Test script to verify VehicleValuation model
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from vehicles.models import Vehicle, VehicleValuation

def test_vehicle_valuation():
    """Test the VehicleValuation model"""
    print("Testing VehicleValuation model...")
    
    # Get or create a test vehicle
    vehicle, created = Vehicle.objects.get_or_create(
        vin='TEST123456789',
        defaults={
            'make': 'Toyota',
            'model': 'Camry',
            'manufacture_year': 2020
        }
    )
    
    # Create or update valuation
    valuation, created = VehicleValuation.objects.get_or_create(
        vehicle=vehicle,
        defaults={
            'estimated_value': Decimal('25000.00'),
            'condition_rating': 'good',
            'valuation_source': 'kbb',
            'mileage_at_valuation': 45000,
            'valuation_notes': 'Test valuation for dashboard implementation'
        }
    )
    
    if created:
        print(f"Created new valuation: {valuation}")
    else:
        print(f"Using existing valuation: {valuation}")
    
    # Test properties
    print(f"Formatted value: {valuation.formatted_value}")
    print(f"Is recent: {valuation.is_recent}")
    print(f"Condition: {valuation.get_condition_rating_display()}")
    print(f"Source: {valuation.get_valuation_source_display()}")
    
    # Test relationship
    print(f"Vehicle has valuation: {hasattr(vehicle, 'valuation')}")
    if hasattr(vehicle, 'valuation'):
        print(f"Vehicle valuation value: {vehicle.valuation.formatted_value}")
    
    print("\n✅ VehicleValuation model test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_vehicle_valuation()
        print("\n🎉 Task 2 implementation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error testing VehicleValuation: {e}")
        sys.exit(1)