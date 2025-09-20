"""
Logging configuration for authentication and security events.

This module provides logging configuration for the group-based authentication system,
including security events, access violations, and authentication attempts.
"""

import logging
import os
from django.conf import settings

def configure_auth_logging():
    """Configure logging for authentication and security events"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Security logger configuration
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    
    # Authentication logger configuration
    auth_logger = logging.getLogger('authentication')
    auth_logger.setLevel(logging.INFO)
    
    # Create formatters
    security_formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    auth_formatter = logging.Formatter(
        '%(asctime)s - AUTH - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Security file handler
    security_handler = logging.FileHandler(
        os.path.join(log_dir, 'security.log')
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(security_formatter)
    
    # Authentication file handler
    auth_handler = logging.FileHandler(
        os.path.join(log_dir, 'authentication.log')
    )
    auth_handler.setLevel(logging.INFO)
    auth_handler.setFormatter(auth_formatter)
    
    # Console handler for development
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(security_formatter)
        
        security_logger.addHandler(console_handler)
        auth_logger.addHandler(console_handler)
    
    # Add handlers to loggers
    security_logger.addHandler(security_handler)
    auth_logger.addHandler(auth_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    security_logger.propagate = False
    auth_logger.propagate = False


# Django logging configuration dictionary
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '{asctime} - SECURITY - {levelname} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'authentication': {
            'format': '{asctime} - AUTH - {levelname} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(settings.BASE_DIR, 'logs', 'security.log'),
            'formatter': 'security',
        },
        'auth_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(settings.BASE_DIR, 'logs', 'authentication.log'),
            'formatter': 'authentication',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'console'] if settings.DEBUG else ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'authentication': {
            'handlers': ['auth_file', 'console'] if settings.DEBUG else ['auth_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users.error_handlers': {
            'handlers': ['security_file', 'console'] if settings.DEBUG else ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'users.permissions': {
            'handlers': ['security_file', 'console'] if settings.DEBUG else ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


def setup_logging():
    """Setup logging configuration for the authentication system"""
    import logging.config
    
    # Create logs directory
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log that logging has been configured
    security_logger = logging.getLogger('security')
    security_logger.info("Authentication system logging configured successfully")