"""
Permission decorators and utilities for group-based authentication system.

This module provides decorators and utility functions for view-level access control
that integrates with the AuthenticationService.
"""

from functools import wraps
from typing import List, Union, Callable, Any
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from .services import AuthenticationService, PermissionUtils
from .error_handlers import AuthenticationErrorHandler, ErrorType, SecurityEventLogger
import logging

logger = logging.getLogger(__name__)


def require_group(group_name: str):
    """
    Decorator to require user to be in a specific group.
    
    Args:
        group_name: Name of the required group
        
    Returns:
        Decorator function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not PermissionUtils.user_has_group(request.user, group_name):
                # Log the access denial
                SecurityEventLogger.log_access_denied(
                    user=request.user,
                    requested_resource=f"{view_func.__module__}.{view_func.__name__}",
                    error_type=ErrorType.ACCESS_DENIED,
                    additional_info={'required_group': group_name}
                )
                
                # Use error handler for consistent response
                custom_message = f"You need to be in the '{group_name}' group to access this page."
                return AuthenticationErrorHandler.handle_access_denied(
                    request, ErrorType.ACCESS_DENIED, custom_message
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_group(group_names: List[str]):
    """
    Decorator to require user to be in any of the specified groups.
    
    Args:
        group_names: List of group names (user needs to be in at least one)
        
    Returns:
        Decorator function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not PermissionUtils.user_has_any_group(request.user, group_names):
                # Log the access denial
                SecurityEventLogger.log_access_denied(
                    user=request.user,
                    requested_resource=f"{view_func.__module__}.{view_func.__name__}",
                    error_type=ErrorType.ACCESS_DENIED,
                    additional_info={'required_groups': group_names}
                )
                
                # Use error handler for consistent response
                custom_message = f"You need to be in one of these groups: {', '.join(group_names)}"
                return AuthenticationErrorHandler.handle_access_denied(
                    request, ErrorType.ACCESS_DENIED, custom_message
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_all_groups(group_names: List[str]):
    """
    Decorator to require user to be in all of the specified groups.
    
    Args:
        group_names: List of group names (user needs to be in all)
        
    Returns:
        Decorator function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not PermissionUtils.user_has_all_groups(request.user, group_names):
                logger.warning(f"User {request.user.id} denied access to {view_func.__name__} - missing some of groups: {group_names}")
                messages.error(request, f"Access denied. You need to be in all of these groups: {', '.join(group_names)}")
                return redirect('access_denied')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_organization_type(org_type: str):
    """
    Decorator to require user to belong to an organization of specific type.
    
    Args:
        org_type: Required organization type
        
    Returns:
        Decorator function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not PermissionUtils.user_belongs_to_organization_type(request.user, org_type):
                # Check if user has no organization at all
                permissions = AuthenticationService.get_user_permissions(request.user)
                
                if not permissions.organization:
                    # User has no organization assignment
                    return AuthenticationErrorHandler.handle_access_denied(
                        request, ErrorType.NO_ORGANIZATION
                    )
                else:
                    # User has wrong organization type
                    SecurityEventLogger.log_access_denied(
                        user=request.user,
                        requested_resource=f"{view_func.__module__}.{view_func.__name__}",
                        error_type=ErrorType.ACCESS_DENIED,
                        additional_info={
                            'required_org_type': org_type,
                            'user_org_type': permissions.organization_type
                        }
                    )
                    
                    custom_message = f"You need to belong to a '{org_type}' organization to access this page."
                    return AuthenticationErrorHandler.handle_access_denied(
                        request, ErrorType.ACCESS_DENIED, custom_message
                    )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_dashboard_access(dashboard_name: str):
    """
    Decorator to require user to have access to a specific dashboard.
    
    Args:
        dashboard_name: Name of the required dashboard
        
    Returns:
        Decorator function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            available_dashboards = AuthenticationService.resolve_dashboard_access(request.user)
            
            if dashboard_name not in available_dashboards:
                logger.warning(f"User {request.user.id} denied access to {view_func.__name__} - no access to dashboard: {dashboard_name}")
                messages.error(request, f"Access denied. You don't have access to the {dashboard_name} dashboard.")
                return redirect('access_denied')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_permission_conflicts(view_func: Callable) -> Callable:
    """
    Decorator to check and log permission conflicts for a user.
    
    This decorator logs warnings when users have group-organization mismatches
    but still allows access if they have valid permissions.
    
    Args:
        view_func: View function to wrap
        
    Returns:
        Decorated view function
    """
    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        permissions = AuthenticationService.get_user_permissions(request.user)
        
        if permissions.has_conflicts:
            # Use the new logging system
            SecurityEventLogger.log_permission_conflict(
                user=request.user,
                groups=permissions.groups,
                org_type=permissions.organization_type or 'None',
                conflict_details=permissions.conflict_details or 'Unknown conflict'
            )
            
            # Add a message to inform the user but don't block access
            messages.warning(request, "Your account has some permission conflicts. Please contact an administrator if you experience issues.")
        
        return view_func(request, *args, **kwargs)
    return wrapper


class PermissionChecker:
    """
    Context manager and utility class for checking permissions in views.
    """
    
    def __init__(self, user: User):
        self.user = user
        self.permissions = AuthenticationService.get_user_permissions(user)
    
    def has_group(self, group_name: str) -> bool:
        """Check if user has specific group."""
        return group_name in self.permissions.groups
    
    def has_any_group(self, group_names: List[str]) -> bool:
        """Check if user has any of the specified groups."""
        return any(group in self.permissions.groups for group in group_names)
    
    def has_all_groups(self, group_names: List[str]) -> bool:
        """Check if user has all of the specified groups."""
        return all(group in self.permissions.groups for group in group_names)
    
    def has_organization_type(self, org_type: str) -> bool:
        """Check if user belongs to organization of specific type."""
        return self.permissions.organization_type == org_type
    
    def has_dashboard_access(self, dashboard_name: str) -> bool:
        """Check if user has access to specific dashboard."""
        return dashboard_name in self.permissions.available_dashboards
    
    def get_available_dashboards(self) -> List[str]:
        """Get list of dashboards user can access."""
        return self.permissions.available_dashboards
    
    def get_default_dashboard(self) -> str:
        """Get user's default dashboard."""
        return self.permissions.default_dashboard or ''
    
    def has_conflicts(self) -> bool:
        """Check if user has permission conflicts."""
        return self.permissions.has_conflicts
    
    def get_conflict_details(self) -> str:
        """Get details about permission conflicts."""
        return self.permissions.conflict_details or ''


def get_permission_checker(user: User) -> PermissionChecker:
    """
    Factory function to create a PermissionChecker instance.
    
    Args:
        user: Django User instance
        
    Returns:
        PermissionChecker instance
    """
    return PermissionChecker(user)