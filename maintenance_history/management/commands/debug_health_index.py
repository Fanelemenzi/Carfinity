from django.core.management.base import BaseCommand
from maintenance_history.models import InitialInspection
import json


class Command(BaseCommand):
    help = 'Debug health index calculations for initial inspections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inspection-id',
            type=int,
            help='Specific inspection ID to debug',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Debug all initial inspections',
        )
        parser.add_argument(
            '--recalculate',
            action='store_true',
            help='Force recalculation of health index',
        )

    def handle(self, *args, **options):
        if options['inspection_id']:
            try:
                inspection = InitialInspection.objects.get(pk=options['inspection_id'])
                self.debug_inspection(inspection, options['recalculate'])
            except InitialInspection.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Inspection with ID {options["inspection_id"]} not found')
                )
        elif options['all']:
            inspections = InitialInspection.objects.all()
            for inspection in inspections:
                self.debug_inspection(inspection, options['recalculate'])
                self.stdout.write('-' * 80)
        else:
            # Debug the most recent inspection
            try:
                inspection = InitialInspection.objects.latest('created_at')
                self.debug_inspection(inspection, options['recalculate'])
            except InitialInspection.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('No initial inspections found')
                )

    def debug_inspection(self, inspection, recalculate=False):
        self.stdout.write(f'\n=== Debugging Inspection {inspection.pk} ===')
        self.stdout.write(f'VIN: {inspection.vehicle.vin}')
        self.stdout.write(f'Inspection Number: {inspection.inspection_number}')
        self.stdout.write(f'Is Completed: {inspection.is_completed}')
        self.stdout.write(f'Completion Percentage: {inspection.completion_percentage}%')
        
        # Get field weights and check data
        try:
            from maintenance_history.utils import get_initial_inspection_field_weights
            field_weights = get_initial_inspection_field_weights()
            
            # Combine all systems
            all_systems = {}
            for category in field_weights.values():
                all_systems.update(category)
            
            total_fields = len(all_systems)
            filled_fields = 0
            field_values = {}
            
            # Check field values
            for field_name, weight in all_systems.items():
                field_value = getattr(inspection, field_name, None)
                if field_value:
                    filled_fields += 1
                field_values[field_name] = field_value
            
            self.stdout.write(f'Total Fields: {total_fields}')
            self.stdout.write(f'Filled Fields: {filled_fields}')
            
            # Try direct calculation
            calculation_error = None
            health_index = None
            inspection_result = None
            
            try:
                health_index, inspection_result = inspection.get_health_index_calculation()
                self.stdout.write(
                    self.style.SUCCESS(f'Health Index: {health_index}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Inspection Result: {inspection_result}')
                )
            except Exception as calc_error:
                calculation_error = str(calc_error)
                self.stdout.write(
                    self.style.ERROR(f'Calculation Error: {calculation_error}')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Debug setup failed: {str(e)}')
            )
            return
        
        # Show current property values
        self.stdout.write(f'\nCurrent Property Values:')
        self.stdout.write(f'vehicle_health_index: {inspection.vehicle_health_index}')
        self.stdout.write(f'inspection_result: {inspection.inspection_result}')
        
        # Show some sample field values
        self.stdout.write(f'\nSample Field Values:')
        sample_fields = ['brake_vibrations', 'steering_feel', 'tire_condition', 'brake_pad_life']
        for field in sample_fields:
            if field in field_values:
                value = field_values[field]
                self.stdout.write(f'  {field}: {value}')
        
        # Show failed points and critical issues
        try:
            failed_points = inspection.failed_points
            critical_issues = inspection.safety_critical_issues
            self.stdout.write(f'\nFailed Points: {len(failed_points)}')
            self.stdout.write(f'Critical Issues: {len(critical_issues)}')
        except Exception as e:
            self.stdout.write(f'Error getting failed points/critical issues: {str(e)}')
        
        if recalculate:
            self.stdout.write('\nForcing recalculation...')
            try:
                if inspection.is_completed:
                    inspection._update_calculated_fields()
                    self.stdout.write(
                        self.style.SUCCESS('Recalculation completed')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('Inspection not marked as completed - skipping recalculation')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Recalculation failed: {str(e)}')
                )
