#!/usr/bin/env python
"""
Fix the duplicate vehicle ownership issue and test the dashboard
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleOwnership

def fix_duplicate_ownership():
    """Fix the duplicate vehicle ownership issue"""
    
    print("🔧 FIXING DUPLICATE VEHICLE OWNERSHIP ISSUE")
    print("=" * 50)
    
    # Find vehicles with multiple current owners
    from django.db.models import Count
    duplicate_ownerships = VehicleOwnership.objects.filter(
        is_current_owner=True
    ).values('vehicle').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    print(f"Found {duplicate_ownerships.count()} vehicles with duplicate ownerships")
    
    for dup in duplicate_ownerships:
        vehicle_id = dup['vehicle']
        vehicle = Vehicle.objects.get(id=vehicle_id)
        
        print(f"\n🚗 Vehicle: {vehicle.make} {vehicle.model} (ID: {vehicle_id})")
        
        # Get all current ownerships for this vehicle
        current_ownerships = VehicleOwnership.objects.filter(
            vehicle_id=vehicle_id,
            is_current_owner=True
        ).order_by('start_date')
        
        print(f"   Current owners:")
        for i, ownership in enumerate(current_ownerships):
            print(f"     {i+1}. {ownership.user.username} (since {ownership.start_date})")
        
        # Keep the most recent ownership, mark others as not current
        if current_ownerships.count() > 1:
            # Keep the last one (most recent)
            latest_ownership = current_ownerships.last()
            
            # Mark others as not current
            other_ownerships = current_ownerships.exclude(id=latest_ownership.id)
            for ownership in other_ownerships:
                ownership.is_current_owner = False
                ownership.save()
                print(f"   ✅ Marked {ownership.user.username} as previous owner")
            
            print(f"   ✅ Kept {latest_ownership.user.username} as current owner")
    
    print("\n✅ Duplicate ownership issue fixed!")

def test_dashboard_for_users():
    """Test dashboard functionality for different user types"""
    
    print("\n🧪 TESTING DASHBOARD FOR DIFFERENT USER TYPES")
    print("=" * 50)
    
    # Test users with different vehicle counts
    test_cases = [
        ('fanele', 'multiple vehicles'),
        ('Michael', 'multiple vehicles'),
        ('Phumzile_Buthelezi', 'multiple vehicles'),
        ('Sisekelo', 'single vehicle'),
        ('testuser', 'single vehicle'),
        ('Sciniseko', 'single vehicle'),
        ('Test4', 'no vehicles'),
    ]
    
    for username, expected_type in test_cases:
        try:
            user = User.objects.get(username=username)
            print(f"\n👤 Testing {username} ({expected_type}):")
            
            # Simulate the dashboard view logic
            user_vehicles = Vehicle.objects.filter(
                ownerships__user=user,
                ownerships__is_current_owner=True
            ).order_by('make', 'model', 'manufacture_year')
            
            vehicle_count = user_vehicles.count()
            print(f"   Vehicle count: {vehicle_count}")
            
            # Simulate get_user_vehicle logic
            vehicle = user_vehicles.first() if user_vehicles.exists() else None
            
            print(f"   Selected vehicle: {vehicle}")
            
            # Template conditions
            has_vehicles = user_vehicles.exists()
            has_multiple = vehicle_count > 1
            show_dropdown = has_vehicles and has_multiple
            show_vehicle_data = bool(vehicle)
            show_no_vehicles = not vehicle
            
            print(f"   Template conditions:")
            print(f"     - Show dropdown: {show_dropdown}")
            print(f"     - Show vehicle data: {show_vehicle_data}")
            print(f"     - Show no vehicles message: {show_no_vehicles}")
            
            # Expected behavior
            if expected_type == 'multiple vehicles':
                if show_dropdown and show_vehicle_data and not show_no_vehicles:
                    print(f"   ✅ CORRECT: Multiple vehicle user should see dropdown and vehicle data")
                else:
                    print(f"   ❌ INCORRECT: Multiple vehicle user not working properly")
            
            elif expected_type == 'single vehicle':
                if not show_dropdown and show_vehicle_data and not show_no_vehicles:
                    print(f"   ✅ CORRECT: Single vehicle user should see vehicle data (no dropdown)")
                else:
                    print(f"   ❌ INCORRECT: Single vehicle user not working properly")
            
            elif expected_type == 'no vehicles':
                if not show_dropdown and not show_vehicle_data and show_no_vehicles:
                    print(f"   ✅ CORRECT: No vehicle user should see no vehicles message")
                else:
                    print(f"   ❌ INCORRECT: No vehicle user not working properly")
            
        except User.DoesNotExist:
            print(f"   ❌ User {username} not found")

if __name__ == "__main__":
    fix_duplicate_ownership()
    test_dashboard_for_users()