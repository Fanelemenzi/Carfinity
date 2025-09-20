from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create Django groups for customers and insurance_company with appropriate permissions'

    def handle(self, *args, **options):
        # Create customers group
        customers_group, created = Group.objects.get_or_create(name='customers')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created "customers" group')
            )
        else:
            self.stdout.write(
                self.style.WARNING('"customers" group already exists')
            )

        # Create insurance_company group
        insurance_group, created = Group.objects.get_or_create(name='insurance_company')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Successfully created "insurance_company" group')
            )
        else:
            self.stdout.write(
                self.style.WARNING('"insurance_company" group already exists')
            )

        # Add basic permissions to customers group
        try:
            # Get content types for relevant models
            from vehicles.models import Vehicle
            from maintenance_history.models import MaintenanceRecord, Inspection
            
            vehicle_ct = ContentType.objects.get_for_model(Vehicle)
            maintenance_ct = ContentType.objects.get_for_model(MaintenanceRecord)
            inspection_ct = ContentType.objects.get_for_model(Inspection)
            
            # Customer permissions - view their own data
            customer_permissions = [
                Permission.objects.get(content_type=vehicle_ct, codename='view_vehicle'),
                Permission.objects.get(content_type=maintenance_ct, codename='view_maintenancerecord'),
                Permission.objects.get(content_type=inspection_ct, codename='view_inspection'),
            ]
            
            customers_group.permissions.set(customer_permissions)
            self.stdout.write(
                self.style.SUCCESS('Added permissions to customers group')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not add permissions to customers group: {e}')
            )

        # Add permissions to insurance_company group
        try:
            from insurance_app.models import InsurancePolicy
            
            insurance_ct = ContentType.objects.get_for_model(InsurancePolicy)
            
            # Insurance company permissions - broader access
            insurance_permissions = [
                Permission.objects.get(content_type=vehicle_ct, codename='view_vehicle'),
                Permission.objects.get(content_type=maintenance_ct, codename='view_maintenancerecord'),
                Permission.objects.get(content_type=inspection_ct, codename='view_inspection'),
                Permission.objects.get(content_type=insurance_ct, codename='view_insurancepolicy'),
                Permission.objects.get(content_type=insurance_ct, codename='add_insurancepolicy'),
                Permission.objects.get(content_type=insurance_ct, codename='change_insurancepolicy'),
            ]
            
            insurance_group.permissions.set(insurance_permissions)
            self.stdout.write(
                self.style.SUCCESS('Added permissions to insurance_company group')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not add permissions to insurance_company group: {e}')
            )

        self.stdout.write(
            self.style.SUCCESS('Group setup completed successfully!')
        )