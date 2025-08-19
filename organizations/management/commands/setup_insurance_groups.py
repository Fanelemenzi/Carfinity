from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from organizations.models import Organization, InsuranceOrganization


class Command(BaseCommand):
    help = 'Set up default insurance groups and permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-org',
            action='store_true',
            help='Create a sample insurance organization',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up insurance groups...')
        
        # Define insurance-related groups and their permissions
        insurance_groups = {
            'Insurance Admins': [
                'add_insurancepolicy', 'change_insurancepolicy', 'delete_insurancepolicy', 'view_insurancepolicy',
                'add_organization', 'change_organization', 'delete_organization', 'view_organization',
                'add_insuranceorganization', 'change_insuranceorganization', 'view_insuranceorganization',
            ],
            'Insurance Agents': [
                'add_insurancepolicy', 'change_insurancepolicy', 'view_insurancepolicy',
                'view_organization', 'view_insuranceorganization',
            ],
            'Underwriters': [
                'view_insurancepolicy', 'change_insurancepolicy',
                'view_organization', 'view_insuranceorganization',
            ],
            'Claims Adjusters': [
                'view_insurancepolicy',
                'view_organization',
            ],
            'Fleet Managers': [
                'view_organization', 'change_organization',
                'add_organizationvehicle', 'change_organizationvehicle', 'view_organizationvehicle',
                'view_insurancepolicy',
            ],
        }
        
        created_groups = {}
        
        for group_name, permissions in insurance_groups.items():
            group, created = Group.objects.get_or_create(name=group_name)
            created_groups[group_name] = group
            
            if created:
                self.stdout.write(f'Created group: {group_name}')
            else:
                self.stdout.write(f'Group already exists: {group_name}')
            
            # Add permissions to group
            for perm_codename in permissions:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(f'Warning: Permission {perm_codename} not found')
        
        self.stdout.write('Insurance groups setup completed!')
        
        # Create sample organization if requested
        if options['create_sample_org']:
            self.create_sample_organization(created_groups)

    def create_sample_organization(self, groups):
        self.stdout.write('Creating sample insurance organization...')
        
        # Create sample insurance organization
        org, created = Organization.objects.get_or_create(
            name='Carfinity Insurance Co.',
            defaults={
                'organization_type': 'insurance',
                'is_insurance_provider': True,
                'contact_email': 'info@carfinity-insurance.com',
                'contact_phone': '+1-555-0123',
                'address': '123 Insurance Blvd',
                'city': 'Insurance City',
                'state': 'IC',
                'country': 'USA',
                'postal_code': '12345',
                'insurance_license_number': 'INS-12345',
                'insurance_rating': 'A+',
            }
        )
        
        if created:
            self.stdout.write(f'Created organization: {org.name}')
            
            # Link relevant groups to the organization
            insurance_groups = ['Insurance Admins', 'Insurance Agents', 'Underwriters', 'Claims Adjusters']
            for group_name in insurance_groups:
                if group_name in groups:
                    org.linked_groups.add(groups[group_name])
            
            # Create insurance organization details
            insurance_org, created = InsuranceOrganization.objects.get_or_create(
                organization=org,
                defaults={
                    'naic_number': '12345',
                    'am_best_rating': 'A+',
                    'states_licensed': 'CA,NY,TX,FL',
                    'max_risk_score_threshold': 7.0,
                    'auto_approve_low_risk': True,
                    'require_inspection_threshold': 5.0,
                    'send_maintenance_alerts': True,
                    'send_risk_alerts': True,
                    'alert_email': 'alerts@carfinity-insurance.com',
                }
            )
            
            if created:
                self.stdout.write('Created insurance organization details')
        
        else:
            self.stdout.write(f'Organization already exists: {org.name}')
        
        self.stdout.write('Sample organization setup completed!')