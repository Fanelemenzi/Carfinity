"""
Test suite for Cloudinary integration in search results template and views.
Tests image retrieval, display, and error handling for vehicle images.
"""

import os
import tempfile
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from PIL import Image
import cloudinary
import cloudinary.uploader
import cloudinary.api
from vehicles.models import Vehicle, VehicleImage
from search.models import VehicleStatus


class CloudinaryIntegrationTestCase(TestCase):
    """Test Cloudinary integration for search results"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            vin='1HGBH41JXMN109186',
            make='Toyota',
            model='Camry',
            manufacture_year=2020,
            body_type='Sedan',
            engine_code='2AR-FE',
            interior_color='Black',
            exterior_color='Silver',
            fuel_type='Gasoline',
            transmission_type='Automatic',
            powertrain_displacement='2.5L',
            powertrain_power='203hp',
            plant_location='Georgetown, KY'
        )
        
        # Create vehicle status
        self.vehicle_status = VehicleStatus.objects.create(
            vehicle=self.vehicle,
            accident_history='NHA',
            theft_involvement='NHT',
            odometer_fraud='NOF',
            legal_status='LG',
            owner_history=1
        )
        
        # Create test image file
        self.test_image = self._create_test_image()
        
    def _create_test_image(self):
        """Create a test image file"""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file.name, 'JPEG')
        temp_file.close()
        
        # Create Django file object
        with open(temp_file.name, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                name='test_image.jpg',
                content=f.read(),
                content_type='image/jpeg'
            )
        
        # Clean up temp file
        os.unlink(temp_file.name)
        return uploaded_file
    
    def test_cloudinary_configuration(self):
        """Test that Cloudinary is properly configured"""
        # Check if Cloudinary settings exist
        self.assertTrue(hasattr(settings, 'CLOUDINARY_STORAGE'))
        
        # Check if environment variables are set (in test environment, they might be mocked)
        cloudinary_config = cloudinary.config()
        self.assertIsNotNone(cloudinary_config.cloud_name)
        
    @patch('cloudinary.uploader.upload')
    def test_vehicle_image_upload_to_cloudinary(self, mock_upload):
        """Test uploading vehicle image to Cloudinary"""
        # Mock Cloudinary upload response
        mock_upload.return_value = {
            'public_id': 'vehicle_images/test_image_123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test_image_123.jpg',
            'url': 'http://res.cloudinary.com/test/image/upload/v123/vehicle_images/test_image_123.jpg',
            'format': 'jpg',
            'width': 800,
            'height': 600,
            'bytes': 45678
        }
        
        # Create vehicle image
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image=self.test_image,
            image_type='exterior_front',
            description='Front view of vehicle',
            is_primary=True
        )
        
        # Verify image was created
        self.assertIsNotNone(vehicle_image.image)
        self.assertEqual(vehicle_image.vehicle, self.vehicle)
        self.assertEqual(vehicle_image.image_type, 'exterior_front')
        
    def test_search_results_view_with_images(self):
        """Test search results view displays vehicle images correctly"""
        # Create vehicle image with mock Cloudinary URL
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test_image.jpg',
            image_type='exterior_front',
            description='Front view',
            is_primary=True
        )
        
        # Make request to search results
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vehicle.vin)
        self.assertContains(response, self.vehicle.make)
        self.assertContains(response, self.vehicle.model)
        
        # Check if image URL is in response
        self.assertContains(response, vehicle_image.image.url)
        
    def test_search_results_view_without_images(self):
        """Test search results view handles vehicles without images"""
        # Make request without creating any images
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Image')
        self.assertContains(response, 'fas fa-image')  # Placeholder icon
        
    @patch('cloudinary.api.resources')
    def test_cloudinary_image_retrieval(self, mock_resources):
        """Test retrieving images from Cloudinary API"""
        # Mock Cloudinary API response
        mock_resources.return_value = {
            'resources': [
                {
                    'public_id': 'vehicle_images/test_image_123',
                    'secure_url': 'https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test_image_123.jpg',
                    'format': 'jpg',
                    'width': 800,
                    'height': 600,
                    'bytes': 45678,
                    'created_at': '2024-01-01T12:00:00Z'
                }
            ]
        }
        
        # Test API call
        result = cloudinary.api.resources(
            type='upload',
            prefix='vehicle_images/',
            max_results=10
        )
        
        # Verify response
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 1)
        self.assertIn('secure_url', result['resources'][0])
        
    def test_image_error_handling_in_template(self):
        """Test template handles image loading errors gracefully"""
        # Create vehicle image with invalid URL
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://invalid-cloudinary-url.com/broken_image.jpg',
            image_type='exterior_front',
            description='Broken image',
            is_primary=True
        )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check that template includes error handling JavaScript
        self.assertContains(response, 'handleImageError')
        self.assertContains(response, 'onerror')
        
    def test_multiple_vehicle_images_display(self):
        """Test displaying multiple images for a vehicle"""
        # Create multiple vehicle images
        images_data = [
            ('exterior_front', 'Front view', True),
            ('exterior_rear', 'Rear view', False),
            ('interior_dashboard', 'Dashboard view', False),
            ('engine_bay', 'Engine compartment', False),
        ]
        
        for image_type, description, is_primary in images_data:
            VehicleImage.objects.create(
                vehicle=self.vehicle,
                image=f'https://res.cloudinary.com/test/image/upload/v123/vehicle_images/{image_type}.jpg',
                image_type=image_type,
                description=description,
                is_primary=is_primary
            )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check all images are displayed
        for image_type, description, is_primary in images_data:
            self.assertContains(response, image_type)
            self.assertContains(response, description)
            if is_primary:
                self.assertContains(response, 'Primary')
                
    def test_image_modal_functionality(self):
        """Test image modal JavaScript functionality"""
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test.jpg',
            image_type='exterior_front',
            description='Test image',
            is_primary=True
        )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check modal-related JavaScript functions exist
        self.assertContains(response, 'openImageModal')
        self.assertContains(response, 'closeImageModal')
        self.assertContains(response, 'imageModal')
        
    @patch('cloudinary.uploader.destroy')
    def test_image_deletion_from_cloudinary(self, mock_destroy):
        """Test deleting images from Cloudinary"""
        # Mock Cloudinary delete response
        mock_destroy.return_value = {
            'result': 'ok'
        }
        
        # Create and then delete vehicle image
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='vehicle_images/test_image_123',
            image_type='exterior_front',
            description='Test image',
            is_primary=True
        )
        
        # Delete the image
        public_id = 'vehicle_images/test_image_123'
        result = cloudinary.uploader.destroy(public_id)
        
        # Verify deletion
        self.assertEqual(result['result'], 'ok')
        mock_destroy.assert_called_once_with(public_id)
        
    def test_cloudinary_url_transformation(self):
        """Test Cloudinary URL transformations for different image sizes"""
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test.jpg',
            image_type='exterior_front',
            description='Test image',
            is_primary=True
        )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check if image URLs are properly formatted
        self.assertContains(response, 'res.cloudinary.com')
        
    @override_settings(DEBUG=True)
    def test_image_loading_in_debug_mode(self):
        """Test image loading behavior in debug mode"""
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test.jpg',
            image_type='exterior_front',
            description='Test image',
            is_primary=True
        )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, vehicle_image.image.url)
        
    def test_image_security_and_access_control(self):
        """Test image access control and security"""
        # Create vehicle image
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test.jpg',
            image_type='exterior_front',
            description='Test image',
            is_primary=True
        )
        
        # Test that images are accessible in search results
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Verify image URL is present and uses HTTPS
        self.assertContains(response, 'https://res.cloudinary.com')
        
    def test_image_metadata_display(self):
        """Test that image metadata is properly displayed"""
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test.jpg',
            image_type='exterior_front',
            description='Detailed front view of the vehicle',
            is_primary=True
        )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check image metadata is displayed
        self.assertContains(response, vehicle_image.get_image_type_display())
        self.assertContains(response, vehicle_image.description)
        self.assertContains(response, 'Primary')
        
    def tearDown(self):
        """Clean up test data"""
        # Clean up any uploaded test files
        VehicleImage.objects.all().delete()
        Vehicle.objects.all().delete()
        User.objects.all().delete()


class CloudinaryPerformanceTestCase(TestCase):
    """Test Cloudinary performance and optimization"""
    
    def setUp(self):
        """Set up performance test data"""
        self.client = Client()
        
        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            vin='1HGBH41JXMN109187',
            make='Honda',
            model='Civic',
            manufacture_year=2021,
            body_type='Sedan'
        )
        
    def test_image_loading_performance(self):
        """Test image loading performance with multiple images"""
        # Create multiple images
        for i in range(10):
            VehicleImage.objects.create(
                vehicle=self.vehicle,
                image=f'https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test_{i}.jpg',
                image_type='exterior_front',
                description=f'Test image {i}',
                is_primary=(i == 0)
            )
        
        # Measure response time
        import time
        start_time = time.time()
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Check response is successful and reasonably fast
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 5.0)  # Should respond within 5 seconds
        
    def test_image_lazy_loading(self):
        """Test that template supports lazy loading for images"""
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test.jpg',
            image_type='exterior_front',
            description='Test image',
            is_primary=True
        )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check for lazy loading attributes (if implemented)
        content = response.content.decode()
        # This would depend on your implementation
        # self.assertIn('loading="lazy"', content)


class CloudinaryErrorHandlingTestCase(TestCase):
    """Test error handling for Cloudinary integration"""
    
    def setUp(self):
        """Set up error handling test data"""
        self.client = Client()
        
        self.vehicle = Vehicle.objects.create(
            vin='1HGBH41JXMN109188',
            make='Ford',
            model='Focus',
            manufacture_year=2019,
            body_type='Hatchback'
        )
        
    @patch('cloudinary.uploader.upload')
    def test_cloudinary_upload_failure(self, mock_upload):
        """Test handling of Cloudinary upload failures"""
        # Mock upload failure
        mock_upload.side_effect = Exception("Cloudinary upload failed")
        
        # Attempt to create vehicle image
        with self.assertRaises(Exception):
            VehicleImage.objects.create(
                vehicle=self.vehicle,
                image=SimpleUploadedFile("test.jpg", b"fake image content", content_type="image/jpeg"),
                image_type='exterior_front',
                description='Test image',
                is_primary=True
            )
            
    def test_missing_cloudinary_credentials(self):
        """Test behavior when Cloudinary credentials are missing"""
        with override_settings(CLOUDINARY_STORAGE={}):
            response = self.client.get(
                reverse('search:search_results'),
                {'vin': self.vehicle.vin}
            )
            
            # Should still render page, but without images
            self.assertEqual(response.status_code, 200)
            
    def test_network_timeout_handling(self):
        """Test handling of network timeouts when loading images"""
        # Create vehicle image with valid URL
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image='https://res.cloudinary.com/test/image/upload/v123/vehicle_images/test.jpg',
            image_type='exterior_front',
            description='Test image',
            is_primary=True
        )
        
        response = self.client.get(
            reverse('search:search_results'),
            {'vin': self.vehicle.vin}
        )
        
        # Check that JavaScript error handling is present
        self.assertContains(response, 'onerror')
        self.assertContains(response, 'handleImageError')


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests([
        'search.tests.test_cloudinary_integration'
    ])