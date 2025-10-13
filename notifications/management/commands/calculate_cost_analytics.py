"""
Management command to calculate cost analytics for vehicles.
Usage: python manage.py calculate_cost_analytics [--vehicle-id ID] [--months N] [--year YYYY] [--month MM]
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from datetime import date
import logging

from vehicles.models import Vehicle
from notifications.cost_utils import CostCalculationUtils
from notifications.tasks import calculate_monthly_cost_analytics, bulk_calculate_historical_analytics

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate cost analytics for vehicles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicle-id',
            type=int,
            help='Calculate analytics for specific vehicle ID'
        )
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Number of months to calculate (for historical calculation)'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Specific year to calculate (defaults to current year)'
        )
        parser.add_argument(
            '--month',
            type=int,
            help='Specific month to calculate (defaults to current month)'
        )
        parser.add_argument(
            '--historical',
            action='store_true',
            help='Calculate historical analytics for specified months'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run calculations asynchronously using Celery'
        )

    def handle(self, *args, **options):
        vehicle_id = options.get('vehicle_id')
        months = options.get('months', 12)
        year = options.get('year')
        month = options.get('month')
        historical = options.get('historical', False)
        use_async = options.get('async', False)

        # Default to current date if not specified
        current_date = date.today()
        year = year or current_date.year
        month = month or current_date.month

        try:
            if historical:
                # Calculate historical analytics
                if vehicle_id:
                    if use_async:
                        task = bulk_calculate_historical_analytics.delay(vehicle_id, months)
                        self.stdout.write(
                            self.style.SUCCESS(f'Started historical analytics calculation task: {task.id}')
                        )
                    else:
                        vehicle = Vehicle.objects.get(id=vehicle_id)
                        count = CostCalculationUtils.bulk_calculate_analytics(vehicle, months)
                        self.stdout.write(
                            self.style.SUCCESS(f'Calculated historical analytics for vehicle {vehicle_id}: {count} months')
                        )
                else:
                    # Calculate historical for all vehicles
                    vehicles = Vehicle.objects.all()
                    total_processed = 0
                    
                    for vehicle in vehicles:
                        if use_async:
                            bulk_calculate_historical_analytics.delay(vehicle.id, months)
                        else:
                            count = CostCalculationUtils.bulk_calculate_analytics(vehicle, months)
                            total_processed += count
                    
                    if use_async:
                        self.stdout.write(
                            self.style.SUCCESS(f'Started historical analytics tasks for {vehicles.count()} vehicles')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'Calculated historical analytics: {total_processed} total months processed')
                        )
            else:
                # Calculate for specific month
                if use_async:
                    task = calculate_monthly_cost_analytics.delay(vehicle_id, year, month)
                    self.stdout.write(
                        self.style.SUCCESS(f'Started monthly analytics calculation task: {task.id}')
                    )
                else:
                    if vehicle_id:
                        vehicles = Vehicle.objects.filter(id=vehicle_id)
                        if not vehicles.exists():
                            raise CommandError(f'Vehicle with ID {vehicle_id} not found')
                    else:
                        vehicles = Vehicle.objects.all()

                    processed_count = 0
                    error_count = 0

                    for vehicle in vehicles:
                        try:
                            with transaction.atomic():
                                analytics = CostCalculationUtils.store_monthly_analytics(vehicle, year, month)
                                if analytics:
                                    processed_count += 1
                                    self.stdout.write(f'Processed vehicle {vehicle.id} ({vehicle.vin})')
                                else:
                                    error_count += 1
                                    self.stdout.write(
                                        self.style.WARNING(f'Failed to process vehicle {vehicle.id}')
                                    )
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Error processing vehicle {vehicle.id}: {str(e)}')
                            )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Completed: {processed_count} vehicles processed, {error_count} errors'
                        )
                    )

        except Vehicle.DoesNotExist:
            raise CommandError(f'Vehicle with ID {vehicle_id} not found')
        except Exception as e:
            raise CommandError(f'Error calculating cost analytics: {str(e)}')

        self.stdout.write(
            self.style.SUCCESS('Cost analytics calculation completed successfully')
        )