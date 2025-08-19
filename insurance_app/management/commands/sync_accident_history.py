# management/commands/sync_accident_history.py
from django.core.management.base import BaseCommand
from django.db import transaction
from insurance_app.models import Accident
from insurance_app.utils import AccidentHistorySyncManager
from vehicles.models import Vehicle, VehicleHistory

class Command(BaseCommand):
    help = 'Synchronize accident records between insurance app and vehicle history'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicle-id',
            type=int,
            help='Sync accidents for specific vehicle ID only',
        )
        parser.add_argument(
            '--import-history',
            action='store_true',
            help='Import accident records from vehicle history to insurance app',
        )
        parser.add_argument(
            '--create-history',
            action='store_true',
            help='Create vehicle history records for insurance accidents that don\'t have them',
        )
        parser.add_argument(
            '--sync-existing',
            action='store_true',
            help='Sync existing linked records',
        )

    def handle(self, *args, **options):
        vehicle_id = options.get('vehicle_id')
        import_history = options.get('import_history', False)
        create_history = options.get('create_history', False)
        sync_existing = options.get('sync_existing', False)

        if vehicle_id:
            vehicles = Vehicle.objects.filter(id=vehicle_id)
            self.stdout.write(f'Processing accidents for vehicle {vehicle_id}...')
        else:
            vehicles = Vehicle.objects.all()
            self.stdout.write('Processing accidents for all vehicles...')

        imported_count = 0
        created_count = 0
        synced_count = 0
        error_count = 0

        with transaction.atomic():
            for vehicle in vehicles:
                try:
                    # Import vehicle history accidents to insurance app
                    if import_history:
                        count = AccidentHistorySyncManager.import_vehicle_history_accidents(
                            vehicle, create_insurance_records=True
                        )
                        imported_count += count
                        if count > 0:
                            self.stdout.write(
                                f'Imported {count} accident records for {vehicle}'
                            )

                    # Create vehicle history records for insurance accidents
                    if create_history:
                        insurance_accidents = Accident.objects.filter(
                            vehicle=vehicle,
                            vehicle_history__isnull=True
                        )
                        
                        for accident in insurance_accidents:
                            AccidentHistorySyncManager.create_vehicle_history_from_accident(accident)
                            created_count += 1
                            self.stdout.write(
                                f'Created vehicle history for accident {accident.id}'
                            )

                    # Sync existing linked records
                    if sync_existing:
                        linked_accidents = Accident.objects.filter(
                            vehicle=vehicle,
                            vehicle_history__isnull=False
                        )
                        
                        for accident in linked_accidents:
                            accident.sync_with_vehicle_history()
                            synced_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error processing vehicle {vehicle.id}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Sync completed: {imported_count} imported, {created_count} created, '
                f'{synced_count} synced, {error_count} errors'
            )
        )

        # Show comprehensive accident data for verification
        if vehicle_id:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            comprehensive_data = AccidentHistorySyncManager.get_comprehensive_accident_data(vehicle)
            
            self.stdout.write(f'\nComprehensive accident data for vehicle {vehicle_id}:')
            for data in comprehensive_data:
                self.stdout.write(
                    f"- {data['type']}: {data['date']} - {data['severity']} - {data['description'][:50]}..."
                )