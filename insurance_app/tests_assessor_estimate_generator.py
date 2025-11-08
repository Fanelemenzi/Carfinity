# tests_assessor_estimate_generator.py
"""
Unit tests for the AssessorEstimateGenerator class.

Tests cover all methods including estimate generation, cost calculations,
validation, and confidence scoring.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from assessments.models import VehicleAssessment
from vehicles.models import Vehicle
from .models import DamagedPart, PartQuoteRequest, PartQuote
from .quote_generators import AssessorEstimateGenerator


class AssessorEstimateGeneratorTestCase(TestCase):
    """Test cases for AssessorEstimateGenerator"""
    
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
            manufacture_year=2020,
            vin='1HGBH41JXMN109186',
            license_plate='ABC123'
        )
        
        # Create test assessment
        self.assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            created_by=self.user,
            assigned_to=self.user,
            assessment_type='comprehensive',
            status='in_progress'
        )
        
        # Create test damaged parts with different categories and severities
        self.body_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dents from minor collision',
            estimated_labor_hours=Decimal('2.5')
        )
        
        self.mechanical_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='mechanical',
            part_name='Brake Pads',
            part_category='mechanical',
            damage_severity='replace',
            damage_description='Worn brake pads need replacement',
            estimated_labor_hours=Decimal('1.0')
        )
        
        self.electrical_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='electrical',
            part_name='Headlight Assembly',
            part_category='electrical',
            damage_severity='severe',
            damage_description='Cracked headlight housing',
            estimated_labor_hours=Decimal('1.5'),
            part_number='HL-12345'
        )
        
        # Initialize generator
        self.generator = AssessorEstimateGenerator()
    
    def test_generate_assessor_estimate_success(self):
        """Test successful generation of assessor estimate"""
        quote = self.generator.generate_assessor_estimate(self.body_part)
        
        # Verify quote was created
        self.assertIsInstance(quote, PartQuote)
        self.assertEqual(quote.damaged_part, self.body_part)
        self.assertEqual(quote.provider_type, 'assessor')
        self.assertEqual(quote.provider_name, 'Internal Assessor Estimate')
        self.assertEqual(quote.part_type, 'oem_equivalent')
        self.assertEqual(quote.status, 'validated')
        
        # Verify cost calculations
        self.assertGreater(quote.part_cost, 0)
        self.assertGreater(quote.labor_cost, 0)
        self.assertGreater(quote.paint_cost, 0)  # Body part should have paint cost
        self.assertGreater(quote.additional_costs, 0)
        self.assertEqual(
            quote.total_cost,
            quote.part_cost + quote.labor_cost + quote.paint_cost + quote.additional_costs
        )
        
        # Verify timeline estimates
        self.assertGreater(quote.estimated_delivery_days, 0)
        self.assertGreater(quote.estimated_completion_days, 0)
        self.assertGreaterEqual(quote.estimated_completion_days, quote.estimated_delivery_days)
        
        # Verify warranty terms
        self.assertEqual(quote.part_warranty_months, 12)
        self.assertEqual(quote.labor_warranty_months, 12)
        
        # Verify confidence score
        self.assertGreaterEqual(quote.confidence_score, 60)
        self.assertLessEqual(quote.confidence_score, 100)
        
        # Verify validity period
        self.assertIsNotNone(quote.valid_until)
        expected_valid_until = timezone.now() + timedelta(days=30)
        self.assertAlmostEqual(
            quote.valid_until.timestamp(),
            expected_valid_until.timestamp(),
            delta=60  # Within 1 minute
        )
    
    def test_generate_assessor_estimate_with_quote_request(self):
        """Test estimate generation with associated quote request"""
        # Create quote request
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.body_part,
            assessment=self.assessment,
            dispatched_by=self.user,
            expiry_date=timezone.now() + timedelta(days=7)
        )
        
        quote = self.generator.generate_assessor_estimate(
            self.body_part, 
            quote_request=quote_request
        )
        
        self.assertEqual(quote.quote_request, quote_request)
    
    def test_generate_assessor_estimate_validation_error(self):
        """Test error handling for invalid damaged part"""
        # Test with None
        with self.assertRaises(ValidationError) as context:
            self.generator.generate_assessor_estimate(None)
        self.assertIn("Damaged part is required", str(context.exception))
        
        # Test with part missing required fields
        invalid_part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Test Part'
            # Missing part_category and damage_severity
        )
        
        with self.assertRaises(ValidationError):
            self.generator.generate_assessor_estimate(invalid_part)
    
    def test_get_base_part_cost_all_categories(self):
        """Test base part cost calculation for all categories"""
        test_cases = [
            ('body', 'moderate', Decimal('500.00') * Decimal('0.6')),
            ('mechanical', 'severe', Decimal('800.00') * Decimal('1.0')),
            ('electrical', 'replace', Decimal('300.00') * Decimal('1.5')),
            ('glass', 'minor', Decimal('200.00') * Decimal('0.3')),
            ('interior', 'moderate', Decimal('150.00') * Decimal('0.6')),
            ('trim', 'minor', Decimal('100.00') * Decimal('0.3')),
            ('wheels', 'replace', Decimal('400.00') * Decimal('1.5')),
            ('safety', 'severe', Decimal('600.00') * Decimal('1.0')),
            ('structural', 'replace', Decimal('1200.00') * Decimal('1.5')),
            ('fluid', 'moderate', Decimal('250.00') * Decimal('0.6')),
        ]
        
        for category, severity, expected_cost in test_cases:
            with self.subTest(category=category, severity=severity):
                part = DamagedPart(
                    assessment=self.assessment,
                    section_type='test',
                    part_name='Test Part',
                    part_category=category,
                    damage_severity=severity,
                    damage_description='Test damage'
                )
                
                cost = self.generator.get_base_part_cost(part)
                self.assertEqual(cost, expected_cost.quantize(Decimal('0.01')))
    
    def test_get_base_part_cost_unknown_category(self):
        """Test base part cost with unknown category falls back to mechanical"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='test',
            part_name='Test Part',
            part_category='unknown_category',
            damage_severity='moderate',
            damage_description='Test damage'
        )
        
        cost = self.generator.get_base_part_cost(part)
        expected_cost = Decimal('800.00') * Decimal('0.6')  # mechanical * moderate
        self.assertEqual(cost, expected_cost.quantize(Decimal('0.01')))
    
    def test_calculate_labor_cost_with_estimated_hours(self):
        """Test labor cost calculation with estimated hours"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='test',
            part_name='Test Part',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage',
            estimated_labor_hours=Decimal('3.5')
        )
        
        labor_cost = self.generator.calculate_labor_cost(part)
        expected_cost = Decimal('3.5') * Decimal('45.00')  # 3.5 hours * £45/hour
        self.assertEqual(labor_cost, expected_cost.quantize(Decimal('0.01')))
    
    def test_calculate_labor_cost_default_hours(self):
        """Test labor cost calculation with default hours"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='test',
            part_name='Test Part',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage',
            estimated_labor_hours=Decimal('0')  # No hours specified
        )
        
        labor_cost = self.generator.calculate_labor_cost(part)
        
        # Should use default: body (3.0) * moderate (1.0) * £45/hour
        expected_cost = Decimal('3.0') * Decimal('1.0') * Decimal('45.00')
        self.assertEqual(labor_cost, expected_cost.quantize(Decimal('0.01')))
    
    def test_calculate_paint_cost_body_parts(self):
        """Test paint cost calculation for body parts"""
        part_cost = Decimal('500.00')
        
        body_part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Door Panel',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratched door panel'
        )
        
        paint_cost = self.generator.calculate_paint_cost(body_part, part_cost)
        expected_cost = part_cost * Decimal('0.15')  # 15% of part cost
        self.assertEqual(paint_cost, expected_cost.quantize(Decimal('0.01')))
    
    def test_calculate_paint_cost_minimum_for_body(self):
        """Test minimum paint cost for body parts"""
        part_cost = Decimal('100.00')  # Low cost part
        
        body_part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Small Trim',
            part_category='body',
            damage_severity='minor',
            damage_description='Minor scratch'
        )
        
        paint_cost = self.generator.calculate_paint_cost(body_part, part_cost)
        # Should use minimum of £50 for body parts
        self.assertEqual(paint_cost, Decimal('50.00'))
    
    def test_calculate_paint_cost_trim_parts(self):
        """Test paint cost calculation for trim parts"""
        part_cost = Decimal('200.00')
        
        trim_part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Side Molding',
            part_category='trim',
            damage_severity='moderate',
            damage_description='Scratched trim'
        )
        
        paint_cost = self.generator.calculate_paint_cost(trim_part, part_cost)
        expected_cost = part_cost * Decimal('0.15')  # 15% of part cost
        self.assertEqual(paint_cost, expected_cost.quantize(Decimal('0.01')))
    
    def test_calculate_paint_cost_non_paintable_parts(self):
        """Test paint cost for non-paintable parts"""
        part_cost = Decimal('300.00')
        
        non_paintable_categories = ['mechanical', 'electrical', 'glass', 'interior', 'wheels', 'safety', 'structural', 'fluid']
        
        for category in non_paintable_categories:
            with self.subTest(category=category):
                part = DamagedPart(
                    assessment=self.assessment,
                    section_type='test',
                    part_name='Test Part',
                    part_category=category,
                    damage_severity='moderate',
                    damage_description='Test damage'
                )
                
                paint_cost = self.generator.calculate_paint_cost(part, part_cost)
                self.assertEqual(paint_cost, Decimal('0.00'))
    
    def test_calculate_confidence_score_standard(self):
        """Test confidence score calculation for standard parts"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Standard Part',
            part_category='body',
            damage_severity='moderate',
            damage_description='Standard damage',
            estimated_labor_hours=Decimal('2.0'),
            part_number='STD-12345'
        )
        
        confidence = self.generator._calculate_confidence_score(part)
        
        # Base confidence (85) + labor hours specified (+5) + part number (+5) = 95
        self.assertEqual(confidence, 95)
    
    def test_calculate_confidence_score_severe_damage(self):
        """Test confidence score reduction for severe damage"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Damaged Part',
            part_category='body',
            damage_severity='severe',
            damage_description='Severe damage'
        )
        
        confidence = self.generator._calculate_confidence_score(part)
        
        # Base confidence (85) - severe damage penalty (-10) = 75
        self.assertEqual(confidence, 75)
    
    def test_calculate_confidence_score_replacement(self):
        """Test confidence score for replacement parts"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='mechanical',
            part_name='Engine Component',
            part_category='mechanical',
            damage_severity='replace',
            damage_description='Needs replacement'
        )
        
        confidence = self.generator._calculate_confidence_score(part)
        
        # Base confidence (85) - replacement penalty (-5) = 80
        self.assertEqual(confidence, 80)
    
    def test_calculate_confidence_score_minimum(self):
        """Test confidence score minimum threshold"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='test',
            part_name='Unknown Part',
            part_category='unknown',  # Will trigger estimated confidence (70)
            damage_severity='severe',  # -10 penalty
            damage_description='Severe unknown damage'
        )
        
        confidence = self.generator._calculate_confidence_score(part)
        
        # Should not go below minimum of 60
        self.assertEqual(confidence, 60)
    
    def test_get_default_labor_hours_all_categories(self):
        """Test default labor hours for all categories and severities"""
        test_cases = [
            ('body', 'minor', Decimal('3.0') * Decimal('0.5')),
            ('body', 'moderate', Decimal('3.0') * Decimal('1.0')),
            ('body', 'severe', Decimal('3.0') * Decimal('1.5')),
            ('body', 'replace', Decimal('3.0') * Decimal('2.0')),
            ('mechanical', 'moderate', Decimal('2.5') * Decimal('1.0')),
            ('electrical', 'severe', Decimal('1.5') * Decimal('1.5')),
            ('glass', 'replace', Decimal('1.0') * Decimal('2.0')),
            ('structural', 'replace', Decimal('5.0') * Decimal('2.0')),
        ]
        
        for category, severity, expected_hours in test_cases:
            with self.subTest(category=category, severity=severity):
                part = DamagedPart(
                    assessment=self.assessment,
                    section_type='test',
                    part_name='Test Part',
                    part_category=category,
                    damage_severity=severity,
                    damage_description='Test damage'
                )
                
                hours = self.generator._get_default_labor_hours(part)
                self.assertEqual(hours, expected_hours)
    
    def test_get_estimated_delivery_days(self):
        """Test estimated delivery days for different part categories"""
        delivery_expectations = {
            'body': 5,
            'mechanical': 3,
            'electrical': 7,
            'glass': 2,
            'interior': 5,
            'trim': 7,
            'wheels': 1,
            'safety': 10,
            'structural': 14,
            'fluid': 1,
        }
        
        for category, expected_days in delivery_expectations.items():
            with self.subTest(category=category):
                part = DamagedPart(
                    assessment=self.assessment,
                    section_type='test',
                    part_name='Test Part',
                    part_category=category,
                    damage_severity='moderate',
                    damage_description='Test damage'
                )
                
                days = self.generator._get_estimated_delivery_days(part)
                self.assertEqual(days, expected_days)
    
    def test_get_estimated_completion_days(self):
        """Test estimated completion days includes delivery and work time"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Body Panel',
            part_category='body',
            damage_severity='severe',  # Should add extra work day
            damage_description='Severe body damage'
        )
        
        completion_days = self.generator._get_estimated_completion_days(part)
        delivery_days = self.generator._get_estimated_delivery_days(part)  # 5 for body
        
        # Body work days (2) + severe damage buffer (1) + delivery (5) = 8
        expected_days = 5 + 2 + 1  # delivery + work + severe buffer
        self.assertEqual(completion_days, expected_days)
    
    def test_calculate_additional_costs_replacement(self):
        """Test additional costs for replacement parts"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='mechanical',
            part_name='Engine Part',
            part_category='mechanical',
            damage_severity='replace',
            damage_description='Needs replacement',
            requires_replacement=True
        )
        
        additional_costs = self.generator._calculate_additional_costs(part)
        
        # Should include disposal fee (£25) + mechanical consumables (£20) = £45
        expected_cost = Decimal('25.00') + Decimal('20.00')
        self.assertEqual(additional_costs, expected_cost)
    
    def test_calculate_additional_costs_repair_only(self):
        """Test additional costs for repair-only parts"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='body',
            part_name='Body Panel',
            part_category='body',
            damage_severity='moderate',
            damage_description='Repairable damage',
            requires_replacement=False
        )
        
        additional_costs = self.generator._calculate_additional_costs(part)
        
        # Should include only body consumables (£30), no disposal fee
        expected_cost = Decimal('30.00')
        self.assertEqual(additional_costs, expected_cost)
    
    def test_generate_estimate_notes(self):
        """Test generation of estimate notes"""
        part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratched and dented',
            estimated_labor_hours=Decimal('2.5'),
            requires_replacement=True
        )
        
        notes = self.generator._generate_estimate_notes(part)
        
        # Check that notes contain expected information
        self.assertIn('Front Bumper', notes)
        self.assertIn('Moderate Damage', notes)
        self.assertIn('Body Panel', notes)
        self.assertIn('Labor hours: 2.5', notes)
        self.assertIn('complete replacement', notes)
        self.assertIn('industry standard rates', notes)
        self.assertIn('OEM equivalent parts', notes)
    
    def test_validation_methods(self):
        """Test validation helper methods"""
        # Test valid part
        valid_part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Valid Part',
            part_category='body',
            damage_severity='moderate',
            damage_description='Valid damage'
        )
        
        # Should not raise exception
        self.generator._validate_damaged_part(valid_part)
        
        # Test invalid part category
        invalid_category_part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Invalid Part',
            part_category='invalid_category',
            damage_severity='moderate',
            damage_description='Invalid category'
        )
        
        with self.assertRaises(ValidationError) as context:
            self.generator._validate_damaged_part(invalid_category_part)
        self.assertIn('Unknown part category', str(context.exception))
        
        # Test invalid damage severity
        invalid_severity_part = DamagedPart(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Invalid Part',
            part_category='body',
            damage_severity='invalid_severity',
            damage_description='Invalid severity'
        )
        
        with self.assertRaises(ValidationError) as context:
            self.generator._validate_damaged_part(invalid_severity_part)
        self.assertIn('Unknown damage severity', str(context.exception))
    
    def test_cost_calculation_precision(self):
        """Test that all cost calculations maintain proper decimal precision"""
        quote = self.generator.generate_assessor_estimate(self.body_part)
        
        # All costs should be rounded to 2 decimal places
        self.assertEqual(quote.part_cost.as_tuple().exponent, -2)
        self.assertEqual(quote.labor_cost.as_tuple().exponent, -2)
        self.assertEqual(quote.paint_cost.as_tuple().exponent, -2)
        self.assertEqual(quote.additional_costs.as_tuple().exponent, -2)
        self.assertEqual(quote.total_cost.as_tuple().exponent, -2)
    
    def test_estimate_consistency(self):
        """Test that estimates are consistent for identical parts"""
        # Create identical parts
        part1 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Identical Part',
            part_category='body',
            damage_severity='moderate',
            damage_description='Same damage',
            estimated_labor_hours=Decimal('2.0')
        )
        
        part2 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Identical Part',
            part_category='body',
            damage_severity='moderate',
            damage_description='Same damage',
            estimated_labor_hours=Decimal('2.0')
        )
        
        quote1 = self.generator.generate_assessor_estimate(part1)
        quote2 = self.generator.generate_assessor_estimate(part2)
        
        # Costs should be identical
        self.assertEqual(quote1.part_cost, quote2.part_cost)
        self.assertEqual(quote1.labor_cost, quote2.labor_cost)
        self.assertEqual(quote1.paint_cost, quote2.paint_cost)
        self.assertEqual(quote1.additional_costs, quote2.additional_costs)
        self.assertEqual(quote1.total_cost, quote2.total_cost)
        self.assertEqual(quote1.confidence_score, quote2.confidence_score)
    
    @patch('insurance_app.quote_generators.logger')
    def test_logging_on_success(self, mock_logger):
        """Test that successful estimate generation is logged"""
        quote = self.generator.generate_assessor_estimate(self.body_part)
        
        # Should log successful generation
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn(f"Generated assessor estimate for part {self.body_part.id}", log_message)
        self.assertIn(str(quote.total_cost), log_message)
    
    @patch('insurance_app.quote_generators.logger')
    def test_logging_on_error(self, mock_logger):
        """Test that errors are logged properly"""
        with self.assertRaises(ValidationError):
            self.generator.generate_assessor_estimate(None)
        
        # Should log error
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        self.assertIn("Error generating assessor estimate", log_message)