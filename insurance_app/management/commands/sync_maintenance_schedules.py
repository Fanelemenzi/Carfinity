# management/commands/sync_maintenance_schedules.py
from django.core.management.base import BaseCommand
from django.db import transaction
from insurance_app.models import MaintenanceSchedule, Vehicle
from maintenance.models import ScheduledMaintenance, AssignedVehiclePlan
from vehicles.models import Vehicle as VehicleModel

class Command(BaseCommand):
    help = 'Synchronize maintenance schedules between maintenance app and insurance app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicle-id',
            type=int,
            help='Sync schedules for specific vehicle ID only',
        )
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create insurance schedules for maintenance schedules that don\'t have them',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing insurance schedules from maintenance app data',
        )

    def handle(self, *args, **options):
        vehicle_id = options.get('vehicle_id')
        create_missing = options.get('create_missing', False)
        update_existing = options.get('update_existing', False)

        if vehicle_id:
            scheduled_maintenances = ScheduledMaintenance.objects.filter(
                assigned_plan__vehicle_id=vehicle_id
            ).select_related('assigned_plan__vehicle', 'task')
            self.stdout.write(f'Syncing schedules for vehicle {vehicle_id}...')
        else:
            scheduled_maintenances = ScheduledMaintenance.objects.all().select_related(
                'assigned_plan__vehicle', 'task'
            )
            self.stdout.write('Syncing all maintenance schedules...')

        created_count = 0
        updated_count = 0
        error_count = 0

        with transaction.atomic():
            for scheduled_maintenance in scheduled_maintenances:
                try:
                    vehicle = scheduled_maintenance.assigned_plan.vehicle
                    
                    # Check if insurance schedule already exists
                    insurance_schedule = MaintenanceSchedule.objects.filter(
                        scheduled_maintenance=scheduled_maintenance
                    ).first()

                    if insurance_schedule:
                        if update_existing:
                            # Update existing insurance schedule
                            insurance_schedule.sync_with_maintenance_app()
                            updated_count += 1
                            self.stdout.write(
                                f'Updated: {vehicle} - {scheduled_maintenance.task.name}'
                            )
                    else:
                        if create_missing:
                            # Create new insurance schedule
                            insurance_schedule = MaintenanceSchedule.create_from_scheduled_maintenance(
                                scheduled_maintenance, vehicle
                            )
                            created_count += 1
                            self.stdout.write(
                                f'Created: {vehicle} - {scheduled_maintenance.task.name}'
                            )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error processing {scheduled_maintenance}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Sync completed: {created_count} created, {updated_count} updated, {error_count} errors'
            )
        )

        # Update compliance scores after sync
        if created_count > 0 or updated_count > 0:
            self.stdout.write('Updating compliance scores...')
            from django.core.management import call_command
            call_command('update_compliance_scores')