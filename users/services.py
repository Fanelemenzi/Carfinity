"""
Simplified authentication and permission services for 3-group system.

This module provides centralized authentication and authorization logic using
only 3 groups: Staff, AutoCare, AutoAssess (no organization-based authentication).
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@dataclass
class UserPermissions:
    """Data class to hold simplified user permission information"""
    user_id: int
    groups: List[str]
    available_dashboards: List[str]
    default_dashboard: Optional[str]
    has_access: bool = True


@dataclass
class DashboardInfo:
    """Data class to hold dashboard information"""
    name: str
    url: str
    display_name: str
    required_groups: List[str]


class AuthenticationService:
    """
    Simplified authentication service for 3-group system.
    
    This service handles authentication using only 3 groups:
    - Staff: Administrative access
    - AutoCare: Vehicle maintenance and care access
    - AutoAssess: Vehicle assessment and inspection access
    """
    
    # Dashboard configuration for 3 groups
    DASHBOARDS = {
        'staff': DashboardInfo(
            name='staff',
            url='/admin/',
            display_name='Staff Dashboard',
            required_groups=['Staff']
        ),
        'autocare': DashboardInfo(
            name='autocare',
            url='/notifications/dashboard/',
            display_name='AutoCare Dashboard',
            required_groups=['AutoCare']
        ),
        'autoassess': DashboardInfo(
            name='autoassess',
            url='/insurance/',
            display_name='AutoAssess Dashboard',
            required_groups=['AutoAssess']
        )
    }
    
    # Group priority mapping (higher number = higher priority)
    GROUP_PRIORITY = {
        'Staff': 3,
        'AutoAssess': 2,
        'AutoCare': 1
    }

    @classmethod
    def get_user_permissions(cls, user: User) -> UserPermissions:
        """
        Get simplified permission information for a user based on 3-group system.
        
        Args:
            user: Django User instance
            
        Returns:
            UserPermissions object with permission details
        """
        logger.info(f"Getting permissions for user: {user.id if user else 'None'} ({user.username if user else 'N/A'})")
        
        if not user or not user.is_authenticated:
            logger.warning(f"User permission check failed - user: {user}, authenticated: {user.is_authenticated if user else 'N/A'}")
            return UserPermissions(
                user_id=0,
                groups=[],
                available_dashboards=[],
                default_dashboard=None,
                has_access=False
            )
        
        # Get user groups with detailed logging
        try:
            user_groups = list(user.groups.values_list('name', flat=True))
            logger.info(f"User {user.id} groups from database: {user_groups}")
        except Exception as e:
            logger.error(f"Error getting user groups for user {user.id}: {str(e)}")
            user_groups = []
        
        # Resolve dashboard access based on groups only
        available_dashboards, default_dashboard = cls._resolve_dashboard_access(user_groups)
        
        permissions = UserPermissions(
            user_id=user.id,
            groups=user_groups,
            available_dashboards=available_dashboards,
            default_dashboard=default_dashboard,
            has_access=len(available_dashboards) > 0
        )
        
        logger.info(f"Final permissions for user {user.id}: {permissions}")
        return permissions

    @classmethod
    def resolve_dashboard_access(cls, user: User) -> List[str]:
        """
        Determine which dashboards a user can access.
        
        Args:
            user: Django User instance
            
        Returns:
            List of dashboard names the user can access
        """
        permissions = cls.get_user_permissions(user)
        return permissions.available_dashboards

    @classmethod
    def get_redirect_url_after_login(cls, user: User) -> str:
        """
        Get the appropriate redirect URL after successful login.
        
        Args:
            user: Django User instance
            
        Returns:
            URL string for post-login redirect
        """
        permissions = cls.get_user_permissions(user)
        
        if not permissions.available_dashboards:
            logger.warning(f"User {user.id} has no available dashboards")
            return '/access-denied/'
        
        # If user has multiple dashboards, redirect to dashboard selector
        if len(permissions.available_dashboards) > 1:
            logger.info(f"User {user.id} has multiple dashboards, redirecting to selector")
            return '/dashboard-selector/'
        
        # If user has only one dashboard, redirect directly to it
        if permissions.default_dashboard:
            dashboard_info = cls.DASHBOARDS.get(permissions.default_dashboard)
            if dashboard_info:
                return dashboard_info.url
        
        # Fallback to first available dashboard
        first_dashboard = permissions.available_dashboards[0]
        dashboard_info = cls.DASHBOARDS.get(first_dashboard)
        return dashboard_info.url if dashboard_info else '/dashboard/'

    @classmethod
    def check_group_access(cls, user: User, required_group: str) -> bool:
        """
        Check if user belongs to the required group.
        
        Args:
            user: Django User instance
            required_group: Required group name (Staff, AutoCare, or AutoAssess)
            
        Returns:
            Boolean indicating if user has required group access
        """
        if not user or not user.is_authenticated:
            logger.warning(f"User check failed - user: {user}, authenticated: {user.is_authenticated if user else 'N/A'}")
            return False
        
        try:
            # Add more robust checking with logging
            result = user.groups.filter(name=required_group).exists()
            logger.info(f"Group access check - User: {user.id} ({user.username}), Group: {required_group}, Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error checking group access for user {user.id}, group {required_group}: {str(e)}")
            return False

    @classmethod
    def _resolve_dashboard_access(cls, user_groups: List[str]) -> Tuple[List[str], Optional[str]]:
        """
        Resolve dashboard access based on user groups only.
        
        Args:
            user_groups: List of user's group names
            
        Returns:
            Tuple of (available_dashboards, default_dashboard)
        """
        available_dashboards = []
        default_dashboard = None
        highest_priority = 0
        
        logger.info(f"Resolving dashboard access for groups: {user_groups}")
        
        # Check each group for dashboard access with explicit mapping
        for group in user_groups:
            logger.info(f"Processing group: {group}")
            
            if group == 'AutoCare':
                available_dashboards.append('autocare')
                logger.info(f"Added 'autocare' dashboard for AutoCare group")
                
                # Set default dashboard based on group priority
                group_priority = cls.GROUP_PRIORITY.get(group, 0)
                logger.info(f"AutoCare group priority: {group_priority}, highest so far: {highest_priority}")
                
                if group_priority > highest_priority:
                    highest_priority = group_priority
                    default_dashboard = 'autocare'
                    logger.info(f"Set default dashboard to 'autocare'")
                    
            elif group == 'AutoAssess':
                available_dashboards.append('autoassess')
                logger.info(f"Added 'autoassess' dashboard for AutoAssess group")
                
                group_priority = cls.GROUP_PRIORITY.get(group, 0)
                if group_priority > highest_priority:
                    highest_priority = group_priority
                    default_dashboard = 'autoassess'
                    logger.info(f"Set default dashboard to 'autoassess'")
                    
            elif group == 'Staff':
                available_dashboards.append('staff')
                logger.info(f"Added 'staff' dashboard for Staff group")
                
                group_priority = cls.GROUP_PRIORITY.get(group, 0)
                if group_priority > highest_priority:
                    highest_priority = group_priority
                    default_dashboard = 'staff'
                    logger.info(f"Set default dashboard to 'staff'")
        
        logger.info(f"Final dashboard access - Available: {available_dashboards}, Default: {default_dashboard}")
        return list(set(available_dashboards)), default_dashboard


class DashboardRouter:
    """
    Simplified routing system for post-login redirects and dashboard access.
    """
    
    @classmethod
    def get_post_login_redirect(cls, user: User, next_url: Optional[str] = None) -> str:
        """
        Get the appropriate redirect URL after successful login.
        
        Args:
            user: Django User instance
            next_url: Optional next URL from login form
            
        Returns:
            URL string for post-login redirect
        """
        if not user or not user.is_authenticated:
            return '/login/'
        
        # If there's a specific next URL requested, validate and use it
        if next_url and cls._is_safe_redirect_url(next_url):
            # Check if user has permission to access the requested URL
            if cls._user_can_access_url(user, next_url):
                return next_url
        
        # Use AuthenticationService to get redirect URL
        return AuthenticationService.get_redirect_url_after_login(user)
    
    @classmethod
    def get_default_dashboard(cls, user: User) -> Optional[str]:
        """
        Get the default dashboard for a user based on their permissions.
        
        Args:
            user: Django User instance
            
        Returns:
            Default dashboard name or None
        """
        permissions = AuthenticationService.get_user_permissions(user)
        return permissions.default_dashboard
    
    @classmethod
    def _is_safe_redirect_url(cls, url: str) -> bool:
        """
        Check if the redirect URL is safe (no external redirects).
        
        Args:
            url: URL to check
            
        Returns:
            Boolean indicating if URL is safe
        """
        if not url:
            return False
        
        # Basic safety check - must start with / and not be a protocol
        return url.startswith('/') and not url.startswith('//')
    
    @classmethod
    def _user_can_access_url(cls, user: User, url: str) -> bool:
        """
        Check if user has permission to access the given URL.
        
        Args:
            user: Django User instance
            url: URL to check access for
            
        Returns:
            Boolean indicating if user can access URL
        """
        # Basic implementation - can be extended with more sophisticated URL permission checking
        permissions = AuthenticationService.get_user_permissions(user)
        
        # Check if URL matches any of the user's available dashboards
        for dashboard_name in permissions.available_dashboards:
            dashboard_info = AuthenticationService.DASHBOARDS.get(dashboard_name)
            if dashboard_info and url.startswith(dashboard_info.url):
                return True
        
        # Allow access to common URLs
        common_urls = ['/profile/', '/logout/', '/api/']
        for common_url in common_urls:
            if url.startswith(common_url):
                return True
        
        return False


# Utility functions for template and view usage
def user_has_group(user: User, group_name: str) -> bool:
    """
    Template-friendly function to check if user has a specific group.
    
    Args:
        user: Django User instance
        group_name: Name of the group to check
        
    Returns:
        Boolean indicating if user has the group
    """
    return AuthenticationService.check_group_access(user, group_name)


def get_user_dashboard_url(user: User) -> str:
    """
    Get the appropriate dashboard URL for a user.
    
    Args:
        user: Django User instance
        
    Returns:
        Dashboard URL string
    """
    return AuthenticationService.get_redirect_url_after_login(user)


def get_available_dashboards(user: User) -> List[Dict[str, str]]:
    """
    Get list of available dashboards for a user with their info.
    
    Args:
        user: Django User instance
        
    Returns:
        List of dashboard info dictionaries
    """
    permissions = AuthenticationService.get_user_permissions(user)
    dashboards = []
    
    for dashboard_name in permissions.available_dashboards:
        dashboard_info = AuthenticationService.DASHBOARDS.get(dashboard_name)
        if dashboard_info:
            dashboards.append({
                'name': dashboard_info.name,
                'url': dashboard_info.url,
                'display_name': dashboard_info.display_name,
                'is_default': dashboard_name == permissions.default_dashboard
            })
    
    return dashboards
