# Parts-Based Quote System - Build Guide

## Overview

The Parts-Based Quote System is a comprehensive solution that replaces static hardcoded cost estimates with a dynamic, multi-provider quote collection system. This guide provides step-by-step instructions for building, deploying, and configuring the system.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Parts-Based Quote System                  │
├─────────────────────────────────────────────────────────────┤
│  Frontend Layer                                             │
│  ├── Parts Review Interface                                 │
│  ├── Quote Request Dispatch                                 │
│  ├── Quote Comparison & Summary                             │
│  └── Admin Dashboard                                        │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer                                       │
│  ├── Parts Identification Engine                            │
│  ├── Quote Request Manager                                  │
│  ├── Market Average Calculator                              │
│  ├── Recommendation Engine                                  │
│  └── Provider Integration Framework                         │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── Quote System Models                                    │
│  ├── Configuration Management                               │
│  ├── Audit Logging                                          │
│  └── Health Monitoring                                      │
├─────────────────────────────────────────────────────────────┤
│  External Integrations                                      │
│  ├── Assessor Estimates (Internal)                          │
│  ├── Authorized Dealers (API/Email)                         │
│  ├── Independent Garages (Platform)                         │
│  └── Insurance Networks (API)                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **Automated Parts Identification**: Scans completed assessments to identify damaged parts
- **Multi-Provider Quote Collection**: Supports 4 provider types with different integration methods
- **Market Analysis**: Calculates statistical averages and identifies outliers
- **Intelligent Recommendations**: AI-powered provider selection based on multiple criteria
- **Comprehensive Admin Interface**: Full configuration and monitoring capabilities
- **Audit Trail**: Complete logging of all system operations
- **Health Monitoring**: Real-time system performance tracking

## Prerequisites

### System Requirements

- **Python**: 3.8+
- **Django**: 4.2+
- **Database**: PostgreSQL 12+ (recommended) or SQLite for development
- **Redis**: 6.0+ (for caching and background tasks)
- **Node.js**: 16+ (for frontend asset compilation)

### Dependencies

```bash
# Core Django packages
Django>=4.2.0
djangorestframework>=3.14.0
django-cors-headers>=4.0.0

# Database
psycopg2-binary>=2.9.0  # PostgreSQL
django-redis>=5.2.0     # Redis caching

# Background tasks
celery>=5.2.0
django-celery-beat>=2.4.0

# API documentation
drf-spectacular>=0.26.0

# Utilities
python-decouple>=3.6
Pillow>=9.0.0
```

### External Services

- **Email Service**: SMTP server for email-based quote requests
- **API Keys**: For external provider integrations
- **Monitoring**: Optional APM service (e.g., Sentry, New Relic)

## Installation Steps

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/carfinity_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Quote System Configuration
QUOTE_SYSTEM_DEBUG=True
QUOTE_SYSTEM_LOG_LEVEL=INFO

# External API Keys
DEALER_API_KEY=your-dealer-api-key
GARAGE_PLATFORM_API_KEY=your-garage-api-key
INSURANCE_NETWORK_API_KEY=your-network-api-key

# Security
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### 3. Install Quote System Components

```bash
# Install the insurance app with quote system
python manage.py collectstatic --noinput

# Install frontend dependencies
npm install

# Build frontend assets
npm run build
```

## Database Setup

### 1. Create Database Schema

```bash
# Create initial migrations
python manage.py makemigrations insurance_app
python manage.py makemigrations assessments

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 2. Initialize Quote System Configuration

```bash
# Initialize system configuration with defaults
python manage.py configure_quote_system --reset-defaults --user admin

# Verify configuration
python manage.py configure_quote_system --show-config
```

### 3. Setup Provider Configurations

```bash
# Configure assessor estimates (internal)
python manage.py configure_quote_system \
    --provider-type assessor \
    --reliability-score 85

# Configure dealer integration
python manage.py configure_quote_system \
    --provider-type dealer \
    --api-endpoint "https://dealer-api.example.com/quotes" \
    --api-key "your-dealer-api-key" \
    --reliability-score 75

# Configure independent garages
python manage.py configure_quote_system \
    --provider-type independent \
    --api-endpoint "https://garage-platform.example.com/api" \
    --api-key "your-garage-api-key" \
    --reliability-score 70

# Configure insurance network
python manage.py configure_quote_system \
    --provider-type network \
    --api-endpoint "https://network-api.example.com/quotes" \
    --api-key "your-network-api-key" \
    --reliability-score 80
```

## Configuration

### 1. System Settings

Configure the quote system through Django admin or management commands:

```bash
# Set labor rate
python manage.py configure_quote_system --labor-rate 45.00

# Set quote expiry period
python manage.py configure_quote_system --quote-expiry-days 7

# Set confidence threshold
python manage.py configure_quote_system --confidence-threshold 70

# Configure recommendation weights
python manage.py configure_quote_system \
    --price-weight 0.40 \
    --quality-weight 0.25 \
    --timeline-weight 0.15
```

### 2. Provider Settings

Enable/disable providers as needed:

```bash
# Enable all providers
python manage.py configure_quote_system \
    --enable-assessor \
    --enable-dealer \
    --enable-independent \
    --enable-network

# Disable specific provider
python manage.py configure_quote_system --disable-dealer
```

### 3. Django Settings

Add to your `settings.py`:

```python
# Quote System Configuration
INSTALLED_APPS = [
    # ... existing apps
    'insurance_app',
    'assessments',
    'rest_framework',
]

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'quote_system': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/quote_system.log',
        },
    },
    'loggers': {
        'quote_system': {
            'handlers': ['quote_system'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Quote System Specific Settings
QUOTE_SYSTEM_SETTINGS = {
    'DEFAULT_LABOR_RATE': 45.00,
    'DEFAULT_QUOTE_EXPIRY_DAYS': 7,
    'ENABLE_PERFORMANCE_LOGGING': True,
    'ENABLE_HEALTH_MONITORING': True,
    'LOG_RETENTION_DAYS': 90,
}
```

## Testing

### 1. Run Unit Tests

```bash
# Run all quote system tests
python manage.py test insurance_app.tests_*

# Run specific test modules
python manage.py test insurance_app.tests_parts_identification
python manage.py test insurance_app.tests_quote_managers
python manage.py test insurance_app.tests_market_analysis
python manage.py test insurance_app.tests_recommendation_engine
python manage.py test insurance_app.tests_api_views

# Run assessment integration tests
python manage.py test assessments.tests_parts_quote_integration
python manage.py test assessments.tests_workflow_integration
```

### 2. Integration Testing

```bash
# Test quote collection workflow
python manage.py test_quote_collection

# Test provider integrations
python manage.py test insurance_app.tests_provider_integrations

# Test API endpoints
python manage.py test insurance_app.tests_api_views
```

### 3. Manual Testing

1. **Create Test Assessment**:
   - Navigate to `/admin/assessments/vehicleassessment/`
   - Create a new assessment with damaged parts

2. **Test Parts Identification**:
   - Complete the assessment
   - Verify parts are automatically identified
   - Check parts in `/admin/insurance_app/damagedpart/`

3. **Test Quote Request**:
   - Navigate to assessment detail page
   - Click "Review Parts" button
   - Select providers and dispatch quotes

4. **Test Market Analysis**:
   - Add multiple quotes for the same part
   - Verify market averages are calculated
   - Check for outlier detection

5. **Test Recommendations**:
   - Ensure multiple quotes exist
   - Generate recommendations
   - Verify recommendation logic

## Deployment

### 1. Production Environment Setup

```bash
# Set production environment variables
export DEBUG=False
export QUOTE_SYSTEM_DEBUG=False
export DATABASE_URL=postgresql://prod_user:password@prod_host:5432/prod_db

# Collect static files
python manage.py collectstatic --noinput

# Apply migrations
python manage.py migrate --no-input
```

### 2. Web Server Configuration

**Nginx Configuration** (`/etc/nginx/sites-available/carfinity`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/your/project/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/your/project/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Gunicorn Configuration** (`gunicorn.conf.py`):

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

### 3. Background Tasks Setup

**Celery Worker Configuration**:

```bash
# Start Celery worker
celery -A carfinity worker --loglevel=info

# Start Celery beat (scheduler)
celery -A carfinity beat --loglevel=info

# For production, use supervisor or systemd
```

**Systemd Service** (`/etc/systemd/system/carfinity-celery.service`):

```ini
[Unit]
Description=Carfinity Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/path/to/your/project/.env
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/your/venv/bin/celery -A carfinity worker --detach --loglevel=info
ExecStop=/path/to/your/venv/bin/celery -A carfinity control shutdown
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Health Monitoring Setup

```bash
# Setup cron job for health monitoring
crontab -e

# Add this line to run health monitoring every hour
0 * * * * /path/to/your/venv/bin/python /path/to/your/project/manage.py monitor_quote_system_health

# For detailed reporting, run daily
0 6 * * * /path/to/your/venv/bin/python /path/to/your/project/manage.py monitor_quote_system_health --generate-report --cleanup-logs
```

## Monitoring & Maintenance

### 1. System Health Monitoring

**Daily Health Checks**:

```bash
# Check system health
python manage.py monitor_quote_system_health --generate-report

# Check configuration
python manage.py configure_quote_system --show-config

# Verify provider status
python manage.py shell -c "
from insurance_app.models import ProviderConfiguration
for p in ProviderConfiguration.objects.all():
    print(f'{p.provider_type}: {\"Enabled\" if p.is_enabled else \"Disabled\"} - {p.reliability_score}%')
"
```

**Performance Monitoring**:

```bash
# Monitor quote request success rates
python manage.py shell -c "
from insurance_app.models import QuoteSystemHealthMetrics
latest = QuoteSystemHealthMetrics.objects.latest('recorded_at')
print(f'Success Rate: {latest.get_overall_success_rate():.1f}%')
print(f'System Health: {latest.get_system_health_status()}')
"
```

### 2. Log Management

**Log Rotation** (`/etc/logrotate.d/carfinity-quotes`):

```
/path/to/your/project/logs/quote_system.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}
```

**Log Cleanup**:

```bash
# Automated cleanup via management command
python manage.py monitor_quote_system_health --cleanup-logs

# Manual cleanup of old audit logs
python manage.py shell -c "
from insurance_app.models import QuoteSystemAuditLog
from django.utils import timezone
from datetime import timedelta
cutoff = timezone.now() - timedelta(days=90)
deleted = QuoteSystemAuditLog.objects.filter(timestamp__lt=cutoff).delete()
print(f'Deleted {deleted[0]} old audit log entries')
"
```

### 3. Database Maintenance

**Regular Maintenance Tasks**:

```bash
# Recalculate market averages
python manage.py shell -c "
from insurance_app.models import DamagedPart
from insurance_app.market_analysis import MarketAverageCalculator
calculator = MarketAverageCalculator()
for part in DamagedPart.objects.filter(quotes__isnull=False).distinct():
    try:
        calculator.calculate_market_average(part)
        print(f'Updated market average for {part.part_name}')
    except Exception as e:
        print(f'Error updating {part.part_name}: {e}')
"

# Clean up expired quotes
python manage.py shell -c "
from insurance_app.models import PartQuote
from django.utils import timezone
expired = PartQuote.objects.filter(valid_until__lt=timezone.now())
print(f'Found {expired.count()} expired quotes')
"
```

## Troubleshooting

### Common Issues

#### 1. Parts Not Being Identified

**Symptoms**: No damaged parts created after assessment completion

**Solutions**:
```bash
# Check if parts identification is enabled
python manage.py shell -c "
from assessments.models import VehicleAssessment
assessment = VehicleAssessment.objects.latest('id')
print(f'Uses parts-based quotes: {assessment.uses_parts_based_quotes}')
print(f'Parts identification complete: {assessment.parts_identification_complete}')
"

# Manually trigger parts identification
python manage.py shell -c "
from insurance_app.parts_identification import PartsIdentificationEngine
from assessments.models import VehicleAssessment
engine = PartsIdentificationEngine()
assessment = VehicleAssessment.objects.get(id=YOUR_ASSESSMENT_ID)
parts = engine.identify_damaged_parts(assessment)
print(f'Identified {len(parts)} parts')
"
```

#### 2. Quote Requests Not Dispatching

**Symptoms**: Quote requests stuck in 'pending' status

**Solutions**:
```bash
# Check provider configurations
python manage.py configure_quote_system --show-config

# Check for API errors in logs
tail -f logs/quote_system.log | grep ERROR

# Manually test provider integration
python manage.py shell -c "
from insurance_app.provider_integrations import AssessorEstimateGenerator
generator = AssessorEstimateGenerator()
# Test with a sample part
"
```

#### 3. Market Averages Not Calculating

**Symptoms**: No market average data for parts with multiple quotes

**Solutions**:
```bash
# Check minimum quotes requirement
python manage.py shell -c "
from insurance_app.models import QuoteSystemConfiguration
config = QuoteSystemConfiguration.get_config()
print(f'Minimum quotes required: {config.minimum_quotes_required}')
"

# Manually calculate market averages
python manage.py shell -c "
from insurance_app.models import DamagedPart
from insurance_app.market_analysis import MarketAverageCalculator
calculator = MarketAverageCalculator()
part = DamagedPart.objects.get(id=YOUR_PART_ID)
try:
    avg = calculator.calculate_market_average(part)
    print(f'Market average: £{avg.average_total_cost}')
except Exception as e:
    print(f'Error: {e}')
"
```

#### 4. Recommendations Not Generating

**Symptoms**: No recommendations available for assessments with quotes

**Solutions**:
```bash
# Check recommendation engine configuration
python manage.py shell -c "
from insurance_app.models import QuoteSystemConfiguration
config = QuoteSystemConfiguration.get_config()
total_weight = config.price_weight + config.quality_weight + config.timeline_weight + config.warranty_weight + config.reliability_weight
print(f'Total recommendation weights: {total_weight} (should be 1.00)')
"

# Manually generate recommendations
python manage.py shell -c "
from insurance_app.recommendation_engine import QuoteRecommendationEngine
from assessments.models import VehicleAssessment
engine = QuoteRecommendationEngine()
assessment = VehicleAssessment.objects.get(id=YOUR_ASSESSMENT_ID)
recommendations = engine.generate_assessment_recommendations(assessment)
print(f'Generated {len(recommendations)} recommendations')
"
```

### Performance Issues

#### 1. Slow Quote Processing

**Diagnosis**:
```bash
# Check system performance metrics
python manage.py monitor_quote_system_health --generate-report

# Monitor database queries
python manage.py shell -c "
from django.db import connection
from django.conf import settings
settings.DEBUG = True
# Run your quote operations
print(f'Database queries: {len(connection.queries)}')
"
```

**Solutions**:
- Enable database query optimization
- Add database indexes for frequently queried fields
- Implement caching for market averages
- Use background tasks for heavy operations

#### 2. High Memory Usage

**Diagnosis**:
```bash
# Monitor memory usage
ps aux | grep python
top -p $(pgrep -f "manage.py")
```

**Solutions**:
- Implement pagination for large datasets
- Use select_related and prefetch_related for database queries
- Clear unused objects from memory
- Optimize image processing for damage photos

### API Integration Issues

#### 1. Provider API Timeouts

**Solutions**:
```bash
# Increase timeout settings
python manage.py configure_quote_system \
    --provider-type dealer \
    --api-timeout 60

# Check network connectivity
curl -I https://dealer-api.example.com/quotes
```

#### 2. Authentication Failures

**Solutions**:
```bash
# Update API keys
python manage.py configure_quote_system \
    --provider-type dealer \
    --api-key "new-api-key"

# Test authentication
python manage.py shell -c "
from insurance_app.provider_integrations import DealerIntegration
integration = DealerIntegration()
result = integration.test_connection()
print(f'Connection test: {result}')
"
```

## Security Considerations

### 1. API Security

- Store API keys in environment variables, not in code
- Use HTTPS for all external API communications
- Implement rate limiting for API endpoints
- Validate all incoming quote data
- Log all API interactions for audit purposes

### 2. Data Protection

- Encrypt sensitive quote data in database
- Implement proper user authentication and authorization
- Use CSRF protection for all forms
- Sanitize all user inputs
- Regular security audits of quote system

### 3. Access Control

```python
# Example permission classes for API views
from rest_framework.permissions import BasePermission

class QuoteSystemPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('insurance_app.view_partquote')
    
    def has_object_permission(self, request, view, obj):
        # Only allow access to quotes for user's organization
        return obj.quote_request.assessment.organization == request.user.organization
```

## Backup and Recovery

### 1. Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump carfinity_db > /backups/carfinity_${DATE}.sql
gzip /backups/carfinity_${DATE}.sql

# Keep only last 30 days of backups
find /backups -name "carfinity_*.sql.gz" -mtime +30 -delete
```

### 2. Configuration Backup

```bash
# Backup system configuration
python manage.py dumpdata insurance_app.QuoteSystemConfiguration insurance_app.ProviderConfiguration > config_backup.json

# Restore configuration
python manage.py loaddata config_backup.json
```

### 3. Recovery Procedures

1. **Database Recovery**:
   ```bash
   # Stop application
   systemctl stop carfinity
   
   # Restore database
   dropdb carfinity_db
   createdb carfinity_db
   gunzip -c /backups/carfinity_YYYYMMDD_HHMMSS.sql.gz | psql carfinity_db
   
   # Restart application
   systemctl start carfinity
   ```

2. **Configuration Recovery**:
   ```bash
   # Reset to defaults and restore
   python manage.py configure_quote_system --reset-defaults
   python manage.py loaddata config_backup.json
   ```

## Conclusion

This build guide provides comprehensive instructions for implementing, deploying, and maintaining the Parts-Based Quote System. The system is designed to be robust, scalable, and maintainable with proper monitoring and configuration management.

For additional support:
- Check the system logs in `logs/quote_system.log`
- Use the Django admin interface for configuration
- Run health monitoring commands regularly
- Follow the troubleshooting guide for common issues

The system includes extensive logging and monitoring capabilities to help identify and resolve issues quickly. Regular maintenance and monitoring will ensure optimal performance and reliability.