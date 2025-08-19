# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from maintenance.models import ScheduledMaintenance
from vehicles.models import VehicleHistory
from .models import MaintenanceSchedule, Accident

@receiver(post_save, sender=ScheduledMaintenance)
def sync_scheduled_maintenance_on_save(sender, instance, created, **kwargs):
    """
    Automatically sync insurance maintenance schedule when maintenance app schedule is updated
    """
    try:
        # Check if insurance schedule exists
        insurance_schedule = MaintenanceSchedule.objects.filter(
            scheduled_maintenance=instance
        ).first()

        if insurance_schedule:
            # Update existing insurance schedule
            insurance_schedule.sync_with_maintenance_app()
        else:
            # Create new insurance schedule if it doesn't exist
            vehicle = instance.assigned_plan.vehicle
            MaintenanceSchedule.create_from_scheduled_maintenance(instance, vehicle)
            
    except Exception as e:
        # Log error but don't break the maintenance app functionality
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error syncing maintenance schedule {instance.id}: {str(e)}")

@receiver(post_delete, sender=ScheduledMaintenance)
def handle_scheduled_maintenance_deletion(sender, instance, **kwargs):
    """
    Handle deletion of scheduled maintenance from maintenance app
    """
    try:
        # Find related insurance schedule and unlink it
        insurance_schedule = MaintenanceSchedule.objects.filter(
            scheduled_maintenance=instance
        ).first()
        
        if insurance_schedule:
            # Don't delete the insurance schedule, just unlink it
            insurance_schedule.scheduled_maintenance = None
            insurance_schedule.save()
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling deletion of maintenance schedule {instance.id}: {str(e)}")

@receiver(post_save, sender=MaintenanceSchedule)
def update_compliance_on_schedule_change(sender, instance, **kwargs):
    """
    Update compliance scores when insurance maintenance schedule changes
    """
    try:
        if hasattr(instance.vehicle, 'compliance'):
            instance.vehicle.compliance.calculate_compliance()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating compliance for vehicle {instance.vehicle.id}: {str(e)}")

# Accident and Vehicle History Synchronization Signals

@receiver(post_save, sender=VehicleHistory)
def sync_vehicle_history_accident(sender, instance, created, **kwargs):
    """
    Automatically create or update insurance accident when vehicle history accident is created/updated
    """
    if instance.event_type == 'ACCIDENT':
        try:
            from .utils import AccidentHistorySyncManager
            
            # Check if insurance accident already exists
            existing_accident = Accident.objects.filter(vehicle_history=instance).first()
            
            if not existing_accident and created:
                # Create new insurance accident from vehicle history
                Accident.create_from_vehicle_history(instance)
            elif existing_accident:
                # Update existing insurance accident
                existing_accident.sync_with_vehicle_history()
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error syncing vehicle history accident {instance.id}: {str(e)}")

@receiver(post_save, sender=Accident)
def sync_accident_with_vehicle_history(sender, instance, created, **kwargs):
    """
    Automatically sync insurance accident with vehicle history
    """
    try:
        from .utils import AccidentHistorySyncManager
        AccidentHistorySyncManager.sync_accident_with_history(instance)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error syncing accident {instance.id} with vehicle history: {str(e)}")

@receiver(post_delete, sender=VehicleHistory)
def handle_vehicle_history_deletion(sender, instance, **kwargs):
    """
    Handle deletion of vehicle history accident record
    """
    if instance.event_type == 'ACCIDENT':
        try:
            # Find related insurance accident and unlink it
            accident = Accident.objects.filter(vehicle_history=instance).first()
            if accident:
                accident.vehicle_history = None
                accident.save()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error handling deletion of vehicle history {instance.id}: {str(e)}")