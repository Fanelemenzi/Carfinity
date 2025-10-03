#!/usr/bin/env python
"""
Simple test script to verify dashboard routing functionality.
Run this script to test the dashboard URL generation for different user types.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import User, Group
from users.services import AuthenticationService
from users.templatetags.dashboard_extras import get_user_dashboard_url

def test_dashboard_routing():
    """Test dashboard routing for different user types"""
    
    print("Testing Dashboard Routing Implementation")
    print("=" * 50)
    
    # Test 1: Unauthenticated user
    print("\n1. Testing unauthenticated user:")
    print(f"   Expected: /login/")
    print(f"   Actual: {get_user_dashboard_url(None)}")
    
    # Test 2: User with no groups
    try:
        user_no_groups = User.objects.filter(groups__isnull=True).first()
        if user_no_groups:
            print(f"\n2. Testing user with no groups ({user_no_groups.username}):")
            url = get_user_dashboard_url(user_no_groups)
            print(f"   Expected: /access-denied/")
            print(f"   Actual: {url}")
        else:
            print("\n2. No users without groups found - skipping test")
    except Exception as e:
        print(f"\n2. Error testing user with no groups: {e}")
    
    # Test 3: AutoCare user
    try:
        autocare_group = Group.objects.get(name='AutoCare')
        autocare_user = autocare_group.user_set.first()
        if autocare_user:
            print(f"\n3. Testing AutoCare user ({autocare_user.username}):")
            url = get_user_dashboard_url(autocare_user)
            print(f"   Expected: /maintenance/dashboard/")
            print(f"   Actual: {url}")
        else:
            print("\n3. No AutoCare users found - skipping test")
    except Group.DoesNotExist:
        print("\n3. AutoCare group not found - skipping test")
    except Exception as e:
        print(f"\n3. Error testing AutoCare user: {e}")
    
    # Test 4: AutoAssess user
    try:
        autoassess_group = Group.objects.get(name='AutoAssess')
        autoassess_user = autoassess_group.user_set.first()
        if autoassess_user:
            print(f"\n4. Testing AutoAssess user ({autoassess_user.username}):")
            url = get_user_dashboard_url(autoassess_user)
            print(f"   Expected: /insurance/")
            print(f"   Actual: {url}")
        else:
            print("\n4. No AutoAssess users found - skipping test")
    except Group.DoesNotExist:
        print("\n4. AutoAssess group not found - skipping test")
    except Exception as e:
        print(f"\n4. Error testing AutoAssess user: {e}")
    
    # Test 5: Staff user
    try:
        staff_group = Group.objects.get(name='Staff')
        staff_user = staff_group.user_set.first()
        if staff_user:
            print(f"\n5. Testing Staff user ({staff_user.username}):")
            url = get_user_dashboard_url(staff_user)
            print(f"   Expected: /admin/")
            print(f"   Actual: {url}")
        else:
            print("\n5. No Staff users found - skipping test")
    except Group.DoesNotExist:
        print("\n5. Staff group not found - skipping test")
    except Exception as e:
        print(f"\n5. Error testing Staff user: {e}")
    
    # Test 6: User with multiple groups
    try:
        # Find a user with multiple groups
        multi_group_user = None
        for user in User.objects.all():
            if user.groups.count() > 1:
                multi_group_user = user
                break
        
        if multi_group_user:
            print(f"\n6. Testing multi-group user ({multi_group_user.username}):")
            groups = list(multi_group_user.groups.values_list('name', flat=True))
            print(f"   Groups: {groups}")
            url = get_user_dashboard_url(multi_group_user)
            print(f"   Expected: /dashboard-selector/")
            print(f"   Actual: {url}")
        else:
            print("\n6. No multi-group users found - skipping test")
    except Exception as e:
        print(f"\n6. Error testing multi-group user: {e}")
    
    print("\n" + "=" * 50)
    print("Dashboard routing test completed!")
    print("\nIf you see any unexpected results, check:")
    print("1. User group assignments in Django admin")
    print("2. AuthenticationService.DASHBOARDS configuration")
    print("3. URL patterns in your Django project")

if __name__ == "__main__":
    test_dashboard_routing()