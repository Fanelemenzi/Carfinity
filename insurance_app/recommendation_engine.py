"""
Quote Recommendation Engine

This module provides intelligent quote analysis and recommendation capabilities
for the parts-based quote system. It evaluates quotes based on multiple criteria
and generates recommendations with reasoning.
"""

from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from dataclasses import dataclass
from .models import PartQuote, DamagedPart, AssessmentQuoteSummary


@dataclass
class QuoteScore:
    """Data class for storing quote scores and breakdown"""
    total_score: float
    price_score: float
    quality_score: float
    timeline_score: float
    warranty_score: float
    reliability_score: float
    reasoning: str


@dataclass
class RecommendationResult:
    """Data class for recommendation results"""
    recommended_quotes: List[PartQuote]
    alternative_strategies: Dict[str, List[PartQuote]]
    total_cost: Decimal
    potential_savings: Decimal
    reasoning: str
    confidence_level: int


class QuoteRecommendationEngine:
    """
    Intelligent quote recommendation engine that evaluates quotes based on
    weighted criteria and generates recommendations with detailed reasoning.
    """
    
    # Default scoring weights (can be customized)
    DEFAULT_WEIGHTS = {
        'price': 0.40,      # 40% weight on price
        'quality': 0.25,    # 25% weight on quality
        'timeline': 0.15,   # 15% weight on timeline
        'warranty': 0.10,   # 10% weight on warranty
        'reliability': 0.10 # 10% weight on reliability
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the recommendation engine with custom weights if provided.
        
        Args:
            weights: Custom scoring weights dictionary
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
    
    def _validate_weights(self):
        """Validate that weights sum to 1.0"""
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def calculate_provider_scores(self, quotes: List[PartQuote]) -> Dict[int, QuoteScore]:
        """
        Calculate comprehensive scores for all quotes using weighted criteria.
        
        Args:
            quotes: List of PartQuote objects to evaluate
            
        Returns:
            Dictionary mapping quote IDs to QuoteScore objects
        """
        if not quotes:
            return {}
        
        scores = {}
        
        # Calculate market statistics for relative scoring
        total_costs = [float(quote.total_cost) for quote in quotes]
        avg_cost = sum(total_costs) / len(total_costs)
        min_cost = min(total_costs)
        max_cost = max(total_costs)
        
        delivery_days = [quote.estimated_delivery_days for quote in quotes]
        avg_delivery = sum(delivery_days) / len(delivery_days)
        min_delivery = min(delivery_days)
        
        completion_days = [quote.estimated_completion_days for quote in quotes]
        avg_completion = sum(completion_days) / len(completion_days)
        min_completion = min(completion_days)
        
        for quote in quotes:
            price_score = self.calculate_price_score(quote, min_cost, max_cost, avg_cost)
            quality_score = self.calculate_quality_score(quote)
            timeline_score = self.calculate_timeline_score(
                quote, min_delivery, min_completion, avg_delivery, avg_completion
            )
            warranty_score = self.calculate_warranty_score(quote)
            reliability_score = self.calculate_reliability_score(quote)
            
            # Calculate weighted total score
            total_score = (
                price_score * self.weights['price'] +
                quality_score * self.weights['quality'] +
                timeline_score * self.weights['timeline'] +
                warranty_score * self.weights['warranty'] +
                reliability_score * self.weights['reliability']
            )
            
            reasoning = self._generate_score_reasoning(
                quote, price_score, quality_score, timeline_score,
                warranty_score, reliability_score, total_score
            )
            
            scores[quote.id] = QuoteScore(
                total_score=total_score,
                price_score=price_score,
                quality_score=quality_score,
                timeline_score=timeline_score,
                warranty_score=warranty_score,
                reliability_score=reliability_score,
                reasoning=reasoning
            )
        
        return scores
    
    def calculate_price_score(self, quote: PartQuote, min_cost: float, 
                            max_cost: float, avg_cost: float) -> float:
        """
        Calculate price competitiveness score (0-100).
        Lower prices get higher scores.
        
        Args:
            quote: PartQuote object
            min_cost: Minimum cost among all quotes
            max_cost: Maximum cost among all quotes
            avg_cost: Average cost among all quotes
            
        Returns:
            Price score (0-100)
        """
        cost = float(quote.total_cost)
        
        if max_cost == min_cost:
            return 100.0  # All quotes have same price
        
        # Normalize cost to 0-1 range (inverted so lower cost = higher score)
        normalized_cost = 1.0 - ((cost - min_cost) / (max_cost - min_cost))
        
        # Apply bonus for being significantly below average
        if cost < avg_cost * 0.9:
            normalized_cost = min(1.0, normalized_cost * 1.1)
        
        return normalized_cost * 100
    
    def calculate_quality_score(self, quote: PartQuote) -> float:
        """
        Calculate quality score based on part type, provider type, and confidence.
        
        Args:
            quote: PartQuote object
            
        Returns:
            Quality score (0-100)
        """
        base_score = 50.0
        
        # Part type scoring
        part_type_scores = {
            'oem': 100,
            'oem_equivalent': 85,
            'aftermarket_premium': 75,
            'aftermarket_standard': 60,
            'used_oem': 70,
            'refurbished': 55,
            'generic': 40
        }
        part_score = part_type_scores.get(quote.part_type, 50)
        
        # Provider type scoring
        provider_type_scores = {
            'dealer': 90,
            'assessor': 85,
            'network': 80,
            'independent': 70
        }
        provider_score = provider_type_scores.get(quote.provider_type, 60)
        
        # Confidence score (already 0-100)
        confidence_score = quote.confidence_score
        
        # Weighted combination
        quality_score = (
            part_score * 0.5 +
            provider_score * 0.3 +
            confidence_score * 0.2
        )
        
        return min(100.0, quality_score)
    
    def calculate_timeline_score(self, quote: PartQuote, min_delivery: int,
                               min_completion: int, avg_delivery: float,
                               avg_completion: float) -> float:
        """
        Calculate timeline score based on delivery and completion times.
        Faster timelines get higher scores.
        
        Args:
            quote: PartQuote object
            min_delivery: Minimum delivery days among all quotes
            min_completion: Minimum completion days among all quotes
            avg_delivery: Average delivery days
            avg_completion: Average completion days
            
        Returns:
            Timeline score (0-100)
        """
        delivery_days = quote.estimated_delivery_days
        completion_days = quote.estimated_completion_days
        
        # Score delivery time (0-100, faster = higher)
        if avg_delivery > min_delivery:
            delivery_score = max(0, 100 - ((delivery_days - min_delivery) / 
                                         (avg_delivery - min_delivery)) * 50)
        else:
            delivery_score = 100 if delivery_days == min_delivery else 90
        
        # Score completion time (0-100, faster = higher)
        if avg_completion > min_completion:
            completion_score = max(0, 100 - ((completion_days - min_completion) / 
                                            (avg_completion - min_completion)) * 50)
        else:
            completion_score = 100 if completion_days == min_completion else 90
        
        # Weighted combination (delivery is more important)
        timeline_score = delivery_score * 0.6 + completion_score * 0.4
        
        return timeline_score
    
    def calculate_warranty_score(self, quote: PartQuote) -> float:
        """
        Calculate warranty score based on part and labor warranty periods.
        
        Args:
            quote: PartQuote object
            
        Returns:
            Warranty score (0-100)
        """
        part_warranty = quote.part_warranty_months
        labor_warranty = quote.labor_warranty_months
        
        # Score part warranty (12 months = 50 points, 24+ months = 100 points)
        part_score = min(100, (part_warranty / 12) * 50)
        if part_warranty >= 24:
            part_score = 100
        
        # Score labor warranty (6 months = 50 points, 12+ months = 100 points)
        labor_score = min(100, (labor_warranty / 6) * 50)
        if labor_warranty >= 12:
            labor_score = 100
        
        # Weighted combination
        warranty_score = part_score * 0.7 + labor_score * 0.3
        
        return warranty_score
    
    def calculate_reliability_score(self, quote: PartQuote) -> float:
        """
        Calculate reliability score based on provider history and quote completeness.
        
        Args:
            quote: PartQuote object
            
        Returns:
            Reliability score (0-100)
        """
        base_score = 70.0
        
        # Provider type reliability
        provider_reliability = {
            'dealer': 95,
            'assessor': 90,
            'network': 85,
            'independent': 75
        }
        provider_score = provider_reliability.get(quote.provider_type, 70)
        
        # Quote completeness bonus
        completeness_bonus = 0
        if quote.part_number_quoted:
            completeness_bonus += 5
        if quote.part_manufacturer:
            completeness_bonus += 5
        if quote.notes:
            completeness_bonus += 5
        
        # Confidence factor
        confidence_factor = quote.confidence_score / 100
        
        reliability_score = (provider_score + completeness_bonus) * confidence_factor
        
        return min(100.0, reliability_score)
    
    def generate_recommendation(self, damaged_part: DamagedPart) -> RecommendationResult:
        """
        Generate comprehensive recommendation for a damaged part.
        
        Args:
            damaged_part: DamagedPart object to generate recommendations for
            
        Returns:
            RecommendationResult with recommendations and alternatives
        """
        quotes = list(damaged_part.quotes.filter(status='validated'))
        
        if not quotes:
            return RecommendationResult(
                recommended_quotes=[],
                alternative_strategies={},
                total_cost=Decimal('0'),
                potential_savings=Decimal('0'),
                reasoning="No validated quotes available for recommendation.",
                confidence_level=0
            )
        
        # Calculate scores for all quotes
        scores = self.calculate_provider_scores(quotes)
        
        # Sort quotes by total score (highest first)
        sorted_quotes = sorted(quotes, key=lambda q: scores[q.id].total_score, reverse=True)
        
        # Primary recommendation (highest scoring quote)
        recommended_quote = sorted_quotes[0]
        
        # Generate alternative strategies
        alternatives = self._generate_alternative_strategies(quotes, scores)
        
        # Calculate potential savings
        costs = [float(q.total_cost) for q in quotes]
        max_cost = max(costs)
        recommended_cost = float(recommended_quote.total_cost)
        potential_savings = Decimal(str(max_cost - recommended_cost))
        
        # Generate reasoning
        reasoning = self._generate_recommendation_reasoning(
            recommended_quote, scores[recommended_quote.id], quotes, alternatives
        )
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(quotes, scores)
        
        return RecommendationResult(
            recommended_quotes=[recommended_quote],
            alternative_strategies=alternatives,
            total_cost=recommended_quote.total_cost,
            potential_savings=potential_savings,
            reasoning=reasoning,
            confidence_level=confidence_level
        )
    
    def _generate_alternative_strategies(self, quotes: List[PartQuote], 
                                       scores: Dict[int, QuoteScore]) -> Dict[str, List[PartQuote]]:
        """Generate alternative recommendation strategies"""
        alternatives = {}
        
        if len(quotes) < 2:
            return alternatives
        
        # Lowest price strategy
        price_sorted = sorted(quotes, key=lambda q: q.total_cost)
        alternatives['lowest_price'] = [price_sorted[0]]
        
        # Fastest completion strategy
        timeline_sorted = sorted(quotes, key=lambda q: q.estimated_completion_days)
        alternatives['fastest_completion'] = [timeline_sorted[0]]
        
        # Highest quality strategy
        quality_sorted = sorted(quotes, key=lambda q: scores[q.id].quality_score, reverse=True)
        alternatives['highest_quality'] = [quality_sorted[0]]
        
        return alternatives
    
    def potential_savings_calculator(self, quotes: List[PartQuote]) -> Dict[str, Decimal]:
        """
        Calculate potential savings by comparing against highest quotes.
        
        Args:
            quotes: List of PartQuote objects
            
        Returns:
            Dictionary with savings calculations
        """
        if len(quotes) < 2:
            return {
                'max_savings': Decimal('0'),
                'avg_savings': Decimal('0'),
                'savings_percentage': Decimal('0')
            }
        
        costs = [q.total_cost for q in quotes]
        max_cost = max(costs)
        min_cost = min(costs)
        avg_cost = sum(costs) / len(costs)
        
        max_savings = max_cost - min_cost
        avg_savings = max_cost - avg_cost
        savings_percentage = (max_savings / max_cost) * 100 if max_cost > 0 else Decimal('0')
        
        return {
            'max_savings': max_savings,
            'avg_savings': avg_savings,
            'savings_percentage': savings_percentage,
            'highest_quote': max_cost,
            'lowest_quote': min_cost,
            'average_quote': avg_cost
        }
    
    def _generate_score_reasoning(self, quote: PartQuote, price_score: float,
                                quality_score: float, timeline_score: float,
                                warranty_score: float, reliability_score: float,
                                total_score: float) -> str:
        """Generate reasoning text for quote scoring"""
        reasoning_parts = []
        
        # Price analysis
        if price_score >= 80:
            reasoning_parts.append("Excellent price competitiveness")
        elif price_score >= 60:
            reasoning_parts.append("Good price point")
        else:
            reasoning_parts.append("Higher cost option")
        
        # Quality analysis
        if quality_score >= 80:
            reasoning_parts.append("high quality components")
        elif quality_score >= 60:
            reasoning_parts.append("standard quality parts")
        else:
            reasoning_parts.append("basic quality level")
        
        # Timeline analysis
        if timeline_score >= 80:
            reasoning_parts.append("fast delivery and completion")
        elif timeline_score >= 60:
            reasoning_parts.append("reasonable timeline")
        else:
            reasoning_parts.append("longer completion time")
        
        return f"Score: {total_score:.1f}/100 - {', '.join(reasoning_parts)}."
    
    def _generate_recommendation_reasoning(self, recommended_quote: PartQuote,
                                         recommended_score: QuoteScore,
                                         all_quotes: List[PartQuote],
                                         alternatives: Dict[str, List[PartQuote]]) -> str:
        """Generate comprehensive reasoning for the recommendation"""
        reasoning_parts = []
        
        # Primary recommendation reasoning
        reasoning_parts.append(
            f"Recommended: {recommended_quote.provider_name} "
            f"(Score: {recommended_score.total_score:.1f}/100)"
        )
        
        # Highlight key strengths
        strengths = []
        if recommended_score.price_score >= 80:
            strengths.append("competitive pricing")
        if recommended_score.quality_score >= 80:
            strengths.append("high quality")
        if recommended_score.timeline_score >= 80:
            strengths.append("fast completion")
        if recommended_score.warranty_score >= 80:
            strengths.append("excellent warranty")
        
        if strengths:
            reasoning_parts.append(f"Key strengths: {', '.join(strengths)}")
        
        # Alternative mentions
        if 'lowest_price' in alternatives:
            lowest_price_quote = alternatives['lowest_price'][0]
            if lowest_price_quote.id != recommended_quote.id:
                savings = recommended_quote.total_cost - lowest_price_quote.total_cost
                reasoning_parts.append(
                    f"Alternative: {lowest_price_quote.provider_name} "
                    f"offers £{savings:.2f} savings but lower overall value"
                )
        
        return ". ".join(reasoning_parts) + "."
    
    def _calculate_confidence_level(self, quotes: List[PartQuote], 
                                  scores: Dict[int, QuoteScore]) -> int:
        """Calculate confidence level for the recommendation"""
        if len(quotes) < 2:
            return 50  # Low confidence with only one quote
        
        # Base confidence on number of quotes
        base_confidence = min(80, 40 + (len(quotes) * 10))
        
        # Adjust based on score spread
        total_scores = [scores[q.id].total_score for q in quotes]
        score_range = max(total_scores) - min(total_scores)
        
        if score_range > 20:
            base_confidence += 10  # Clear winner increases confidence
        elif score_range < 5:
            base_confidence -= 10  # Close scores reduce confidence
        
        # Adjust based on quote quality
        avg_confidence = sum(q.confidence_score for q in quotes) / len(quotes)
        if avg_confidence >= 80:
            base_confidence += 5
        elif avg_confidence < 60:
            base_confidence -= 5
        
        return max(30, min(95, base_confidence))