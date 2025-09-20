"""
Tests for the DashboardRouter class and dashboard routing logic.
"""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from unittest.mock import patch, MagicMock
from users.services import DashboardRouter, AuthenticationService, UserPermissions


class DashboardRouterTestCase(TestCase):
    """Test cases for DashboardRouter functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test groups
        self.customers_group = Group.objects.create(name='customers')
        self.insurance_group = Group.objects.create(name='insurance_company')
    
    def test_get_post_login_redirect_unauthenticated_user(self):
        """Test redirect for unauthenticated user"""
        unauthenticated_user = User()  # Not saved, not authenticated
        redirect_url = DashboardRouter.get_post_login_redirect(unauthenticated_user)
        self.assertEqual(redirect_url, '/login/')
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_get_post_login_redirect_no_dashboard_access(self, mock_get_permissions):
        """Test redirect for user with no dashboard access"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=[],
            organization=None,
            organization_type=None,
            available_dashboards=[],
            default_dashboard=None,
            has_conflicts=True,
            conflict_details="User has no group assignments"
        )
        
        redirect_url = DashboardRouter.get_post_login_redirect(self.user)
        self.assertTrue(redirect_url.startswith('/access-denied/'))
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_get_post_login_redirect_single_dashboard(self, mock_get_permissions):
        """Test redirect for user with single dashboard access"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=['customers'],
            organization='Test Fleet',
            organization_type='fleet',
            available_dashboards=['customer'],
            default_dashboard='customer',
            has_conflicts=False
        )
        
        redirect_url = DashboardRouter.get_post_login_redirect(self.user)
        self.assertEqual(redirect_url, '/dashboard/')
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_get_post_login_redirect_multiple_dashboards(self, mock_get_permissions):
        """Test redirect for user with multiple dashboard access"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=['customers', 'insurance_company'],
            organization='Test Company',
            organization_type='insurance',
            available_dashboards=['customer', 'insurance'],
            default_dashboard='selector',
            has_conflicts=False
        )
        
        redirect_url = DashboardRouter.get_post_login_redirect(self.user)
        self.assertEqual(redirect_url, '/dashboard-selector/')
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_get_default_dashboard(self, mock_get_permissions):
        """Test getting default dashboard for user"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=['customers'],
            organization='Test Fleet',
            organization_type='fleet',
            available_dashboards=['customer'],
            default_dashboard='customer',
            has_conflicts=False
        )
        
        default_dashboard = DashboardRouter.get_default_dashboard(self.user)
        self.assertEqual(default_dashboard, 'customer')
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_validate_dashboard_access_valid(self, mock_get_permissions):
        """Test dashboard access validation for valid access"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=['customers'],
            organization='Test Fleet',
            organization_type='fleet',
            available_dashboards=['customer'],
            default_dashboard='customer',
            has_conflicts=False
        )
        
        has_access = DashboardRouter.validate_dashboard_access(self.user, 'customer')
        self.assertTrue(has_access)
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_validate_dashboard_access_invalid(self, mock_get_permissions):
        """Test dashboard access validation for invalid access"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=['customers'],
            organization='Test Fleet',
            organization_type='fleet',
            available_dashboards=['customer'],
            default_dashboard='customer',
            has_conflicts=False
        )
        
        has_access = DashboardRouter.validate_dashboard_access(self.user, 'insurance')
        self.assertFalse(has_access)
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_resolve_dashboard_conflicts_no_groups(self, mock_get_permissions):
        """Test conflict resolution for user with no groups"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=[],
            organization='Test Fleet',
            organization_type='fleet',
            available_dashboards=[],
            default_dashboard=None,
            has_conflicts=True,
            conflict_details="User has no group assignments"
        )
        
        resolution = DashboardRouter.resolve_dashboard_conflicts(self.user)
        self.assertTrue(resolution['has_conflicts'])
        self.assertEqual(resolution['resolution_strategy'], 'organization_fallback')
        self.assertIn('Contact administrator', resolution['recommended_action'])
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_resolve_dashboard_conflicts_no_organization(self, mock_get_permissions):
        """Test conflict resolution for user with no organization"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=['customers'],
            organization=None,
            organization_type=None,
            available_dashboards=[],
            default_dashboard=None,
            has_conflicts=True,
            conflict_details="User has no organization assignment"
        )
        
        resolution = DashboardRouter.resolve_dashboard_conflicts(self.user)
        self.assertTrue(resolution['has_conflicts'])
        self.assertEqual(resolution['resolution_strategy'], 'group_fallback')
        self.assertIn('Complete organization profile', resolution['recommended_action'])
    
    def test_is_safe_redirect_url_valid(self):
        """Test safe redirect URL validation for valid URLs"""
        safe_urls = [
            '/dashboard/',
            '/insurance-dashboard/',
            '/dashboard-selector/',
            '/some/path/'
        ]
        
        for url in safe_urls:
            with self.subTest(url=url):
                self.assertTrue(DashboardRouter._is_safe_redirect_url(url))
    
    def test_is_safe_redirect_url_invalid(self):
        """Test safe redirect URL validation for invalid URLs"""
        unsafe_urls = [
            'http://example.com/',
            'https://malicious.com/',
            '//example.com/',
            'javascript:alert(1)',
            'ftp://example.com/',
            'relative-path',  # doesn't start with /
            ''
        ]
        
        for url in unsafe_urls:
            with self.subTest(url=url):
                self.assertFalse(DashboardRouter._is_safe_redirect_url(url))
    
    def test_user_can_access_url_protected_urls(self):
        """Test URL access validation for protected URLs"""
        # Add user to customers group
        self.user.groups.add(self.customers_group)
        
        # Test customer dashboard access
        can_access = DashboardRouter._user_can_access_url(self.user, '/dashboard/')
        self.assertTrue(can_access)
        
        # Test insurance dashboard access (should fail)
        can_access = DashboardRouter._user_can_access_url(self.user, '/insurance-dashboard/')
        self.assertFalse(can_access)
    
    def test_user_can_access_url_unprotected_urls(self):
        """Test URL access validation for unprotected URLs"""
        # Test access to unprotected URL
        can_access = DashboardRouter._user_can_access_url(self.user, '/some/other/path/')
        self.assertTrue(can_access)
    
    @patch('users.services.AuthenticationService.get_user_permissions')
    def test_get_dashboard_switch_options(self, mock_get_permissions):
        """Test getting dashboard switch options"""
        mock_get_permissions.return_value = UserPermissions(
            user_id=self.user.id,
            groups=['customers', 'insurance_company'],
            organization='Test Company',
            organization_type='insurance',
            available_dashboards=['customer', 'insurance'],
            default_dashboard='customer',
            has_conflicts=False
        )
        
        switch_options = DashboardRouter.get_dashboard_switch_options(self.user, 'customer')
        
        # Should return insurance dashboard as switch option
        self.assertEqual(len(switch_options), 1)
        self.assertEqual(switch_options[0]['name'], 'insurance')
        self.assertEqual(switch_options[0]['display_name'], 'Insurance Dashboard')
        self.assertEqual(switch_options[0]['url'], '/insurance-dashboard/')