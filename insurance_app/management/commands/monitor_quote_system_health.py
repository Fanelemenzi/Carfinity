"""
Management command for monitoring quote system health and performance.
This command collects system metrics, logs performance data, and generates health reports.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta
import logging

from insurance_app.models import (
    QuoteSystemHealthMetrics, QuoteSystemAuditLog, PartQuoteRequest, 
    PartQuote, DamagedPart, PartMarketAverage, QuoteSystemConfiguration
)

logger = logging.getLogger('quote_system')

class Command(BaseCommand):
    help = 'Monitor quote system health and collect performance metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup-logs',
            action='store_true',
            help='Clean up old audit logs based on retention policy'
        )
        parser.add_argument(
            '--generate-report',
            action='store_true',
            help='Generate detailed health report'
        )
        parser.add_argument(
            '--alert-threshold',
            type=int,
            default=80,
            help='Success rate threshold for alerts (default: 80%)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting quote system health monitoring...'))
        
        # Collect current metrics
        metrics = self.collect_health_metrics()
        
        # Save metrics to database
        health_record = QuoteSystemHealthMetrics.objects.create(**metrics)
        
        # Check for alerts
        self.check_system_alerts(health_record, options['alert_threshold'])
        
        # Clean up old logs if requested
        if options['cleanup_logs']:
            self.cleanup_old_logs()
        
        # Generate detailed report if requested
        if options['generate_report']:
            self.generate_health_report(health_record)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Health monitoring completed. Overall success rate: {health_record.get_overall_success_rate():.1f}%'
            )
        )
    
    def collect_health_metrics(self):
        """Collect comprehensive system health metrics"""
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        # Quote request metrics
        total_requests = PartQuoteRequest.objects.filter(
            request_date__gte=yesterday
        ).count()
        
        successful_requests = PartQuoteRequest.objects.filter(
            request_date__gte=yesterday,
            status__in=['sent', 'received']
        ).count()
        
        failed_requests = PartQuoteRequest.objects.filter(
            request_date__gte=yesterday,
            status__in=['expired', 'cancelled']
        ).count()
        
        # Quote response metrics
        quotes_received = PartQuote.objects.filter(
            quote_date__gte=yesterday
        ).count()
        
        # Calculate average response time
        avg_response_time = self.calculate_average_response_time(yesterday)
        
        # Provider success rates
        provider_rates = self.calculate_provider_success_rates(yesterday)
        
        # System performance metrics
        performance_metrics = self.calculate_performance_metrics()
        
        # Error tracking
        error_metrics = self.calculate_error_metrics(yesterday)
        
        # Data quality metrics
        quality_metrics = self.calculate_data_quality_metrics()
        
        return {
            'total_quote_requests_24h': total_requests,
            'successful_quote_requests_24h': successful_requests,
            'failed_quote_requests_24h': failed_requests,
            'total_quotes_received_24h': quotes_received,
            'average_response_time_hours': avg_response_time,
            'assessor_success_rate': provider_rates.get('assessor', 0),
            'dealer_success_rate': provider_rates.get('dealer', 0),
            'independent_success_rate': provider_rates.get('independent', 0),
            'network_success_rate': provider_rates.get('network', 0),
            **performance_metrics,
            **error_metrics,
            **quality_metrics
        }
    
    def calculate_average_response_time(self, since_date):
        """Calculate average response time for quotes"""
        quotes_with_requests = PartQuote.objects.filter(
            quote_date__gte=since_date,
            quote_request__dispatched_at__isnull=False
        ).select_related('quote_request')
        
        if not quotes_with_requests.exists():
            return 0
        
        total_hours = 0
        count = 0
        
        for quote in quotes_with_requests:
            if quote.quote_request.dispatched_at:
                time_diff = quote.quote_date - quote.quote_request.dispatched_at
                total_hours += time_diff.total_seconds() / 3600
                count += 1
        
        return total_hours / count if count > 0 else 0
    
    def calculate_provider_success_rates(self, since_date):
        """Calculate success rates for each provider type"""
        provider_types = ['assessor', 'dealer', 'independent', 'network']
        rates = {}
        
        for provider_type in provider_types:
            total_requests = PartQuoteRequest.objects.filter(
                request_date__gte=since_date,
                **{f'include_{provider_type}': True}
            ).count()
            
            successful_quotes = PartQuote.objects.filter(
                quote_date__gte=since_date,
                provider_type=provider_type
            ).count()
            
            if total_requests > 0:
                rates[provider_type] = (successful_quotes / total_requests) * 100
            else:
                rates[provider_type] = 0
        
        return rates
    
    def calculate_performance_metrics(self):
        """Calculate system performance metrics"""
        # These would typically be collected from application logs or monitoring
        # For now, return default values - in production, integrate with APM tools
        return {
            'average_parts_identification_time_seconds': 2.5,
            'average_market_calculation_time_seconds': 1.8,
            'average_recommendation_time_seconds': 0.9
        }
    
    def calculate_error_metrics(self, since_date):
        """Calculate error metrics from audit logs"""
        api_errors = QuoteSystemAuditLog.objects.filter(
            timestamp__gte=since_date,
            severity='error',
            action_type__in=['quote_request_dispatched', 'quote_received']
        ).count()
        
        database_errors = QuoteSystemAuditLog.objects.filter(
            timestamp__gte=since_date,
            severity='error',
            description__icontains='database'
        ).count()
        
        validation_errors = QuoteSystemAuditLog.objects.filter(
            timestamp__gte=since_date,
            severity='error',
            action_type='quote_rejected'
        ).count()
        
        return {
            'api_errors_24h': api_errors,
            'database_errors_24h': database_errors,
            'validation_errors_24h': validation_errors
        }
    
    def calculate_data_quality_metrics(self):
        """Calculate data quality metrics"""
        high_confidence = PartMarketAverage.objects.filter(
            confidence_level__gte=70
        ).count()
        
        low_confidence = PartMarketAverage.objects.filter(
            confidence_level__lt=70
        ).count()
        
        # Count outliers from market averages
        outlier_count = 0
        for market_avg in PartMarketAverage.objects.all():
            if market_avg.outlier_quotes:
                outlier_count += len(market_avg.outlier_quotes)
        
        return {
            'high_confidence_market_averages': high_confidence,
            'low_confidence_market_averages': low_confidence,
            'outlier_quotes_detected': outlier_count
        }
    
    def check_system_alerts(self, health_record, threshold):
        """Check for system alerts and log warnings"""
        success_rate = health_record.get_overall_success_rate()
        
        if success_rate < threshold:
            self.log_audit_event(
                'system_error',
                'critical',
                f'Quote system success rate ({success_rate:.1f}%) below threshold ({threshold}%)',
                {'success_rate': success_rate, 'threshold': threshold}
            )
            self.stdout.write(
                self.style.ERROR(
                    f'ALERT: System success rate ({success_rate:.1f}%) below threshold ({threshold}%)'
                )
            )
        
        # Check for high error rates
        total_errors = (
            health_record.api_errors_24h + 
            health_record.database_errors_24h + 
            health_record.validation_errors_24h
        )
        
        if total_errors > 10:  # More than 10 errors in 24h
            self.log_audit_event(
                'system_error',
                'warning',
                f'High error count detected: {total_errors} errors in 24h',
                {'total_errors': total_errors}
            )
            self.stdout.write(
                self.style.WARNING(f'WARNING: High error count: {total_errors} errors in 24h')
            )
        
        # Check provider performance
        provider_rates = [
            ('Assessor', health_record.assessor_success_rate),
            ('Dealer', health_record.dealer_success_rate),
            ('Independent', health_record.independent_success_rate),
            ('Network', health_record.network_success_rate)
        ]
        
        for provider_name, rate in provider_rates:
            if rate < 50:  # Less than 50% success rate
                self.log_audit_event(
                    'provider_disabled',
                    'warning',
                    f'{provider_name} provider performance below 50%: {rate:.1f}%',
                    {'provider': provider_name.lower(), 'success_rate': rate}
                )
                self.stdout.write(
                    self.style.WARNING(f'WARNING: {provider_name} provider performance: {rate:.1f}%')
                )
    
    def cleanup_old_logs(self):
        """Clean up old audit logs based on retention policy"""
        try:
            config = QuoteSystemConfiguration.get_config()
            retention_days = config.log_retention_days
        except:
            retention_days = 90  # Default retention
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        deleted_count, _ = QuoteSystemAuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {deleted_count} old audit log entries')
            )
            
            self.log_audit_event(
                'system_maintenance',
                'info',
                f'Cleaned up {deleted_count} audit log entries older than {retention_days} days',
                {'deleted_count': deleted_count, 'retention_days': retention_days}
            )
    
    def generate_health_report(self, health_record):
        """Generate detailed health report"""
        self.stdout.write(self.style.SUCCESS('\n=== QUOTE SYSTEM HEALTH REPORT ==='))
        self.stdout.write(f'Report Time: {health_record.recorded_at}')
        self.stdout.write(f'Overall Health: {health_record.get_system_health_status().upper()}')
        self.stdout.write(f'Success Rate: {health_record.get_overall_success_rate():.1f}%')
        
        self.stdout.write('\n--- Request Metrics (24h) ---')
        self.stdout.write(f'Total Requests: {health_record.total_quote_requests_24h}')
        self.stdout.write(f'Successful: {health_record.successful_quote_requests_24h}')
        self.stdout.write(f'Failed: {health_record.failed_quote_requests_24h}')
        self.stdout.write(f'Quotes Received: {health_record.total_quotes_received_24h}')
        self.stdout.write(f'Avg Response Time: {health_record.average_response_time_hours:.1f}h')
        
        self.stdout.write('\n--- Provider Performance ---')
        self.stdout.write(f'Assessor: {health_record.assessor_success_rate:.1f}%')
        self.stdout.write(f'Dealer: {health_record.dealer_success_rate:.1f}%')
        self.stdout.write(f'Independent: {health_record.independent_success_rate:.1f}%')
        self.stdout.write(f'Network: {health_record.network_success_rate:.1f}%')
        
        self.stdout.write('\n--- System Performance ---')
        self.stdout.write(f'Parts Identification: {health_record.average_parts_identification_time_seconds:.2f}s')
        self.stdout.write(f'Market Calculation: {health_record.average_market_calculation_time_seconds:.2f}s')
        self.stdout.write(f'Recommendation: {health_record.average_recommendation_time_seconds:.2f}s')
        
        self.stdout.write('\n--- Error Summary (24h) ---')
        self.stdout.write(f'API Errors: {health_record.api_errors_24h}')
        self.stdout.write(f'Database Errors: {health_record.database_errors_24h}')
        self.stdout.write(f'Validation Errors: {health_record.validation_errors_24h}')
        
        self.stdout.write('\n--- Data Quality ---')
        self.stdout.write(f'High Confidence Market Averages: {health_record.high_confidence_market_averages}')
        self.stdout.write(f'Low Confidence Market Averages: {health_record.low_confidence_market_averages}')
        self.stdout.write(f'Outlier Quotes Detected: {health_record.outlier_quotes_detected}')
        
        self.stdout.write(self.style.SUCCESS('\n=== END REPORT ===\n'))
    
    def log_audit_event(self, action_type, severity, description, additional_data=None):
        """Log an audit event"""
        QuoteSystemAuditLog.objects.create(
            action_type=action_type,
            severity=severity,
            description=description,
            additional_data=additional_data or {},
            object_type='system',
            object_id='health_monitor'
        )