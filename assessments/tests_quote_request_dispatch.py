"""
Tests for Quote Request Dispatch Interface
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from assessments.models import VehicleAssessment
from insurance_app.models import DamagedPart, PartQuoteRequest
from insurance_app.quote_managers import PartQuoteRequestManager
from vehicles.models import Vehicle


class QuoteRequestDispatchTestCase(TestCase):
    """Test cases for quote request dispatch interface"""
    
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
            vin='1234567890ABCDEFG'
        )
        
        # Create test assessment
        self.assessment = VehicleAssessment.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            assessment_id='TEST-001',
            status='completed',
            uses_parts_based_quotes=True
        )
        
        # Create test damaged parts
        self.damaged_part1 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dents on front bumper',
            estimated_labor_hours=2.5
        )
        
        self.damaged_part2 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='mechanical',
            part_name='Brake Pads',
            part_category='mechanical',
            damage_severity='replace',
            damage_description='Worn brake pads need replacement',
            estimated_labor_hours=1.0
        )
        
        # Initialize quote manager
        self.quote_manager = PartQuoteRequestManager()
    
    def test_quote_request_dispatch_view_get(self):
        """Test GET request to quote request dispatch view"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quote Request Dispatch')
        self.assertContains(response, self.assessment.assessment_id)
        self.assertContains(response, 'Front Bumper')
        self.assertContains(response, 'Brake Pads')
    
    def test_quote_request_dispatch_post_valid(self):
        """Test POST request with valid data"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        data = {
            'action': 'dispatch_quotes',
            'selected_parts': [self.damaged_part1.id, self.damaged_part2.id],
            'include_assessor': 'on',
            'include_dealer': 'on',
        }
        
        response = self.client.post(url, data)
        
        # Should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        
        # Check that quote requests were created
        quote_requests = PartQuoteRequest.objects.filter(assessment=self.assessment)
        self.assertEqual(quote_requests.count(), 2)
        
        # Check provider selection
        for request in quote_requests:
            self.assertTrue(request.include_assessor)
            self.assertTrue(request.include_dealer)
            self.assertFalse(request.include_independent)
            self.assertFalse(request.include_network)
    
    def test_quote_request_dispatch_post_no_providers(self):
        """Test POST request with no providers selected"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        data = {
            'action': 'dispatch_quotes',
            'selected_parts': [self.damaged_part1.id],
            # No providers selected
        }
        
        response = self.client.post(url, data)
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # No quote requests should be created
        quote_requests = PartQuoteRequest.objects.filter(assessment=self.assessment)
        self.assertEqual(quote_requests.count(), 0)
    
    def test_quote_request_dispatch_post_no_parts(self):
        """Test POST request with no parts selected"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        data = {
            'action': 'dispatch_quotes',
            'selected_parts': [],  # No parts selected
            'include_assessor': 'on',
        }
        
        response = self.client.post(url, data)
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # No quote requests should be created
        quote_requests = PartQuoteRequest.objects.filter(assessment=self.assessment)
        self.assertEqual(quote_requests.count(), 0)
    
    def test_quote_request_cancel(self):
        """Test cancelling a quote request"""
        # Create a quote request first
        quote_request = self.quote_manager.create_quote_request(
            damaged_part=self.damaged_part1,
            dispatched_by=self.user,
            include_assessor=True
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        data = {
            'action': 'cancel_request',
            'request_id': quote_request.request_id,
        }
        
        response = self.client.post(url, data)
        
        # Should redirect back to the same page
        self.assertEqual(response.status_code, 302)
        
        # Check that request was cancelled
        quote_request.refresh_from_db()
        self.assertEqual(quote_request.status, 'cancelled')
    
    def test_ajax_request_handling(self):
        """Test AJAX request handling"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        data = {
            'action': 'dispatch_quotes',
            'selected_parts': [self.damaged_part1.id],
            'include_assessor': 'on',
        }
        
        response = self.client.post(
            url, 
            data, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Should return JSON response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Parse JSON response
        import json
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('message', response_data)
    
    def test_provider_performance_display(self):
        """Test that provider performance data is displayed"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assessor Estimate')
        self.assertContains(response, 'Authorized Dealers')
        self.assertContains(response, 'Independent Garages')
        self.assertContains(response, 'Insurance Networks')
        self.assertContains(response, 'Reliable')  # Performance indicators
    
    def test_request_history_display(self):
        """Test that request history is displayed"""
        # Create some quote requests
        request1 = self.quote_manager.create_quote_request(
            damaged_part=self.damaged_part1,
            dispatched_by=self.user,
            include_assessor=True
        )
        
        request2 = self.quote_manager.create_quote_request(
            damaged_part=self.damaged_part2,
            dispatched_by=self.user,
            include_dealer=True,
            include_independent=True
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, request1.request_id)
        self.assertContains(response, request2.request_id)
        self.assertContains(response, 'Front Bumper')
        self.assertContains(response, 'Brake Pads')
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access the view"""
        # Don't login
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_wrong_user_access(self):
        """Test that users cannot access other users' assessments"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.client.login(username='otheruser', password='otherpass123')
        
        url = reverse('assessments:quote_request_dispatch', args=[self.assessment.id])
        response = self.client.get(url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)


class PartQuoteRequestManagerTestCase(TestCase):
    """Test cases for PartQuoteRequestManager"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Honda',
            model='Civic',
            manufacture_year=2019,
            vin='ABCDEFG1234567890'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            assessment_id='TEST-002',
            status='completed'
        )
        
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Side Mirror',
            part_category='body',
            damage_severity='replace',
            damage_description='Broken side mirror',
            estimated_labor_hours=0.5
        )
        
        self.quote_manager = PartQuoteRequestManager()
    
    def test_create_quote_request_success(self):
        """Test successful quote request creation"""
        quote_request = self.quote_manager.create_quote_request(
            damaged_part=self.damaged_part,
            dispatched_by=self.user,
            include_assessor=True,
            include_dealer=True
        )
        
        self.assertIsNotNone(quote_request)
        self.assertEqual(quote_request.damaged_part, self.damaged_part)
        self.assertEqual(quote_request.assessment, self.assessment)
        self.assertEqual(quote_request.dispatched_by, self.user)
        self.assertTrue(quote_request.include_assessor)
        self.assertTrue(quote_request.include_dealer)
        self.assertFalse(quote_request.include_independent)
        self.assertFalse(quote_request.include_network)
        self.assertEqual(quote_request.status, 'draft')
    
    def test_create_quote_request_no_providers(self):
        """Test quote request creation with no providers selected"""
        from django.core.exceptions import ValidationError
        
        with self.assertRaises(ValidationError):
            self.quote_manager.create_quote_request(
                damaged_part=self.damaged_part,
                dispatched_by=self.user
                # No providers selected
            )
    
    def test_create_quote_request_duplicate(self):
        """Test creating duplicate quote request for same part"""
        from django.core.exceptions import ValidationError
        
        # Create first request
        self.quote_manager.create_quote_request(
            damaged_part=self.damaged_part,
            dispatched_by=self.user,
            include_assessor=True
        )
        
        # Try to create duplicate
        with self.assertRaises(ValidationError):
            self.quote_manager.create_quote_request(
                damaged_part=self.damaged_part,
                dispatched_by=self.user,
                include_dealer=True
            )
    
    def test_expiry_date_calculation(self):
        """Test that expiry date is calculated correctly"""
        quote_request = self.quote_manager.create_quote_request(
            damaged_part=self.damaged_part,
            dispatched_by=self.user,
            include_assessor=True,
            expiry_days=5
        )
        
        expected_expiry = timezone.now() + timedelta(days=5)
        
        # Allow for small time differences in test execution
        time_diff = abs((quote_request.expiry_date - expected_expiry).total_seconds())
        self.assertLess(time_diff, 60)  # Within 1 minute