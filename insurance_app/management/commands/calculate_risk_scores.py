# management/commands/calculate_risk_scores.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from insurance.models import *

class Command(BaseCommand):
    help = 'Calculate and update risk scores for all vehicles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--policy-id',
            type=int,
            help='Calculate for specific policy ID only',
        )

    def handle(self, *args, **options):
        policy_id = options.get('policy_id')
        
        if policy_id:
            vehicles = Vehicle.objects.filter(policy_id=policy_id)
            self.stdout.write(f'Calculating risk scores for policy {policy_id}...')
        else:
            vehicles = Vehicle.objects.all()
            self.stdout.write('Calculating risk scores for all vehicles...')

        updated_count = 0
        alerts_created = 0

        for vehicle in vehicles:
            old_risk_score = vehicle.risk_score
            new_risk_score = self.calculate_vehicle_risk_score(vehicle)
            
            vehicle.risk_score = new_risk_score
            vehicle.save()
            
            # Update vehicle health index based on latest condition score
            latest_condition = vehicle.condition_scores.first()
            if latest_condition:
                vehicle.vehicle_health_index = latest_condition.overall_score
                vehicle.save()
            
            # Create risk alerts if needed
            if new_risk_score >= 7.0 and old_risk_score < 7.0:
                alert = self.create_risk_alert(vehicle, new_risk_score)
                if alert:
                    alerts_created += 1
            
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} vehicles and created {alerts_created} alerts'
            )
        )

    def calculate_vehicle_risk_score(self, vehicle):
        """Calculate risk score based on multiple factors"""
        risk_factors = {
            'maintenance_compliance': 0,
            'overdue_maintenance': 0,
            'recent_accidents': 0,
            'condition_score': 100,
            'vehicle_age': timezone.now().year - vehicle.year,
            'mileage': vehicle.mileage
        }

        # Get maintenance compliance
        compliance = getattr(vehicle, 'compliance', None)
        if compliance:
            risk_factors['maintenance_compliance'] = compliance.overall_compliance_rate
        
        # Count overdue maintenance
        risk_factors['overdue_maintenance'] = vehicle.maintenance_schedules.filter(
            is_completed=False,
            scheduled_date__lt=timezone.now().date()
        ).count()
        
        # Count recent accidents
        risk_factors['recent_accidents'] = vehicle.accidents.filter(
            accident_date__gte=timezone.now() - timedelta(days=365)
        ).count()
        
        # Get latest condition score
        latest_condition = vehicle.condition_scores.first()
        if latest_condition:
            risk_factors['condition_score'] = latest_condition.overall_score

        # Calculate weighted risk score
        compliance_weight = 0.25
        maintenance_weight = 0.20
        accident_weight = 0.25
        condition_weight = 0.20
        age_weight = 0.05
        mileage_weight = 0.05

        compliance_risk = (100 - risk_factors['maintenance_compliance']) / 10
        maintenance_risk = min(risk_factors['overdue_maintenance'] * 2, 10)
        accident_risk = min(risk_factors['recent_accidents'] * 3, 10)
        condition_risk = (100 - risk_factors['condition_score']) / 10
        age_risk = min(risk_factors['vehicle_age'] / 2, 10)
        mileage_risk = min(risk_factors['mileage'] / 50000, 10)

        total_risk = (
            compliance_risk * compliance_weight +
            maintenance_risk * maintenance_weight +
            accident_risk * accident_weight +
            condition_risk * condition_weight +
            age_risk * age_weight +
            mileage_risk * mileage_weight
        )

        return round(min(total_risk, 10), 2)

    def create_risk_alert(self, vehicle, risk_score):
        """Create appropriate risk alert based on score"""
        if risk_score >= 8.0:
            severity = 'critical'
            title = f'Critical Risk: {vehicle.year} {vehicle.make} {vehicle.model}'
        elif risk_score >= 7.0:
            severity = 'high'
            title = f'High Risk: {vehicle.year} {vehicle.make} {vehicle.model}'
        else:
            return None

        # Check if similar alert already exists
        existing_alert = RiskAlert.objects.filter(
            vehicle=vehicle,
            alert_type='high_risk_vehicle',
            is_resolved=False
        ).first()

        if existing_alert:
            return None

        alert = RiskAlert.objects.create(
            vehicle=vehicle,
            alert_type='high_risk_vehicle',
            severity=severity,
            title=title,
            description=f'Vehicle risk score has increased to {risk_score}. Immediate attention required.',
            risk_score_impact=risk_score
        )

        return alert