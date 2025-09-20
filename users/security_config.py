"""
Security configuration for the group-based authentication system.

This module provides comprehensive security settings including session management,
CSRF protection, permission re-verification, and security logging.
"""

import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
import hashlib

# Get security logger
security_logger = logging.getLogger('security')
auth_logger = logging.getLogger('authentication')


class SecurityConfig:
    """Central configuration for security settings"""
    
    # Session security settings
    SESSION_COOKIE_AGE = 3600  # 1 hour
    SESSION_COOKIE_SECURE = not settings.DEBUG  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_SAVE_EVERY_REQUEST = True  # Refresh session on activity
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Clear on browser close
    
    # CSRF protection settings
    CSRF_COOKIE_SECURE = not settings.DEBUG  # HTTPS only in production
    CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    CSRF_COOKIE_SAMESITE = 'Lax'  # Additional CSRF protection
    CSRF_USE_SESSIONS = True  # Store CSRF token in session
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000 if not settings.DEBUG else 0  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Login attempt tracking
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_TIMEOUT = 900  # 15 minutes
    
    # Permission re-verification settings
    SENSITIVE_OPERATIONS_TIMEOUT = 300  # 5 minutes
    PERMISSION_CACHE_TIMEOUT = 600  # 10 minutes


def get_security_settings():
    """Get Django settings dictionary for security configuration"""
    config = SecurityConfig()
    
    return {
        # Session settings
        'SESSION_COOKIE_AGE': config.SESSION_COOKIE_AGE,
        'SESSION_COOKIE_SECURE': config.SESSION_COOKIE_SECURE,
        'SESSION_COOKIE_HTTPONLY': config.SESSION_COOKIE_HTTPONLY,
        'SESSION_COOKIE_SAMESITE': config.SESSION_COOKIE_SAMESITE,
        'SESSION_SAVE_EVERY_REQUEST': config.SESSION_SAVE_EVERY_REQUEST,
        'SESSION_EXPIRE_AT_BROWSER_CLOSE': config.SESSION_EXPIRE_AT_BROWSER_CLOSE,
        
        # CSRF settings
        'CSRF_COOKIE_SECURE': config.CSRF_COOKIE_SECURE,
        'CSRF_COOKIE_HTTPONLY': config.CSRF_COOKIE_HTTPONLY,
        'CSRF_COOKIE_SAMESITE': config.CSRF_COOKIE_SAMESITE,
        'CSRF_USE_SESSIONS': config.CSRF_USE_SESSIONS,
        
        # Security headers
        'SECURE_BROWSER_XSS_FILTER': config.SECURE_BROWSER_XSS_FILTER,
        'SECURE_CONTENT_TYPE_NOSNIFF': config.SECURE_CONTENT_TYPE_NOSNIFF,
        'SECURE_HSTS_SECONDS': config.SECURE_HSTS_SECONDS,
        'SECURE_HSTS_INCLUDE_SUBDOMAINS': config.SECURE_HSTS_INCLUDE_SUBDOMAINS,
        'SECURE_HSTS_PRELOAD': config.SECURE_HSTS_PRELOAD,
        'X_FRAME_OPTIONS': config.X_FRAME_OPTIONS,
    }


class LoginAttemptTracker:
    """Track and manage login attempts for security"""
    
    @staticmethod
    def get_attempt_key(identifier):
        """Generate cache key for login attempts"""
        return f"login_attempts:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    @staticmethod
    def get_lockout_key(identifier):
        """Generate cache key for account lockout"""
        return f"account_lockout:{hashlib.md5(identifier.encode()).hexdigest()}"
    
    @classmethod
    def record_failed_attempt(cls, identifier, ip_address=None):
        """Record a failed login attempt"""
        attempt_key = cls.get_attempt_key(identifier)
        lockout_key = cls.get_lockout_key(identifier)
        
        # Get current attempt count
        attempts = cache.get(attempt_key, 0)
        attempts += 1
        
        # Store updated attempt count
        cache.set(attempt_key, attempts, SecurityConfig.LOGIN_ATTEMPT_TIMEOUT)
        
        # Log the failed attempt
        auth_logger.warning(
            f"Failed login attempt for {identifier} from IP {ip_address}. "
            f"Attempt {attempts}/{SecurityConfig.MAX_LOGIN_ATTEMPTS}"
        )
        
        # Check if account should be locked
        if attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            cache.set(lockout_key, True, SecurityConfig.LOGIN_ATTEMPT_TIMEOUT)
            security_logger.warning(
                f"Account locked for {identifier} after {attempts} failed attempts. "
                f"IP: {ip_address}"
            )
            return True  # Account is now locked
        
        return False  # Account not locked yet
    
    @classmethod
    def is_locked(cls, identifier):
        """Check if account is locked due to failed attempts"""
        lockout_key = cls.get_lockout_key(identifier)
        return cache.get(lockout_key, False)
    
    @classmethod
    def clear_attempts(cls, identifier):
        """Clear login attempts for successful login"""
        attempt_key = cls.get_attempt_key(identifier)
        lockout_key = cls.get_lockout_key(identifier)
        
        cache.delete(attempt_key)
        cache.delete(lockout_key)


class PermissionReVerifier:
    """Handle permission re-verification for sensitive operations"""
    
    @staticmethod
    def get_verification_key(user_id, operation):
        """Generate cache key for permission verification"""
        return f"perm_verify:{user_id}:{operation}"
    
    @classmethod
    def mark_verified(cls, user, operation):
        """Mark user as verified for sensitive operation"""
        key = cls.get_verification_key(user.id, operation)
        cache.set(key, timezone.now().isoformat(), SecurityConfig.SENSITIVE_OPERATIONS_TIMEOUT)
        
        security_logger.info(
            f"User {user.username} (ID: {user.id}) verified for operation: {operation}"
        )
    
    @classmethod
    def is_recently_verified(cls, user, operation):
        """Check if user was recently verified for operation"""
        key = cls.get_verification_key(user.id, operation)
        verification_time = cache.get(key)
        
        if not verification_time:
            return False
        
        try:
            verified_at = timezone.datetime.fromisoformat(verification_time)
            if timezone.is_naive(verified_at):
                verified_at = timezone.make_aware(verified_at)
            
            time_since_verification = timezone.now() - verified_at
            is_valid = time_since_verification.total_seconds() < SecurityConfig.SENSITIVE_OPERATIONS_TIMEOUT
            
            if not is_valid:
                # Clean up expired verification
                cache.delete(key)
            
            return is_valid
        except (ValueError, TypeError):
            # Invalid timestamp, remove it
            cache.delete(key)
            return False
    
    @classmethod
    def require_reverification(cls, user, operation):
        """Force re-verification for user and operation"""
        key = cls.get_verification_key(user.id, operation)
        cache.delete(key)
        
        security_logger.info(
            f"Re-verification required for user {user.username} (ID: {user.id}) "
            f"for operation: {operation}"
        )


def cleanup_expired_sessions():
    """Clean up expired sessions from database"""
    try:
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired_sessions.count()
        expired_sessions.delete()
        
        if count > 0:
            security_logger.info(f"Cleaned up {count} expired sessions")
    except Exception as e:
        security_logger.error(f"Error cleaning up expired sessions: {e}")


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Signal handlers for authentication events
@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Log successful login attempts"""
    ip_address = get_client_ip(request)
    
    # Clear any failed login attempts
    LoginAttemptTracker.clear_attempts(user.username)
    
    # Log successful login
    auth_logger.info(
        f"Successful login for user {user.username} (ID: {user.id}) from IP {ip_address}"
    )
    
    # Store login information in session
    request.session['login_time'] = timezone.now().isoformat()
    request.session['login_ip'] = ip_address


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    """Log user logout"""
    if user:
        ip_address = get_client_ip(request)
        auth_logger.info(
            f"User logout: {user.username} (ID: {user.id}) from IP {ip_address}"
        )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts and track for security"""
    ip_address = get_client_ip(request)
    username = credentials.get('username', 'unknown')
    
    # Record failed attempt
    is_locked = LoginAttemptTracker.record_failed_attempt(username, ip_address)
    
    if is_locked:
        security_logger.warning(
            f"Account locked due to repeated failed login attempts: {username} from IP {ip_address}"
        )


def setup_security():
    """Initialize security configuration"""
    # Ensure logging is configured
    from .logging_config import setup_logging
    setup_logging()
    
    # Log security setup
    security_logger.info("Security configuration initialized")
    
    # Clean up expired sessions on startup
    cleanup_expired_sessions()