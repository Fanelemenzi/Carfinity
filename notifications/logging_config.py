"""
Logging configuration for AutoCare Dashboard Backend
Provides structured logging with performance metrics and security monitoring
"""
import logging
import time
from functools import wraps
from django.conf import settings
from django.utils import timezone
import json


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    """
    
    def format(self, record):
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'vehicle_id'):
            log_entry['vehicle_id'] = record.vehicle_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'performance_metrics'):
            log_entry['performance_metrics'] = record.performance_metrics
        if hasattr(record, 'security_event'):
            log_entry['security_event'] = record.security_event
        if hasattr(record, 'api_endpoint'):
            log_entry['api_endpoint'] = record.api_endpoint
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        if hasattr(record, 'cache_hit'):
            log_entry['cache_hit'] = record.cache_hit
        if hasattr(record, 'database_queries'):
            log_entry['database_queries'] = record.database_queries
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class DashboardLogger:
    """
    Centralized logger for dashboard operations with structured logging
    """
    
    def __init__(self, name='dashboard'):
        self.logger = logging.getLogger(f'notifications.{name}')
    
    def log_api_access(self, user_id, endpoint, method, response_time=None, status_code=None, cache_hit=False):
        """Log API access attempts for security monitoring"""
        self.logger.info(
            f"API access: {method} {endpoint}",
            extra={
                'user_id': user_id,
                'api_endpoint': endpoint,
                'method': method,
                'response_time': response_time,
                'status_code': status_code,
                'cache_hit': cache_hit,
                'security_event': 'api_access'
            }
        )
    
    def log_vehicle_access(self, user_id, vehicle_id, action, success=True):
        """Log vehicle access attempts for security monitoring"""
        level = logging.INFO if success else logging.WARNING
        message = f"Vehicle access {'successful' if success else 'denied'}: {action}"
        
        self.logger.log(
            level,
            message,
            extra={
                'user_id': user_id,
                'vehicle_id': vehicle_id,
                'security_event': 'vehicle_access',
                'action': action,
                'success': success
            }
        )
    
    def log_data_retrieval(self, data_type, user_id, vehicle_id=None, success=True, response_time=None, cache_hit=False):
        """Log data retrieval operations with performance metrics"""
        level = logging.INFO if success else logging.ERROR
        message = f"Data retrieval {'successful' if success else 'failed'}: {data_type}"
        
        extra_data = {
            'user_id': user_id,
            'data_type': data_type,
            'success': success,
            'cache_hit': cache_hit
        }
        
        if vehicle_id:
            extra_data['vehicle_id'] = vehicle_id
        if response_time:
            extra_data['response_time'] = response_time
        
        self.logger.log(level, message, extra=extra_data)
    
    def log_cache_operation(self, operation, key, success=True, response_time=None):
        """Log cache operations for performance monitoring"""
        level = logging.INFO if success else logging.WARNING
        message = f"Cache {operation} {'successful' if success else 'failed'}: {key}"
        
        self.logger.log(
            level,
            message,
            extra={
                'cache_operation': operation,
                'cache_key': key,
                'success': success,
                'response_time': response_time
            }
        )
    
    def log_external_service_call(self, service_name, success=True, response_time=None, error_message=None):
        """Log external service calls for monitoring"""
        level = logging.INFO if success else logging.ERROR
        message = f"External service call {'successful' if success else 'failed'}: {service_name}"
        
        extra_data = {
            'external_service': service_name,
            'success': success,
            'response_time': response_time
        }
        
        if error_message:
            extra_data['error_message'] = error_message
        
        self.logger.log(level, message, extra=extra_data)
    
    def log_performance_metrics(self, operation, metrics):
        """Log performance metrics for optimization"""
        self.logger.info(
            f"Performance metrics: {operation}",
            extra={
                'performance_metrics': metrics,
                'operation': operation
            }
        )
    
    def log_security_event(self, event_type, user_id, details=None, severity='medium'):
        """Log security events for monitoring"""
        level_map = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }
        
        level = level_map.get(severity, logging.WARNING)
        message = f"Security event: {event_type}"
        
        extra_data = {
            'security_event': event_type,
            'user_id': user_id,
            'severity': severity
        }
        
        if details:
            extra_data['details'] = details
        
        self.logger.log(level, message, extra=extra_data)


def log_performance(operation_name):
    """
    Decorator to log performance metrics for functions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = DashboardLogger('performance')
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                # Log successful operation
                logger.log_performance_metrics(operation_name, {
                    'function': func.__name__,
                    'response_time_ms': response_time,
                    'success': True
                })
                
                return result
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                # Log failed operation
                logger.log_performance_metrics(operation_name, {
                    'function': func.__name__,
                    'response_time_ms': response_time,
                    'success': False,
                    'error': str(e)
                })
                
                raise
        
        return wrapper
    return decorator


def log_api_call(endpoint_name):
    """
    Decorator to log API calls with performance and security metrics
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            logger = DashboardLogger('api')
            start_time = time.time()
            
            # Extract user and vehicle info
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            vehicle_id = kwargs.get('vehicle_id')
            
            try:
                response = func(self, request, *args, **kwargs)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                # Log successful API call
                logger.log_api_access(
                    user_id=user_id,
                    endpoint=endpoint_name,
                    method=request.method,
                    response_time=response_time,
                    status_code=response.status_code if hasattr(response, 'status_code') else None
                )
                
                return response
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                # Log failed API call
                logger.log_api_access(
                    user_id=user_id,
                    endpoint=endpoint_name,
                    method=request.method,
                    response_time=response_time,
                    status_code=500
                )
                
                # Log security event for suspicious activity
                if user_id:
                    logger.log_security_event(
                        'api_error',
                        user_id,
                        details={
                            'endpoint': endpoint_name,
                            'error': str(e),
                            'vehicle_id': vehicle_id
                        }
                    )
                
                raise
        
        return wrapper
    return decorator


class DatabaseQueryLogger:
    """
    Logger for database query performance monitoring
    """
    
    def __init__(self):
        self.logger = DashboardLogger('database')
    
    def log_query_performance(self, query_type, table_name, execution_time, query_count=1):
        """Log database query performance"""
        self.logger.log_performance_metrics('database_query', {
            'query_type': query_type,
            'table_name': table_name,
            'execution_time_ms': execution_time * 1000,
            'query_count': query_count
        })
    
    def log_slow_query(self, query, execution_time, threshold=1000):
        """Log slow queries that exceed threshold"""
        if execution_time * 1000 > threshold:
            self.logger.logger.warning(
                f"Slow query detected: {execution_time * 1000:.2f}ms",
                extra={
                    'performance_metrics': {
                        'query': query[:200],  # Truncate long queries
                        'execution_time_ms': execution_time * 1000,
                        'threshold_ms': threshold
                    }
                }
            )


# Configure logging settings
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': StructuredFormatter,
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/dashboard.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'structured',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'structured',
        },
        'performance_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/performance.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'structured',
        },
    },
    'loggers': {
        'notifications': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications.api': {
            'handlers': ['console', 'file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications.performance': {
            'handlers': ['console', 'performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications.database': {
            'handlers': ['console', 'performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


def setup_logging():
    """
    Setup logging configuration for the dashboard
    """
    import logging.config
    import os
    
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log startup message
    logger = DashboardLogger('startup')
    logger.logger.info("Dashboard logging system initialized")


# Initialize logging when module is imported
setup_logging()