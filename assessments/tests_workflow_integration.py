"""
Tests for parts-based quote system integration with assessment workflow
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from decimal import Decimal

from .models import VehicleAssessment
from vehicles.models import Vehicle


class AssessmentWorkflowIntegrationTest(TestCase):
    """Test integration of parts-based quotes into assessment workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create a test vehicle
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            manufacture_year=2020,
            vin='1234567890ABCDEFG'
        )
        
        # Create a test assessment
        self.assessment = VehicleAssessment.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            assessment_id='TEST-001',
            assessment_type='crash',
            status='completed',
            uses_parts_based_quotes=True,
            estimated_repair_cost=Decimal('5000.00'),
            vehicle_market_value=Decimal('20000.00'),
            salvage_value=Decimal('2000.00')
        )
    
    def test_assessment_detail_displays_quote_progress(self):
        """Test that assessment detail view displays quote collection progress"""
        url = reverse('assessments:assessment_detail', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quote Collection Status')
        self.assertContains(response, 'Parts-Based Quotes')
        
        # Check that quote progress is in context
        self.assertIn('quote_progress', response.context)
        quote_progress = response.context['quote_progress']
        self.assertEqual(quote_progress['method'], 'parts_based')
    
    def test_assessment_detail_hardcoded_costs(self):
        """Test assessment detail view with hardcoded costs"""
        # Update assessment to use hardcoded costs
        self.assessment.uses_parts_based_quotes = False
        self.assessment.save()
        
        url = reverse('assessments:assessment_detail', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hardcoded Estimates')
        
        # Check cost info
        cost_info = response.context['cost_info']
        self.assertEqual(cost_info['method'], 'hardcoded')
        self.assertEqual(cost_info['repair_cost'], Decimal('5000.00'))
    
    def test_trigger_parts_identification_view(self):
        """Test the trigger parts identification view"""
        url = reverse('assessments:trigger_parts_identification', args=[self.assessment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Identify Damaged Parts')
        self.assertContains(response, 'Parts Identification')
    
    @patch('insurance_app.parts_identification.PartsIdentificationEngine')
    def test_trigger_parts_identification_post(self, mock_engine_class):
        """Test triggering parts identification via POST"""
        # Mock the parts identification engine
        mock_engine = MagicMock()
        mock_engine.identify_damaged_parts.return_value = ['part1', 'part2']
        mock_engine_class.return_value = mock_engine
        
        url = reverse('assessments:trigger_parts_identification', args=[self.assessment.id])
        response = self.client.post(url)
        
        # Should redirect to assessment detail
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(f'/assessments/{self.assessment.id}/'))
        
        # Check that assessment was updated
        self.assessment.refresh_from_db()
        self.assertTrue(self.assessment.parts_identification_complete)
        self.assertEqual(self.assessment.quote_collection_status, 'not_started')
    
    def test_trigger_parts_identification_hardcoded_assessment(self):
        """Test triggering parts identification on hardcoded assessment shows error"""
        # Update assessment to use hardcoded costs
        self.assessment.uses_parts_based_quotes = False
        self.assessment.save()
        
        url = reverse('assessments:trigger_parts_identification', args=[self.assessment.id])
        response = self.client.post(url)
        
        # Should redirect back with error message
        self.assertEqual(response.status_code, 302)
        
        # Assessment should not be updated
        self.assessment.refresh_from_db()
        self.assertFalse(self.assessment.parts_identification_complete)
    
    @patch('insurance_app.parts_identification.PartsIdentificationEngine')
    def test_assessment_completion_triggers_parts_identification(self, mock_engine_class):
        """Test that completing an assessment triggers parts identification"""
        # Create an in-progress assessment
        assessment = VehicleAssessment.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            assessment_id='TEST-002',
            assessment_type='crash',
            status='in_progress',
            uses_parts_based_quotes=True
        )
        
        # Mock the parts identification engine
        mock_engine = MagicMock()
        mock_engine.identify_damaged_parts.return_value = ['part1', 'part2', 'part3']
        mock_engine_class.return_value = mock_engine
        
        # Complete the assessment
        url = reverse('assessments:assessment_notes', args=[assessment.id])
        response = self.client.post(url, {
            'overall_notes': 'Test notes',
            'complete_assessment': 'true'
        })
        
        # Should redirect to assessment detail
        self.assertEqual(response.status_code, 302)
        
        # Check that assessment was completed and parts identified
        assessment.refresh_from_db()
        self.assertEqual(assessment.status, 'completed')
        self.assertTrue(assessment.parts_identification_complete)
        self.assertEqual(assessment.quote_collection_status, 'not_started')
    
    def test_cost_calculation_methods(self):
        """Test cost calculation methods in VehicleAssessment model"""
        # Test hardcoded costs
        self.assessment.uses_parts_based_quotes = False
        self.assessment.save()
        
        self.assertEqual(self.assessment.get_cost_calculation_method(), 'hardcoded')
        self.assertTrue(self.assessment.uses_hardcoded_costs())
        self.assertFalse(self.assessment.uses_parts_based_costs())
        self.assertEqual(self.assessment.get_current_repair_cost(), Decimal('5000.00'))
        
        # Test parts-based costs
        self.assessment.uses_parts_based_quotes = True
        self.assessment.save()
        
        self.assertEqual(self.assessment.get_cost_calculation_method(), 'parts_based')
        self.assertFalse(self.assessment.uses_hardcoded_costs())
        self.assertTrue(self.assessment.uses_parts_based_costs())
        # Should fall back to estimated cost when no quote summary exists
        self.assertEqual(self.assessment.get_current_repair_cost(), Decimal('5000.00'))
    
    def test_settlement_calculation(self):
        """Test settlement amount calculation"""
        # Test repair scenario (cost < 70% of market value)
        self.assessment.estimated_repair_cost = Decimal('10000.00')  # 50% of market value
        self.assessment.save()
        
        settlement = self.assessment.calculate_settlement_amount()
        self.assertEqual(settlement, Decimal('10000.00'))  # Repair cost
        self.assertFalse(self.assessment.is_total_loss_by_cost())
        
        # Test total loss scenario (cost > 70% of market value)
        self.assessment.estimated_repair_cost = Decimal('15000.00')  # 75% of market value
        self.assessment.save()
        
        settlement = self.assessment.calculate_settlement_amount()
        self.assertEqual(settlement, Decimal('18000.00'))  # Market value - salvage value
        self.assertTrue(self.assessment.is_total_loss_by_cost())
    
    def test_cost_summary(self):
        """Test comprehensive cost summary"""
        summary = self.assessment.get_cost_summary()
        
        self.assertEqual(summary['method'], 'parts_based')
        self.assertEqual(summary['repair_cost'], Decimal('5000.00'))
        self.assertEqual(summary['market_value'], Decimal('20000.00'))
        self.assertEqual(summary['salvage_value'], Decimal('2000.00'))
        self.assertEqual(summary['settlement_amount'], Decimal('5000.00'))
        self.assertFalse(summary['is_total_loss'])
    
    def test_quote_collection_progress(self):
        """Test quote collection progress tracking"""
        # Test parts-based assessment without parts identification
        progress = self.assessment.get_quote_collection_progress()
        self.assertEqual(progress['method'], 'parts_based')
        self.assertEqual(progress['progress_percentage'], 0)
        self.assertIn('parts identification', progress['message'].lower())
        
        # Test after parts identification
        self.assessment.parts_identification_complete = True
        self.assessment.quote_collection_status = 'not_started'
        self.assessment.save()
        
        progress = self.assessment.get_quote_collection_progress()
        self.assertEqual(progress['progress_percentage'], 25)
        
        # Test in progress
        self.assessment.quote_collection_status = 'in_progress'
        self.assessment.save()
        
        progress = self.assessment.get_quote_collection_progress()
        self.assertEqual(progress['progress_percentage'], 60)
        
        # Test completed
        self.assessment.quote_collection_status = 'completed'
        self.assessment.save()
        
        progress = self.assessment.get_quote_collection_progress()
        self.assertEqual(progress['progress_percentage'], 100)
        
        # Test hardcoded assessment
        self.assessment.uses_parts_based_quotes = False
        self.assessment.save()
        
        progress = self.assessment.get_quote_collection_progress()
        self.assertEqual(progress['method'], 'hardcoded')
        self.assertEqual(progress['progress_percentage'], 100)