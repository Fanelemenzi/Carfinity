from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import VehicleAssessment
from vehicles.models import Vehicle
from insurance_app.models import (
    DamagedPart, PartQuote, PartQuoteRequest, PartMarketAverage, AssessmentQuoteSummary
)


class QuoteSummaryViewTest(TestCase):
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
            make='Toyota',
            model='Camry',
            manufacture_year=2020,
            vin='1234567890ABCDEFG',
            registration_number='ABC123'
        )
        
        # Create test assessment
        self.assessment = VehicleAssessment.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            assessment_id='TEST-001',
            status='completed',
            uses_parts_based_quotes=True,
            parts_identification_complete=True,
            quote_collection_status='completed'
        )
        
        # Create damaged parts
        self.damaged_part1 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dents',
            estimated_labor_hours=Decimal('2.5')
        )
        
        self.damaged_part2 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Headlight Assembly',
            part_category='electrical',
            damage_severity='replace',
            damage_description='Cracked lens',
            estimated_labor_hours=Decimal('1.0')
        )
        
        # Create quote requests
        self.quote_request1 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            request_id='QR-001',
            expiry_date=timezone.now() + timedelta(days=7),
            status='received',
            include_assessor=True,
            include_dealer=True,
            dispatched_by=self.user,
            dispatched_at=timezone.now()
        )
        
        self.quote_request2 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part2,
            assessment=self.assessment,
            request_id='QR-002',
            expiry_date=timezone.now() + timedelta(days=7),
            status='received',
            include_assessor=True,
            include_independent=True,
            dispatched_by=self.user,
            dispatched_at=timezone.now()
        )
        
        # Create quotes
        self.quote1_assessor = PartQuote.objects.create(
            quote_request=self.quote_request1,
            damaged_part=self.damaged_part1,
            provider_type='assessor',
            provider_name='Internal Assessor',
            part_cost=Decimal('300.00'),
            labor_cost=Decimal('112.50'),  # 2.5 hours * £45
            paint_cost=Decimal('45.00'),   # 15% of part cost
            total_cost=Decimal('457.50'),
            part_type='oem_equivalent',
            estimated_delivery_days=3,
            estimated_completion_days=5,
            valid_until=timezone.now() + timedelta(days=30),
            status='validated'
        )
        
        self.quote1_dealer = PartQuote.objects.create(
            quote_request=self.quote_request1,
            damaged_part=self.damaged_part1,
            provider_type='dealer',
            provider_name='Toyota Dealer',
            part_cost=Decimal('450.00'),
            labor_cost=Decimal('112.50'),
            paint_cost=Decimal('67.50'),
            total_cost=Decimal('630.00'),
            part_type='oem',
            estimated_delivery_days=5,
            estimated_completion_days=7,
            valid_until=timezone.now() + timedelta(days=30),
            status='validated'
        )
        
        self.quote2_assessor = PartQuote.objects.create(
            quote_request=self.quote_request2,
            damaged_part=self.damaged_part2,
            provider_type='assessor',
            provider_name='Internal Assessor',
            part_cost=Decimal('150.00'),
            labor_cost=Decimal('45.00'),   # 1 hour * £45
            total_cost=Decimal('195.00'),
            part_type='oem_equivalent',
            estimated_delivery_days=2,
            estimated_completion_days=3,
            valid_until=timezone.now() + timedelta(days=30),
            status='validated'
        )
        
        self.quote2_independent = PartQuote.objects.create(
            quote_request=self.quote_request2,
            damaged_part=self.damaged_part2,
            provider_type='independent',
            provider_name='Local Garage',
            part_cost=Decimal('120.00'),
            labor_cost=Decimal('40.00'),   # Slightly lower rate
            total_cost=Decimal('160.00'),
            part_type='aftermarket',
            estimated_delivery_days=3,
            estimated_completion_days=4,
            valid_until=timezone.now() + timedelta(days=30),
            status='validated'
        )
        
        # Create market averages
        self.market_avg1 = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part1,
            average_total_cost=Decimal('543.75'),  # Average of 457.50 and 630.00
            average_part_cost=Decimal('375.00'),
            average_labor_cost=Decimal('112.50'),
            min_total_cost=Decimal('457.50'),
            max_total_cost=Decimal('630.00'),
            standard_deviation=Decimal('86.25'),
            variance_percentage=Decimal('15.86'),
            quote_count=2,
            confidence_level=75
        )
        
        self.market_avg2 = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part2,
            average_total_cost=Decimal('177.50'),  # Average of 195.00 and 160.00
            average_part_cost=Decimal('135.00'),
            average_labor_cost=Decimal('42.50'),
            min_total_cost=Decimal('160.00'),
            max_total_cost=Decimal('195.00'),
            standard_deviation=Decimal('17.50'),
            variance_percentage=Decimal('9.86'),
            quote_count=2,
            confidence_level=80
        )
        
        # Create assessment quote summary
        self.quote_summary = AssessmentQuoteSummary.objects.create(
            assessment=self.assessment,
            status='ready',
            total_parts_identified=2,
            parts_with_quotes=2,
            total_quote_requests=2,
            quotes_received=4,
            assessor_total=Decimal('652.50'),  # 457.50 + 195.00
            dealer_total=Decimal('630.00'),    # Only part 1 has dealer quote
            independent_total=Decimal('160.00'), # Only part 2 has independent quote
            market_average_total=Decimal('721.25'), # 543.75 + 177.50
            potential_savings=Decimal('68.75')  # Difference between highest and lowest
        )
    
    def test_quote_summary_view_get(self):
        """Test GET request to quote summary view"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quote Summary')
        self.assertContains(response, self.assessment.assessment_id)
        self.assertContains(response, 'Front Bumper')
        self.assertContains(response, 'Headlight Assembly')
        
        # Check context data
        self.assertEqual(response.context['assessment'], self.assessment)
        self.assertEqual(response.context['quote_summary'], self.quote_summary)
        self.assertEqual(len(response.context['parts_comparison']), 2)
        self.assertGreater(response.context['completion_percentage'], 0)
    
    def test_quote_summary_parts_comparison_data(self):
        """Test parts comparison data structure"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        response = self.client.get(url)
        
        parts_comparison = response.context['parts_comparison']
        
        # Check first part (Front Bumper)
        part1_data = parts_comparison[0]
        self.assertEqual(part1_data['part'], self.damaged_part1)
        self.assertEqual(part1_data['market_average'], self.market_avg1)
        self.assertEqual(part1_data['best_quote'], self.quote1_assessor)  # Lowest cost
        
        # Check provider quotes structure
        provider_quotes = part1_data['provider_quotes']
        self.assertEqual(len(provider_quotes), 4)  # assessor, dealer, independent, network
        
        # Find assessor quote
        assessor_quote_data = next(pq for pq in provider_quotes if pq['provider_type'] == 'assessor')
        self.assertEqual(assessor_quote_data['quote'], self.quote1_assessor)
        self.assertFalse(assessor_quote_data['is_outlier'])
        
        # Find dealer quote
        dealer_quote_data = next(pq for pq in provider_quotes if pq['provider_type'] == 'dealer')
        self.assertEqual(dealer_quote_data['quote'], self.quote1_dealer)
    
    def test_quote_summary_provider_variances(self):
        """Test provider variance calculations"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        response = self.client.get(url)
        
        # Check that variance data is calculated
        context = response.context
        
        # Assessor should be below market average
        if 'assessor_variance' in context:
            assessor_var = context['assessor_variance']
            self.assertEqual(assessor_var['direction'], 'below')
            self.assertEqual(assessor_var['class'], 'success')
    
    def test_quote_finalization_post(self):
        """Test POST request to finalize quotes"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        
        post_data = {
            'action': 'finalize_quotes',
            'selection_strategy': 'lowest_cost',
            'priority_factor': 'cost_focused'
        }
        
        response = self.client.post(url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        
        # Check JSON response
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('redirect_url', data)
        
        # Check that quote summary was updated
        self.quote_summary.refresh_from_db()
        self.assertEqual(self.quote_summary.status, 'approved')
        self.assertEqual(self.quote_summary.completed_by, self.user)
        
        # Check that assessment status was updated
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.quote_collection_status, 'completed')
    
    def test_part_details_api(self):
        """Test part details API endpoint"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:part_details_api', args=[self.assessment.id, self.damaged_part1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['part_name'], 'Front Bumper')
        self.assertEqual(data['part_category'], 'Body Panel')
        self.assertEqual(data['damage_severity'], 'Moderate Damage')
        self.assertEqual(len(data['quotes']), 2)  # Assessor and dealer quotes
    
    def test_quote_status_refresh_api(self):
        """Test quote status refresh API endpoint"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_status_refresh_api', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('updated', data)
        self.assertIn('last_updated', data)
        self.assertIn('status', data)
        self.assertIn('completion_percentage', data)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access quote summary"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        self.client.login(username='otheruser', password='otherpass123')
        
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)  # Should not find assessment for other user
    
    def test_quote_summary_without_login(self):
        """Test that login is required"""
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)


class QuoteSummaryIntegrationTest(TestCase):
    """Integration tests for quote summary functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Honda',
            model='Civic',
            manufacture_year=2019,
            vin='9876543210ZYXWVUT',
            registration_number='XYZ789'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            assessment_id='INT-TEST-001',
            status='completed',
            uses_parts_based_quotes=True
        )
    
    def test_quote_summary_creation_on_first_access(self):
        """Test that quote summary is created on first access"""
        self.client.login(username='testuser', password='testpass123')
        
        # Ensure no quote summary exists
        self.assertFalse(
            AssessmentQuoteSummary.objects.filter(assessment=self.assessment).exists()
        )
        
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that quote summary was created
        self.assertTrue(
            AssessmentQuoteSummary.objects.filter(assessment=self.assessment).exists()
        )
        
        quote_summary = AssessmentQuoteSummary.objects.get(assessment=self.assessment)
        self.assertEqual(quote_summary.status, 'collecting')
    
    def test_empty_quote_summary_display(self):
        """Test quote summary display with no parts or quotes"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_summary', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No damaged parts identified yet')
        
        # Check completion percentage is 0
        self.assertEqual(response.context['completion_percentage'], 0)