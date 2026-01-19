"""
Market Average Calculator for Parts-Based Quote System

This module provides comprehensive market analysis functionality for calculating
statistical averages, identifying outliers, and determining confidence levels
for parts-based quotes in the insurance assessment system.
"""

import statistics
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count, Q
from .models import (
    DamagedPart, 
    PartQuote, 
    PartMarketAverage, 
    AssessmentQuoteSummary,
    VehicleAssessment
)


class InsufficientDataError(Exception):
    """Raised when insufficient quote data is available for market analysis"""
    pass


class MarketAverageCalculator:
    """
    Calculator for market averages and statistical analysis of parts quotes.
    
    This class provides methods to:
    - Calculate comprehensive market statistics for individual parts
    - Identify statistical outliers using 2-standard-deviation rule
    - Determine confidence levels based on data quality and variance
    - Calculate assessment-level market averages
    - Batch process market averages for multiple assessments
    """
    
    def __init__(self):
        self.minimum_quotes_required = 2
        self.outlier_threshold_std_dev = 2.0
        self.high_confidence_threshold = 70
        self.minimum_high_confidence_quotes = 3
    
    def calculate_market_average(self, damaged_part: DamagedPart) -> PartMarketAverage:
        """
        Calculate comprehensive market statistics for a damaged part.
        
        Args:
            damaged_part: DamagedPart instance to calculate averages for
            
        Returns:
            PartMarketAverage instance with calculated statistics
            
        Raises:
            InsufficientDataError: If fewer than minimum required quotes available
        """
        # Get valid quotes for this part
        valid_quotes = self._get_valid_quotes(damaged_part)
        
        if len(valid_quotes) < self.minimum_quotes_required:
            raise InsufficientDataError(
                f"Need at least {self.minimum_quotes_required} quotes for market analysis. "
                f"Found {len(valid_quotes)} quotes."
            )
        
        # Extract cost data
        total_costs = [float(quote.total_cost) for quote in valid_quotes]
        part_costs = [float(quote.part_cost) for quote in valid_quotes]
        labor_costs = [float(quote.labor_cost) for quote in valid_quotes]
        
        # Calculate basic statistics
        avg_total = statistics.mean(total_costs)
        avg_part = statistics.mean(part_costs)
        avg_labor = statistics.mean(labor_costs)
        
        min_total = min(total_costs)
        max_total = max(total_costs)
        
        # Calculate variance and standard deviation
        if len(total_costs) > 1:
            std_dev = statistics.stdev(total_costs)
            variance_pct = (std_dev / avg_total) * 100 if avg_total > 0 else 0
        else:
            std_dev = 0
            variance_pct = 0
        
        # Identify outliers
        outliers = self.identify_outliers(valid_quotes)
        outlier_data = [
            {
                'quote_id': quote.id,
                'provider_name': quote.provider_name,
                'total_cost': float(quote.total_cost),
                'deviation_from_mean': float(quote.total_cost) - avg_total
            }
            for quote in outliers
        ]
        
        # Calculate confidence level
        confidence = self.calculate_confidence_level(
            quote_count=len(valid_quotes),
            variance_percentage=variance_pct,
            outlier_count=len(outliers)
        )
        
        # Create or update market average record
        market_average, created = PartMarketAverage.objects.update_or_create(
            damaged_part=damaged_part,
            defaults={
                'average_total_cost': Decimal(str(avg_total)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                'average_part_cost': Decimal(str(avg_part)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                'average_labor_cost': Decimal(str(avg_labor)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                'min_total_cost': Decimal(str(min_total)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                'max_total_cost': Decimal(str(max_total)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                'standard_deviation': Decimal(str(std_dev)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                'variance_percentage': Decimal(str(variance_pct)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                ),
                'quote_count': len(valid_quotes),
                'confidence_level': confidence,
                'outlier_quotes': outlier_data,
                'last_updated': timezone.now()
            }
        )
        
        return market_average
    
    def calculate_confidence_level(
        self, 
        quote_count: int, 
        variance_percentage: float, 
        outlier_count: int = 0
    ) -> int:
        """
        Calculate confidence level based on data quality metrics.
        
        Args:
            quote_count: Number of quotes available
            variance_percentage: Price variance as percentage
            outlier_count: Number of outlier quotes identified
            
        Returns:
            Confidence level as integer (0-100)
        """
        # Base confidence from quote count
        if quote_count >= 5:
            base_confidence = 90
        elif quote_count >= 3:
            base_confidence = 70
        elif quote_count >= 2:
            base_confidence = 50
        else:
            base_confidence = 20
        
        # Adjust for variance (lower variance = higher confidence)
        if variance_percentage <= 10:
            variance_adjustment = 10
        elif variance_percentage <= 20:
            variance_adjustment = 5
        elif variance_percentage <= 30:
            variance_adjustment = 0
        elif variance_percentage <= 50:
            variance_adjustment = -10
        else:
            variance_adjustment = -20
        
        # Adjust for outliers (more outliers = lower confidence)
        outlier_adjustment = -5 * outlier_count
        
        # Calculate final confidence
        confidence = base_confidence + variance_adjustment + outlier_adjustment
        
        # Ensure confidence is within bounds
        return max(0, min(100, confidence))
    
    def identify_outliers(self, quotes: List[PartQuote]) -> List[PartQuote]:
        """
        Identify statistical outliers using 2-standard-deviation rule.
        
        Args:
            quotes: List of PartQuote instances to analyze
            
        Returns:
            List of PartQuote instances that are statistical outliers
        """
        if len(quotes) < 3:
            return []  # Need at least 3 quotes to identify outliers
        
        total_costs = [float(quote.total_cost) for quote in quotes]
        
        # Calculate mean and standard deviation
        mean_cost = statistics.mean(total_costs)
        
        if len(total_costs) < 2:
            return []
        
        std_dev = statistics.stdev(total_costs)
        
        # Identify outliers (beyond 2 standard deviations)
        outliers = []
        threshold = self.outlier_threshold_std_dev * std_dev
        
        for quote in quotes:
            cost = float(quote.total_cost)
            deviation = abs(cost - mean_cost)
            
            if deviation > threshold:
                outliers.append(quote)
        
        return outliers
    
    def calculate_assessment_market_average(self, assessment: VehicleAssessment) -> Dict:
        """
        Calculate overall market average for entire assessment.
        
        Args:
            assessment: VehicleAssessment instance to calculate totals for
            
        Returns:
            Dictionary containing assessment-level market statistics
        """
        damaged_parts_queryset = assessment.damaged_parts
        
        if not damaged_parts_queryset.exists():
            return {
                'total_parts': 0,
                'parts_with_averages': 0,
                'market_average_total': None,
                'confidence_level': 0,
                'price_range': None,
                'variance_percentage': None
            }
        
        # Calculate market averages for each part if not already done
        parts_with_averages = []
        total_market_cost = Decimal('0.00')
        total_min_cost = Decimal('0.00')
        total_max_cost = Decimal('0.00')
        confidence_scores = []
        variance_percentages = []
        
        damaged_parts = damaged_parts_queryset.all()
        for part in damaged_parts:
            try:
                # Get or calculate market average
                if hasattr(part, 'market_average'):
                    market_avg = part.market_average
                else:
                    market_avg = self.calculate_market_average(part)
                
                parts_with_averages.append(part)
                total_market_cost += market_avg.average_total_cost
                total_min_cost += market_avg.min_total_cost
                total_max_cost += market_avg.max_total_cost
                confidence_scores.append(market_avg.confidence_level)
                variance_percentages.append(float(market_avg.variance_percentage))
                
            except InsufficientDataError:
                # Skip parts without sufficient quote data
                continue
        
        # Calculate overall statistics
        parts_count = len(parts_with_averages)
        if parts_count == 0:
            return {
                'total_parts': damaged_parts.count(),
                'parts_with_averages': 0,
                'market_average_total': None,
                'confidence_level': 0,
                'price_range': None,
                'variance_percentage': None
            }
        
        # Overall confidence is weighted average
        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Overall variance is average of part variances
        overall_variance = sum(variance_percentages) / len(variance_percentages)
        
        return {
            'total_parts': damaged_parts_queryset.count(),
            'parts_with_averages': parts_count,
            'market_average_total': total_market_cost,
            'min_total_cost': total_min_cost,
            'max_total_cost': total_max_cost,
            'confidence_level': int(overall_confidence),
            'price_range': {
                'min': total_min_cost,
                'max': total_max_cost,
                'spread': total_max_cost - total_min_cost
            },
            'variance_percentage': round(overall_variance, 2)
        }
    
    def update_market_averages(
        self, 
        assessment_ids: Optional[List[int]] = None,
        force_recalculate: bool = False
    ) -> Dict:
        """
        Batch process market averages for multiple assessments.
        
        Args:
            assessment_ids: List of assessment IDs to process. If None, processes all.
            force_recalculate: If True, recalculates even if averages exist
            
        Returns:
            Dictionary with processing statistics
        """
        # Get assessments to process
        if assessment_ids:
            assessments = VehicleAssessment.objects.filter(id__in=assessment_ids)
        else:
            # Process assessments with parts but no market averages
            assessments = VehicleAssessment.objects.filter(
                damaged_parts__isnull=False
            ).distinct()
        
        stats = {
            'assessments_processed': 0,
            'parts_processed': 0,
            'averages_calculated': 0,
            'averages_updated': 0,
            'errors': []
        }
        
        for assessment in assessments:
            try:
                with transaction.atomic():
                    assessment_stats = self._process_assessment_market_averages(
                        assessment, force_recalculate
                    )
                    
                    stats['assessments_processed'] += 1
                    stats['parts_processed'] += assessment_stats['parts_processed']
                    stats['averages_calculated'] += assessment_stats['averages_calculated']
                    stats['averages_updated'] += assessment_stats['averages_updated']
                    
                    # Update assessment quote summary
                    self._update_assessment_quote_summary(assessment)
                    
            except Exception as e:
                error_msg = f"Error processing assessment {assessment.id}: {str(e)}"
                stats['errors'].append(error_msg)
        
        return stats
    
    def _get_valid_quotes(self, damaged_part: DamagedPart) -> List[PartQuote]:
        """Get valid quotes for market analysis"""
        return list(PartQuote.objects.filter(
            damaged_part=damaged_part,
            status='validated',
            valid_until__gt=timezone.now()
        ).select_related('quote_request'))
    
    def _process_assessment_market_averages(
        self, 
        assessment: VehicleAssessment, 
        force_recalculate: bool
    ) -> Dict:
        """Process market averages for a single assessment"""
        stats = {
            'parts_processed': 0,
            'averages_calculated': 0,
            'averages_updated': 0
        }
        
        for part in assessment.damaged_parts.all():
            stats['parts_processed'] += 1
            
            # Check if market average already exists
            has_existing = hasattr(part, 'market_average')
            
            if force_recalculate or not has_existing:
                try:
                    market_avg = self.calculate_market_average(part)
                    
                    if has_existing:
                        stats['averages_updated'] += 1
                    else:
                        stats['averages_calculated'] += 1
                        
                except InsufficientDataError:
                    # Skip parts without sufficient quotes
                    continue
        
        return stats
    
    def _update_assessment_quote_summary(self, assessment: VehicleAssessment):
        """Update assessment quote summary with market average data"""
        try:
            quote_summary = assessment.quote_summary
        except AssessmentQuoteSummary.DoesNotExist:
            # Create quote summary if it doesn't exist
            quote_summary = AssessmentQuoteSummary.objects.create(
                assessment=assessment
            )
        
        # Calculate assessment market average
        market_data = self.calculate_assessment_market_average(assessment)
        
        # Update quote summary with market data
        quote_summary.market_average_total = market_data.get('market_average_total')
        quote_summary.save()
        
        # Update other summary metrics
        quote_summary.update_summary_metrics()


class MarketAnalysisReporter:
    """
    Utility class for generating market analysis reports and insights.
    """
    
    def __init__(self, calculator: MarketAverageCalculator = None):
        self.calculator = calculator or MarketAverageCalculator()
    
    def generate_part_analysis_report(self, damaged_part: DamagedPart) -> Dict:
        """Generate comprehensive analysis report for a single part"""
        try:
            market_avg = damaged_part.market_average
        except PartMarketAverage.DoesNotExist:
            try:
                market_avg = self.calculator.calculate_market_average(damaged_part)
            except InsufficientDataError as e:
                return {
                    'error': str(e),
                    'part_name': damaged_part.part_name,
                    'quotes_available': damaged_part.quotes.filter(status='validated').count()
                }
        
        quotes = self.calculator._get_valid_quotes(damaged_part)
        outliers = self.calculator.identify_outliers(quotes)
        
        return {
            'part_name': damaged_part.part_name,
            'part_category': damaged_part.get_part_category_display(),
            'damage_severity': damaged_part.get_damage_severity_display(),
            'market_statistics': {
                'average_cost': float(market_avg.average_total_cost),
                'price_range': {
                    'min': float(market_avg.min_total_cost),
                    'max': float(market_avg.max_total_cost)
                },
                'standard_deviation': float(market_avg.standard_deviation),
                'variance_percentage': float(market_avg.variance_percentage)
            },
            'data_quality': {
                'quote_count': market_avg.quote_count,
                'confidence_level': market_avg.confidence_level,
                'outlier_count': len(outliers),
                'is_high_confidence': market_avg.is_high_confidence()
            },
            'outliers': [
                {
                    'provider': quote.provider_name,
                    'cost': float(quote.total_cost),
                    'deviation': float(quote.total_cost) - float(market_avg.average_total_cost)
                }
                for quote in outliers
            ]
        }
    
    def generate_assessment_analysis_report(self, assessment: VehicleAssessment) -> Dict:
        """Generate comprehensive analysis report for entire assessment"""
        market_data = self.calculator.calculate_assessment_market_average(assessment)
        
        # Get part-level analysis
        part_analyses = []
        for part in assessment.damaged_parts.all():
            part_analysis = self.generate_part_analysis_report(part)
            if 'error' not in part_analysis:
                part_analyses.append(part_analysis)
        
        return {
            'assessment_id': assessment.assessment_id,
            'vehicle_info': {
                'make': assessment.vehicle.make if assessment.vehicle else 'Unknown',
                'model': assessment.vehicle.model if assessment.vehicle else 'Unknown',
                'year': assessment.vehicle.manufacture_year if assessment.vehicle else 'Unknown'
            },
            'overall_statistics': market_data,
            'part_analyses': part_analyses,
            'summary': {
                'total_parts': market_data['total_parts'],
                'analyzable_parts': market_data['parts_with_averages'],
                'coverage_percentage': (
                    (market_data['parts_with_averages'] / market_data['total_parts']) * 100
                    if market_data['total_parts'] > 0 else 0
                ),
                'overall_confidence': market_data['confidence_level']
            }
        }