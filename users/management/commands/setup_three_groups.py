"""
Management command to set up the simplified 3-group authentication system.

This command creates the three required groups (Staff, AutoCare, AutoAssess) 
with appropriate permissions for the simplified authentication system.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up the simplified 3-group authentication system (Staff, AutoCare, AutoAssess)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing groups and recreate them',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(
            self.style.SUCCESS('Setting up simplified 3-group authentication system...')
        )
        
        dry_run = options.get('dry_run', False)
        reset = options.get('reset', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            with transaction.atomic():
                if reset:
                    self._reset_groups(dry_run)
                
                self._create_groups(dry_run)
                self._assign_permissions(dry_run)
                
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Successfully set up 3-group authentication system')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Dry run completed - no changes made')
                    )
                    
        except Exception as e:
            logger.error(f"Error setting up groups: {str(e)}")
            raise CommandError(f'Failed to set up groups: {str(e)}')

    def _reset_groups(self, dry_run=False):
        """Reset existing groups if requested"""
        group_names = ['Staff', 'AutoCare', 'AutoAssess']
        
        for group_name in group_names:
            try:
                group = Group.objects.get(name=group_name)
                if not dry_run:
                    group.delete()
                self.stdout.write(f'  - Deleted existing group: {group_name}')
            except Group.DoesNotExist:
                self.stdout.write(f'  - Group {group_name} does not exist (skipping)')

    def _create_groups(self, dry_run=False):
        """Create the three required groups"""
        groups_config = {
            'Staff': {
                'description': 'Administrative staff with full system access',
                'permissions': ['admin_access', 'user_management', 'system_configuration']
            },
            'AutoCare': {
                'description': 'Vehicle maintenance and care professionals',
                'permissions': ['vehicle_maintenance', 'inspection_access', 'parts_management']
            },
            'AutoAssess': {
                'description': 'Vehicle assessment and insurance professionals',
                'permissions': ['assessment_access', 'insurance_claims', 'damage_evaluation']
            }
        }
        
        self.stdout.write('\nCreating groups:')
        
        for group_name, config in groups_config.items():
            if not dry_run:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    self.stdout.write(f'  ✓ Created group: {group_name}')
                else:
                    self.stdout.write(f'  - Group already exists: {group_name}')
            else:
                self.stdout.write(f'  [DRY RUN] Would create group: {group_name}')
            
            self.stdout.write(f'    Description: {config["description"]}')

    def _assign_permissions(self, dry_run=False):
        """Assign appropriate permissions to each group"""
        self.stdout.write('\nAssigning permissions:')
        
        # Define permission mappings for each group
        permission_mappings = {
            'Staff': self._get_staff_permissions(),
            'AutoCare': self._get_autocare_permissions(),
            'AutoAssess': self._get_autoassess_permissions()
        }
        
        for group_name, permission_codenames in permission_mappings.items():
            if not dry_run:
                try:
                    group = Group.objects.get(name=group_name)
                    
                    # Clear existing permissions
                    group.permissions.clear()
                    
                    # Add new permissions
                    permissions = Permission.objects.filter(codename__in=permission_codenames)
                    group.permissions.set(permissions)
                    
                    self.stdout.write(f'  ✓ Assigned {permissions.count()} permissions to {group_name}')
                    
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Group {group_name} not found')
                    )
            else:
                self.stdout.write(f'  [DRY RUN] Would assign {len(permission_codenames)} permissions to {group_name}')
                for perm in permission_codenames[:3]:  # Show first 3 permissions
                    self.stdout.write(f'    - {perm}')
                if len(permission_codenames) > 3:
                    self.stdout.write(f'    ... and {len(permission_codenames) - 3} more')

    def _get_staff_permissions(self):
        """Get permission codenames for Staff group"""
        return [
            # User management
            'add_user', 'change_user', 'delete_user', 'view_user',
            'add_group', 'change_group', 'delete_group', 'view_group',
            
            # Profile management
            'add_profile', 'change_profile', 'delete_profile', 'view_profile',
            
            # Organization management (if needed for cleanup)
            'add_organization', 'change_organization', 'delete_organization', 'view_organization',
            
            # Vehicle management
            'add_vehicle', 'change_vehicle', 'delete_vehicle', 'view_vehicle',
            
            # Maintenance management
            'add_maintenancerecord', 'change_maintenancerecord', 'delete_maintenancerecord', 'view_maintenancerecord',
            
            # Assessment management
            'add_assessment', 'change_assessment', 'delete_assessment', 'view_assessment',
            
            # Insurance management
            'add_insurancepolicy', 'change_insurancepolicy', 'delete_insurancepolicy', 'view_insurancepolicy',
        ]

    def _get_autocare_permissions(self):
        """Get permission codenames for AutoCare group"""
        return [
            # Vehicle access
            'view_vehicle', 'change_vehicle',
            
            # Maintenance records
            'add_maintenancerecord', 'change_maintenancerecord', 'view_maintenancerecord',
            
            # Inspections
            'add_inspection', 'change_inspection', 'view_inspection',
            
            # Parts management
            'add_part', 'change_part', 'view_part',
            'add_partusage', 'change_partusage', 'view_partusage',
            
            # Scheduled maintenance
            'add_scheduledmaintenance', 'change_scheduledmaintenance', 'view_scheduledmaintenance',
            
            # Vehicle equipment
            'view_powertrainanddrivetrain', 'view_chassissuspensionandbraking',
            'view_electricalsystem', 'view_exteriorfeaturesandbody', 'view_activesafetyandadas',
        ]

    def _get_autoassess_permissions(self):
        """Get permission codenames for AutoAssess group"""
        return [
            # Vehicle access (read-only for assessment)
            'view_vehicle',
            
            # Assessment management
            'add_assessment', 'change_assessment', 'view_assessment',
            
            # Insurance policies
            'add_insurancepolicy', 'change_insurancepolicy', 'view_insurancepolicy',
            
            # Inspections (for assessment purposes)
            'add_inspection', 'change_inspection', 'view_inspection',
            
            # Vehicle equipment (for assessment)
            'view_powertrainanddrivetrain', 'view_chassissuspensionandbraking',
            'view_electricalsystem', 'view_exteriorfeaturesandbody', 'view_activesafetyandadas',
            
            # Vehicle status and history
            'view_vehiclestatus', 'view_vehiclehistory',
        ]

    def _show_summary(self):
        """Show a summary of the created groups"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SIMPLIFIED AUTHENTICATION SYSTEM SUMMARY')
        self.stdout.write('='*60)
        
        groups = Group.objects.filter(name__in=['Staff', 'AutoCare', 'AutoAssess'])
        
        for group in groups:
            self.stdout.write(f'\n{group.name}:')
            self.stdout.write(f'  - Users: {group.user_set.count()}')
            self.stdout.write(f'  - Permissions: {group.permissions.count()}')
            
            # Show dashboard access
            if group.name == 'Staff':
                self.stdout.write('  - Dashboard: /admin/ (Staff Dashboard)')
            elif group.name == 'AutoCare':
                self.stdout.write('  - Dashboard: /dashboard/ (AutoCare Dashboard)')
            elif group.name == 'AutoAssess':
                self.stdout.write('  - Dashboard: /insurance/ (AutoAssess Dashboard)')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Next steps:')
        self.stdout.write('1. Assign users to appropriate groups')
        self.stdout.write('2. Test dashboard access for each group')
        self.stdout.write('3. Remove old organization-based authentication code')
        self.stdout.write('='*60)
