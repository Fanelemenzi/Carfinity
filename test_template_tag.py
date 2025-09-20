#!/usr/bin/env python
"""
Simple test to verify the template tag works correctly.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import User
from users.templatetags.dashboard_extras import get_user_dashboard_access

def test_template_tag():
    """Test the get_user_dashboard_access template tag"""
    
    print("Testing get_user_dashboard_access template tag...")
    
    # Test with None user
    result = get_user_dashboard_access(None)
    print(f"None user result: {result}")
    
    # Test with unauthenticated user
    try:
        user = User.objects.first()
        if user:
            result = get_user_dashboard_access(user)
            print(f"User {user.username} result: {result}")
        else:
            print("No users found in database")
    except Exception as e:
        print(f"Error testing with user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_template_tag()