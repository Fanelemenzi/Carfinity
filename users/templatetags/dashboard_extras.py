"""
Template tags for dashboard navigation and user experience features.

This module provides template tags that integrate with the authentication system
to provide conditional navigation and dashboard switching functionality.
"""

from django import template
from django.contrib.auth.models import User
from ..services import AuthenticationService, DashboardRouter
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=False)
def get_user_dashboard_access(user):
    """
    Template tag to get user's dashboard access information.
    
    Args:
        user: Django User instance
        
    Returns:
        Dictionary with user's dashboard access information
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return {
            'user': user,
            'available_dashboards': [],
            'user_groups': [],
            'organization': None,
            'organization_type': None,
            'has_conflicts': False,
            'default_dashboard': None
        }
    
    try:
        permissions = AuthenticationService.get_user_permissions(user)
        
        return {
            'user': user,
            'available_dashboards': permissions.available_dashboards,
            'user_groups': permissions.groups,
            'organization': permissions.organization,
            'organization_type': permissions.organization_type,
            'has_conflicts': permissions.has_conflicts,
            'conflict_details': permissions.conflict_details,
            'default_dashboard': permissions.default_dashboard
        }
    except Exception as e:
        logger.error(f"Error getting dashboard access for user {user.id}: {str(e)}")
        return {
            'user': user,
            'available_dashboards': [],
            'user_groups': [],
            'organization': None,
            'organization_type': None,
            'has_conflicts': True,
            'conflict_details': 'Error loading dashboard access',
            'default_dashboard': None
        }


@register.simple_tag
def get_dashboard_switch_options(user, current_dashboard):
    """
    Template tag to get dashboard switching options for the current user.
    
    Args:
        user: Django User instance
        current_dashboard: Name of currently active dashboard
        
    Returns:
        List of dashboard options for switching
    """
    if not user or not user.is_authenticated:
        return []
    
    try:
        return DashboardRouter.get_dashboard_switch_options(user, current_dashboard)
    except Exception as e:
        logger.error(f"Error getting dashboard switch options for user {user.id}: {str(e)}")
        return []


@register.simple_tag
def can_access_dashboard(user, dashboard_name):
    """
    Template tag to check if user can access a specific dashboard.
    
    Args:
        user: Django User instance
        dashboard_name: Name of the dashboard to check
        
    Returns:
        Boolean indicating access permission
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        return DashboardRouter.validate_dashboard_access(user, dashboard_name)
    except Exception as e:
        logger.error(f"Error checking dashboard access for user {user.id}, dashboard {dashboard_name}: {str(e)}")
        return False


@register.simple_tag
def get_user_default_dashboard(user):
    """
    Template tag to get user's default dashboard.
    
    Args:
        user: Django User instance
        
    Returns:
        Default dashboard name or empty string
    """
    if not user or not user.is_authenticated:
        return ''
    
    try:
        return DashboardRouter.get_default_dashboard(user) or ''
    except Exception as e:
        logger.error(f"Error getting default dashboard for user {user.id}: {str(e)}")
        return ''


@register.filter
def has_group(user, group_name):
    """
    Template filter to check if user belongs to a specific group.
    
    Args:
        user: Django User instance
        group_name: Name of the group to check
        
    Returns:
        Boolean indicating group membership
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.groups.filter(name=group_name).exists()


@register.filter
def has_any_group(user, group_names):
    """
    Template filter to check if user belongs to any of the specified groups.
    
    Args:
        user: Django User instance
        group_names: Comma-separated list of group names
        
    Returns:
        Boolean indicating membership in any of the groups
    """
    if not user or not user.is_authenticated:
        return False
    
    group_list = [name.strip() for name in group_names.split(',')]
    return user.groups.filter(name__in=group_list).exists()


@register.inclusion_tag('dashboard/navigation_context.html', takes_context=True)
def get_navigation_context(context):
    """
    Template tag to get comprehensive navigation context for the current user.
    
    Args:
        context: Template context
        
    Returns:
        Dictionary with navigation context information
    """
    request = context.get('request')
    user = request.user if request else None
    
    if not user or not user.is_authenticated:
        return {
            'user': user,
            'is_authenticated': False,
            'current_dashboard': None,
            'available_dashboards': [],
            'switch_options': [],
            'has_conflicts': False,
            'show_dashboard_selector': False
        }
    
    try:
        permissions = AuthenticationService.get_user_permissions(user)
        current_dashboard = _get_current_dashboard_from_request(request)
        switch_options = DashboardRouter.get_dashboard_switch_options(user, current_dashboard) if current_dashboard else []
        
        return {
            'user': user,
            'is_authenticated': True,
            'current_dashboard': current_dashboard,
            'available_dashboards': permissions.available_dashboards,
            'switch_options': switch_options,
            'has_conflicts': permissions.has_conflicts,
            'conflict_details': permissions.conflict_details,
            'show_dashboard_selector': len(permissions.available_dashboards) > 1,
            'user_groups': permissions.groups,
            'organization_type': permissions.organization_type
        }
    except Exception as e:
        logger.error(f"Error getting navigation context for user {user.id}: {str(e)}")
        return {
            'user': user,
            'is_authenticated': True,
            'current_dashboard': None,
            'available_dashboards': [],
            'switch_options': [],
            'has_conflicts': True,
            'conflict_details': 'Error loading navigation context',
            'show_dashboard_selector': False
        }


@register.simple_tag
def get_dashboard_info(dashboard_name):
    """
    Template tag to get information about a specific dashboard from Authentication Group Management.
    
    Args:
        dashboard_name: Name of the dashboard
        
    Returns:
        Dictionary with dashboard information
    """
    # First try to get from Authentication Group Management
    dashboard_info = AuthenticationService.get_dashboard_info_from_auth_groups(dashboard_name)
    
    if dashboard_info:
        return {
            'name': dashboard_info['name'],
            'display_name': dashboard_info['display_name'],
            'url': dashboard_info['url'],
            'description': dashboard_info.get('description', ''),
            'required_groups': ', '.join(dashboard_info.get('required_groups', [])),
            'required_org_types': ', '.join(dashboard_info.get('required_org_types', []))
        }
    
    # Fallback to hardcoded configurations
    hardcoded_dashboard = AuthenticationService.DASHBOARDS.get(dashboard_name)
    if hardcoded_dashboard:
        return {
            'name': hardcoded_dashboard.name,
            'display_name': hardcoded_dashboard.display_name,
            'url': hardcoded_dashboard.url,
            'description': f'Access {hardcoded_dashboard.display_name.lower()} features',
            'required_groups': ', '.join(hardcoded_dashboard.required_groups),
            'required_org_types': ', '.join(hardcoded_dashboard.required_org_types)
        }
    
    # Final fallback
    return {
        'name': dashboard_name,
        'display_name': dashboard_name.replace('_', ' ').title(),
        'url': f'/{dashboard_name}/',
        'description': f'Access {dashboard_name} dashboard features',
        'required_groups': 'Not configured',
        'required_org_types': 'Not configured'
    }


@register.simple_tag(takes_context=True)
def is_current_dashboard(context, dashboard_name):
    """
    Template tag to check if the specified dashboard is currently active.
    
    Args:
        context: Template context
        dashboard_name: Name of the dashboard to check
        
    Returns:
        Boolean indicating if dashboard is currently active
    """
    request = context.get('request')
    if not request:
        return False
    
    current_dashboard = _get_current_dashboard_from_request(request)
    return current_dashboard == dashboard_name


def _get_current_dashboard_from_request(request):
    """
    Helper function to determine current dashboard from request.
    
    Args:
        request: Django request object
        
    Returns:
        Current dashboard name or None
    """
    if not request or not hasattr(request, 'resolver_match'):
        return None
    
    resolver_match = request.resolver_match
    if not resolver_match:
        return None
    
    url_name = resolver_match.url_name
    namespace = resolver_match.namespace
    
    # Map URL patterns to dashboard names
    if url_name == 'dashboard' and not namespace:
        return 'customer'
    elif url_name == 'insurance_dashboard' and namespace == 'insurance':
        return 'insurance'
    elif url_name == 'dashboard_selector':
        return 'selector'
    
    return None


@register.simple_tag
def get_auth_group_configs():
    """
    Template tag to get all active authentication group configurations.
    Useful for debugging and admin interfaces.
    
    Returns:
        List of authentication group configurations
    """
    from ..models import AuthenticationGroup
    
    try:
        auth_groups = AuthenticationGroup.objects.filter(is_active=True).select_related('group').order_by('-priority')
        configs = []
        
        for auth_group in auth_groups:
            configs.append({
                'group_name': auth_group.group.name,
                'display_name': auth_group.display_name,
                'dashboard_type': auth_group.dashboard_type,
                'dashboard_url': auth_group.dashboard_url,
                'priority': auth_group.priority,
                'description': auth_group.description,
                'compatible_org_types': auth_group.compatible_org_types,
                'user_count': auth_group.group.user_set.count()
            })
        
        return configs
    except Exception as e:
        logger.error(f"Error getting auth group configs: {str(e)}")
        return []


@register.inclusion_tag('dashboard/session_info.html', takes_context=True)
def get_session_info(context):
    """
    Template tag to get session information for debugging and user feedback.
    
    Args:
        context: Template context
        
    Returns:
        Dictionary with session information
    """
    request = context.get('request')
    if not request or not hasattr(request, 'session'):
        return {'has_session': False}
    
    session = request.session
    
    return {
        'has_session': True,
        'session_key': session.session_key,
        'session_age': session.get_expiry_age(),
        'last_dashboard': session.get('last_dashboard'),
        'dashboard_switches': session.get('dashboard_switches', 0),
        'login_timestamp': session.get('login_timestamp')
    }