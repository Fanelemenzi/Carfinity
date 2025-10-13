"""
Template tags and filters for dashboard data formatting and calculations
"""

from django import template
from django.utils import timezone
from datetime import datetime, timedelta
import locale

register = template.Library()


@register.filter
def currency_format(value):
    """
    Format a number as currency
    """
    if value is None:
        return "N/A"
    try:
        return f"E{float(value):,.0f}"
    except (ValueError, TypeError):
        return "N/A"


@register.filter
def mileage_format(value):
    """
    Format mileage with proper units
    """
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,} km"
    except (ValueError, TypeError):
        return "N/A"


@register.filter
def days_until(date_value):
    """
    Calculate days until a given date
    """
    if not date_value:
        return None
    
    try:
        if isinstance(date_value, str):
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        
        current_date = timezone.now().date()
        delta = date_value - current_date
        return delta.days
    except (ValueError, TypeError):
        return None


@register.filter
def days_since(date_value):
    """
    Calculate days since a given date
    """
    if not date_value:
        return None
    
    try:
        if isinstance(date_value, str):
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        
        current_date = timezone.now().date()
        delta = current_date - date_value
        return delta.days
    except (ValueError, TypeError):
        return None


@register.filter
def health_status_color(status):
    """
    Return appropriate CSS color class for health status
    """
    status_colors = {
        'Healthy': 'text-green-600',
        'Needs Attention': 'text-yellow-600',
        'Critical': 'text-red-600',
        'Unknown': 'text-gray-500'
    }
    return status_colors.get(status, 'text-gray-500')


@register.filter
def alert_priority_color(priority):
    """
    Return appropriate CSS color class for alert priority
    """
    priority_colors = {
        'HIGH': 'text-red-600',
        'MEDIUM': 'text-orange-500',
        'LOW': 'text-blue-500'
    }
    return priority_colors.get(priority, 'text-gray-500')


@register.filter
def alert_priority_emoji(priority):
    """
    Return appropriate emoji for alert priority
    """
    priority_emojis = {
        'HIGH': '⚠️',
        'MEDIUM': '🛠️',
        'LOW': '📑'
    }
    return priority_emojis.get(priority, '📋')


@register.filter
def condition_rating_display(rating):
    """
    Convert condition rating to display format
    """
    rating_display = {
        'excellent': 'Excellent',
        'very_good': 'Very Good',
        'good': 'Good',
        'fair': 'Fair',
        'poor': 'Poor'
    }
    return rating_display.get(rating, rating.replace('_', ' ').title() if rating else 'N/A')


@register.filter
def service_urgency_class(days_until):
    """
    Return CSS class based on service urgency
    """
    if days_until is None:
        return 'text-gray-500'
    elif days_until < 0:
        return 'text-red-600 font-bold'  # Overdue
    elif days_until <= 7:
        return 'text-orange-600 font-semibold'  # Due soon
    elif days_until <= 30:
        return 'text-yellow-600'  # Due this month
    else:
        return 'text-green-600'  # Not urgent


@register.filter
def service_urgency_text(days_until):
    """
    Return appropriate text for service urgency
    """
    if days_until is None:
        return 'Not scheduled'
    elif days_until < 0:
        return f'{abs(days_until)} days overdue'
    elif days_until == 0:
        return 'Due today'
    elif days_until == 1:
        return 'Due tomorrow'
    else:
        return f'In {days_until} days'


@register.simple_tag
def get_health_score_color(score):
    """
    Return appropriate color for health score
    """
    if score is None:
        return 'text-gray-500'
    
    try:
        # Convert to float to handle both string and numeric inputs
        score_value = float(score)
        if score_value >= 80:
            return 'text-green-600'
        elif score_value >= 60:
            return 'text-yellow-600'
        else:
            return 'text-red-600'
    except (ValueError, TypeError):
        return 'text-gray-500'


@register.filter
def format_date_friendly(date_value):
    """
    Format date in a user-friendly way
    """
    if not date_value:
        return 'N/A'
    
    try:
        if isinstance(date_value, str):
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        
        return date_value.strftime('%B %d, %Y')
    except (ValueError, TypeError):
        return 'N/A'


@register.simple_tag
def get_next_service_summary(upcoming_maintenance):
    """
    Get summary of next service from upcoming maintenance list
    """
    if not upcoming_maintenance:
        return {
            'service_type': 'No scheduled maintenance',
            'date': None,
            'days_until': None,
            'is_overdue': False
        }
    
    # Get the most urgent maintenance item
    next_service = upcoming_maintenance[0] if upcoming_maintenance else None
    
    if next_service:
        return {
            'service_type': next_service.get('service_type', 'Unknown Service'),
            'date': next_service.get('scheduled_date'),
            'days_until': next_service.get('days_until'),
            'is_overdue': next_service.get('is_overdue', False)
        }
    
    return {
        'service_type': 'No scheduled maintenance',
        'date': None,
        'days_until': None,
        'is_overdue': False
    }


@register.filter
def truncate_vin(vin):
    """
    Truncate VIN for display (show first 8 and last 4 characters)
    """
    if not vin or len(vin) < 12:
        return vin
    
    return f"{vin[:8]}...{vin[-4:]}"


@register.filter
def default_if_none(value, default):
    """
    Return default value if the given value is None
    """
    return default if value is None else value


@register.simple_tag
def calculate_service_interval(last_service_date, interval_days):
    """
    Calculate next service date based on last service and interval
    """
    if not last_service_date or not interval_days:
        return None
    
    try:
        if isinstance(last_service_date, str):
            last_service_date = datetime.strptime(last_service_date, '%Y-%m-%d').date()
        
        next_service_date = last_service_date + timedelta(days=interval_days)
        return next_service_date
    except (ValueError, TypeError):
        return None


@register.simple_tag
def health_score_progress_width(score):
    """
    Calculate progress bar width percentage for health score
    """
    if score is None:
        return 0
    try:
        return min(max(int(score), 0), 100)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def health_score_status_text(score):
    """
    Return descriptive text for health score
    """
    if score is None:
        return 'No data available'
    
    try:
        score = int(score)
        if score >= 90:
            return 'Excellent condition'
        elif score >= 80:
            return 'Good condition'
        elif score >= 70:
            return 'Fair condition'
        elif score >= 60:
            return 'Needs attention'
        else:
            return 'Poor condition'
    except (ValueError, TypeError):
        return 'No data available'


@register.filter
def percentage_format(value):
    """
    Format a number as percentage
    """
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "N/A"


@register.simple_tag
def days_until_service_text(days):
    """
    Convert days until service to friendly text
    """
    if days is None:
        return 'Not scheduled'
    elif days < 0:
        return f'{abs(days)} days overdue'
    elif days == 0:
        return 'Due today'
    elif days == 1:
        return 'Due tomorrow'
    elif days <= 7:
        return f'Due in {days} days'
    elif days <= 30:
        return f'Due in {days} days'
    else:
        return f'Due in {days} days'


@register.filter
def number_format(value):
    """
    Format numbers with thousand separators
    """
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "N/A"


@register.simple_tag
def vehicle_age_years(manufacture_year):
    """
    Calculate vehicle age in years
    """
    if not manufacture_year:
        return None
    
    try:
        current_year = timezone.now().year
        return current_year - int(manufacture_year)
    except (ValueError, TypeError):
        return None


@register.filter
def alert_type_display(alert_type):
    """
    Convert alert type to display format
    """
    type_display = {
        'MAINTENANCE_OVERDUE': 'Maintenance Overdue',
        'PART_REPLACEMENT': 'Part Replacement',
        'INSURANCE_EXPIRY': 'Insurance Expiry',
        'INSPECTION_DUE': 'Inspection Due'
    }
    return type_display.get(alert_type, alert_type.replace('_', ' ').title() if alert_type else 'Unknown')


@register.filter
def mileage_with_unit(value, unit='km'):
    """
    Format mileage with specified unit (km or miles)
    """
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,} {unit}"
    except (ValueError, TypeError):
        return "N/A"


@register.filter
def mileage_difference(current_mileage, target_mileage):
    """
    Calculate difference between current and target mileage
    """
    if current_mileage is None or target_mileage is None:
        return None
    try:
        return int(target_mileage) - int(current_mileage)
    except (ValueError, TypeError):
        return None


@register.simple_tag
def alert_priority_badge_class(priority):
    """
    Return complete CSS classes for alert priority badge
    """
    priority_classes = {
        'HIGH': 'bg-red-100 text-red-800 border-red-200',
        'MEDIUM': 'bg-orange-100 text-orange-800 border-orange-200',
        'LOW': 'bg-blue-100 text-blue-800 border-blue-200'
    }
    base_classes = 'px-2 py-1 text-xs font-medium rounded-full border'
    priority_class = priority_classes.get(priority, 'bg-gray-100 text-gray-800 border-gray-200')
    return f"{base_classes} {priority_class}"


@register.simple_tag
def alert_priority_icon(priority):
    """
    Return appropriate icon class for alert priority
    """
    priority_icons = {
        'HIGH': 'fas fa-exclamation-triangle',
        'MEDIUM': 'fas fa-exclamation-circle',
        'LOW': 'fas fa-info-circle'
    }
    return priority_icons.get(priority, 'fas fa-bell')


@register.simple_tag
def cost_trend_indicator(current_cost, previous_cost):
    """
    Return cost trend indicator (up, down, or stable)
    """
    if current_cost is None or previous_cost is None:
        return {'trend': 'stable', 'percentage': 0, 'icon': 'fas fa-minus'}
    
    try:
        current = float(current_cost)
        previous = float(previous_cost)
        
        if previous == 0:
            return {'trend': 'up', 'percentage': 100, 'icon': 'fas fa-arrow-up'}
        
        percentage_change = ((current - previous) / previous) * 100
        
        if percentage_change > 5:
            return {
                'trend': 'up',
                'percentage': abs(percentage_change),
                'icon': 'fas fa-arrow-up',
                'color': 'text-red-600'
            }
        elif percentage_change < -5:
            return {
                'trend': 'down',
                'percentage': abs(percentage_change),
                'icon': 'fas fa-arrow-down',
                'color': 'text-green-600'
            }
        else:
            return {
                'trend': 'stable',
                'percentage': abs(percentage_change),
                'icon': 'fas fa-minus',
                'color': 'text-gray-600'
            }
    except (ValueError, TypeError):
        return {'trend': 'stable', 'percentage': 0, 'icon': 'fas fa-minus'}


@register.simple_tag
def cost_trend_text(current_cost, previous_cost):
    """
    Return descriptive text for cost trend
    """
    trend_data = cost_trend_indicator(current_cost, previous_cost)
    
    if trend_data['trend'] == 'up':
        return f"↑ {trend_data['percentage']:.1f}% increase"
    elif trend_data['trend'] == 'down':
        return f"↓ {trend_data['percentage']:.1f}% decrease"
    else:
        return "No significant change"


@register.filter
def cost_category_percentage(category_cost, total_cost):
    """
    Calculate percentage of category cost from total cost
    """
    if category_cost is None or total_cost is None or total_cost == 0:
        return 0
    try:
        return (float(category_cost) / float(total_cost)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.simple_tag
def format_cost_breakdown(maintenance_cost, parts_cost, labor_cost):
    """
    Format cost breakdown for display
    """
    try:
        maintenance = float(maintenance_cost or 0)
        parts = float(parts_cost or 0)
        labor = float(labor_cost or 0)
        total = maintenance + parts + labor
        
        if total == 0:
            return {
                'maintenance_pct': 0,
                'parts_pct': 0,
                'labor_pct': 0,
                'total': 0
            }
        
        return {
            'maintenance_pct': (maintenance / total) * 100,
            'parts_pct': (parts / total) * 100,
            'labor_pct': (labor / total) * 100,
            'total': total
        }
    except (ValueError, TypeError):
        return {
            'maintenance_pct': 0,
            'parts_pct': 0,
            'labor_pct': 0,
            'total': 0
        }


@register.filter
def service_type_icon(service_type):
    """
    Return appropriate icon for service type
    """
    service_icons = {
        'Oil Change': 'fas fa-oil-can',
        'Brake Service': 'fas fa-car-crash',
        'Tire Rotation': 'fas fa-circle',
        'Engine Service': 'fas fa-cog',
        'Transmission Service': 'fas fa-cogs',
        'Battery Service': 'fas fa-car-battery',
        'Air Filter': 'fas fa-wind',
        'Inspection': 'fas fa-search',
        'General Maintenance': 'fas fa-wrench'
    }
    
    # Try exact match first
    if service_type in service_icons:
        return service_icons[service_type]
    
    # Try partial matches
    service_type_lower = service_type.lower() if service_type else ''
    for key, icon in service_icons.items():
        if key.lower() in service_type_lower:
            return icon
    
    # Default icon
    return 'fas fa-tools'


@register.simple_tag
def average_monthly_cost(cost_analytics):
    """
    Calculate average monthly cost from cost analytics data
    """
    if not cost_analytics or not isinstance(cost_analytics, list):
        return 0
    
    try:
        total_cost = sum(float(item.get('total_cost', 0)) for item in cost_analytics)
        months = len(cost_analytics)
        return total_cost / months if months > 0 else 0
    except (ValueError, TypeError):
        return 0


@register.filter
def format_large_number(value):
    """
    Format large numbers with K, M suffixes
    """
    if value is None:
        return "N/A"
    
    try:
        num = float(value)
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return f"{num:.0f}"
    except (ValueError, TypeError):
        return "N/A"