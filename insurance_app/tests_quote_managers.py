# tests_quote_managers.py
"""
Unit tests for the PartQuoteRequestManager class.

Tests cover all methods including creation, validation, status updates,
batch operations, and query methods.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from assessments.models import VehicleAssessment
from vehicles.models import Vehicle
from .models import DamagedPart, PartQuoteRequest
from .quote_managers import PartQuoteRequestManager


class PartQuoteRequestManagerTestCase(TestCase):
    """Test cases for PartQuoteRequestManager"""
    
    def setUp(self):
        """Set up test data"""
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
            year=2020,
            vin='1HGBH41JXMN109186',
            registration='ABC123'
        )
        
        # Create test assessment
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            created_by=self.user,
            assigned_to=self.user,
            assessment_type='comprehensive',
            status='in_progress'
        )
        
        # Create test damaged parts
        self.damaged_part1 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dents from minor collision',
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
        
        # Initialize manager
        self.manager = PartQuoteRequestManager()
    
    def test_create_quote_requests_success(self):
        """Test successful creation of quote requests"""
        provider_selection = {
            'assessor': True,
            'dealer': True,
            'independent': False,
            'network': False
        }
        
        requests = self.manager.create_quote_requests(
            assessment=self.assessment,
            provider_selection=provider_selection,
            expiry_days=7
        )
        
        # Should create requests for both damaged parts
        self.assertEqual(len(requests), 2)
        
        # Check first request
        request1 = requests[0]
        self.assertEqual(request1.damaged_part, self.damaged_part1)
        self.assertEqual(request1.assessment, self.assessment)
        self.assertTrue(request1.include_assessor)
        self.assertTrue(request1.include_dealer)
        self.assertFalse(request1.include_independent)
        self.assertFalse(request1.include_network)
        self.assertEqual(request1.status, 'draft')
        self.assertEqual(request1.vehicle_make, 'Toyota')
        self.assertEqual(request1.vehicle_model, 'Camry')
        self.assertEqual(request1.vehicle_year, 2020)
        
        # Check expiry date is approximately 7 days from now
        expected_expiry = timezone.now() + timedelta(days=7)
        self.assertAlmostEqual(
            request1.expiry_date.timestamp(),
            expected_expiry.timestamp(),
            delta=60  # Within 1 minute
        )
    
    def test_create_quote_requests_specific_parts(self):
        """Test creating requests for specific parts only"""
        provider_selection = {'assessor': True}
        
        requests = self.manager.create_quote_requests(
            assessment=self.assessment,
            damaged_parts=[self.damaged_part1],
            provider_selection=provider_selection
        )
        
        # Should create request for only the specified part
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].damaged_part, self.damaged_part1)
    
    def test_create_quote_requests_no_parts(self):
        """Test error when no damaged parts exist"""
        # Create assessment with no damaged parts
        empty_assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            created_by=self.user,
            assessment_type='basic',
            status='draft'
        )
        
        provider_selection = {'assessor': True}
        
        with self.assertRaises(ValueError) as context:
            self.manager.create_quote_requests(
                assessment=empty_assessment,
                provider_selection=provider_selection
            )
        
        self.assertIn("No damaged parts found", str(context.exception))
    
    def test_create_quote_requests_default_provider_selection(self):
        """Test creation with default provider selection"""
        requests = self.manager.create_quote_requests(
            assessment=self.assessment
        )
        
        # Should use default selection (assessor only)
        self.assertEqual(len(requests), 2)
        for request in requests:
            self.assertTrue(request.include_assessor)
            self.assertFalse(request.include_dealer)
            self.assertFalse(request.include_independent)
            self.assertFalse(request.include_network)
    
    def test_create_quote_requests_duplicate_prevention(self):
        """Test that duplicate requests are not created"""
        provider_selection = {'assessor': True}
        
        # Create first set of requests
        requests1 = self.manager.create_quote_requests(
            assessment=self.assessment,
            provider_selection=provider_selection
        )
        self.assertEqual(len(requests1), 2)
        
        # Try to create again - should skip existing requests
        with patch('insurance_app.quote_managers.logger') as mock_logger:
            requests2 = self.manager.create_quote_requests(
                assessment=self.assessment,
                provider_selection=provider_selection
            )
            
            # Should create no new requests
            self.assertEqual(len(requests2), 0)
            
            # Should log warnings about existing requests
            self.assertEqual(mock_logger.warning.call_count, 2)
    
    def test_validate_provider_selection_valid(self):
        """Test validation of valid provider selections"""
        valid_selections = [
            {'assessor': True},
            {'dealer': True, 'independent': True},
            {'assessor': True, 'dealer': True, 'independent': True, 'network': True},
            {'network': True}
        ]
        
        for selection in valid_selections:
            with self.subTest(selection=selection):
                result = self.manager.validate_provider_selection(selection)
                self.assertTrue(result)
    
    def test_validate_provider_selection_invalid(self):
        """Test validation of invalid provider selections"""
        invalid_selections = [
            {},  # No providers selected
            {'assessor': False, 'dealer': False},  # All false
            {'invalid_provider': True},  # Invalid provider type
            {'assessor': True, 'invalid': True},  # Mix of valid and invalid
            "not_a_dict",  # Not a dictionary
        ]
        
        for selection in invalid_selections:
            with self.subTest(selection=selection):
                with self.assertRaises(ValidationError):
                    self.manager.validate_provider_selection(selection)
    
    def test_update_request_status_success(self):
        """Test successful status update"""
        # Create a request first
        request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7)
        )
        
        # Update status
        updated_request = self.manager.update_request_status(
            request_id=request.request_id,
            new_status='pending'
        )
        
        self.assertEqual(updated_request.status, 'pending')
        self.assertEqual(updated_request.id, request.id)
    
    def test_update_request_status_with_dispatch_timestamp(self):
        """Test that dispatch timestamp is set when status changes to 'sent'"""
        request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='pending'
        )
        
        # Update to 'sent' status
        updated_request = self.manager.update_request_status(
            request_id=request.request_id,
            new_status='sent'
        )
        
        self.assertEqual(updated_request.status, 'sent')
        self.assertIsNotNone(updated_request.dispatched_at)
        self.assertAlmostEqual(
            updated_request.dispatched_at.timestamp(),
            timezone.now().timestamp(),
            delta=5  # Within 5 seconds
        )
    
    def test_update_request_status_not_found(self):
        """Test error when request ID not found"""
        with self.assertRaises(PartQuoteRequest.DoesNotExist):
            self.manager.update_request_status(
                request_id='nonexistent-id',
                new_status='pending'
            )
    
    def test_update_request_status_invalid_transition(self):
        """Test error for invalid status transitions"""
        request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='cancelled'  # Terminal state
        )
        
        with self.assertRaises(ValidationError) as context:
            self.manager.update_request_status(
                request_id=request.request_id,
                new_status='pending'
            )
        
        self.assertIn("Invalid status transition", str(context.exception))
    
    def test_batch_create_requests_success(self):
        """Test successful batch creation of requests"""
        # Create second assessment
        assessment2 = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            created_by=self.user,
            assessment_type='basic',
            status='draft'
        )
        
        # Add damaged part to second assessment
        DamagedPart.objects.create(
            assessment=assessment2,
            section_type='interior',
            part_name='Dashboard',
            part_category='interior',
            damage_severity='minor',
            damage_description='Scratch on dashboard',
            estimated_labor_hours=0.5
        )
        
        provider_selection = {'assessor': True, 'dealer': True}
        
        results = self.manager.batch_create_requests(
            assessments=[self.assessment, assessment2],
            provider_selection=provider_selection,
            expiry_days=5
        )
        
        # Should have results for both assessments
        self.assertEqual(len(results), 2)
        self.assertIn(self.assessment.assessment_id, results)
        self.assertIn(assessment2.assessment_id, results)
        
        # First assessment should have 2 requests
        self.assertEqual(len(results[self.assessment.assessment_id]), 2)
        
        # Second assessment should have 1 request
        self.assertEqual(len(results[assessment2.assessment_id]), 1)
    
    def test_batch_create_requests_with_errors(self):
        """Test batch creation with some failures"""
        # Create assessment with no damaged parts (will cause error)
        empty_assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            created_by=self.user,
            assessment_type='basic',
            status='draft'
        )
        
        provider_selection = {'assessor': True}
        
        with patch('insurance_app.quote_managers.logger') as mock_logger:
            results = self.manager.batch_create_requests(
                assessments=[self.assessment, empty_assessment],
                provider_selection=provider_selection
            )
            
            # Should have result for successful assessment only
            self.assertEqual(len(results), 1)
            self.assertIn(self.assessment.assessment_id, results)
            self.assertNotIn(empty_assessment.assessment_id, results)
            
            # Should log error for failed assessment
            mock_logger.error.assert_called()
            mock_logger.warning.assert_called()
    
    def test_get_pending_requests(self):
        """Test getting pending requests"""
        # Create requests with different statuses
        request1 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='draft'
        )
        
        request2 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part2,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='sent'
        )
        
        # Create completed request (should not be included)
        PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='received'
        )
        
        pending_requests = self.manager.get_pending_requests()
        
        # Should return only draft and sent requests
        self.assertEqual(pending_requests.count(), 2)
        request_ids = [r.request_id for r in pending_requests]
        self.assertIn(request1.request_id, request_ids)
        self.assertIn(request2.request_id, request_ids)
    
    def test_get_pending_requests_filtered(self):
        """Test getting pending requests with filters"""
        # Create second assessment
        assessment2 = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            created_by=self.user,
            assessment_type='basic',
            status='draft'
        )
        
        part2 = DamagedPart.objects.create(
            assessment=assessment2,
            section_type='exterior',
            part_name='Rear Bumper',
            part_category='body',
            damage_severity='severe',
            damage_description='Damage from collision',
            estimated_labor_hours=3.0
        )
        
        # Create requests for both assessments
        request1 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='draft'
        )
        
        PartQuoteRequest.objects.create(
            damaged_part=part2,
            assessment=assessment2,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='pending'
        )
        
        # Filter by assessment
        filtered_requests = self.manager.get_pending_requests(assessment=self.assessment)
        self.assertEqual(filtered_requests.count(), 1)
        self.assertEqual(filtered_requests.first().request_id, request1.request_id)
        
        # Filter by user
        user_requests = self.manager.get_pending_requests(user=self.user)
        self.assertEqual(user_requests.count(), 2)
    
    def test_get_expired_requests(self):
        """Test getting expired requests"""
        # Create expired request
        expired_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() - timedelta(days=1),  # Expired
            status='sent'
        )
        
        # Create non-expired request
        PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part2,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),  # Not expired
            status='sent'
        )
        
        # Create already marked as expired (should not be included)
        PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() - timedelta(days=2),
            status='expired'
        )
        
        expired_requests = self.manager.get_expired_requests()
        
        # Should return only the expired request that's not marked as expired
        self.assertEqual(expired_requests.count(), 1)
        self.assertEqual(expired_requests.first().request_id, expired_request.request_id)
    
    def test_cleanup_expired_requests(self):
        """Test cleanup of expired requests"""
        # Create expired requests
        expired1 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() - timedelta(days=1),
            status='sent'
        )
        
        expired2 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part2,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() - timedelta(days=2),
            status='pending'
        )
        
        # Run cleanup
        count = self.manager.cleanup_expired_requests()
        
        # Should mark 2 requests as expired
        self.assertEqual(count, 2)
        
        # Verify requests are marked as expired
        expired1.refresh_from_db()
        expired2.refresh_from_db()
        self.assertEqual(expired1.status, 'expired')
        self.assertEqual(expired2.status, 'expired')
    
    def test_get_request_statistics(self):
        """Test getting request statistics"""
        # Create requests with various statuses
        PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='draft'
        )
        
        PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part2,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='sent'
        )
        
        PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='received'
        )
        
        stats = self.manager.get_request_statistics()
        
        expected_stats = {
            'total': 3,
            'draft': 1,
            'pending': 0,
            'sent': 1,
            'received': 1,
            'expired': 0,
            'cancelled': 0,
        }
        
        self.assertEqual(stats, expected_stats)
    
    def test_get_request_statistics_filtered(self):
        """Test getting statistics filtered by assessment"""
        # Create second assessment with request
        assessment2 = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            created_by=self.user,
            assessment_type='basic',
            status='draft'
        )
        
        part2 = DamagedPart.objects.create(
            assessment=assessment2,
            section_type='exterior',
            part_name='Side Mirror',
            part_category='body',
            damage_severity='replace',
            damage_description='Broken mirror',
            estimated_labor_hours=1.0
        )
        
        # Create requests for both assessments
        PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part1,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='draft'
        )
        
        PartQuoteRequest.objects.create(
            damaged_part=part2,
            assessment=assessment2,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7),
            status='sent'
        )
        
        # Get stats for specific assessment
        stats = self.manager.get_request_statistics(assessment=self.assessment)
        
        expected_stats = {
            'total': 1,
            'draft': 1,
            'pending': 0,
            'sent': 0,
            'received': 0,
            'expired': 0,
            'cancelled': 0,
        }
        
        self.assertEqual(stats, expected_stats)
    
    def test_validate_status_transition_valid(self):
        """Test valid status transitions"""
        valid_transitions = [
            ('draft', 'pending'),
            ('draft', 'cancelled'),
            ('pending', 'sent'),
            ('pending', 'cancelled'),
            ('sent', 'received'),
            ('sent', 'expired'),
            ('sent', 'cancelled'),
            ('received', 'cancelled'),
            ('expired', 'cancelled'),
        ]
        
        for current, new in valid_transitions:
            with self.subTest(current=current, new=new):
                result = self.manager._validate_status_transition(current, new)
                self.assertTrue(result)
    
    def test_validate_status_transition_invalid(self):
        """Test invalid status transitions"""
        invalid_transitions = [
            ('draft', 'sent'),      # Must go through pending
            ('draft', 'received'),  # Can't skip to received
            ('pending', 'received'), # Must go through sent
            ('received', 'draft'),   # Can't go backwards
            ('cancelled', 'draft'),  # Terminal state
            ('expired', 'sent'),     # Can't reactivate
        ]
        
        for current, new in invalid_transitions:
            with self.subTest(current=current, new=new):
                with self.assertRaises(ValidationError):
                    self.manager._validate_status_transition(current, new)