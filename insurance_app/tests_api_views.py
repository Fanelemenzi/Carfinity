# tests_api_views.py
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from .models import (
    InsurancePolicy, Vehicle, DamagedPart, PartQuoteRequest, 
    PartQuote, PartMarketAverage, AssessmentQuoteSummary
)
from assessments.models import VehicleAssessment
from vehicles.models import Vehicle as VehicleModel
from organizations.models import Organization


class APIViewsTestCase(TestCase):
    """Test case for Parts-Based Quote System API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Insurance Co',
            is_insurance_provider=True
        )
        
        # Create test insurance policy
        self.policy = InsurancePolicy.objects.create(
            policy_number='TEST001',
            policy_holder=self.user,
            organization=self.organization,
            start_date='2024-01-01',
            end_date='2024-12-31',
            premium_amount=Decimal('1200.00')
        )
        
        # Create test vehicle
        self.vehicle_model = VehicleModel.objects.create(
            make='Toyota',
            model='Camry',
            manufacture_year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        self.vehicle = Vehicle.objects.create(
            policy=self.policy,
            vehicle=self.vehicle_model,
            purchase_date='2020-01-01',
            current_condition='good'
        )
        
        # Create test assessment
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='ASS001',
            user=self.user,
            vehicle=self.vehicle_model,
            status='completed',
            uses_parts_based_quotes=True
        )
        
        # Create test damaged part
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dents from minor collision',
            estimated_labor_hours=Decimal('2.5')
        )
    
    def test_damaged_parts_list(self):
        """Test listing damaged parts"""
        url = reverse('insurance:damaged-part-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['part_name'], 'Front Bumper')
    
    def test_damaged_parts_by_assessment(self):
        """Test getting damaged parts by assessment"""
        url = reverse('insurance:damaged-part-by-assessment')
        response = self.client.get(url, {'assessment_id': 'ASS001'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['parts']), 1)
        self.assertIn('summary', response.data)
        self.assertEqual(response.data['summary']['total_parts'], 1)
    
    def test_create_quote_request(self):
        """Test creating a quote request"""
        url = reverse('insurance:quote-request-list')
        data = {
            'damaged_part': self.damaged_part.id,
            'assessment': self.assessment.id,
            'expiry_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'include_assessor': True,
            'include_dealer': True,
            'include_independent': False,
            'include_network': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PartQuoteRequest.objects.filter(
            damaged_part=self.damaged_part
        ).exists())
    
    def test_batch_create_requests(self):
        """Test creating batch quote requests"""
        url = reverse('insurance:quote-request-create-batch-requests')
        data = {
            'assessment_id': 'ASS001',
            'part_ids': [self.damaged_part.id],
            'providers': {
                'include_assessor': True,
                'include_dealer': True,
                'include_independent': False,
                'include_network': False
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(PartQuoteRequest.objects.filter(
            damaged_part=self.damaged_part
        ).exists())
    
    def test_create_quote(self):
        """Test creating a quote"""
        # First create a quote request
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            dispatched_by=self.user
        )
        
        url = reverse('insurance:quote-list')
        data = {
            'quote_request': quote_request.id,
            'damaged_part': self.damaged_part.id,
            'provider_type': 'assessor',
            'provider_name': 'Internal Assessment',
            'part_cost': '450.00',
            'labor_cost': '112.50',
            'paint_cost': '67.50',
            'additional_costs': '0.00',
            'part_type': 'oem',
            'estimated_delivery_days': 3,
            'estimated_completion_days': 5,
            'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PartQuote.objects.filter(
            quote_request=quote_request
        ).exists())
    
    def test_quotes_by_request(self):
        """Test getting quotes by request ID"""
        # Create quote request and quote
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            dispatched_by=self.user
        )
        
        quote = PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=self.damaged_part,
            provider_type='assessor',
            provider_name='Internal Assessment',
            part_cost=Decimal('450.00'),
            labor_cost=Decimal('112.50'),
            paint_cost=Decimal('67.50'),
            additional_costs=Decimal('0.00'),
            total_cost=Decimal('630.00'),
            estimated_delivery_days=3,
            estimated_completion_days=5,
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        url = reverse('insurance:quote-by-request')
        response = self.client.get(url, {'request_id': quote_request.request_id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['quotes']), 1)
        self.assertIn('comparison', response.data)
    
    def test_validate_quote(self):
        """Test validating a quote"""
        # Create quote request and quote
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            dispatched_by=self.user
        )
        
        quote = PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=self.damaged_part,
            provider_type='assessor',
            provider_name='Internal Assessment',
            part_cost=Decimal('450.00'),
            labor_cost=Decimal('112.50'),
            paint_cost=Decimal('67.50'),
            additional_costs=Decimal('0.00'),
            total_cost=Decimal('630.00'),
            estimated_delivery_days=3,
            estimated_completion_days=5,
            valid_until=timezone.now() + timedelta(days=30),
            status='submitted'
        )
        
        url = reverse('insurance:quote-validate-quote', kwargs={'pk': quote.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        self.assertEqual(quote.status, 'validated')
    
    def test_market_average_calculation(self):
        """Test market average calculation"""
        # Create multiple quotes for market average calculation
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            dispatched_by=self.user
        )
        
        # Create multiple quotes
        for i, (provider, cost) in enumerate([
            ('assessor', '630.00'),
            ('dealer', '750.00'),
            ('independent', '580.00')
        ]):
            PartQuote.objects.create(
                quote_request=quote_request,
                damaged_part=self.damaged_part,
                provider_type=provider,
                provider_name=f'{provider.title()} Provider {i+1}',
                part_cost=Decimal(cost) * Decimal('0.7'),
                labor_cost=Decimal(cost) * Decimal('0.3'),
                total_cost=Decimal(cost),
                estimated_delivery_days=3,
                estimated_completion_days=5,
                valid_until=timezone.now() + timedelta(days=30),
                status='validated'
            )
        
        url = reverse('insurance:market-average-calculate-for-part')
        data = {'part_id': self.damaged_part.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('market_average', response.data)
        self.assertTrue(PartMarketAverage.objects.filter(
            damaged_part=self.damaged_part
        ).exists())
    
    def test_recommendation_generation(self):
        """Test recommendation generation"""
        # Create quotes for recommendation
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            include_assessor=True,
            dispatched_by=self.user
        )
        
        PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=self.damaged_part,
            provider_type='assessor',
            provider_name='Internal Assessment',
            part_cost=Decimal('450.00'),
            labor_cost=Decimal('112.50'),
            total_cost=Decimal('562.50'),
            estimated_delivery_days=3,
            estimated_completion_days=5,
            valid_until=timezone.now() + timedelta(days=30),
            status='validated'
        )
        
        url = reverse('insurance:recommendation-generate-for-part')
        data = {
            'part_id': self.damaged_part.id,
            'strategy': 'best_value'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendation', response.data)
    
    def test_available_strategies(self):
        """Test getting available recommendation strategies"""
        url = reverse('insurance:recommendation-available-strategies')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('strategies', response.data)
        self.assertTrue(len(response.data['strategies']) > 0)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access the API"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Try to access damaged parts with other user
        self.client.force_authenticate(user=other_user)
        url = reverse('insurance:damaged-part-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty results since other user has no parts
        self.assertEqual(len(response.data['results']), 0)
    
    def test_permission_denied_for_other_users_data(self):
        """Test that users cannot access other users' data"""
        # Create another user with their own data
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Try to create quote request for other user's assessment
        url = reverse('insurance:quote-request-list')
        data = {
            'damaged_part': self.damaged_part.id,
            'assessment': self.assessment.id,
            'expiry_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'include_assessor': True
        }
        
        self.client.force_authenticate(user=other_user)
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class APIEndpointIntegrationTest(TestCase):
    """Integration tests for API endpoint workflows"""
    
    def setUp(self):
        """Set up test data for integration tests"""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create complete test setup
        self.organization = Organization.objects.create(
            name='Integration Insurance Co',
            is_insurance_provider=True
        )
        
        self.policy = InsurancePolicy.objects.create(
            policy_number='INT001',
            policy_holder=self.user,
            organization=self.organization,
            start_date='2024-01-01',
            end_date='2024-12-31',
            premium_amount=Decimal('1500.00')
        )
        
        self.vehicle_model = VehicleModel.objects.create(
            make='Honda',
            model='Civic',
            manufacture_year=2019,
            vin='2HGFC2F59KH123456'
        )
        
        self.vehicle = Vehicle.objects.create(
            policy=self.policy,
            vehicle=self.vehicle_model,
            purchase_date='2019-01-01',
            current_condition='fair'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='INT001',
            user=self.user,
            vehicle=self.vehicle_model,
            status='completed',
            uses_parts_based_quotes=True
        )
    
    def test_complete_quote_workflow(self):
        """Test complete workflow from part identification to recommendation"""
        # 1. Create damaged part
        part_url = reverse('insurance:damaged-part-list')
        part_data = {
            'assessment': self.assessment.id,
            'section_type': 'exterior',
            'part_name': 'Rear Door Panel',
            'part_category': 'body',
            'damage_severity': 'severe',
            'damage_description': 'Large dent requiring replacement',
            'estimated_labor_hours': '4.0'
        }
        
        part_response = self.client.post(part_url, part_data, format='json')
        self.assertEqual(part_response.status_code, status.HTTP_201_CREATED)
        part_id = part_response.data['id']
        
        # 2. Create quote request
        request_url = reverse('insurance:quote-request-create-batch-requests')
        request_data = {
            'assessment_id': 'INT001',
            'part_ids': [part_id],
            'providers': {
                'include_assessor': True,
                'include_dealer': True,
                'include_independent': True,
                'include_network': False
            }
        }
        
        request_response = self.client.post(request_url, request_data, format='json')
        self.assertEqual(request_response.status_code, status.HTTP_200_OK)
        request_id = request_response.data['requests'][0]['request_id']
        
        # 3. Submit multiple quotes
        quote_url = reverse('insurance:quote-list')
        quotes_data = [
            {
                'provider_type': 'assessor',
                'provider_name': 'Internal Assessment',
                'part_cost': '800.00',
                'labor_cost': '180.00',
                'total_cost': '980.00'
            },
            {
                'provider_type': 'dealer',
                'provider_name': 'Honda Authorized Dealer',
                'part_cost': '950.00',
                'labor_cost': '200.00',
                'total_cost': '1150.00'
            },
            {
                'provider_type': 'independent',
                'provider_name': 'Local Body Shop',
                'part_cost': '720.00',
                'labor_cost': '160.00',
                'total_cost': '880.00'
            }
        ]
        
        quote_request = PartQuoteRequest.objects.get(request_id=request_id)
        
        for quote_data in quotes_data:
            quote_data.update({
                'quote_request': quote_request.id,
                'damaged_part': part_id,
                'estimated_delivery_days': 5,
                'estimated_completion_days': 7,
                'valid_until': (timezone.now() + timedelta(days=30)).isoformat()
            })
            
            quote_response = self.client.post(quote_url, quote_data, format='json')
            self.assertEqual(quote_response.status_code, status.HTTP_201_CREATED)
        
        # 4. Validate quotes
        quotes = PartQuote.objects.filter(quote_request=quote_request)
        for quote in quotes:
            validate_url = reverse('insurance:quote-validate-quote', kwargs={'pk': quote.id})
            validate_response = self.client.post(validate_url)
            self.assertEqual(validate_response.status_code, status.HTTP_200_OK)
        
        # 5. Calculate market average
        market_url = reverse('insurance:market-average-calculate-for-part')
        market_data = {'part_id': part_id}
        market_response = self.client.post(market_url, market_data, format='json')
        self.assertEqual(market_response.status_code, status.HTTP_200_OK)
        
        # 6. Generate recommendation
        recommendation_url = reverse('insurance:recommendation-generate-for-part')
        recommendation_data = {
            'part_id': part_id,
            'strategy': 'best_value'
        }
        recommendation_response = self.client.post(
            recommendation_url, recommendation_data, format='json'
        )
        self.assertEqual(recommendation_response.status_code, status.HTTP_200_OK)
        
        # Verify the complete workflow created all expected data
        self.assertTrue(DamagedPart.objects.filter(id=part_id).exists())
        self.assertTrue(PartQuoteRequest.objects.filter(request_id=request_id).exists())
        self.assertEqual(PartQuote.objects.filter(quote_request=quote_request).count(), 3)
        self.assertTrue(PartMarketAverage.objects.filter(damaged_part_id=part_id).exists())