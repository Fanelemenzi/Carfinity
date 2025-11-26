# test_quote_collection.py
"""
Management command to test quote collection functionality
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import timedelta

from assessments.models import VehicleAssessment
from vehicles.models import Vehicle
from insurance_app.models import (
    DamagedPart, 
    PartQuoteRequest, 
    VehicleAssessmentQuoteExtension
)
from insurance_app.quote_collection import QuoteCollectionEngine


class Command(BaseCommand):
    help = 'Test quote collection engine functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test data for quote collection',
        )
        
        parser.add_argument(
            '--test-validation',
            action='store_true',
            help='Test quote data validation',
        )
        
        parser.add_argument(
            '--test-processing',
            action='store_true',
            help='Test quote processing workflow',
        )
    
    def handle(self, *args, **options):
        engine = QuoteCollectionEngine()
        
        if options['create_test_data']:
            self.create_test_data()
        
        if options['test_validation']:
            self.test_validation(engine)
        
        if options['test_processing']:
            self.test_processing(engine)
    
    def create_test_data(self):
        """Create test data for quote collection testing"""
        self.stdout.write("Creating test data...")
        
        # Create or get test user
        user, created = User.objects.get_or_create(
            username='test_assessor',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'Assessor'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Create test vehicle
        vehicle, created = Vehicle.objects.get_or_create(
            vin='TEST123456789',
            defaults={
                'make': 'Toyota',
                'model': 'Camry',
                'manufacture_year': 2020
            }
        )
        
        # Create test assessment
        assessment, created = VehicleAssessment.objects.get_or_create(
            vehicle=vehicle,
            user=user,
            defaults={
                'status': 'completed',
                'assessment_type': 'insurance_claim',
                'assessor_name': 'Test Assessor'
            }
        )
        
        # Create quote extension
        quote_ext, created = VehicleAssessmentQuoteExtension.objects.get_or_create(
            assessment=assessment,
            defaults={
                'uses_parts_based_quotes': True,
                'parts_identification_complete': True
            }
        )
        
        # Create damaged part
        damaged_part, created = DamagedPart.objects.get_or_create(
            assessment=assessment,
            part_name='Front Bumper',
            defaults={
                'section_type': 'exterior',
                'part_category': 'body',
                'damage_severity': 'moderate',
                'damage_description': 'Scratches and dents from minor collision',
                'estimated_labor_hours': Decimal('2.5')
            }
        )
        
        # Create quote request
        quote_request, created = PartQuoteRequest.objects.get_or_create(
            damaged_part=damaged_part,
            assessment=assessment,
            defaults={
                'expiry_date': timezone.now() + timedelta(days=7),
                'include_assessor': True,
                'include_dealer': True,
                'dispatched_by': user,
                'status': 'sent'
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Test data created:\n"
                f"- Assessment ID: {assessment.id}\n"
                f"- Damaged Part: {damaged_part.part_name}\n"
                f"- Quote Request ID: {quote_request.request_id}"
            )
        )
        
        return assessment, damaged_part, quote_request
    
    def test_validation(self, engine):
        """Test quote data validation"""
        self.stdout.write("Testing quote data validation...")
        
        # Create minimal test data
        assessment, damaged_part, quote_request = self.create_test_data()
        
        # Test valid data
        valid_data = {
            'provider_type': 'dealer',
            'provider_name': 'Toyota Authorized Dealer',
            'part_cost': '450.00',
            'labor_cost': '112.50',
            'paint_cost': '67.50',
            'additional_costs': '20.00',
            'total_cost': '650.00',
            'estimated_delivery_days': 3,
            'estimated_completion_days': 5,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        result = engine.validate_quote_data(valid_data, quote_request)
        
        if result['is_valid']:
            self.stdout.write(self.style.SUCCESS("✓ Valid data validation passed"))
        else:
            self.stdout.write(
                self.style.ERROR(f"✗ Valid data validation failed: {result['errors']}")
            )
        
        # Test invalid data
        invalid_data = {
            'provider_type': 'invalid_type',
            'provider_name': 'Test Provider',
            'part_cost': '-100.00',  # Negative cost
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() - timedelta(days=1)).isoformat()  # Past date
        }
        
        result = engine.validate_quote_data(invalid_data, quote_request)
        
        if not result['is_valid']:
            self.stdout.write(self.style.SUCCESS("✓ Invalid data validation correctly failed"))
            self.stdout.write(f"  Errors: {result['errors']}")
        else:
            self.stdout.write(self.style.ERROR("✗ Invalid data validation should have failed"))
    
    def test_processing(self, engine):
        """Test quote processing workflow"""
        self.stdout.write("Testing quote processing workflow...")
        
        # Create test data
        assessment, damaged_part, quote_request = self.create_test_data()
        
        # Test successful quote processing
        quote_data = {
            'provider_type': 'assessor',
            'provider_name': 'Internal Assessment',
            'part_cost': '350.00',
            'labor_cost': '112.50',
            'paint_cost': '52.50',
            'additional_costs': '10.00',
            'total_cost': '525.00',
            'part_type': 'oem_equivalent',
            'estimated_delivery_days': 1,
            'estimated_completion_days': 3,
            'part_warranty_months': 12,
            'labor_warranty_months': 12,
            'confidence_score': 90,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat(),
            'notes': 'Internal estimate based on standard rates'
        }
        
        result = engine.process_provider_response(quote_request.request_id, quote_data)
        
        if result['success']:
            self.stdout.write(self.style.SUCCESS("✓ Quote processing successful"))
            self.stdout.write(f"  Quote ID: {result['quote_id']}")
            
            # Test completion checker
            completion = engine.quote_completion_checker(assessment)
            self.stdout.write(
                f"  Completion: {completion['completion_percentage']:.1f}% "
                f"({completion['received_quotes']}/{completion['expected_quotes']} quotes)"
            )
            
            # Test statistics
            stats = engine.get_quote_statistics(assessment)
            self.stdout.write(
                f"  Statistics: {stats['overall_statistics']['total_quotes']} total quotes"
            )
            
        else:
            self.stdout.write(
                self.style.ERROR(f"✗ Quote processing failed: {result['errors']}")
            )
        
        # Test invalid request ID
        invalid_result = engine.process_provider_response('INVALID-ID', quote_data)
        
        if not invalid_result['success']:
            self.stdout.write(self.style.SUCCESS("✓ Invalid request ID correctly rejected"))
        else:
            self.stdout.write(self.style.ERROR("✗ Invalid request ID should have been rejected"))
        
        self.stdout.write(self.style.SUCCESS("Quote collection engine testing completed!"))