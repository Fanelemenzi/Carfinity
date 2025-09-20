"""
Test file for authentication service and permission utilities.

This file contains basic tests to verify the authentication service implementation.
"""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from organizations.models import Organization, OrganizationUser
from users.services import AuthenticationService, PermissionUtils
from users.permissions import PermissionChecker


class AuthenticationServiceTestCase(TestCase):
    """Test cases for AuthenticationService"""
    
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
    
    def test_get_user_permissions_customer(self):
        """Test getting permissions for customer user"""
        permissions = AuthenticationService.get_user_permissions(self.customer_user)
        
        self.assertEqual(permissions.user_id, self.customer_user.id)
        self.assertIn('customers', permissions.groups)
        self.assertEqual(permissions.organization, 'Test Fleet Company')
        self.assertEqual(permissions.organization_type, 'fleet')
        self.assertIn('customer', permissions.available_dashboards)
        self.assertEqual(permissions.default_dashboard, 'customer')
        self.assertFalse(permissions.has_conflicts)
    
    def test_get_user_permissions_insurance(self):
        """Test getting permissions for insurance user"""
        permissions = AuthenticationService.get_user_permissions(self.insurance_user)
        
        self.assertEqual(permissions.user_id, self.insurance_user.id)
        self.assertIn('insurance_company', permissions.groups)
        self.assertEqual(permissions.organization, 'Test Insurance Company')
        self.assertEqual(permissions.organization_type, 'insurance')
        self.assertIn('insurance', permissions.available_dashboards)
        self.assertEqual(permissions.default_dashboard, 'insurance')
        self.assertFalse(permissions.has_conflicts)
    
    def test_resolve_dashboard_access(self):
        """Test dashboard access resolution"""
        customer_dashboards = AuthenticationService.resolve_dashboard_access(self.customer_user)
        insurance_dashboards = AuthenticationService.resolve_dashboard_access(self.insurance_user)
        
        self.assertIn('customer', customer_dashboards)
        self.assertNotIn('insurance', customer_dashboards)
        
        self.assertIn('insurance', insurance_dashboards)
        self.assertNotIn('customer', insurance_dashboards)
    
    def test_get_redirect_url_after_login(self):
        """Test post-login redirect URL generation"""
        customer_url = AuthenticationService.get_redirect_url_after_login(self.customer_user)
        insurance_url = AuthenticationService.get_redirect_url_after_login(self.insurance_user)
        
        self.assertEqual(customer_url, '/dashboard/')
        self.assertEqual(insurance_url, '/insurance-dashboard/')
    
    def test_check_organization_access(self):
        """Test organization access checking"""
        self.assertTrue(
            AuthenticationService.check_organization_access(self.customer_user, 'fleet')
        )
        self.assertFalse(
            AuthenticationService.check_organization_access(self.customer_user, 'insurance')
        )
        
        self.assertTrue(
            AuthenticationService.check_organization_access(self.insurance_user, 'insurance')
        )
        self.assertFalse(
            AuthenticationService.check_organization_access(self.insurance_user, 'fleet')
        )


class PermissionUtilsTestCase(TestCase):
    """Test cases for PermissionUtils"""
    
    def setUp(self):
        """Set up test data"""
        self.group1 = Group.objects.create(name='customers')
        self.group2 = Group.objects.create(name='insurance_company')
        
        self.user = User.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123'
        )
        
        self.user.groups.add(self.group1)
        
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
    
    def test_user_has_group(self):
        """Test group membership checking"""
        self.assertTrue(PermissionUtils.user_has_group(self.user, 'customers'))
        self.assertFalse(PermissionUtils.user_has_group(self.user, 'insurance_company'))
    
    def test_user_has_any_group(self):
        """Test any group membership checking"""
        self.assertTrue(
            PermissionUtils.user_has_any_group(self.user, ['customers', 'insurance_company'])
        )
        self.assertFalse(
            PermissionUtils.user_has_any_group(self.user, ['insurance_company', 'admin'])
        )
    
    def test_user_has_all_groups(self):
        """Test all groups membership checking"""
        self.assertTrue(PermissionUtils.user_has_all_groups(self.user, ['customers']))
        self.assertFalse(
            PermissionUtils.user_has_all_groups(self.user, ['customers', 'insurance_company'])
        )
    
    def test_get_user_organization(self):
        """Test getting user organization"""
        org = PermissionUtils.get_user_organization(self.user)
        self.assertEqual(org.name, 'Test Organization')
        self.assertEqual(org.organization_type, 'fleet')
    
    def test_user_belongs_to_organization_type(self):
        """Test organization type membership checking"""
        self.assertTrue(
            PermissionUtils.user_belongs_to_organization_type(self.user, 'fleet')
        )
        self.assertFalse(
            PermissionUtils.user_belongs_to_organization_type(self.user, 'insurance')
        )
    
    def test_get_user_organization_role(self):
        """Test getting user organization role"""
        role = PermissionUtils.get_user_organization_role(self.user)
        self.assertEqual(role, 'ADMIN')


class PermissionCheckerTestCase(TestCase):
    """Test cases for PermissionChecker"""
    
    def setUp(self):
        """Set up test data"""
        self.group = Group.objects.create(name='customers')
        
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
        
        self.checker = PermissionChecker(self.user)
    
    def test_has_group(self):
        """Test group checking via PermissionChecker"""
        self.assertTrue(self.checker.has_group('customers'))
        self.assertFalse(self.checker.has_group('insurance_company'))
    
    def test_has_organization_type(self):
        """Test organization type checking via PermissionChecker"""
        self.assertTrue(self.checker.has_organization_type('fleet'))
        self.assertFalse(self.checker.has_organization_type('insurance'))
    
    def test_has_dashboard_access(self):
        """Test dashboard access checking via PermissionChecker"""
        self.assertTrue(self.checker.has_dashboard_access('customer'))
        self.assertFalse(self.checker.has_dashboard_access('insurance'))
    
    def test_get_available_dashboards(self):
        """Test getting available dashboards via PermissionChecker"""
        dashboards = self.checker.get_available_dashboards()
        self.assertIn('customer', dashboards)
        self.assertNotIn('insurance', dashboards)


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
                'users',
                'organizations',
            ],
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])