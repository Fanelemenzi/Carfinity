"""
Django management command to test Cloudinary integration with search results.
Usage: python manage.py test_cloudinary
"""

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
from django.conf import settings
import cloudinary
import cloudinary.uploader
import os
import tempfile
from PIL import Image
import io


class Command(BaseCommand):
    help = 'Test Cloudinary integration with search results template and view'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test vehicle and image data',
        )
        parser.add_argument(
            '--upload-test',
            action='store_true',
            help='Test actual upload to Cloudinary',
        )
        parser.add_argument(
            '--vin',
            type=str,
            help='VIN to test search results with',
            default='TEST123456789ABCDEF'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Testing Cloudinary Integration with Search Results')
        )
        self.stdout.write('=' * 60)

        # Test 1: Configuration
        self.test_configuration()

        # Test 2: Models
        self.test_models()

        # Test 3: Create test data if requested
        if options['create_test_data']:
            self.create_test_data(options['vin'])

        # Test 4: Upload test if requested
        if options['upload_test']:
            self.test_upload()

        # Test 5: Search view
        self.test_search_view(options['vin'])

        # Test 6: Template rendering
        self.test_template_rendering(options['vin'])

        self.stdout.write(
            self.style.SUCCESS('\n✅ Cloudinary integration test completed!')
        )

    def test_configuration(self):
        """Test Cloudinary configuration"""
        self.stdout.write('\n📋 Testing Cloudinary Configuration...')

        try:
            # Check if Cloudinary is configured
            config = cloudinary.config()
            
            if config.cloud_name:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Cloud name: {config.cloud_name}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Cloud name not configured')
                )

            if config.api_key:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ API key: {config.api_key[:10]}...')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ API key not configured')
                )

            if config.api_secret:
                self.stdout.write(
                    self.style.SUCCESS('✅ API secret: configured')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ API secret not configured')
                )

            # Check Django settings
            if hasattr(settings, 'CLOUDINARY_STORAGE'):
                self.stdout.write(
                    self.style.SUCCESS('✅ CLOUDINARY_STORAGE in Django settings')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  CLOUDINARY_STORAGE not in Django settings')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Configuration error: {e}')
            )

    def test_models(self):
        """Test Vehicle and VehicleImage models"""
        self.stdout.write('\n📋 Testing Models...')

        try:
            from vehicles.models import Vehicle, VehicleImage
            self.stdout.write(
                self.style.SUCCESS('✅ Vehicle models imported successfully')
            )

            # Check model fields
            vehicle_fields = [f.name for f in Vehicle._meta.fields]
            required_fields = ['vin', 'make', 'model', 'manufacture_year']

            for field in required_fields:
                if field in vehicle_fields:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Vehicle.{field} field exists')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Vehicle.{field} field missing')
                    )

            # Check VehicleImage model
            image_fields = [f.name for f in VehicleImage._meta.fields]
            required_image_fields = ['vehicle', 'image', 'image_type']

            for field in required_image_fields:
                if field in image_fields:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ VehicleImage.{field} field exists')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ VehicleImage.{field} field missing')
                    )

        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to import models: {e}')
            )

    def create_test_data(self, vin):
        """Create test vehicle and image data"""
        self.stdout.write(f'\n📋 Creating Test Data for VIN: {vin}...')

        try:
            from vehicles.models import Vehicle, VehicleImage

            # Create or get test vehicle
            vehicle, created = Vehicle.objects.get_or_create(
                vin=vin,
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
                self.stdout.write(
                    self.style.SUCCESS('✅ Created test vehicle')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ Using existing test vehicle')
                )

            # Create test image records
            image_types = [
                ('exterior_front', 'Front view', True),
                ('exterior_rear', 'Rear view', False),
                ('interior_dashboard', 'Dashboard view', False),
            ]

            for image_type, description, is_primary in image_types:
                image, created = VehicleImage.objects.get_or_create(
                    vehicle=vehicle,
                    image_type=image_type,
                    defaults={
                        'image': f'https://res.cloudinary.com/demo/image/upload/v1/{image_type}_sample.jpg',
                        'description': description,
                        'is_primary': is_primary
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created {image_type} image')
                    )

            # Create vehicle status if search app has it
            try:
                from search.models import VehicleStatus
                status, created = VehicleStatus.objects.get_or_create(
                    vehicle=vehicle,
                    defaults={
                        'accident_history': 'NHA',
                        'theft_involvement': 'NHT',
                        'odometer_fraud': 'NOF',
                        'legal_status': 'LG',
                        'owner_history': 1
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Created vehicle status')
                    )
            except ImportError:
                self.stdout.write(
                    self.style.WARNING('⚠️  VehicleStatus model not available')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create test data: {e}')
            )

    def test_upload(self):
        """Test actual Cloudinary upload"""
        self.stdout.write('\n📋 Testing Cloudinary Upload...')

        try:
            # Create a small test image
            img = Image.new('RGB', (100, 100), color='red')
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG')
            img_buffer.seek(0)

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                img_buffer,
                folder="test_uploads",
                public_id=f"test_image_management_command",
                resource_type="image"
            )

            self.stdout.write(
                self.style.SUCCESS('✅ Successfully uploaded test image')
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Image URL: {result.get("secure_url", "N/A")}')
            )

            # Clean up
            try:
                cloudinary.uploader.destroy(result['public_id'])
                self.stdout.write(
                    self.style.SUCCESS('✅ Test image cleaned up')
                )
            except:
                self.stdout.write(
                    self.style.WARNING('⚠️  Could not clean up test image')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Upload test failed: {e}')
            )

    def test_search_view(self, vin):
        """Test search view functionality"""
        self.stdout.write(f'\n📋 Testing Search View with VIN: {vin}...')

        try:
            # Test URL resolution
            try:
                url = reverse('search:search_results')
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Search URL resolved: {url}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to resolve search URL: {e}')
                )
                return

            # Test view response
            client = Client()
            response = client.get(url, {'vin': vin})

            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS('✅ Search view responds successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Search view returned status {response.status_code}')
                )

            # Check response content
            content = response.content.decode('utf-8')

            if vin in content:
                self.stdout.write(
                    self.style.SUCCESS('✅ VIN found in response')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  VIN not found in response')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Search view test failed: {e}')
            )

    def test_template_rendering(self, vin):
        """Test template rendering with images"""
        self.stdout.write(f'\n📋 Testing Template Rendering...')

        try:
            client = Client()
            url = reverse('search:search_results')
            response = client.get(url, {'vin': vin})

            if response.status_code != 200:
                self.stdout.write(
                    self.style.ERROR('❌ Cannot test template - view not responding')
                )
                return

            content = response.content.decode('utf-8')

            # Check for image-related content
            image_checks = [
                ('vehicle_images', 'Vehicle images loop'),
                ('image.url', 'Image URL access'),
                ('openImageModal', 'Image modal function'),
                ('handleImageError', 'Error handling function'),
                ('No Image', 'No image placeholder'),
                ('fas fa-image', 'Image icon'),
            ]

            for check, description in image_checks:
                if check in content:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {description}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {description} not found')
                    )

            # Check for Cloudinary URLs
            if 'cloudinary.com' in content:
                self.stdout.write(
                    self.style.SUCCESS('✅ Cloudinary URLs found in template')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  No Cloudinary URLs found')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Template rendering test failed: {e}')
            )