# quote_collection.py
"""
Quote Collection and Validation System

This module handles the collection, validation, and processing of quotes from various providers
for the parts-based quote system. It includes comprehensive data validation, quote storage,
completion tracking, and expiry management.
"""

from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional, Tuple, Any

from .models import (
    PartQuoteRequest, 
    PartQuote, 
    DamagedPart, 
    VehicleAssessment
)

logger = logging.getLogger(__name__)


class QuoteValidationError(Exception):
    """Custom exception for quote validation errors"""
    pass


class QuoteCollectionEngine:
    """
    Engine for collecting, validating, and managing quotes from providers.
    
    This class handles the complete quote collection workflow including:
    - Processing provider responses
    - Validating quote data completeness and accuracy
    - Creating or updating quote records
    - Tracking quote completion status
    - Managing quote expiry and cleanup
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def process_provider_response(self, request_id: str, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a provider response and create/update quote records.
        
        Args:
            request_id: Unique identifier for the quote request
            provider_data: Dictionary containing provider quote data
            
        Returns:
            Dictionary with processing results and any errors
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            # Get the quote request
            quote_request = PartQuoteRequest.objects.get(request_id=request_id)
            
            # Validate the quote request is still active
            if quote_request.is_expired():
                raise QuoteValidationError(f"Quote request {request_id} has expired")
            
            if quote_request.status == 'cancelled':
                raise QuoteValidationError(f"Quote request {request_id} has been cancelled")
            
            # Validate provider data
            validation_result = self.validate_quote_data(provider_data, quote_request)
            if not validation_result['is_valid']:
                self.logger.warning(
                    f"Invalid quote data for request {request_id}: {validation_result['errors']}"
                )
                return {
                    'success': False,
                    'errors': validation_result['errors'],
                    'quote_id': None
                }
            
            # Create or update the quote
            with transaction.atomic():
                quote = self.create_or_update_quote(quote_request, provider_data)
                
                # Update request status
                quote_request.status = 'received'
                quote_request.save()
                
                # Check if all expected quotes are received
                completion_status = self.quote_completion_checker(quote_request.assessment)
                
                self.logger.info(
                    f"Successfully processed quote for request {request_id}, "
                    f"quote ID: {quote.id}, completion: {completion_status['completion_percentage']:.1f}%"
                )
                
                return {
                    'success': True,
                    'quote_id': quote.id,
                    'completion_status': completion_status,
                    'errors': []
                }
                
        except PartQuoteRequest.DoesNotExist:
            error_msg = f"Quote request {request_id} not found"
            self.logger.error(error_msg)
            return {
                'success': False,
                'errors': [error_msg],
                'quote_id': None
            }
            
        except QuoteValidationError as e:
            self.logger.error(f"Validation error for request {request_id}: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)],
                'quote_id': None
            }
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing quote for request {request_id}: {str(e)}")
            return {
                'success': False,
                'errors': [f"Internal error: {str(e)}"],
                'quote_id': None
            }
    
    def validate_quote_data(self, provider_data: Dict[str, Any], quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """
        Validate quote data for completeness and accuracy.
        
        Args:
            provider_data: Dictionary containing provider quote data
            quote_request: The associated quote request
            
        Returns:
            Dictionary with validation results
            
        Requirements: 3.2, 3.3
        """
        errors = []
        warnings = []
        
        # Required fields validation
        required_fields = [
            'provider_type', 'provider_name', 'part_cost', 'labor_cost',
            'total_cost', 'estimated_delivery_days', 'estimated_completion_days',
            'valid_until'
        ]
        
        for field in required_fields:
            if field not in provider_data or provider_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        # Provider type validation
        valid_provider_types = ['assessor', 'dealer', 'independent', 'network']
        if provider_data['provider_type'] not in valid_provider_types:
            errors.append(f"Invalid provider type: {provider_data['provider_type']}")
        
        # Cost validation
        try:
            part_cost = Decimal(str(provider_data['part_cost']))
            labor_cost = Decimal(str(provider_data['labor_cost']))
            total_cost = Decimal(str(provider_data['total_cost']))
            
            if part_cost < 0:
                errors.append("Part cost cannot be negative")
            if labor_cost < 0:
                errors.append("Labor cost cannot be negative")
            if total_cost < 0:
                errors.append("Total cost cannot be negative")
            
            # Calculate expected total
            paint_cost = Decimal(str(provider_data.get('paint_cost', 0)))
            additional_costs = Decimal(str(provider_data.get('additional_costs', 0)))
            expected_total = part_cost + labor_cost + paint_cost + additional_costs
            
            # Allow 1% tolerance for rounding differences
            tolerance = expected_total * Decimal('0.01')
            if abs(total_cost - expected_total) > tolerance:
                warnings.append(
                    f"Total cost ({total_cost}) doesn't match sum of components ({expected_total})"
                )
            
        except (InvalidOperation, ValueError, TypeError) as e:
            errors.append(f"Invalid cost format: {str(e)}")
        
        # Timeline validation
        try:
            delivery_days = int(provider_data['estimated_delivery_days'])
            completion_days = int(provider_data['estimated_completion_days'])
            
            if delivery_days < 0:
                errors.append("Delivery days cannot be negative")
            if completion_days < 0:
                errors.append("Completion days cannot be negative")
            if completion_days < delivery_days:
                warnings.append("Completion days is less than delivery days")
            
            # Reasonable timeline validation
            if delivery_days > 365:
                warnings.append("Delivery timeline exceeds 1 year")
            if completion_days > 365:
                warnings.append("Completion timeline exceeds 1 year")
                
        except (ValueError, TypeError):
            errors.append("Invalid timeline format")
        
        # Valid until date validation
        try:
            if isinstance(provider_data['valid_until'], str):
                valid_until = datetime.fromisoformat(provider_data['valid_until'].replace('Z', '+00:00'))
            else:
                valid_until = provider_data['valid_until']
            
            if valid_until <= timezone.now():
                errors.append("Quote validity date must be in the future")
                
        except (ValueError, TypeError):
            errors.append("Invalid valid_until date format")
        
        # Part type validation
        if 'part_type' in provider_data:
            valid_part_types = ['oem', 'oem_equivalent', 'aftermarket', 'used']
            if provider_data['part_type'] not in valid_part_types:
                errors.append(f"Invalid part type: {provider_data['part_type']}")
        
        # Warranty validation
        if 'part_warranty_months' in provider_data:
            try:
                warranty_months = int(provider_data['part_warranty_months'])
                if warranty_months < 0 or warranty_months > 120:  # 10 years max
                    warnings.append("Part warranty period seems unusual")
            except (ValueError, TypeError):
                errors.append("Invalid part warranty format")
        
        if 'labor_warranty_months' in provider_data:
            try:
                labor_warranty = int(provider_data['labor_warranty_months'])
                if labor_warranty < 0 or labor_warranty > 60:  # 5 years max
                    warnings.append("Labor warranty period seems unusual")
            except (ValueError, TypeError):
                errors.append("Invalid labor warranty format")
        
        # Confidence score validation
        if 'confidence_score' in provider_data:
            try:
                confidence = int(provider_data['confidence_score'])
                if confidence < 0 or confidence > 100:
                    errors.append("Confidence score must be between 0 and 100")
            except (ValueError, TypeError):
                errors.append("Invalid confidence score format")
        
        # Cross-validation with damaged part
        damaged_part = quote_request.damaged_part
        
        # Check if quote is reasonable for part category
        estimated_range = damaged_part.get_estimated_cost_range()
        quote_total = Decimal(str(provider_data['total_cost']))
        
        # Allow quotes up to 3x the estimated max (for premium providers)
        if quote_total > estimated_range['max_cost'] * 3:
            warnings.append(
                f"Quote significantly higher than estimated range "
                f"(£{quote_total} vs £{estimated_range['max_cost']:.2f} max)"
            )
        
        # Very low quotes might indicate missing components
        if quote_total < estimated_range['min_cost'] * 0.3:
            warnings.append(
                f"Quote significantly lower than estimated range "
                f"(£{quote_total} vs £{estimated_range['min_cost']:.2f} min)"
            )
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def create_or_update_quote(self, quote_request: PartQuoteRequest, provider_data: Dict[str, Any]) -> PartQuote:
        """
        Create a new quote or update an existing one.
        
        Args:
            quote_request: The quote request object
            provider_data: Validated provider data
            
        Returns:
            Created or updated PartQuote instance
            
        Requirements: 3.1, 3.4
        """
        # Check if quote already exists for this provider
        existing_quote = PartQuote.objects.filter(
            quote_request=quote_request,
            provider_type=provider_data['provider_type'],
            provider_name=provider_data['provider_name']
        ).first()
        
        # Prepare quote data
        quote_data = {
            'quote_request': quote_request,
            'damaged_part': quote_request.damaged_part,
            'provider_type': provider_data['provider_type'],
            'provider_name': provider_data['provider_name'],
            'provider_contact': provider_data.get('provider_contact', ''),
            'part_cost': Decimal(str(provider_data['part_cost'])),
            'labor_cost': Decimal(str(provider_data['labor_cost'])),
            'paint_cost': Decimal(str(provider_data.get('paint_cost', 0))),
            'additional_costs': Decimal(str(provider_data.get('additional_costs', 0))),
            'total_cost': Decimal(str(provider_data['total_cost'])),
            'part_type': provider_data.get('part_type', 'oem'),
            'estimated_delivery_days': int(provider_data['estimated_delivery_days']),
            'estimated_completion_days': int(provider_data['estimated_completion_days']),
            'part_warranty_months': int(provider_data.get('part_warranty_months', 12)),
            'labor_warranty_months': int(provider_data.get('labor_warranty_months', 12)),
            'confidence_score': int(provider_data.get('confidence_score', 50)),
            'notes': provider_data.get('notes', ''),
        }
        
        # Handle valid_until date
        if isinstance(provider_data['valid_until'], str):
            quote_data['valid_until'] = datetime.fromisoformat(
                provider_data['valid_until'].replace('Z', '+00:00')
            )
        else:
            quote_data['valid_until'] = provider_data['valid_until']
        
        if existing_quote:
            # Update existing quote
            for field, value in quote_data.items():
                if field not in ['quote_request', 'damaged_part']:  # Don't update FK fields
                    setattr(existing_quote, field, value)
            
            existing_quote.save()
            
            self.logger.info(
                f"Updated existing quote {existing_quote.id} for request {quote_request.request_id}"
            )
            return existing_quote
        else:
            # Create new quote
            quote = PartQuote.objects.create(**quote_data)
            
            self.logger.info(
                f"Created new quote {quote.id} for request {quote_request.request_id}"
            )
            return quote
    
    def quote_completion_checker(self, assessment: VehicleAssessment) -> Dict[str, Any]:
        """
        Check completion status of quote collection for an assessment.
        
        Args:
            assessment: VehicleAssessment instance
            
        Returns:
            Dictionary with completion status and statistics
            
        Requirements: 3.4, 3.5
        """
        # Get all quote requests for this assessment
        quote_requests = PartQuoteRequest.objects.filter(
            assessment=assessment,
            status__in=['sent', 'received']  # Exclude draft, expired, cancelled
        )
        
        total_requests = quote_requests.count()
        if total_requests == 0:
            return {
                'is_complete': False,
                'completion_percentage': 0.0,
                'total_requests': 0,
                'received_quotes': 0,
                'pending_requests': 0,
                'expired_requests': 0,
                'expected_quotes': 0,
                'received_quote_count': 0
            }
        
        # Count expected quotes based on provider selections
        expected_quotes = 0
        for request in quote_requests:
            if request.include_assessor:
                expected_quotes += 1
            if request.include_dealer:
                expected_quotes += 1
            if request.include_independent:
                expected_quotes += 1
            if request.include_network:
                expected_quotes += 1
        
        # Count received quotes
        received_quotes = PartQuote.objects.filter(
            quote_request__in=quote_requests
        ).count()
        
        # Count pending and expired requests
        pending_requests = quote_requests.filter(status='sent').count()
        expired_requests = quote_requests.filter(
            status='sent',
            expiry_date__lt=timezone.now()
        ).count()
        
        # Calculate completion percentage
        completion_percentage = (received_quotes / expected_quotes * 100) if expected_quotes > 0 else 0
        
        # Determine if collection is complete
        # Complete if we have at least one quote per part and no pending non-expired requests
        parts_with_quotes = PartQuote.objects.filter(
            quote_request__in=quote_requests
        ).values('damaged_part').distinct().count()
        
        total_parts = quote_requests.values('damaged_part').distinct().count()
        active_pending = pending_requests - expired_requests
        
        is_complete = (parts_with_quotes == total_parts and active_pending == 0) or completion_percentage >= 80
        
        # Update assessment quote collection status
        try:
            quote_extension = assessment.quote_extension
            if is_complete:
                quote_extension.quote_collection_status = 'completed'
            elif received_quotes > 0:
                quote_extension.quote_collection_status = 'in_progress'
            else:
                quote_extension.quote_collection_status = 'not_started'
            
            quote_extension.save()
        except AttributeError:
            # Fallback for assessments without quote extension
            # This handles backward compatibility
            pass
        
        return {
            'is_complete': is_complete,
            'completion_percentage': completion_percentage,
            'total_requests': total_requests,
            'received_quotes': received_quotes,
            'pending_requests': pending_requests,
            'expired_requests': expired_requests,
            'expected_quotes': expected_quotes,
            'received_quote_count': received_quotes,
            'parts_with_quotes': parts_with_quotes,
            'total_parts': total_parts
        }
    
    def cleanup_expired_quotes(self, days_old: int = 30) -> Dict[str, int]:
        """
        Clean up expired quote requests and associated data.
        
        Args:
            days_old: Number of days after expiry to clean up (default: 30)
            
        Returns:
            Dictionary with cleanup statistics
            
        Requirements: 3.5
        """
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Find expired requests to clean up
        expired_requests = PartQuoteRequest.objects.filter(
            expiry_date__lt=cutoff_date,
            status__in=['sent', 'expired']
        )
        
        expired_count = expired_requests.count()
        
        # Find quotes associated with expired requests
        expired_quotes = PartQuote.objects.filter(
            quote_request__in=expired_requests
        )
        
        quotes_count = expired_quotes.count()
        
        # Perform cleanup in transaction
        with transaction.atomic():
            # Update request status to expired
            updated_requests = expired_requests.update(status='expired')
            
            # Optionally delete very old quotes (configurable)
            very_old_cutoff = timezone.now() - timedelta(days=days_old * 2)
            very_old_quotes = PartQuote.objects.filter(
                quote_request__expiry_date__lt=very_old_cutoff,
                quote_request__status='expired'
            )
            
            deleted_quotes = very_old_quotes.count()
            very_old_quotes.delete()
        
        self.logger.info(
            f"Cleanup completed: {updated_requests} requests marked expired, "
            f"{deleted_quotes} old quotes deleted"
        )
        
        return {
            'expired_requests_updated': updated_requests,
            'total_expired_quotes': quotes_count,
            'deleted_old_quotes': deleted_quotes
        }
    
    def get_quote_statistics(self, assessment: VehicleAssessment) -> Dict[str, Any]:
        """
        Get comprehensive statistics for quote collection on an assessment.
        
        Args:
            assessment: VehicleAssessment instance
            
        Returns:
            Dictionary with detailed statistics
        """
        quote_requests = PartQuoteRequest.objects.filter(assessment=assessment)
        quotes = PartQuote.objects.filter(quote_request__in=quote_requests)
        
        # Provider statistics
        provider_stats = {}
        for provider_type in ['assessor', 'dealer', 'independent', 'network']:
            provider_quotes = quotes.filter(provider_type=provider_type)
            if provider_quotes.exists():
                costs = [float(q.total_cost) for q in provider_quotes]
                provider_stats[provider_type] = {
                    'count': len(costs),
                    'avg_cost': sum(costs) / len(costs),
                    'min_cost': min(costs),
                    'max_cost': max(costs),
                    'avg_delivery_days': provider_quotes.aggregate(
                        models.Avg('estimated_delivery_days')
                    )['estimated_delivery_days__avg'] or 0
                }
        
        # Overall statistics
        if quotes.exists():
            all_costs = [float(q.total_cost) for q in quotes]
            total_stats = {
                'total_quotes': quotes.count(),
                'avg_total_cost': sum(all_costs) / len(all_costs),
                'min_total_cost': min(all_costs),
                'max_total_cost': max(all_costs),
                'cost_variance': max(all_costs) - min(all_costs) if len(all_costs) > 1 else 0
            }
        else:
            total_stats = {
                'total_quotes': 0,
                'avg_total_cost': 0,
                'min_total_cost': 0,
                'max_total_cost': 0,
                'cost_variance': 0
            }
        
        return {
            'provider_statistics': provider_stats,
            'overall_statistics': total_stats,
            'completion_status': self.quote_completion_checker(assessment)
        }