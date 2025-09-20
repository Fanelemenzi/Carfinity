"""
Tests for OrganizationService class.

This module tests the organization integration service that interfaces with the organization app
and provides organization-based access validation logic.
"""

import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User, Group
from organizations.models import Organization, OrganizationUser
from users.services import OrganizationService, AuthenticationService


class OrganizationServiceTest(TestCase):
    """Test cases for OrganizationService class"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        self.user_no_org = User.objects.create_user(
            username='noorg',
            email='noorg@example.com',
            password='testpass123'
        )
        
        # Create test groups
        self.customers_group = Group.objects.create(name='customers')
        self.insurance_group = Group.objects.create(name='insurance_company')
        
        # Create test organizations
        self.insurance_org = Organization.objects.create(
            name='Test Insurance Co',
            organization_type='insurance',
            contact_email='contact@testinsurance.com'
        )
        
        self.fleet_org = Organization.objects.create(
            name='Test Fleet Management',
            organization_type='fleet',
            contact_email='contact@testfleet.com'
        )
        
        # Create organization memberships
        self.org_user1 = OrganizationUser.objects.create(
            user=self.user1,
            organization=self.insurance_org,
            role='AGENT',
            is_active=True
        )
        
        self.org_user2 = OrganizationUser.objects.create(
            user=self.user2,
            organization=self.fleet_org,
            role='MANAGER',
            is_active=True
        )
        
        # Add users to groups
        self.user1.groups.add(self.insurance_group)
        self.user2.groups.add(self.customers_group)

    def test_get_user_organization_success(self):
        """Test getting user organization successfully"""
        organization = OrganizationService.get_user_organization(self.user1)
        
        self.assertIsNotNone(organization)
        self.assertEqual(organization.id, self.insurance_org.id)
        self.assertEqual(organization.name, 'Test Insurance Co')
        self.assertEqual(organization.organization_type, 'insurance')

    def test_get_user_organization_no_membership(self):
        """Test getting organization for user with no membership"""
        organization = OrganizationService.get_user_organization(self.user_no_org)
        
        self.assertIsNone(organization)

    def test_get_user_organization_unauthenticated(self):
        """Test getting organization for unauthenticated user"""
        unauthenticated_user = User()
        organization = OrganizationService.get_user_organization(unauthenticated_user)
        
        self.assertIsNone(organization)

    def test_get_user_organization_inactive_membership(self):
        """Test getting organization for user with inactive membership"""
        # Make membership inactive
        self.org_user1.is_active = False
        self.org_user1.save()
        
        organization = OrganizationService.get_user_organization(self.user1)
        
        self.assertIsNone(organization)

    def test_get_user_organization_type_success(self):
        """Test getting user organization type successfully"""
        org_type = OrganizationService.get_user_organization_type(self.user1)
        
        self.assertEqual(org_type, 'insurance')

    def test_get_user_organization_type_no_org(self):
        """Test getting organization type for user with no organization"""
        org_type = OrganizationService.get_user_organization_type(self.user_no_org)
        
        self.assertIsNone(org_type)

    def test_validate_organization_type_success(self):
        """Test validating organization type successfully"""
        is_valid = OrganizationService.validate_organization_type(self.user1, 'insurance')
        
        self.assertTrue(is_valid)

    def test_validate_organization_type_mismatch(self):
        """Test validating organization type with mismatch"""
        is_valid = OrganizationService.validate_organization_type(self.user1, 'fleet')
        
        self.assertFalse(is_valid)

    def test_validate_organization_type_no_org(self):
        """Test validating organization type for user with no organization"""
        is_valid = OrganizationService.validate_organization_type(self.user_no_org, 'insurance')
        
        self.assertFalse(is_valid)

    def test_validate_user_organization_access_success(self):
        """Test validating user organization access successfully"""
        is_valid = OrganizationService.validate_user_organization_access(
            self.user1, ['insurance', 'fleet']
        )
        
        self.assertTrue(is_valid)

    def test_validate_user_organization_access_not_in_list(self):
        """Test validating user organization access when type not in allowed list"""
        is_valid = OrganizationService.validate_user_organization_access(
            self.user1, ['fleet', 'dealership']
        )
        
        self.assertFalse(is_valid)

    def test_validate_user_organization_access_empty_list(self):
        """Test validating user organization access with empty allowed list"""
        is_valid = OrganizationService.validate_user_organization_access(
            self.user1, []
        )
        
        self.assertTrue(is_valid)

    def test_get_user_organization_role_success(self):
        """Test getting user organization role successfully"""
        role = OrganizationService.get_user_organization_role(self.user1)
        
        self.assertEqual(role, 'AGENT')

    def test_get_user_organization_role_no_org(self):
        """Test getting organization role for user with no organization"""
        role = OrganizationService.get_user_organization_role(self.user_no_org)
        
        self.assertIsNone(role)

    def test_check_group_organization_compatibility_valid(self):
        """Test checking group-organization compatibility for valid combination"""
        compatibility = OrganizationService.check_group_organization_compatibility(self.user1)
        
        self.assertTrue(compatibility['is_compatible'])
        self.assertEqual(len(compatibility['conflicts']), 0)
        self.assertEqual(len(compatibility['valid_combinations']), 1)
        self.assertIn(('insurance_company', 'insurance'), compatibility['valid_combinations'])

    def test_check_group_organization_compatibility_no_groups(self):
        """Test checking compatibility for user with no groups"""
        # Remove user from all groups
        self.user1.groups.clear()
        
        compatibility = OrganizationService.check_group_organization_compatibility(self.user1)
        
        self.assertFalse(compatibility['is_compatible'])
        self.assertIn('User has no group assignments', compatibility['conflicts'])
        self.assertIn('Contact administrator to assign appropriate user groups', compatibility['recommendations'])

    def test_check_group_organization_compatibility_no_org(self):
        """Test checking compatibility for user with no organization"""
        compatibility = OrganizationService.check_group_organization_compatibility(self.user_no_org)
        
        self.assertFalse(compatibility['is_compatible'])
        self.assertIn('User has no organization assignment', compatibility['conflicts'])
        self.assertIn('Complete organization profile setup', compatibility['recommendations'])

    def test_check_group_organization_compatibility_incompatible(self):
        """Test checking compatibility for incompatible group-organization combination"""
        # User2 has customers group but insurance organization - create this scenario
        self.org_user2.organization = self.insurance_org
        self.org_user2.save()
        
        compatibility = OrganizationService.check_group_organization_compatibility(self.user2)
        
        self.assertFalse(compatibility['is_compatible'])
        self.assertTrue(any('No valid combinations found' in conflict for conflict in compatibility['conflicts']))

    def test_get_organization_dashboard_mapping(self):
        """Test getting dashboard mapping for organization types"""
        insurance_dashboards = OrganizationService.get_organization_dashboard_mapping('insurance')
        fleet_dashboards = OrganizationService.get_organization_dashboard_mapping('fleet')
        unknown_dashboards = OrganizationService.get_organization_dashboard_mapping('unknown')
        
        self.assertEqual(insurance_dashboards, ['insurance'])
        self.assertEqual(fleet_dashboards, ['customer'])
        self.assertEqual(unknown_dashboards, [])

    def test_get_organization_required_groups(self):
        """Test getting required groups for organization types"""
        insurance_groups = OrganizationService.get_organization_required_groups('insurance')
        fleet_groups = OrganizationService.get_organization_required_groups('fleet')
        unknown_groups = OrganizationService.get_organization_required_groups('unknown')
        
        self.assertEqual(insurance_groups, ['insurance_company'])
        self.assertEqual(fleet_groups, ['customers'])
        self.assertEqual(unknown_groups, [])

    def test_validate_organization_exists_success(self):
        """Test validating existing organization"""
        exists = OrganizationService.validate_organization_exists(self.insurance_org.id)
        
        self.assertTrue(exists)

    def test_validate_organization_exists_not_found(self):
        """Test validating non-existent organization"""
        exists = OrganizationService.validate_organization_exists(99999)
        
        self.assertFalse(exists)

    def test_get_organization_members(self):
        """Test getting organization members"""
        members = OrganizationService.get_organization_members(self.insurance_org)
        
        self.assertEqual(len(members), 1)
        self.assertIn(self.user1, members)

    def test_get_organization_members_include_inactive(self):
        """Test getting organization members including inactive"""
        # Make one membership inactive
        self.org_user1.is_active = False
        self.org_user1.save()
        
        active_members = OrganizationService.get_organization_members(self.insurance_org, active_only=True)
        all_members = OrganizationService.get_organization_members(self.insurance_org, active_only=False)
        
        self.assertEqual(len(active_members), 0)
        self.assertEqual(len(all_members), 1)

    def test_sync_organization_groups(self):
        """Test syncing organization groups"""
        # Link groups to organization
        self.insurance_org.linked_groups.add(self.insurance_group)
        
        # Remove user from group to test sync
        self.user1.groups.remove(self.insurance_group)
        self.assertFalse(self.user1.groups.filter(name='insurance_company').exists())
        
        # Sync groups
        stats = OrganizationService.sync_organization_groups(self.insurance_org)
        
        # Verify sync worked
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.groups.filter(name='insurance_company').exists())
        self.assertEqual(stats['members_processed'], 1)
        self.assertEqual(stats['groups_added'], 1)

    @patch('users.services.logger')
    def test_log_organization_group_conflict_no_groups(self, mock_logger):
        """Test logging organization-group conflict for no groups"""
        OrganizationService._log_organization_group_conflict(
            self.user1, 'no_groups', [], 'insurance'
        )
        
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('ORGANIZATION-GROUP CONFLICT', call_args)
        self.assertIn('has no group assignments', call_args)

    @patch('users.services.logger')
    def test_log_organization_group_conflict_no_organization(self, mock_logger):
        """Test logging organization-group conflict for no organization"""
        OrganizationService._log_organization_group_conflict(
            self.user1, 'no_organization', ['customers'], None
        )
        
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('ORGANIZATION-GROUP CONFLICT', call_args)
        self.assertIn('no organization assignment', call_args)

    @patch('users.services.logger')
    def test_log_organization_group_conflict_incompatible(self, mock_logger):
        """Test logging organization-group conflict for incompatible combination"""
        OrganizationService._log_organization_group_conflict(
            self.user1, 'incompatible_combination', ['customers'], 'insurance'
        )
        
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('ORGANIZATION-GROUP CONFLICT', call_args)
        self.assertIn('incompatible group-organization combination', call_args)

    @patch('users.services.logger')
    def test_log_organization_group_conflict_partial_incompatibility(self, mock_logger):
        """Test logging organization-group conflict for partial incompatibility"""
        OrganizationService._log_organization_group_conflict(
            self.user1, 'partial_incompatibility', ['customers', 'insurance_company'], 'insurance'
        )
        
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('ORGANIZATION-GROUP NOTICE', call_args)
        self.assertIn('some incompatible group-organization combinations', call_args)

    def test_integration_with_authentication_service(self):
        """Test integration between OrganizationService and AuthenticationService"""
        # Test that AuthenticationService uses OrganizationService correctly
        permissions = AuthenticationService.get_user_permissions(self.user1)
        
        self.assertEqual(permissions.organization, 'Test Insurance Co')
        self.assertEqual(permissions.organization_type, 'insurance')
        self.assertIn('insurance', permissions.available_dashboards)

    def test_error_handling_database_error(self):
        """Test error handling when database errors occur"""
        with patch('organizations.models.OrganizationUser.objects.select_related') as mock_query:
            mock_query.side_effect = Exception("Database error")
            
            organization = OrganizationService.get_user_organization(self.user1)
            
            self.assertIsNone(organization)

    def tearDown(self):
        """Clean up test data"""
        User.objects.all().delete()
        Group.objects.all().delete()
        Organization.objects.all().delete()
        OrganizationUser.objects.all().delete()