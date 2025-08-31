from django import template
from django.utils import timezone
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