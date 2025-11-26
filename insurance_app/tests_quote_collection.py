# tests_quote_collection.py
"""
Unit tests for the Quote Collection and Validation System

Tests cover all aspects of quote collection including data validation,
quote processing, completion tracking, and expiry management.
"""

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

from assessments.models import VehicleAssessment
from vehicles.models import Vehicle
from .models import (
    DamagedPart, 
    PartQuoteRequest, 
    PartQuote, 
    VehicleAssessmentQuoteExtension
)
from .quote_collection import QuoteCollectionEngine, QuoteValidationError


class QuoteCollectionEngineTestCase(TestCase):
    """Test cases for QuoteCollectionEngine"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testassessor',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            manufacture_year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        # Create test assessment
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            status='completed'
        )
        
        # Create quote extension
        self.quote_extension = VehicleAssessmentQuoteExtension.objects.create(
            assessment=self.assessment,
            uses_parts_based_quotes=True,
            parts_identification_complete=True
        )
        
        # Create test damaged part
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dents',
            estimated_labor_hours=Decimal('2.5')
        )
        
        # Create test quote request
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            include_dealer=True,
            dispatched_by=self.user,
            dispatched_at=timezone.now()
        )
        
        # Initialize engine
        self.engine = QuoteCollectionEngine()
    
    def test_process_provider_response_success(self):
        """Test successful processing of provider response"""
        provider_data = {
            'provider_type': 'dealer',
            'provider_name': 'Toyota Authorized Dealer',
            'provider_contact': 'dealer@toyota.com',
            'part_cost': '450.00',
            'labor_cost': '112.50',
            'paint_cost': '67.50',
            'additional_costs': '20.00',
            'total_cost': '650.00',
            'part_type': 'oem',
            'estimated_delivery_days': 3,
            'estimated_completion_days': 5,
            'part_warranty_months': 24,
            'labor_warranty_months': 12,
            'confidence_score': 85,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat(),
            'notes': 'OEM part with full warranty'
        }
        
        result = self.engine.process_provider_response(
            self.quote_request.request_id, 
            provider_data
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['quote_id'])
        self.assertEqual(len(result['errors']), 0)
        
        # Verify quote was created
        quote = PartQuote.objects.get(id=result['quote_id'])
        self.assertEqual(quote.provider_type, 'dealer')
        self.assertEqual(quote.provider_name, 'Toyota Authorized Dealer')
        self.assertEqual(quote.total_cost, Decimal('650.00'))
        self.assertEqual(quote.confidence_score, 85)
        
        # Verify request status updated
        self.quote_request.refresh_from_db()
        self.assertEqual(self.quote_request.status, 'received')
    
    def test_process_provider_response_invalid_request_id(self):
        """Test processing with invalid request ID"""
        provider_data = {
            'provider_type': 'dealer',
            'provider_name': 'Test Dealer',
            'part_cost': '100.00',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        result = self.engine.process_provider_response('INVALID-ID', provider_data)
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['errors'][0])
        self.assertIsNone(result['quote_id'])
    
    def test_process_provider_response_expired_request(self):
        """Test processing response for expired request"""
        # Create expired request
        expired_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() - timedelta(days=1),
            include_dealer=True,
            dispatched_by=self.user
        )
        
        provider_data = {
            'provider_type': 'dealer',
            'provider_name': 'Test Dealer',
            'part_cost': '100.00',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        result = self.engine.process_provider_response(
            expired_request.request_id, 
            provider_data
        )
        
        self.assertFalse(result['success'])
        self.assertIn('expired', result['errors'][0])
    
    def test_validate_quote_data_success(self):
        """Test successful quote data validation"""
        valid_data = {
            'provider_type': 'independent',
            'provider_name': 'Local Garage',
            'part_cost': '300.00',
            'labor_cost': '100.00',
            'paint_cost': '45.00',
            'additional_costs': '15.00',
            'total_cost': '460.00',
            'part_type': 'aftermarket',
            'estimated_delivery_days': 2,
            'estimated_completion_days': 4,
            'part_warranty_months': 12,
            'labor_warranty_months': 6,
            'confidence_score': 70,
            'valid_until': (timezone.now() + timedelta(days=14)).isoformat()
        }
        
        result = self.engine.validate_quote_data(valid_data, self.quote_request)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_quote_data_missing_required_fields(self):
        """Test validation with missing required fields"""
        invalid_data = {
            'provider_type': 'dealer',
            'provider_name': 'Test Dealer',
            # Missing required fields: part_cost, labor_cost, total_cost, etc.
        }
        
        result = self.engine.validate_quote_data(invalid_data, self.quote_request)
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn('Missing required field', result['errors'][0])
    
    def test_validate_quote_data_invalid_provider_type(self):
        """Test validation with invalid provider type"""
        invalid_data = {
            'provider_type': 'invalid_provider',
            'provider_name': 'Test Provider',
            'part_cost': '100.00',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        result = self.engine.validate_quote_data(invalid_data, self.quote_request)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Invalid provider type', result['errors'][0])
    
    def test_validate_quote_data_negative_costs(self):
        """Test validation with negative costs"""
        invalid_data = {
            'provider_type': 'dealer',
            'provider_name': 'Test Dealer',
            'part_cost': '-100.00',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        result = self.engine.validate_quote_data(invalid_data, self.quote_request)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('cannot be negative', result['errors'][0])
    
    def test_validate_quote_data_cost_mismatch(self):
        """Test validation with mismatched total cost"""
        invalid_data = {
            'provider_type': 'dealer',
            'provider_name': 'Test Dealer',
            'part_cost': '100.00',
            'labor_cost': '50.00',
            'paint_cost': '25.00',
            'additional_costs': '10.00',
            'total_cost': '200.00',  # Should be 185.00
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        result = self.engine.validate_quote_data(invalid_data, self.quote_request)
        
        # Should still be valid but with warning
        self.assertTrue(result['is_valid'])
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn("doesn't match sum", result['warnings'][0])
    
    def test_validate_quote_data_invalid_timeline(self):
        """Test validation with invalid timeline"""
        invalid_data = {
            'provider_type': 'dealer',
            'provider_name': 'Test Dealer',
            'part_cost': '100.00',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': -5,  # Invalid
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        result = self.engine.validate_quote_data(invalid_data, self.quote_request)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('cannot be negative', result['errors'][0])
    
    def test_validate_quote_data_past_validity_date(self):
        """Test validation with past validity date"""
        invalid_data = {
            'provider_type': 'dealer',
            'provider_name': 'Test Dealer',
            'part_cost': '100.00',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7,
            'valid_until': (timezone.now() - timedelta(days=1)).isoformat()  # Past date
        }
        
        result = self.engine.validate_quote_data(invalid_data, self.quote_request)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('must be in the future', result['errors'][0])
    
    def test_create_or_update_quote_new_quote(self):
        """Test creating a new quote"""
        provider_data = {
            'provider_type': 'assessor',
            'provider_name': 'Internal Assessment',
            'provider_contact': '',
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
            'valid_until': timezone.now() + timedelta(days=30),
            'notes': 'Internal estimate based on standard rates'
        }
        
        quote = self.engine.create_or_update_quote(self.quote_request, provider_data)
        
        self.assertIsNotNone(quote.id)
        self.assertEqual(quote.provider_type, 'assessor')
        self.assertEqual(quote.total_cost, Decimal('525.00'))
        self.assertEqual(quote.confidence_score, 90)
        self.assertEqual(quote.part_type, 'oem_equivalent')
    
    def test_create_or_update_quote_update_existing(self):
        """Test updating an existing quote"""
        # Create initial quote
        initial_quote = PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='dealer',
            provider_name='Toyota Dealer',
            part_cost=Decimal('400.00'),
            labor_cost=Decimal('100.00'),
            total_cost=Decimal('500.00'),
            estimated_delivery_days=5,
            estimated_completion_days=7,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        # Update data
        updated_data = {
            'provider_type': 'dealer',
            'provider_name': 'Toyota Dealer',
            'provider_contact': 'updated@toyota.com',
            'part_cost': '450.00',
            'labor_cost': '120.00',
            'paint_cost': '60.00',
            'additional_costs': '15.00',
            'total_cost': '645.00',
            'part_type': 'oem',
            'estimated_delivery_days': 3,
            'estimated_completion_days': 5,
            'part_warranty_months': 24,
            'labor_warranty_months': 12,
            'confidence_score': 95,
            'valid_until': timezone.now() + timedelta(days=30),
            'notes': 'Updated quote with premium parts'
        }
        
        updated_quote = self.engine.create_or_update_quote(self.quote_request, updated_data)
        
        # Should be the same quote object, updated
        self.assertEqual(updated_quote.id, initial_quote.id)
        self.assertEqual(updated_quote.total_cost, Decimal('645.00'))
        self.assertEqual(updated_quote.confidence_score, 95)
        self.assertEqual(updated_quote.provider_contact, 'updated@toyota.com')
    
    def test_quote_completion_checker_no_requests(self):
        """Test completion checker with no quote requests"""
        # Create assessment without quote requests
        empty_assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            status='completed'
        )
        
        result = self.engine.quote_completion_checker(empty_assessment)
        
        self.assertFalse(result['is_complete'])
        self.assertEqual(result['completion_percentage'], 0.0)
        self.assertEqual(result['total_requests'], 0)
    
    def test_quote_completion_checker_partial_completion(self):
        """Test completion checker with partial quote collection"""
        # Create additional quote request
        second_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_independent=True,
            dispatched_by=self.user,
            status='sent'
        )
        
        # Create one quote
        PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='assessor',
            provider_name='Internal Assessment',
            part_cost=Decimal('300.00'),
            labor_cost=Decimal('100.00'),
            total_cost=Decimal('400.00'),
            estimated_delivery_days=1,
            estimated_completion_days=3,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        result = self.engine.quote_completion_checker(self.assessment)
        
        self.assertFalse(result['is_complete'])
        self.assertEqual(result['received_quotes'], 1)
        self.assertGreater(result['completion_percentage'], 0)
        self.assertLess(result['completion_percentage'], 100)
    
    def test_quote_completion_checker_full_completion(self):
        """Test completion checker with full quote collection"""
        # Set request status to sent
        self.quote_request.status = 'sent'
        self.quote_request.save()
        
        # Create quotes for all selected providers
        PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='assessor',
            provider_name='Internal Assessment',
            part_cost=Decimal('300.00'),
            labor_cost=Decimal('100.00'),
            total_cost=Decimal('400.00'),
            estimated_delivery_days=1,
            estimated_completion_days=3,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='dealer',
            provider_name='Toyota Dealer',
            part_cost=Decimal('450.00'),
            labor_cost=Decimal('120.00'),
            total_cost=Decimal('570.00'),
            estimated_delivery_days=3,
            estimated_completion_days=5,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        result = self.engine.quote_completion_checker(self.assessment)
        
        self.assertTrue(result['is_complete'])
        self.assertEqual(result['received_quotes'], 2)
        self.assertEqual(result['completion_percentage'], 100.0)
        
        # Check assessment status updated
        self.quote_extension.refresh_from_db()
        self.assertEqual(self.quote_extension.quote_collection_status, 'completed')
    
    def test_cleanup_expired_quotes(self):
        """Test cleanup of expired quotes"""
        # Create expired quote request
        expired_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() - timedelta(days=35),  # 35 days ago
            include_dealer=True,
            dispatched_by=self.user,
            status='sent'
        )
        
        # Create quote for expired request
        expired_quote = PartQuote.objects.create(
            quote_request=expired_request,
            damaged_part=self.damaged_part,
            provider_type='dealer',
            provider_name='Test Dealer',
            part_cost=Decimal('200.00'),
            labor_cost=Decimal('80.00'),
            total_cost=Decimal('280.00'),
            estimated_delivery_days=5,
            estimated_completion_days=7,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        # Run cleanup
        result = self.engine.cleanup_expired_quotes(days_old=30)
        
        self.assertGreater(result['expired_requests_updated'], 0)
        
        # Check request status updated
        expired_request.refresh_from_db()
        self.assertEqual(expired_request.status, 'expired')
    
    def test_get_quote_statistics(self):
        """Test quote statistics calculation"""
        # Create multiple quotes
        PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='assessor',
            provider_name='Internal Assessment',
            part_cost=Decimal('300.00'),
            labor_cost=Decimal('100.00'),
            total_cost=Decimal('400.00'),
            estimated_delivery_days=1,
            estimated_completion_days=3,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='dealer',
            provider_name='Toyota Dealer',
            part_cost=Decimal('450.00'),
            labor_cost=Decimal('120.00'),
            total_cost=Decimal('570.00'),
            estimated_delivery_days=3,
            estimated_completion_days=5,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        stats = self.engine.get_quote_statistics(self.assessment)
        
        self.assertIn('provider_statistics', stats)
        self.assertIn('overall_statistics', stats)
        self.assertIn('completion_status', stats)
        
        # Check provider stats
        self.assertIn('assessor', stats['provider_statistics'])
        self.assertIn('dealer', stats['provider_statistics'])
        
        # Check overall stats
        overall = stats['overall_statistics']
        self.assertEqual(overall['total_quotes'], 2)
        self.assertEqual(overall['min_total_cost'], 400.0)
        self.assertEqual(overall['max_total_cost'], 570.0)
        self.assertEqual(overall['cost_variance'], 170.0)


class QuoteCollectionIntegrationTestCase(TestCase):
    """Integration tests for quote collection workflow"""
    
    def setUp(self):
        """Set up integration test data"""
        self.user = User.objects.create_user(
            username='integrationtest',
            email='integration@test.com',
            password='testpass123'
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Honda',
            model='Civic',
            manufacture_year=2019,
            vin='2HGFC2F59KH123456'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            status='completed'
        )
        
        self.quote_extension = VehicleAssessmentQuoteExtension.objects.create(
            assessment=self.assessment,
            uses_parts_based_quotes=True,
            parts_identification_complete=True
        )
        
        self.engine = QuoteCollectionEngine()
    
    def test_full_quote_collection_workflow(self):
        """Test complete quote collection workflow"""
        # Create damaged parts
        front_bumper = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dents',
            estimated_labor_hours=Decimal('2.5')
        )
        
        headlight = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Headlight Assembly',
            part_category='electrical',
            damage_severity='replace',
            damage_description='Cracked lens',
            estimated_labor_hours=Decimal('1.0')
        )
        
        # Create quote requests
        bumper_request = PartQuoteRequest.objects.create(
            damaged_part=front_bumper,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            include_dealer=True,
            dispatched_by=self.user,
            status='sent'
        )
        
        headlight_request = PartQuoteRequest.objects.create(
            damaged_part=headlight,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            include_independent=True,
            dispatched_by=self.user,
            status='sent'
        )
        
        # Process quotes for bumper
        bumper_assessor_data = {
            'provider_type': 'assessor',
            'provider_name': 'Internal Assessment',
            'part_cost': '350.00',
            'labor_cost': '112.50',
            'total_cost': '462.50',
            'estimated_delivery_days': 1,
            'estimated_completion_days': 3,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        bumper_dealer_data = {
            'provider_type': 'dealer',
            'provider_name': 'Honda Authorized Dealer',
            'part_cost': '450.00',
            'labor_cost': '112.50',
            'total_cost': '562.50',
            'estimated_delivery_days': 3,
            'estimated_completion_days': 5,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        # Process quotes for headlight
        headlight_assessor_data = {
            'provider_type': 'assessor',
            'provider_name': 'Internal Assessment',
            'part_cost': '180.00',
            'labor_cost': '45.00',
            'total_cost': '225.00',
            'estimated_delivery_days': 1,
            'estimated_completion_days': 2,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        headlight_independent_data = {
            'provider_type': 'independent',
            'provider_name': 'Local Auto Parts',
            'part_cost': '150.00',
            'labor_cost': '45.00',
            'total_cost': '195.00',
            'estimated_delivery_days': 2,
            'estimated_completion_days': 3,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        # Process all quotes
        results = []
        for request_id, data in [
            (bumper_request.request_id, bumper_assessor_data),
            (bumper_request.request_id, bumper_dealer_data),
            (headlight_request.request_id, headlight_assessor_data),
            (headlight_request.request_id, headlight_independent_data),
        ]:
            result = self.engine.process_provider_response(request_id, data)
            results.append(result)
            self.assertTrue(result['success'], f"Failed to process quote: {result['errors']}")
        
        # Check completion status
        completion_status = self.engine.quote_completion_checker(self.assessment)
        self.assertTrue(completion_status['is_complete'])
        self.assertEqual(completion_status['received_quotes'], 4)
        self.assertEqual(completion_status['parts_with_quotes'], 2)
        
        # Check statistics
        stats = self.engine.get_quote_statistics(self.assessment)
        self.assertEqual(stats['overall_statistics']['total_quotes'], 4)
        self.assertIn('assessor', stats['provider_statistics'])
        self.assertIn('dealer', stats['provider_statistics'])
        self.assertIn('independent', stats['provider_statistics'])
        
        # Verify assessment status
        self.assessment.refresh_from_db()
        quote_ext = self.assessment.quote_extension
        self.assertEqual(quote_ext.quote_collection_status, 'completed')