"""
Celery tasks for cost analytics calculations and background processing.
"""

from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db import transaction
import logging

from vehicles.models import Vehicle
from notifications.cost_utils import CostCalculationUtils
from notifications.models import VehicleCostAnalytics, VehicleAlert
from notifications.services import AlertService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def calculate_monthly_cost_analytics(self, vehicle_id=None, year=None, month=None):
    """
    Calculate and store monthly cost analytics for vehicles.
    
    Args:
        vehicle_id: Specific vehicle ID (optional, if None processes all vehicles)
        year: Specific year (optional, defaults to current year)
        month: Specific month (optional, defaults to current month)
        
    Returns:
        str: Success message with processing summary
    """
    try:
        # Default to current month if not specified
        if year is None or month is None:
            current_date = date.today()
            year = year or current_date.year
            month = month or current_date.month
        
        # Get vehicles to process
        if vehicle_id:
            vehicles = Vehicle.objects.filter(id=vehicle_id)
            if not vehicles.exists():
                return f"Vehicle with ID {vehicle_id} not found"
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
                        logger.info(f"Processed cost analytics for vehicle {vehicle.id} ({year}-{month:02d})")
                    else:
                        error_count += 1
                        logger.warning(f"Failed to process cost analytics for vehicle {vehicle.id}")
                        
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing vehicle {vehicle.id}: {str(e)}")
        
        result_message = f"Processed {processed_count} vehicles successfully"
        if error_count > 0:
            result_message += f", {error_count} errors occurred"
            
        logger.info(f"Monthly cost analytics task completed: {result_message}")
        return result_message
        
    except Exception as exc:
        logger.error(f"Monthly cost analytics task failed: {str(exc)}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def bulk_calculate_historical_analytics(self, vehicle_id, months=12):
    """
    Calculate historical cost analytics for a specific vehicle.
    
    Args:
        vehicle_id: Vehicle ID to process
        months: Number of months to calculate backwards from current month
        
    Returns:
        str: Success message with processing summary
    """
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        
        processed_count = CostCalculationUtils.bulk_calculate_analytics(vehicle, months)
        
        result_message = f"Calculated historical analytics for vehicle {vehicle_id}: {processed_count} months processed"
        logger.info(result_message)
        return result_message
        
    except Vehicle.DoesNotExist:
        error_message = f"Vehicle with ID {vehicle_id} not found"
        logger.error(error_message)
        return error_message
        
    except Exception as exc:
        logger.error(f"Bulk historical analytics task failed for vehicle {vehicle_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def cleanup_old_analytics(self, months_to_keep=24):
    """
    Clean up old cost analytics records to prevent database bloat.
    
    Args:
        months_to_keep: Number of months of analytics to retain (default: 24)
        
    Returns:
        str: Success message with cleanup summary
    """
    try:
        cutoff_date = date.today() - relativedelta(months=months_to_keep)
        
        deleted_count, _ = VehicleCostAnalytics.objects.filter(
            month__lt=cutoff_date
        ).delete()
        
        result_message = f"Cleaned up {deleted_count} old cost analytics records (older than {cutoff_date})"
        logger.info(result_message)
        return result_message
        
    except Exception as exc:
        logger.error(f"Analytics cleanup task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def recalculate_all_current_month_analytics(self):
    """
    Recalculate cost analytics for all vehicles for the current month.
    Useful for ensuring data accuracy after maintenance record updates.
    
    Returns:
        str: Success message with processing summary
    """
    try:
        current_date = date.today()
        
        # Use the main monthly calculation task
        result = calculate_monthly_cost_analytics.delay(
            vehicle_id=None,
            year=current_date.year,
            month=current_date.month
        )
        
        result_message = f"Triggered recalculation of current month analytics for all vehicles"
        logger.info(result_message)
        return result_message
        
    except Exception as exc:
        logger.error(f"Recalculate all analytics task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def update_vehicle_cost_analytics_on_maintenance(self, maintenance_record_id):
    """
    Update cost analytics when a new maintenance record is added or updated.
    
    Args:
        maintenance_record_id: ID of the maintenance record that was updated
        
    Returns:
        str: Success message
    """
    try:
        from maintenance_history.models import MaintenanceRecord
        
        maintenance_record = MaintenanceRecord.objects.get(id=maintenance_record_id)
        vehicle = maintenance_record.vehicle
        
        # Get the month of the maintenance record
        maintenance_date = maintenance_record.date_performed.date()
        year = maintenance_date.year
        month = maintenance_date.month
        
        # Recalculate analytics for that month
        analytics = CostCalculationUtils.store_monthly_analytics(vehicle, year, month)
        
        if analytics:
            result_message = f"Updated cost analytics for vehicle {vehicle.id} after maintenance record {maintenance_record_id}"
            logger.info(result_message)
            return result_message
        else:
            error_message = f"Failed to update cost analytics for maintenance record {maintenance_record_id}"
            logger.error(error_message)
            return error_message
            
    except Exception as exc:
        logger.error(f"Update analytics on maintenance task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def generate_cost_analytics_report():
    """
    Generate a summary report of cost analytics across all vehicles.
    This task can be used for monitoring and reporting purposes.
    
    Returns:
        dict: Summary statistics
    """
    try:
        current_month = date.today().replace(day=1)
        
        # Get current month analytics
        current_analytics = VehicleCostAnalytics.objects.filter(month=current_month)
        
        total_vehicles = current_analytics.count()
        total_cost = sum(analytics.total_cost for analytics in current_analytics)
        total_parts_cost = sum(analytics.parts_cost for analytics in current_analytics)
        total_labor_cost = sum(analytics.labor_cost for analytics in current_analytics)
        
        # Calculate averages
        avg_cost_per_vehicle = total_cost / total_vehicles if total_vehicles > 0 else 0
        
        report = {
            'month': current_month.strftime('%Y-%m'),
            'total_vehicles': total_vehicles,
            'total_cost': float(total_cost),
            'total_parts_cost': float(total_parts_cost),
            'total_labor_cost': float(total_labor_cost),
            'average_cost_per_vehicle': float(avg_cost_per_vehicle),
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"Generated cost analytics report: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Error generating cost analytics report: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True, max_retries=3)
def generate_vehicle_alerts(self, vehicle_id=None):
    """
    Generate alerts for vehicles based on maintenance schedules, part replacements, and insurance expiry.
    This task runs weekly to check for overdue maintenance and upcoming expirations.
    
    Args:
        vehicle_id: Specific vehicle ID (optional, if None processes all vehicles)
        
    Returns:
        dict: Summary of alerts generated
    """
    try:
        # Get vehicles to process
        if vehicle_id:
            vehicles = Vehicle.objects.filter(id=vehicle_id)
            if not vehicles.exists():
                return {'error': f"Vehicle with ID {vehicle_id} not found"}
        else:
            # Get all vehicles that have current owners
            vehicles = Vehicle.objects.filter(
                ownerships__is_current_owner=True
            ).distinct()
        
        alert_service = AlertService()
        
        total_alerts_created = 0
        vehicles_processed = 0
        error_count = 0
        
        alert_summary = {
            'maintenance_alerts': 0,
            'part_replacement_alerts': 0,
            'insurance_expiry_alerts': 0,
            'total_alerts': 0,
            'vehicles_processed': 0,
            'errors': 0
        }
        
        for vehicle in vehicles:
            try:
                # Generate all types of alerts for this vehicle
                alerts_created = alert_service.generate_all_alerts(vehicle)
                
                # Count alerts by type
                for alert in alerts_created:
                    if alert.alert_type == 'MAINTENANCE_OVERDUE':
                        alert_summary['maintenance_alerts'] += 1
                    elif alert.alert_type == 'PART_REPLACEMENT':
                        alert_summary['part_replacement_alerts'] += 1
                    elif alert.alert_type == 'INSURANCE_EXPIRY':
                        alert_summary['insurance_expiry_alerts'] += 1
                
                total_alerts_created += len(alerts_created)
                vehicles_processed += 1
                
                logger.info(f"Generated {len(alerts_created)} alerts for vehicle {vehicle.id} ({vehicle.vin})")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error generating alerts for vehicle {vehicle.id}: {str(e)}")
        
        alert_summary.update({
            'total_alerts': total_alerts_created,
            'vehicles_processed': vehicles_processed,
            'errors': error_count,
            'generated_at': timezone.now().isoformat()
        })
        
        result_message = (f"Alert generation completed: {total_alerts_created} alerts created "
                         f"for {vehicles_processed} vehicles")
        if error_count > 0:
            result_message += f", {error_count} errors occurred"
            
        logger.info(f"Weekly alert generation task completed: {result_message}")
        
        return alert_summary
        
    except Exception as exc:
        logger.error(f"Weekly alert generation task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def cleanup_resolved_alerts(self, days_to_keep=30):
    """
    Clean up old resolved alerts to prevent database bloat.
    
    Args:
        days_to_keep: Number of days to keep resolved alerts (default: 30)
        
    Returns:
        str: Success message with cleanup summary
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        deleted_count, _ = VehicleAlert.objects.filter(
            is_active=False,
            resolved_at__lt=cutoff_date
        ).delete()
        
        result_message = f"Cleaned up {deleted_count} old resolved alerts (older than {days_to_keep} days)"
        logger.info(result_message)
        return result_message
        
    except Exception as exc:
        logger.error(f"Alert cleanup task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def check_insurance_expiry_alerts(self):
    """
    Specifically check for insurance expiry alerts across all vehicles.
    This task can run more frequently than the main alert generation.
    
    Returns:
        dict: Summary of insurance alerts generated
    """
    try:
        vehicles = Vehicle.objects.filter(
            ownerships__is_current_owner=True
        ).distinct()
        
        alert_service = AlertService()
        
        total_insurance_alerts = 0
        vehicles_processed = 0
        error_count = 0
        
        for vehicle in vehicles:
            try:
                # Generate only insurance expiry alerts
                insurance_alerts = alert_service.check_insurance_expiry(vehicle)
                total_insurance_alerts += len(insurance_alerts)
                vehicles_processed += 1
                
                if insurance_alerts:
                    logger.info(f"Generated {len(insurance_alerts)} insurance alerts for vehicle {vehicle.id}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error checking insurance expiry for vehicle {vehicle.id}: {str(e)}")
        
        summary = {
            'insurance_alerts_created': total_insurance_alerts,
            'vehicles_processed': vehicles_processed,
            'errors': error_count,
            'generated_at': timezone.now().isoformat()
        }
        
        result_message = (f"Insurance expiry check completed: {total_insurance_alerts} alerts created "
                         f"for {vehicles_processed} vehicles")
        if error_count > 0:
            result_message += f", {error_count} errors occurred"
            
        logger.info(f"Insurance expiry check task completed: {result_message}")
        
        return summary
        
    except Exception as exc:
        logger.error(f"Insurance expiry check task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# Periodic task configurations (to be added to settings.py CELERY_BEAT_SCHEDULE)
"""
Add these to your CELERY_BEAT_SCHEDULE in settings.py:

# Cost Analytics Tasks
'calculate-monthly-cost-analytics': {
    'task': 'notifications.tasks.calculate_monthly_cost_analytics',
    'schedule': crontab(day_of_month=1, hour=2, minute=0),  # Run on 1st of each month at 2 AM
},
'cleanup-old-analytics': {
    'task': 'notifications.tasks.cleanup_old_analytics',
    'schedule': crontab(day_of_month=15, hour=3, minute=0),  # Run on 15th of each month at 3 AM
},
'generate-cost-analytics-report': {
    'task': 'notifications.tasks.generate_cost_analytics_report',
    'schedule': crontab(day_of_month=1, hour=4, minute=0),  # Run on 1st of each month at 4 AM
},

# Alert Generation Tasks
'generate-vehicle-alerts': {
    'task': 'notifications.tasks.generate_vehicle_alerts',
    'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Run every Monday at 8 AM
},
'check-insurance-expiry-alerts': {
    'task': 'notifications.tasks.check_insurance_expiry_alerts',
    'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
},
'cleanup-resolved-alerts': {
    'task': 'notifications.tasks.cleanup_resolved_alerts',
    'schedule': crontab(day_of_month=1, hour=1, minute=0),  # Run on 1st of each month at 1 AM
},
"""