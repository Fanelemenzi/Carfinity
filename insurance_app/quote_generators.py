# quote_generators.py
"""
Quote generation system for creating assessor estimates and managing quote workflows.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import DamagedPart, PartQuote, PartQuoteRequest
import logging

logger = logging.getLogger(__name__)


class AssessorEstimateGenerator:
    """
    Generator class for creating internal assessor estimates using pricing database
    and industry standard rates.
    """
    
    # Standard labor rate per hour
    STANDARD_LABOR_RATE = Decimal('45.00')  # £45/hour
    
    # Paint cost percentage for body panels
    PAINT_COST_PERCENTAGE = Decimal('0.15')  # 15% of part cost
    
    # Base part costs by category (in GBP)
    BASE_PART_COSTS = {
        'body': Decimal('500.00'),
        'mechanical': Decimal('800.00'),
        'electrical': Decimal('300.00'),
        'glass': Decimal('200.00'),
        'interior': Decimal('150.00'),
        'trim': Decimal('100.00'),
        'wheels': Decimal('400.00'),
        'safety': Decimal('600.00'),
        'structural': Decimal('1200.00'),
        'fluid': Decimal('250.00'),
    }
    
    # Damage severity multipliers
    SEVERITY_MULTIPLIERS = {
        'minor': Decimal('0.3'),
        'moderate': Decimal('0.6'),
        'severe': Decimal('1.0'),
        'replace': Decimal('1.5'),
    }
    
    # Confidence scores by calculation method
    CONFIDENCE_SCORES = {
        'standard': 85,  # Standard calculation
        'estimated': 70,  # When using fallback estimates
        'minimum': 60,   # Minimum confidence for any estimate
    }
    
    def __init__(self):
        """Initialize the assessor estimate generator."""
        self.provider_name = "Internal Assessor Estimate"
        self.provider_type = "assessor"
    
    def generate_assessor_estimate(self, damaged_part, quote_request=None):
        """
        Generate an assessor estimate for a damaged part.
        
        Args:
            damaged_part (DamagedPart): The damaged part to estimate
            quote_request (PartQuoteRequest, optional): Associated quote request
            
        Returns:
            PartQuote: Created assessor estimate quote
            
        Raises:
            ValidationError: If damaged part data is invalid
        """
        try:
            # Validate input
            self._validate_damaged_part(damaged_part)
            
            # Calculate cost components
            part_cost = self.get_base_part_cost(damaged_part)
            labor_cost = self.calculate_labor_cost(damaged_part)
            paint_cost = self.calculate_paint_cost(damaged_part, part_cost)
            additional_costs = self._calculate_additional_costs(damaged_part)
            
            # Calculate total cost
            total_cost = part_cost + labor_cost + paint_cost + additional_costs
            
            # Determine confidence score
            confidence_score = self._calculate_confidence_score(damaged_part)
            
            # Set validity period (30 days for assessor estimates)
            valid_until = timezone.now() + timedelta(days=30)
            
            # Create the quote
            quote = PartQuote.objects.create(
                quote_request=quote_request,
                damaged_part=damaged_part,
                provider_type=self.provider_type,
                provider_name=self.provider_name,
                provider_contact="Internal Assessment Team",
                
                # Cost breakdown
                part_cost=part_cost,
                labor_cost=labor_cost,
                paint_cost=paint_cost,
                additional_costs=additional_costs,
                total_cost=total_cost,
                
                # Part specifications
                part_type='oem_equivalent',  # Conservative estimate using OEM equivalent
                part_manufacturer='Various',
                part_number_quoted='',
                
                # Timeline estimates
                estimated_delivery_days=self._get_estimated_delivery_days(damaged_part),
                estimated_completion_days=self._get_estimated_completion_days(damaged_part),
                part_warranty_months=12,
                labor_warranty_months=12,
                
                # Quality metrics
                confidence_score=confidence_score,
                
                # Validity
                valid_until=valid_until,
                notes=self._generate_estimate_notes(damaged_part),
                status='validated'
            )
            
            logger.info(f"Generated assessor estimate for part {damaged_part.id}: £{total_cost}")
            return quote
            
        except Exception as e:
            logger.error(f"Error generating assessor estimate for part {damaged_part.id}: {str(e)}")
            raise ValidationError(f"Failed to generate assessor estimate: {str(e)}")
    
    def get_base_part_cost(self, damaged_part):
        """
        Calculate base part cost using part category and damage severity.
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            Decimal: Base part cost
        """
        # Get base cost for part category
        base_cost = self.BASE_PART_COSTS.get(
            damaged_part.part_category, 
            self.BASE_PART_COSTS['mechanical']  # Default fallback
        )
        
        # Apply severity multiplier
        severity_multiplier = self.SEVERITY_MULTIPLIERS.get(
            damaged_part.damage_severity,
            self.SEVERITY_MULTIPLIERS['moderate']  # Default fallback
        )
        
        # Calculate final part cost
        part_cost = base_cost * severity_multiplier
        
        # Round to 2 decimal places
        return part_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_labor_cost(self, damaged_part):
        """
        Calculate labor cost using standard £45/hour rate.
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            Decimal: Labor cost
        """
        # Use estimated labor hours from the damaged part
        labor_hours = damaged_part.estimated_labor_hours
        
        # If no labor hours estimated, use default based on severity
        if labor_hours <= 0:
            labor_hours = self._get_default_labor_hours(damaged_part)
        
        # Calculate labor cost
        labor_cost = labor_hours * self.STANDARD_LABOR_RATE
        
        # Round to 2 decimal places
        return labor_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_paint_cost(self, damaged_part, part_cost):
        """
        Calculate paint cost for body panel parts (15% of part cost).
        
        Args:
            damaged_part (DamagedPart): The damaged part
            part_cost (Decimal): The calculated part cost
            
        Returns:
            Decimal: Paint cost
        """
        # Paint cost only applies to body panels and some trim pieces
        paint_categories = ['body', 'trim']
        
        if damaged_part.part_category not in paint_categories:
            return Decimal('0.00')
        
        # Calculate paint cost as percentage of part cost
        paint_cost = part_cost * self.PAINT_COST_PERCENTAGE
        
        # Minimum paint cost for body panels
        min_paint_cost = Decimal('50.00')
        if damaged_part.part_category == 'body' and paint_cost < min_paint_cost:
            paint_cost = min_paint_cost
        
        # Round to 2 decimal places
        return paint_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _validate_damaged_part(self, damaged_part):
        """
        Validate damaged part data for estimate generation.
        
        Args:
            damaged_part (DamagedPart): The damaged part to validate
            
        Raises:
            ValidationError: If validation fails
        """
        if not damaged_part:
            raise ValidationError("Damaged part is required")
        
        if not damaged_part.part_category:
            raise ValidationError("Part category is required")
        
        if not damaged_part.damage_severity:
            raise ValidationError("Damage severity is required")
        
        if damaged_part.part_category not in self.BASE_PART_COSTS:
            raise ValidationError(f"Unknown part category: {damaged_part.part_category}")
        
        if damaged_part.damage_severity not in self.SEVERITY_MULTIPLIERS:
            raise ValidationError(f"Unknown damage severity: {damaged_part.damage_severity}")
    
    def _calculate_additional_costs(self, damaged_part):
        """
        Calculate additional costs (disposal, consumables, etc.).
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            Decimal: Additional costs
        """
        additional_costs = Decimal('0.00')
        
        # Add disposal cost for replaced parts
        if damaged_part.requires_replacement:
            additional_costs += Decimal('25.00')  # Standard disposal fee
        
        # Add consumables cost based on part category
        consumables_costs = {
            'body': Decimal('30.00'),      # Primer, sealants, etc.
            'mechanical': Decimal('20.00'), # Fluids, gaskets, etc.
            'electrical': Decimal('15.00'), # Connectors, tape, etc.
            'glass': Decimal('10.00'),     # Sealants, clips, etc.
            'interior': Decimal('10.00'),  # Clips, adhesives, etc.
            'trim': Decimal('5.00'),       # Clips, adhesives, etc.
            'wheels': Decimal('15.00'),    # Balancing weights, etc.
            'safety': Decimal('25.00'),    # Calibration, testing, etc.
            'structural': Decimal('40.00'), # Welding materials, etc.
            'fluid': Decimal('20.00'),     # Seals, filters, etc.
        }
        
        consumables = consumables_costs.get(damaged_part.part_category, Decimal('15.00'))
        additional_costs += consumables
        
        return additional_costs.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_confidence_score(self, damaged_part):
        """
        Calculate confidence score for the estimate.
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            int: Confidence score (0-100)
        """
        base_confidence = self.CONFIDENCE_SCORES['standard']
        
        # Reduce confidence for unknown part categories
        if damaged_part.part_category not in self.BASE_PART_COSTS:
            base_confidence = self.CONFIDENCE_SCORES['estimated']
        
        # Reduce confidence for severe damage (more variables)
        if damaged_part.damage_severity == 'severe':
            base_confidence -= 10
        elif damaged_part.damage_severity == 'replace':
            base_confidence -= 5
        
        # Increase confidence if labor hours are specified
        if damaged_part.estimated_labor_hours > 0:
            base_confidence += 5
        
        # Increase confidence if part number is available
        if damaged_part.part_number:
            base_confidence += 5
        
        # Ensure confidence is within valid range
        return max(self.CONFIDENCE_SCORES['minimum'], min(100, base_confidence))
    
    def _get_default_labor_hours(self, damaged_part):
        """
        Get default labor hours based on part category and damage severity.
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            Decimal: Default labor hours
        """
        # Base labor hours by category
        base_hours = {
            'body': Decimal('3.0'),
            'mechanical': Decimal('2.5'),
            'electrical': Decimal('1.5'),
            'glass': Decimal('1.0'),
            'interior': Decimal('1.0'),
            'trim': Decimal('0.5'),
            'wheels': Decimal('1.0'),
            'safety': Decimal('2.0'),
            'structural': Decimal('5.0'),
            'fluid': Decimal('1.5'),
        }
        
        # Severity multipliers for labor
        labor_multipliers = {
            'minor': Decimal('0.5'),
            'moderate': Decimal('1.0'),
            'severe': Decimal('1.5'),
            'replace': Decimal('2.0'),
        }
        
        base = base_hours.get(damaged_part.part_category, Decimal('2.0'))
        multiplier = labor_multipliers.get(damaged_part.damage_severity, Decimal('1.0'))
        
        return base * multiplier
    
    def _get_estimated_delivery_days(self, damaged_part):
        """
        Get estimated delivery days for the part.
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            int: Estimated delivery days
        """
        # Delivery times by part category (conservative estimates)
        delivery_days = {
            'body': 5,        # Body panels usually in stock
            'mechanical': 3,   # Common mechanical parts
            'electrical': 7,   # May need ordering
            'glass': 2,       # Usually available quickly
            'interior': 5,    # Moderate availability
            'trim': 7,        # Often need ordering
            'wheels': 1,      # Usually in stock
            'safety': 10,     # May need calibration parts
            'structural': 14, # Often custom or special order
            'fluid': 1,       # Usually in stock
        }
        
        return delivery_days.get(damaged_part.part_category, 7)
    
    def _get_estimated_completion_days(self, damaged_part):
        """
        Get estimated completion days including delivery and work time.
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            int: Estimated completion days
        """
        delivery_days = self._get_estimated_delivery_days(damaged_part)
        
        # Work days by complexity
        work_days = {
            'body': 2,        # Paint and fit
            'mechanical': 1,   # Replace and test
            'electrical': 1,   # Install and test
            'glass': 1,       # Install and seal
            'interior': 1,    # Remove and replace
            'trim': 1,        # Fit and align
            'wheels': 1,      # Mount and balance
            'safety': 3,      # Install and calibrate
            'structural': 5,  # Weld and align
            'fluid': 1,       # Replace and test
        }
        
        work_time = work_days.get(damaged_part.part_category, 2)
        
        # Add buffer for severe damage
        if damaged_part.damage_severity in ['severe', 'replace']:
            work_time += 1
        
        return delivery_days + work_time
    
    def _generate_estimate_notes(self, damaged_part):
        """
        Generate notes for the estimate.
        
        Args:
            damaged_part (DamagedPart): The damaged part
            
        Returns:
            str: Estimate notes
        """
        notes = [
            f"Internal assessor estimate for {damaged_part.part_name}",
            f"Damage severity: {damaged_part.get_damage_severity_display()}",
            f"Part category: {damaged_part.get_part_category_display()}",
        ]
        
        if damaged_part.estimated_labor_hours > 0:
            notes.append(f"Labor hours: {damaged_part.estimated_labor_hours}")
        
        if damaged_part.requires_replacement:
            notes.append("Part requires complete replacement")
        
        notes.append("Estimate based on industry standard rates and OEM equivalent parts")
        notes.append("Final costs may vary based on actual part availability and labor requirements")
        
        return ". ".join(notes) + "."