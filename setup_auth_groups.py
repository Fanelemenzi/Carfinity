#!/usr/bin/env python
"""
Script to set up Django groups for the group-based authentication system.
Run this script after activating the virtual environment.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_groups():
    """Create the required Django groups for authentication"""
    
    print("Setting up Django groups for group-based authentication...")
    
    # Create customers group
    customers_group, created = Group.objects.get_or_create(name='customers')
    if created:
        print("✓ Successfully created 'customers' group")
    else:
        print("⚠ 'customers' group already exists")

    # Create insurance_company group
    insurance_group, created = Group.objects.get_or_create(name='insurance_company')
    if created:
        print("✓ Successfully created 'insurance_company' group")
    else:
        print("⚠ 'insurance_company' group already exists")

    print("\nGroup setup completed successfully!")
    print(f"Total groups in system: {Group.objects.count()}")
    
    # List all groups
    print("\nCurrent groups:")
    for group in Group.objects.all():
        print(f"  - {group.name}")


if __name__ == '__main__':
    try:
        create_groups()
    except Exception as e:
        print(f"Error setting up groups: {e}")
        sys.exit(1)