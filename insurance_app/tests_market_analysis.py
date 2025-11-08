"""
Unit tests for Market Average Calculator

Tests cover all functionality of the MarketAverageCalculator class including:
- Market average calculations with various quote scenarios
- Confidence level calculations based on data quality
- Outlier identification using statistical methods
- Assessment-level market average calculations
- Batch processing of market averages
- Error handling for insufficient data
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from assessments.models import VehicleAssessment
from vehicles.models import Vehicle
from .models import (
    DamagedPart, 
    PartQuote, 
    PartQuoteRequest, 
    PartMarketAverage,
    AssessmentQuoteSummary
)
from .market_analysis import MarketAverageCalculator, InsufficientDataError, MarketAnalysisReporter


class MarketAverageCalculatorTestCase(TestCase):
    """Test cases for MarketAverageCalculator class"""
    
    def setUp(self):
        """Set up test data"""
        self.calculator = MarketAverageCalculator()
        
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
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now().date(),
            status='completed'
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
        
        # Create test quote request
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            dispatched_by=self.user,
            include_assessor=True,
            include_dealer=True,
            include_independent=True
        )
    
    def _create_test_quotes(self, costs_and_providers):
        """Helper method to create test quotes"""
        quotes = []
        for i, (cost, provider_type, provider_name) in enumerate(costs_and_providers):
            quote = PartQuote.objects.create(
                quote_request=self.quote_request,
                damaged_part=self.damaged_part,
                provider_type=provider_type,
                provider_name=provider_name,
                part_cost=Decimal(str(cost * 0.7)),  # 70% of total for part
                labor_cost=Decimal(str(cost * 0.25)),  # 25% for labor
                paint_cost=Decimal(str(cost * 0.05)),  # 5% for paint
                total_cost=Decimal(str(cost)),
                estimated_delivery_days=5 + i,
                estimated_completion_days=7 + i,
                valid_until=timezone.now() + timedelta(days=30),
                status='validated'
            )
            quotes.append(quote)
        return quotes
    
    def test_calculate_market_average_success(self):
        """Test successful market average calculation"""
        # Create test quotes with varied costs
        test_data = [
            (500.00, 'assessor', 'Internal Assessor'),
            (550.00, 'dealer', 'Toyota Dealer'),
            (480.00, 'independent', 'Local Garage'),
            (520.00, 'network', 'Insurance Network')
        ]
        self._create_test_quotes(test_data)
        
        # Calculate market average
        market_avg = self.calculator.calculate_market_average(self.damaged_part)
        
        # Verify calculations
        expected_avg = (500 + 550 + 480 + 520) / 4  # 512.50
        self.assertEqual(float(market_avg.average_total_cost), expected_avg)
        self.assertEqual(float(market_avg.min_total_cost), 480.00)
        self.assertEqual(float(market_avg.max_total_cost), 550.00)
        self.assertEqual(market_avg.quote_count, 4)
        self.assertGreater(market_avg.confidence_level, 0)
        
        # Verify part cost and labor cost averages
        expected_part_avg = expected_avg * 0.7
        expected_labor_avg = expected_avg * 0.25
        self.assertAlmostEqual(float(market_avg.average_part_cost), expected_part_avg, places=2)
        self.assertAlmostEqual(float(market_avg.average_labor_cost), expected_labor_avg, places=2)
    
    def test_calculate_market_average_insufficient_data(self):
        """Test market average calculation with insufficient quotes"""
        # Create only one quote (below minimum requirement)
        self._create_test_quotes([(500.00, 'assessor', 'Internal Assessor')])
        
        # Should raise InsufficientDataError
        with self.assertRaises(InsufficientDataError) as context:
            self.calculator.calculate_market_average(self.damaged_part)
        
        self.assertIn("Need at least 2 quotes", str(context.exception))
    
    def test_calculate_market_average_no_quotes(self):
        """Test market average calculation with no quotes"""
        # Don't create any quotes
        
        # Should raise InsufficientDataError
        with self.assertRaises(InsufficientDataError):
            self.calculator.calculate_market_average(self.damaged_part)
    
    def test_calculate_confidence_level_high_confidence(self):
        """Test confidence level calculation for high-quality data"""
        # High confidence: many quotes, low variance, no outliers
        confidence = self.calculator.calculate_confidence_level(
            quote_count=5,
            variance_percentage=8.0,
            outlier_count=0
        )
        
        # Should be high confidence (90 base + 10 variance - 0 outliers = 100)
        self.assertEqual(confidence, 100)
    
    def test_calculate_confidence_level_medium_confidence(self):
        """Test confidence level calculation for medium-quality data"""
        # Medium confidence: moderate quotes, moderate variance, some outliers
        confidence = self.calculator.calculate_confidence_level(
            quote_count=3,
            variance_percentage=15.0,
            outlier_count=1
        )
        
        # Should be medium confidence (70 base + 5 variance - 5 outliers = 70)
        self.assertEqual(confidence, 70)
    
    def test_calculate_confidence_level_low_confidence(self):
        """Test confidence level calculation for low-quality data"""
        # Low confidence: few quotes, high variance, many outliers
        confidence = self.calculator.calculate_confidence_level(
            quote_count=2,
            variance_percentage=60.0,
            outlier_count=2
        )
        
        # Should be low confidence (50 base - 20 variance - 10 outliers = 20)
        self.assertEqual(confidence, 20)
    
    def test_calculate_confidence_level_bounds(self):
        """Test confidence level bounds (0-100)"""
        # Test lower bound
        confidence_low = self.calculator.calculate_confidence_level(
            quote_count=1,
            variance_percentage=100.0,
            outlier_count=10
        )
        self.assertEqual(confidence_low, 0)
        
        # Test upper bound (should not exceed 100)
        confidence_high = self.calculator.calculate_confidence_level(
            quote_count=10,
            variance_percentage=5.0,
            outlier_count=0
        )
        self.assertEqual(confidence_high, 100)
    
    def test_identify_outliers_with_outliers(self):
        """Test outlier identification with clear outliers"""
        # Create quotes with one clear outlier
        test_data = [
            (500.00, 'assessor', 'Internal Assessor'),
            (520.00, 'dealer', 'Toyota Dealer'),
            (510.00, 'independent', 'Local Garage'),
            (800.00, 'network', 'Expensive Provider')  # Clear outlier
        ]
        quotes = self._create_test_quotes(test_data)
        
        # Identify outliers
        outliers = self.calculator.identify_outliers(quotes)
        
        # Should identify the expensive quote as outlier
        self.assertEqual(len(outliers), 1)
        self.assertEqual(float(outliers[0].total_cost), 800.00)
        self.assertEqual(outliers[0].provider_name, 'Expensive Provider')
    
    def test_identify_outliers_no_outliers(self):
        """Test outlier identification with no outliers"""
        # Create quotes with similar costs
        test_data = [
            (500.00, 'assessor', 'Internal Assessor'),
            (510.00, 'dealer', 'Toyota Dealer'),
            (520.00, 'independent', 'Local Garage'),
            (515.00, 'network', 'Insurance Network')
        ]
        quotes = self._create_test_quotes(test_data)
        
        # Identify outliers
        outliers = self.calculator.identify_outliers(quotes)
        
        # Should find no outliers
        self.assertEqual(len(outliers), 0)
    
    def test_identify_outliers_insufficient_quotes(self):
        """Test outlier identification with insufficient quotes"""
        # Create only 2 quotes (need at least 3 for outlier detection)
        test_data = [
            (500.00, 'assessor', 'Internal Assessor'),
            (520.00, 'dealer', 'Toyota Dealer')
        ]
        quotes = self._create_test_quotes(test_data)
        
        # Should return empty list
        outliers = self.calculator.identify_outliers(quotes)
        self.assertEqual(len(outliers), 0)
    
    def test_calculate_assessment_market_average_success(self):
        """Test assessment-level market average calculation"""
        # Create additional damaged part
        part2 = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Rear Bumper',
            part_category='body',
            damage_severity='minor',
            damage_description='Minor scratches',
            estimated_labor_hours=Decimal('1.5')
        )
        
        # Create quote request for second part
        quote_request2 = PartQuoteRequest.objects.create(
            damaged_part=part2,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            dispatched_by=self.user
        )
        
        # Create quotes for first part
        test_data1 = [
            (500.00, 'assessor', 'Internal Assessor'),
            (520.00, 'dealer', 'Toyota Dealer')
        ]
        self._create_test_quotes(test_data1)
        
        # Create quotes for second part
        for cost, provider_type, provider_name in [(300.00, 'assessor', 'Internal Assessor'), (320.00, 'dealer', 'Toyota Dealer')]:
            PartQuote.objects.create(
                quote_request=quote_request2,
                damaged_part=part2,
                provider_type=provider_type,
                provider_name=provider_name,
                part_cost=Decimal(str(cost * 0.7)),
                labor_cost=Decimal(str(cost * 0.25)),
                paint_cost=Decimal(str(cost * 0.05)),
                total_cost=Decimal(str(cost)),
                estimated_delivery_days=5,
                estimated_completion_days=7,
                valid_until=timezone.now() + timedelta(days=30),
                status='validated'
            )
        
        # Calculate assessment market average
        result = self.calculator.calculate_assessment_market_average(self.assessment)
        
        # Verify results
        self.assertEqual(result['total_parts'], 2)
        self.assertEqual(result['parts_with_averages'], 2)
        self.assertIsNotNone(result['market_average_total'])
        self.assertGreater(result['confidence_level'], 0)
        self.assertIsNotNone(result['price_range'])
        
        # Expected total: (500+520)/2 + (300+320)/2 = 510 + 310 = 820
        expected_total = Decimal('820.00')
        self.assertEqual(result['market_average_total'], expected_total)
    
    def test_calculate_assessment_market_average_no_parts(self):
        """Test assessment market average with no damaged parts"""
        # Create assessment without damaged parts
        empty_assessment = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now().date(),
            status='completed'
        )
        
        result = self.calculator.calculate_assessment_market_average(empty_assessment)
        
        # Should return empty result
        self.assertEqual(result['total_parts'], 0)
        self.assertEqual(result['parts_with_averages'], 0)
        self.assertIsNone(result['market_average_total'])
        self.assertEqual(result['confidence_level'], 0)
    
    def test_update_market_averages_batch_processing(self):
        """Test batch processing of market averages"""
        # Create quotes for the damaged part
        test_data = [
            (500.00, 'assessor', 'Internal Assessor'),
            (520.00, 'dealer', 'Toyota Dealer'),
            (480.00, 'independent', 'Local Garage')
        ]
        self._create_test_quotes(test_data)
        
        # Create second assessment with damaged part
        assessment2 = VehicleAssessment.objects.create(
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now().date(),
            status='completed'
        )
        
        part2 = DamagedPart.objects.create(
            assessment=assessment2,
            section_type='mechanical',
            part_name='Engine Mount',
            part_category='mechanical',
            damage_severity='severe',
            damage_description='Cracked engine mount',
            estimated_labor_hours=Decimal('3.0')
        )
        
        quote_request2 = PartQuoteRequest.objects.create(
            damaged_part=part2,
            assessment=assessment2,
            expiry_date=timezone.now() + timedelta(days=7),
            dispatched_by=self.user
        )
        
        # Create quotes for second part
        for cost, provider_type, provider_name in [(800.00, 'assessor', 'Internal Assessor'), (850.00, 'dealer', 'Toyota Dealer')]:
            PartQuote.objects.create(
                quote_request=quote_request2,
                damaged_part=part2,
                provider_type=provider_type,
                provider_name=provider_name,
                part_cost=Decimal(str(cost * 0.7)),
                labor_cost=Decimal(str(cost * 0.25)),
                paint_cost=Decimal(str(cost * 0.05)),
                total_cost=Decimal(str(cost)),
                estimated_delivery_days=5,
                estimated_completion_days=7,
                valid_until=timezone.now() + timedelta(days=30),
                status='validated'
            )
        
        # Run batch processing
        stats = self.calculator.update_market_averages(
            assessment_ids=[self.assessment.id, assessment2.id]
        )
        
        # Verify processing statistics
        self.assertEqual(stats['assessments_processed'], 2)
        self.assertEqual(stats['parts_processed'], 2)
        self.assertEqual(stats['averages_calculated'], 2)
        self.assertEqual(len(stats['errors']), 0)
        
        # Verify market averages were created
        self.assertTrue(PartMarketAverage.objects.filter(damaged_part=self.damaged_part).exists())
        self.assertTrue(PartMarketAverage.objects.filter(damaged_part=part2).exists())
    
    def test_update_market_averages_force_recalculate(self):
        """Test force recalculation of existing market averages"""
        # Create quotes and initial market average
        test_data = [
            (500.00, 'assessor', 'Internal Assessor'),
            (520.00, 'dealer', 'Toyota Dealer')
        ]
        self._create_test_quotes(test_data)
        
        # Calculate initial market average
        initial_avg = self.calculator.calculate_market_average(self.damaged_part)
        initial_confidence = initial_avg.confidence_level
        
        # Add more quotes to improve confidence
        additional_quotes = [
            (510.00, 'independent', 'Local Garage'),
            (515.00, 'network', 'Insurance Network')
        ]
        for cost, provider_type, provider_name in additional_quotes:
            PartQuote.objects.create(
                quote_request=self.quote_request,
                damaged_part=self.damaged_part,
                provider_type=provider_type,
                provider_name=provider_name,
                part_cost=Decimal(str(cost * 0.7)),
                labor_cost=Decimal(str(cost * 0.25)),
                paint_cost=Decimal(str(cost * 0.05)),
                total_cost=Decimal(str(cost)),
                estimated_delivery_days=5,
                estimated_completion_days=7,
                valid_until=timezone.now() + timedelta(days=30),
                status='validated'
            )
        
        # Force recalculation
        stats = self.calculator.update_market_averages(
            assessment_ids=[self.assessment.id],
            force_recalculate=True
        )
        
        # Verify recalculation occurred
        self.assertEqual(stats['averages_updated'], 1)
        
        # Verify confidence improved with more quotes
        updated_avg = PartMarketAverage.objects.get(damaged_part=self.damaged_part)
        self.assertGreater(updated_avg.confidence_level, initial_confidence)
        self.assertEqual(updated_avg.quote_count, 4)
    
    def test_update_market_averages_with_errors(self):
        """Test batch processing with some errors"""
        # Don't create any quotes (will cause InsufficientDataError)
        
        # Run batch processing
        stats = self.calculator.update_market_averages(
            assessment_ids=[self.assessment.id]
        )
        
        # Should process assessment but have no averages calculated
        self.assertEqual(stats['assessments_processed'], 1)
        self.assertEqual(stats['parts_processed'], 1)
        self.assertEqual(stats['averages_calculated'], 0)
    
    @patch('insurance_app.market_analysis.MarketAverageCalculator.calculate_market_average')
    def test_update_market_averages_exception_handling(self, mock_calculate):
        """Test exception handling in batch processing"""
        # Mock an exception during calculation
        mock_calculate.side_effect = Exception("Database error")
        
        # Create quotes to trigger calculation
        self._create_test_quotes([(500.00, 'assessor', 'Internal Assessor'), (520.00, 'dealer', 'Toyota Dealer')])
        
        # Run batch processing
        stats = self.calculator.update_market_averages(
            assessment_ids=[self.assessment.id]
        )
        
        # Should capture the error
        self.assertEqual(len(stats['errors']), 1)
        self.assertIn("Database error", stats['errors'][0])


class MarketAnalysisReporterTestCase(TestCase):
    """Test cases for MarketAnalysisReporter class"""
    
    def setUp(self):
        """Set up test data"""
        self.calculator = MarketAverageCalculator()
        self.reporter = MarketAnalysisReporter(self.calculator)
        
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
            vehicle=self.vehicle,
            assessor=self.user,
            assessment_date=timezone.now().date(),
            status='completed'
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
    
    def test_generate_part_analysis_report_with_data(self):
        """Test part analysis report generation with sufficient data"""
        # Create market average
        market_avg = PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('500.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('125.00'),
            min_total_cost=Decimal('480.00'),
            max_total_cost=Decimal('520.00'),
            standard_deviation=Decimal('15.00'),
            variance_percentage=Decimal('3.00'),
            quote_count=4,
            confidence_level=85
        )
        
        # Generate report
        report = self.reporter.generate_part_analysis_report(self.damaged_part)
        
        # Verify report structure and content
        self.assertEqual(report['part_name'], 'Front Bumper')
        self.assertEqual(report['part_category'], 'Body Panel')
        self.assertEqual(report['damage_severity'], 'Moderate Damage')
        
        # Verify market statistics
        stats = report['market_statistics']
        self.assertEqual(stats['average_cost'], 500.00)
        self.assertEqual(stats['price_range']['min'], 480.00)
        self.assertEqual(stats['price_range']['max'], 520.00)
        self.assertEqual(stats['standard_deviation'], 15.00)
        self.assertEqual(stats['variance_percentage'], 3.00)
        
        # Verify data quality metrics
        quality = report['data_quality']
        self.assertEqual(quality['quote_count'], 4)
        self.assertEqual(quality['confidence_level'], 85)
        self.assertTrue(quality['is_high_confidence'])
    
    def test_generate_part_analysis_report_insufficient_data(self):
        """Test part analysis report with insufficient data"""
        # Don't create market average or quotes
        
        # Generate report
        report = self.reporter.generate_part_analysis_report(self.damaged_part)
        
        # Should return error information
        self.assertIn('error', report)
        self.assertEqual(report['part_name'], 'Front Bumper')
        self.assertEqual(report['quotes_available'], 0)
    
    def test_generate_assessment_analysis_report(self):
        """Test assessment-level analysis report generation"""
        # Create market average for the part
        PartMarketAverage.objects.create(
            damaged_part=self.damaged_part,
            average_total_cost=Decimal('500.00'),
            average_part_cost=Decimal('350.00'),
            average_labor_cost=Decimal('125.00'),
            min_total_cost=Decimal('480.00'),
            max_total_cost=Decimal('520.00'),
            standard_deviation=Decimal('15.00'),
            variance_percentage=Decimal('3.00'),
            quote_count=4,
            confidence_level=85
        )
        
        # Generate assessment report
        report = self.reporter.generate_assessment_analysis_report(self.assessment)
        
        # Verify report structure
        self.assertEqual(report['assessment_id'], self.assessment.assessment_id)
        
        # Verify vehicle info
        vehicle_info = report['vehicle_info']
        self.assertEqual(vehicle_info['make'], 'Toyota')
        self.assertEqual(vehicle_info['model'], 'Camry')
        self.assertEqual(vehicle_info['year'], 2020)
        
        # Verify overall statistics
        stats = report['overall_statistics']
        self.assertEqual(stats['total_parts'], 1)
        self.assertEqual(stats['parts_with_averages'], 1)
        
        # Verify part analyses
        self.assertEqual(len(report['part_analyses']), 1)
        part_analysis = report['part_analyses'][0]
        self.assertEqual(part_analysis['part_name'], 'Front Bumper')
        
        # Verify summary
        summary = report['summary']
        self.assertEqual(summary['total_parts'], 1)
        self.assertEqual(summary['analyzable_parts'], 1)
        self.assertEqual(summary['coverage_percentage'], 100.0)
        self.assertEqual(summary['overall_confidence'], 85)