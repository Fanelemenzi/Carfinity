"""
Management command for group-based authentication system maintenance.

This command provides various utilities for managing the authentication system:
- Check permission conflicts
- Sync users with organization groups
- Generate permission reports
- Fix common permission issues
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.db.models import Count
from users.services import AuthenticationService, OrganizationService
from organizations.models import Organization, OrganizationUser
import csv
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage group-based authentication system'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=[
                'check-conflicts',
                'sync-org-groups',
                'generate-report',
                'fix-permissions',
                'list-users-without-groups',
                'list-users-without-orgs',
                'validate-system'
            ],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for reports (CSV format)'
        )
        
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID to process (for targeted operations)'
        )
        
        parser.add_argument(
            '--org-id',
            type=int,
            help='Specific organization ID to process'
        )
        
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually fix issues (dry-run by default)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if options['verbose']:
            self.stdout.write(f"Executing action: {action}")
        
        try:
            if action == 'check-conflicts':
                self.check_conflicts(options)
            elif action == 'sync-org-groups':
                self.sync_org_groups(options)
            elif action == 'generate-report':
                self.generate_report(options)
            elif action == 'fix-permissions':
                self.fix_permissions(options)
            elif action == 'list-users-without-groups':
                self.list_users_without_groups(options)
            elif action == 'list-users-without-orgs':
                self.list_users_without_orgs(options)
            elif action == 'validate-system':
                self.validate_system(options)
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except Exception as e:
            raise CommandError(f"Error executing {action}: {e}")

    def check_conflicts(self, options):
        """Check for permission conflicts across all users"""
        self.stdout.write("Checking permission conflicts...")
        
        users = User.objects.all()
        if options.get('user_id'):
            users = users.filter(id=options['user_id'])
        
        conflicts_found = 0
        total_users = users.count()
        
        for user in users:
            permissions = AuthenticationService.get_user_permissions(user)
            
            if permissions.has_conflicts:
                conflicts_found += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"CONFLICT - User: {user.username} ({user.email})"
                    )
                )
                self.stdout.write(f"  Details: {permissions.conflict_details}")
                self.stdout.write(f"  Groups: {permissions.groups}")
                self.stdout.write(f"  Org Type: {permissions.organization_type}")
                self.stdout.write(f"  Available Dashboards: {permissions.available_dashboards}")
                self.stdout.write("")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Conflict check complete: {conflicts_found} conflicts found out of {total_users} users"
            )
        )

    def sync_org_groups(self, options):
        """Sync users with their organization groups"""
        self.stdout.write("Syncing users with organization groups...")
        
        organizations = Organization.objects.all()
        if options.get('org_id'):
            organizations = organizations.filter(id=options['org_id'])
        
        total_synced = 0
        total_errors = 0
        
        for org in organizations:
            if options['verbose']:
                self.stdout.write(f"Processing organization: {org.name}")
            
            try:
                sync_stats = OrganizationService.sync_organization_groups(org)
                total_synced += sync_stats['members_processed']
                total_errors += sync_stats['errors']
                
                if options['verbose']:
                    self.stdout.write(f"  Members processed: {sync_stats['members_processed']}")
                    self.stdout.write(f"  Groups added: {sync_stats['groups_added']}")
                    self.stdout.write(f"  Errors: {sync_stats['errors']}")
                    
            except Exception as e:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(f"Error syncing organization {org.name}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete: {total_synced} users processed, {total_errors} errors"
            )
        )

    def generate_report(self, options):
        """Generate comprehensive permission report"""
        self.stdout.write("Generating permission report...")
        
        users = User.objects.select_related('profile').prefetch_related('groups').all()
        
        report_data = []
        for user in users:
            permissions = AuthenticationService.get_user_permissions(user)
            org = OrganizationService.get_user_organization(user)
            org_role = OrganizationService.get_user_organization_role(user)
            
            report_data.append({
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'groups': ', '.join(permissions.groups),
                'organization': org.name if org else '',
                'organization_type': permissions.organization_type or '',
                'organization_role': org_role or '',
                'available_dashboards': ', '.join(permissions.available_dashboards),
                'default_dashboard': permissions.default_dashboard or '',
                'has_conflicts': 'Yes' if permissions.has_conflicts else 'No',
                'conflict_details': permissions.conflict_details or '',
                'is_active': 'Yes' if user.is_active else 'No',
                'is_staff': 'Yes' if user.is_staff else 'No',
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        # Output to file if specified
        if options.get('output'):
            with open(options['output'], 'w', newline='', encoding='utf-8') as csvfile:
                if report_data:
                    fieldnames = report_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(report_data)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"Report saved to {options['output']}")
                    )
                else:
                    self.stdout.write(self.style.WARNING("No data to export"))
        else:
            # Output to console
            self.stdout.write(f"{'Username':<20} {'Email':<30} {'Groups':<20} {'Organization':<20} {'Conflicts':<10}")
            self.stdout.write("-" * 100)
            
            for row in report_data:
                conflicts_display = "YES" if row['has_conflicts'] == 'Yes' else "No"
                style = self.style.WARNING if row['has_conflicts'] == 'Yes' else self.style.SUCCESS
                
                self.stdout.write(
                    style(f"{row['username']:<20} {row['email']:<30} {row['groups']:<20} {row['organization']:<20} {conflicts_display:<10}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Report generated for {len(report_data)} users")
        )

    def fix_permissions(self, options):
        """Attempt to fix common permission issues"""
        if not options.get('fix'):
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - Use --fix to actually make changes")
            )
        
        self.stdout.write("Analyzing permission issues...")
        
        users = User.objects.all()
        if options.get('user_id'):
            users = users.filter(id=options['user_id'])
        
        fixes_applied = 0
        
        for user in users:
            permissions = AuthenticationService.get_user_permissions(user)
            
            if permissions.has_conflicts:
                if options['verbose']:
                    self.stdout.write(f"Analyzing user: {user.username}")
                
                # Try to fix users with no groups but have organization
                if not permissions.groups and permissions.organization_type:
                    recommended_groups = OrganizationService.get_organization_required_groups(permissions.organization_type)
                    
                    if recommended_groups:
                        self.stdout.write(
                            f"  Fix: Add user {user.username} to groups {recommended_groups} based on org type {permissions.organization_type}"
                        )
                        
                        if options.get('fix'):
                            for group_name in recommended_groups:
                                try:
                                    group = Group.objects.get(name=group_name)
                                    user.groups.add(group)
                                    fixes_applied += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(f"    Added {user.username} to group {group_name}")
                                    )
                                except Group.DoesNotExist:
                                    self.stdout.write(
                                        self.style.ERROR(f"    Group {group_name} does not exist")
                                    )
                
                # Try to sync users with their organization groups
                org = OrganizationService.get_user_organization(user)
                if org and org.linked_groups.exists():
                    self.stdout.write(
                        f"  Fix: Sync user {user.username} with organization groups"
                    )
                    
                    if options.get('fix'):
                        org.add_user_to_groups(user)
                        fixes_applied += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"    Synced {user.username} with organization groups")
                        )
        
        if options.get('fix'):
            self.stdout.write(
                self.style.SUCCESS(f"Applied {fixes_applied} fixes")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Would apply {fixes_applied} fixes (use --fix to execute)")
            )

    def list_users_without_groups(self, options):
        """List users who have no group assignments"""
        self.stdout.write("Finding users without groups...")
        
        users_without_groups = User.objects.annotate(
            group_count=Count('groups')
        ).filter(group_count=0, is_active=True)
        
        if users_without_groups.exists():
            self.stdout.write(f"Found {users_without_groups.count()} users without groups:")
            self.stdout.write("")
            
            for user in users_without_groups:
                org = OrganizationService.get_user_organization(user)
                org_info = f" (Org: {org.name} - {org.organization_type})" if org else " (No organization)"
                
                self.stdout.write(
                    self.style.WARNING(f"  {user.username} ({user.email}){org_info}")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("All active users have group assignments!")
            )

    def list_users_without_orgs(self, options):
        """List users who have no organization assignments"""
        self.stdout.write("Finding users without organizations...")
        
        users_with_orgs = OrganizationUser.objects.filter(
            is_active=True
        ).values_list('user_id', flat=True)
        
        users_without_orgs = User.objects.exclude(
            id__in=users_with_orgs
        ).filter(is_active=True)
        
        if users_without_orgs.exists():
            self.stdout.write(f"Found {users_without_orgs.count()} users without organizations:")
            self.stdout.write("")
            
            for user in users_without_orgs:
                groups = list(user.groups.values_list('name', flat=True))
                group_info = f" (Groups: {', '.join(groups)})" if groups else " (No groups)"
                
                self.stdout.write(
                    self.style.WARNING(f"  {user.username} ({user.email}){group_info}")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("All active users have organization assignments!")
            )

    def validate_system(self, options):
        """Validate the entire authentication system"""
        self.stdout.write("Validating authentication system...")
        self.stdout.write("")
        
        # Check groups
        required_groups = ['customers', 'insurance_company']
        existing_groups = list(Group.objects.values_list('name', flat=True))
        
        self.stdout.write("1. Checking required groups:")
        for group_name in required_groups:
            if group_name in existing_groups:
                group = Group.objects.get(name=group_name)
                member_count = group.user_set.count()
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {group_name} exists ({member_count} members)")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {group_name} missing")
                )
        
        # Check organizations
        self.stdout.write("\n2. Checking organizations:")
        org_count = Organization.objects.count()
        orgs_with_groups = Organization.objects.filter(linked_groups__isnull=False).distinct().count()
        
        self.stdout.write(f"  Total organizations: {org_count}")
        self.stdout.write(f"  Organizations with linked groups: {orgs_with_groups}")
        
        if orgs_with_groups < org_count:
            self.stdout.write(
                self.style.WARNING(f"  {org_count - orgs_with_groups} organizations have no linked groups")
            )
        
        # Check users
        self.stdout.write("\n3. Checking users:")
        total_users = User.objects.filter(is_active=True).count()
        users_with_groups = User.objects.filter(is_active=True, groups__isnull=False).distinct().count()
        users_with_orgs = User.objects.filter(
            is_active=True,
            id__in=OrganizationUser.objects.filter(is_active=True).values_list('user_id', flat=True)
        ).count()
        
        self.stdout.write(f"  Total active users: {total_users}")
        self.stdout.write(f"  Users with groups: {users_with_groups}")
        self.stdout.write(f"  Users with organizations: {users_with_orgs}")
        
        # Check conflicts
        self.stdout.write("\n4. Checking conflicts:")
        conflict_count = 0
        for user in User.objects.filter(is_active=True):
            permissions = AuthenticationService.get_user_permissions(user)
            if permissions.has_conflicts:
                conflict_count += 1
        
        if conflict_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ No permission conflicts found")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"  ⚠ {conflict_count} users have permission conflicts")
            )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        if conflict_count == 0 and orgs_with_groups == org_count:
            self.stdout.write(
                self.style.SUCCESS("✓ Authentication system validation passed!")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠ Authentication system has issues that need attention")
            )
            self.stdout.write("  Run 'check-conflicts' and 'fix-permissions' commands for details")