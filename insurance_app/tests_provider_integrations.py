"""
Unit tests for provider integration framework.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
import requests

from .models import DamagedPart, PartQuoteRequest, PartQuote
from .provider_integrations import (
    ProviderIntegration, DealerIntegration, IndependentGarageIntegration,
    InsuranceNetworkIntegration, ProviderFactory,
    ProviderIntegrationError, ProviderAuthenticationError,
    ProviderCommunicationError, ProviderDataError
)
from assessments.models import VehicleAssessment
from vehicles.models import Vehicle


class MockProviderIntegration(ProviderIntegration):
    """Mock provider for testing base functionality."""
    
    def authenticate(self):
        return True
    
    def send_quote_request(self, quote_request):
        return {'status': 'sent', 'request_id': quote_request.request_id}
    
    def process_quote_response(self, response_data, quote_request):
        return PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=quote_request.damaged_part,
            provider_type='mock',
            provider_name='Mock Provider',
            part_cost=Decimal('100.00'),
            labor_cost=Decimal('50.00'),
            total_cost=Decimal('150.00'),
            estimated_delivery_days=5,
            estimated_completion_days=7,
            valid_until=timezone.now() + timedelta(days=30)
        )


class ProviderIntegrationBaseTest(TestCase):
    """Test base ProviderIntegration functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testassessor',
            email='assessor@test.com',
            first_name='Test',
            last_name='Assessor'
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            registration_number='ABC123',
            vin='1234567890ABCDEFG'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now(),
            uses_parts_based_quotes=True
        )
        
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_number='52119-06180',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dent on left side',
            requires_replacement=True,
            estimated_labor_hours=Decimal('2.5')
        )
        
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            request_id='REQ-TEST-001',
            expiry_date=timezone.now() + timedelta(days=7),
            vehicle_make=self.vehicle.make,
            vehicle_model=self.vehicle.model,
            vehicle_year=self.vehicle.year,
            dispatched_by=self.user,
            include_dealer=True
        )
    
    def test_format_request_data(self):
        """Test request data formatting."""
        provider = MockProviderIntegration()
        request_data = provider.format_request_data(self.quote_request)
        
        self.assertEqual(request_data['request_id'], 'REQ-TEST-001')
        self.assertEqual(request_data['vehicle']['make'], 'Toyota')
        self.assertEqual(request_data['vehicle']['model'], 'Camry')
        self.assertEqual(request_data['vehicle']['year'], 2020)
        self.assertEqual(request_data['part']['name'], 'Front Bumper')
        self.assertEqual(request_data['part']['category'], 'body')
        self.assertEqual(request_data['part']['damage_severity'], 'moderate')
        self.assertTrue(request_data['part']['requires_replacement'])
        self.assertEqual(request_data['part']['estimated_labor_hours'], 2.5)
    
    def test_validate_response_data_valid(self):
        """Test response data validation with valid data."""
        provider = MockProviderIntegration()
        
        valid_data = {
            'provider_name': 'Test Provider',
            'part_cost': '100.00',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7
        }
        
        self.assertTrue(provider.validate_response_data(valid_data))
    
    def test_validate_response_data_missing_fields(self):
        """Test response data validation with missing fields."""
        provider = MockProviderIntegration()
        
        invalid_data = {
            'provider_name': 'Test Provider',
            'part_cost': '100.00',
            # Missing required fields
        }
        
        self.assertFalse(provider.validate_response_data(invalid_data))
    
    def test_validate_response_data_invalid_numeric(self):
        """Test response data validation with invalid numeric values."""
        provider = MockProviderIntegration()
        
        invalid_data = {
            'provider_name': 'Test Provider',
            'part_cost': 'invalid',
            'labor_cost': '50.00',
            'total_cost': '150.00',
            'estimated_delivery_days': 5,
            'estimated_completion_days': 7
        }
        
        self.assertFalse(provider.validate_response_data(invalid_data))
    
    @patch('time.sleep')
    def test_retry_with_backoff_success(self, mock_sleep):
        """Test retry mechanism with successful execution."""
        provider = MockProviderIntegration({'max_retries': 2, 'retry_delay': 0.1})
        
        mock_func = Mock(return_value='success')
        result = provider.retry_with_backoff(mock_func, 'arg1', kwarg1='value1')
        
        self.assertEqual(result, 'success')
        mock_func.assert_called_once_with('arg1', kwarg1='value1')
        mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    def test_retry_with_backoff_eventual_success(self, mock_sleep):
        """Test retry mechanism with eventual success."""
        provider = MockProviderIntegration({'max_retries': 2, 'retry_delay': 0.1})
        
        mock_func = Mock(side_effect=[Exception('fail'), Exception('fail'), 'success'])
        result = provider.retry_with_backoff(mock_func)
        
        self.assertEqual(result, 'success')
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('time.sleep')
    def test_retry_with_backoff_all_fail(self, mock_sleep):
        """Test retry mechanism when all attempts fail."""
        provider = MockProviderIntegration({'max_retries': 2, 'retry_delay': 0.1})
        
        mock_func = Mock(side_effect=Exception('persistent failure'))
        
        with self.assertRaises(ProviderCommunicationError):
            provider.retry_with_backoff(mock_func)
        
        self.assertEqual(mock_func.call_count, 3)  # Initial + 2 retries
        self.assertEqual(mock_sleep.call_count, 2)


class DealerIntegrationTest(TestCase):
    """Test DealerIntegration functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testassessor',
            email='assessor@test.com'
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020
        )
        
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now()
        )
        
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage',
            estimated_labor_hours=Decimal('2.0')
        )
        
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            request_id='REQ-DEALER-001',
            expiry_date=timezone.now() + timedelta(days=7),
            vehicle_make=self.vehicle.make,
            vehicle_model=self.vehicle.model,
            vehicle_year=self.vehicle.year,
            dispatched_by=self.user
        )
    
    def test_authenticate_api_success(self):
        """Test successful API authentication."""
        config = {
            'api_endpoint': 'https://dealer-api.test.com',
            'api_key': 'test-api-key'
        }
        
        dealer = DealerIntegration(config)
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {'access_token': 'test-token'}
            mock_post.return_value = mock_response
            
            result = dealer.authenticate()
            
            self.assertTrue(result)
            self.assertEqual(dealer.access_token, 'test-token')
            mock_post.assert_called_once()
    
    def test_authenticate_email_success(self):
        """Test successful email configuration validation."""
        config = {
            'email_enabled': True,
            'dealer_email': 'dealer@test.com'
        }
        
        dealer = DealerIntegration(config)
        result = dealer.authenticate()
        
        self.assertTrue(result)
    
    def test_authenticate_email_invalid_format(self):
        """Test email authentication with invalid email format."""
        config = {
            'email_enabled': True,
            'dealer_email': 'invalid-email'
        }
        
        dealer = DealerIntegration(config)
        
        with self.assertRaises(ProviderAuthenticationError):
            dealer.authenticate()
    
    def test_send_api_request(self):
        """Test sending quote request via API."""
        config = {
            'api_endpoint': 'https://dealer-api.test.com',
            'api_key': 'test-api-key'
        }
        
        dealer = DealerIntegration(config)
        dealer.access_token = 'test-token'
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {'status': 'received', 'quote_id': 'Q123'}
            mock_post.return_value = mock_response
            
            result = dealer.send_quote_request(self.quote_request)
            
            self.assertEqual(result['status'], 'received')
            self.assertEqual(result['quote_id'], 'Q123')
            mock_post.assert_called_once()
    
    def test_send_email_request(self):
        """Test sending quote request via email."""
        config = {
            'email_enabled': True,
            'dealer_email': 'dealer@test.com'
        }
        
        dealer = DealerIntegration(config)
        
        result = dealer.send_quote_request(self.quote_request)
        
        self.assertEqual(result['status'], 'email_sent')
        self.assertEqual(result['recipient'], 'dealer@test.com')
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Parts Quote Request', mail.outbox[0].subject)
        self.assertIn('dealer@test.com', mail.outbox[0].to)
    
    def test_process_quote_response(self):
        """Test processing dealer quote response."""
        dealer = DealerIntegration()
        
        response_data = {
            'provider_name': 'Toyota Dealer',
            'contact_info': 'parts@toyotadealer.com',
            'part_cost': '250.00',
            'labor_cost': '112.50',
            'paint_cost': '37.50',
            'total_cost': '400.00',
            'part_type': 'oem',
            'estimated_delivery_days': 3,
            'estimated_completion_days': 5,
            'part_warranty_months': 24,
            'confidence_score': 90
        }
        
        quote = dealer.process_quote_response(response_data, self.quote_request)
        
        self.assertEqual(quote.provider_type, 'dealer')
        self.assertEqual(quote.provider_name, 'Toyota Dealer')
        self.assertEqual(quote.part_cost, Decimal('250.00'))
        self.assertEqual(quote.labor_cost, Decimal('112.50'))
        self.assertEqual(quote.paint_cost, Decimal('37.50'))
        self.assertEqual(quote.total_cost, Decimal('400.00'))
        self.assertEqual(quote.part_type, 'oem')
        self.assertEqual(quote.estimated_delivery_days, 3)
        self.assertEqual(quote.estimated_completion_days, 5)
        self.assertEqual(quote.part_warranty_months, 24)
        self.assertEqual(quote.confidence_score, 90)


class IndependentGarageIntegrationTest(TestCase):
    """Test IndependentGarageIntegration functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testassessor')
        self.vehicle = Vehicle.objects.create(make='Ford', model='Focus', year=2019)
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now()
        )
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Rear Light',
            part_category='electrical',
            damage_severity='severe',
            damage_description='Cracked lens',
            estimated_labor_hours=Decimal('1.0')
        )
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            request_id='REQ-GARAGE-001',
            expiry_date=timezone.now() + timedelta(days=7),
            vehicle_make=self.vehicle.make,
            vehicle_model=self.vehicle.model,
            vehicle_year=self.vehicle.year,
            dispatched_by=self.user
        )
    
    def test_authenticate_success(self):
        """Test successful platform authentication."""
        config = {
            'platform_url': 'https://garage-platform.test.com',
            'api_key': 'test-key',
            'partner_id': 'partner123'
        }
        
        garage = IndependentGarageIntegration(config)
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {'session_token': 'session123'}
            mock_post.return_value = mock_response
            
            result = garage.authenticate()
            
            self.assertTrue(result)
            self.assertEqual(garage.session_token, 'session123')
    
    def test_send_platform_request(self):
        """Test sending request to garage platform."""
        config = {
            'platform_url': 'https://garage-platform.test.com',
            'partner_id': 'partner123',
            'max_garages': 3
        }
        
        garage = IndependentGarageIntegration(config)
        garage.session_token = 'session123'
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {'request_id': 'REQ123', 'status': 'dispatched'}
            mock_post.return_value = mock_response
            
            result = garage.send_quote_request(self.quote_request)
            
            self.assertEqual(result['status'], 'dispatched')
            mock_post.assert_called_once()
    
    def test_process_multiple_quotes(self):
        """Test processing multiple garage quotes."""
        garage = IndependentGarageIntegration()
        
        response_data = {
            'quotes': [
                {
                    'provider_name': 'Garage A',
                    'part_cost': '80.00',
                    'labor_cost': '45.00',
                    'total_cost': '125.00',
                    'estimated_delivery_days': 2,
                    'estimated_completion_days': 3,
                    'part_type': 'aftermarket'
                },
                {
                    'provider_name': 'Garage B',
                    'part_cost': '75.00',
                    'labor_cost': '50.00',
                    'total_cost': '125.00',
                    'estimated_delivery_days': 1,
                    'estimated_completion_days': 2,
                    'part_type': 'oem_equivalent'
                }
            ]
        }
        
        quotes = garage.process_quote_response(response_data, self.quote_request)
        
        self.assertEqual(len(quotes), 2)
        self.assertEqual(quotes[0].provider_name, 'Garage A')
        self.assertEqual(quotes[1].provider_name, 'Garage B')
        self.assertEqual(quotes[0].part_type, 'aftermarket')
        self.assertEqual(quotes[1].part_type, 'oem_equivalent')


class InsuranceNetworkIntegrationTest(TestCase):
    """Test InsuranceNetworkIntegration functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testassessor')
        self.vehicle = Vehicle.objects.create(make='BMW', model='X3', year=2021)
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now()
        )
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Side Mirror',
            part_category='body',
            damage_severity='replace',
            damage_description='Mirror housing cracked',
            estimated_labor_hours=Decimal('0.5')
        )
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            request_id='REQ-NETWORK-001',
            expiry_date=timezone.now() + timedelta(days=7),
            vehicle_make=self.vehicle.make,
            vehicle_model=self.vehicle.model,
            vehicle_year=self.vehicle.year,
            dispatched_by=self.user
        )
    
    def test_authenticate_oauth_success(self):
        """Test successful OAuth authentication."""
        config = {
            'network_url': 'https://network.test.com',
            'client_id': 'client123',
            'client_secret': 'secret456'
        }
        
        network = InsuranceNetworkIntegration(config)
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'access_token': 'token123',
                'expires_in': 3600
            }
            mock_post.return_value = mock_response
            
            result = network.authenticate()
            
            self.assertTrue(result)
            self.assertEqual(network.access_token, 'token123')
            self.assertIsNotNone(network.token_expires)
    
    def test_send_network_request(self):
        """Test sending request to insurance network."""
        config = {
            'network_url': 'https://network.test.com',
            'network_id': 'net456'
        }
        
        network = InsuranceNetworkIntegration(config)
        network.access_token = 'token123'
        network.token_expires = datetime.now() + timedelta(hours=1)
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {'status': 'accepted', 'tracking_id': 'T789'}
            mock_post.return_value = mock_response
            
            result = network.send_quote_request(self.quote_request)
            
            self.assertEqual(result['status'], 'accepted')
            mock_post.assert_called_once()
    
    def test_process_network_quote(self):
        """Test processing insurance network quote."""
        network = InsuranceNetworkIntegration()
        
        response_data = {
            'provider_name': 'Network Provider',
            'part_cost': '150.00',
            'labor_cost': '22.50',
            'total_cost': '172.50',
            'part_type': 'oem_equivalent',
            'estimated_delivery_days': 2,
            'estimated_completion_days': 3,
            'part_warranty_months': 18,
            'confidence_score': 85
        }
        
        quote = network.process_quote_response(response_data, self.quote_request)
        
        self.assertEqual(quote.provider_type, 'network')
        self.assertEqual(quote.provider_name, 'Network Provider')
        self.assertEqual(quote.total_cost, Decimal('172.50'))
        self.assertEqual(quote.part_type, 'oem_equivalent')
        self.assertEqual(quote.part_warranty_months, 18)
        self.assertEqual(quote.confidence_score, 85)


class ProviderFactoryTest(TestCase):
    """Test ProviderFactory functionality."""
    
    def test_create_dealer_provider(self):
        """Test creating dealer provider."""
        config = {'api_endpoint': 'https://dealer.test.com'}
        provider = ProviderFactory.create_provider('dealer', config)
        
        self.assertIsInstance(provider, DealerIntegration)
        self.assertEqual(provider.config, config)
    
    def test_create_independent_provider(self):
        """Test creating independent garage provider."""
        config = {'platform_url': 'https://garage.test.com'}
        provider = ProviderFactory.create_provider('independent', config)
        
        self.assertIsInstance(provider, IndependentGarageIntegration)
        self.assertEqual(provider.config, config)
    
    def test_create_network_provider(self):
        """Test creating insurance network provider."""
        config = {'network_url': 'https://network.test.com'}
        provider = ProviderFactory.create_provider('network', config)
        
        self.assertIsInstance(provider, InsuranceNetworkIntegration)
        self.assertEqual(provider.config, config)
    
    def test_create_invalid_provider(self):
        """Test creating invalid provider type."""
        with self.assertRaises(ValueError):
            ProviderFactory.create_provider('invalid_type')
    
    def test_get_available_providers(self):
        """Test getting available provider types."""
        providers = ProviderFactory.get_available_providers()
        
        self.assertIn('dealer', providers)
        self.assertIn('independent', providers)
        self.assertIn('network', providers)
        self.assertEqual(len(providers), 3)


class ProviderIntegrationErrorTest(TestCase):
    """Test provider integration error handling."""
    
    def test_provider_integration_error(self):
        """Test base provider integration error."""
        error = ProviderIntegrationError("Test error")
        self.assertEqual(str(error), "Test error")
    
    def test_provider_authentication_error(self):
        """Test provider authentication error."""
        error = ProviderAuthenticationError("Auth failed")
        self.assertIsInstance(error, ProviderIntegrationError)
        self.assertEqual(str(error), "Auth failed")
    
    def test_provider_communication_error(self):
        """Test provider communication error."""
        error = ProviderCommunicationError("Communication failed")
        self.assertIsInstance(error, ProviderIntegrationError)
        self.assertEqual(str(error), "Communication failed")
    
    def test_provider_data_error(self):
        """Test provider data error."""
        error = ProviderDataError("Invalid data")
        self.assertIsInstance(error, ProviderIntegrationError)
        self.assertEqual(str(error), "Invalid data")