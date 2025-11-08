"""
Unit tests for parts-based quote system models
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from assessments.models import VehicleAssessment, AssessmentPhoto
from vehicles.models import Vehicle
from organizations.models import Organization

from .models import (
    DamagedPart, 
    PartQuoteRequest, 
    PartQuote, 
    PartMarketAverage, 
    AssessmentQuoteSummary,
    VehicleAssessmentQuoteExtension
)


class DamagedPartModelTest(TestCase):
    """Test cases for DamagedPart model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create organization
        self.organization = Organization.objects.create(
            name='Test Insurance Co',
            organization_type='insurance',
            is_insurance_provider=True
        )
        
        # Create vehicle (simplified for testing)
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        # Create assessment
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='TEST-001',
            assessment_type='insurance_claim',
            user=self.user,
            vehicle=self.vehicle,
            organization=self.organization,
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
    
    def test_damaged_part_creation(self):
        """Test creating a damaged part"""
        part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Cracked and dented from impact',
            requires_replacement=True,
            estimated_labor_hours=Decimal('2.5')
        )
        
        self.assertEqual(part.part_name, 'Front Bumper')
        self.assertEqual(part.damage_severity, 'moderate')
        self.assertTrue(part.requires_replacement)
        self.assertEqual(part.estimated_labor_hours, Decimal('2.5'))
        self.assertIsNotNone(part.identified_date)
    
    def test_damaged_part_str_representation(self):
        """Test string representation of damaged part"""
        part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage'
        )
        
        expected_str = f"{self.assessment.assessment_id} - Front Bumper (Moderate Damage)"
        self.assertEqual(str(part), expected_str)
    
    def test_estimated_cost_range_calculation(self):
        """Test estimated cost range calculation"""
        part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage',
            estimated_labor_hours=Decimal('2.0')
        )
        
        cost_range = part.get_estimated_cost_range()
        
        # Base cost for body parts: 500, moderate multiplier: 0.6
        # Expected part cost: 500 * 0.6 = 300
        # Labor cost: 2.0 * 45 = 90
        # Total estimated: 300 + 90 = 390
        
        self.assertIn('min_cost', cost_range)
        self.assertIn('max_cost', cost_range)
        self.assertIn('estimated_cost', cost_range)
        self.assertEqual(cost_range['estimated_cost'], 390)
    
    def test_damaged_part_validation(self):
        """Test model validation"""
        # Test negative labor hours should be prevented by validator
        with self.assertRaises(ValidationError):
            part = DamagedPart(
                assessment=self.assessment,
                section_type='exterior',
                part_name='Test Part',
                part_category='body',
                damage_severity='minor',
                damage_description='Test',
                estimated_labor_hours=Decimal('-1.0')
            )
            part.full_clean()


class PartQuoteRequestModelTest(TestCase):
    """Test cases for PartQuoteRequest model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.organization = Organization.objects.create(
            name='Test Insurance Co',
            organization_type='insurance',
            is_insurance_provider=True
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='TEST-001',
            assessment_type='insurance_claim',
            user=self.user,
            vehicle=self.vehicle,
            organization=self.organization,
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
        
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage'
        )
    
    def test_quote_request_creation(self):
        """Test creating a quote request"""
        expiry_date = timezone.now() + timedelta(days=7)
        
        request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=expiry_date,
            include_assessor=True,
            include_dealer=True,
            dispatched_by=self.user
        )
        
        self.assertIsNotNone(request.request_id)
        self.assertTrue(request.include_assessor)
        self.assertTrue(request.include_dealer)
        self.assertFalse(request.include_independent)
        self.assertEqual(request.vehicle_make, 'Toyota')
        self.assertEqual(request.vehicle_model, 'Camry')
        self.assertEqual(request.vehicle_year, 2020)
    
    def test_request_id_generation(self):
        """Test automatic request ID generation"""
        request = PartQuoteRequest()
        request_id = request.generate_request_id()
        
        self.assertTrue(request_id.startswith('QR-'))
        self.assertEqual(len(request_id), 22)  # QR- + 12 digit timestamp + - + 8 char UUID
    
    def test_selected_providers_method(self):
        """Test get_selected_providers method"""
        expiry_date = timezone.now() + timedelta(days=7)
        
        request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=expiry_date,
            include_assessor=True,
            include_independent=True,
            dispatched_by=self.user
        )
        
        providers = request.get_selected_providers()
        self.assertIn('assessor', providers)
        self.assertIn('independent', providers)
        self.assertNotIn('dealer', providers)
        self.assertNotIn('network', providers)
    
    def test_expiry_check(self):
        """Test expiry date checking"""
        # Create expired request
        expired_date = timezone.now() - timedelta(days=1)
        request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=expired_date,
            dispatched_by=self.user
        )
        
        self.assertTrue(request.is_expired())
        
        # Create valid request
        future_date = timezone.now() + timedelta(days=7)
        request2 = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=future_date,
            dispatched_by=self.user
        )
        
        self.assertFalse(request2.is_expired())


class PartQuoteModelTest(TestCase):
    """Test cases for PartQuote model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.organization = Organization.objects.create(
            name='Test Insurance Co',
            organization_type='insurance',
            is_insurance_provider=True
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='TEST-001',
            assessment_type='insurance_claim',
            user=self.user,
            vehicle=self.vehicle,
            organization=self.organization,
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
        
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage'
        )
        
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            dispatched_by=self.user
        )
    
    def test_quote_creation(self):
        """Test creating a part quote"""
        valid_until = timezone.now() + timedelta(days=30)
        
        quote = PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='dealer',
            provider_name='Toyota Dealer',
            part_cost=Decimal('450.00'),
            labor_cost=Decimal('120.00'),
            paint_cost=Decimal('80.00'),
            estimated_delivery_days=5,
            estimated_completion_days=3,
            valid_until=valid_until
        )
        
        self.assertEqual(quote.provider_type, 'dealer')
        self.assertEqual(quote.provider_name, 'Toyota Dealer')
        self.assertEqual(quote.part_cost, Decimal('450.00'))
        self.assertEqual(quote.total_cost, Decimal('650.00'))  # Auto-calculated
    
    def test_total_cost_calculation(self):
        """Test automatic total cost calculation"""
        valid_until = timezone.now() + timedelta(days=30)
        
        quote = PartQuote(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='independent',
            provider_name='Local Garage',
            part_cost=Decimal('300.00'),
            labor_cost=Decimal('100.00'),
            paint_cost=Decimal('50.00'),
            additional_costs=Decimal('25.00'),
            estimated_delivery_days=3,
            estimated_completion_days=2,
            valid_until=valid_until
        )
        
        quote.save()
        self.assertEqual(quote.total_cost, Decimal('475.00'))
    
    def test_cost_breakdown_method(self):
        """Test get_cost_breakdown method"""
        valid_until = timezone.now() + timedelta(days=30)
        
        quote = PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='assessor',
            provider_name='Internal Estimate',
            part_cost=Decimal('400.00'),
            labor_cost=Decimal('90.00'),
            paint_cost=Decimal('60.00'),
            estimated_delivery_days=0,
            estimated_completion_days=1,
            valid_until=valid_until
        )
        
        breakdown = quote.get_cost_breakdown()
        
        self.assertEqual(breakdown['part_cost'], 400.00)
        self.assertEqual(breakdown['labor_cost'], 90.00)
        self.assertEqual(breakdown['paint_cost'], 60.00)
        self.assertEqual(breakdown['total_cost'], 550.00)
    
    def test_price_score_calculation(self):
        """Test calculate_price_score method"""
        valid_until = timezone.now() + timedelta(days=30)
        
        quote = PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='independent',
            provider_name='Budget Garage',
            part_cost=Decimal('200.00'),
            labor_cost=Decimal('80.00'),
            estimated_delivery_days=3,
            estimated_completion_days=2,
            valid_until=valid_until
        )
        
        # Test with market average of 350
        score = quote.calculate_price_score(350)
        self.assertEqual(score, 100)  # 280/350 = 0.8, should get 100 points
        
        # Test with market average of 250
        score = quote.calculate_price_score(250)
        self.assertEqual(score, 60)  # 280/250 = 1.12, should get 60 points
    
    def test_quote_validity(self):
        """Test quote validity checking"""
        # Valid quote
        future_date = timezone.now() + timedelta(days=30)
        valid_quote = PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='dealer',
            provider_name='Test Dealer',
            part_cost=Decimal('400.00'),
            labor_cost=Decimal('100.00'),
            estimated_delivery_days=5,
            estimated_completion_days=3,
            valid_until=future_date
        )
        
        self.assertTrue(valid_quote.is_valid())
        
        # Expired quote
        past_date = timezone.now() - timedelta(days=1)
        expired_quote = PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_type='network',
            provider_name='Network Provider',
            part_cost=Decimal('350.00'),
            labor_cost=Decimal('90.00'),
            estimated_delivery_days=4,
            estimated_completion_days=2,
            valid_until=past_date
        )
        
        self.assertFalse(expired_quote.is_valid())


class PartMarketAverageModelTest(TestCase):
    """Test cases for PartMarketAverage model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.organization = Organization.objects.create(
            name='Test Insurance Co',
            organization_type='insurance',
            is_insurance_provider=True
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='TEST-001',
            assessment_type='insurance_claim',
            user=self.user,
            vehicle=self.vehicle,
            organization=self.organization,
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
        
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage'
        )
    
    def test_market_average_creation(self):
        """Test creating market average"""
        market_avg = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('450.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('100.00'),
            min_total_cost=Decimal('380.00'),
            max_total_cost=Decimal('520.00'),
            standard_deviation=Decimal('45.50'),
            variance_percentage=Decimal('10.11'),
            quote_count=5,
            confidence_level=85
        )
        
        self.assertEqual(market_avg.average_total_cost, Decimal('450.00'))
        self.assertEqual(market_avg.quote_count, 5)
        self.assertEqual(market_avg.confidence_level, 85)
    
    def test_price_range_display(self):
        """Test price range display method"""
        market_avg = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('450.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('100.00'),
            min_total_cost=Decimal('380.00'),
            max_total_cost=Decimal('520.00'),
            standard_deviation=Decimal('45.50'),
            variance_percentage=Decimal('10.11'),
            quote_count=5,
            confidence_level=85
        )
        
        price_range = market_avg.get_price_range_display()
        self.assertEqual(price_range, "£380.00 - £520.00")
    
    def test_high_confidence_check(self):
        """Test high confidence checking"""
        # High confidence case
        high_conf = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('450.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('100.00'),
            min_total_cost=Decimal('380.00'),
            max_total_cost=Decimal('520.00'),
            standard_deviation=Decimal('45.50'),
            variance_percentage=Decimal('10.11'),
            quote_count=5,
            confidence_level=85
        )
        
        self.assertTrue(high_conf.is_high_confidence())
        
        # Low confidence case (low quote count)
        low_conf = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('450.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('100.00'),
            min_total_cost=Decimal('380.00'),
            max_total_cost=Decimal('520.00'),
            standard_deviation=Decimal('45.50'),
            variance_percentage=Decimal('10.11'),
            quote_count=2,
            confidence_level=85
        )
        
        self.assertFalse(low_conf.is_high_confidence())
    
    def test_variance_categorization(self):
        """Test variance category method"""
        # Low variance
        low_var = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('450.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('100.00'),
            min_total_cost=Decimal('430.00'),
            max_total_cost=Decimal('470.00'),
            standard_deviation=Decimal('15.50'),
            variance_percentage=Decimal('5.5'),
            quote_count=4,
            confidence_level=90
        )
        
        self.assertEqual(low_var.get_variance_category(), 'low')
        
        # High variance
        high_var = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('450.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('100.00'),
            min_total_cost=Decimal('300.00'),
            max_total_cost=Decimal('600.00'),
            standard_deviation=Decimal('95.50'),
            variance_percentage=Decimal('35.8'),
            quote_count=4,
            confidence_level=60
        )
        
        self.assertEqual(high_var.get_variance_category(), 'high')


class AssessmentQuoteSummaryModelTest(TestCase):
    """Test cases for AssessmentQuoteSummary model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.organization = Organization.objects.create(
            name='Test Insurance Co',
            organization_type='insurance',
            is_insurance_provider=True
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='TEST-001',
            assessment_type='insurance_claim',
            user=self.user,
            vehicle=self.vehicle,
            organization=self.organization,
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
    
    def test_quote_summary_creation(self):
        """Test creating assessment quote summary"""
        summary = AssessmentQuoteSummary.objects.create(
            assessment=self.assessment,
            total_parts_identified=3,
            parts_with_quotes=2,
            total_quote_requests=6,
            quotes_received=4,
            assessor_total=Decimal('1200.00'),
            dealer_total=Decimal('1500.00'),
            independent_total=Decimal('1100.00'),
            market_average_total=Decimal('1300.00')
        )
        
        self.assertEqual(summary.total_parts_identified, 3)
        self.assertEqual(summary.assessor_total, Decimal('1200.00'))
        self.assertEqual(summary.status, 'collecting')
    
    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation"""
        summary = AssessmentQuoteSummary.objects.create(
            assessment=self.assessment,
            total_parts_identified=5,
            parts_with_quotes=3
        )
        
        percentage = summary.calculate_completion_percentage()
        self.assertEqual(percentage, 60.0)  # 3/5 * 100
        
        # Test with zero parts
        summary.total_parts_identified = 0
        percentage = summary.calculate_completion_percentage()
        self.assertEqual(percentage, 0)
    
    def test_best_provider_total(self):
        """Test getting best provider total"""
        summary = AssessmentQuoteSummary.objects.create(
            assessment=self.assessment,
            assessor_total=Decimal('1200.00'),
            dealer_total=Decimal('1500.00'),
            independent_total=Decimal('1100.00'),
            network_total=None  # Not available
        )
        
        best_total = summary.get_best_provider_total()
        self.assertEqual(best_total, Decimal('1100.00'))
    
    def test_potential_savings_calculation(self):
        """Test potential savings calculation"""
        summary = AssessmentQuoteSummary.objects.create(
            assessment=self.assessment,
            assessor_total=Decimal('1200.00'),
            dealer_total=Decimal('1500.00'),
            independent_total=Decimal('1100.00')
        )
        
        savings = summary.calculate_potential_savings()
        self.assertEqual(savings, Decimal('400.00'))  # 1500 - 1100


class VehicleAssessmentQuoteExtensionModelTest(TestCase):
    """Test cases for VehicleAssessmentQuoteExtension model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.organization = Organization.objects.create(
            name='Test Insurance Co',
            organization_type='insurance',
            is_insurance_provider=True
        )
        
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='TEST-001',
            assessment_type='insurance_claim',
            user=self.user,
            vehicle=self.vehicle,
            organization=self.organization,
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
    
    def test_quote_extension_creation(self):
        """Test creating quote extension"""
        extension = VehicleAssessmentQuoteExtension.objects.create(
            assessment=self.assessment,
            uses_parts_based_quotes=True,
            parts_identification_complete=True,
            quote_collection_status='in_progress'
        )
        
        self.assertTrue(extension.uses_parts_based_quotes)
        self.assertTrue(extension.parts_identification_complete)
        self.assertEqual(extension.quote_collection_status, 'in_progress')
    
    def test_cost_calculation_method(self):
        """Test cost calculation method identification"""
        extension = VehicleAssessmentQuoteExtension.objects.create(
            assessment=self.assessment,
            uses_parts_based_quotes=True
        )
        
        self.assertEqual(extension.get_cost_calculation_method(), 'parts_based')
        
        extension.uses_parts_based_quotes = False
        extension.save()
        
        self.assertEqual(extension.get_cost_calculation_method(), 'hardcoded')
    
    def test_can_start_quote_collection(self):
        """Test quote collection readiness check"""
        extension = VehicleAssessmentQuoteExtension.objects.create(
            assessment=self.assessment,
            uses_parts_based_quotes=True,
            parts_identification_complete=True,
            quote_collection_status='not_started'
        )
        
        self.assertTrue(extension.can_start_quote_collection())
        
        # Test when parts identification not complete
        extension.parts_identification_complete = False
        extension.save()
        
        self.assertFalse(extension.can_start_quote_collection())
        
        # Test when already in progress
        extension.parts_identification_complete = True
        extension.quote_collection_status = 'in_progress'
        extension.save()
        
        self.assertFalse(extension.can_start_quote_collection())