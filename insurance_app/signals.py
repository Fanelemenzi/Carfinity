# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from maintenance.models import ScheduledMaintenance
from vehicles.models import VehicleHistory
from .models import MaintenanceSchedule, Accident

# Removed automatic sync signals - now using manual selection

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