#!/usr/bin/env python
"""
Manual Cloudinary Integration Test
Quick test to verify Cloudinary is working with search results.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

def test_cloudinary_basic_config():
    """Test basic Cloudinary configuration"""
    print("🔍 Testing Cloudinary Configuration...")
    
    try:
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
        print("✅ Cloudinary library imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Cloudinary: {e}")
        return False
    
    # Check configuration
    config = cloudinary.config()
    print(f"✅ Cloud name: {config.cloud_name}")
    print(f"✅ API key: {config.api_key[:10]}..." if config.api_key else "❌ API key not set")
    print(f"✅ API secret: {'*' * 10}" if config.api_secret else "❌ API secret not set")
    
    return bool(config.cloud_name and config.api_key and config.api_secret)

def test_vehicle_model():
    """Test Vehicle and VehicleImage models"""
    print("\n🔍 Testing Vehicle Models...")
    
    try:
        from vehicles.models import Vehicle, VehicleImage
        print("✅ Vehicle models imported successfully")
        
        # Check if models have required fields
        vehicle_fields = [f.name for f in Vehicle._meta.fields]
        required_fields = ['vin', 'make', 'model', 'manufacture_year']
        
        for field in required_fields:
            if field in vehicle_fields:
                print(f"✅ Vehicle.{field} field exists")
            else:
                print(f"❌ Vehicle.{field} field missing")
        
        # Check VehicleImage model
        image_fields = [f.name for f in VehicleImage._meta.fields]
        required_image_fields = ['vehicle', 'image', 'image_type']
        
        for field in required_image_fields:
            if field in image_fields:
                print(f"✅ VehicleImage.{field} field exists")
            else:
                print(f"❌ VehicleImage.{field} field missing")
                
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False

def test_search_view():
    """Test search view exists and is accessible"""
    print("\n🔍 Testing Search View...")
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        # Try to reverse the URL
        try:
            url = reverse('search:search_results')
            print(f"✅ Search results URL: {url}")
        except Exception as e:
            print(f"❌ Failed to reverse search URL: {e}")
            return False
        
        # Test view with client
        client = Client()
        response = client.get(url, {'vin': 'TEST123456789'})
        
        if response.status_code == 200:
            print("✅ Search view responds successfully")
        elif response.status_code == 404:
            print("❌ Search view not found (404)")
            return False
        else:
            print(f"⚠️  Search view returned status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing search view: {e}")
        return False

def test_template_exists():
    """Test that search results template exists"""
    print("\n🔍 Testing Template...")
    
    template_paths = [
        'templates/search/search-results.html',
        'search/templates/search/search-results.html',
        'templates/search/search_results.html',
    ]
    
    template_found = False
    for path in template_paths:
        if os.path.exists(path):
            print(f"✅ Template found: {path}")
            template_found = True
            
            # Check template content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for image-related code
            if 'vehicle_images' in content:
                print("✅ Template contains vehicle_images reference")
            else:
                print("⚠️  Template may not handle vehicle images")
            
            if 'image.url' in content:
                print("✅ Template accesses image URLs")
            else:
                print("⚠️  Template may not display image URLs")
                
            break
    
    if not template_found:
        print("❌ Search results template not found")
        print("Checked paths:", template_paths)
    
    return template_found

def test_cloudinary_upload():
    """Test actual Cloudinary upload (if credentials are available)"""
    print("\n🔍 Testing Cloudinary Upload...")
    
    try:
        import cloudinary.uploader
        from PIL import Image
        import tempfile
        import io
        
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        # Try to upload to Cloudinary
        result = cloudinary.uploader.upload(
            img_buffer,
            folder="test_uploads",
            public_id="test_image_" + str(int(time.time())),
            resource_type="image"
        )
        
        print("✅ Successfully uploaded test image to Cloudinary")
        print(f"✅ Image URL: {result.get('secure_url', 'N/A')}")
        
        # Clean up - delete the test image
        try:
            cloudinary.uploader.destroy(result['public_id'])
            print("✅ Test image cleaned up")
        except:
            print("⚠️  Could not clean up test image")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloudinary upload test failed: {e}")
        print("This might be due to:")
        print("  - Invalid Cloudinary credentials")
        print("  - Network connectivity issues")
        print("  - Missing PIL/Pillow library")
        return False

def create_test_data():
    """Create test vehicle and image data"""
    print("\n🔍 Creating Test Data...")
    
    try:
        from vehicles.models import Vehicle, VehicleImage
        from django.contrib.auth.models import User
        
        # Create or get test vehicle
        vehicle, created = Vehicle.objects.get_or_create(
            vin='TEST123456789ABCDEF',
            defaults={
                'make': 'Toyota',
                'model': 'Camry',
                'manufacture_year': 2020,
                'body_type': 'Sedan',
                'engine_code': '2AR-FE',
                'interior_color': 'Black',
                'exterior_color': 'Silver',
                'fuel_type': 'Gasoline',
                'transmission_type': 'Automatic',
                'powertrain_displacement': '2.5L',
                'powertrain_power': '203hp',
                'plant_location': 'Georgetown, KY'
            }
        )
        
        if created:
            print("✅ Created test vehicle")
        else:
            print("✅ Using existing test vehicle")
        
        # Create test image record (with mock Cloudinary URL)
        image, created = VehicleImage.objects.get_or_create(
            vehicle=vehicle,
            image_type='exterior_front',
            defaults={
                'image': 'https://res.cloudinary.com/demo/image/upload/sample.jpg',
                'description': 'Test front view',
                'is_primary': True
            }
        )
        
        if created:
            print("✅ Created test vehicle image")
        else:
            print("✅ Using existing test vehicle image")
        
        print(f"✅ Test VIN: {vehicle.vin}")
        return vehicle.vin
        
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return None

def test_search_with_images():
    """Test search results with actual image data"""
    print("\n🔍 Testing Search Results with Images...")
    
    # Create test data
    test_vin = create_test_data()
    if not test_vin:
        return False
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        url = reverse('search:search_results')
        response = client.get(url, {'vin': test_vin})
        
        if response.status_code == 200:
            print("✅ Search results page loaded successfully")
            
            content = response.content.decode('utf-8')
            
            # Check for vehicle data
            if test_vin in content:
                print("✅ Vehicle VIN found in response")
            else:
                print("❌ Vehicle VIN not found in response")
            
            # Check for image-related content
            if 'vehicle_images' in content or 'image' in content.lower():
                print("✅ Image-related content found in response")
            else:
                print("⚠️  No image-related content found")
            
            # Check for Cloudinary URLs
            if 'cloudinary.com' in content:
                print("✅ Cloudinary URLs found in response")
            else:
                print("⚠️  No Cloudinary URLs found")
            
            return True
        else:
            print(f"❌ Search results returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing search results: {e}")
        return False

def main():
    """Run all tests"""
    print("CLOUDINARY SEARCH INTEGRATION - MANUAL TEST")
    print("=" * 50)
    
    import time
    
    tests = [
        ("Basic Configuration", test_cloudinary_basic_config),
        ("Vehicle Models", test_vehicle_model),
        ("Search View", test_search_view),
        ("Template", test_template_exists),
        ("Cloudinary Upload", test_cloudinary_upload),
        ("Search with Images", test_search_with_images),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Cloudinary integration appears to be working.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
        
        print("\nCommon solutions:")
        print("- Ensure Cloudinary credentials are set in .env file")
        print("- Run 'python manage.py migrate' to create database tables")
        print("- Install required packages: pip install cloudinary pillow")
        print("- Check that search app is in INSTALLED_APPS")

if __name__ == '__main__':
    main()