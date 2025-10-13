"""
Custom exceptions for the AutoCare Dashboard Backend
"""
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class DashboardException(Exception):
    """Base exception for dashboard-related errors"""
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code or 'DASHBOARD_ERROR'
        self.details = details
        super().__init__(self.message)


class VehicleNotFoundError(DashboardException):
    """Raised when a vehicle is not found or access is denied"""
    def __init__(self, vehicle_id=None, user_id=None):
        message = "Vehicle not found or access denied"
        details = f"Vehicle ID: {vehicle_id}, User ID: {user_id}" if vehicle_id and user_id else None
        super().__init__(message, 'VEHICLE_NOT_FOUND', details)


class VehicleAccessDeniedError(DashboardException):
    """Raised when user doesn't have permission to access a vehicle"""
    def __init__(self, vehicle_id=None, user_id=None):
        message = "Access denied to vehicle"
        details = f"Vehicle ID: {vehicle_id}, User ID: {user_id}" if vehicle_id and user_id else None
        super().__init__(message, 'VEHICLE_ACCESS_DENIED', details)


class DataRetrievalError(DashboardException):
    """Raised when data retrieval fails"""
    def __init__(self, data_type, original_error=None):
        message = f"Failed to retrieve {data_type} data"
        details = str(original_error) if original_error else None
        super().__init__(message, 'DATA_RETRIEVAL_ERROR', details)


class ExternalServiceError(DashboardException):
    """Raised when external service calls fail"""
    def __init__(self, service_name, original_error=None):
        message = f"External service '{service_name}' is unavailable"
        details = str(original_error) if original_error else None
        super().__init__(message, 'EXTERNAL_SERVICE_ERROR', details)


class ValidationError(DashboardException):
    """Raised when input validation fails"""
    def __init__(self, field_name, value=None, reason=None):
        message = f"Validation failed for field '{field_name}'"
        details = f"Value: {value}, Reason: {reason}" if value and reason else None
        super().__init__(message, 'VALIDATION_ERROR', details)


class CacheError(DashboardException):
    """Raised when cache operations fail"""
    def __init__(self, operation, key=None, original_error=None):
        message = f"Cache {operation} operation failed"
        details = f"Key: {key}, Error: {str(original_error)}" if key and original_error else None
        super().__init__(message, 'CACHE_ERROR', details)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for API views
    Returns standardized error responses
    """
    # Get the standard error response
    response = exception_handler(exc, context)
    
    # Handle custom dashboard exceptions
    if isinstance(exc, DashboardException):
        custom_response_data = {
            'error': {
                'code': exc.code,
                'message': exc.message,
                'details': exc.details
            }
        }
        
        # Map exception types to HTTP status codes
        status_code_map = {
            'VEHICLE_NOT_FOUND': status.HTTP_404_NOT_FOUND,
            'VEHICLE_ACCESS_DENIED': status.HTTP_403_FORBIDDEN,
            'DATA_RETRIEVAL_ERROR': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'EXTERNAL_SERVICE_ERROR': status.HTTP_503_SERVICE_UNAVAILABLE,
            'VALIDATION_ERROR': status.HTTP_400_BAD_REQUEST,
            'CACHE_ERROR': status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        
        status_code = status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log the error
        logger.error(f"Dashboard exception: {exc.code} - {exc.message}", extra={
            'exception_type': type(exc).__name__,
            'code': exc.code,
            'details': exc.details,
            'context': context
        })
        
        return Response(custom_response_data, status=status_code)
    
    # Handle standard DRF exceptions with custom format
    if response is not None:
        custom_response_data = {
            'error': {
                'code': 'API_ERROR',
                'message': 'An error occurred while processing your request',
                'details': response.data
            }
        }
        response.data = custom_response_data
        
        # Log API errors
        logger.warning(f"API error: {response.status_code}", extra={
            'status_code': response.status_code,
            'response_data': response.data,
            'context': context
        })
    
    return response


class ErrorHandler:
    """
    Utility class for handling errors with graceful degradation
    """
    
    @staticmethod
    def handle_data_retrieval(func, fallback_value=None, error_message=None):
        """
        Handle data retrieval with graceful degradation
        
        Args:
            func: Function to execute
            fallback_value: Value to return if function fails
            error_message: Custom error message for logging
        
        Returns:
            Function result or fallback value
        """
        try:
            return func()
        except Exception as e:
            error_msg = error_message or f"Error in {func.__name__}"
            logger.warning(f"{error_msg}: {str(e)}", exc_info=True)
            return fallback_value
    
    @staticmethod
    def handle_external_service(service_name, func, fallback_value=None):
        """
        Handle external service calls with graceful degradation
        
        Args:
            service_name: Name of the external service
            func: Function that calls the external service
            fallback_value: Value to return if service fails
        
        Returns:
            Service result or fallback value
        """
        try:
            return func()
        except Exception as e:
            logger.error(f"External service '{service_name}' failed: {str(e)}", exc_info=True)
            if fallback_value is not None:
                logger.info(f"Using fallback value for {service_name}")
                return fallback_value
            raise ExternalServiceError(service_name, e)
    
    @staticmethod
    def handle_cache_operation(operation, key, func, fallback_func=None):
        """
        Handle cache operations with fallback to database
        
        Args:
            operation: Cache operation name (get, set, delete)
            key: Cache key
            func: Cache operation function
            fallback_func: Function to call if cache fails
        
        Returns:
            Cache result or fallback result
        """
        try:
            return func()
        except Exception as e:
            logger.warning(f"Cache {operation} failed for key '{key}': {str(e)}")
            if fallback_func:
                logger.info(f"Using fallback for cache {operation}")
                return fallback_func()
            return None
    
    @staticmethod
    def validate_vehicle_access(user, vehicle_id):
        """
        Validate user access to vehicle with proper error handling
        
        Args:
            user: User object
            vehicle_id: Vehicle ID to validate
        
        Returns:
            Vehicle object if access is valid
        
        Raises:
            VehicleNotFoundError: If vehicle doesn't exist
            VehicleAccessDeniedError: If user doesn't have access
        """
        from vehicles.models import Vehicle
        
        try:
            vehicle = Vehicle.objects.get(
                id=vehicle_id,
                ownerships__user=user,
                ownerships__is_current_owner=True
            )
            return vehicle
        except Vehicle.DoesNotExist:
            # Check if vehicle exists but user doesn't have access
            if Vehicle.objects.filter(id=vehicle_id).exists():
                raise VehicleAccessDeniedError(vehicle_id, user.id)
            else:
                raise VehicleNotFoundError(vehicle_id, user.id)
    
    @staticmethod
    def safe_float_conversion(value, default=0.0):
        """
        Safely convert value to float with fallback
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
        
        Returns:
            Float value or default
        """
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert '{value}' to float, using default {default}")
            return default
    
    @staticmethod
    def safe_int_conversion(value, default=0):
        """
        Safely convert value to int with fallback
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
        
        Returns:
            Int value or default
        """
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert '{value}' to int, using default {default}")
            return default