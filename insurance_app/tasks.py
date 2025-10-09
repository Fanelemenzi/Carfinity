# tasks.py (Celery tasks for background processing)
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import *

@shared_task
def calculate_daily_risk_scores():
    """Daily task to recalculate risk scores"""
    from django.core.management import call_command
    call_command('calculate_risk_scores')
    return "Risk scores calculated successfully"

@shared_task
def update_compliance_scores():
    """Daily task to update compliance scores"""
    from django.core.management import call_command
    call_command('update_compliance_scores')
    return "Compliance scores updated successfully"

@shared_task
def generate_maintenance_alerts():
    """Check for overdue maintenance and create alerts"""
    overdue_schedules = MaintenanceSchedule.objects.filter(
        is_completed=False,
        scheduled_date__lt=timezone.now().date()
    ).select_related('vehicle')

    alerts_created = 0
    
    for schedule in overdue_schedules:
        # Check if alert already exists
        existing_alert = RiskAlert.objects.filter(
            vehicle=schedule.vehicle,
            alert_type='maintenance_overdue',
            is_resolved=False,
            description__contains=schedule.maintenance_type
        ).first()

        if not existing_alert:
            days_overdue = schedule.days_overdue()
            severity = 'critical' if days_overdue > 30 else 'high'
            
            RiskAlert.objects.create(
                vehicle=schedule.vehicle,
                alert_type='maintenance_overdue',
                severity=severity,
                title=f'Overdue Maintenance: {schedule.get_maintenance_type_display()}',
                description=f'{schedule.get_maintenance_type_display()} overdue by {days_overdue} days',
                risk_score_impact=days_overdue * 0.1
            )
            alerts_created += 1

    return f"Created {alerts_created} maintenance alerts"

@shared_task
def check_condition_deterioration():
    """Monitor vehicle condition scores for deterioration"""
    vehicles = Vehicle.objects.all()
    alerts_created = 0

    for vehicle in vehicles:
        recent_scores = vehicle.condition_scores.all()[:2]
        
        if len(recent_scores) >= 2:
            latest_score = recent_scores[0].overall_score
            previous_score = recent_scores[1].overall_score
            
            # Check for significant deterioration (>10 point drop)
            if previous_score - latest_score > 10:
                existing_alert = RiskAlert.objects.filter(
                    vehicle=vehicle,
                    alert_type='condition_deterioration',
                    is_resolved=False
                ).first()

                if not existing_alert:
                    RiskAlert.objects.create(
                        vehicle=vehicle,
                        alert_type='condition_deterioration',
                        severity='medium',
                        title=f'Condition Deterioration: {vehicle.manufacture_year} {vehicle.make} {vehicle.model}',
                        description=f'Vehicle health index dropped from {previous_score} to {latest_score}',
                        risk_score_impact=abs(previous_score - latest_score) * 0.05
                    )
                    alerts_created += 1

    return f"Created {alerts_created} condition deterioration alerts"
