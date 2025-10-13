#!/usr/bin/env python
"""
Test script to verify the dashboard logging system is working correctly
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from notifications.logging_config import DashboardLogger, setup_logging
from notifications.log_analyzer import LogAnalyzer
import logging
import time
import json

def test_structured_logging():
    """
    Test structured logging functionality
    """
    print("Testing structured logging...")
    
    # Initialize logger
    dashboard_logger = DashboardLogger('test')
    
    # Test different types of logging
    print("1. Testing API access logging...")
    dashboard_logger.log_api_access(
        user_id=123,
        endpoint='/notifications/api/dashboard/1/',
        method='GET',
        response_time=250.5,
        status_code=200,
        cache_hit=True
    )
    
    print("2. Testing vehicle access logging...")
    dashboard_logger.log_vehicle_access(
        user_id=123,
        vehicle_id=1,
        action='view_dashboard',
        success=True
    )
    
    print("3. Testing data retrieval logging...")
    dashboard_logger.log_data_retrieval(
        data_type='vehicle_overview',
        user_id=123,
        vehicle_id=1,
        success=True,
        response_time=150.2,
        cache_hit=False
    )
    
    print("4. Testing cache operation logging...")
    dashboard_logger.log_cache_operation(
        operation='get',
        key='dashboard_data_1_123',
        success=True,
        response_time=5.2
    )
    
    print("5. Testing external service call logging...")
    dashboard_logger.log_external_service_call(
        service_name='vehicle_valuation_api',
        success=False,
        response_time=3000.0,
        error_message='Service timeout'
    )
    
    print("6. Testing performance metrics logging...")
    dashboard_logger.log_performance_metrics('database_query', {
        'query_type': 'SELECT',
        'table_name': 'vehicles_vehicle',
        'execution_time_ms': 45.2,
        'query_count': 3
    })
    
    print("7. Testing security event logging...")
    dashboard_logger.log_security_event(
        'rapid_requests',
        user_id=123,
        details={
            'endpoint': '/notifications/api/dashboard/1/',
            'request_count': 15,
            'time_window': '1 minute'
        },
        severity='high'
    )
    
    print("✓ Structured logging tests completed")

def test_log_file_creation():
    """
    Test that log files are created correctly
    """
    print("\nTesting log file creation...")
    
    logs_dir = Path('logs')
    expected_files = [
        'dashboard.log',
        'security.log',
        'performance.log'
    ]
    
    for log_file in expected_files:
        log_path = logs_dir / log_file
        if log_path.exists():
            print(f"✓ {log_file} exists")
            
            # Check if file has content
            if log_path.stat().st_size > 0:
                print(f"  - File has content ({log_path.stat().st_size} bytes)")
                
                # Try to read and parse a few lines
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()[-5:]  # Last 5 lines
                        for line in lines:
                            try:
                                entry = json.loads(line.strip())
                                print(f"  - Valid JSON entry: {entry.get('level', 'N/A')} - {entry.get('message', 'N/A')[:50]}...")
                                break
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"  - Error reading file: {e}")
            else:
                print(f"  - File is empty")
        else:
            print(f"✗ {log_file} does not exist")

def test_log_analyzer():
    """
    Test log analysis functionality
    """
    print("\nTesting log analyzer...")
    
    try:
        analyzer = LogAnalyzer()
        
        # Test parsing log files
        print("1. Testing log file parsing...")
        entries = analyzer.parse_log_file('logs/dashboard.log')
        print(f"   Parsed {len(entries)} log entries")
        
        if entries:
            print("   Sample entry keys:", list(entries[0].keys()))
        
        # Test performance analysis
        print("2. Testing API performance analysis...")
        performance_report = analyzer.analyze_api_performance()
        print(f"   Analyzed {len(performance_report)} endpoints")
        
        for endpoint, stats in list(performance_report.items())[:3]:  # Show first 3
            print(f"   - {endpoint}: {stats.get('total_requests', 0)} requests, "
                  f"{stats.get('average_response_time_ms', 0):.2f}ms avg")
        
        # Test security analysis
        print("3. Testing security event analysis...")
        security_report = analyzer.analyze_security_events()
        print(f"   Found {security_report.get('total_events', 0)} security events")
        
        # Test comprehensive report
        print("4. Testing comprehensive report generation...")
        comprehensive_report = analyzer.generate_comprehensive_report()
        print(f"   Generated report covering {comprehensive_report['analysis_period']['duration_days']} days")
        
        print("✓ Log analyzer tests completed")
        
    except Exception as e:
        print(f"✗ Log analyzer test failed: {e}")

def test_performance_decorators():
    """
    Test performance monitoring decorators
    """
    print("\nTesting performance decorators...")
    
    from notifications.logging_config import log_performance
    
    @log_performance('test_operation')
    def test_function():
        """Test function with performance logging"""
        time.sleep(0.1)  # Simulate some work
        return "test_result"
    
    try:
        result = test_function()
        print(f"✓ Performance decorator test completed: {result}")
    except Exception as e:
        print(f"✗ Performance decorator test failed: {e}")

def main():
    """
    Run all logging system tests
    """
    print("=" * 60)
    print("DASHBOARD LOGGING SYSTEM TEST")
    print("=" * 60)
    
    # Ensure logs directory exists
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Run tests
    test_structured_logging()
    test_log_file_creation()
    test_log_analyzer()
    test_performance_decorators()
    
    print("\n" + "=" * 60)
    print("LOGGING SYSTEM TEST COMPLETED")
    print("=" * 60)
    
    # Show summary
    print("\nTo view the generated logs:")
    print("- Dashboard logs: logs/dashboard.log")
    print("- Security logs: logs/security.log") 
    print("- Performance logs: logs/performance.log")
    
    print("\nTo analyze logs:")
    print("python manage.py monitor_dashboard_health --report-type all --days 1")

if __name__ == '__main__':
    main()