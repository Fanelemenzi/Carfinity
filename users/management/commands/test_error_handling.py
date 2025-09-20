"""
Management command to test the error handling system.

This command tests various error scenarios to ensure the error handling
system is working correctly.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.test import RequestFactory
from users.error_handlers import (
    AuthenticationErrorHandler, 
    ErrorType, 
    SecurityEventLogger,
    ErrorMessageGenerator,
    UserGuidanceProvider
)
from users.services import AuthenticationService
import logging

class Command(BaseCommand):
    help = 'Test the error handling system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--scenario',
            type=str,
            choices=['all', 'no_auth', 'no_groups', 'no_org', 'conflicts', 'logging'],
            default='all',
            help='Which error scenario to test'
        )
    
    def handle(self, *args, **options):
        scenario = options['scenario']
        
        self.stdout.write(self.style.SUCCESS('Testing Error Handling System'))
        self.stdout.write('=' * 50)
        
        if scenario == 'all' or scenario == 'no_auth':
            self.test_no_authentication()
        
        if scenario == 'all' or scenario == 'no_groups':
            self.test_no_groups()
        
        if scenario == 'all' or scenario == 'no_org':
            self.test_no_organization()
        
        if scenario == 'all' or scenario == 'conflicts':
            self.test_permission_conflicts()
        
        if scenario == 'all' or scenario == 'logging':
            self.test_logging_system()
        
        self.stdout.write(self.style.SUCCESS('\nAll tests completed!'))
    
    def test_no_authentication(self):
        """Test error handling for unauthenticated users"""
        self.stdout.write('\n1. Testing No Authentication Scenario')
        self.stdout.write('-' * 40)
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = None
        
        # Test error message generation
        context = ErrorMessageGenerator.get_error_context(ErrorType.NO_AUTHENTICATION)
        
        self.stdout.write(f"Error Title: {context['error_title']}")
        self.stdout.write(f"Error Message: {context['error_message']}")
        self.stdout.write(f"Suggestions: {len(context['suggestions'])} items")
        
        # Test logging
        SecurityEventLogger.log_access_denied(
            user=None,
            requested_resource='/dashboard/',
            error_type=ErrorType.NO_AUTHENTICATION
        )
        
        self.stdout.write(self.style.SUCCESS('✓ No authentication test completed'))
    
    def test_no_groups(self):
        """Test error handling for users with no groups"""
        self.stdout.write('\n2. Testing No Groups Scenario')
        self.stdout.write('-' * 40)
        
        # Create or get a test user with no groups
        user, created = User.objects.get_or_create(
            username='test_no_groups',
            defaults={'email': 'test@example.com'}
        )
        
        # Ensure user has no groups
        user.groups.clear()
        
        # Test permission checking
        permissions = AuthenticationService.get_user_permissions(user)
        
        self.stdout.write(f"User Groups: {permissions.groups}")
        self.stdout.write(f"Available Dashboards: {permissions.available_dashboards}")
        
        # Test error message generation
        context = ErrorMessageGenerator.get_error_context(ErrorType.NO_GROUPS, user)
        
        self.stdout.write(f"Error Title: {context['error_title']}")
        self.stdout.write(f"User Groups in Context: {context.get('user_groups', [])}")
        
        # Test user guidance
        guidance = UserGuidanceProvider.get_guidance_for_user(user)
        self.stdout.write(f"Primary Issue: {guidance['primary_issue']}")
        self.stdout.write(f"Steps to Resolve: {len(guidance['steps_to_resolve'])} steps")
        
        self.stdout.write(self.style.SUCCESS('✓ No groups test completed'))
    
    def test_no_organization(self):
        """Test error handling for users with no organization"""
        self.stdout.write('\n3. Testing No Organization Scenario')
        self.stdout.write('-' * 40)
        
        # Create or get a test user with groups but no organization
        user, created = User.objects.get_or_create(
            username='test_no_org',
            defaults={'email': 'test2@example.com'}
        )
        
        # Add user to a group
        customers_group, _ = Group.objects.get_or_create(name='customers')
        user.groups.add(customers_group)
        
        # Test permission checking
        permissions = AuthenticationService.get_user_permissions(user)
        
        self.stdout.write(f"User Groups: {permissions.groups}")
        self.stdout.write(f"Organization: {permissions.organization}")
        self.stdout.write(f"Organization Type: {permissions.organization_type}")
        
        # Test error message generation
        context = ErrorMessageGenerator.get_error_context(ErrorType.NO_ORGANIZATION, user)
        
        self.stdout.write(f"Error Title: {context['error_title']}")
        
        # Test user guidance
        guidance = UserGuidanceProvider.get_guidance_for_user(user)
        self.stdout.write(f"Primary Issue: {guidance['primary_issue']}")
        
        self.stdout.write(self.style.SUCCESS('✓ No organization test completed'))
    
    def test_permission_conflicts(self):
        """Test permission conflict detection and handling"""
        self.stdout.write('\n4. Testing Permission Conflicts')
        self.stdout.write('-' * 40)
        
        # Create a test user
        user, created = User.objects.get_or_create(
            username='test_conflicts',
            defaults={'email': 'test3@example.com'}
        )
        
        # Add user to multiple groups to simulate conflicts
        customers_group, _ = Group.objects.get_or_create(name='customers')
        insurance_group, _ = Group.objects.get_or_create(name='insurance_company')
        
        user.groups.add(customers_group)
        user.groups.add(insurance_group)
        
        # Test permission checking
        permissions = AuthenticationService.get_user_permissions(user)
        
        self.stdout.write(f"User Groups: {permissions.groups}")
        self.stdout.write(f"Has Conflicts: {permissions.has_conflicts}")
        self.stdout.write(f"Conflict Details: {permissions.conflict_details}")
        
        # Test conflict logging
        if permissions.has_conflicts:
            SecurityEventLogger.log_permission_conflict(
                user=user,
                groups=permissions.groups,
                org_type=permissions.organization_type or 'None',
                conflict_details=permissions.conflict_details or 'Test conflict'
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Permission conflicts test completed'))
    
    def test_logging_system(self):
        """Test the logging system"""
        self.stdout.write('\n5. Testing Logging System')
        self.stdout.write('-' * 40)
        
        # Test different types of logging
        test_user, _ = User.objects.get_or_create(
            username='test_logging',
            defaults={'email': 'test4@example.com'}
        )
        
        # Test authentication logging
        SecurityEventLogger.log_authentication_attempt('test_user', True, '127.0.0.1')
        SecurityEventLogger.log_authentication_attempt('bad_user', False, '192.168.1.1')
        
        # Test access denied logging
        SecurityEventLogger.log_access_denied(
            user=test_user,
            requested_resource='/test-resource/',
            error_type=ErrorType.ACCESS_DENIED,
            additional_info={'test': 'data'}
        )
        
        # Test security violation logging
        SecurityEventLogger.log_security_violation(
            user=test_user,
            violation_type='test_violation',
            details='This is a test security violation',
            request_path='/test-path/'
        )
        
        self.stdout.write('Logged various security events')
        
        # Check if log files exist
        import os
        from django.conf import settings
        
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        security_log = os.path.join(log_dir, 'security.log')
        auth_log = os.path.join(log_dir, 'authentication.log')
        
        if os.path.exists(security_log):
            self.stdout.write(f'✓ Security log exists: {security_log}')
        else:
            self.stdout.write(f'✗ Security log missing: {security_log}')
        
        if os.path.exists(auth_log):
            self.stdout.write(f'✓ Authentication log exists: {auth_log}')
        else:
            self.stdout.write(f'✗ Authentication log missing: {auth_log}')
        
        self.stdout.write(self.style.SUCCESS('✓ Logging system test completed'))
    
    def cleanup_test_users(self):
        """Clean up test users created during testing"""
        test_usernames = ['test_no_groups', 'test_no_org', 'test_conflicts', 'test_logging']
        
        for username in test_usernames:
            try:
                user = User.objects.get(username=username)
                user.delete()
                self.stdout.write(f'Cleaned up test user: {username}')
            except User.DoesNotExist:
                pass