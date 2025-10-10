#!/usr/bin/env python
"""
Test runner script for Cloudinary integration in search results.
Run this script to test whether the search results template and view
can properly retrieve and display images from Cloudinary.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')

def run_cloudinary_tests():
    """Run Cloudinary integration tests"""
    
    print("=" * 60)
    print("CLOUDINARY INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Testing search results template and view integration with Cloudinary...")
    print()
    
    # Setup Django
    django.setup()
    
    # Get test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Define test modules to run
    test_modules = [
        'search.tests.test_cloudinary_integration.CloudinaryIntegrationTestCase',
        'search.tests.test_cloudinary_integration.CloudinaryPerformanceTestCase',
        'search.tests.test_cloudinary_integration.CloudinaryErrorHandlingTestCase',
    ]
    
    print("Running the following test suites:")
    for module in test_modules:
        print(f"  - {module}")
    print()
    
    # Run tests
    failures = test_runner.run_tests(test_modules)
    
    print()
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if failures:
        print(f"❌ {failures} test(s) failed")
        print("\nFailed tests indicate issues with Cloudinary integration:")
        print("- Check Cloudinary configuration in settings.py")
        print("- Verify environment variables are set correctly")
        print("- Ensure VehicleImage model is properly configured")
        print("- Check search results template for image handling")
        return False
    else:
        print("✅ All tests passed!")
        print("\nCloudinary integration is working correctly:")
        print("- Images can be uploaded to Cloudinary")
        print("- Search results template displays images properly")
        print("- Error handling is implemented")
        print("- Performance is acceptable")
        return True

def check_cloudinary_config():
    """Check Cloudinary configuration"""
    print("Checking Cloudinary configuration...")
    print()
    
    # Check Django settings
    try:
        cloudinary_storage = getattr(settings, 'CLOUDINARY_STORAGE', None)
        if cloudinary_storage:
            print("✅ CLOUDINARY_STORAGE found in settings")
            
            # Check required keys
            required_keys = ['CLOUD_NAME', 'API_KEY', 'API_SECRET']
            for key in required_keys:
                if key in cloudinary_storage:
                    print(f"✅ {key} configured")
                else:
                    print(f"❌ {key} missing from CLOUDINARY_STORAGE")
        else:
            print("❌ CLOUDINARY_STORAGE not found in settings")
            
    except Exception as e:
        print(f"❌ Error checking settings: {e}")
    
    # Check environment variables
    print("\nChecking environment variables...")
    env_vars = ['CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var} set (value: {value[:10]}...)")
        else:
            print(f"❌ {var} not set")
    
    print()

def check_template_integration():
    """Check template integration"""
    print("Checking search results template...")
    
    template_path = 'templates/search/search-results.html'
    
    if os.path.exists(template_path):
        print(f"✅ Template found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for image-related code
        checks = [
            ('vehicle_images', 'Vehicle images loop'),
            ('image.url', 'Image URL access'),
            ('openImageModal', 'Image modal functionality'),
            ('handleImageError', 'Error handling'),
            ('No Image', 'No image placeholder'),
            ('fas fa-image', 'Image placeholder icon'),
        ]
        
        print("\nTemplate integration checks:")
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - '{check}' not found")
                
    else:
        print(f"❌ Template not found: {template_path}")
    
    print()

def main():
    """Main test execution"""
    print("CLOUDINARY SEARCH RESULTS INTEGRATION TEST")
    print("=" * 50)
    print()
    
    # Step 1: Check configuration
    check_cloudinary_config()
    
    # Step 2: Check template
    check_template_integration()
    
    # Step 3: Run tests
    try:
        success = run_cloudinary_tests()
        
        if success:
            print("\n🎉 All checks passed! Cloudinary integration is working properly.")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Please review the issues above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        print("\nThis might indicate:")
        print("- Django is not properly configured")
        print("- Required models don't exist")
        print("- Database is not set up")
        print("- Missing dependencies")
        sys.exit(1)

if __name__ == '__main__':
    main()