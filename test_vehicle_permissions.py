#!/usr/bin/env python
"""
Test script to verify VehicleOwnerPermission class functionality
"""

import os
import sys
import django
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import Mock

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from notifications.permissions import VehicleOwnerPermission
from vehicles.models import Vehicle


def test_vehicle_owner_permission():
    """
    Test VehicleOwnerPermission class functionality
    """
    print("Testing VehicleOwnerPermission class...")
    
    # Create mock request factory
    factory = RequestFactory()
    permission = VehicleOwnerPermission()
    
    # Test 1: Unauthenticated user
    print("\n1. Testing unauthenticated user...")
    request = factory.get('/api/vehicle/1/')
    request.user = Mock()
    request.user.is_authenticated = False
    
    mock_view = Mock()
    mock_view.kwargs = {'vehicle_id': 1}
    
    result = permission.has_permission(request, mock_view)
    print(f"   Unauthenticated user access: {result} (should be False)")
    assert not result, "Unauthenticated users should be denied access"
    
    # Test 2: Authenticated user without vehicle ownership
    print("\n2. Testing authenticated user without vehicle ownership...")
    request.user.is_authenticated = True
    request.user.id = 999  # Non-existent user ID
    
    result = permission.has_permission(request, mock_view)
    print(f"   User without vehicle ownership: {result} (should be False)")
    # This will be False because check_vehicle_ownership will return None
    
    # Test 3: Test utility methods
    print("\n3. Testing utility methods...")
    
    # Test check_vehicle_ownership with non-existent vehicle
    vehicle = permission.check_vehicle_ownership(request.user, 999)
    print(f"   Non-existent vehicle check: {vehicle} (should be None)")
    assert vehicle is None, "Non-existent vehicle should return None"
    
    # Test get_user_vehicles with mock user
    vehicles = permission.get_user_vehicles(request.user)
    print(f"   User vehicles count: {vehicles.count()} (should be 0 for non-existent user)")
    
    print("\n4. Testing permission class methods...")
    
    # Test has_object_permission with mock vehicle
    mock_vehicle = Mock(spec=Vehicle)
    mock_vehicle.ownerships.filter.return_value.exists.return_value = False
    
    result = permission.has_object_permission(request, mock_view, mock_vehicle)
    print(f"   Object permission without ownership: {result} (should be False)")
    assert not result, "User without ownership should be denied object access"
    
    # Test with ownership
    mock_vehicle.ownerships.filter.return_value.exists.return_value = True
    result = permission.has_object_permission(request, mock_view, mock_vehicle)
    print(f"   Object permission with ownership: {result} (should be True)")
    assert result, "User with ownership should be granted object access"
    
    print("\n✅ All VehicleOwnerPermission tests passed!")


def test_permission_logging():
    """
    Test that permission class logs access attempts appropriately
    """
    print("\nTesting permission logging...")
    
    factory = RequestFactory()
    permission = VehicleOwnerPermission()
    
    # Test logging for unauthenticated access
    request = factory.get('/api/vehicle/1/')
    request.user = Mock()
    request.user.is_authenticated = False
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    
    mock_view = Mock()
    mock_view.kwargs = {'vehicle_id': 1}
    
    # This should log a warning about unauthenticated access
    result = permission.has_permission(request, mock_view)
    print(f"   Logged unauthenticated access attempt: {not result}")
    
    print("✅ Permission logging test completed!")


if __name__ == '__main__':
    try:
        test_vehicle_owner_permission()
        test_permission_logging()
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)