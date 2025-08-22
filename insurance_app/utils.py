# utils.py
from django.db import transaction
from .models import MaintenanceSchedule
from maintenance.models import ScheduledMaintenance

class AccidentHistorySyncManager:
    """
    Utility class to manage synchronization between insurance accidents and vehicle history
    """
    
    @staticmethod
    def sync_accident_with_history(accident):
        """Sync insurance accident with vehicle history record"""
        if accident.vehicle_history:
            accident.sync_with_vehicle_history()
        else:
            # Create new vehicle history record
            AccidentHistorySyncManager.create_vehicle_history_from_accident(accident)
    
    @staticmethod
    def create_vehicle_history_from_accident(accident):
        """Create vehicle history record from insurance accident"""
        from vehicles.models import VehicleHistory
        
        # Map insurance severity to vehicle history severity
        severity_mapping = {
            'minor': 'MINOR',
            'moderate': 'MAJOR',
            'major': 'MAJOR',
            'total_loss': 'TOTAL_LOSS'
        }
        
        vehicle_history = VehicleHistory.objects.create(
            vehicle=accident.vehicle,
            event_type='ACCIDENT',
            event_date=accident.accident_date.date(),
            description=accident.description,
            accident_severity=severity_mapping.get(accident.severity, 'MAJOR'),
            accident_location=accident.location,
            notes=f"Insurance claim amount: ${accident.claim_amount}. "
                  f"Weather conditions: {accident.weather_conditions}. "
                  f"Fault determination: {accident.fault_determination}."
        )
        
        # Link the records
        accident.vehicle_history = vehicle_history
        accident.save()
        
        return vehicle_history
    
    @staticmethod
    def import_vehicle_history_accidents(vehicle, create_insurance_records=True):
        """Import accident records from vehicle history"""
        from vehicles.models import VehicleHistory
        from .models import Accident
        
        accident_histories = VehicleHistory.objects.filter(
            vehicle=vehicle,
            event_type='ACCIDENT'
        ).exclude(
            insurance_accident__isnull=False  # Exclude already linked records
        )
        
        imported_count = 0
        
        for history in accident_histories:
            if create_insurance_records:
                try:
                    accident = Accident.create_from_vehicle_history(history)
                    imported_count += 1
                except Exception as e:
                    # Log error but continue processing
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error importing accident history {history.id}: {str(e)}")
        
        return imported_count
    
    @staticmethod
    def get_comprehensive_accident_data(vehicle):
        """Get comprehensive accident data combining insurance and history records"""
        from .models import Accident
        from vehicles.models import VehicleHistory
        
        # Get insurance accidents
        insurance_accidents = Accident.objects.filter(vehicle=vehicle).select_related('vehicle_history')
        
        # Get vehicle history accidents not linked to insurance
        unlinked_history = VehicleHistory.objects.filter(
            vehicle=vehicle,
            event_type='ACCIDENT',
            insurance_accident__isnull=True
        )
        
        comprehensive_data = []
        
        # Add insurance accidents with detailed info
        for accident in insurance_accidents:
            data = {
                'type': 'insurance_accident',
                'id': accident.id,
                'date': accident.accident_date,
                'severity': accident.get_severity_display(),
                'claim_amount': accident.claim_amount,
                'description': accident.description,
                'location': accident.location,
                'maintenance_related': accident.maintenance_related,
                'detailed_info': accident.get_detailed_accident_info(),
                'has_vehicle_history': accident.vehicle_history is not None
            }
            comprehensive_data.append(data)
        
        # Add unlinked vehicle history accidents
        for history in unlinked_history:
            data = {
                'type': 'vehicle_history',
                'id': history.id,
                'date': history.event_date,
                'severity': history.get_accident_severity_display() if history.accident_severity else 'Unknown',
                'claim_amount': None,
                'description': history.description,
                'location': history.accident_location,
                'maintenance_related': False,
                'detailed_info': {
                    'police_report_number': history.police_report_number,
                    'insurance_claim_number': history.insurance_claim_number,
                    'reported_by': history.reported_by,
                    'verified': history.verified,
                    'notes': history.notes
                },
                'has_insurance_record': False
            }
            comprehensive_data.append(data)
        
        # Sort by date (most recent first)
        comprehensive_data.sort(key=lambda x: x['date'], reverse=True)
        
        return comprehensive_data


class MaintenanceSyncManager:
    """
    Utility class to manage synchronization between maintenance app and insurance app
    """
    
    @staticmethod
    def get_maintenance_type_mapping():
        """Map maintenance task names to insurance maintenance types"""
        return {
            'Oil Change': 'oil_change',
            'Brake Service': 'brake_service',
            'Brake Inspection': 'brake_service',
            'Tire Rotation': 'tire_rotation',
            'Tire Replacement': 'tire_rotation',
            'Transmission Service': 'transmission',
            'Transmission Fluid Change': 'transmission',
            'Engine Tune-up': 'engine_tune',
            'Engine Service': 'engine_tune',
            'Safety Inspection': 'inspection',
            'Annual Inspection': 'inspection',
            'Emissions Test': 'inspection',
        }
    
    @staticmethod
    def get_priority_mapping():
        """Map maintenance task priorities to insurance priorities"""
        return {
            'LOW': 'low',
            'MEDIUM': 'medium',
            'HIGH': 'high'
        }
    
    @staticmethod
    def determine_insurance_priority(scheduled_maintenance):
        """
        Determine insurance priority based on maintenance task and conditions
        """
        task_priority = scheduled_maintenance.task.priority
        base_priority = MaintenanceSyncManager.get_priority_mapping().get(task_priority, 'medium')
        
        # Upgrade priority if overdue
        if scheduled_maintenance.status == 'OVERDUE':
            if base_priority == 'low':
                return 'medium'
            elif base_priority == 'medium':
                return 'high'
            elif base_priority == 'high':
                return 'critical'
        
        # Upgrade priority for safety-critical tasks
        safety_critical_tasks = ['Brake Service', 'Brake Inspection', 'Safety Inspection']
        if scheduled_maintenance.task.name in safety_critical_tasks:
            if base_priority in ['low', 'medium']:
                return 'high'
        
        return base_priority
    
    @staticmethod
    @transaction.atomic
    def sync_vehicle_schedules(vehicle):
        """
        Sync all maintenance schedules for a specific vehicle
        """
        # Get all scheduled maintenance for this vehicle
        scheduled_maintenances = ScheduledMaintenance.objects.filter(
            assigned_plan__vehicle=vehicle
        ).select_related('task', 'assigned_plan')
        
        synced_count = 0
        created_count = 0
        
        for scheduled_maintenance in scheduled_maintenances:
            insurance_schedule = MaintenanceSchedule.objects.filter(
                scheduled_maintenance=scheduled_maintenance
            ).first()
            
            if insurance_schedule:
                insurance_schedule.sync_with_maintenance_app()
                synced_count += 1
            else:
                MaintenanceSchedule.create_from_scheduled_maintenance(
                    scheduled_maintenance, vehicle
                )
                created_count += 1
        
        return synced_count, created_count
    
    @staticmethod
    def get_sync_status(vehicle):
        """
        Get synchronization status for a vehicle
        """
        maintenance_schedules_count = ScheduledMaintenance.objects.filter(
            assigned_plan__vehicle=vehicle
        ).count()
        
        insurance_schedules_count = MaintenanceSchedule.objects.filter(
            vehicle=vehicle,
            scheduled_maintenance__isnull=False
        ).count()
        
        unlinked_insurance_schedules = MaintenanceSchedule.objects.filter(
            vehicle=vehicle,
            scheduled_maintenance__isnull=True
        ).count()
        
        return {
            'maintenance_schedules': maintenance_schedules_count,
            'linked_insurance_schedules': insurance_schedules_count,
            'unlinked_insurance_schedules': unlinked_insurance_schedules,
            'sync_percentage': (insurance_schedules_count / maintenance_schedules_count * 100) 
                             if maintenance_schedules_count > 0 else 100
        }
    
    @staticmethod
    def create_insurance_schedule_from_maintenance(scheduled_maintenance, vehicle=None):
        """
        Enhanced method to create insurance schedule with better mapping
        """
        if not vehicle:
            vehicle = scheduled_maintenance.assigned_plan.vehicle
        
        maintenance_type_mapping = MaintenanceSyncManager.get_maintenance_type_mapping()
        
        # Try exact match first, then partial match
        task_name = scheduled_maintenance.task.name
        maintenance_type = maintenance_type_mapping.get(task_name)
        
        if not maintenance_type:
            # Try partial matching
            for key, value in maintenance_type_mapping.items():
                if key.lower() in task_name.lower() or task_name.lower() in key.lower():
                    maintenance_type = value
                    break
            else:
                maintenance_type = 'other'
        
        # Determine priority
        priority = MaintenanceSyncManager.determine_insurance_priority(scheduled_maintenance)
        
        # Handle due_mileage - provide default if None or missing
        due_mileage = scheduled_maintenance.due_mileage
        if due_mileage is None:
            # Use current vehicle mileage + task interval as fallback
            current_mileage = getattr(scheduled_maintenance.assigned_plan, 'current_mileage', 0)
            task_interval = getattr(scheduled_maintenance.task, 'interval_miles', 5000)
            due_mileage = current_mileage + task_interval
        
        # Create insurance schedule
        insurance_schedule = MaintenanceSchedule.objects.create(
            vehicle=vehicle,
            maintenance_type=maintenance_type,
            priority_level=priority,
            scheduled_date=scheduled_maintenance.due_date,
            due_mileage=due_mileage,
            description=scheduled_maintenance.task.description or task_name,
            is_completed=(scheduled_maintenance.status == 'COMPLETED'),
            completed_date=scheduled_maintenance.completed_date,
            scheduled_maintenance=scheduled_maintenance
        )
        
        return insurance_schedule