#!/usr/bin/env python
"""
Test the dashboard fix to ensure users with vehicles see their data correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleOwnership
from notifications.views import AutoCareDashboardView

def test_dashboard_fix():
    """Test that the dashboard fix works for all user types"""
    
    print("🧪 TESTING DASHBOARD FIX")
    print("=" * 50)
    
    # Create a request factory for testing
    factory = RequestFactory()
    client = Client()
    
    # Test cases: users with different vehicle scenarios
    test_users = [
        ('fanele', 'multiple vehicles', True, True),      # Should see dropdown + vehicle data
        ('Michael', 'multiple vehicles', True, True),     # Should see dropdown + vehicle data  
        ('Sisekelo', 'single vehicle', False, True),      # Should see vehicle data (no dropdown)
        ('testuser', 'single vehicle', False, True),      # Should see vehicle data (no dropdown)
        ('Sciniseko', 'single vehicle', False, True),     # Should see vehicle data (no dropdown)
        ('Test4', 'no vehicles', False, False),           # Should see no vehicles message
    ]
    
    for username, scenario, should_show_dropdown, should_show_vehicle in test_users:
        print(f"\n👤 Testing {username} ({scenario}):")
        
        try:
            user = User.objects.get(username=username)
            
            # Test the view logic directly
            view = AutoCareDashboardView()
            request = factory.get('/dashboard/')
            request.user = user
            view.request = request
            view.kwargs = {}  # No specific vehicle_id
            
            # Get context data
            context = view.get_context_data()
            
            # Check results
            user_vehicles = context.get('user_vehicles', [])
            vehicle = context.get('vehicle')
            
            vehicle_count = len(user_vehicles)
            has_dropdown = vehicle_count > 1
            has_vehicle_data = bool(vehicle)
            
            print(f"   User vehicles count: {vehicle_count}")
            print(f"   Selected vehicle: {vehicle}")
            print(f"   Should show dropdown: {should_show_dropdown} | Actually shows: {has_dropdown}")
            print(f"   Should show vehicle data: {should_show_vehicle} | Actually shows: {has_vehicle_data}")
            
            # Verify expectations
            dropdown_correct = (has_dropdown == should_show_dropdown)
            vehicle_correct = (has_vehicle_data == should_show_vehicle)
            
            if dropdown_correct and vehicle_correct:
                print(f"   ✅ PASS: Dashboard working correctly for {scenario}")
            else:
                print(f"   ❌ FAIL: Dashboard not working correctly")
                if not dropdown_correct:
                    print(f"      - Dropdown logic incorrect")
                if not vehicle_correct:
                    print(f"      - Vehicle data logic incorrect")
            
            # Additional checks for specific scenarios
            if scenario == 'multiple vehicles':
                if vehicle and vehicle.id in [v.id for v in user_vehicles]:
                    print(f"   ✅ Selected vehicle is in user's vehicle list")
                else:
                    print(f"   ❌ Selected vehicle not in user's vehicle list")
            
            elif scenario == 'single vehicle':
                if vehicle and vehicle == user_vehicles[0]:
                    print(f"   ✅ Correctly selected the user's only vehicle")
                else:
                    print(f"   ❌ Did not select the user's only vehicle correctly")
            
            elif scenario == 'no vehicles':
                no_vehicles_message = context.get('no_vehicles_message')
                if no_vehicles_message:
                    print(f"   ✅ No vehicles message present: {no_vehicles_message}")
                else:
                    print(f"   ⚠️  No vehicles message not set (will use default)")
                    
        except User.DoesNotExist:
            print(f"   ❌ User {username} not found")
        except Exception as e:
            print(f"   ❌ Error testing {username}: {e}")
    
    print(f"\n" + "=" * 50)
    print("🎯 DASHBOARD FIX SUMMARY")
    print("=" * 50)
    
    print("\n✅ EXPECTED BEHAVIOR:")
    print("• Users with multiple vehicles: See dropdown + vehicle data")
    print("• Users with single vehicle: See vehicle data (no dropdown)")  
    print("• Users with no vehicles: See 'no vehicles' message")
    
    print("\n🔧 FIXES APPLIED:")
    print("• Fixed duplicate vehicle ownership (Honda Civic)")
    print("• Enhanced get_context_data to auto-select first vehicle")
    print("• Improved vehicle selection logic for users without specific vehicle_id")
    
    print("\n🚀 DASHBOARD STATUS: READY FOR TESTING")
    print("Users should now see appropriate content based on their vehicle ownership.")

if __name__ == "__main__":
    test_dashboard_fix()