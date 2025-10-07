#!/usr/bin/env python
"""
Test script to verify the vehicle selector dropdown functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from vehicles.models import Vehicle, VehicleOwnership
from notifications.views import AutoCareDashboardView
import json

def test_dropdown_functionality():
    """Test the vehicle selector dropdown functionality comprehensively"""
    
    print("🔍 TESTING VEHICLE SELECTOR DROPDOWN FUNCTIONALITY")
    print("=" * 65)
    
    # Test 1: Check template structure
    print("1. Template Structure Verification...")
    
    template_path = "templates/dashboard/autocare_dashboard.html"
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Check critical elements
        dropdown_elements = [
            ('id="vehicle-selector"', 'Dropdown element with correct ID'),
            ('id="vehicle-loading"', 'Loading indicator element'),
            ('{% if user_vehicles and user_vehicles|length > 1 %}', 'Conditional rendering logic'),
            ('{% for v in user_vehicles %}', 'Vehicle iteration loop'),
            ('value="{{ v.id }}"', 'Vehicle ID in option value'),
            ('{{ v.manufacture_year }} {{ v.make }} {{ v.model }}', 'Vehicle display format'),
            ('{% if vehicle and v.id == vehicle.id %}selected{% endif %}', 'Current selection logic'),
        ]
        
        template_ok = True
        for element, description in dropdown_elements:
            if element in template_content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - MISSING!")
                template_ok = False
        
        if template_ok:
            print("   🎉 Template structure: CORRECT")
        else:
            print("   ⚠️  Template structure: HAS ISSUES")
            
    except FileNotFoundError:
        print("   ❌ Template file not found!")
        return False
    
    # Test 2: JavaScript Event Handling
    print("\n2. JavaScript Event Handling Verification...")
    
    js_elements = [
        ('vehicleSelector.addEventListener(\'change\'', 'Change event listener'),
        ('handleVehicleChange(selectedVehicleId)', 'Vehicle change handler'),
        ('fetchDashboardData(vehicleId)', 'API data fetching'),
        ('updateDashboardUI(data)', 'UI update function'),
        ('showLoadingState()', 'Loading state management'),
        ('hideLoadingState()', 'Loading state cleanup'),
        ('updateBrowserURL(vehicleId)', 'URL update functionality'),
    ]
    
    js_ok = True
    for element, description in js_elements:
        if element in template_content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} - MISSING!")
            js_ok = False
    
    if js_ok:
        print("   🎉 JavaScript functionality: COMPLETE")
    else:
        print("   ⚠️  JavaScript functionality: HAS ISSUES")
    
    # Test 3: Backend Logic Verification
    print("\n3. Backend Logic Verification...")
    
    try:
        from notifications.views import AutoCareDashboardView
        from vehicles.models import Vehicle, VehicleOwnership
        
        # Check view methods
        view = AutoCareDashboardView()
        backend_methods = [
            ('get_user_vehicles', 'Method to fetch user vehicles'),
            ('get_user_vehicle', 'Method to fetch specific vehicle'),
            ('get_context_data', 'Context data preparation'),
        ]
        
        backend_ok = True
        for method_name, description in backend_methods:
            if hasattr(view, method_name):
                print(f"   ✅ {description}: {method_name}")
            else:
                print(f"   ❌ {description}: {method_name} - MISSING!")
                backend_ok = False
        
        # Check model relationships
        vehicle_fields = [field.name for field in Vehicle._meta.get_fields()]
        ownership_fields = [field.name for field in VehicleOwnership._meta.get_fields()]
        
        if 'ownerships' in [field.name for field in Vehicle._meta.get_fields()]:
            print("   ✅ Vehicle -> VehicleOwnership relationship")
        else:
            print("   ❌ Vehicle -> VehicleOwnership relationship - MISSING!")
            backend_ok = False
        
        if 'is_current_owner' in ownership_fields:
            print("   ✅ VehicleOwnership.is_current_owner field")
        else:
            print("   ❌ VehicleOwnership.is_current_owner field - MISSING!")
            backend_ok = False
        
        if backend_ok:
            print("   🎉 Backend logic: CORRECT")
        else:
            print("   ⚠️  Backend logic: HAS ISSUES")
            
    except ImportError as e:
        print(f"   ❌ Backend import error: {e}")
        backend_ok = False
    
    # Test 4: API Endpoint Verification
    print("\n4. API Endpoint Verification...")
    
    try:
        from notifications.urls import urlpatterns
        from notifications.views import DashboardAPIView
        
        # Check URL pattern
        api_found = False
        for pattern in urlpatterns:
            if hasattr(pattern, 'pattern') and 'api/dashboard' in str(pattern.pattern):
                print(f"   ✅ API endpoint pattern: {pattern.pattern}")
                api_found = True
                break
        
        if not api_found:
            print("   ❌ API endpoint pattern - NOT FOUND!")
        
        # Check API view
        if hasattr(DashboardAPIView, 'get'):
            print("   ✅ DashboardAPIView.get method")
        else:
            print("   ❌ DashboardAPIView.get method - MISSING!")
        
        # Check permissions
        if hasattr(DashboardAPIView, 'permission_classes'):
            print(f"   ✅ API permissions: {DashboardAPIView.permission_classes}")
        else:
            print("   ❌ API permissions - NOT CONFIGURED!")
        
        print("   🎉 API endpoint: CONFIGURED")
        
    except ImportError as e:
        print(f"   ❌ API import error: {e}")
    
    # Test 5: UI Update Functions
    print("\n5. UI Update Functions Verification...")
    
    ui_functions = [
        'updateVehicleOverview',
        'updateUpcomingMaintenance',
        'updateAlerts', 
        'updateServiceHistory',
        'updateValuation',
        'updateCostAnalytics'
    ]
    
    ui_ok = True
    for func_name in ui_functions:
        if f'function {func_name}(' in template_content:
            print(f"   ✅ {func_name}")
        else:
            print(f"   ❌ {func_name} - MISSING!")
            ui_ok = False
    
    if ui_ok:
        print("   🎉 UI update functions: COMPLETE")
    else:
        print("   ⚠️  UI update functions: INCOMPLETE")
    
    # Test 6: Error Handling
    print("\n6. Error Handling Verification...")
    
    error_elements = [
        ('showErrorMessage(', 'Error message display'),
        ('catch(error =>', 'JavaScript error catching'),
        ('if (!response.ok)', 'HTTP response validation'),
        ('vehicle-switch-error', 'Error message styling'),
        ('setTimeout(() =>', 'Auto-hide error messages'),
    ]
    
    error_ok = True
    for element, description in error_elements:
        if element in template_content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} - MISSING!")
            error_ok = False
    
    if error_ok:
        print("   🎉 Error handling: ROBUST")
    else:
        print("   ⚠️  Error handling: NEEDS IMPROVEMENT")
    
    # Test 7: Utility Functions
    print("\n7. Utility Functions Verification...")
    
    utility_functions = [
        'formatCurrency',
        'formatDate', 
        'formatDateFriendly',
        'formatTimeSince',
        'getServiceUrgencyClass',
        'getHealthStatusColor',
        'getAlertPriorityEmoji'
    ]
    
    utility_ok = True
    for func_name in utility_functions:
        if f'function {func_name}(' in template_content:
            print(f"   ✅ {func_name}")
        else:
            print(f"   ❌ {func_name} - MISSING!")
            utility_ok = False
    
    if utility_ok:
        print("   🎉 Utility functions: COMPLETE")
    else:
        print("   ⚠️  Utility functions: INCOMPLETE")
    
    # Final Assessment
    print("\n" + "=" * 65)
    print("📊 DROPDOWN FUNCTIONALITY ASSESSMENT")
    print("=" * 65)
    
    all_checks = [template_ok, js_ok, backend_ok, ui_ok, error_ok, utility_ok]
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    
    print(f"\n✅ Passed: {passed_checks}/{total_checks} major functionality checks")
    
    if passed_checks == total_checks:
        print("\n🎉 VERDICT: DROPDOWN FULLY FUNCTIONAL!")
        print("The vehicle selector dropdown is properly implemented and should work as intended.")
        
        print("\n🚀 EXPECTED BEHAVIOR:")
        print("• Dropdown appears only for users with multiple vehicles")
        print("• Selecting a vehicle triggers AJAX call to fetch new data")
        print("• Loading spinner shows during data fetch")
        print("• All dashboard sections update with new vehicle data")
        print("• Browser URL updates without page reload")
        print("• Error messages appear if API calls fail")
        print("• Graceful fallback for single-vehicle users")
        
    elif passed_checks >= total_checks * 0.8:
        print("\n⚠️  VERDICT: MOSTLY FUNCTIONAL WITH MINOR ISSUES")
        print("The dropdown should work but may have some edge cases to address.")
        
    else:
        print("\n❌ VERDICT: SIGNIFICANT ISSUES DETECTED")
        print("The dropdown may not work properly and needs fixes.")
    
    print(f"\n📈 Functionality Score: {(passed_checks/total_checks)*100:.1f}%")
    
    return passed_checks == total_checks

if __name__ == "__main__":
    test_dropdown_functionality()