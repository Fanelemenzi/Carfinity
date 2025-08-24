#!/usr/bin/env python
"""
Test script to demonstrate the inspection workflow functionality
"""

import os
import sys
import django
from datetime import date, datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from maintenance_history.models import Inspection, Inspections
from maintenance_history.utils import calculate_vehicle_health_index, generate_inspection_number
from vehicles.models import Vehicle
from django.contrib.auth.models import User

def test_inspection_workflow():
    """Test the complete inspection workflow"""
    
    print("=== Testing Inspection Workflow ===\n")
    
    # Step 1: Create a test vehicle (if needed)
    try:
        vehicle = Vehicle.objects.first()
        if not vehicle:
            print("No vehicles found. Please create a vehicle first.")
            return
        print(f"✓ Using vehicle: {vehicle.vin}")
    except Exception as e:
        print(f"✗ Error getting vehicle: {e}")
        return
    
    # Step 2: Create a test user (technician)
    try:
        technician = User.objects.first()
        if not technician:
            print("No users found. Please create a user first.")
            return
        print(f"✓ Using technician: {technician.username}")
    except Exception as e:
        print(f"✗ Error getting user: {e}")
        return
    
    # Step 3: Create basic inspection record (simulating StartInspectionWorkflowView)
    try:
        inspection = Inspection.objects.create(
            vehicle=vehicle,
            inspection_number=generate_inspection_number(),
            year=2024,
            inspection_result='FAI',  # Default, will be updated
            vehicle_health_index='Pending Assessment',
            inspection_date=date.today()
        )
        print(f"✓ Created inspection record: {inspection.inspection_number}")
    except Exception as e:
        print(f"✗ Error creating inspection: {e}")
        return
    
    # Step 4: Create inspection form (simulating technician filling out form)
    try:
        inspection_form = Inspections.objects.create(
            inspection=inspection,
            technician=technician,
            inspection_date=datetime.now(),
            mileage_at_inspection=50000,
            
            # Sample inspection results - mix of pass/fail to test calculation
            # Critical systems - mostly good
            engine_oil_level='pass',
            brake_pads='pass',
            brake_discs='pass',
            brake_fluid='pass',
            tire_tread_depth='minor',  # Minor issue
            tire_pressure='pass',
            steering_response='pass',
            seat_belts='pass',
            headlights='pass',
            brake_lights='pass',
            
            # Some other systems with issues
            air_filter='minor',
            cabin_air_filter='fail',  # Minor system failure
            battery_voltage='major',  # Major issue
            alternator_output='pass',
            transmission_fluid='pass',
            
            # Safety systems
            airbags='pass',
            horn_function='pass',
            first_aid_kit='minor',
            
            # Lighting
            turn_signals='pass',
            interior_lights='pass',
            windshield='pass',
            wiper_blades='minor',
            
            # HVAC
            air_conditioning='pass',
            ventilation='pass',
            
            # Technology
            infotainment_system='pass',
            rear_view_camera='na',  # Not applicable
            
            # Notes
            overall_notes='Test inspection with mixed results',
            recommendations='Replace cabin air filter, check battery system',
            
            # Mark as completed to trigger calculation
            is_completed=True
        )
        print(f"✓ Created inspection form with {inspection_form.total_points_checked} points checked")
        print(f"✓ Completion percentage: {inspection_form.completion_percentage}%")
    except Exception as e:
        print(f"✗ Error creating inspection form: {e}")
        return
    
    # Step 5: Test health index calculation
    try:
        health_index, inspection_result = calculate_vehicle_health_index(inspection_form)
        print(f"✓ Calculated health index: {health_index}")
        print(f"✓ Inspection result: {inspection_result}")
        
        # Check if the main inspection record was updated
        inspection.refresh_from_db()
        print(f"✓ Updated inspection record:")
        print(f"  - Health Index: {inspection.vehicle_health_index}")
        print(f"  - Result: {inspection.inspection_result}")
        
    except Exception as e:
        print(f"✗ Error calculating health index: {e}")
        return
    
    # Step 6: Test failed points detection
    try:
        failed_points = inspection_form.failed_points
        print(f"✓ Failed points detected: {len(failed_points)}")
        for point in failed_points:
            print(f"  - {point}")
            
        print(f"✓ Has major issues: {inspection_form.has_major_issues}")
        
    except Exception as e:
        print(f"✗ Error getting failed points: {e}")
        return
    
    # Step 7: Test recommendations
    try:
        from maintenance_history.utils import get_inspection_recommendations
        recommendations = get_inspection_recommendations(inspection_form)
        print(f"✓ Generated {len(recommendations)} recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
            
    except Exception as e:
        print(f"✗ Error generating recommendations: {e}")
        return
    
    print(f"\n=== Workflow Test Complete ===")
    print(f"Inspection {inspection.inspection_number} successfully processed!")
    print(f"Final Health Index: {inspection.vehicle_health_index}")
    print(f"Final Result: {dict(Inspection.RESULT_CHOICES)[inspection.inspection_result]}")

def test_health_calculation_scenarios():
    """Test different health calculation scenarios"""
    
    print("\n=== Testing Health Calculation Scenarios ===\n")
    
    scenarios = [
        {
            'name': 'Perfect Vehicle',
            'data': {
                'brake_pads': 'pass', 'brake_discs': 'pass', 'brake_fluid': 'pass',
                'tire_tread_depth': 'pass', 'tire_pressure': 'pass',
                'engine_oil_level': 'pass', 'battery_voltage': 'pass',
                'headlights': 'pass', 'brake_lights': 'pass', 'seat_belts': 'pass'
            }
        },
        {
            'name': 'Critical Brake Failure',
            'data': {
                'brake_pads': 'fail', 'brake_discs': 'major', 'brake_fluid': 'pass',
                'tire_tread_depth': 'pass', 'tire_pressure': 'pass',
                'engine_oil_level': 'pass', 'battery_voltage': 'pass',
                'headlights': 'pass', 'brake_lights': 'pass', 'seat_belts': 'pass'
            }
        },
        {
            'name': 'Multiple Minor Issues',
            'data': {
                'brake_pads': 'pass', 'brake_discs': 'pass', 'brake_fluid': 'pass',
                'tire_tread_depth': 'minor', 'tire_pressure': 'minor',
                'engine_oil_level': 'minor', 'battery_voltage': 'minor',
                'headlights': 'pass', 'brake_lights': 'pass', 'seat_belts': 'pass',
                'air_filter': 'minor', 'cabin_air_filter': 'minor'
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"Testing: {scenario['name']}")
        
        # Create a mock inspection form for testing
        class MockInspectionForm:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
                # Set default 'pass' for any missing critical fields
                critical_fields = [
                    'brake_pads', 'brake_discs', 'brake_fluid', 'tire_tread_depth', 
                    'tire_pressure', 'engine_oil_level', 'battery_voltage',
                    'headlights', 'brake_lights', 'seat_belts'
                ]
                for field in critical_fields:
                    if not hasattr(self, field):
                        setattr(self, field, 'pass')
        
        mock_form = MockInspectionForm(scenario['data'])
        
        try:
            health_index, inspection_result = calculate_vehicle_health_index(mock_form)
            result_display = dict(Inspection.RESULT_CHOICES)[inspection_result]
            print(f"  ✓ Health Index: {health_index}")
            print(f"  ✓ Result: {result_display}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print()

if __name__ == '__main__':
    try:
        test_inspection_workflow()
        test_health_calculation_scenarios()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()