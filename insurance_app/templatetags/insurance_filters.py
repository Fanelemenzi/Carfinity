from django import template
from django.utils.safestring import mark_safe
import statistics

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_num(value, arg):
    """Add arg to value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def avg(queryset, field):
    """Calculate average of a field in queryset"""
    try:
        if hasattr(queryset, '__iter__'):
            values = []
            for item in queryset:
                if isinstance(item, dict):
                    val = item.get(field, 0)
                else:
                    val = getattr(item, field, 0)
                if val:
                    values.append(float(val))
            
            if values:
                return statistics.mean(values)
        return 0
    except (ValueError, TypeError, AttributeError):
        return 0

@register.filter
def min_by(queryset, field):
    """Get item with minimum value for field"""
    try:
        if hasattr(queryset, '__iter__'):
            min_item = None
            min_value = float('inf')
            
            for item in queryset:
                if isinstance(item, dict):
                    val = item.get(field, 0)
                else:
                    val = getattr(item, field, 0)
                
                if val and float(val) < min_value:
                    min_value = float(val)
                    min_item = item
            
            return min_item
        return None
    except (ValueError, TypeError, AttributeError):
        return None

@register.filter
def max_by(queryset, field):
    """Get item with maximum value for field"""
    try:
        if hasattr(queryset, '__iter__'):
            max_item = None
            max_value = float('-inf')
            
            for item in queryset:
                if isinstance(item, dict):
                    val = item.get(field, 0)
                else:
                    val = getattr(item, field, 0)
                
                if val and float(val) > max_value:
                    max_value = float(val)
                    max_item = item
            
            return max_item
        return None
    except (ValueError, TypeError, AttributeError):
        return None

@register.filter
def format_currency(value):
    """Format value as currency"""
    try:
        return f"£{float(value):,.0f}"
    except (ValueError, TypeError):
        return "£0"

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def pluralize(value, suffix='s'):
    """Add plural suffix if value is not 1"""
    try:
        if int(value) == 1:
            return ''
        return suffix
    except (ValueError, TypeError):
        return suffix

@register.filter
def split(value, delimiter):
    """Split string by delimiter"""
    try:
        return str(value).split(delimiter)
    except (AttributeError, TypeError):
        return []

@register.filter
def replace(value, args):
    """Replace substring in string"""
    try:
        old, new = args.split(',', 1)
        return str(value).replace(old, new)
    except (AttributeError, ValueError, TypeError):
        return value