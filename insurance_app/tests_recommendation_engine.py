"""
Tests for Quote Recommendation Engine

This module contains comprehensive tests for the QuoteRecommendationEngine
including scoring algorithms, recommendation generation, and alternative strategies.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from .models import (
    DamagedPart, PartQuote, PartQuoteRequest, VehicleAssessment,
    AssessmentQuoteSummary
)
from .recommendation_engine import QuoteRecommendationEngine, QuoteScore, RecommendationResult
from assessments.models import VehicleAssessment as AssessmentModel
from vehicles.models import Vehicle


class QuoteRecommendationEngineTest(TestCase):
    """Test cases for QuoteRecommendationEngine"""
    
    def setUp(self):
        """Set up test data"""
        self.engine = QuoteRecommendationEngine()
        
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
        self.assessment = AssessmentModel.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            assessment_type='insurance_claim',
            status='in_progress',
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
        
        # Create damaged part
        self.damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Scratches and dent on front bumper',
            estimated_labor_hours=Decimal('2.5')
        )
        
        # Create quote request
        self.quote_request = PartQuoteRequest.objects.create(
            damaged_part=self.damaged_part,
            assessment=self.assessment,
            expiry_date=timezone.now() + timedelta(days=7),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            dispatched_by=self.user
        )
    
    def create_test_quote(self, provider_name, provider_type, total_cost,
                         part_type='oem', delivery_days=5, completion_days=7,
                         part_warranty=12, labor_warranty=12, confidence=80):
        """Helper method to create test quotes"""
        return PartQuote.objects.create(
            quote_request=self.quote_request,
            damaged_part=self.damaged_part,
            provider_name=provider_name,
            provider_type=provider_type,
            part_cost=Decimal(str(total_cost * 0.7)),
            labor_cost=Decimal(str(total_cost * 0.25)),
            paint_cost=Decimal(str(total_cost * 0.05)),
            additional_costs=Decimal('0'),
            total_cost=Decimal(str(total_cost)),
            part_type=part_type,
            estimated_delivery_days=delivery_days,
            estimated_completion_days=completion_days,
            part_warranty_months=part_warranty,
            labor_warranty_months=labor_warranty,
            confidence_score=confidence,
            valid_until=timezone.now() + timedelta(days=30),
            status='validated'
        )
    
    def test_engine_initialization(self):
        """Test engine initialization with default and custom weights"""
        # Test default weights
        engine = QuoteRecommendationEngine()
        self.assertEqual(engine.weights['price'], 0.40)
        self.assertEqual(engine.weights['quality'], 0.25)
        self.assertEqual(engine.weights['timeline'], 0.15)
        self.assertEqual(engine.weights['warranty'], 0.10)
        self.assertEqual(engine.weights['reliability'], 0.10)
        
        # Test custom weights
        custom_weights = {
            'price': 0.50,
            'quality': 0.20,
            'timeline': 0.15,
            'warranty': 0.10,
            'reliability': 0.05
        }
        engine = QuoteRecommendationEngine(custom_weights)
        self.assertEqual(engine.weights['price'], 0.50)
        
        # Test invalid weights
        with self.assertRaises(ValueError):
            QuoteRecommendationEngine({'price': 0.60, 'quality': 0.60})
    
    def test_calculate_price_score(self):
        """Test price score calculation"""
        quote1 = self.create_test_quote('Provider A', 'dealer', 1000)
        quote2 = self.create_test_quote('Provider B', 'independent', 800)
        quote3 = self.create_test_quote('Provider C', 'network', 1200)
        
        quotes = [quote1, quote2, quote3]
        costs = [1000, 800, 1200]
        min_cost, max_cost = min(costs), max(costs)
        avg_cost = sum(costs) / len(costs)
        
        # Lowest cost should get highest score
        score_low = self.engine.calculate_price_score(quote2, min_cost, max_cost, avg_cost)
        score_high = self.engine.calculate_price_score(quote3, min_cost, max_cost, avg_cost)
        
        self.assertGreater(score_low, score_high)
        self.assertEqual(score_low, 100.0)  # Lowest cost gets perfect score
        self.assertEqual(score_high, 0.0)   # Highest cost gets zero score
    
    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        # Test different part types
        oem_quote = self.create_test_quote('Dealer', 'dealer', 1000, 'oem', confidence=90)
        aftermarket_quote = self.create_test_quote('Shop', 'independent', 800, 'aftermarket_standard', confidence=70)
        
        oem_score = self.engine.calculate_quality_score(oem_quote)
        aftermarket_score = self.engine.calculate_quality_score(aftermarket_quote)
        
        self.assertGreater(oem_score, aftermarket_score)
        self.assertGreaterEqual(oem_score, 80)  # OEM from dealer should score high
    
    def test_calculate_timeline_score(self):
        """Test timeline score calculation"""
        fast_quote = self.create_test_quote('Fast Provider', 'network', 1000, delivery_days=2, completion_days=3)
        slow_quote = self.create_test_quote('Slow Provider', 'independent', 900, delivery_days=10, completion_days=14)
        
        quotes = [fast_quote, slow_quote]
        delivery_days = [2, 10]
        completion_days = [3, 14]
        
        min_delivery, avg_delivery = min(delivery_days), sum(delivery_days) / len(delivery_days)
        min_completion, avg_completion = min(completion_days), sum(completion_days) / len(completion_days)
        
        fast_score = self.engine.calculate_timeline_score(
            fast_quote, min_delivery, min_completion, avg_delivery, avg_completion
        )
        slow_score = self.engine.calculate_timeline_score(
            slow_quote, min_delivery, min_completion, avg_delivery, avg_completion
        )
        
        self.assertGreater(fast_score, slow_score)
    
    def test_calculate_warranty_score(self):
        """Test warranty score calculation"""
        good_warranty = self.create_test_quote('Provider A', 'dealer', 1000, part_warranty=24, labor_warranty=12)
        basic_warranty = self.create_test_quote('Provider B', 'independent', 900, part_warranty=12, labor_warranty=6)
        
        good_score = self.engine.calculate_warranty_score(good_warranty)
        basic_score = self.engine.calculate_warranty_score(basic_warranty)
        
        self.assertGreater(good_score, basic_score)
        self.assertEqual(good_score, 100.0)  # 24 month part + 12 month labor = perfect score
    
    def test_calculate_reliability_score(self):
        """Test reliability score calculation"""
        dealer_quote = self.create_test_quote('Toyota Dealer', 'dealer', 1200, confidence=95)
        dealer_quote.part_number_quoted = 'TOY-12345'
        dealer_quote.part_manufacturer = 'Toyota'
        dealer_quote.notes = 'OEM part with full documentation'
        dealer_quote.save()
        
        independent_quote = self.create_test_quote('Local Shop', 'independent', 800, confidence=70)
        
        dealer_score = self.engine.calculate_reliability_score(dealer_quote)
        independent_score = self.engine.calculate_reliability_score(independent_quote)
        
        self.assertGreater(dealer_score, independent_score)
    
    def test_calculate_provider_scores(self):
        """Test comprehensive provider scoring"""
        quote1 = self.create_test_quote('Dealer A', 'dealer', 1200, 'oem', 3, 5, 24, 12, 95)
        quote2 = self.create_test_quote('Shop B', 'independent', 800, 'aftermarket_standard', 7, 10, 12, 6, 75)
        quote3 = self.create_test_quote('Network C', 'network', 1000, 'oem_equivalent', 5, 7, 18, 12, 85)
        
        quotes = [quote1, quote2, quote3]
        scores = self.engine.calculate_provider_scores(quotes)
        
        self.assertEqual(len(scores), 3)
        
        # Check that all scores are QuoteScore objects
        for quote_id, score in scores.items():
            self.assertIsInstance(score, QuoteScore)
            self.assertGreaterEqual(score.total_score, 0)
            self.assertLessEqual(score.total_score, 100)
            self.assertIsInstance(score.reasoning, str)
            self.assertGreater(len(score.reasoning), 0)
    
    def test_generate_recommendation_single_quote(self):
        """Test recommendation generation with single quote"""
        quote = self.create_test_quote('Only Provider', 'dealer', 1000)
        
        result = self.engine.generate_recommendation(self.damaged_part)
        
        self.assertIsInstance(result, RecommendationResult)
        self.assertEqual(len(result.recommended_quotes), 1)
        self.assertEqual(result.recommended_quotes[0], quote)
        self.assertEqual(result.total_cost, Decimal('1000'))
        self.assertEqual(result.potential_savings, Decimal('0'))
        self.assertGreater(len(result.reasoning), 0)
    
    def test_generate_recommendation_multiple_quotes(self):
        """Test recommendation generation with multiple quotes"""
        quote1 = self.create_test_quote('Expensive Dealer', 'dealer', 1500, 'oem', 3, 5, 24, 12, 95)
        quote2 = self.create_test_quote('Cheap Shop', 'independent', 700, 'aftermarket_standard', 10, 14, 12, 6, 60)
        quote3 = self.create_test_quote('Balanced Network', 'network', 1000, 'oem_equivalent', 5, 7, 18, 12, 85)
        
        result = self.engine.generate_recommendation(self.damaged_part)
        
        self.assertIsInstance(result, RecommendationResult)
        self.assertEqual(len(result.recommended_quotes), 1)
        self.assertIn('alternative_strategies', result.__dict__)
        self.assertGreater(result.potential_savings, 0)
        self.assertGreater(result.confidence_level, 0)
        self.assertLessEqual(result.confidence_level, 100)
    
    def test_generate_recommendation_no_quotes(self):
        """Test recommendation generation with no quotes"""
        result = self.engine.generate_recommendation(self.damaged_part)
        
        self.assertEqual(len(result.recommended_quotes), 0)
        self.assertEqual(result.total_cost, Decimal('0'))
        self.assertEqual(result.potential_savings, Decimal('0'))
        self.assertEqual(result.confidence_level, 0)
        self.assertIn("No validated quotes", result.reasoning)
    
    def test_alternative_strategies(self):
        """Test alternative strategy generation"""
        # Create quotes with different strengths
        expensive_fast = self.create_test_quote('Fast Dealer', 'dealer', 1500, 'oem', 1, 2, 24, 12, 95)
        cheap_slow = self.create_test_quote('Cheap Shop', 'independent', 600, 'aftermarket_standard', 14, 21, 12, 6, 60)
        balanced = self.create_test_quote('Network', 'network', 1000, 'oem_equivalent', 5, 7, 18, 12, 85)
        
        quotes = [expensive_fast, cheap_slow, balanced]
        scores = self.engine.calculate_provider_scores(quotes)
        alternatives = self.engine._generate_alternative_strategies(quotes, scores)
        
        self.assertIn('lowest_price', alternatives)
        self.assertIn('fastest_completion', alternatives)
        self.assertIn('highest_quality', alternatives)
        
        # Verify strategies pick correct quotes
        self.assertEqual(alternatives['lowest_price'][0], cheap_slow)
        self.assertEqual(alternatives['fastest_completion'][0], expensive_fast)
    
    def test_potential_savings_calculator(self):
        """Test potential savings calculation"""
        quote1 = self.create_test_quote('Expensive', 'dealer', 1500)
        quote2 = self.create_test_quote('Moderate', 'network', 1000)
        quote3 = self.create_test_quote('Cheap', 'independent', 700)
        
        quotes = [quote1, quote2, quote3]
        savings = self.engine.potential_savings_calculator(quotes)
        
        self.assertEqual(savings['max_savings'], Decimal('800'))  # 1500 - 700
        self.assertEqual(savings['highest_quote'], Decimal('1500'))
        self.assertEqual(savings['lowest_quote'], Decimal('700'))
        self.assertAlmostEqual(float(savings['savings_percentage']), 53.33, places=1)
    
    def test_potential_savings_calculator_single_quote(self):
        """Test potential savings with single quote"""
        quote = self.create_test_quote('Only Provider', 'dealer', 1000)
        
        savings = self.engine.potential_savings_calculator([quote])
        
        self.assertEqual(savings['max_savings'], Decimal('0'))
        self.assertEqual(savings['savings_percentage'], Decimal('0'))
    
    def test_custom_weights_impact(self):
        """Test that custom weights impact scoring"""
        # Create quotes where price and quality favor different providers
        cheap_low_quality = self.create_test_quote('Cheap Shop', 'independent', 600, 'generic', confidence=50)
        expensive_high_quality = self.create_test_quote('Premium Dealer', 'dealer', 1400, 'oem', confidence=95)
        
        quotes = [cheap_low_quality, expensive_high_quality]
        
        # Test with price-focused weights
        price_focused_engine = QuoteRecommendationEngine({
            'price': 0.70, 'quality': 0.10, 'timeline': 0.10, 'warranty': 0.05, 'reliability': 0.05
        })
        price_scores = price_focused_engine.calculate_provider_scores(quotes)
        
        # Test with quality-focused weights
        quality_focused_engine = QuoteRecommendationEngine({
            'price': 0.10, 'quality': 0.70, 'timeline': 0.10, 'warranty': 0.05, 'reliability': 0.05
        })
        quality_scores = quality_focused_engine.calculate_provider_scores(quotes)
        
        # Price-focused should favor cheap quote
        cheap_price_score = price_scores[cheap_low_quality.id].total_score
        expensive_price_score = price_scores[expensive_high_quality.id].total_score
        
        # Quality-focused should favor expensive quote
        cheap_quality_score = quality_scores[cheap_low_quality.id].total_score
        expensive_quality_score = quality_scores[expensive_high_quality.id].total_score
        
        self.assertGreater(cheap_price_score, expensive_price_score)
        self.assertGreater(expensive_quality_score, cheap_quality_score)
    
    def test_confidence_level_calculation(self):
        """Test confidence level calculation"""
        # Single quote should have lower confidence
        single_quote = [self.create_test_quote('Only Provider', 'dealer', 1000)]
        single_scores = self.engine.calculate_provider_scores(single_quote)
        single_confidence = self.engine._calculate_confidence_level(single_quote, single_scores)
        
        # Multiple quotes should have higher confidence
        multiple_quotes = [
            self.create_test_quote('Provider A', 'dealer', 1200, confidence=90),
            self.create_test_quote('Provider B', 'network', 1000, confidence=85),
            self.create_test_quote('Provider C', 'independent', 800, confidence=75)
        ]
        multiple_scores = self.engine.calculate_provider_scores(multiple_quotes)
        multiple_confidence = self.engine._calculate_confidence_level(multiple_quotes, multiple_scores)
        
        self.assertGreater(multiple_confidence, single_confidence)
        self.assertGreaterEqual(single_confidence, 30)
        self.assertLessEqual(multiple_confidence, 95)
    
    def test_score_reasoning_generation(self):
        """Test score reasoning text generation"""
        quote = self.create_test_quote('Test Provider', 'dealer', 1000)
        
        reasoning = self.engine._generate_score_reasoning(
            quote, 85.0, 90.0, 75.0, 80.0, 88.0, 84.5
        )
        
        self.assertIsInstance(reasoning, str)
        self.assertGreater(len(reasoning), 20)
        self.assertIn("84.5", reasoning)  # Should include total score
        self.assertIn("Excellent price", reasoning)  # Should describe price performance
    
    def test_recommendation_reasoning_generation(self):
        """Test recommendation reasoning generation"""
        quote1 = self.create_test_quote('Best Provider', 'dealer', 1000, confidence=95)
        quote2 = self.create_test_quote('Cheap Provider', 'independent', 700, confidence=70)
        
        quotes = [quote1, quote2]
        scores = self.engine.calculate_provider_scores(quotes)
        alternatives = self.engine._generate_alternative_strategies(quotes, scores)
        
        reasoning = self.engine._generate_recommendation_reasoning(
            quote1, scores[quote1.id], quotes, alternatives
        )
        
        self.assertIsInstance(reasoning, str)
        self.assertGreater(len(reasoning), 30)
        self.assertIn("Best Provider", reasoning)
        self.assertIn("Score:", reasoning)