"""
Error handling utilities for the group-based authentication system.

This module provides centralized error handling, user feedback, and logging
for authentication and authorization failures.
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime

# Configure logger for security events
security_logger = logging.getLogger('security')
auth_logger = logging.getLogger('authentication')


class ErrorType:
    """Constants for different error types"""
    NO_AUTHENTICATION = 'no_authentication'
    NO_GROUPS = 'no_groups'
    NO_ORGANIZATION = 'no_organization'
    GROUP_ORG_MISMATCH = 'group_org_mismatch'
    ACCESS_DENIED = 'access_denied'
    INVALID_PERMISSIONS = 'invalid_permissions'
    SYSTEM_ERROR = 'system_error'
    SESSION_EXPIRED = 'session_expired'


class SecurityEventLogger:
    """Handles logging of security events and access violations"""
    
    @staticmethod
    def log_access_denied(user: Optional[User], requested_resource: str, 
                         error_type: str, additional_info: Optional[Dict] = None):
        """Log access denied events"""
        user_info = f"User {user.id} ({user.username})" if user else "Anonymous user"
        
        security_logger.warning(
            f"Access denied: {user_info} attempted to access {requested_resource}. "
            f"Reason: {error_type}. Additional info: {additional_info or {}}"
        )
    
    @staticmethod
    def log_authentication_attempt(username: str, success: bool, ip_address: str = None):
        """Log authentication attempts"""
        status = "successful" if success else "failed"
        ip_info = f" from {ip_address}" if ip_address else ""
        
        auth_logger.info(f"Authentication {status} for username: {username}{ip_info}")
    
    @staticmethod
    def log_permission_conflict(user: User, groups: List[str], org_type: str, 
                               conflict_details: str):
        """Log permission conflicts between groups and organization"""
        security_logger.warning(
            f"Permission conflict for User {user.id} ({user.username}): "
            f"Groups: {groups}, Org Type: {org_type}. Details: {conflict_details}"
        )
    
    @staticmethod
    def log_security_violation(user: Optional[User], violation_type: str, 
                              details: str, request_path: str = None):
        """Log general security violations"""
        user_info = f"User {user.id} ({user.username})" if user else "Anonymous user"
        path_info = f" on path {request_path}" if request_path else ""
        
        security_logger.error(
            f"Security violation: {violation_type} by {user_info}{path_info}. "
            f"Details: {details}"
        )


class ErrorMessageGenerator:
    """Generates user-friendly error messages and suggestions"""
    
    ERROR_MESSAGES = {
        ErrorType.NO_AUTHENTICATION: {
            'title': 'Authentication Required',
            'message': 'You must be logged in to access this page.',
            'suggestions': [
                'Please log in to your account',
                'If you don\'t have an account, you can register for free',
                'Contact support if you\'re having trouble logging in'
            ]
        },
        ErrorType.NO_GROUPS: {
            'title': 'No Group Assignment',
            'message': 'Your account is not assigned to any user groups.',
            'suggestions': [
                'Contact your administrator to assign you to the appropriate group',
                'If you believe this is an error, please contact support',
                'Check if your account setup is complete'
            ]
        },
        ErrorType.NO_ORGANIZATION: {
            'title': 'No Organization Assignment',
            'message': 'Your account is not associated with any organization.',
            'suggestions': [
                'Contact your administrator to assign you to an organization',
                'Complete your profile setup if you haven\'t already',
                'Verify your organization membership with your administrator'
            ]
        },
        ErrorType.GROUP_ORG_MISMATCH: {
            'title': 'Permission Configuration Issue',
            'message': 'There\'s a mismatch between your group assignment and organization type.',
            'suggestions': [
                'Contact your administrator to resolve the permission conflict',
                'This issue has been logged and will be reviewed',
                'You may have limited access until this is resolved'
            ]
        },
        ErrorType.ACCESS_DENIED: {
            'title': 'Access Denied',
            'message': 'You do not have permission to access this page.',
            'suggestions': [
                'Contact your administrator if you need additional permissions',
                'Make sure you\'re accessing the correct dashboard for your role',
                'Check if your account has the necessary group assignments'
            ]
        },
        ErrorType.INVALID_PERMISSIONS: {
            'title': 'Invalid Permissions',
            'message': 'Your current permissions are not valid for this action.',
            'suggestions': [
                'Contact your administrator to review your permissions',
                'Try logging out and logging back in',
                'Verify your organization membership is active'
            ]
        },
        ErrorType.SYSTEM_ERROR: {
            'title': 'System Error',
            'message': 'An unexpected error occurred while processing your request.',
            'suggestions': [
                'Please try again in a few moments',
                'Contact support if the problem persists',
                'Check if there are any system maintenance notifications'
            ]
        },
        ErrorType.SESSION_EXPIRED: {
            'title': 'Session Expired',
            'message': 'Your session has expired for security reasons.',
            'suggestions': [
                'Please log in again to continue',
                'Make sure to save your work regularly',
                'Contact support if you\'re experiencing frequent session timeouts'
            ]
        }
    }
    
    @classmethod
    def get_error_context(cls, error_type: str, user: Optional[User] = None, 
                         custom_message: str = None) -> Dict:
        """Generate error context for templates"""
        error_info = cls.ERROR_MESSAGES.get(error_type, cls.ERROR_MESSAGES[ErrorType.SYSTEM_ERROR])
        
        context = {
            'error_title': error_info['title'],
            'error_message': custom_message or error_info['message'],
            'suggestions': error_info['suggestions'].copy(),
            'error_type': error_type,
            'timestamp': timezone.now(),
        }
        
        # Add user-specific suggestions
        if user and user.is_authenticated:
            context['user_groups'] = list(user.groups.values_list('name', flat=True))
            
            # Add specific suggestions based on user state
            if error_type == ErrorType.NO_GROUPS and not context['user_groups']:
                context['suggestions'].insert(0, f'Your account ({user.username}) needs group assignment')
        
        return context


class AuthenticationErrorHandler:
    """Main error handler for authentication and authorization errors"""
    
    @staticmethod
    def handle_access_denied(request, error_type: str, custom_message: str = None,
                           log_event: bool = True) -> HttpResponse:
        """
        Handle access denied scenarios with appropriate logging and user feedback.
        
        Args:
            request: Django request object
            error_type: Type of error from ErrorType constants
            custom_message: Optional custom error message
            log_event: Whether to log this event
            
        Returns:
            HttpResponse with appropriate error page
        """
        user = request.user if hasattr(request, 'user') else None
        
        # Log the event if requested
        if log_event:
            SecurityEventLogger.log_access_denied(
                user=user,
                requested_resource=request.path,
                error_type=error_type,
                additional_info={
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': AuthenticationErrorHandler._get_client_ip(request),
                    'referer': request.META.get('HTTP_REFERER', ''),
                }
            )
        
        # Generate error context
        context = ErrorMessageGenerator.get_error_context(error_type, user, custom_message)
        
        # Add request-specific context
        context.update({
            'requested_path': request.path,
            'can_retry': error_type in [ErrorType.SYSTEM_ERROR, ErrorType.SESSION_EXPIRED],
            'show_login_button': not (user and user.is_authenticated),
            'show_contact_admin': error_type in [ErrorType.NO_GROUPS, ErrorType.NO_ORGANIZATION, ErrorType.GROUP_ORG_MISMATCH],
        })
        
        # Return appropriate response
        if error_type == ErrorType.NO_AUTHENTICATION:
            # Redirect to login with next parameter
            login_url = reverse('login')
            next_url = request.get_full_path()
            return redirect(f"{login_url}?next={next_url}")
        else:
            # Show error page
            return render(request, 'errors/access_denied.html', context, status=403)
    
    @staticmethod
    def handle_system_error(request, error_message: str = None, 
                          exception: Exception = None) -> HttpResponse:
        """Handle system errors with logging"""
        user = request.user if hasattr(request, 'user') else None
        
        # Log the system error
        error_details = str(exception) if exception else error_message or "Unknown system error"
        SecurityEventLogger.log_security_violation(
            user=user,
            violation_type="system_error",
            details=error_details,
            request_path=request.path
        )
        
        # Generate error context
        context = ErrorMessageGenerator.get_error_context(ErrorType.SYSTEM_ERROR, user, error_message)
        
        return render(request, 'errors/system_error.html', context, status=500)
    
    @staticmethod
    def handle_permission_conflict(request, user: User, groups: List[str], 
                                 org_type: str, conflict_details: str) -> HttpResponse:
        """Handle permission conflicts between groups and organization"""
        # Log the conflict
        SecurityEventLogger.log_permission_conflict(user, groups, org_type, conflict_details)
        
        # Generate custom message
        custom_message = (
            f"Your group assignments ({', '.join(groups)}) don't match your organization type ({org_type}). "
            f"This has been logged for administrator review."
        )
        
        return AuthenticationErrorHandler.handle_access_denied(
            request, ErrorType.GROUP_ORG_MISMATCH, custom_message, log_event=False
        )
    
    @staticmethod
    def _get_client_ip(request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'


class UserGuidanceProvider:
    """Provides guidance for users with specific permission issues"""
    
    @staticmethod
    def get_guidance_for_user(user: User) -> Dict:
        """Get specific guidance based on user's current state"""
        guidance = {
            'primary_issue': None,
            'steps_to_resolve': [],
            'contact_info': {
                'admin_email': 'admin@carfinity.com',
                'support_email': 'support@carfinity.com',
                'phone': '1-800-CARFINITY'
            }
        }
        
        if not user.is_authenticated:
            guidance.update({
                'primary_issue': 'Not logged in',
                'steps_to_resolve': [
                    'Click the "Log In" button',
                    'Enter your username and password',
                    'If you forgot your password, use the "Forgot Password" link'
                ]
            })
            return guidance
        
        # Check user groups
        user_groups = list(user.groups.values_list('name', flat=True))
        if not user_groups:
            guidance.update({
                'primary_issue': 'No group assignment',
                'steps_to_resolve': [
                    'Contact your administrator to assign you to the appropriate group',
                    'Provide your username and the type of access you need',
                    'Wait for confirmation that your permissions have been updated'
                ]
            })
            return guidance
        
        # Check organization membership
        try:
            from organizations.models import OrganizationUser
            org_user = OrganizationUser.objects.filter(user=user, is_active=True).first()
            if not org_user:
                guidance.update({
                    'primary_issue': 'No organization assignment',
                    'steps_to_resolve': [
                        'Contact your administrator to assign you to an organization',
                        'Complete your profile setup if prompted',
                        'Verify your organization membership status'
                    ]
                })
                return guidance
        except ImportError:
            # Organization app not available
            pass
        
        # Default guidance for permission issues
        guidance.update({
            'primary_issue': 'Permission configuration',
            'steps_to_resolve': [
                'Contact your administrator to review your permissions',
                'Provide details about what you were trying to access',
                'Ask them to verify your group and organization assignments'
            ]
        })
        
        return guidance