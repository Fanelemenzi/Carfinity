from django import template

register = template.Library()

@register.filter
def getattr(obj, attr_name):
    """Get an attribute of an object dynamically from a string name"""
    try:
        return getattr(obj, attr_name)
    except AttributeError:
        return None

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a dynamic key"""
    return dictionary.get(key)

@register.filter
def status_badge_class(status):
    """Return CSS classes for status badges"""
    status_classes = {
        'pass': 'bg-green-100 text-green-800',
        'fail': 'bg-red-100 text-red-800',
        'major': 'bg-red-100 text-red-800',
        'minor': 'bg-yellow-100 text-yellow-800',
        'na': 'bg-gray-100 text-gray-800',
    }
    return status_classes.get(status, 'bg-gray-100 text-gray-500')

@register.filter
def status_display(status):
    """Return display text for status values"""
    status_display = {
        'pass': '✓ Pass',
        'fail': '✗ Fail',
        'major': '⚠️ Major Issue',
        'minor': '⚠️ Minor Issue',
        'na': 'N/A',
    }
    return status_display.get(status, 'Not Checked')