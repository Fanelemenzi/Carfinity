# quote_managers.py
"""
Quote Request Management System

This module provides the PartQuoteRequestManager class for managing quote requests
in the parts-based quote system. It handles creation, validation, status updates,
and batch operations for quote requests.
"""

from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from typing import List, Dict, Optional, Tuple
import logging

from .models import DamagedPart, PartQuoteRequest, VehicleAssessment
from assessments.models import VehicleAssessment as AssessmentModel

logger = logging.getLogger(__name__)


class PartQuoteRequestManager:
    """
    Manager class for handling part quote request operations.
    
    This class provides methods for creating, validating, and managing
    quote requests for damaged parts identified in vehicle assessments.
    """
    
    # Default expiry period for quote requests (7 days)
    DEFAULT_EXPIRY_DAYS = 7
    
    # Valid provider combinations
    VALID_PROVIDER_TYPES = ['assessor', 'dealer', 'independent', 'network']
    
    def __init__(self):
        """Initialize the quote request manager."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_quote_requests(
        self, 
        assessment: VehicleAssessment, 
        damaged_parts: Optional[List[DamagedPart]] = None,
        provider_selection: Optional[Dict[str, bool]] = None,
        expiry_days: int = DEFAULT_EXPIRY_DAYS
    ) -> List[PartQuoteRequest]:
        """
        Create quote requests for identified damaged parts.
        
        Args:
            assessment: The vehicle assessment containing damaged parts
            damaged_parts: Optional list of specific parts to create requests for.
                          If None, creates requests for all parts in assessment.
            provider_selection: Dict specifying which providers to include
                               {'assessor': True, 'dealer': False, etc.}
            expiry_days: Number of days until request expires
        
        Returns:
            List of created PartQuoteRequest objects
        
        Raises:
            ValidationError: If validation fails
            ValueError: If invalid parameters provided
        """
        try:
            with transaction.atomic():
                # Get damaged parts if not provided
                if damaged_parts is None:
                    damaged_parts = list(assessment.damaged_parts.all())
                
                if not damaged_parts:
                    raise ValueError("No damaged parts found for assessment")
                
                # Set default provider selection if not provided
                if provider_selection is None:
                    provider_selection = {
                        'assessor': True,
                        'dealer': False,
                        'independent': False,
                        'network': False
                    }
                
                # Validate provider selection
                self.validate_provider_selection(provider_selection)
                
                # Calculate expiry date
                expiry_date = timezone.now() + timedelta(days=expiry_days)
                
                created_requests = []
                
                for part in damaged_parts:
                    # Check if request already exists for this part
                    existing_request = PartQuoteRequest.objects.filter(
                        damaged_part=part,
                        status__in=['draft', 'pending', 'sent']
                    ).first()
                    
                    if existing_request:
                        self.logger.warning(
                            f"Quote request already exists for part {part.id}: {existing_request.request_id}"
                        )
                        continue
                    
                    # Create quote request
                    quote_request = PartQuoteRequest.objects.create(
                        damaged_part=part,
                        assessment=assessment,
                        expiry_date=expiry_date,
                        include_assessor=provider_selection.get('assessor', False),
                        include_dealer=provider_selection.get('dealer', False),
                        include_independent=provider_selection.get('independent', False),
                        include_network=provider_selection.get('network', False),
                        dispatched_by=assessment.assigned_to or assessment.created_by
                    )
                    
                    created_requests.append(quote_request)
                    
                    self.logger.info(
                        f"Created quote request {quote_request.request_id} for part {part.part_name}"
                    )
                
                return created_requests
                
        except Exception as e:
            self.logger.error(f"Error creating quote requests: {str(e)}")
            raise
    
    def validate_provider_selection(self, provider_selection: Dict[str, bool]) -> bool:
        """
        Validate provider selection to ensure valid combinations.
        
        Args:
            provider_selection: Dict with provider types and boolean values
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(provider_selection, dict):
            raise ValidationError("Provider selection must be a dictionary")
        
        # Check for valid provider types
        invalid_providers = set(provider_selection.keys()) - set(self.VALID_PROVIDER_TYPES)
        if invalid_providers:
            raise ValidationError(
                f"Invalid provider types: {invalid_providers}. "
                f"Valid types are: {self.VALID_PROVIDER_TYPES}"
            )
        
        # Check that at least one provider is selected
        selected_providers = [k for k, v in provider_selection.items() if v]
        if not selected_providers:
            raise ValidationError("At least one provider must be selected")
        
        # Validate specific combinations
        if provider_selection.get('assessor') and len(selected_providers) == 1:
            # Assessor-only is valid
            pass
        elif not provider_selection.get('assessor') and len(selected_providers) >= 1:
            # External providers without assessor is valid
            pass
        elif provider_selection.get('assessor') and len(selected_providers) > 1:
            # Assessor with external providers is valid for comparison
            pass
        
        return True
    
    def update_request_status(
        self, 
        request_id: str, 
        new_status: str, 
        notes: Optional[str] = None
    ) -> PartQuoteRequest:
        """
        Update the status of a quote request.
        
        Args:
            request_id: Unique identifier for the quote request
            new_status: New status value
            notes: Optional notes about the status change
        
        Returns:
            Updated PartQuoteRequest object
        
        Raises:
            PartQuoteRequest.DoesNotExist: If request not found
            ValidationError: If invalid status transition
        """
        try:
            quote_request = PartQuoteRequest.objects.get(request_id=request_id)
            
            # Validate status transition
            self._validate_status_transition(quote_request.status, new_status)
            
            old_status = quote_request.status
            quote_request.status = new_status
            
            # Set dispatch timestamp when status changes to 'sent'
            if new_status == 'sent' and not quote_request.dispatched_at:
                quote_request.dispatched_at = timezone.now()
            
            quote_request.save()
            
            self.logger.info(
                f"Updated quote request {request_id} status from {old_status} to {new_status}"
            )
            
            return quote_request
            
        except PartQuoteRequest.DoesNotExist:
            self.logger.error(f"Quote request not found: {request_id}")
            raise
        except Exception as e:
            self.logger.error(f"Error updating request status: {str(e)}")
            raise
    
    def batch_create_requests(
        self, 
        assessments: List[VehicleAssessment],
        provider_selection: Dict[str, bool],
        expiry_days: int = DEFAULT_EXPIRY_DAYS
    ) -> Dict[str, List[PartQuoteRequest]]:
        """
        Create quote requests for multiple assessments in batch.
        
        Args:
            assessments: List of assessments to process
            provider_selection: Provider selection to apply to all requests
            expiry_days: Days until requests expire
        
        Returns:
            Dict mapping assessment IDs to lists of created requests
        
        Raises:
            ValidationError: If validation fails
        """
        results = {}
        errors = {}
        
        # Validate provider selection once
        self.validate_provider_selection(provider_selection)
        
        for assessment in assessments:
            try:
                requests = self.create_quote_requests(
                    assessment=assessment,
                    provider_selection=provider_selection,
                    expiry_days=expiry_days
                )
                results[assessment.assessment_id] = requests
                
                self.logger.info(
                    f"Created {len(requests)} quote requests for assessment {assessment.assessment_id}"
                )
                
            except Exception as e:
                error_msg = f"Failed to create requests for assessment {assessment.assessment_id}: {str(e)}"
                errors[assessment.assessment_id] = error_msg
                self.logger.error(error_msg)
        
        if errors:
            self.logger.warning(f"Batch operation completed with {len(errors)} errors")
        
        return results
    
    def batch_create_requests_for_parts(
        self,
        assessment: VehicleAssessment,
        part_ids: List[int],
        provider_selection: Dict[str, bool],
        user,
        expiry_days: int = DEFAULT_EXPIRY_DAYS
    ) -> List[PartQuoteRequest]:
        """
        Create quote requests for specific parts in an assessment.
        
        Args:
            assessment: The assessment containing the parts
            part_ids: List of damaged part IDs to create requests for
            provider_selection: Provider selection settings
            user: User creating the requests
            expiry_days: Days until requests expire
        
        Returns:
            List of created PartQuoteRequest objects
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate provider selection
        self.validate_provider_selection(provider_selection)
        
        # Get damaged parts
        damaged_parts = DamagedPart.objects.filter(
            id__in=part_ids,
            assessment=assessment
        )
        
        if len(damaged_parts) != len(part_ids):
            raise ValidationError("Some part IDs are invalid or don't belong to this assessment")
        
        # Create requests
        requests = []
        expiry_date = timezone.now() + timedelta(days=expiry_days)
        
        with transaction.atomic():
            for part in damaged_parts:
                request = PartQuoteRequest.objects.create(
                    damaged_part=part,
                    assessment=assessment,
                    expiry_date=expiry_date,
                    include_assessor=provider_selection.get('include_assessor', False),
                    include_dealer=provider_selection.get('include_dealer', False),
                    include_independent=provider_selection.get('include_independent', False),
                    include_network=provider_selection.get('include_network', False),
                    dispatched_by=user
                )
                requests.append(request)
                
                self.logger.info(
                    f"Created quote request {request.request_id} for part {part.part_name} "
                    f"in assessment {assessment.assessment_id}"
                )
        
        return requests
    
    def create_quote_request(
        self,
        damaged_part: DamagedPart,
        dispatched_by: object,
        include_assessor: bool = False,
        include_dealer: bool = False,
        include_independent: bool = False,
        include_network: bool = False,
        expiry_days: int = DEFAULT_EXPIRY_DAYS
    ) -> PartQuoteRequest:
        """
        Create a single quote request for a damaged part.
        
        Args:
            damaged_part: The damaged part to request quotes for
            dispatched_by: User creating the request
            include_assessor: Whether to include assessor estimate
            include_dealer: Whether to include dealer quotes
            include_independent: Whether to include independent garage quotes
            include_network: Whether to include insurance network quotes
            expiry_days: Number of days until request expires
        
        Returns:
            Created PartQuoteRequest object
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate provider selection
        provider_selection = {
            'include_assessor': include_assessor,
            'include_dealer': include_dealer,
            'include_independent': include_independent,
            'include_network': include_network,
        }
        
        if not any(provider_selection.values()):
            raise ValidationError("At least one provider must be selected")
        
        # Check for existing active requests
        existing_request = PartQuoteRequest.objects.filter(
            damaged_part=damaged_part,
            status__in=['draft', 'pending', 'sent']
        ).first()
        
        if existing_request:
            raise ValidationError(
                f"Active quote request already exists for this part: {existing_request.request_id}"
            )
        
        # Calculate expiry date
        expiry_date = timezone.now() + timedelta(days=expiry_days)
        
        # Create the quote request
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=damaged_part,
            assessment=damaged_part.assessment,
            expiry_date=expiry_date,
            include_assessor=include_assessor,
            include_dealer=include_dealer,
            include_independent=include_independent,
            include_network=include_network,
            dispatched_by=dispatched_by
        )
        
        self.logger.info(
            f"Created quote request {quote_request.request_id} for part {damaged_part.part_name} "
            f"in assessment {damaged_part.assessment.assessment_id}"
        )
        
        return quote_request
    
    def dispatch_quote_request(self, quote_request: PartQuoteRequest) -> bool:
        """
        Dispatch a quote request to selected providers.
        
        Args:
            quote_request: The quote request to dispatch
        
        Returns:
            True if dispatch was successful, False otherwise
        """
        try:
            # For now, just mark as dispatched
            # In a real implementation, this would send requests to actual providers
            self.logger.info(
                f"Dispatching quote request {quote_request.request_id} "
                f"to providers: {quote_request.get_selected_providers()}"
            )
            
            # Simulate successful dispatch
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to dispatch quote request {quote_request.request_id}: {str(e)}"
            )
            return False
    
    def get_pending_requests(
        self, 
        assessment: Optional[VehicleAssessment] = None,
        user: Optional[object] = None
    ) -> models.QuerySet:
        """
        Get pending quote requests.
        
        Args:
            assessment: Optional assessment to filter by
            user: Optional user to filter by (dispatched_by)
        
        Returns:
            QuerySet of pending PartQuoteRequest objects
        """
        queryset = PartQuoteRequest.objects.filter(
            status__in=['draft', 'pending', 'sent']
        ).select_related(
            'damaged_part', 'assessment', 'dispatched_by'
        ).order_by('-request_date')
        
        if assessment:
            queryset = queryset.filter(assessment=assessment)
        
        if user:
            queryset = queryset.filter(dispatched_by=user)
        
        return queryset
    
    def get_expired_requests(
        self, 
        assessment: Optional[VehicleAssessment] = None
    ) -> models.QuerySet:
        """
        Get expired quote requests that haven't been marked as expired.
        
        Args:
            assessment: Optional assessment to filter by
        
        Returns:
            QuerySet of expired PartQuoteRequest objects
        """
        now = timezone.now()
        
        queryset = PartQuoteRequest.objects.filter(
            expiry_date__lt=now,
            status__in=['draft', 'pending', 'sent']
        ).select_related(
            'damaged_part', 'assessment', 'dispatched_by'
        ).order_by('expiry_date')
        
        if assessment:
            queryset = queryset.filter(assessment=assessment)
        
        return queryset
    
    def cleanup_expired_requests(self) -> int:
        """
        Mark expired requests as expired and return count.
        
        Returns:
            Number of requests marked as expired
        """
        expired_requests = self.get_expired_requests()
        count = 0
        
        for request in expired_requests:
            try:
                self.update_request_status(request.request_id, 'expired')
                count += 1
            except Exception as e:
                self.logger.error(
                    f"Error marking request {request.request_id} as expired: {str(e)}"
                )
        
        if count > 0:
            self.logger.info(f"Marked {count} quote requests as expired")
        
        return count
    
    def get_request_statistics(
        self, 
        assessment: Optional[VehicleAssessment] = None
    ) -> Dict[str, int]:
        """
        Get statistics about quote requests.
        
        Args:
            assessment: Optional assessment to filter by
        
        Returns:
            Dict with request statistics
        """
        queryset = PartQuoteRequest.objects.all()
        
        if assessment:
            queryset = queryset.filter(assessment=assessment)
        
        stats = {
            'total': queryset.count(),
            'draft': queryset.filter(status='draft').count(),
            'pending': queryset.filter(status='pending').count(),
            'sent': queryset.filter(status='sent').count(),
            'received': queryset.filter(status='received').count(),
            'expired': queryset.filter(status='expired').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
        }
        
        return stats
    
    def _validate_status_transition(self, current_status: str, new_status: str) -> bool:
        """
        Validate that a status transition is allowed.
        
        Args:
            current_status: Current request status
            new_status: Proposed new status
        
        Returns:
            True if transition is valid
        
        Raises:
            ValidationError: If transition is invalid
        """
        # Define valid transitions
        valid_transitions = {
            'draft': ['pending', 'cancelled'],
            'pending': ['sent', 'cancelled'],
            'sent': ['received', 'expired', 'cancelled'],
            'received': ['cancelled'],  # Can cancel even after receiving
            'expired': ['cancelled'],   # Can cancel expired requests
            'cancelled': [],            # Terminal state
        }
        
        allowed_statuses = valid_transitions.get(current_status, [])
        
        if new_status not in allowed_statuses:
            raise ValidationError(
                f"Invalid status transition from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {allowed_statuses}"
            )
        
        return True