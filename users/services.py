"""
Authentication and permission services for group-based authentication system.

This module provides centralized authentication and authorization logic that combines
Django groups with organization membership to determine user permissions and dashboard access.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationUser
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@dataclass
class UserPermissions:
    """Data class to hold user permission information"""
    user_id: int
    groups: List[str]
    organization: Optional[str]
    organization_type: Optional[str]
    available_dashboards: List[str]
    default_dashboard: Optional[str]
    has_conflicts: bool = False
    conflict_details: Optional[str] = None


@dataclass
class DashboardInfo:
    """Data class to hold dashboard information"""
    name: str
    url: str
    display_name: str
    required_groups: List[str]
    required_org_types: List[str]


class AuthenticationService:
    """
    Central service for handling user authentication and permission resolution.
    
    This service combines Django groups with organization membership to determine
    user permissions and appropriate dashboard access.
    """
    
    # Dashboard configuration
    DASHBOARDS = {
        'customer': DashboardInfo(
            name='customer',
            url='/dashboard/',
            display_name='Customer Dashboard',
            required_groups=['customers'],
            required_org_types=['fleet', 'dealership', 'other']
        ),
        'insurance': DashboardInfo(
            name='insurance',
            url='/insurance-dashboard/',
            display_name='Insurance Dashboard',
            required_groups=['Insurance Companies'],
            required_org_types=['insurance']
        )
    }
    
    # Permission matrix for group-organization combinations
    PERMISSION_MATRIX = {
        ('customers', 'fleet'): {
            'dashboards': ['customer'],
            'default_redirect': '/dashboard/',
            'priority': 1
        },
        ('customers', 'dealership'): {
            'dashboards': ['customer'],
            'default_redirect': '/dashboard/',
            'priority': 1
        },
        ('customers', 'other'): {
            'dashboards': ['customer'],
            'default_redirect': '/dashboard/',
            'priority': 1
        },
        ('Insurance Companies', 'insurance'): {
            'dashboards': ['insurance'],
            'default_redirect': '/insurance-dashboard/',
            'priority': 1
        },
        # Multi-access scenarios
        ('customers', 'insurance'): {
            'dashboards': ['customer', 'insurance'],
            'default_redirect': '/dashboard-selector/',
            'priority': 2
        }
    }

    @classmethod
    def get_user_permissions(cls, user: User) -> UserPermissions:
        """
        Get comprehensive permission information for a user using Authentication Group Management.
        
        Args:
            user: Django User instance
            
        Returns:
            UserPermissions object with all permission details
        """
        if not user or not user.is_authenticated:
            return UserPermissions(
                user_id=0,
                groups=[],
                organization=None,
                organization_type=None,
                available_dashboards=[],
                default_dashboard=None
            )
        
        # Get user groups
        user_groups = list(user.groups.values_list('name', flat=True))
        
        # Get user organization
        organization, org_type = cls._get_user_organization_info(user)
        
        # Resolve dashboard access using Authentication Group Management
        available_dashboards, default_dashboard, has_conflicts, conflict_details = cls._resolve_dashboard_access_dynamic(
            user, user_groups, org_type
        )
        
        return UserPermissions(
            user_id=user.id,
            groups=user_groups,
            organization=organization,
            organization_type=org_type,
            available_dashboards=available_dashboards,
            default_dashboard=default_dashboard,
            has_conflicts=has_conflicts,
            conflict_details=conflict_details
        )

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
        
        if permissions.default_dashboard:
            dashboard_info = cls.DASHBOARDS.get(permissions.default_dashboard)
            if dashboard_info:
                return dashboard_info.url
        
        # Fallback to first available dashboard
        first_dashboard = permissions.available_dashboards[0]
        dashboard_info = cls.DASHBOARDS.get(first_dashboard)
        return dashboard_info.url if dashboard_info else '/dashboard/'

    @classmethod
    def check_organization_access(cls, user: User, required_org_type: str) -> bool:
        """
        Check if user's organization matches the required type.
        
        Args:
            user: Django User instance
            required_org_type: Required organization type
            
        Returns:
            Boolean indicating if user has required organization access
        """
        return OrganizationService.validate_organization_type(user, required_org_type)

    @classmethod
    def _get_user_organization_info(cls, user: User) -> Tuple[Optional[str], Optional[str]]:
        """
        Get user's organization name and type.
        
        Args:
            user: Django User instance
            
        Returns:
            Tuple of (organization_name, organization_type)
        """
        try:
            organization = OrganizationService.get_user_organization(user)
            
            if organization:
                return organization.name, organization.organization_type
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting organization info for user {user.id}: {e}")
            return None, None

    @classmethod
    def _resolve_dashboard_access(cls, user_groups: List[str], org_type: Optional[str]) -> Tuple[List[str], Optional[str], bool, Optional[str]]:
        """
        Resolve dashboard access based on groups and organization type.
        
        Args:
            user_groups: List of user's group names
            org_type: User's organization type
            
        Returns:
            Tuple of (available_dashboards, default_dashboard, has_conflicts, conflict_details)
        """
        available_dashboards = []
        default_dashboard = None
        has_conflicts = False
        conflict_details = None
        
        if not user_groups:
            return [], None, True, "User has no group assignments"
        
        if not org_type:
            return [], None, True, "User has no organization assignment"
        
        # Check each group-organization combination
        for group in user_groups:
            permission_key = (group, org_type)
            
            if permission_key in cls.PERMISSION_MATRIX:
                matrix_entry = cls.PERMISSION_MATRIX[permission_key]
                dashboards = matrix_entry['dashboards']
                
                # Add dashboards to available list
                for dashboard in dashboards:
                    if dashboard not in available_dashboards:
                        available_dashboards.append(dashboard)
                
                # Set default dashboard based on priority
                if not default_dashboard or matrix_entry['priority'] == 1:
                    if len(dashboards) == 1:
                        default_dashboard = dashboards[0]
                    else:
                        # Multiple dashboards available, use selector
                        default_dashboard = 'selector'
            else:
                # Log potential group-organization mismatch
                has_conflicts = True
                conflict_details = f"Group '{group}' not compatible with organization type '{org_type}'"
                logger.warning(f"Group-organization mismatch: {conflict_details}")
        
        # If no valid combinations found, try to provide access based on organization type
        if not available_dashboards and org_type:
            fallback_dashboards = cls._get_fallback_dashboards_by_org_type(org_type)
            if fallback_dashboards:
                available_dashboards = fallback_dashboards
                default_dashboard = fallback_dashboards[0]
                has_conflicts = True
                conflict_details = f"Using organization-based fallback access for type '{org_type}'"
        
        return available_dashboards, default_dashboard, has_conflicts, conflict_details

    @classmethod
    def _resolve_dashboard_access_dynamic(cls, user: User, user_groups: List[str], org_type: Optional[str]) -> Tuple[List[str], Optional[str], bool, Optional[str]]:
        """
        Resolve dashboard access using Authentication Group Management configurations.
        
        Args:
            user: Django User instance
            user_groups: List of user's group names
            org_type: User's organization type
            
        Returns:
            Tuple of (available_dashboards, default_dashboard, has_conflicts, conflict_details)
        """
        from .models import AuthenticationGroup
        
        available_dashboards = []
        dashboard_configs = []
        has_conflicts = False
        conflict_details = None
        
        if not user_groups:
            return [], None, True, "User has no group assignments"
        
        # Get authentication group configurations for user's groups
        auth_groups = AuthenticationGroup.objects.filter(
            group__name__in=user_groups,
            is_active=True
        ).select_related('group').order_by('-priority')
        
        if not auth_groups.exists():
            return [], None, True, f"No dashboard configurations found for user groups: {', '.join(user_groups)}"
        
        # Check organization compatibility and collect dashboard configurations
        for auth_group in auth_groups:
            # Check organization type compatibility
            if org_type and auth_group.compatible_org_types:
                if org_type not in auth_group.compatible_org_types:
                    has_conflicts = True
                    if not conflict_details:
                        conflict_details = f"Group '{auth_group.group.name}' not compatible with organization type '{org_type}'"
                    continue
            
            # Add dashboard to available list
            dashboard_name = auth_group.dashboard_type
            if dashboard_name not in available_dashboards:
                available_dashboards.append(dashboard_name)
                dashboard_configs.append({
                    'name': dashboard_name,
                    'url': auth_group.dashboard_url,
                    'display_name': auth_group.display_name,
                    'priority': auth_group.priority,
                    'group': auth_group.group.name
                })
        
        # Determine default dashboard (highest priority)
        default_dashboard = None
        if dashboard_configs:
            # Sort by priority (highest first)
            dashboard_configs.sort(key=lambda x: x['priority'], reverse=True)
            default_dashboard = dashboard_configs[0]['name']
        
        # If no compatible dashboards found but user has groups, provide fallback
        if not available_dashboards and user_groups:
            has_conflicts = True
            conflict_details = f"No compatible dashboard configurations found for groups: {', '.join(user_groups)}"
            
            # Try fallback based on organization type
            if org_type:
                fallback_dashboards = cls._get_fallback_dashboards_by_org_type(org_type)
                if fallback_dashboards:
                    available_dashboards = fallback_dashboards
                    default_dashboard = fallback_dashboards[0]
                    conflict_details += f" Using organization-based fallback for '{org_type}'"
        
        return available_dashboards, default_dashboard, has_conflicts, conflict_details

    @classmethod
    def get_dashboard_info_from_auth_groups(cls, dashboard_name: str) -> Optional[Dict[str, str]]:
        """
        Get dashboard information from Authentication Group Management.
        
        Args:
            dashboard_name: Name of the dashboard
            
        Returns:
            Dictionary with dashboard information or None if not found
        """
        from .models import AuthenticationGroup
        
        try:
            auth_group = AuthenticationGroup.objects.filter(
                dashboard_type=dashboard_name,
                is_active=True
            ).first()
            
            if auth_group:
                return {
                    'name': auth_group.dashboard_type,
                    'url': auth_group.dashboard_url,
                    'display_name': auth_group.display_name,
                    'description': auth_group.description,
                    'required_groups': [auth_group.group.name],
                    'required_org_types': auth_group.compatible_org_types
                }
        except Exception as e:
            logger.error(f"Error getting dashboard info for {dashboard_name}: {str(e)}")
        
        return None

    @classmethod
    def _get_fallback_dashboards_by_org_type(cls, org_type: str) -> List[str]:
        """
        Get fallback dashboard access based on organization type.
        
        Args:
            org_type: Organization type
            
        Returns:
            List of dashboard names for fallback access
        """
        return OrganizationService.get_organization_dashboard_mapping(org_type)


class DashboardRouter:
    """
    Intelligent routing system for post-login redirects and dashboard access.
    
    This class handles complex routing logic including:
    - Multi-group user scenarios
    - Group-organization conflict resolution
    - Default dashboard determination
    - Dashboard switching functionality
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
        
        # Get user permissions to determine appropriate dashboard
        permissions = AuthenticationService.get_user_permissions(user)
        
        # Handle users with no dashboard access
        if not permissions.available_dashboards:
            logger.warning(f"User {user.id} has no available dashboards after login")
            return cls._handle_no_dashboard_access(user, permissions)
        
        # Handle users with single dashboard access
        if len(permissions.available_dashboards) == 1:
            dashboard_name = permissions.available_dashboards[0]
            dashboard_info = AuthenticationService.DASHBOARDS.get(dashboard_name)
            if dashboard_info:
                logger.info(f"User {user.id} redirected to single dashboard: {dashboard_name}")
                return dashboard_info.url
        
        # Handle users with multiple dashboard access
        return cls._handle_multi_dashboard_access(user, permissions)
    
    @classmethod
    def get_default_dashboard(cls, user: User) -> Optional[str]:
        """
        Get the default dashboard for a user based on their permissions.
        
        Args:
            user: Django User instance
            
        Returns:
            Dashboard name or None if no default available
        """
        permissions = AuthenticationService.get_user_permissions(user)
        
        if permissions.default_dashboard and permissions.default_dashboard != 'selector':
            return permissions.default_dashboard
        
        # If no specific default, return first available dashboard
        if permissions.available_dashboards:
            return permissions.available_dashboards[0]
        
        return None
    
    @classmethod
    def get_available_dashboards(cls, user: User) -> List[DashboardInfo]:
        """
        Get list of dashboards available to the user.
        
        Args:
            user: Django User instance
            
        Returns:
            List of DashboardInfo objects for available dashboards
        """
        permissions = AuthenticationService.get_user_permissions(user)
        available_dashboards = []
        
        for dashboard_name in permissions.available_dashboards:
            dashboard_info = AuthenticationService.DASHBOARDS.get(dashboard_name)
            if dashboard_info:
                available_dashboards.append(dashboard_info)
        
        return available_dashboards
    
    @classmethod
    def handle_multi_access_user(cls, user: User) -> str:
        """
        Handle routing for users with access to multiple dashboards.
        
        Args:
            user: Django User instance
            
        Returns:
            URL string for multi-access user routing
        """
        permissions = AuthenticationService.get_user_permissions(user)
        
        # If user has a clear default dashboard preference, use it
        if permissions.default_dashboard and permissions.default_dashboard != 'selector':
            dashboard_info = AuthenticationService.DASHBOARDS.get(permissions.default_dashboard)
            if dashboard_info:
                return dashboard_info.url
        
        # Otherwise, redirect to dashboard selector
        return '/dashboard-selector/'
    
    @classmethod
    def resolve_dashboard_conflicts(cls, user: User) -> Dict[str, any]:
        """
        Resolve conflicts between user groups and organization types.
        
        Args:
            user: Django User instance
            
        Returns:
            Dictionary with conflict resolution details
        """
        permissions = AuthenticationService.get_user_permissions(user)
        
        resolution = {
            'has_conflicts': permissions.has_conflicts,
            'conflict_details': permissions.conflict_details,
            'resolution_strategy': 'none',
            'recommended_action': None,
            'fallback_dashboard': None
        }
        
        if permissions.has_conflicts:
            # Determine resolution strategy based on conflict type
            if "no group assignments" in (permissions.conflict_details or "").lower():
                resolution.update({
                    'resolution_strategy': 'organization_fallback',
                    'recommended_action': 'Contact administrator to assign user groups',
                    'fallback_dashboard': cls._get_organization_fallback_dashboard(user)
                })
            elif "no organization assignment" in (permissions.conflict_details or "").lower():
                resolution.update({
                    'resolution_strategy': 'group_fallback',
                    'recommended_action': 'Complete organization profile setup',
                    'fallback_dashboard': cls._get_group_fallback_dashboard(user)
                })
            elif "not compatible" in (permissions.conflict_details or "").lower():
                resolution.update({
                    'resolution_strategy': 'organization_priority',
                    'recommended_action': 'Review user group assignments with administrator',
                    'fallback_dashboard': cls._get_organization_fallback_dashboard(user)
                })
            else:
                resolution.update({
                    'resolution_strategy': 'default_fallback',
                    'recommended_action': 'Contact administrator for permission review',
                    'fallback_dashboard': 'customer'  # Safe default
                })
        
        return resolution
    
    @classmethod
    def validate_dashboard_access(cls, user: User, dashboard_name: str) -> bool:
        """
        Validate if user has access to a specific dashboard.
        
        Args:
            user: Django User instance
            dashboard_name: Name of the dashboard to check
            
        Returns:
            Boolean indicating access permission
        """
        permissions = AuthenticationService.get_user_permissions(user)
        return dashboard_name in permissions.available_dashboards
    
    @classmethod
    def get_dashboard_switch_options(cls, user: User, current_dashboard: str) -> List[Dict[str, str]]:
        """
        Get available dashboard switching options for the current user.
        
        Args:
            user: Django User instance
            current_dashboard: Name of currently active dashboard
            
        Returns:
            List of dashboard options for switching
        """
        available_dashboards = cls.get_available_dashboards(user)
        switch_options = []
        
        for dashboard_info in available_dashboards:
            if dashboard_info.name != current_dashboard:
                switch_options.append({
                    'name': dashboard_info.name,
                    'display_name': dashboard_info.display_name,
                    'url': dashboard_info.url,
                    'description': f'Switch to {dashboard_info.display_name}'
                })
        
        return switch_options
    
    @classmethod
    def _handle_no_dashboard_access(cls, user: User, permissions: UserPermissions) -> str:
        """
        Handle users who have no dashboard access.
        
        Args:
            user: Django User instance
            permissions: UserPermissions object
            
        Returns:
            Appropriate redirect URL
        """
        # Log the access issue for administrator review
        logger.warning(
            f"User {user.id} ({user.username}) has no dashboard access. "
            f"Groups: {permissions.groups}, Org: {permissions.organization_type}, "
            f"Conflicts: {permissions.conflict_details}"
        )
        
        # Redirect to access denied page with specific context
        return '/access-denied/?reason=no_dashboard_access'
    
    @classmethod
    def _handle_multi_dashboard_access(cls, user: User, permissions: UserPermissions) -> str:
        """
        Handle users with access to multiple dashboards.
        
        Args:
            user: Django User instance
            permissions: UserPermissions object
            
        Returns:
            Appropriate redirect URL
        """
        # Check if user has a clear preference based on primary group/organization
        if permissions.default_dashboard and permissions.default_dashboard != 'selector':
            dashboard_info = AuthenticationService.DASHBOARDS.get(permissions.default_dashboard)
            if dashboard_info:
                logger.info(f"User {user.id} redirected to default dashboard: {permissions.default_dashboard}")
                return dashboard_info.url
        
        # Redirect to dashboard selector for user choice
        logger.info(f"User {user.id} redirected to dashboard selector (multiple access)")
        return '/dashboard-selector/'
    
    @classmethod
    def _get_organization_fallback_dashboard(cls, user: User) -> Optional[str]:
        """
        Get fallback dashboard based on user's organization type.
        
        Args:
            user: Django User instance
            
        Returns:
            Dashboard name or None
        """
        org_type = OrganizationService.get_user_organization_type(user)
        
        if not org_type:
            return None
        
        dashboards = OrganizationService.get_organization_dashboard_mapping(org_type)
        return dashboards[0] if dashboards else None
    
    @classmethod
    def _get_group_fallback_dashboard(cls, user: User) -> Optional[str]:
        """
        Get fallback dashboard based on user's groups.
        
        Args:
            user: Django User instance
            
        Returns:
            Dashboard name or None
        """
        user_groups = list(user.groups.values_list('name', flat=True))
        
        # Priority order: Insurance Companies > customers
        if 'Insurance Companies' in user_groups:
            return 'insurance'
        elif 'customers' in user_groups:
            return 'customer'
        
        return None
    
    @classmethod
    def _is_safe_redirect_url(cls, url: str) -> bool:
        """
        Check if a redirect URL is safe (prevents open redirect attacks).
        
        Args:
            url: URL to validate
            
        Returns:
            Boolean indicating if URL is safe
        """
        if not url:
            return False
        
        # Basic safety checks
        if url.startswith('//') or url.startswith('http://') or url.startswith('https://'):
            return False
        
        # Must start with / for relative URLs
        if not url.startswith('/'):
            return False
        
        return True
    
    @classmethod
    def _user_can_access_url(cls, user: User, url: str) -> bool:
        """
        Check if user has permission to access a specific URL.
        
        Args:
            user: Django User instance
            url: URL to check access for
            
        Returns:
            Boolean indicating access permission
        """
        # Get dynamic URL permissions from AuthenticationGroup configurations
        from .models import AuthenticationGroup
        
        url_permissions = {}
        auth_groups = AuthenticationGroup.get_active_auth_groups()
        
        for auth_group in auth_groups:
            dashboard_url = auth_group.dashboard_url
            group_name = auth_group.group.name
            
            if dashboard_url not in url_permissions:
                url_permissions[dashboard_url] = []
            url_permissions[dashboard_url].append(group_name)
        
        # Add dashboard selector for users with multiple groups
        if len(auth_groups) > 1:
            all_groups = [ag.group.name for ag in auth_groups]
            url_permissions['/dashboard-selector/'] = all_groups
        
        # Check if URL requires specific permissions
        for protected_url, required_groups in url_permissions.items():
            if url.startswith(protected_url):
                user_groups = list(user.groups.values_list('name', flat=True))
                return any(group in user_groups for group in required_groups)
        
        # If URL is not in protected list, allow access
        return True


class OrganizationService:
    """
    Service class to interface with organization app and provide organization-based access validation.
    
    This service handles:
    - Getting user organization information
    - Validating organization types
    - Organization-based access validation logic
    - Logging organization-group conflicts
    """
    
    @classmethod
    def get_user_organization(cls, user: User) -> Optional[Organization]:
        """
        Get user's active organization.
        
        Args:
            user: Django User instance
            
        Returns:
            Organization instance or None if user has no active organization
        """
        if not user or not user.is_authenticated:
            logger.debug(f"get_user_organization called with unauthenticated user")
            return None
        
        try:
            org_user = OrganizationUser.objects.select_related('organization').filter(
                user=user,
                is_active=True
            ).first()
            
            if org_user:
                logger.debug(f"User {user.id} belongs to organization: {org_user.organization.name}")
                return org_user.organization
            else:
                logger.warning(f"User {user.id} has no active organization membership")
                return None
                
        except Exception as e:
            logger.error(f"Error getting organization for user {user.id}: {e}")
            return None

    @classmethod
    def get_user_organization_type(cls, user: User) -> Optional[str]:
        """
        Get user's organization type.
        
        Args:
            user: Django User instance
            
        Returns:
            Organization type string or None if user has no organization
        """
        organization = cls.get_user_organization(user)
        if organization:
            logger.debug(f"User {user.id} organization type: {organization.organization_type}")
            return organization.organization_type
        
        logger.debug(f"User {user.id} has no organization type")
        return None

    @classmethod
    def validate_organization_type(cls, user: User, required_type: str) -> bool:
        """
        Validate if user's organization matches the required type.
        
        Args:
            user: Django User instance
            required_type: Required organization type
            
        Returns:
            Boolean indicating if user's organization matches required type
        """
        if not user or not user.is_authenticated:
            logger.debug(f"validate_organization_type called with unauthenticated user")
            return False
        
        user_org_type = cls.get_user_organization_type(user)
        
        if not user_org_type:
            logger.warning(f"User {user.id} has no organization type, cannot validate against '{required_type}'")
            return False
        
        is_valid = user_org_type == required_type
        
        if is_valid:
            logger.debug(f"User {user.id} organization type '{user_org_type}' matches required '{required_type}'")
        else:
            logger.info(f"User {user.id} organization type '{user_org_type}' does not match required '{required_type}'")
        
        return is_valid

    @classmethod
    def validate_user_organization_access(cls, user: User, required_org_types: List[str]) -> bool:
        """
        Validate if user's organization type is in the list of allowed types.
        
        Args:
            user: Django User instance
            required_org_types: List of allowed organization types
            
        Returns:
            Boolean indicating if user has valid organization access
        """
        if not user or not user.is_authenticated:
            logger.debug(f"validate_user_organization_access called with unauthenticated user")
            return False
        
        if not required_org_types:
            logger.debug(f"No required organization types specified, allowing access")
            return True
        
        user_org_type = cls.get_user_organization_type(user)
        
        if not user_org_type:
            logger.warning(f"User {user.id} has no organization type, cannot validate against {required_org_types}")
            return False
        
        is_valid = user_org_type in required_org_types
        
        if is_valid:
            logger.debug(f"User {user.id} organization type '{user_org_type}' is in allowed types {required_org_types}")
        else:
            logger.info(f"User {user.id} organization type '{user_org_type}' not in allowed types {required_org_types}")
        
        return is_valid

    @classmethod
    def get_user_organization_role(cls, user: User) -> Optional[str]:
        """
        Get user's role in their organization.
        
        Args:
            user: Django User instance
            
        Returns:
            Role string or None if user has no organization role
        """
        if not user or not user.is_authenticated:
            logger.debug(f"get_user_organization_role called with unauthenticated user")
            return None
        
        try:
            org_user = OrganizationUser.objects.filter(
                user=user,
                is_active=True
            ).first()
            
            if org_user:
                logger.debug(f"User {user.id} has role '{org_user.role}' in organization")
                return org_user.role
            else:
                logger.debug(f"User {user.id} has no organization role")
                return None
                
        except Exception as e:
            logger.error(f"Error getting organization role for user {user.id}: {e}")
            return None

    @classmethod
    def check_group_organization_compatibility(cls, user: User) -> Dict[str, any]:
        """
        Check compatibility between user's groups and organization type.
        
        Args:
            user: Django User instance
            
        Returns:
            Dictionary with compatibility information and conflict details
        """
        if not user or not user.is_authenticated:
            return {
                'is_compatible': False,
                'conflicts': ['User not authenticated'],
                'recommendations': ['User must be authenticated']
            }
        
        user_groups = list(user.groups.values_list('name', flat=True))
        user_org_type = cls.get_user_organization_type(user)
        
        compatibility_result = {
            'is_compatible': True,
            'conflicts': [],
            'recommendations': [],
            'user_groups': user_groups,
            'organization_type': user_org_type,
            'valid_combinations': []
        }
        
        # Check if user has groups
        if not user_groups:
            compatibility_result['is_compatible'] = False
            compatibility_result['conflicts'].append('User has no group assignments')
            compatibility_result['recommendations'].append('Contact administrator to assign appropriate user groups')
            cls._log_organization_group_conflict(user, 'no_groups', user_groups, user_org_type)
        
        # Check if user has organization
        if not user_org_type:
            compatibility_result['is_compatible'] = False
            compatibility_result['conflicts'].append('User has no organization assignment')
            compatibility_result['recommendations'].append('Complete organization profile setup')
            cls._log_organization_group_conflict(user, 'no_organization', user_groups, user_org_type)
        
        # If both groups and organization exist, check compatibility
        if user_groups and user_org_type:
            valid_combinations = []
            invalid_combinations = []
            
            for group in user_groups:
                permission_key = (group, user_org_type)
                
                if permission_key in AuthenticationService.PERMISSION_MATRIX:
                    valid_combinations.append(permission_key)
                    logger.debug(f"Valid combination found for user {user.id}: {permission_key}")
                else:
                    invalid_combinations.append(permission_key)
                    logger.info(f"Invalid combination for user {user.id}: {permission_key}")
            
            compatibility_result['valid_combinations'] = valid_combinations
            
            # If no valid combinations found, mark as incompatible
            if not valid_combinations:
                compatibility_result['is_compatible'] = False
                compatibility_result['conflicts'].append(
                    f"No valid combinations found between groups {user_groups} and organization type '{user_org_type}'"
                )
                compatibility_result['recommendations'].append(
                    'Review user group assignments or organization type with administrator'
                )
                cls._log_organization_group_conflict(user, 'incompatible_combination', user_groups, user_org_type)
            
            # If some combinations are invalid, log warnings but don't mark as incompatible
            elif invalid_combinations:
                compatibility_result['conflicts'].append(
                    f"Some group-organization combinations are invalid: {invalid_combinations}"
                )
                compatibility_result['recommendations'].append(
                    'Consider reviewing group assignments for optimal access'
                )
                cls._log_organization_group_conflict(user, 'partial_incompatibility', user_groups, user_org_type)
        
        return compatibility_result

    @classmethod
    def get_organization_dashboard_mapping(cls, org_type: str) -> List[str]:
        """
        Get available dashboards for a specific organization type using configurable authentication groups.
        
        Args:
            org_type: Organization type
            
        Returns:
            List of dashboard names available for the organization type
        """
        from .models import AuthenticationGroup
        
        dashboards = []
        auth_groups = AuthenticationGroup.get_active_auth_groups()
        
        for auth_group in auth_groups:
            if org_type in auth_group.compatible_org_types:
                dashboards.append(auth_group.dashboard_type)
        
        # Fallback to default mapping if no configured groups found
        if not dashboards:
            default_mapping = {
                'insurance': ['insurance'],
                'fleet': ['customer'],
                'dealership': ['customer'],
                'service': ['customer'],
                'other': ['customer']
            }
            dashboards = default_mapping.get(org_type, ['customer'])
        
        logger.debug(f"Organization type '{org_type}' maps to dashboards: {dashboards}")
        return dashboards

    @classmethod
    def get_organization_required_groups(cls, org_type: str) -> List[str]:
        """
        Get recommended groups for a specific organization type using configurable authentication groups.
        
        Args:
            org_type: Organization type
            
        Returns:
            List of group names recommended for the organization type
        """
        from .models import AuthenticationGroup
        
        groups = AuthenticationGroup.get_recommended_groups_for_org_type(org_type)
        
        # Fallback to default mapping if no configured groups found
        if not groups:
            default_mapping = {
                'insurance': ['Insurance Companies'],
                'fleet': ['customers'],
                'dealership': ['customers'],
                'service': ['customers'],
                'other': ['customers']
            }
            groups = default_mapping.get(org_type, ['customers'])
        
        logger.debug(f"Organization type '{org_type}' should have groups: {groups}")
        return groups

    @classmethod
    def validate_organization_exists(cls, organization_id: int) -> bool:
        """
        Validate if an organization exists and is active.
        
        Args:
            organization_id: ID of the organization to validate
            
        Returns:
            Boolean indicating if organization exists
        """
        try:
            organization = Organization.objects.get(id=organization_id)
            logger.debug(f"Organization {organization_id} exists: {organization.name}")
            return True
        except Organization.DoesNotExist:
            logger.warning(f"Organization {organization_id} does not exist")
            return False
        except Exception as e:
            logger.error(f"Error validating organization {organization_id}: {e}")
            return False

    @classmethod
    def get_organization_members(cls, organization: Organization, active_only: bool = True) -> List[User]:
        """
        Get all members of an organization.
        
        Args:
            organization: Organization instance
            active_only: Whether to return only active members
            
        Returns:
            List of User instances who are members of the organization
        """
        try:
            query = OrganizationUser.objects.select_related('user').filter(
                organization=organization
            )
            
            if active_only:
                query = query.filter(is_active=True)
            
            members = [org_user.user for org_user in query]
            logger.debug(f"Organization {organization.name} has {len(members)} {'active ' if active_only else ''}members")
            
            return members
            
        except Exception as e:
            logger.error(f"Error getting members for organization {organization.id}: {e}")
            return []

    @classmethod
    def sync_organization_groups(cls, organization: Organization) -> Dict[str, int]:
        """
        Sync all organization members to the organization's linked groups.
        
        Args:
            organization: Organization instance
            
        Returns:
            Dictionary with sync statistics
        """
        try:
            active_members = cls.get_organization_members(organization, active_only=True)
            linked_groups = organization.linked_groups.all()
            
            sync_stats = {
                'members_processed': 0,
                'groups_added': 0,
                'groups_removed': 0,
                'errors': 0
            }
            
            for member in active_members:
                try:
                    # Add user to all linked groups
                    for group in linked_groups:
                        if not member.groups.filter(id=group.id).exists():
                            member.groups.add(group)
                            sync_stats['groups_added'] += 1
                            logger.debug(f"Added user {member.id} to group {group.name}")
                    
                    sync_stats['members_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing groups for user {member.id}: {e}")
                    sync_stats['errors'] += 1
            
            logger.info(f"Organization {organization.name} group sync completed: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"Error syncing organization groups for {organization.id}: {e}")
            return {'members_processed': 0, 'groups_added': 0, 'groups_removed': 0, 'errors': 1}

    @classmethod
    def _log_organization_group_conflict(cls, user: User, conflict_type: str, user_groups: List[str], org_type: Optional[str]):
        """
        Log organization-group conflicts for administrator review.
        
        Args:
            user: Django User instance
            conflict_type: Type of conflict detected
            user_groups: User's current groups
            org_type: User's organization type
        """
        conflict_details = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'conflict_type': conflict_type,
            'user_groups': user_groups,
            'organization_type': org_type,
            'timestamp': logger.handlers[0].format(logger.makeRecord(
                logger.name, logging.INFO, __file__, 0, '', (), None
            )) if logger.handlers else 'N/A'
        }
        
        conflict_messages = {
            'no_groups': f"User {user.id} ({user.username}) has no group assignments but belongs to organization type '{org_type}'",
            'no_organization': f"User {user.id} ({user.username}) has groups {user_groups} but no organization assignment",
            'incompatible_combination': f"User {user.id} ({user.username}) has incompatible group-organization combination: groups {user_groups}, org type '{org_type}'",
            'partial_incompatibility': f"User {user.id} ({user.username}) has some incompatible group-organization combinations: groups {user_groups}, org type '{org_type}'"
        }
        
        message = conflict_messages.get(conflict_type, f"Unknown conflict type '{conflict_type}' for user {user.id}")
        
        # Log at appropriate level based on conflict severity
        if conflict_type in ['no_groups', 'no_organization', 'incompatible_combination']:
            logger.warning(f"ORGANIZATION-GROUP CONFLICT: {message}")
        else:
            logger.info(f"ORGANIZATION-GROUP NOTICE: {message}")
        
        # Additional structured logging for monitoring systems
        logger.info(f"CONFLICT_DETAILS: {conflict_details}")


class PermissionUtils:
    """
    Utility functions for checking user groups and organization membership.
    """
    
    @staticmethod
    def user_has_group(user: User, group_name: str) -> bool:
        """
        Check if user belongs to a specific group.
        
        Args:
            user: Django User instance
            group_name: Name of the group to check
            
        Returns:
            Boolean indicating group membership
        """
        if not user or not user.is_authenticated:
            return False
        
        return user.groups.filter(name=group_name).exists()

    @staticmethod
    def user_has_any_group(user: User, group_names: List[str]) -> bool:
        """
        Check if user belongs to any of the specified groups.
        
        Args:
            user: Django User instance
            group_names: List of group names to check
            
        Returns:
            Boolean indicating membership in any of the groups
        """
        if not user or not user.is_authenticated:
            return False
        
        return user.groups.filter(name__in=group_names).exists()

    @staticmethod
    def user_has_all_groups(user: User, group_names: List[str]) -> bool:
        """
        Check if user belongs to all of the specified groups.
        
        Args:
            user: Django User instance
            group_names: List of group names to check
            
        Returns:
            Boolean indicating membership in all groups
        """
        if not user or not user.is_authenticated:
            return False
        
        user_groups = set(user.groups.values_list('name', flat=True))
        required_groups = set(group_names)
        
        return required_groups.issubset(user_groups)

    @staticmethod
    def get_user_organization(user: User) -> Optional[Organization]:
        """
        Get user's active organization.
        
        Args:
            user: Django User instance
            
        Returns:
            Organization instance or None
        """
        return OrganizationService.get_user_organization(user)

    @staticmethod
    def user_belongs_to_organization_type(user: User, org_type: str) -> bool:
        """
        Check if user belongs to an organization of specific type.
        
        Args:
            user: Django User instance
            org_type: Organization type to check
            
        Returns:
            Boolean indicating organization type membership
        """
        return OrganizationService.validate_organization_type(user, org_type)

    @staticmethod
    def get_user_organization_role(user: User) -> Optional[str]:
        """
        Get user's role in their organization.
        
        Args:
            user: Django User instance
            
        Returns:
            Role string or None
        """
        return OrganizationService.get_user_organization_role(user)

    @staticmethod
    def validate_group_organization_compatibility(group_name: str, org_type: str) -> bool:
        """
        Validate if a group is compatible with an organization type.
        
        Args:
            group_name: Name of the group
            org_type: Organization type
            
        Returns:
            Boolean indicating compatibility
        """
        permission_key = (group_name, org_type)
        return permission_key in AuthenticationService.PERMISSION_MATRIX