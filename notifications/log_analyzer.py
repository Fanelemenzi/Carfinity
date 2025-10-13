"""
Log analysis utilities for AutoCare Dashboard Backend
Provides tools to parse, analyze, and generate insights from structured logs
"""
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LogAnalyzer:
    """
    Analyzer for structured JSON logs from the dashboard system
    """
    
    def __init__(self, log_file_path=None):
        self.log_file_path = log_file_path or 'logs/dashboard.log'
        self.security_log_path = 'logs/security.log'
        self.performance_log_path = 'logs/performance.log'
    
    def parse_log_file(self, file_path, start_date=None, end_date=None):
        """
        Parse structured JSON log file and return filtered entries
        """
        entries = []
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line.strip())
                        
                        # Parse timestamp
                        if 'timestamp' in entry:
                            entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                            
                            # Filter by date range if specified
                            if start_date and entry_time < start_date:
                                continue
                            if end_date and entry_time > end_date:
                                continue
                        
                        entries.append(entry)
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON on line {line_num} in {file_path}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error processing line {line_num} in {file_path}: {e}")
                        continue
        
        except FileNotFoundError:
            logger.warning(f"Log file not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
            return []
        
        return entries
    
    def analyze_api_performance(self, start_date=None, end_date=None):
        """
        Analyze API performance metrics from logs
        """
        entries = self.parse_log_file(self.log_file_path, start_date, end_date)
        
        endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_response_time': 0,
            'error_count': 0,
            'slow_requests': 0,
            'cache_hits': 0,
            'database_queries': []
        })
        
        for entry in entries:
            if entry.get('api_endpoint') and 'response_time' in entry:
                endpoint = entry['api_endpoint']
                response_time = entry.get('response_time', 0)
                status_code = entry.get('status_code', 200)
                cache_hit = entry.get('cache_hit', False)
                db_queries = entry.get('database_queries', 0)
                
                stats = endpoint_stats[endpoint]
                stats['count'] += 1
                stats['total_response_time'] += response_time
                
                if status_code >= 400:
                    stats['error_count'] += 1
                
                if response_time > 2000:  # Slow requests > 2 seconds
                    stats['slow_requests'] += 1
                
                if cache_hit:
                    stats['cache_hits'] += 1
                
                if db_queries:
                    stats['database_queries'].append(db_queries)
        
        # Calculate averages and percentages
        performance_summary = {}
        for endpoint, stats in endpoint_stats.items():
            if stats['count'] > 0:
                performance_summary[endpoint] = {
                    'total_requests': stats['count'],
                    'average_response_time_ms': stats['total_response_time'] / stats['count'],
                    'error_rate_percent': (stats['error_count'] / stats['count']) * 100,
                    'slow_request_rate_percent': (stats['slow_requests'] / stats['count']) * 100,
                    'cache_hit_rate_percent': (stats['cache_hits'] / stats['count']) * 100,
                    'average_db_queries': sum(stats['database_queries']) / len(stats['database_queries']) if stats['database_queries'] else 0,
                    'max_db_queries': max(stats['database_queries']) if stats['database_queries'] else 0
                }
        
        return performance_summary
    
    def analyze_security_events(self, start_date=None, end_date=None):
        """
        Analyze security events from logs
        """
        entries = self.parse_log_file(self.security_log_path, start_date, end_date)
        
        security_summary = {
            'total_events': len(entries),
            'events_by_type': Counter(),
            'events_by_severity': Counter(),
            'events_by_user': Counter(),
            'suspicious_patterns': []
        }
        
        for entry in entries:
            event_type = entry.get('security_event', 'unknown')
            severity = entry.get('severity', 'unknown')
            user_id = entry.get('user_id')
            
            security_summary['events_by_type'][event_type] += 1
            security_summary['events_by_severity'][severity] += 1
            
            if user_id:
                security_summary['events_by_user'][user_id] += 1
        
        # Identify suspicious patterns
        for user_id, count in security_summary['events_by_user'].most_common(5):
            if count > 10:  # More than 10 security events
                security_summary['suspicious_patterns'].append({
                    'type': 'high_security_events_user',
                    'user_id': user_id,
                    'event_count': count,
                    'severity': 'medium'
                })
        
        return security_summary
    
    def generate_comprehensive_report(self, start_date=None, end_date=None):
        """
        Generate a comprehensive analysis report
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        report = {
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'api_performance': self.analyze_api_performance(start_date, end_date),
            'security_events': self.analyze_security_events(start_date, end_date),
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def export_report(self, report, output_file, format='json'):
        """
        Export analysis report to file
        """
        try:
            if format == 'json':
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif format == 'text':
                with open(output_file, 'w') as f:
                    f.write(self._format_text_report(report))
            
            logger.info(f"Report exported to {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False
    
    def _format_text_report(self, report):
        """
        Format report as human-readable text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("DASHBOARD LOG ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Analysis Period: {report['analysis_period']['start_date']} to {report['analysis_period']['end_date']}")
        lines.append(f"Duration: {report['analysis_period']['duration_days']} days")
        lines.append("")
        
        # API Performance
        lines.append("API PERFORMANCE SUMMARY")
        lines.append("-" * 40)
        api_perf = report.get('api_performance', {})
        for endpoint, stats in api_perf.items():
            lines.append(f"Endpoint: {endpoint}")
            lines.append(f"  Total Requests: {stats.get('total_requests', 0)}")
            lines.append(f"  Avg Response Time: {stats.get('average_response_time_ms', 0):.2f}ms")
            lines.append(f"  Error Rate: {stats.get('error_rate_percent', 0):.2f}%")
            lines.append(f"  Cache Hit Rate: {stats.get('cache_hit_rate_percent', 0):.2f}%")
            lines.append("")
        
        # Security Events
        lines.append("SECURITY EVENTS SUMMARY")
        lines.append("-" * 40)
        security = report.get('security_events', {})
        lines.append(f"Total Security Events: {security.get('total_events', 0)}")
        lines.append("Events by Type:")
        for event_type, count in security.get('events_by_type', {}).items():
            lines.append(f"  {event_type}: {count}")
        lines.append("")
        
        lines.append(f"Report generated at: {report.get('generated_at', 'Unknown')}")
        
        return "\n".join(lines)