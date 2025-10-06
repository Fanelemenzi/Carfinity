"""
Management command to analyze dashboard logs and generate reports
"""
from django.core.management.base import BaseCommand
from notifications.log_analyzer import LogAnalyzer
from datetime import datetime, timedelta
import json


class Command(BaseCommand):
    help = 'Analyze dashboard logs and generate performance/security reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        
        parser.add_argument(
            '--output',
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
        
        parser.add_argument(
            '--type',
            type=str,
            choices=['performance', 'security', 'all'],
            default='all',
            help='Type of analysis to perform (default: all)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        output_file = options.get('output')
        output_format = options['format']
        analysis_type = options['type']
        
        self.stdout.write(f"Analyzing logs for the last {days} days...")
        
        # Initialize analyzer
        analyzer = LogAnalyzer()
        
        # Set date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate report based on type
        if analysis_type == 'all':
            report = analyzer.generate_comprehensive_report(start_date, end_date)
        elif analysis_type == 'performance':
            report = {
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_days': days
                },
                'api_performance': analyzer.analyze_api_performance(start_date, end_date),
                'generated_at': datetime.now().isoformat()
            }
        elif analysis_type == 'security':
            report = {
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_days': days
                },
                'security_events': analyzer.analyze_security_events(start_date, end_date),
                'generated_at': datetime.now().isoformat()
            }
        
        # Output report
        if output_file:
            success = analyzer.export_report(report, output_file, output_format)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Report saved to {output_file}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to save report to {output_file}')
                )
        else:
            # Print to console
            if output_format == 'json':
                self.stdout.write(json.dumps(report, indent=2, default=str))
            else:
                self.stdout.write(analyzer._format_text_report(report))
        
        # Show summary
        if analysis_type in ['all', 'performance']:
            api_perf = report.get('api_performance', {})
            if api_perf:
                self.stdout.write(f"\nPerformance Summary:")
                self.stdout.write(f"- Analyzed {len(api_perf)} endpoints")
                
                total_requests = sum(stats.get('total_requests', 0) for stats in api_perf.values())
                self.stdout.write(f"- Total requests: {total_requests}")
                
                if total_requests > 0:
                    avg_response_time = sum(
                        stats.get('average_response_time_ms', 0) * stats.get('total_requests', 0)
                        for stats in api_perf.values()
                    ) / total_requests
                    self.stdout.write(f"- Overall average response time: {avg_response_time:.2f}ms")
        
        if analysis_type in ['all', 'security']:
            security = report.get('security_events', {})
            if security:
                self.stdout.write(f"\nSecurity Summary:")
                self.stdout.write(f"- Total security events: {security.get('total_events', 0)}")
                
                suspicious_patterns = security.get('suspicious_patterns', [])
                if suspicious_patterns:
                    self.stdout.write(f"- Suspicious patterns detected: {len(suspicious_patterns)}")
                    for pattern in suspicious_patterns[:3]:  # Show first 3
                        self.stdout.write(f"  - {pattern.get('type', 'Unknown')}: {pattern.get('severity', 'Unknown')} severity")
        
        self.stdout.write(
            self.style.SUCCESS(f'\nLog analysis completed for {days} days')
        )