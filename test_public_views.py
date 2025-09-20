#!/usr/bin/env python
"""
Simple test script to verify public views implementation
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
    django.setup()
    
    # Import after Django setup
    from django.test import TestCase, Client
    from django.urls import reverse
    from django.contrib.auth.models import User
    
    class PublicViewsTest(TestCase):
        def setUp(self):
            self.client = Client()
        
        def test_home_view_accessible_without_login(self):
            """Test that home view is accessible without authentication"""
            response = self.client.get(reverse('home'))
            self.assertEqual(response.status_code, 200)
            print("✓ Home view accessible without login")
        
        def test_about_view_accessible_without_login(self):
            """Test that about view is accessible without authentication"""
            response = self.client.get(reverse('about'))
            self.assertEqual(response.status_code, 200)
            print("✓ About view accessible without login")
        
        def test_blog_view_accessible_without_login(self):
            """Test that blog view is accessible without authentication"""
            response = self.client.get(reverse('blog'))
            self.assertEqual(response.status_code, 200)
            print("✓ Blog view accessible without login")
        
        def test_contact_view_accessible_without_login(self):
            """Test that contact view is accessible without authentication"""
            response = self.client.get(reverse('contact'))
            self.assertEqual(response.status_code, 200)
            print("✓ Contact view accessible without login")
        
        def test_login_view_accessible_without_login(self):
            """Test that login view is accessible without authentication"""
            response = self.client.get(reverse('login'))
            self.assertEqual(response.status_code, 200)
            print("✓ Login view accessible without login")
        
        def test_login_form_submission(self):
            """Test that login form handles POST requests correctly"""
            # Test with invalid credentials
            response = self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            # Should redirect back to login with error
            self.assertEqual(response.status_code, 302)
            print("✓ Login form handles invalid credentials correctly")
        
        def test_logout_redirects_to_home(self):
            """Test that logout redirects to home page"""
            response = self.client.get(reverse('logout'))
            self.assertRedirects(response, reverse('home'))
            print("✓ Logout redirects to home page")
    
    # Run the tests
    print("Testing public views implementation...")
    print("=" * 50)
    
    test_case = PublicViewsTest()
    test_case.setUp()
    
    try:
        test_case.test_home_view_accessible_without_login()
        test_case.test_about_view_accessible_without_login()
        test_case.test_blog_view_accessible_without_login()
        test_case.test_contact_view_accessible_without_login()
        test_case.test_login_view_accessible_without_login()
        test_case.test_login_form_submission()
        test_case.test_logout_redirects_to_home()
        
        print("=" * 50)
        print("✅ All public views tests passed!")
        print("✅ Task 7 implementation is complete and working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)