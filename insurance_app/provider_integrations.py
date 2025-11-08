"""
Provider Integration Framework for Parts-Based Quote System

This module provides the integration layer for communicating with different
provider types to collect repair quotes for damaged vehicle parts.
"""

import logging
import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import PartQuoteRequest, PartQuote, DamagedPart


logger = logging.getLogger(__name__)


class ProviderIntegrationError(Exception):
    """Base exception for provider integration errors"""
    pass


class ProviderAuthenticationError(ProviderIntegrationError):
    """Raised when provider authentication fails"""
    pass


class ProviderCommunicationError(ProviderIntegrationError):
    """Raised when communication with provider fails"""
    pass


class ProviderDataError(ProviderIntegrationError):
    """Raised when provider returns invalid data"""
    pass


class ProviderIntegration(ABC):
    """
    Abstract base class for all provider integrations.
    
    Defines the common interface and shared functionality for communicating
    with different types of repair quote providers.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize provider integration with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config or {}
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.timeout = self.config.get('timeout', 30)
        
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the provider.
        
        Returns:
            bool: True if authentication successful, False otherwise
            
        Raises:
            ProviderAuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    def send_quote_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """
        Send a quote request to the provider.
        
        Args:
            quote_request: The PartQuoteRequest instance to send
            
        Returns:
            Dict containing provider response data
            
        Raises:
            ProviderCommunicationError: If request fails
            ProviderDataError: If request data is invalid
        """
        pass
    
    @abstractmethod
    def process_quote_response(self, response_data: Dict[str, Any], 
                             quote_request: PartQuoteRequest) -> PartQuote:
        """
        Process a quote response from the provider.
        
        Args:
            response_data: Raw response data from provider
            quote_request: Original quote request
            
        Returns:
            PartQuote instance created from response
            
        Raises:
            ProviderDataError: If response data is invalid
        """
        pass
    
    def format_request_data(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """
        Format quote request data for provider API.
        
        Args:
            quote_request: The PartQuoteRequest to format
            
        Returns:
            Dict containing formatted request data
        """
        damaged_part = quote_request.damaged_part
        assessment = quote_request.assessment
        
        return {
            'request_id': quote_request.request_id,
            'vehicle': {
                'make': quote_request.vehicle_make,
                'model': quote_request.vehicle_model,
                'year': quote_request.vehicle_year,
                'vin': getattr(assessment.vehicle, 'vin', ''),
                'registration': getattr(assessment.vehicle, 'registration_number', ''),
            },
            'part': {
                'name': damaged_part.part_name,
                'number': damaged_part.part_number or '',
                'category': damaged_part.part_category,
                'damage_severity': damaged_part.damage_severity,
                'damage_description': damaged_part.damage_description,
                'requires_replacement': damaged_part.requires_replacement,
                'estimated_labor_hours': float(damaged_part.estimated_labor_hours),
            },
            'timeline': {
                'request_date': quote_request.request_date.isoformat(),
                'expiry_date': quote_request.expiry_date.isoformat(),
            },
            'contact': {
                'assessor_name': quote_request.dispatched_by.get_full_name(),
                'assessor_email': quote_request.dispatched_by.email,
                'organization': getattr(assessment, 'organization', ''),
            }
        }
    
    def validate_response_data(self, response_data: Dict[str, Any]) -> bool:
        """
        Validate provider response data structure.
        
        Args:
            response_data: Response data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = [
            'provider_name', 'part_cost', 'labor_cost', 'total_cost',
            'estimated_delivery_days', 'estimated_completion_days'
        ]
        
        for field in required_fields:
            if field not in response_data:
                logger.error(f"Missing required field in response: {field}")
                return False
                
        # Validate numeric fields
        numeric_fields = [
            'part_cost', 'labor_cost', 'total_cost',
            'estimated_delivery_days', 'estimated_completion_days'
        ]
        
        for field in numeric_fields:
            try:
                float(response_data[field])
            except (ValueError, TypeError):
                logger.error(f"Invalid numeric value for field: {field}")
                return False
                
        return True
    
    def retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            ProviderCommunicationError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
                    
        raise ProviderCommunicationError(
            f"Failed after {self.max_retries + 1} attempts: {str(last_exception)}"
        )
    
    def log_request(self, quote_request: PartQuoteRequest, action: str, 
                   details: str = None):
        """
        Log provider integration activity.
        
        Args:
            quote_request: The quote request being processed
            action: Action being performed
            details: Additional details to log
        """
        logger.info(
            f"Provider {self.__class__.__name__}: {action} for request "
            f"{quote_request.request_id} - Part: {quote_request.damaged_part.part_name}"
            f"{f' - {details}' if details else ''}"
        )


class DealerIntegration(ProviderIntegration):
    """
    Integration with authorized vehicle dealers.
    
    Supports both API integration and email-based quote requests
    depending on dealer capabilities.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_endpoint = self.config.get('api_endpoint')
        self.api_key = self.config.get('api_key')
        self.email_enabled = self.config.get('email_enabled', True)
        self.dealer_email = self.config.get('dealer_email')
        
    def authenticate(self) -> bool:
        """Authenticate with dealer API or validate email configuration."""
        if self.api_endpoint and self.api_key:
            return self._authenticate_api()
        elif self.email_enabled and self.dealer_email:
            return self._validate_email_config()
        else:
            raise ProviderAuthenticationError(
                "No valid authentication method configured for dealer"
            )
    
    def _authenticate_api(self) -> bool:
        """Authenticate with dealer API."""
        try:
            response = requests.post(
                f"{self.api_endpoint}/auth",
                json={'api_key': self.api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data.get('access_token')
            
            if not self.access_token:
                raise ProviderAuthenticationError("No access token received")
                
            logger.info("Successfully authenticated with dealer API")
            return True
            
        except requests.RequestException as e:
            raise ProviderAuthenticationError(f"API authentication failed: {str(e)}")
    
    def _validate_email_config(self) -> bool:
        """Validate email configuration."""
        if not self.dealer_email:
            raise ProviderAuthenticationError("Dealer email not configured")
            
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.dealer_email):
            raise ProviderAuthenticationError("Invalid dealer email format")
            
        logger.info("Email configuration validated for dealer integration")
        return True
    
    def send_quote_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """Send quote request to dealer via API or email."""
        self.log_request(quote_request, "Sending quote request")
        
        if self.api_endpoint and hasattr(self, 'access_token'):
            return self.retry_with_backoff(self._send_api_request, quote_request)
        else:
            return self.retry_with_backoff(self._send_email_request, quote_request)
    
    def _send_api_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """Send quote request via dealer API."""
        request_data = self.format_request_data(quote_request)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.api_endpoint}/quotes",
            json=request_data,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def _send_email_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """Send quote request via email."""
        request_data = self.format_request_data(quote_request)
        
        # Render email template
        email_content = render_to_string(
            'emails/dealer_quote_request.html',
            {
                'request_data': request_data,
                'quote_request': quote_request,
                'damaged_part': quote_request.damaged_part,
            }
        )
        
        subject = f"Parts Quote Request - {quote_request.request_id}"
        
        send_mail(
            subject=subject,
            message="Please see HTML version",
            html_message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.dealer_email],
            fail_silently=False
        )
        
        self.log_request(quote_request, "Email sent", f"to {self.dealer_email}")
        
        return {
            'status': 'email_sent',
            'recipient': self.dealer_email,
            'request_id': quote_request.request_id
        }
    
    def process_quote_response(self, response_data: Dict[str, Any], 
                             quote_request: PartQuoteRequest) -> PartQuote:
        """Process dealer quote response."""
        if not self.validate_response_data(response_data):
            raise ProviderDataError("Invalid response data from dealer")
        
        # Create PartQuote instance
        quote = PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=quote_request.damaged_part,
            provider_type='dealer',
            provider_name=response_data['provider_name'],
            provider_contact=response_data.get('contact_info', ''),
            
            # Cost breakdown
            part_cost=response_data['part_cost'],
            labor_cost=response_data['labor_cost'],
            paint_cost=response_data.get('paint_cost', 0),
            additional_costs=response_data.get('additional_costs', 0),
            total_cost=response_data['total_cost'],
            
            # Part specifications (dealers typically provide OEM)
            part_type=response_data.get('part_type', 'oem'),
            
            # Timeline and warranty
            estimated_delivery_days=response_data['estimated_delivery_days'],
            estimated_completion_days=response_data['estimated_completion_days'],
            part_warranty_months=response_data.get('part_warranty_months', 24),
            labor_warranty_months=response_data.get('labor_warranty_months', 12),
            
            # Metadata
            valid_until=datetime.now() + timedelta(days=30),
            confidence_score=response_data.get('confidence_score', 85),
            notes=response_data.get('notes', '')
        )
        
        self.log_request(quote_request, "Quote processed", 
                        f"Total: £{quote.total_cost}")
        
        return quote


class IndependentGarageIntegration(ProviderIntegration):
    """
    Integration with independent garage networks and platforms.
    
    Connects to multi-garage quote aggregation platforms to collect
    competitive quotes from independent repair shops.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.platform_url = self.config.get('platform_url')
        self.api_key = self.config.get('api_key')
        self.partner_id = self.config.get('partner_id')
        
    def authenticate(self) -> bool:
        """Authenticate with garage platform API."""
        if not all([self.platform_url, self.api_key, self.partner_id]):
            raise ProviderAuthenticationError(
                "Missing required configuration for garage platform"
            )
        
        try:
            response = requests.post(
                f"{self.platform_url}/api/v1/auth",
                json={
                    'api_key': self.api_key,
                    'partner_id': self.partner_id
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.session_token = auth_data.get('session_token')
            
            if not self.session_token:
                raise ProviderAuthenticationError("No session token received")
                
            logger.info("Successfully authenticated with garage platform")
            return True
            
        except requests.RequestException as e:
            raise ProviderAuthenticationError(
                f"Garage platform authentication failed: {str(e)}"
            )
    
    def send_quote_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """Send quote request to garage platform."""
        self.log_request(quote_request, "Sending to garage platform")
        
        return self.retry_with_backoff(self._send_platform_request, quote_request)
    
    def _send_platform_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """Send request to garage platform API."""
        request_data = self.format_request_data(quote_request)
        
        # Add platform-specific fields
        request_data.update({
            'partner_id': self.partner_id,
            'quote_type': 'parts_and_labor',
            'preferred_part_types': ['aftermarket', 'oem_equivalent'],
            'max_garages': self.config.get('max_garages', 5),
            'location_radius': self.config.get('location_radius', 25),
        })
        
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.platform_url}/api/v1/quote-requests",
            json=request_data,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def process_quote_response(self, response_data: Dict[str, Any], 
                             quote_request: PartQuoteRequest) -> List[PartQuote]:
        """Process garage platform response (may contain multiple quotes)."""
        quotes = []
        
        # Platform may return multiple garage quotes
        garage_quotes = response_data.get('quotes', [])
        
        for garage_quote in garage_quotes:
            if not self.validate_response_data(garage_quote):
                logger.warning(f"Skipping invalid garage quote: {garage_quote}")
                continue
            
            quote = PartQuote.objects.create(
                quote_request=quote_request,
                damaged_part=quote_request.damaged_part,
                provider_type='independent',
                provider_name=garage_quote['provider_name'],
                provider_contact=garage_quote.get('contact_info', ''),
                
                # Cost breakdown
                part_cost=garage_quote['part_cost'],
                labor_cost=garage_quote['labor_cost'],
                paint_cost=garage_quote.get('paint_cost', 0),
                additional_costs=garage_quote.get('additional_costs', 0),
                total_cost=garage_quote['total_cost'],
                
                # Part specifications (independents often use aftermarket)
                part_type=garage_quote.get('part_type', 'aftermarket'),
                
                # Timeline and warranty
                estimated_delivery_days=garage_quote['estimated_delivery_days'],
                estimated_completion_days=garage_quote['estimated_completion_days'],
                part_warranty_months=garage_quote.get('part_warranty_months', 12),
                labor_warranty_months=garage_quote.get('labor_warranty_months', 12),
                
                # Metadata
                valid_until=datetime.now() + timedelta(days=14),
                confidence_score=garage_quote.get('confidence_score', 70),
                notes=garage_quote.get('notes', '')
            )
            
            quotes.append(quote)
            
        self.log_request(quote_request, "Processed garage quotes", 
                        f"Count: {len(quotes)}")
        
        return quotes


class InsuranceNetworkIntegration(ProviderIntegration):
    """
    Integration with insurance network providers.
    
    Connects directly to insurance network APIs for pre-negotiated
    rates and streamlined claims processing.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.network_url = self.config.get('network_url')
        self.client_id = self.config.get('client_id')
        self.client_secret = self.config.get('client_secret')
        self.network_id = self.config.get('network_id')
        
    def authenticate(self) -> bool:
        """Authenticate with insurance network API."""
        if not all([self.network_url, self.client_id, self.client_secret]):
            raise ProviderAuthenticationError(
                "Missing required configuration for insurance network"
            )
        
        try:
            response = requests.post(
                f"{self.network_url}/oauth/token",
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': 'quotes:read quotes:write'
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data.get('access_token')
            self.token_expires = datetime.now() + timedelta(
                seconds=auth_data.get('expires_in', 3600)
            )
            
            if not self.access_token:
                raise ProviderAuthenticationError("No access token received")
                
            logger.info("Successfully authenticated with insurance network")
            return True
            
        except requests.RequestException as e:
            raise ProviderAuthenticationError(
                f"Insurance network authentication failed: {str(e)}"
            )
    
    def send_quote_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """Send quote request to insurance network."""
        self.log_request(quote_request, "Sending to insurance network")
        
        # Check token expiry
        if hasattr(self, 'token_expires') and datetime.now() >= self.token_expires:
            self.authenticate()
        
        return self.retry_with_backoff(self._send_network_request, quote_request)
    
    def _send_network_request(self, quote_request: PartQuoteRequest) -> Dict[str, Any]:
        """Send request to insurance network API."""
        request_data = self.format_request_data(quote_request)
        
        # Add network-specific fields
        request_data.update({
            'network_id': self.network_id,
            'claim_type': 'parts_replacement',
            'priority': self.config.get('priority', 'standard'),
            'preferred_providers': self.config.get('preferred_providers', []),
        })
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.network_url}/api/v2/quote-requests",
            json=request_data,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def process_quote_response(self, response_data: Dict[str, Any], 
                             quote_request: PartQuoteRequest) -> PartQuote:
        """Process insurance network quote response."""
        if not self.validate_response_data(response_data):
            raise ProviderDataError("Invalid response data from insurance network")
        
        # Create PartQuote instance
        quote = PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=quote_request.damaged_part,
            provider_type='network',
            provider_name=response_data['provider_name'],
            provider_contact=response_data.get('contact_info', ''),
            
            # Cost breakdown
            part_cost=response_data['part_cost'],
            labor_cost=response_data['labor_cost'],
            paint_cost=response_data.get('paint_cost', 0),
            additional_costs=response_data.get('additional_costs', 0),
            total_cost=response_data['total_cost'],
            
            # Part specifications (networks often use mix of OEM and aftermarket)
            part_type=response_data.get('part_type', 'oem_equivalent'),
            
            # Timeline and warranty
            estimated_delivery_days=response_data['estimated_delivery_days'],
            estimated_completion_days=response_data['estimated_completion_days'],
            part_warranty_months=response_data.get('part_warranty_months', 18),
            labor_warranty_months=response_data.get('labor_warranty_months', 12),
            
            # Metadata
            valid_until=datetime.now() + timedelta(days=21),
            confidence_score=response_data.get('confidence_score', 80),
            notes=response_data.get('notes', '')
        )
        
        self.log_request(quote_request, "Network quote processed", 
                        f"Total: £{quote.total_cost}")
        
        return quote


# Provider factory for easy instantiation
class ProviderFactory:
    """Factory class for creating provider integration instances."""
    
    PROVIDER_CLASSES = {
        'dealer': DealerIntegration,
        'independent': IndependentGarageIntegration,
        'network': InsuranceNetworkIntegration,
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any] = None) -> ProviderIntegration:
        """
        Create a provider integration instance.
        
        Args:
            provider_type: Type of provider ('dealer', 'independent', 'network')
            config: Provider-specific configuration
            
        Returns:
            ProviderIntegration instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type not in cls.PROVIDER_CLASSES:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        provider_class = cls.PROVIDER_CLASSES[provider_type]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider types."""
        return list(cls.PROVIDER_CLASSES.keys())