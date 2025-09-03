from django import template
from django.utils import timezone
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    """Add days to a date"""
    try:
        return value + timedelta(days=int(days))
    except (ValueError, TypeError):
        return value

@register.filter
def days_until(value):
    """Calculate days until a date"""
    try:
        today = timezone.now().date()
        if hasattr(value, 'date'):
            value = value.date()
        delta = value - today
        return delta.days
    except (ValueError, TypeError, AttributeError):
        return 0

@register.filter
def is_overdue(value):
    """Check if a date is overdue"""
    try:
        today = timezone.now().date()
        if hasattr(value, 'date'):
            value = value.date()
        return value < today
    except (ValueError, TypeError, AttributeError):
        return False

@register.filter
def is_due_soon(value, days=7):
    """Check if a date is due within specified days"""
    try:
        today = timezone.now().date()
        if hasattr(value, 'date'):
            value = value.date()
        future_date = today + timedelta(days=int(days))
        return today <= value <= future_date
    except (ValueError, TypeError, AttributeError):
        return False

@register.simple_tag(takes_context=True)
def check_auth_redirect(context):
    """
    Check if user is authenticated and redirect to index.html if not,
    with exceptions for search.html, search-results.html, and index.html
    """
    request = context.get('request')
    if not request:
        return ''
    
    # Get the current path
    current_path = request.path
    
    # Define allowed paths for unauthenticated users
    allowed_paths = [
        '/',  # home/index page
        '/search/',
        '/search-results/',
    ]
    
    # Check if current path is allowed
    is_allowed_path = any(current_path.startswith(path) for path in allowed_paths)
    
    # If user is not authenticated and not on an allowed page, redirect to home
    if not request.user.is_authenticated and not is_allowed_path:
        return f'<script>window.location.href = "{reverse("home")}";</script>'
    
    return ''

@register.inclusion_tag('auth_check.html', takes_context=True)
def auth_guard(context):
    """
    Template inclusion tag that renders authentication guard
    """
    request = context.get('request')
    if not request:
        return {'show_content': True, 'redirect_url': ''}
    
    # Get the current path
    current_path = request.path
    
    # Define allowed paths for unauthenticated users
    allowed_paths = [
        '/',  # index page
        '/search/',
        '/search-results/',
    ]
    
    # Check if current path is allowed
    is_allowed_path = any(current_path.startswith(path) for path in allowed_paths)
    
    # Determine if content should be shown
    show_content = request.user.is_authenticated or is_allowed_path
    redirect_url = reverse('home') if not show_content else ''
    
    return {
        'show_content': show_content,
        'redirect_url': redirect_url,
        'is_authenticated': request.user.is_authenticated
    }