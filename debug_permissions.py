#!/usr/bin/env python
"""
Debug script to check user permissions and group assignments.
Run this to understand what groups and permissions are set up.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import User, Group
from organizations.models import Organization, OrganizationUser
from users.services import AuthenticationService

def debug_user_permissions():
    """Debug user permissions and group assignments"""
    
    print("=== DEBUGGING USER PERMISSIONS ===\n")
    
    # Check all groups
    print("1. Available Groups:")
    groups = Group.objects.all()
    if groups:
        for group in groups:
            print(f"   - {group.name}")
    else:
        print("   No groups found!")
    
    print(f"\nTotal groups: {groups.count()}\n")
    
    # Check all users
    print("2. Users and their groups:")
    users = User.objects.all()
    for user in users:
        user_groups = list(user.groups.values_list('name', flat=True))
        print(f"   User: {user.username} ({user.email})")
        print(f"   Groups: {user_groups if user_groups else 'None'}")
        
        # Check organization
        try:
            org_user = OrganizationUser.objects.filter(user=user, is_active=True).first()
            if org_user:
                print(f"   Organization: {org_user.organization.name} ({org_user.organization.organization_type})")
            else:
                print(f"   Organization: None")
        except Exception as e:
            print(f"   Organization: Error - {e}")
        
        # Check permissions using AuthenticationService
        try:
            permissions = AuthenticationService.get_user_permissions(user)
            print(f"   Available Dashboards: {permissions.available_dashboards}")
            print(f"   Default Dashboard: {permissions.default_dashboard}")
            print(f"   Has Conflicts: {permissions.has_conflicts}")
            if permissions.conflict_details:
                print(f"   Conflict Details: {permissions.conflict_details}")
        except Exception as e:
            print(f"   Permission Error: {e}")
        
        print()
    
    # Check organizations
    print("3. Organizations:")
    orgs = Organization.objects.all()
    if orgs:
        for org in orgs:
            print(f"   - {org.name} ({org.organization_type})")
            members = OrganizationUser.objects.filter(organization=org, is_active=True)
            print(f"     Members: {[m.user.username for m in members]}")
    else:
        print("   No organizations found!")
    
    print(f"\nTotal organizations: {orgs.count()}\n")
    
    # Check dashboard configurations
    print("4. Dashboard Configurations:")
    dashboards = AuthenticationService.DASHBOARDS
    for name, info in dashboards.items():
        print(f"   Dashboard: {name}")
        print(f"   Display Name: {info.display_name}")
        print(f"   URL: {info.url}")
        print(f"   Required Groups: {info.required_groups}")
        print(f"   Required Org Types: {info.required_org_types}")
        print()

if __name__ == '__main__':
    try:
        debug_user_permissions()
    except Exception as e:
        print(f"Error debugging permissions: {e}")
        import traceback
        traceback.print_exc()