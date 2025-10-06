from django.db.models import Q, Prefetch, Sum, Avg, Count
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from vehicles.models import Vehicle
from maintenance.models import ScheduledMaintenance
from maintenance_history.models import MaintenanceRecord, Inspection
from insurance_app.models import InsurancePolicy
from .models import VehicleAlert, VehicleCostAnalytics
# from .cache_utils import CacheManager  # Temporarily disabled
from .exceptions import (
    VehicleNotFoundError, VehicleAccessDeniedError, DataRetrievalError,
    ExternalServiceError, ErrorHandler
)
from .logging_config import DashboardLogger, log_performance
import logging

logger = logging.getLogger(__name__)
dashboard_logger = DashboardLogger('services')


class DashboardService:
    """
    Service class for handling dashboard-related business logic
    """
    
    @log_performance('get_complete_dashboard_data')
    def get_complete_dashboard_data(self, vehicle_id, user):
        """
        Get all dashboard data in a single optimized query to minimize database hits
        Uses Redis caching for expensive operations like valuation and health scores
        """
        try:
            # Validate vehicle access first
            vehicle = ErrorHandler.validate_vehicle_access(user, vehicle_id)
            
            # Check cache first for complete dashboard data
            # cached_data = ErrorHandler.handle_cache_operation(
            #     'get', f'dashboard_data_{vehicle_id}_{user.id}',
            #     lambda: CacheManager.get_dashboard_data(vehicle_id, user.id)
            # )
            cached_data = None  # Caching temporarily disabled
            
            if cached_data:
                logger.info(f"Retrieved dashboard data from cache for vehicle {vehicle_id}, user {user.id}")
                return cached_data
            
            # Single comprehensive query with all necessary data
            def fetch_vehicle_data():
                return Vehicle.objects.select_related(
                    'valuation'
                ).prefetch_related(
                    # Latest maintenance records for service history and mileage
                    Prefetch(
                        'maintenance_history',
                        queryset=MaintenanceRecord.objects.select_related('vehicle')
                            .order_by('-date_performed')[:10],
                        to_attr='recent_maintenance'
                    ),
                    # Latest inspections for health data
                    Prefetch(
                        'inspections',
                        queryset=Inspection.objects.select_related('vehicle')
                            .order_by('-inspection_date')[:5],
                        to_attr='recent_inspections'
                    ),
                    # Upcoming scheduled maintenance
                    Prefetch(
                        'assigned_plans__schedules',
                        queryset=ScheduledMaintenance.objects.select_related('task', 'assigned_plan')
                            .filter(status__in=['PENDING', 'OVERDUE'])
                            .order_by('due_date'),
                        to_attr='all_upcoming_schedules'
                    ),
                    # Active alerts
                    Prefetch(
                        'alerts',
                        queryset=VehicleAlert.objects.filter(is_active=True)
                            .order_by(
                                models.Case(
                                    models.When(priority='HIGH', then=models.Value(1)),
                                    models.When(priority='MEDIUM', then=models.Value(2)),
                                    models.When(priority='LOW', then=models.Value(3)),
                                    default=models.Value(4),
                                    output_field=models.IntegerField()
                                ),
                                '-created_at'
                            ),
                        to_attr='all_active_alerts'
                    ),
                    # Recent cost analytics
                    Prefetch(
                        'cost_analytics',
                        queryset=VehicleCostAnalytics.objects.order_by('-month')[:12],
                        to_attr='recent_cost_analytics'
                    )
                ).get(
                    id=vehicle_id,
                    ownerships__user=user,
                    ownerships__is_current_owner=True
                )
            
            vehicle_data = ErrorHandler.handle_data_retrieval(
                fetch_vehicle_data,
                fallback_value=None,
                error_message=f"Failed to fetch complete vehicle data for vehicle {vehicle_id}"
            )
            
            if not vehicle_data:
                raise DataRetrievalError("complete dashboard data")
            
            # Build complete dashboard data from prefetched relationships with error handling
            dashboard_data = {
                'vehicle_overview': ErrorHandler.handle_data_retrieval(
                    lambda: self._build_overview_from_vehicle(vehicle_data),
                    fallback_value={},
                    error_message="Failed to build vehicle overview"
                ),
                'upcoming_maintenance': ErrorHandler.handle_data_retrieval(
                    lambda: self._build_maintenance_from_vehicle(vehicle_data),
                    fallback_value=[],
                    error_message="Failed to build maintenance data"
                ),
                'alerts': ErrorHandler.handle_data_retrieval(
                    lambda: self._build_alerts_from_vehicle(vehicle_data),
                    fallback_value=[],
                    error_message="Failed to build alerts data"
                ),
                'service_history': ErrorHandler.handle_data_retrieval(
                    lambda: self._build_history_from_vehicle(vehicle_data, limit=5),
                    fallback_value=[],
                    error_message="Failed to build service history"
                ),
                'cost_analytics': ErrorHandler.handle_data_retrieval(
                    lambda: self._build_analytics_from_vehicle(vehicle_data),
                    fallback_value={},
                    error_message="Failed to build cost analytics"
                ),
                'valuation': ErrorHandler.handle_data_retrieval(
                    lambda: self._build_valuation_from_vehicle(vehicle_data),
                    fallback_value={},
                    error_message="Failed to build valuation data"
                )
            }
            
            # Cache the complete dashboard data with error handling
            # ErrorHandler.handle_cache_operation(
            #     'set', f'dashboard_data_{vehicle_id}_{user.id}',
            #     lambda: CacheManager.set_dashboard_data(vehicle_id, user.id, dashboard_data)
            # )
            # Caching temporarily disabled
            
            # Log successful data retrieval with performance metrics
            dashboard_logger.log_data_retrieval(
                'complete_dashboard_data',
                user.id,
                vehicle_id,
                success=True,
                cache_hit=cached_data is not None
            )
            
            logger.info(f"Successfully retrieved and cached dashboard data for vehicle {vehicle_id}, user {user.id}")
            return dashboard_data
            
        except (VehicleNotFoundError, VehicleAccessDeniedError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving dashboard data for vehicle {vehicle_id}, user {user.id}: {str(e)}", exc_info=True)
            raise DataRetrievalError("complete dashboard data", e)
    
    def _build_overview_from_vehicle(self, vehicle):
        """Build overview data from prefetched vehicle data"""
        next_maintenance = None
        if hasattr(vehicle, 'all_upcoming_schedules') and vehicle.all_upcoming_schedules:
            next_schedule = vehicle.all_upcoming_schedules[0]
            next_maintenance = {
                'date': next_schedule.due_date,
                'mileage': next_schedule.due_mileage,
                'service_type': next_schedule.task.name
            }
        
        overview = {
            'id': vehicle.id,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.manufacture_year,
            'vin': vehicle.vin,
            'mileage': vehicle.current_mileage,
            'mileage_last_updated': vehicle.mileage_last_updated,
            'health_status': vehicle.health_status,
            'health_score': vehicle.health_score,
            'last_inspection_date': vehicle.last_inspection_date,
            'next_service_date': next_maintenance.get('date') if next_maintenance else None,
            'next_service_mileage': next_maintenance.get('mileage') if next_maintenance else None,
            'next_service_type': next_maintenance.get('service_type') if next_maintenance else None,
            'estimated_value': None,
            'active_alerts_count': len(vehicle.all_active_alerts) if hasattr(vehicle, 'all_active_alerts') else 0
        }
        
        if hasattr(vehicle, 'vehiclevaluation') and vehicle.vehiclevaluation:
            overview['estimated_value'] = float(vehicle.vehiclevaluation.estimated_value)
            overview['condition_rating'] = vehicle.vehiclevaluation.condition_rating
            overview['valuation_last_updated'] = vehicle.vehiclevaluation.last_updated
        
        return overview
    
    def _build_maintenance_from_vehicle(self, vehicle):
        """Build maintenance data from prefetched vehicle data"""
        if not hasattr(vehicle, 'all_upcoming_schedules'):
            return []
        
        upcoming_maintenance = []
        current_date = timezone.now().date()
        
        for item in vehicle.all_upcoming_schedules:
            days_until = (item.due_date - current_date).days if item.due_date else None
            is_overdue = days_until is not None and days_until < 0
            
            maintenance_item = {
                'id': item.id,
                'service_type': item.task.name,
                'scheduled_date': item.due_date,
                'scheduled_mileage': item.due_mileage,
                'days_until': abs(days_until) if days_until is not None else None,
                'is_overdue': is_overdue,
                'estimated_cost': None,
                'service_provider': None,
                'description': item.task.description,
                'priority': item.task.priority,
                'status': item.status
            }
            upcoming_maintenance.append(maintenance_item)
        
        return upcoming_maintenance
    
    def _build_alerts_from_vehicle(self, vehicle):
        """Build alerts data from prefetched vehicle data"""
        if not hasattr(vehicle, 'all_active_alerts'):
            return []
        
        alert_list = []
        for alert in vehicle.all_active_alerts:
            alert_data = {
                'id': alert.id,
                'alert_type': alert.alert_type,
                'priority': alert.priority,
                'title': alert.title,
                'description': alert.description,
                'created_at': alert.created_at,
                'priority_display': alert.get_priority_display(),
                'alert_type_display': alert.get_alert_type_display()
            }
            alert_list.append(alert_data)
        
        return alert_list
    
    def _build_history_from_vehicle(self, vehicle, limit=None):
        """Build service history from prefetched vehicle data"""
        if not hasattr(vehicle, 'recent_maintenance'):
            return []
        
        service_history = []
        maintenance_records = vehicle.recent_maintenance[:limit] if limit else vehicle.recent_maintenance
        
        for record in maintenance_records:
            history_item = {
                'id': record.id,
                'date_performed': record.date_performed,
                'work_done': record.work_done,
                'mileage': record.mileage,
                'cost': float(record.cost) if record.cost else None,
                'service_provider': record.service_provider,
                'notes': record.notes,
                'parts_replaced': record.parts_replaced
            }
            service_history.append(history_item)
        
        return service_history
    
    def _build_analytics_from_vehicle(self, vehicle):
        """Build cost analytics from prefetched vehicle data"""
        if not hasattr(vehicle, 'recent_cost_analytics'):
            return {}
        
        monthly_data = []
        total_monthly_cost = 0
        analytics_count = 0
        
        for analytics in vehicle.recent_cost_analytics:
            monthly_item = {
                'month': analytics.month,
                'total_cost': float(analytics.total_cost),
                'maintenance_cost': float(analytics.maintenance_cost),
                'parts_cost': float(analytics.parts_cost),
                'labor_cost': float(analytics.labor_cost)
            }
            monthly_data.append(monthly_item)
            total_monthly_cost += float(analytics.total_cost)
            analytics_count += 1
        
        # Calculate lifetime costs from maintenance records
        lifetime_total = 0
        lifetime_count = 0
        if hasattr(vehicle, 'recent_maintenance'):
            for record in vehicle.recent_maintenance:
                if record.cost:
                    lifetime_total += float(record.cost)
                    lifetime_count += 1
        
        avg_monthly_cost = total_monthly_cost / analytics_count if analytics_count > 0 else 0
        avg_lifetime_cost = lifetime_total / lifetime_count if lifetime_count > 0 else 0
        
        return {
            'monthly_data': monthly_data,
            'lifetime_total': lifetime_total,
            'lifetime_average': avg_lifetime_cost,
            'monthly_average': avg_monthly_cost,
            'total_records': lifetime_count,
            'health_score': vehicle.health_score,
            'last_service_date': self._get_last_service_date_from_records(vehicle.recent_maintenance) if hasattr(vehicle, 'recent_maintenance') else None,
            'next_service_days': self._get_days_until_next_service_from_schedules(vehicle.all_upcoming_schedules) if hasattr(vehicle, 'all_upcoming_schedules') else None
        }
    
    def _build_valuation_from_vehicle(self, vehicle):
        """Build valuation data from prefetched vehicle data with caching"""
        # Check cache first for valuation data
        # cached_valuation = CacheManager.get_vehicle_valuation(vehicle.id)
        # if cached_valuation:
        #     return cached_valuation
        # Caching temporarily disabled
        
        valuation_data = {}
        if hasattr(vehicle, 'vehiclevaluation') and vehicle.vehiclevaluation:
            valuation = vehicle.vehiclevaluation
            valuation_data = {
                'estimated_value': float(valuation.estimated_value),
                'condition_rating': valuation.condition_rating,
                'last_updated': valuation.last_updated,
                'valuation_source': valuation.valuation_source,
                'vehicle_age_years': timezone.now().year - vehicle.manufacture_year,
                'current_mileage': vehicle.current_mileage
            }
        else:
            valuation_data = {
                'estimated_value': None,
                'condition_rating': None,
                'last_updated': None,
                'valuation_source': None,
                'vehicle_age_years': timezone.now().year - vehicle.manufacture_year,
                'current_mileage': vehicle.current_mileage
            }
        
        # Cache the valuation data
        # CacheManager.set_vehicle_valuation(vehicle.id, valuation_data)
        # Caching temporarily disabled
        return valuation_data
    
    def _get_last_service_date_from_records(self, maintenance_records):
        """Helper to get last service date from prefetched records"""
        if maintenance_records:
            return maintenance_records[0].date_performed
        return None
    
    def _get_days_until_next_service_from_schedules(self, schedules):
        """Helper to get days until next service from prefetched schedules"""
        if schedules:
            next_schedule = schedules[0]
            if next_schedule.due_date:
                days_until = (next_schedule.due_date - timezone.now().date()).days
                return days_until if days_until > 0 else 0
        return None
    
    @log_performance('get_vehicle_overview')
    def get_vehicle_overview(self, vehicle_id, user):
        """
        Get comprehensive vehicle overview data including basic info,
        current status, and key metrics - optimized single query approach
        """
        try:
            # Validate vehicle access first
            ErrorHandler.validate_vehicle_access(user, vehicle_id)
            
            # Single optimized query with all necessary joins and prefetches
            def fetch_vehicle_overview():
                return Vehicle.objects.select_related(
                    'vehiclevaluation'  # Use correct related name for valuation
                ).prefetch_related(
                    # Optimize maintenance history queries - limit to latest 5 records
                    Prefetch(
                        'maintenance_history',
                        queryset=MaintenanceRecord.objects.select_related('vehicle')
                            .order_by('-date_performed')[:5],
                        to_attr='latest_maintenance_records'
                    ),
                    # Optimize inspection queries - limit to latest 3 inspections
                    Prefetch(
                        'inspections',
                        queryset=Inspection.objects.select_related('vehicle')
                            .order_by('-inspection_date')[:3],
                        to_attr='latest_inspections'
                    ),
                    # Optimize scheduled maintenance queries - only pending/overdue
                    Prefetch(
                        'assigned_plans__schedules',
                        queryset=ScheduledMaintenance.objects.select_related('task', 'assigned_plan')
                            .filter(status__in=['PENDING', 'OVERDUE'])
                            .order_by('due_date')[:5],
                        to_attr='upcoming_schedules'
                    ),
                    # Prefetch active alerts to avoid additional queries
                    Prefetch(
                        'alerts',
                        queryset=VehicleAlert.objects.filter(is_active=True)
                            .order_by('-priority', '-created_at')[:10],
                        to_attr='active_alerts'
                    )
                ).get(
                    id=vehicle_id,
                    ownerships__user=user,
                    ownerships__is_current_owner=True
                )
            
            vehicle = ErrorHandler.handle_data_retrieval(
                fetch_vehicle_overview,
                fallback_value=None,
                error_message=f"Failed to fetch vehicle overview for vehicle {vehicle_id}"
            )
            
            if not vehicle:
                raise DataRetrievalError("vehicle overview")
            
            # Get next scheduled maintenance from prefetched data with error handling
            next_maintenance = ErrorHandler.handle_data_retrieval(
                lambda: self._get_next_maintenance_from_vehicle(vehicle),
                fallback_value=None,
                error_message="Failed to get next maintenance"
            )
            
            # Build overview data using prefetched relationships with safe conversions
            overview = {
                'id': vehicle.id,
                'make': vehicle.make or 'Unknown',
                'model': vehicle.model or 'Unknown',
                'year': vehicle.manufacture_year,
                'vin': vehicle.vin or 'Unknown',
                'mileage': ErrorHandler.safe_int_conversion(vehicle.current_mileage),
                'mileage_last_updated': vehicle.mileage_last_updated,
                'health_status': vehicle.health_status or 'Unknown',
                'health_score': ErrorHandler.safe_int_conversion(vehicle.health_score),
                'last_inspection_date': vehicle.last_inspection_date,
                'next_service_date': next_maintenance.get('date') if next_maintenance else None,
                'next_service_mileage': next_maintenance.get('mileage') if next_maintenance else None,
                'next_service_type': next_maintenance.get('service_type') if next_maintenance else None,
                'estimated_value': None,
                'active_alerts_count': len(vehicle.active_alerts) if hasattr(vehicle, 'active_alerts') else 0
            }
            
            # Add valuation if available with error handling
            if hasattr(vehicle, 'vehiclevaluation') and vehicle.vehiclevaluation:
                try:
                    overview['estimated_value'] = ErrorHandler.safe_float_conversion(vehicle.vehiclevaluation.estimated_value)
                    overview['condition_rating'] = vehicle.vehiclevaluation.condition_rating
                    overview['valuation_last_updated'] = vehicle.vehiclevaluation.last_updated
                except Exception as e:
                    logger.warning(f"Failed to process valuation data for vehicle {vehicle_id}: {str(e)}")
            
            # Log successful data retrieval
            dashboard_logger.log_data_retrieval(
                'vehicle_overview',
                user.id,
                vehicle_id,
                success=True
            )
            
            logger.info(f"Successfully retrieved vehicle overview for vehicle {vehicle_id}, user {user.id}")
            return overview
            
        except (VehicleNotFoundError, VehicleAccessDeniedError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving vehicle overview for vehicle {vehicle_id}, user {user.id}: {str(e)}", exc_info=True)
            raise DataRetrievalError("vehicle overview", e)
    
    def _get_next_maintenance_from_vehicle(self, vehicle):
        """Helper method to get next maintenance from prefetched data"""
        if hasattr(vehicle, 'upcoming_schedules') and vehicle.upcoming_schedules:
            next_schedule = vehicle.upcoming_schedules[0]  # First item is earliest due date
            return {
                'date': next_schedule.due_date,
                'mileage': next_schedule.due_mileage,
                'service_type': next_schedule.task.name if next_schedule.task else 'Unknown'
            }
        return None
    
    def get_upcoming_maintenance(self, vehicle_id, user):
        """
        Get scheduled maintenance items for the vehicle
        """
        try:
            # Optimized single query approach
            scheduled_items = ScheduledMaintenance.objects.filter(
                assigned_plan__vehicle_id=vehicle_id,
                assigned_plan__vehicle__ownerships__user=user,
                assigned_plan__vehicle__ownerships__is_current_owner=True,
                status__in=['PENDING', 'OVERDUE']
            ).select_related(
                'assigned_plan__vehicle', 'task'
            ).order_by('due_date')
            
            upcoming_maintenance = []
            current_date = timezone.now().date()
            
            for item in scheduled_items:
                # Calculate days until service
                days_until = (item.due_date - current_date).days if item.due_date else None
                
                # Determine if overdue
                is_overdue = days_until is not None and days_until < 0
                
                maintenance_item = {
                    'id': item.id,
                    'service_type': item.task.name,
                    'scheduled_date': item.due_date,
                    'scheduled_mileage': item.due_mileage,
                    'days_until': abs(days_until) if days_until is not None else None,
                    'is_overdue': is_overdue,
                    'estimated_cost': None,  # Not available in current model
                    'service_provider': None,  # Not available in current model
                    'description': item.task.description,
                    'priority': item.task.priority,
                    'status': item.status
                }
                
                upcoming_maintenance.append(maintenance_item)
            
            return upcoming_maintenance
            
        except (Vehicle.DoesNotExist, ScheduledMaintenance.DoesNotExist):
            return []
    
    def get_vehicle_alerts(self, vehicle_id, user):
        """
        Get active alerts for the vehicle
        """
        try:
            # Optimized single query approach
            alerts = VehicleAlert.objects.filter(
                vehicle_id=vehicle_id,
                vehicle__ownerships__user=user,
                vehicle__ownerships__is_current_owner=True,
                is_active=True
            ).select_related('vehicle').order_by(
                # Custom ordering for priority (HIGH, MEDIUM, LOW)
                models.Case(
                    models.When(priority='HIGH', then=models.Value(1)),
                    models.When(priority='MEDIUM', then=models.Value(2)),
                    models.When(priority='LOW', then=models.Value(3)),
                    default=models.Value(4),
                    output_field=models.IntegerField()
                ),
                '-created_at'
            )
            
            alert_list = []
            for alert in alerts:
                alert_data = {
                    'id': alert.id,
                    'alert_type': alert.alert_type,
                    'priority': alert.priority,
                    'title': alert.title,
                    'description': alert.description,
                    'created_at': alert.created_at,
                    'priority_display': alert.get_priority_display(),
                    'alert_type_display': alert.get_alert_type_display()
                }
                alert_list.append(alert_data)
            
            return alert_list
            
        except Vehicle.DoesNotExist:
            return []
    

    
    def get_service_history(self, vehicle_id, user, limit=None, offset=None):
        """
        Get paginated service history for the vehicle
        """
        try:
            # Optimized single query with proper slicing
            history_query = MaintenanceRecord.objects.filter(
                vehicle_id=vehicle_id,
                vehicle__ownerships__user=user,
                vehicle__ownerships__is_current_owner=True
            ).select_related('vehicle').order_by('-date_performed')
            
            # Apply pagination using database-level slicing
            start = offset or 0
            end = start + limit if limit else None
            history_query = history_query[start:end]
            
            service_history = []
            for record in history_query:
                history_item = {
                    'id': record.id,
                    'date_performed': record.date_performed,
                    'work_done': record.work_done,
                    'mileage': record.mileage,
                    'cost': float(record.cost) if record.cost else None,
                    'service_provider': record.service_provider,
                    'notes': record.notes,
                    'parts_replaced': record.parts_replaced
                }
                service_history.append(history_item)
            
            return service_history
            
        except Vehicle.DoesNotExist:
            return []
    
    def get_service_history_count(self, vehicle_id, user):
        """
        Get total count of service history records for pagination
        """
        try:
            # Optimized count query without fetching the vehicle object
            return MaintenanceRecord.objects.filter(
                vehicle_id=vehicle_id,
                vehicle__ownerships__user=user,
                vehicle__ownerships__is_current_owner=True
            ).count()
            
        except Exception:
            return 0
    
    def get_cost_analytics(self, vehicle_id, user):
        """
        Get cost analytics and spending insights for the vehicle - optimized with aggregation
        """
        try:
            # Single query to verify vehicle ownership and get basic info
            vehicle = Vehicle.objects.only('id', 'manufacture_year').get(
                id=vehicle_id,
                ownerships__user=user,
                ownerships__is_current_owner=True
            )
            
            # Optimized query for recent cost analytics (last 12 months)
            twelve_months_ago = timezone.now().date().replace(day=1) - timedelta(days=365)
            cost_analytics = VehicleCostAnalytics.objects.filter(
                vehicle_id=vehicle_id,  # Use vehicle_id directly to avoid join
                month__gte=twelve_months_ago
            ).order_by('-month')
            
            # Single aggregation query for lifetime costs
            lifetime_maintenance = MaintenanceRecord.objects.filter(
                vehicle_id=vehicle_id,  # Use vehicle_id directly
                cost__isnull=False
            ).aggregate(
                total_cost=models.Sum('cost'),
                avg_cost=models.Avg('cost'),
                record_count=models.Count('id'),
                latest_service_date=models.Max('date_performed')
            )
            
            # Calculate monthly averages from analytics
            monthly_data = []
            total_monthly_cost = 0
            analytics_count = 0
            
            for analytics in cost_analytics:
                monthly_item = {
                    'month': analytics.month,
                    'total_cost': float(analytics.total_cost),
                    'maintenance_cost': float(analytics.maintenance_cost),
                    'parts_cost': float(analytics.parts_cost),
                    'labor_cost': float(analytics.labor_cost)
                }
                monthly_data.append(monthly_item)
                total_monthly_cost += float(analytics.total_cost)
                analytics_count += 1
            
            # Calculate averages
            avg_monthly_cost = total_monthly_cost / analytics_count if analytics_count > 0 else 0
            
            analytics_summary = {
                'monthly_data': monthly_data,
                'lifetime_total': float(lifetime_maintenance['total_cost']) if lifetime_maintenance['total_cost'] else 0,
                'lifetime_average': float(lifetime_maintenance['avg_cost']) if lifetime_maintenance['avg_cost'] else 0,
                'monthly_average': avg_monthly_cost,
                'total_records': lifetime_maintenance['record_count'] or 0,
                'health_score': vehicle.health_score,
                'last_service_date': lifetime_maintenance['latest_service_date'],
                'next_service_days': self._get_days_until_next_service_optimized(vehicle_id)
            }
            
            return analytics_summary
            
        except Vehicle.DoesNotExist:
            return {}
    
    def get_vehicle_valuation(self, vehicle_id, user):
        """
        Get current vehicle valuation and market value data
        Uses Redis caching for expensive valuation operations
        """
        try:
            # Check cache first for valuation data
            # cached_valuation = CacheManager.get_vehicle_valuation(vehicle_id)
            # if cached_valuation:
            #     logger.info(f"Retrieved valuation data from cache for vehicle {vehicle_id}")
            #     return cached_valuation
            # Caching temporarily disabled
            
            vehicle = Vehicle.objects.select_related('vehiclevaluation').get(
                id=vehicle_id,
                ownerships__user=user,
                ownerships__is_current_owner=True
            )
            
            valuation_data = {}
            if hasattr(vehicle, 'vehiclevaluation') and vehicle.vehiclevaluation:
                valuation = vehicle.vehiclevaluation
                valuation_data = {
                    'estimated_value': float(valuation.estimated_value),
                    'condition_rating': valuation.condition_rating,
                    'last_updated': valuation.last_updated,
                    'valuation_source': valuation.valuation_source,
                    'vehicle_age_years': timezone.now().year - vehicle.manufacture_year,
                    'current_mileage': vehicle.current_mileage
                }
            else:
                valuation_data = {
                    'estimated_value': None,
                    'condition_rating': None,
                    'last_updated': None,
                    'valuation_source': None,
                    'vehicle_age_years': timezone.now().year - vehicle.manufacture_year,
                    'current_mileage': vehicle.current_mileage
                }
            
            # Cache the valuation data
            # CacheManager.set_vehicle_valuation(vehicle_id, valuation_data)
            # logger.info(f"Cached valuation data for vehicle {vehicle_id}")
            # Caching temporarily disabled
            
            return valuation_data
                
        except Vehicle.DoesNotExist:
            return {}
    
    def _get_next_scheduled_maintenance(self, vehicle):
        """
        Helper method to get the next scheduled maintenance item
        """
        next_maintenance = ScheduledMaintenance.objects.filter(
            assigned_plan__vehicle=vehicle,
            status__in=['PENDING', 'OVERDUE'],
            due_date__gte=timezone.now().date()
        ).order_by('due_date').first()
        
        if next_maintenance:
            return {
                'date': next_maintenance.due_date,
                'mileage': next_maintenance.due_mileage,
                'service_type': next_maintenance.task.name
            }
        
        return None
    
    def _get_last_service_date(self, vehicle):
        """
        Helper method to get the date of the last service
        """
        last_service = MaintenanceRecord.objects.filter(
            vehicle=vehicle
        ).order_by('-date_performed').first()
        
        return last_service.date_performed if last_service else None
    
    def _get_days_until_next_service(self, vehicle):
        """
        Helper method to calculate days until next scheduled service
        """
        next_maintenance = self._get_next_scheduled_maintenance(vehicle)
        if next_maintenance and next_maintenance['date']:
            days_until = (next_maintenance['date'] - timezone.now().date()).days
            return days_until if days_until > 0 else 0
        return None
    
    def _get_days_until_next_service_optimized(self, vehicle_id):
        """
        Optimized helper method to calculate days until next scheduled service
        """
        next_schedule = ScheduledMaintenance.objects.filter(
            assigned_plan__vehicle_id=vehicle_id,
            status__in=['PENDING', 'OVERDUE'],
            due_date__gte=timezone.now().date()
        ).order_by('due_date').values('due_date').first()
        
        if next_schedule and next_schedule['due_date']:
            days_until = (next_schedule['due_date'] - timezone.now().date()).days
            return days_until if days_until > 0 else 0
        return None
    
    def invalidate_vehicle_cache(self, vehicle_id, user_id=None):
        """
        Invalidate cached data for a vehicle when data is updated
        """
        try:
            # Invalidate general vehicle cache
            # CacheManager.invalidate_vehicle_cache(vehicle_id)
            
            # If user_id is provided, invalidate user-specific dashboard cache
            # if user_id:
            #     CacheManager.invalidate_user_dashboard_cache(vehicle_id, user_id)
            
            # logger.info(f"Invalidated cache for vehicle {vehicle_id}, user {user_id}")
            # Caching temporarily disabled
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache for vehicle {vehicle_id}: {e}")
            return False
    
    def warm_vehicle_cache(self, vehicle_id, user):
        """
        Pre-load cache with commonly accessed data for better performance
        """
        try:
            # Pre-load valuation data
            self.get_vehicle_valuation(vehicle_id, user)
            
            # Pre-load complete dashboard data
            self.get_complete_dashboard_data(vehicle_id, user)
            
            logger.info(f"Warmed cache for vehicle {vehicle_id}, user {user.id}")
            return True
        except Exception as e:
            logger.error(f"Error warming cache for vehicle {vehicle_id}: {e}")
            return False


class AlertService:
    """
    Service class for generating and managing vehicle alerts
    """
    
    def generate_maintenance_alerts(self, vehicle):
        """
        Generate alerts for overdue maintenance items
        """
        alerts_created = []
        current_date = timezone.now().date()
        
        # Get overdue scheduled maintenance from the maintenance app
        overdue_maintenance = ScheduledMaintenance.objects.filter(
            assigned_plan__vehicle=vehicle,
            status__in=['PENDING', 'OVERDUE'],
            due_date__lt=current_date
        ).select_related('assigned_plan', 'task')
        
        for maintenance_item in overdue_maintenance:
            days_overdue = (current_date - maintenance_item.due_date).days
            
            # Update status to OVERDUE if it's still PENDING
            if maintenance_item.status == 'PENDING':
                maintenance_item.status = 'OVERDUE'
                maintenance_item.save(update_fields=['status'])
            
            # Check if alert already exists for this maintenance item
            existing_alert = VehicleAlert.objects.filter(
                vehicle=vehicle,
                alert_type='MAINTENANCE_OVERDUE',
                title__icontains=maintenance_item.task.name,
                is_active=True
            ).first()
            
            if not existing_alert:
                # Determine priority based on maintenance type and how overdue it is
                service_type = maintenance_item.task.name.lower()
                
                # High priority for critical maintenance items
                if ('oil' in service_type and 'change' in service_type) or days_overdue > 30:
                    priority = 'HIGH'
                elif days_overdue > 14 or maintenance_item.task.priority == 'HIGH':
                    priority = 'MEDIUM'  
                else:
                    priority = 'LOW'
                
                # Create more specific alert titles and descriptions
                if 'oil' in service_type and 'change' in service_type:
                    title = f"Overdue Oil Change"
                    description = (f"Your oil change was due on "
                                 f"{maintenance_item.due_date.strftime('%B %d, %Y')} "
                                 f"and is now {days_overdue} days overdue. "
                                 f"Continuing to drive without an oil change can cause "
                                 f"serious engine damage. Please schedule this service immediately.")
                else:
                    title = f"Overdue: {maintenance_item.task.name}"
                    description = (f"Your {maintenance_item.task.name} was scheduled for "
                                 f"{maintenance_item.due_date.strftime('%B %d, %Y')} "
                                 f"and is now {days_overdue} days overdue. "
                                 f"Please schedule this service as soon as possible.")
                
                alert = VehicleAlert.objects.create(
                    vehicle=vehicle,
                    alert_type='MAINTENANCE_OVERDUE',
                    priority=priority,
                    title=title,
                    description=description
                )
                alerts_created.append(alert)
        
        return alerts_created
    
    def generate_part_replacement_alerts(self, vehicle):
        """
        Generate alerts for parts needing replacement based on maintenance history
        """
        alerts_created = []
        current_date = timezone.now().date()
        
        # Get all maintenance records to analyze part replacement patterns
        all_maintenance = MaintenanceRecord.objects.filter(
            vehicle=vehicle
        ).order_by('-date_performed')
        
        # Common parts that need regular replacement and their typical intervals (in days)
        part_intervals = {
            'oil filter': 90,      # Every 3 months
            'air filter': 365,     # Every 12 months  
            'brake pads': 730,     # Every 2 years
            'brake fluid': 730,    # Every 2 years
            'transmission fluid': 1095,  # Every 3 years
            'coolant': 730,        # Every 2 years
            'spark plugs': 1095,   # Every 3 years
            'battery': 1460,       # Every 4 years
            'cabin filter': 365,   # Every 12 months
            'fuel filter': 730,    # Every 2 years
            'timing belt': 1825,   # Every 5 years
            'serpentine belt': 1095, # Every 3 years
        }
        
        for part_name, interval_days in part_intervals.items():
            # Find the last time this part was replaced
            last_replacement = None
            last_replacement_record = None
            
            for record in all_maintenance:
                # Check in work_done field
                if (record.work_done and 
                    part_name.lower() in record.work_done.lower()):
                    last_replacement = record.date_performed.date() if hasattr(record.date_performed, 'date') else record.date_performed
                    last_replacement_record = record
                    break
                
                # Also check parts_used relationship if it exists
                if hasattr(record, 'parts_used'):
                    for part_usage in record.parts_used.all():
                        if part_name.lower() in part_usage.part.name.lower():
                            last_replacement = record.date_performed.date() if hasattr(record.date_performed, 'date') else record.date_performed
                            last_replacement_record = record
                            break
                    if last_replacement:
                        break
            
            if last_replacement:
                days_since_replacement = (current_date - last_replacement).days
                
                # Check if part is due for replacement (within 30 days) or overdue
                if days_since_replacement >= interval_days - 30:
                    # Check if alert already exists for this part
                    existing_alert = VehicleAlert.objects.filter(
                        vehicle=vehicle,
                        alert_type='PART_REPLACEMENT',
                        title__icontains=part_name,
                        is_active=True
                    ).first()
                    
                    if not existing_alert:
                        # Determine priority based on how overdue the replacement is and part criticality
                        critical_parts = ['brake pads', 'brake fluid', 'battery', 'timing belt']
                        
                        if days_since_replacement > interval_days:
                            # Overdue
                            if part_name in critical_parts:
                                priority = 'HIGH'
                            else:
                                priority = 'MEDIUM'
                            days_overdue = days_since_replacement - interval_days
                            status_text = f"overdue by {days_overdue} days"
                        else:
                            # Due soon
                            priority = 'MEDIUM'
                            days_until_due = interval_days - days_since_replacement
                            status_text = f"due in {days_until_due} days"
                        
                        # Create more specific descriptions for critical parts
                        if part_name == 'brake pads':
                            description = (f"Your brake pads were last replaced on "
                                         f"{last_replacement.strftime('%B %d, %Y')} "
                                         f"and are {status_text}. "
                                         f"Worn brake pads can compromise your safety. "
                                         f"Please have them inspected and replaced if necessary.")
                        elif part_name == 'battery':
                            description = (f"Your battery was last replaced on "
                                         f"{last_replacement.strftime('%B %d, %Y')} "
                                         f"and is {status_text}. "
                                         f"A failing battery can leave you stranded. "
                                         f"Consider having it tested and replaced if needed.")
                        else:
                            description = (f"Your {part_name} was last replaced on "
                                         f"{last_replacement.strftime('%B %d, %Y')} "
                                         f"and is {status_text}. "
                                         f"Regular replacement helps maintain vehicle performance and reliability.")
                        
                        alert = VehicleAlert.objects.create(
                            vehicle=vehicle,
                            alert_type='PART_REPLACEMENT',
                            priority=priority,
                            title=f"{part_name.title()} Replacement Due",
                            description=description
                        )
                        alerts_created.append(alert)
        
        return alerts_created
    
    def check_insurance_expiry(self, vehicle):
        """
        Generate alerts for insurance policies nearing expiry
        """
        alerts_created = []
        current_date = timezone.now().date()
        
        try:
            # Get active insurance policies for this vehicle's owner
            # Since InsurancePolicy doesn't have a direct vehicle relationship,
            # we need to find policies for the vehicle owner
            vehicle_owners = vehicle.ownerships.filter(is_current_owner=True)
            
            active_policies = InsurancePolicy.objects.filter(
                policy_holder__in=[ownership.user for ownership in vehicle_owners],
                status='active',
                end_date__isnull=False
            )
            
            for policy in active_policies:
                days_until_expiry = (policy.end_date - current_date).days
                
                # Generate alerts for policies expiring within 30 days
                if 0 <= days_until_expiry <= 30:
                    # Check if alert already exists for this policy
                    existing_alert = VehicleAlert.objects.filter(
                        vehicle=vehicle,
                        alert_type='INSURANCE_EXPIRY',
                        title__icontains=policy.policy_number,
                        is_active=True
                    ).first()
                    
                    if not existing_alert:
                        # Determine priority based on days until expiry
                        if days_until_expiry <= 7:
                            priority = 'HIGH'
                        elif days_until_expiry <= 14:
                            priority = 'MEDIUM'
                        else:
                            priority = 'LOW'
                        
                        provider_name = policy.organization.name if policy.organization else "your insurance provider"
                        
                        alert = VehicleAlert.objects.create(
                            vehicle=vehicle,
                            alert_type='INSURANCE_EXPIRY',
                            priority=priority,
                            title=f"Insurance Expiring Soon - {policy.policy_number}",
                            description=f"Your insurance policy with {provider_name} "
                                       f"(Policy #{policy.policy_number}) expires on "
                                       f"{policy.end_date.strftime('%B %d, %Y')} "
                                       f"({days_until_expiry} days). "
                                       f"Please renew your policy to avoid coverage gaps."
                        )
                        alerts_created.append(alert)
                
                # Generate alerts for expired policies
                elif days_until_expiry < 0:
                    existing_alert = VehicleAlert.objects.filter(
                        vehicle=vehicle,
                        alert_type='INSURANCE_EXPIRY',
                        title__icontains=policy.policy_number,
                        is_active=True
                    ).first()
                    
                    if not existing_alert:
                        provider_name = policy.organization.name if policy.organization else "your insurance provider"
                        
                        alert = VehicleAlert.objects.create(
                            vehicle=vehicle,
                            alert_type='INSURANCE_EXPIRY',
                            priority='HIGH',
                            title=f"Insurance Expired - {policy.policy_number}",
                            description=f"Your insurance policy with {provider_name} "
                                       f"(Policy #{policy.policy_number}) expired on "
                                       f"{policy.end_date.strftime('%B %d, %Y')} "
                                       f"({abs(days_until_expiry)} days ago). "
                                       f"Your vehicle is currently uninsured. "
                                       f"Please renew immediately."
                        )
                        alerts_created.append(alert)
        
        except Exception as e:
            # Log the error but don't fail the entire alert generation
            print(f"Error checking insurance expiry for vehicle {vehicle.id}: {str(e)}")
        
        return alerts_created
    
    def generate_all_alerts(self, vehicle):
        """
        Generate all types of alerts for a vehicle
        """
        all_alerts = []
        
        # Generate maintenance alerts
        maintenance_alerts = self.generate_maintenance_alerts(vehicle)
        all_alerts.extend(maintenance_alerts)
        
        # Generate part replacement alerts
        part_alerts = self.generate_part_replacement_alerts(vehicle)
        all_alerts.extend(part_alerts)
        
        # Generate insurance expiry alerts
        insurance_alerts = self.check_insurance_expiry(vehicle)
        all_alerts.extend(insurance_alerts)
        
        return all_alerts
    
    def resolve_alert(self, alert_id, user):
        """
        Resolve an alert (mark as inactive)
        """
        try:
            alert = VehicleAlert.objects.get(
                id=alert_id,
                vehicle__ownerships__user=user,
                vehicle__ownerships__is_current_owner=True
            )
            alert.resolve()
            return True
        except VehicleAlert.DoesNotExist:
            return False