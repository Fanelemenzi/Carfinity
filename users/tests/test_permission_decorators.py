"""
Test file for permission decorators.

This file contains tests to verify the permission decorators work correctly
for view-level access control.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, Group, AnonymousUser
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.urls import reverse
from organizations.models import Organization, OrganizationUser
from users.permissions import (
    require_group, require_any_group, require_all_groups,
    require_organization_type, require_dashboard_access,
    check_permission_conflicts, PermissionChecker
)


class PermissionDecoratorsTestCase(TestCase):
    """Test cases for permission decorators"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        
        # Create groups
        self.customers_group = Group.objects.create(name='customers')
        self.insurance_group = Group.objects.create(name='insurance_company')
        self.admin_group = Group.objects.create(name='admin')
        
        # Create organizations
        self.customer_org = Organization.objects.create(
            name='Test Fleet Company',
            organization_type='fleet'
        )
        
        self.insurance_org = Organization.objects.create(
            name='Test Insurance Company',
            organization_type='insurance'
        )
        
        # Create users
        self.customer_user = User.objects.create_user(
            username='customer@test.com',
            email='customer@test.com',
            password='testpass123'
        )
        
        self.insurance_user = User.objects.create_user(
            username='insurance@test.com',
            email='insurance@test.com',
            password='testpass123'
        )
        
        self.multi_user = User.objects.create_user(
            username='multi@test.com',
            email='multi@test.com',
            password='testpass123'
        )
        
        self.no_group_user = User.objects.create_user(
            username='nogroup@test.com',
            email='nogroup@test.com',
            password='testpass123'
        )
        
        # Set up user groups and organizations
        self.customer_user.groups.add(self.customers_group)
        OrganizationUser.objects.create(
            user=self.customer_user,
            organization=self.customer_org,
            role='DRIVER',
            is_active=True
        )
        
        self.insurance_user.groups.add(self.insurance_group)
        OrganizationUser.objects.create(
            user=self.insurance_user,
            organization=self.insurance_org,
            role='AGENT',
            is_active=True
        )
        
        # Multi-access user (both groups)
        self.multi_user.groups.add(self.customers_group, self.insurance_group)
        OrganizationUser.objects.create(
            user=self.multi_user,
            organization=self.customer_org,
            role='ADMIN',
            is_active=True
        )
        
        # Create test views
        @require_group('customers')
        def customer_view(request):
            return HttpResponse('Customer Dashboard')
        
        @require_group('insurance_company')
        def insurance_view(request):
            return HttpResponse('Insurance Dashboard')
        
        @require_any_group(['customers', 'insurance_company'])
        def multi_access_view(request):
            return HttpResponse('Multi Access View')
        
        @require_all_groups(['customers', 'admin'])
        def admin_customer_view(request):
            return HttpResponse('Admin Customer View')
        
        @require_organization_type('fleet')
        def fleet_view(request):
            return HttpResponse('Fleet View')
        
        @require_organization_type('insurance')
        def insurance_org_view(request):
            return HttpResponse('Insurance Org View')
        
        @require_dashboard_access('customer')
        def customer_dashboard_view(request):
            return HttpResponse('Customer Dashboard Access')
        
        @check_permission_conflicts
        def conflict_check_view(request):
            return HttpResponse('Conflict Check View')
        
        self.customer_view = customer_view
        self.insurance_view = insurance_view
        self.multi_access_view = multi_access_view
        self.admin_customer_view = admin_customer_view
        self.fleet_view = fleet_view
        self.insurance_org_view = insurance_org_view
        self.customer_dashboard_view = customer_dashboard_view
        self.conflict_check_view = conflict_check_view
    
    def test_require_group_decorator_success(self):
        """Test require_group decorator allows access for users with correct group"""
        request = self.factory.get('/test/')
        request.user = self.customer_user
        
        response = self.customer_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Customer Dashboard')
    
    def test_require_group_decorator_denied(self):
        """Test require_group decorator denies access for users without correct group"""
        request = self.factory.get('/test/')
        request.user = self.insurance_user
        
        response = self.customer_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to access_denied
    
    def test_require_group_decorator_unauthenticated(self):
        """Test require_group decorator redirects unauthenticated users to login"""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = self.customer_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_require_any_group_decorator_success(self):
        """Test require_any_group decorator allows access for users with any required group"""
        request = self.factory.get('/test/')
        request.user = self.customer_user
        
        response = self.multi_access_view(request)
        self.assertEqual(response.status_code, 200)
        
        request.user = self.insurance_user
        response = self.multi_access_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_require_any_group_decorator_denied(self):
        """Test require_any_group decorator denies access for users without any required group"""
        request = self.factory.get('/test/')
        request.user = self.no_group_user
        
        response = self.multi_access_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to access_denied
    
    def test_require_all_groups_decorator_success(self):
        """Test require_all_groups decorator allows access for users with all required groups"""
        # Add admin group to customer user
        self.customer_user.groups.add(self.admin_group)
        
        request = self.factory.get('/test/')
        request.user = self.customer_user
        
        response = self.admin_customer_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_require_all_groups_decorator_denied(self):
        """Test require_all_groups decorator denies access for users missing some required groups"""
        request = self.factory.get('/test/')
        request.user = self.customer_user  # Has customers but not admin
        
        response = self.admin_customer_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to access_denied
    
    def test_require_organization_type_decorator_success(self):
        """Test require_organization_type decorator allows access for users with correct org type"""
        request = self.factory.get('/test/')
        request.user = self.customer_user
        
        response = self.fleet_view(request)
        self.assertEqual(response.status_code, 200)
        
        request.user = self.insurance_user
        response = self.insurance_org_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_require_organization_type_decorator_denied(self):
        """Test require_organization_type decorator denies access for users with wrong org type"""
        request = self.factory.get('/test/')
        request.user = self.customer_user
        
        response = self.insurance_org_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to access_denied
    
    def test_require_dashboard_access_decorator_success(self):
        """Test require_dashboard_access decorator allows access for users with dashboard access"""
        request = self.factory.get('/test/')
        request.user = self.customer_user
        
        response = self.customer_dashboard_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_require_dashboard_access_decorator_denied(self):
        """Test require_dashboard_access decorator denies access for users without dashboard access"""
        request = self.factory.get('/test/')
        request.user = self.insurance_user
        
        response = self.customer_dashboard_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to access_denied
    
    def test_check_permission_conflicts_decorator(self):
        """Test check_permission_conflicts decorator logs conflicts but allows access"""
        request = self.factory.get('/test/')
        request.user = self.customer_user
        
        response = self.conflict_check_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Conflict Check View')


class PermissionCheckerTestCase(TestCase):
    """Test cases for PermissionChecker utility class"""
    
    def setUp(self):
        """Set up test data"""
        self.group = Group.objects.create(name='customers')
        self.group2 = Group.objects.create(name='insurance_company')
        
        self.user = User.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123'
        )
        
        self.user.groups.add(self.group)
        
        self.org = Organization.objects.create(
            name='Test Organization',
            organization_type='fleet'
        )
        
        OrganizationUser.objects.create(
            user=self.user,
            organization=self.org,
            role='ADMIN',
            is_active=True
        )
    
    def test_permission_checker_initialization(self):
        """Test PermissionChecker initialization"""
        checker = PermissionChecker(self.user)
        self.assertEqual(checker.user, self.user)
        self.assertIsNotNone(checker.permissions)
    
    def test_permission_checker_has_group(self):
        """Test PermissionChecker has_group method"""
        checker = PermissionChecker(self.user)
        self.assertTrue(checker.has_group('customers'))
        self.assertFalse(checker.has_group('insurance_company'))
    
    def test_permission_checker_has_any_group(self):
        """Test PermissionChecker has_any_group method"""
        checker = PermissionChecker(self.user)
        self.assertTrue(checker.has_any_group(['customers', 'insurance_company']))
        self.assertFalse(checker.has_any_group(['insurance_company', 'admin']))
    
    def test_permission_checker_has_all_groups(self):
        """Test PermissionChecker has_all_groups method"""
        checker = PermissionChecker(self.user)
        self.assertTrue(checker.has_all_groups(['customers']))
        self.assertFalse(checker.has_all_groups(['customers', 'insurance_company']))
    
    def test_permission_checker_has_organization_type(self):
        """Test PermissionChecker has_organization_type method"""
        checker = PermissionChecker(self.user)
        self.assertTrue(checker.has_organization_type('fleet'))
        self.assertFalse(checker.has_organization_type('insurance'))
    
    def test_permission_checker_has_dashboard_access(self):
        """Test PermissionChecker has_dashboard_access method"""
        checker = PermissionChecker(self.user)
        self.assertTrue(checker.has_dashboard_access('customer'))
        self.assertFalse(checker.has_dashboard_access('insurance'))
    
    def test_permission_checker_get_available_dashboards(self):
        """Test PermissionChecker get_available_dashboards method"""
        checker = PermissionChecker(self.user)
        dashboards = checker.get_available_dashboards()
        self.assertIn('customer', dashboards)
        self.assertNotIn('insurance', dashboards)
    
    def test_permission_checker_get_default_dashboard(self):
        """Test PermissionChecker get_default_dashboard method"""
        checker = PermissionChecker(self.user)
        default_dashboard = checker.get_default_dashboard()
        self.assertEqual(default_dashboard, 'customer')


class ViewIntegrationTestCase(TestCase):
    """Integration tests for views with permission decorators"""
    
    def setUp(self):
        """Set up test data"""
        # Create groups
        self.customers_group = Group.objects.create(name='customers')
        self.insurance_group = Group.objects.create(name='insurance_company')
        
        # Create organizations
        self.customer_org = Organization.objects.create(
            name='Test Fleet Company',
            organization_type='fleet'
        )
        
        # Create user
        self.customer_user = User.objects.create_user(
            username='customer@test.com',
            email='customer@test.com',
            password='testpass123'
        )
        
        self.customer_user.groups.add(self.customers_group)
        OrganizationUser.objects.create(
            user=self.customer_user,
            organization=self.customer_org,
            role='DRIVER',
            is_active=True
        )
    
    def test_access_denied_view(self):
        """Test access_denied view renders correctly"""
        response = self.client.get('/access-denied/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Access Denied')
    
    def test_dashboard_selector_view_authenticated(self):
        """Test dashboard_selector view for authenticated user"""
        self.client.login(username='customer@test.com', password='testpass123')
        response = self.client.get('/dashboard-selector/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select Dashboard')
    
    def test_dashboard_selector_view_unauthenticated(self):
        """Test dashboard_selector view redirects unauthenticated users"""
        response = self.client.get('/dashboard-selector/')
        self.assertEqual(response.status_code, 302)  # Redirect to login


if __name__ == '__main__':
    # This allows running the tests directly
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.messages',
                'django.contrib.sessions',
                'users',
                'organizations',
            ],
            MIDDLEWARE=[
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
            ],
            SECRET_KEY='test-secret-key',
            ROOT_URLCONF='users.urls',
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])