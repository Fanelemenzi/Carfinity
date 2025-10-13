"""
Monitoring middleware for AutoCare Dashboard Backend
Provides performance monitoring, security logging, and metrics collection
"""
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from .logging_config import DashboardLogger
import logging

logger = logging.getLogger(__name__)
dashboard_logger = DashboardLogger('middleware')


class DashboardMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor dashboard performance and security events
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.monitoring_config = getattr(settings, 'DASHBOARD_MONITORING', {})
        self.security_config = getattr(settings, 'SECURITY_MONITORING', {})
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Process incoming request and start monitoring
        """
        # Record request start time
        request._monitoring_start_time = time.time()
        request._monitoring_start_queries = len(connection.queries)
        
        # Log API access for dashboard endpoints
        if request.path.startswith('/notifications/'):
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            dashboard_logger.log_api_access(
                user_id=user_id,
                endpoint=request.path,
                method=request.method
            )
        
        return None
    
    def process_response(self, request, response):
        """
        Process response and log performance metrics
        """
        if not hasattr(request, '_monitoring_start_time'):
            return response
        
        # Calculate response time
        response_time = (time.time() - request._monitoring_start_time) * 1000  # Convert to milliseconds
        
        # Calculate database queries
        query_count = len(connection.queries) - request._monitoring_start_queries
        
        # Log performance metrics for dashboard endpoints
        if request.path.startswith('/notifications/'):
            self._log_performance_metrics(request, response, response_time, query_count)
        
        # Check for slow responses
        threshold = self.monitoring_config.get('API_RESPONSE_TIME_THRESHOLD_MS', 2000)
        if response_time > threshold:
            self._log_slow_response(request, response_time, query_count)
        
        # Log security events
        if response.status_code in [403, 404] and request.path.startswith('/notifications/'):
            self._log_security_event(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        """
        Process exceptions and log error metrics
        """
        if hasattr(request, '_monitoring_start_time'):
            response_time = (time.time() - request._monitoring_start_time) * 1000
            query_count = len(connection.queries) - request._monitoring_start_queries
            
            # Log exception with performance context
            dashboard_logger.logger.error(
                f"Exception in {request.path}: {str(exception)}",
                extra={
                    'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                    'api_endpoint': request.path,
                    'method': request.method,
                    'response_time': response_time,
                    'database_queries': query_count,
                    'exception_type': type(exception).__name__,
                    'security_event': 'api_exception'
                },
                exc_info=True
            )
        
        return None
    
    def _log_performance_metrics(self, request, response, response_time, query_count):
        """
        Log detailed performance metrics for dashboard operations
        """
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Extract vehicle ID from URL if present
        vehicle_id = None
        path_parts = request.path.split('/')
        for i, part in enumerate(path_parts):
            if part == 'vehicle' and i + 1 < len(path_parts):
                try:
                    vehicle_id = int(path_parts[i + 1])
                    break
                except ValueError:
                    pass
        
        # Check cache hit rate for this request
        cache_hit = self._check_cache_hit(request)
        
        # Log comprehensive performance metrics
        dashboard_logger.log_performance_metrics('api_request', {
            'endpoint': request.path,
            'method': request.method,
            'user_id': user_id,
            'vehicle_id': vehicle_id,
            'response_time_ms': response_time,
            'status_code': response.status_code,
            'database_queries': query_count,
            'cache_hit': cache_hit,
            'content_length': len(response.content) if hasattr(response, 'content') else 0
        })
        
        # Log to API access logger with performance data
        dashboard_logger.log_api_access(
            user_id=user_id,
            endpoint=request.path,
            method=request.method,
            response_time=response_time,
            status_code=response.status_code,
            cache_hit=cache_hit
        )
    
    def _log_slow_response(self, request, response_time, query_count):
        """
        Log slow API responses for performance optimization
        """
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        
        dashboard_logger.logger.warning(
            f"Slow response detected: {request.path} took {response_time:.2f}ms",
            extra={
                'user_id': user_id,
                'api_endpoint': request.path,
                'method': request.method,
                'response_time': response_time,
                'database_queries': query_count,
                'performance_metrics': {
                    'slow_response': True,
                    'threshold_exceeded': True
                }
            }
        )
    
    def _log_security_event(self, request, response):
        """
        Log security-related events for monitoring
        """
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        
        event_type = 'access_denied' if response.status_code == 403 else 'resource_not_found'
        severity = 'medium' if response.status_code == 403 else 'low'
        
        dashboard_logger.log_security_event(
            event_type,
            user_id,
            details={
                'endpoint': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request)
            },
            severity=severity
        )
    
    def _check_cache_hit(self, request):
        """
        Check if this request likely hit the cache
        """
        # This is a simplified cache hit detection
        # In a real implementation, you'd track cache keys and hits more precisely
        cache_key = f"request_cache_{request.path}_{request.user.id if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}"
        return cache.get(cache_key) is not None
    
    def _get_client_ip(self, request):
        """
        Get the client IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware specifically for security monitoring and threat detection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_config = getattr(settings, 'SECURITY_MONITORING', {})
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Monitor for suspicious security patterns
        """
        if not self.security_config.get('LOG_SUSPICIOUS_ACTIVITY', True):
            return None
        
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        client_ip = self._get_client_ip(request)
        
        # Check for rapid successive requests (potential brute force)
        if user_id:
            self._check_rapid_requests(user_id, client_ip, request.path)
        
        # Check for suspicious vehicle access patterns
        if '/vehicle/' in request.path:
            self._check_vehicle_access_patterns(user_id, client_ip, request.path)
        
        return None
    
    def _check_rapid_requests(self, user_id, client_ip, endpoint):
        """
        Check for rapid successive requests that might indicate abuse
        """
        cache_key = f"request_rate_{user_id}_{client_ip}"
        current_time = time.time()
        
        # Get recent request timestamps
        recent_requests = cache.get(cache_key, [])
        
        # Remove requests older than 1 hour
        recent_requests = [ts for ts in recent_requests if current_time - ts < 3600]
        
        # Add current request
        recent_requests.append(current_time)
        
        # Update cache
        cache.set(cache_key, recent_requests, 3600)  # Store for 1 hour
        
        # Check if threshold exceeded
        max_requests = self.security_config.get('MAX_FAILED_ATTEMPTS_PER_HOUR', 10)
        if len(recent_requests) > max_requests:
            dashboard_logger = DashboardLogger('security')
            dashboard_logger.log_security_event(
                'rapid_requests',
                user_id,
                details={
                    'endpoint': endpoint,
                    'client_ip': client_ip,
                    'request_count': len(recent_requests),
                    'time_window': '1 hour'
                },
                severity='high'
            )
    
    def _check_vehicle_access_patterns(self, user_id, client_ip, endpoint):
        """
        Check for suspicious vehicle access patterns
        """
        if not self.security_config.get('ALERT_ON_MULTIPLE_VEHICLE_ACCESS_ATTEMPTS', True):
            return
        
        # Extract vehicle ID from endpoint
        vehicle_id = None
        path_parts = endpoint.split('/')
        for i, part in enumerate(path_parts):
            if part == 'vehicle' and i + 1 < len(path_parts):
                try:
                    vehicle_id = int(path_parts[i + 1])
                    break
                except ValueError:
                    pass
        
        if not vehicle_id or not user_id:
            return
        
        # Track vehicle access attempts
        cache_key = f"vehicle_access_{user_id}_{vehicle_id}"
        current_time = time.time()
        
        access_attempts = cache.get(cache_key, [])
        access_attempts = [ts for ts in access_attempts if current_time - ts < 300]  # Last 5 minutes
        access_attempts.append(current_time)
        
        cache.set(cache_key, access_attempts, 300)
        
        # Alert on multiple rapid access attempts to the same vehicle
        if len(access_attempts) > 5:  # More than 5 attempts in 5 minutes
            dashboard_logger = DashboardLogger('security')
            dashboard_logger.log_security_event(
                'multiple_vehicle_access',
                user_id,
                details={
                    'vehicle_id': vehicle_id,
                    'client_ip': client_ip,
                    'attempt_count': len(access_attempts),
                    'time_window': '5 minutes'
                },
                severity='medium'
            )
    
    def _get_client_ip(self, request):
        """
        Get the client IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DatabaseQueryMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor database query performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.monitoring_config = getattr(settings, 'DASHBOARD_MONITORING', {})
        super().__init__(get_response)
    
    def process_response(self, request, response):
        """
        Monitor database query performance
        """
        if not self.monitoring_config.get('ENABLE_PERFORMANCE_LOGGING', True):
            return response
        
        if not hasattr(request, '_monitoring_start_queries'):
            return response
        
        # Calculate query metrics
        query_count = len(connection.queries) - request._monitoring_start_queries
        slow_query_threshold = self.monitoring_config.get('SLOW_QUERY_THRESHOLD_MS', 1000) / 1000.0
        
        # Check for slow queries
        slow_queries = []
        for query in connection.queries[request._monitoring_start_queries:]:
            query_time = float(query['time'])
            if query_time > slow_query_threshold:
                slow_queries.append({
                    'sql': query['sql'][:200],  # Truncate long queries
                    'time': query_time
                })
        
        # Log slow queries
        if slow_queries:
            dashboard_logger = DashboardLogger('database')
            for slow_query in slow_queries:
                dashboard_logger.logger.warning(
                    f"Slow query detected: {slow_query['time']:.3f}s",
                    extra={
                        'performance_metrics': {
                            'query_time': slow_query['time'],
                            'query_sql': slow_query['sql'],
                            'threshold': slow_query_threshold
                        },
                        'api_endpoint': request.path,
                        'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
                    }
                )
        
        # Log overall query performance for dashboard endpoints
        if request.path.startswith('/notifications/') and query_count > 0:
            total_query_time = sum(float(q['time']) for q in connection.queries[request._monitoring_start_queries:])
            
            dashboard_logger = DashboardLogger('database')
            dashboard_logger.log_performance_metrics('database_queries', {
                'endpoint': request.path,
                'query_count': query_count,
                'total_query_time': total_query_time,
                'average_query_time': total_query_time / query_count if query_count > 0 else 0,
                'slow_query_count': len(slow_queries)
            })
        
        return response