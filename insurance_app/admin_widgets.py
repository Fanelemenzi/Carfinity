"""
Custom admin widgets and dashboard components for the quote system.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    QuoteSystemHealthMetrics, PartQuoteRequest, PartQuote, 
    DamagedPart, QuoteSystemConfiguration, ProviderConfiguration
)

class QuoteSystemHealthWidget:
    """Widget for displaying quote system health in admin dashboard"""
    
    @staticmethod
    def get_health_summary():
        """Get current system health summary"""
        try:
            # Get latest health metrics
            latest_metrics = QuoteSystemHealthMetrics.objects.latest('recorded_at')
            
            # Calculate current stats
            now = timezone.now()
            yesterday = now - timedelta(days=1)
            
            current_stats = {
                'requests_24h': PartQuoteRequest.objects.filter(request_date__gte=yesterday).count(),
                'quotes_24h': PartQuote.objects.filter(quote_date__gte=yesterday).count(),
                'pending_requests': PartQuoteRequest.objects.filter(status='pending').count(),
                'active_parts': DamagedPart.objects.filter(quotes__isnull=False).distinct().count(),
            }
            
            return {
                'health_status': latest_metrics.get_system_health_status(),
                'success_rate': latest_metrics.get_overall_success_rate(),
                'last_updated': latest_metrics.recorded_at,
                **current_stats
            }
        except QuoteSystemHealthMetrics.DoesNotExist:
            return {
                'health_status': 'unknown',
                'success_rate': 0,
                'last_updated': None,
                'requests_24h': 0,
                'quotes_24h': 0,
                'pending_requests': 0,
                'active_parts': 0,
            }
    
    @staticmethod
    def render_health_widget():
        """Render health widget HTML"""
        health_data = QuoteSystemHealthWidget.get_health_summary()
        
        # Health status colors
        status_colors = {
            'excellent': '#28a745',
            'good': '#17a2b8',
            'fair': '#ffc107',
            'poor': '#dc3545',
            'unknown': '#6c757d'
        }
        
        status_color = status_colors.get(health_data['health_status'], '#6c757d')
        
        html = f"""
        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin: 10px 0;">
            <h3 style="margin-top: 0; color: #495057;">Quote System Health</h3>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: {status_color};">
                        {health_data['health_status'].upper()}
                    </div>
                    <div style="font-size: 12px; color: #6c757d;">System Status</div>
                </div>
                
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #495057;">
                        {health_data['success_rate']:.1f}%
                    </div>
                    <div style="font-size: 12px; color: #6c757d;">Success Rate</div>
                </div>
                
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #495057;">
                        {health_data['requests_24h']}
                    </div>
                    <div style="font-size: 12px; color: #6c757d;">Requests (24h)</div>
                </div>
                
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: bold; color: #495057;">
                        {health_data['quotes_24h']}
                    </div>
                    <div style="font-size: 12px; color: #6c757d;">Quotes (24h)</div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; font-size: 14px;">
                <span>Pending Requests: <strong>{health_data['pending_requests']}</strong></span>
                <span>Active Parts: <strong>{health_data['active_parts']}</strong></span>
            </div>
            
            <div style="margin-top: 10px; font-size: 12px; color: #6c757d;">
                Last Updated: {health_data['last_updated'].strftime('%Y-%m-%d %H:%M') if health_data['last_updated'] else 'Never'}
            </div>
            
            <div style="margin-top: 10px;">
                <a href="{reverse('admin:insurance_app_quotesystemhealthmetrics_changelist')}" 
                   style="color: #007bff; text-decoration: none; font-size: 12px;">
                    View Detailed Metrics →
                </a>
            </div>
        </div>
        """
        
        return mark_safe(html)

class QuoteSystemConfigWidget:
    """Widget for displaying current system configuration"""
    
    @staticmethod
    def get_config_summary():
        """Get current configuration summary"""
        try:
            config = QuoteSystemConfiguration.get_config()
            
            # Count enabled providers
            enabled_providers = sum([
                config.enable_assessor_estimates,
                config.enable_dealer_quotes,
                config.enable_independent_quotes,
                config.enable_network_quotes
            ])
            
            return {
                'labor_rate': config.default_labor_rate,
                'quote_expiry_days': config.default_quote_expiry_days,
                'confidence_threshold': config.confidence_threshold,
                'enabled_providers': enabled_providers,
                'total_providers': 4,
                'performance_logging': config.enable_performance_logging,
                'health_monitoring': config.enable_health_monitoring,
                'last_updated': config.updated_at,
                'updated_by': config.updated_by.username if config.updated_by else 'System'
            }
        except:
            return {
                'labor_rate': 0,
                'quote_expiry_days': 0,
                'confidence_threshold': 0,
                'enabled_providers': 0,
                'total_providers': 4,
                'performance_logging': False,
                'health_monitoring': False,
                'last_updated': None,
                'updated_by': 'Unknown'
            }
    
    @staticmethod
    def render_config_widget():
        """Render configuration widget HTML"""
        config_data = QuoteSystemConfigWidget.get_config_summary()
        
        provider_color = '#28a745' if config_data['enabled_providers'] == 4 else '#ffc107' if config_data['enabled_providers'] > 0 else '#dc3545'
        
        html = f"""
        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin: 10px 0;">
            <h3 style="margin-top: 0; color: #495057;">System Configuration</h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div>
                    <div style="font-weight: bold; color: #495057;">Labor Rate</div>
                    <div style="font-size: 18px; color: #007bff;">£{config_data['labor_rate']}/hour</div>
                </div>
                
                <div>
                    <div style="font-weight: bold; color: #495057;">Quote Expiry</div>
                    <div style="font-size: 18px; color: #007bff;">{config_data['quote_expiry_days']} days</div>
                </div>
                
                <div>
                    <div style="font-weight: bold; color: #495057;">Confidence Threshold</div>
                    <div style="font-size: 18px; color: #007bff;">{config_data['confidence_threshold']}%</div>
                </div>
                
                <div>
                    <div style="font-weight: bold; color: #495057;">Active Providers</div>
                    <div style="font-size: 18px; color: {provider_color};">
                        {config_data['enabled_providers']}/{config_data['total_providers']}
                    </div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 10px;">
                <span>Performance Logging: 
                    <strong style="color: {'#28a745' if config_data['performance_logging'] else '#dc3545'};">
                        {'✓ Enabled' if config_data['performance_logging'] else '✗ Disabled'}
                    </strong>
                </span>
                <span>Health Monitoring: 
                    <strong style="color: {'#28a745' if config_data['health_monitoring'] else '#dc3545'};">
                        {'✓ Enabled' if config_data['health_monitoring'] else '✗ Disabled'}
                    </strong>
                </span>
            </div>
            
            <div style="font-size: 12px; color: #6c757d;">
                Last Updated: {config_data['last_updated'].strftime('%Y-%m-%d %H:%M') if config_data['last_updated'] else 'Never'} 
                by {config_data['updated_by']}
            </div>
            
            <div style="margin-top: 10px;">
                <a href="{reverse('admin:insurance_app_quotesystemconfiguration_changelist')}" 
                   style="color: #007bff; text-decoration: none; font-size: 12px;">
                    Modify Configuration →
                </a>
            </div>
        </div>
        """
        
        return mark_safe(html)

# Custom admin site class to include widgets
class QuoteSystemAdminSite(admin.AdminSite):
    """Custom admin site with quote system dashboard widgets"""
    
    def index(self, request, extra_context=None):
        """Override index to include quote system widgets"""
        extra_context = extra_context or {}
        
        # Add quote system widgets to context
        extra_context.update({
            'quote_health_widget': QuoteSystemHealthWidget.render_health_widget(),
            'quote_config_widget': QuoteSystemConfigWidget.render_config_widget(),
        })
        
        return super().index(request, extra_context)

# Function to add widgets to existing admin
def add_quote_widgets_to_admin():
    """Add quote system widgets to the existing admin interface"""
    # This would be called in apps.py ready() method
    # For now, we'll just provide the widget functions
    pass