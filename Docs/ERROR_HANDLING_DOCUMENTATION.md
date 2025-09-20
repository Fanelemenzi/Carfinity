# Error Handling and User Feedback System Documentation

## Overview

This document describes the comprehensive error handling and user feedback system implemented for the group-based authentication system. The system provides consistent, user-friendly error messages, comprehensive logging, and proper guidance for users experiencing access issues.

## Components

### 1. Error Handlers (`error_handlers.py`)

The main error handling module provides centralized error processing and user feedback.

#### Key Classes:

- **`ErrorType`**: Constants for different error types
- **`SecurityEventLogger`**: Handles logging of security events and access violations
- **`ErrorMessageGenerator`**: Generates user-friendly error messages and suggestions
- **`AuthenticationErrorHandler`**: Main error handler for authentication and authorization errors
- **`UserGuidanceProvider`**: Provides specific guidance based on user's current state

#### Error Types:

- `NO_AUTHENTICATION`: User not logged in
- `NO_GROUPS`: User has no group assignments
- `NO_ORGANIZATION`: User not associated with any organization
- `GROUP_ORG_MISMATCH`: Mismatch between user groups and organization type
- `ACCESS_DENIED`: General access denied
- `INVALID_PERMISSIONS`: Invalid permission configuration
- `SYSTEM_ERROR`: Unexpected system errors
- `SESSION_EXPIRED`: Session timeout/expiration

### 2. Error Templates

#### `templates/errors/access_denied.html`
- Enhanced version of the original access denied template
- Uses new error context variables
- Displays error IDs for support
- Conditional action buttons based on error type

#### `templates/errors/system_error.html`
- Template for system errors
- Includes error ID for support tracking
- Retry functionality for recoverable errors

#### `templates/errors/no_groups.html`
- Specific template for users with no group assignments
- Step-by-step guidance for resolution
- Contact information for administrators

#### `templates/errors/no_organization.html`
- Specific template for users with no organization assignments
- Information about organization types
- Clear next steps for users

### 3. Middleware (`middleware.py`)

#### `AuthenticationErrorMiddleware`
- Catches authentication-related exceptions globally
- Provides consistent error handling across the application
- Logs security events automatically

#### `SessionSecurityMiddleware`
- Handles session security and timeout
- Detects session tampering
- Adds security headers to responses

#### `RequestLoggingMiddleware`
- Logs requests to sensitive endpoints
- Monitors authentication-related activities
- Tracks error responses

### 4. Updated Permission Decorators (`permissions.py`)

Enhanced permission decorators now use the new error handling system:

- `@require_group(group_name)`
- `@require_any_group(group_names)`
- `@require_organization_type(org_type)`
- `@require_dashboard_access(dashboard_name)`
- `@check_permission_conflicts`

All decorators now:
- Use `SecurityEventLogger` for consistent logging
- Use `AuthenticationErrorHandler` for consistent responses
- Provide detailed error context

### 5. Logging Configuration (`logging_config.py`)

Comprehensive logging setup for security and authentication events:

- **Security Logger**: Logs access violations, permission conflicts, security events
- **Authentication Logger**: Logs login attempts, authentication events
- **File Handlers**: Separate log files for security and authentication events
- **Console Handlers**: Development-time console output

#### Log Files:
- `logs/security.log`: Security events and access violations
- `logs/authentication.log`: Authentication attempts and events

### 6. Updated Views (`views.py`)

Enhanced views with new error handling:

- `access_denied()`: Uses new error handling system
- `no_groups_error()`: Specific view for no groups scenario
- `no_organization_error()`: Specific view for no organization scenario
- `system_error()`: View for system errors
- `login_user()`: Enhanced with security logging

## Usage Examples

### 1. Using Error Handlers in Views

```python
from users.error_handlers import AuthenticationErrorHandler, ErrorType

def my_view(request):
    if not request.user.is_authenticated:
        return AuthenticationErrorHandler.handle_access_denied(
            request, ErrorType.NO_AUTHENTICATION
        )
    
    # View logic here
```

### 2. Using Permission Decorators

```python
from users.permissions import require_group, check_permission_conflicts

@require_group('customers')
@check_permission_conflicts
def customer_dashboard(request):
    # Dashboard logic here
```

### 3. Logging Security Events

```python
from users.error_handlers import SecurityEventLogger, ErrorType

# Log access denied
SecurityEventLogger.log_access_denied(
    user=request.user,
    requested_resource=request.path,
    error_type=ErrorType.ACCESS_DENIED,
    additional_info={'custom': 'data'}
)

# Log authentication attempt
SecurityEventLogger.log_authentication_attempt(
    username='user123',
    success=True,
    ip_address='192.168.1.1'
)
```

### 4. Custom Error Messages

```python
from users.error_handlers import ErrorMessageGenerator

context = ErrorMessageGenerator.get_error_context(
    ErrorType.NO_GROUPS,
    user=request.user,
    custom_message="Your account needs group assignment."
)
```

## Configuration

### 1. URL Configuration

Add error handling URLs to your `urls.py`:

```python
urlpatterns = [
    path('access-denied/', views.access_denied, name='access_denied'),
    path('no-groups/', views.no_groups_error, name='no_groups_error'),
    path('no-organization/', views.no_organization_error, name='no_organization_error'),
    path('system-error/', views.system_error, name='system_error'),
]
```

### 2. Middleware Configuration

Add middleware to your Django settings:

```python
MIDDLEWARE = [
    # ... other middleware
    'users.middleware.AuthenticationErrorMiddleware',
    'users.middleware.SessionSecurityMiddleware',
    'users.middleware.RequestLoggingMiddleware',
]
```

### 3. Logging Configuration

Add logging configuration to your Django settings:

```python
from users.logging_config import LOGGING_CONFIG

LOGGING = LOGGING_CONFIG
```

Or call the setup function in your Django app's ready method:

```python
from users.logging_config import setup_logging

def ready(self):
    setup_logging()
```

## Testing

### Management Command

Use the test management command to verify the error handling system:

```bash
# Test all scenarios
python manage.py test_error_handling

# Test specific scenario
python manage.py test_error_handling --scenario no_groups
```

### Available Test Scenarios:
- `all`: Test all scenarios
- `no_auth`: Test unauthenticated user handling
- `no_groups`: Test users with no group assignments
- `no_org`: Test users with no organization assignments
- `conflicts`: Test permission conflicts
- `logging`: Test logging system

## Security Considerations

### 1. Information Disclosure
- Error messages are user-friendly but don't reveal sensitive system information
- Detailed error information is logged securely for administrators
- Error IDs allow support to track issues without exposing details to users

### 2. Logging Security
- Security events are logged with appropriate detail levels
- Log files are stored securely and should be protected
- IP addresses and user agents are logged for security monitoring

### 3. Session Security
- Session tampering detection
- Automatic session invalidation on security violations
- Security headers added to responses

## Maintenance

### 1. Log File Management
- Monitor log file sizes and implement rotation
- Regularly review security logs for suspicious activity
- Archive old logs according to your retention policy

### 2. Error Message Updates
- Review error messages periodically for clarity
- Update contact information in templates as needed
- Add new error types as the system evolves

### 3. Performance Monitoring
- Monitor the performance impact of logging
- Adjust log levels in production as needed
- Consider async logging for high-traffic applications

## Troubleshooting

### Common Issues:

1. **Log files not created**
   - Check directory permissions for `logs/` folder
   - Verify logging configuration is properly loaded
   - Check Django settings for logging configuration

2. **Error templates not found**
   - Verify template paths in `templates/errors/`
   - Check Django template settings
   - Ensure templates extend the correct base template

3. **Middleware not working**
   - Verify middleware is added to Django settings
   - Check middleware order (should be after authentication middleware)
   - Ensure middleware classes are properly imported

4. **Permission decorators not working**
   - Check that decorators are applied in correct order
   - Verify user groups and organization assignments
   - Check that required services are properly configured

## Integration with Existing Code

The error handling system is designed to integrate seamlessly with existing code:

1. **Backward Compatibility**: Existing error handling continues to work
2. **Gradual Migration**: Views can be updated incrementally to use new system
3. **Fallback Handling**: System gracefully handles missing configurations
4. **Flexible Configuration**: Error messages and templates can be customized

## Future Enhancements

Potential improvements to consider:

1. **Internationalization**: Multi-language error messages
2. **User Notifications**: Email notifications for security events
3. **Dashboard Integration**: Admin dashboard for monitoring errors
4. **API Error Handling**: Extend system for API endpoints
5. **Automated Recovery**: Self-healing for certain error conditions