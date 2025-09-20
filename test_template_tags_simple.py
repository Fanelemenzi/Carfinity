#!/usr/bin/env python
"""
Simple test script for template tags
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from users.templatetags.dashboard_extras import get_user_dashboard_access

def test_template_tags():
    print("Testing template tags...")
    
    # Test with None user
    result = get_user_dashboard_access(None)
    print("Test with None user:", result)
    
    # Test with mock unauthenticated user
    class MockUser:
        is_authenticated = False
        id = 1
    
    mock_user = MockUser()
    result = get_user_dashboard_access(mock_user)
    print("Test with unauthenticated user:", result)
    
    print("Template tag tests completed successfully!")

if __name__ == "__main__":
    test_template_tags()