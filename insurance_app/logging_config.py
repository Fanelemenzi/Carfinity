"""
Logging configuration for the parts-based quote system.
This module provides structured logging for all quote system operations.
"""

import logging
import json
from datetime import datetime
from django.conf import settings
from django.utils import timezone

from .models import QuoteSystemAuditLog, QuoteSystemConfiguration

class QuoteSystemLogger:
    """
    Centralized logger for quote system operations with audit trail support.
    """
    
    def __init__(self, component_name='quote_system'):
        self.component_name = component_name
        self.logger = logging.getLogger(f'quote_system.{component_name}')
        
        # Check if performance logging is enabled
        try:
            config = QuoteSystemConfiguration.get_config()
            self.performance_logging_enabled = config.enable_performance_logging
        except:
            self.performance_logging_enabled = True  # Default to enabled
    
    def log_parts_identification(self, assessment, parts_count, duration_seconds, user=None):
        """Log parts identification operation"""
        message = f"Parts identification completed for assessment {assessment.id}: {parts_count} parts identified in {duration_seconds:.2f}s"
        
        self.logger.info(message)
        
        if self.performance_logging_enabled:
            self._create_audit_log(
                action_type='parts_identification',
                severity='info',
                user=user,
                description=message,
                additional_data={
                    'assessment_id': assessment.id,
                    'parts_count': parts_count,
                    'duration_seconds': duration_seconds
                },
                object_type='assessment',
                object_id=str(assessment.id)
            )
    
    def log_quote_request_created(self, quote_request, user=None):
        """Log quote request creation"""
        providers = quote_request.get_selected_providers()
        message = f"Quote request {quote_request.request_id} created for part {quote_request.damaged_part.part_name} with providers: {', '.join(providers)}"
        
        self.logger.info(message)
        
        self._create_audit_log(
            action_type='quote_request_created',
            severity='info',
            user=user,
            description=message,
            additional_data={
                'request_id': quote_request.request_id,
                'part_name': quote_request.damaged_part.part_name,
                'providers': providers,
                'assessment_id': quote_request.assessment.id
            },
            object_type='quote_request',
            object_id=str(quote_request.id)
        )
    
    def log_quote_request_dispatched(self, quote_request, provider_type, success=True, error_message=None, user=None):
        """Log quote request dispatch"""
        if success:
            message = f"Quote request {quote_request.request_id} successfully dispatched to {provider_type} provider"
            severity = 'info'
        else:
            message = f"Failed to dispatch quote request {quote_request.request_id} to {provider_type} provider: {error_message}"
            severity = 'error'
        
        self.logger.log(logging.INFO if success else logging.ERROR, message)
        
        self._create_audit_log(
            action_type='quote_request_dispatched',
            severity=severity,
            user=user,
            description=message,
            additional_data={
                'request_id': quote_request.request_id,
                'provider_type': provider_type,
                'success': success,
                'error_message': error_message
            },
            object_type='quote_request',
            object_id=str(quote_request.id)
        )
    
    def log_quote_received(self, quote, validation_success=True, validation_errors=None, user=None):
        """Log quote reception and validation"""
        if validation_success:
            message = f"Quote received from {quote.provider_name} ({quote.provider_type}) for {quote.damaged_part.part_name}: £{quote.total_cost}"
            severity = 'info'
            action_type = 'quote_received'
        else:
            message = f"Quote from {quote.provider_name} rejected due to validation errors: {', '.join(validation_errors or [])}"
            severity = 'warning'
            action_type = 'quote_rejected'
        
        self.logger.log(logging.INFO if validation_success else logging.WARNING, message)
        
        self._create_audit_log(
            action_type=action_type,
            severity=severity,
            user=user,
            description=message,
            additional_data={
                'quote_id': quote.id,
                'provider_name': quote.provider_name,
                'provider_type': quote.provider_type,
                'part_name': quote.damaged_part.part_name,
                'total_cost': float(quote.total_cost),
                'validation_success': validation_success,
                'validation_errors': validation_errors or []
            },
            object_type='quote',
            object_id=str(quote.id)
        )
    
    def log_market_average_calculated(self, market_average, duration_seconds=None, user=None):
        """Log market average calculation"""
        message = f"Market average calculated for {market_average.damaged_part.part_name}: £{market_average.average_total_cost} (confidence: {market_average.confidence_level}%)"
        
        if duration_seconds and self.performance_logging_enabled:
            message += f" in {duration_seconds:.2f}s"
        
        self.logger.info(message)
        
        additional_data = {
            'part_name': market_average.damaged_part.part_name,
            'average_cost': float(market_average.average_total_cost),
            'confidence_level': market_average.confidence_level,
            'quote_count': market_average.quote_count,
            'standard_deviation': float(market_average.standard_deviation)
        }
        
        if duration_seconds:
            additional_data['duration_seconds'] = duration_seconds
        
        self._create_audit_log(
            action_type='market_average_calculated',
            severity='info',
            user=user,
            description=message,
            additional_data=additional_data,
            object_type='market_average',
            object_id=str(market_average.id)
        )
    
    def log_recommendation_generated(self, assessment, recommended_provider, potential_savings, duration_seconds=None, user=None):
        """Log recommendation generation"""
        message = f"Recommendation generated for assessment {assessment.id}: {recommended_provider} provider recommended with £{potential_savings:.2f} potential savings"
        
        if duration_seconds and self.performance_logging_enabled:
            message += f" in {duration_seconds:.2f}s"
        
        self.logger.info(message)
        
        additional_data = {
            'assessment_id': assessment.id,
            'recommended_provider': recommended_provider,
            'potential_savings': float(potential_savings)
        }
        
        if duration_seconds:
            additional_data['duration_seconds'] = duration_seconds
        
        self._create_audit_log(
            action_type='recommendation_generated',
            severity='info',
            user=user,
            description=message,
            additional_data=additional_data,
            object_type='assessment',
            object_id=str(assessment.id)
        )
    
    def log_provider_performance(self, provider_type, success_rate, response_time_hours, user=None):
        """Log provider performance metrics"""
        message = f"Provider performance update - {provider_type}: {success_rate:.1f}% success rate, {response_time_hours:.1f}h avg response time"
        
        self.logger.info(message)
        
        self._create_audit_log(
            action_type='provider_performance_updated',
            severity='info',
            user=user,
            description=message,
            additional_data={
                'provider_type': provider_type,
                'success_rate': success_rate,
                'response_time_hours': response_time_hours
            },
            object_type='provider',
            object_id=provider_type
        )
    
    def log_system_error(self, error_type, error_message, context=None, user=None):
        """Log system errors"""
        message = f"System error ({error_type}): {error_message}"
        
        self.logger.error(message)
        
        additional_data = {
            'error_type': error_type,
            'error_message': error_message
        }
        
        if context:
            additional_data['context'] = context
        
        self._create_audit_log(
            action_type='system_error',
            severity='error',
            user=user,
            description=message,
            additional_data=additional_data,
            object_type='system',
            object_id='error'
        )
    
    def log_user_action(self, action, description, user, object_type=None, object_id=None, additional_data=None):
        """Log user actions in the quote system"""
        message = f"User action - {user.username}: {action} - {description}"
        
        self.logger.info(message)
        
        audit_data = {
            'action': action,
            'username': user.username
        }
        
        if additional_data:
            audit_data.update(additional_data)
        
        self._create_audit_log(
            action_type='user_action',
            severity='info',
            user=user,
            description=message,
            additional_data=audit_data,
            object_type=object_type or 'user_action',
            object_id=object_id or action
        )
    
    def log_configuration_change(self, change_description, old_value, new_value, user=None):
        """Log configuration changes"""
        message = f"Configuration changed: {change_description} - {old_value} → {new_value}"
        
        self.logger.info(message)
        
        self._create_audit_log(
            action_type='configuration_updated',
            severity='info',
            user=user,
            description=message,
            additional_data={
                'change_description': change_description,
                'old_value': str(old_value),
                'new_value': str(new_value)
            },
            object_type='configuration',
            object_id='system'
        )
    
    def _create_audit_log(self, action_type, severity, description, additional_data=None, 
                         user=None, object_type=None, object_id=None, session_key=None, 
                         ip_address=None, user_agent=None):
        """Create audit log entry"""
        try:
            QuoteSystemAuditLog.objects.create(
                action_type=action_type,
                severity=severity,
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                object_type=object_type,
                object_id=object_id,
                object_repr=f"{object_type} #{object_id}" if object_type and object_id else None,
                description=description,
                additional_data=additional_data or {}
            )
        except Exception as e:
            # If audit logging fails, log to standard logger but don't raise
            self.logger.error(f"Failed to create audit log entry: {str(e)}")

# Convenience functions for common logging operations
def get_quote_logger(component_name='quote_system'):
    """Get a quote system logger instance"""
    return QuoteSystemLogger(component_name)

def log_quote_operation(operation_name, success=True, duration=None, details=None, user=None):
    """Log a generic quote operation"""
    logger = get_quote_logger()
    
    if success:
        message = f"Quote operation '{operation_name}' completed successfully"
        if duration:
            message += f" in {duration:.2f}s"
        logger.logger.info(message)
    else:
        message = f"Quote operation '{operation_name}' failed"
        if details:
            message += f": {details}"
        logger.logger.error(message)
    
    logger._create_audit_log(
        action_type='quote_operation',
        severity='info' if success else 'error',
        user=user,
        description=message,
        additional_data={
            'operation_name': operation_name,
            'success': success,
            'duration': duration,
            'details': details
        },
        object_type='operation',
        object_id=operation_name
    )

# Context manager for performance logging
class QuoteOperationTimer:
    """Context manager for timing quote operations"""
    
    def __init__(self, operation_name, logger=None, user=None):
        self.operation_name = operation_name
        self.logger = logger or get_quote_logger()
        self.user = user
        self.start_time = None
        self.success = True
        self.error_message = None
    
    def __enter__(self):
        self.start_time = timezone.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (timezone.now() - self.start_time).total_seconds()
        
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
        
        log_quote_operation(
            self.operation_name,
            success=self.success,
            duration=duration,
            details=self.error_message,
            user=self.user
        )
        
        # Don't suppress exceptions
        return False

# Example usage:
# with QuoteOperationTimer('parts_identification', user=request.user):
#     # Your operation code here
#     identify_parts(assessment)