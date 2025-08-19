# management/commands/generate_risk_report.py
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, Q
from insurance.models import *
import csv
from datetime import datetime

class Command(BaseCommand):
    help = 'Generate comprehensive risk assessment report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='risk_report.csv',
            help='Output filename for the report',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            default='csv',
            help='Output format (csv or json)',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        output_format = options['format']

        self.stdout.write('Generating risk assessment report...')

        # Collect comprehensive data
        vehicles_data = []
        
        for vehicle in Vehicle.objects.select_related('policy', 'compliance').all():
            compliance = getattr(vehicle, 'compliance', None)
            latest_condition = vehicle.condition_scores.first()
            overdue_maintenance = vehicle.maintenance_schedules.filter(
                is_completed=False,
                scheduled_date__lt=timezone.now().date()
            ).count()
            
            recent_accidents = vehicle.accidents.filter(
                accident_date__gte=timezone.now() - timedelta(days=365)
            ).count()
            
            active_alerts = vehicle.risk_alerts.filter(is_resolved=False).count()

            vehicle_data = {
                'policy_number': vehicle.policy.policy_number,
                'vin': vehicle.vin,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year,
                'mileage': vehicle.mileage,
                'risk_score': vehicle.risk_score,
                'health_index': vehicle.vehicle_health_index,
                'compliance_rate': compliance.overall_compliance_rate if compliance else 0,
                'critical_compliance': compliance.critical_maintenance_compliance if compliance else 0,
                'overdue_maintenance': overdue_maintenance,
                'recent_accidents': recent_accidents,
                'condition_score': latest_condition.overall_score if latest_condition else 0,
                'active_alerts': active_alerts,
                'last_inspection': vehicle.last_inspection_date or 'Never'
            }
            vehicles_data.append(vehicle_data)

        if output_format == 'csv':
            self.write_csv_report(vehicles_data, output_file)
        else:
            self.write_json_report(vehicles_data, output_file)

        self.stdout.write(
            self.style.SUCCESS(f'Report generated: {output_file}')
        )

    def write_csv_report(self, data, filename):
        with open(filename, 'w', newline='') as csvfile:
            if not data:
                return
            
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                writer.writerow(row)

    def write_json_report(self, data, filename):
        import json
        with open(filename, 'w') as jsonfile:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_vehicles': len(data),
                'vehicles': data
            }, jsonfile, indent=2, default=str)