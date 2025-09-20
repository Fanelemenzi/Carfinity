from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from users.models import AuthenticationGroup


class Command(BaseCommand):
    help = 'Set up default authentication group configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing configurations (delete and recreate)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting existing authentication group configurations...')
            AuthenticationGroup.objects.all().delete()

        # Default authentication group configurations
        default_configs = [
            {
                'group_name': 'customers',
                'display_name': 'Customer Users',
                'dashboard_type': 'customer',
                'dashboard_url': '/dashboard/',
                'priority': 1,
                'description': 'Regular customers who need access to vehicle information, maintenance records, and inspections',
                'compatible_org_types': ['fleet', 'dealership', 'service', 'other']
            },
            {
                'group_name': 'insurance_company',
                'display_name': 'Insurance Company Users',
                'dashboard_type': 'insurance',
                'dashboard_url': '/insurance/',
                'priority': 2,
                'description': 'Insurance company users who need access to policies, risk assessments, and insurance features',
                'compatible_org_types': ['insurance']
            },
            {
                'group_name': 'technicians',
                'display_name': 'Service Technicians',
                'dashboard_type': 'technician',
                'dashboard_url': '/technician-dashboard/',
                'priority': 1,
                'description': 'Service technicians who need access to maintenance tools and vehicle service records',
                'compatible_org_types': ['service', 'dealership', 'fleet']
            },
            {
                'group_name': 'admins',
                'display_name': 'System Administrators',
                'dashboard_type': 'admin',
                'dashboard_url': '/admin/',
                'priority': 3,
                'description': 'System administrators with full access to all system features',
                'compatible_org_types': ['fleet', 'dealership', 'service', 'insurance', 'other']
            }
        ]

        created_count = 0
        updated_count = 0

        for config in default_configs:
            # Get or create the Django group
            group, group_created = Group.objects.get_or_create(name=config['group_name'])
            
            if group_created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created Django group: {group.name}')
                )

            # Get or create the authentication group configuration
            auth_group, auth_created = AuthenticationGroup.objects.get_or_create(
                group=group,
                defaults={
                    'display_name': config['display_name'],
                    'dashboard_type': config['dashboard_type'],
                    'dashboard_url': config['dashboard_url'],
                    'priority': config['priority'],
                    'description': config['description'],
                    'compatible_org_types': config['compatible_org_types'],
                    'is_active': True
                }
            )

            if auth_created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created authentication group config: {auth_group.display_name}')
                )
            else:
                # Update existing configuration
                auth_group.display_name = config['display_name']
                auth_group.dashboard_type = config['dashboard_type']
                auth_group.dashboard_url = config['dashboard_url']
                auth_group.priority = config['priority']
                auth_group.description = config['description']
                auth_group.compatible_org_types = config['compatible_org_types']
                auth_group.is_active = True
                auth_group.save()
                
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated authentication group config: {auth_group.display_name}')
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSetup completed successfully!'
                f'\n- Created: {created_count} authentication group configurations'
                f'\n- Updated: {updated_count} authentication group configurations'
            )
        )

        # Show current active configurations
        self.stdout.write('\nCurrent active authentication groups:')
        for auth_group in AuthenticationGroup.objects.filter(is_active=True).order_by('-priority'):
            self.stdout.write(
                f'  • {auth_group.display_name} ({auth_group.group.name}) -> {auth_group.dashboard_url} '
                f'[Priority: {auth_group.priority}]'
            )