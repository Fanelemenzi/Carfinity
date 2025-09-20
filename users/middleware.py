"""
Middleware for handling authentication and authorization errors.

This middleware provides global error handling for authentication failures
and integrates with the error handling system.
"""

import logging
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from .error_handlers import AuthenticationErrorHandler, ErrorType, SecurityEventLogger

logger = logging.getLogger(__name__)


class AuthenticationErrorMiddleware:
    """
    Middleware to handle authentication and authorization errors globally.
    
    This middleware catches authentication-related exceptions and provides
    consistent error handling across the application.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Handle authentication-related exceptions"""
        
        if isinstance(exception, PermissionDenied):
            # Handle Django's built-in PermissionDenied exception
            return self._handle_permission_denied(request, exception)
        
        # Let other exceptions bubble up
        return None
    
    def _handle_permission_denied(self, request, exception):
        """Handle PermissionDenied exceptions"""
        user = getattr(request, 'user', None)
        
        # Log the permission denied event
        SecurityEventLogger.log_access_denied(
            user=user if user and not isinstance(user, AnonymousUser) else None,
            requested_resource=request.path,
            error_type=ErrorType.ACCESS_DENIED,
            additional_info={
                'exception_message': str(exception),
                'view_name': getattr(request.resolver_match, 'view_name', 'unknown') if hasattr(request, 'resolver_match') else 'unknown'
            }
        )
        
        # Determine appropriate error type
        if not user or isinstance(user, AnonymousUser):
            error_type = ErrorType.NO_AUTHENTICATION
        else:
            error_type = ErrorType.ACCESS_DENIED
        
        # Use the error handler
        return AuthenticationErrorHandler.handle_access_denied(
            request, error_type, str(exception)
        )


class SessionSecurityMiddleware:
    """
    Middleware to handle session security and timeout.
    
    This middleware checks for session expiration and handles
    security-related session issues.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check session before processing request
        self._check_session_security(request)
        
        response = self.get_response(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _check_session_security(self, request):
        """Check session security and validity"""
        if not hasattr(request, 'session'):
            return
        
        # Check for session tampering indicators
        if request.user.is_authenticated:
            session_user_id = request.session.get('_auth_user_id')
            if session_user_id and str(request.user.id) != session_user_id:
                # Session user ID mismatch - potential tampering
                SecurityEventLogger.log_security_violation(
                    user=request.user,
                    violation_type="session_tampering",
                    details=f"Session user ID mismatch: session={session_user_id}, user={request.user.id}",
                    request_path=request.path
                )
                
                # Clear the session and redirect to login
                request.session.flush()
                messages.error(request, "Your session has been invalidated for security reasons. Please log in again.")
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Add security headers for authentication pages
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add cache control for sensitive pages
        if hasattr(response, 'context_data') and response.context_data:
            # This is a template response with context
            if any(keyword in str(response.context_data) for keyword in ['dashboard', 'access_denied', 'error']):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'


class RequestLoggingMiddleware:
    """
    Middleware to log authentication-related requests.
    
    This middleware logs requests to sensitive endpoints for security monitoring.
    """
    
    # Paths that should be logged for security monitoring
    MONITORED_PATHS = [
        '/login/',
        '/logout/',
        '/dashboard/',
        '/insurance-dashboard/',
        '/access-denied/',
        '/no-groups/',
        '/no-organization/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log request if it's to a monitored path
        self._log_request_if_monitored(request)
        
        response = self.get_response(request)
        
        # Log response for monitored paths
        self._log_response_if_monitored(request, response)
        
        return response
    
    def _log_request_if_monitored(self, request):
        """Log request if it's to a monitored path"""
        if any(request.path.startswith(path) for path in self.MONITORED_PATHS):
            user = getattr(request, 'user', None)
            user_info = f"User {user.id} ({user.username})" if user and user.is_authenticated else "Anonymous"
            
            SecurityEventLogger.log_security_violation(
                user=user if user and user.is_authenticated else None,
                violation_type="monitored_access",
                details=f"{user_info} accessed {request.path} via {request.method}",
                request_path=request.path
            )
    
    def _log_response_if_monitored(self, request, response):
        """Log response for monitored paths"""
        if any(request.path.startswith(path) for path in self.MONITORED_PATHS):
            if response.status_code >= 400:
                user = getattr(request, 'user', None)
                SecurityEventLogger.log_security_violation(
                    user=user if user and user.is_authenticated else None,
                    violation_type="error_response",
                    details=f"HTTP {response.status_code} response for {request.path}",
                    request_path=request.path
                )