"""
Management command to monitor dashboard health and generate performance reports
"""
import os
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from notifications.models import VehicleAlert, VehicleCostAnalytics
from vehicles.models import Vehicle
from maintenance_history.models import MaintenanceRecord
from notifications.logging_config import DashboardLogger
import logging

logger = logging.getLogger(__name__)
dashboard_logger = DashboardLogger('health_monitor')


class Command(BaseCommand):
    help = 'Monitor dashboard health and generate performance reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['performance', 'security', 'health', 'all'],
            default='all',
            help='Type of report to generate'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path for the report'
        )
        
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'text'],
            default='text',
            help='Output format (default: text)'
        )
    
    def handle(self, *args, **options):
        """
        Main command handler
        """
        report_type = options['report_type']
        days = options['days']
        output_file = options.get('output_file')
        output_format = options['format']
        
        self.stdout.write(f"Generating {report_type} report for the last {days} days...")
        
        # Generate the requested report
        if report_type == 'all':
            report_data = {
                'performance': self.generate_performance_report(days),
                'security': self.generate_security_report(days),
                'health': self.generate_health_report(days),
                'generated_at': timezone.now().isoformat()
            }
        elif report_type == 'performance':
            report_data = self.generate_performance_report(days)
        elif report_type == 'security':
            report_data = self.generate_security_report(days)
        elif report_type == 'health':
            report_data = self.generate_health_report(days)
        
        # Output the report
        if output_format == 'json':
            report_output = json.dumps(report_data, indent=2, default=str)
        else:
            report_output = self.format_text_report(report_data, report_type)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_output)
            self.stdout.write(f"Report saved to {output_file}")
        else:
            self.stdout.write(report_output)
        
        # Log the report generation
        dashboard_logger.log_performance_metrics('health_report_generated', {
            'report_type': report_type,
            'days_analyzed': days,
            'output_format': output_format,
            'output_file': output_file
        })
    
    def generate_performance_report(self, days):
        """
        Generate performance metrics report
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Database performance metrics
        db_metrics = self.get_database_metrics()
        
        # Cache performance metrics
        cache_metrics = self.get_cache_metrics()
        
        # API performance metrics (would need to be collected from logs)
        api_metrics = self.get_api_metrics(start_date, end_date)
        
        # System resource usage
        system_metrics = self.get_system_metrics()
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'database': db_metrics,
            'cache': cache_metrics,
            'api': api_metrics,
            'system': system_metrics
        }
    
    def generate_security_report(self, days):
        """
        Generate security monitoring report
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Security events (would need to be collected from logs)
        security_events = self.get_security_events(start_date, end_date)
        
        # Failed authentication attempts
        auth_failures = self.get_auth_failures(start_date, end_date)
        
        # Suspicious activity patterns
        suspicious_activity = self.get_suspicious_activity(start_date, end_date)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'security_events': security_events,
            'authentication_failures': auth_failures,
            'suspicious_activity': suspicious_activity
        }
    
    def generate_health_report(self, days):
        """
        Generate overall system health report
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # System health indicators
        health_indicators = {
            'database_health': self.check_database_health(),
            'cache_health': self.check_cache_health(),
            'application_health': self.check_application_health(),
            'data_integrity': self.check_data_integrity()
        }
        
        # Recent alerts and issues
        recent_alerts = self.get_recent_system_alerts(start_date, end_date)
        
        # Performance trends
        performance_trends = self.get_performance_trends(start_date, end_date)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'health_indicators': health_indicators,
            'recent_alerts': recent_alerts,
            'performance_trends': performance_trends,
            'overall_status': self.calculate_overall_health_status(health_indicators)
        }
    
    def get_database_metrics(self):
        """
        Get database performance metrics
        """
        try:
            with connection.cursor() as cursor:
                # Get table sizes and row counts
                cursor.execute("""
                    SELECT 
                        table_name,
                        table_rows,
                        data_length,
                        index_length
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE()
                    AND table_name IN (
                        'vehicles_vehicle',
                        'maintenance_history_maintenancerecord',
                        'notifications_vehiclealert',
                        'notifications_vehiclecostanalytics'
                    )
                """)
                
                table_stats = []
                for row in cursor.fetchall():
                    table_stats.append({
                        'table_name': row[0],
                        'row_count': row[1] or 0,
                        'data_size_mb': (row[2] or 0) / 1024 / 1024,
                        'index_size_mb': (row[3] or 0) / 1024 / 1024
                    })
                
                return {
                    'connection_status': 'healthy',
                    'table_statistics': table_stats,
                    'total_queries_today': len(connection.queries)
                }
        
        except Exception as e:
            logger.error(f"Error getting database metrics: {str(e)}")
            return {
                'connection_status': 'error',
                'error': str(e)
            }
    
    def get_cache_metrics(self):
        """
        Get cache performance metrics
        """
        try:
            # Test cache connectivity
            test_key = 'health_check_test'
            cache.set(test_key, 'test_value', 60)
            test_result = cache.get(test_key)
            cache.delete(test_key)
            
            cache_status = 'healthy' if test_result == 'test_value' else 'degraded'
            
            return {
                'status': cache_status,
                'connectivity': 'ok' if test_result else 'failed'
            }
        
        except Exception as e:
            logger.error(f"Error getting cache metrics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_api_metrics(self, start_date, end_date):
        """
        Get API performance metrics (placeholder - would need log analysis)
        """
        # In a real implementation, this would analyze log files
        # For now, return placeholder data
        return {
            'total_requests': 'N/A - requires log analysis',
            'average_response_time': 'N/A - requires log analysis',
            'error_rate': 'N/A - requires log analysis',
            'slow_requests': 'N/A - requires log analysis'
        }
    
    def get_system_metrics(self):
        """
        Get system resource metrics
        """
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                'disk_usage_percent': disk.percent,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024
            }
        
        except ImportError:
            return {
                'error': 'psutil not installed - cannot get system metrics'
            }
        except Exception as e:
            return {
                'error': f'Error getting system metrics: {str(e)}'
            }
    
    def get_security_events(self, start_date, end_date):
        """
        Get security events (placeholder - would need log analysis)
        """
        return {
            'failed_login_attempts': 'N/A - requires log analysis',
            'access_denied_events': 'N/A - requires log analysis',
            'suspicious_activity_alerts': 'N/A - requires log analysis'
        }
    
    def get_auth_failures(self, start_date, end_date):
        """
        Get authentication failure metrics
        """
        return {
            'total_failures': 'N/A - requires log analysis',
            'unique_ips': 'N/A - requires log analysis',
            'blocked_ips': 'N/A - requires log analysis'
        }
    
    def get_suspicious_activity(self, start_date, end_date):
        """
        Get suspicious activity patterns
        """
        return {
            'rapid_request_patterns': 'N/A - requires log analysis',
            'unusual_access_patterns': 'N/A - requires log analysis',
            'potential_attacks': 'N/A - requires log analysis'
        }
    
    def check_database_health(self):
        """
        Check database health indicators
        """
        try:
            # Test basic connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            # Check for recent maintenance records
            recent_records = MaintenanceRecord.objects.filter(
                date_performed__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            return {
                'status': 'healthy',
                'connectivity': 'ok',
                'recent_maintenance_records': recent_records
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_cache_health(self):
        """
        Check cache health indicators
        """
        try:
            # Test cache operations
            test_key = 'health_check_cache'
            cache.set(test_key, {'test': True}, 60)
            result = cache.get(test_key)
            cache.delete(test_key)
            
            return {
                'status': 'healthy' if result else 'degraded',
                'read_write_test': 'passed' if result else 'failed'
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_application_health(self):
        """
        Check application-specific health indicators
        """
        try:
            # Check for active alerts
            active_alerts = VehicleAlert.objects.filter(is_active=True).count()
            
            # Check for recent cost analytics
            recent_analytics = VehicleCostAnalytics.objects.filter(
                month__gte=timezone.now().date().replace(day=1) - timedelta(days=30)
            ).count()
            
            # Check for vehicles with recent activity
            active_vehicles = Vehicle.objects.filter(
                maintenance_history__date_performed__gte=timezone.now() - timedelta(days=30)
            ).distinct().count()
            
            return {
                'status': 'healthy',
                'active_alerts': active_alerts,
                'recent_cost_analytics': recent_analytics,
                'active_vehicles': active_vehicles
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_data_integrity(self):
        """
        Check data integrity indicators
        """
        try:
            # Check for orphaned records
            orphaned_alerts = VehicleAlert.objects.filter(vehicle__isnull=True).count()
            orphaned_analytics = VehicleCostAnalytics.objects.filter(vehicle__isnull=True).count()
            
            # Check for data consistency
            vehicles_with_maintenance = Vehicle.objects.filter(
                maintenance_history__isnull=False
            ).distinct().count()
            
            total_vehicles = Vehicle.objects.count()
            
            return {
                'status': 'healthy' if orphaned_alerts == 0 and orphaned_analytics == 0 else 'warning',
                'orphaned_alerts': orphaned_alerts,
                'orphaned_analytics': orphaned_analytics,
                'vehicles_with_maintenance': vehicles_with_maintenance,
                'total_vehicles': total_vehicles,
                'maintenance_coverage_percent': (vehicles_with_maintenance / total_vehicles * 100) if total_vehicles > 0 else 0
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_recent_system_alerts(self, start_date, end_date):
        """
        Get recent system alerts and issues
        """
        try:
            # Get high priority vehicle alerts
            high_priority_alerts = VehicleAlert.objects.filter(
                priority='HIGH',
                created_at__gte=start_date,
                is_active=True
            ).count()
            
            # Get overdue maintenance items
            from maintenance.models import ScheduledMaintenance
            overdue_maintenance = ScheduledMaintenance.objects.filter(
                status='OVERDUE',
                due_date__gte=start_date.date()
            ).count()
            
            return {
                'high_priority_alerts': high_priority_alerts,
                'overdue_maintenance_items': overdue_maintenance
            }
        
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def get_performance_trends(self, start_date, end_date):
        """
        Get performance trends over the specified period
        """
        # Placeholder - would need historical performance data
        return {
            'response_time_trend': 'N/A - requires historical data',
            'database_query_trend': 'N/A - requires historical data',
            'cache_hit_rate_trend': 'N/A - requires historical data'
        }
    
    def calculate_overall_health_status(self, health_indicators):
        """
        Calculate overall system health status
        """
        statuses = []
        for indicator, data in health_indicators.items():
            if isinstance(data, dict) and 'status' in data:
                statuses.append(data['status'])
        
        if 'error' in statuses:
            return 'critical'
        elif 'warning' in statuses or 'degraded' in statuses:
            return 'warning'
        elif all(status == 'healthy' for status in statuses):
            return 'healthy'
        else:
            return 'unknown'
    
    def format_text_report(self, report_data, report_type):
        """
        Format report data as human-readable text
        """
        output = []
        output.append("=" * 60)
        output.append(f"Dashboard Health Report - {report_type.upper()}")
        output.append("=" * 60)
        output.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        
        if report_type == 'all':
            for section, data in report_data.items():
                if section != 'generated_at':
                    output.append(f"\n{section.upper()} REPORT:")
                    output.append("-" * 40)
                    output.extend(self._format_section_data(data))
        else:
            output.extend(self._format_section_data(report_data))
        
        return "\n".join(output)
    
    def _format_section_data(self, data, indent=0):
        """
        Recursively format section data
        """
        output = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                output.append(f"{indent_str}{key}:")
                output.extend(self._format_section_data(value, indent + 1))
            elif isinstance(value, list):
                output.append(f"{indent_str}{key}: {len(value)} items")
                for i, item in enumerate(value[:5]):  # Show first 5 items
                    if isinstance(item, dict):
                        output.append(f"{indent_str}  [{i+1}]:")
                        output.extend(self._format_section_data(item, indent + 2))
                    else:
                        output.append(f"{indent_str}  [{i+1}] {item}")
                if len(value) > 5:
                    output.append(f"{indent_str}  ... and {len(value) - 5} more")
            else:
                output.append(f"{indent_str}{key}: {value}")
        
        return output