# management/commands/update_compliance_scores.py
from django.core.management.base import BaseCommand
from insurance.models import *

class Command(BaseCommand):
    help = 'Update maintenance compliance scores for all vehicles'

    def handle(self, *args, **options):
        vehicles = Vehicle.objects.all()
        updated_count = 0

        for vehicle in vehicles:
            compliance, created = MaintenanceCompliance.objects.get_or_create(
                vehicle=vehicle
            )
            compliance.calculate_compliance()
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Updated compliance scores for {updated_count} vehicles')
        )