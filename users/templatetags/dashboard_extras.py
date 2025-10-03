"""
Template tags for dashboard navigation and user experience features.

This module provides template tags that integrate with the simplified 3-group
authentication system to provide conditional navigation and dashboard functionality.
"""

from django import template
from django.contrib.auth.models import User
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=False)
def get_user_dashboard_access(user):
    """
    Template tag to get user's dashboard access information using the 3-group system.

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
            'has_conflicts': False,
            'default_dashboard': None
        }

    try:
        # Get user's groups in priority order (Staff=3, AutoAssess=2, AutoCare=1)
        user_groups = list(user.groups.values_list('name', flat=True))
        available_dashboards = []

        # Debug logging
        logger.info(f"User {user.id} ({user.username}) groups: {user_groups}")

        # Determine available dashboards based on group membership
        if user.groups.filter(name='Staff').exists():
            available_dashboards.append('staff')
            logger.info(f"User {user.id} has Staff group, added 'staff' dashboard")
        if user.groups.filter(name='AutoCare').exists():
            available_dashboards.append('autocare')
            logger.info(f"User {user.id} has AutoCare group, added 'autocare' dashboard")
        if user.groups.filter(name='AutoAssess').exists():
            available_dashboards.append('autoassess')
            logger.info(f"User {user.id} has AutoAssess group, added 'autoassess' dashboard")

        logger.info(f"User {user.id} available dashboards: {available_dashboards}")

        # Set default dashboard based on highest priority group
        default_dashboard = None
        if user.groups.filter(name='Staff').exists():
            default_dashboard = 'staff'
        elif user.groups.filter(name='AutoAssess').exists():
            default_dashboard = 'autoassess'
        elif user.groups.filter(name='AutoCare').exists():
            default_dashboard = 'autocare'

        result = {
            'user': user,
            'available_dashboards': available_dashboards,
            'user_groups': user_groups,
            'has_conflicts': False,
            'default_dashboard': default_dashboard
        }

        logger.info(f"User {user.id} dashboard access result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting dashboard access for user {user.id}: {str(e)}")
        return {
            'user': user,
            'available_dashboards': [],
            'user_groups': [],
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
        dashboard_access = get_user_dashboard_access(user)
        available_dashboards = dashboard_access['available_dashboards']

        # Define dashboard options
        dashboard_options = {
            'staff': {'name': 'staff', 'display_name': 'Staff Dashboard', 'url': '/admin/', 'icon': 'fas fa-shield-alt'},
            'autocare': {'name': 'autocare', 'display_name': 'AutoCare Dashboard', 'url': '/maintenance/dashboard/', 'icon': 'fas fa-car'},
            'autoassess': {'name': 'autoassess', 'display_name': 'AutoAssess Dashboard', 'url': '/insurance/', 'icon': 'fas fa-clipboard-check'}
        }

        options = []
        for dashboard_name in available_dashboards:
            if dashboard_name in dashboard_options and dashboard_name != current_dashboard:
                options.append(dashboard_options[dashboard_name])

        return options
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
        dashboard_access = get_user_dashboard_access(user)
        return dashboard_name in dashboard_access['available_dashboards']
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
        dashboard_access = get_user_dashboard_access(user)
        return dashboard_access['default_dashboard'] or ''
    except Exception as e:
        logger.error(f"Error getting default dashboard for user {user.id}: {str(e)}")
        return ''


@register.simple_tag
def get_user_dashboard_url(user):
    """
    Template tag to get the appropriate dashboard URL for a user.

    Args:
        user: Django User instance

    Returns:
        Dashboard URL string
    """
    if not user or not user.is_authenticated:
        return '/login/'

    try:
        from ..services import AuthenticationService
        
        # Get user permissions
        permissions = AuthenticationService.get_user_permissions(user)
        
        if not permissions.available_dashboards:
            logger.warning(f"User {user.id} has no available dashboards")
            return '/access-denied/'
        
        # If user has multiple dashboards, redirect to dashboard selector
        if len(permissions.available_dashboards) > 1:
            logger.info(f"User {user.id} has multiple dashboards, redirecting to selector")
            return '/dashboard-selector/'
        
        # If user has only one dashboard, redirect directly to it
        if permissions.default_dashboard:
            dashboard_info = AuthenticationService.DASHBOARDS.get(permissions.default_dashboard)
            if dashboard_info:
                return dashboard_info.url
        
        # Fallback to first available dashboard
        first_dashboard = permissions.available_dashboards[0]
        dashboard_info = AuthenticationService.DASHBOARDS.get(first_dashboard)
        return dashboard_info.url if dashboard_info else '/dashboard/'
        
    except Exception as e:
        logger.error(f"Error getting dashboard URL for user {user.id}: {str(e)}")
        return '/dashboard/'


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
        dashboard_access = get_user_dashboard_access(user)
        current_dashboard = _get_current_dashboard_from_request(request)
        switch_options = get_dashboard_switch_options(user, current_dashboard)

        return {
            'user': user,
            'is_authenticated': True,
            'current_dashboard': current_dashboard,
            'available_dashboards': dashboard_access['available_dashboards'],
            'switch_options': switch_options,
            'has_conflicts': dashboard_access['has_conflicts'],
            'conflict_details': dashboard_access.get('conflict_details', ''),
            'show_dashboard_selector': len(dashboard_access['available_dashboards']) > 1,
            'user_groups': dashboard_access['user_groups']
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
    Template tag to get information about a specific dashboard.

    Args:
        dashboard_name: Name of the dashboard

    Returns:
        Dictionary with dashboard information
    """
    dashboard_info = {
        'staff': {
            'name': 'staff',
            'display_name': 'Staff Dashboard',
            'url': '/admin/',
            'description': 'Administrative access to all system features',
            'required_groups': 'Staff',
            'required_org_types': 'All'
        },
        'autocare': {
            'name': 'autocare',
            'display_name': 'AutoCare Dashboard',
            'url': '/maintenance/dashboard/',
            'description': 'Vehicle maintenance and service management',
            'required_groups': 'AutoCare',
            'required_org_types': 'All'
        },
        'autoassess': {
            'name': 'autoassess',
            'display_name': 'AutoAssess Dashboard',
            'url': '/insurance/',
            'description': 'Vehicle assessment and insurance claims',
            'required_groups': 'AutoAssess',
            'required_org_types': 'All'
        }
    }

    return dashboard_info.get(dashboard_name, {
        'name': dashboard_name,
        'display_name': dashboard_name.replace('_', ' ').title(),
        'url': f'/{dashboard_name}/',
        'description': f'Access {dashboard_name} dashboard features',
        'required_groups': 'Not configured',
        'required_org_types': 'Not configured'
    })


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
        return 'autocare'
    elif url_name == 'insurance_dashboard' and namespace == 'insurance':
        return 'autoassess'
    elif url_name == 'admin:index' or (url_name == 'index' and namespace == 'admin'):
        return 'staff'

    return None


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