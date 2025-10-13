"""
Cost calculation utilities for vehicle maintenance analytics.
Provides methods to calculate monthly, lifetime, and categorized costs.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from typing import Dict, List, Optional, Tuple
import logging

from vehicles.models import Vehicle
from maintenance_history.models import MaintenanceRecord, PartUsage
from notifications.models import VehicleCostAnalytics

logger = logging.getLogger(__name__)


class CostCalculationUtils:
    """Utility class for calculating vehicle maintenance costs."""
    
    @staticmethod
    def calculate_parts_cost(maintenance_record: MaintenanceRecord) -> Decimal:
        """
        Calculate total parts cost for a maintenance record.
        
        Args:
            maintenance_record: MaintenanceRecord instance
            
        Returns:
            Decimal: Total parts cost
        """
        try:
            parts_cost = maintenance_record.parts_used.aggregate(
                total=Coalesce(
                    Sum(F('unit_cost') * F('quantity'), output_field=DecimalField()),
                    Decimal('0.00')
                )
            )['total']
            
            return parts_cost or Decimal('0.00')
        except Exception as e:
            logger.error(f"Error calculating parts cost for record {maintenance_record.id}: {str(e)}")
            return Decimal('0.00')
    
    @staticmethod
    def calculate_labor_cost(maintenance_record: MaintenanceRecord) -> Decimal:
        """
        Calculate labor cost for a maintenance record.
        
        Note: Currently returns 0 as labor cost is not tracked in the current model.
        This method is a placeholder for future implementation.
        
        Args:
            maintenance_record: MaintenanceRecord instance
            
        Returns:
            Decimal: Labor cost (currently always 0)
        """
        # TODO: Implement labor cost calculation when labor cost tracking is added to models
        return Decimal('0.00')
    
    @staticmethod
    def calculate_total_maintenance_cost(maintenance_record: MaintenanceRecord) -> Decimal:
        """
        Calculate total cost for a maintenance record (parts + labor).
        
        Args:
            maintenance_record: MaintenanceRecord instance
            
        Returns:
            Decimal: Total maintenance cost
        """
        parts_cost = CostCalculationUtils.calculate_parts_cost(maintenance_record)
        labor_cost = CostCalculationUtils.calculate_labor_cost(maintenance_record)
        
        return parts_cost + labor_cost
    
    @staticmethod
    def calculate_monthly_costs(vehicle: Vehicle, year: int, month: int) -> Dict[str, Decimal]:
        """
        Calculate maintenance costs for a specific month.
        
        Args:
            vehicle: Vehicle instance
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            Dict containing total_cost, maintenance_cost, parts_cost, labor_cost
        """
        try:
            # Get maintenance records for the specified month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            maintenance_records = MaintenanceRecord.objects.filter(
                vehicle=vehicle,
                date_performed__date__gte=start_date,
                date_performed__date__lt=end_date
            ).prefetch_related('parts_used')
            
            total_parts_cost = Decimal('0.00')
            total_labor_cost = Decimal('0.00')
            
            for record in maintenance_records:
                total_parts_cost += CostCalculationUtils.calculate_parts_cost(record)
                total_labor_cost += CostCalculationUtils.calculate_labor_cost(record)
            
            total_maintenance_cost = total_parts_cost + total_labor_cost
            
            return {
                'total_cost': total_maintenance_cost,
                'maintenance_cost': total_maintenance_cost,
                'parts_cost': total_parts_cost,
                'labor_cost': total_labor_cost
            }
            
        except Exception as e:
            logger.error(f"Error calculating monthly costs for vehicle {vehicle.id}, {year}-{month}: {str(e)}")
            return {
                'total_cost': Decimal('0.00'),
                'maintenance_cost': Decimal('0.00'),
                'parts_cost': Decimal('0.00'),
                'labor_cost': Decimal('0.00')
            }
    
    @staticmethod
    def calculate_lifetime_costs(vehicle: Vehicle) -> Dict[str, Decimal]:
        """
        Calculate lifetime maintenance costs for a vehicle.
        
        Args:
            vehicle: Vehicle instance
            
        Returns:
            Dict containing lifetime cost breakdown
        """
        try:
            maintenance_records = MaintenanceRecord.objects.filter(
                vehicle=vehicle
            ).prefetch_related('parts_used')
            
            total_parts_cost = Decimal('0.00')
            total_labor_cost = Decimal('0.00')
            
            for record in maintenance_records:
                total_parts_cost += CostCalculationUtils.calculate_parts_cost(record)
                total_labor_cost += CostCalculationUtils.calculate_labor_cost(record)
            
            total_lifetime_cost = total_parts_cost + total_labor_cost
            
            return {
                'lifetime_total_cost': total_lifetime_cost,
                'lifetime_parts_cost': total_parts_cost,
                'lifetime_labor_cost': total_labor_cost,
                'total_maintenance_records': maintenance_records.count()
            }
            
        except Exception as e:
            logger.error(f"Error calculating lifetime costs for vehicle {vehicle.id}: {str(e)}")
            return {
                'lifetime_total_cost': Decimal('0.00'),
                'lifetime_parts_cost': Decimal('0.00'),
                'lifetime_labor_cost': Decimal('0.00'),
                'total_maintenance_records': 0
            }
    
    @staticmethod
    def calculate_average_monthly_cost(vehicle: Vehicle, months: int = 12) -> Decimal:
        """
        Calculate average monthly maintenance cost over a specified period.
        
        Args:
            vehicle: Vehicle instance
            months: Number of months to calculate average over (default: 12)
            
        Returns:
            Decimal: Average monthly cost
        """
        try:
            end_date = date.today()
            start_date = end_date - relativedelta(months=months)
            
            maintenance_records = MaintenanceRecord.objects.filter(
                vehicle=vehicle,
                date_performed__date__gte=start_date,
                date_performed__date__lte=end_date
            ).prefetch_related('parts_used')
            
            total_cost = Decimal('0.00')
            
            for record in maintenance_records:
                total_cost += CostCalculationUtils.calculate_total_maintenance_cost(record)
            
            if months > 0:
                average_cost = total_cost / Decimal(str(months))
                return average_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            return Decimal('0.00')
            
        except Exception as e:
            logger.error(f"Error calculating average monthly cost for vehicle {vehicle.id}: {str(e)}")
            return Decimal('0.00')
    
    @staticmethod
    def get_cost_trends(vehicle: Vehicle, months: int = 12) -> List[Dict]:
        """
        Get monthly cost trends for the specified number of months.
        
        Args:
            vehicle: Vehicle instance
            months: Number of months to retrieve trends for
            
        Returns:
            List of dictionaries with month and cost data
        """
        try:
            trends = []
            end_date = date.today()
            
            for i in range(months):
                month_date = end_date - relativedelta(months=i)
                monthly_costs = CostCalculationUtils.calculate_monthly_costs(
                    vehicle, month_date.year, month_date.month
                )
                
                trends.append({
                    'month': month_date.strftime('%Y-%m'),
                    'month_name': month_date.strftime('%B %Y'),
                    'total_cost': monthly_costs['total_cost'],
                    'parts_cost': monthly_costs['parts_cost'],
                    'labor_cost': monthly_costs['labor_cost']
                })
            
            # Reverse to get chronological order (oldest first)
            return list(reversed(trends))
            
        except Exception as e:
            logger.error(f"Error getting cost trends for vehicle {vehicle.id}: {str(e)}")
            return []
    
    @staticmethod
    def calculate_cost_by_service_type(vehicle: Vehicle, months: int = 12) -> Dict[str, Decimal]:
        """
        Calculate costs grouped by service type over specified months.
        
        Args:
            vehicle: Vehicle instance
            months: Number of months to analyze
            
        Returns:
            Dict with service types as keys and costs as values
        """
        try:
            end_date = date.today()
            start_date = end_date - relativedelta(months=months)
            
            maintenance_records = MaintenanceRecord.objects.filter(
                vehicle=vehicle,
                date_performed__date__gte=start_date,
                date_performed__date__lte=end_date
            ).prefetch_related('parts_used', 'scheduled_maintenance__task__service_type')
            
            service_costs = {}
            
            for record in maintenance_records:
                total_cost = CostCalculationUtils.calculate_total_maintenance_cost(record)
                
                # Get service type from scheduled maintenance or use work_done as fallback
                if record.scheduled_maintenance and record.scheduled_maintenance.task.service_type:
                    service_type = record.scheduled_maintenance.task.service_type.name
                else:
                    # Use first 50 characters of work_done as service type
                    service_type = record.work_done[:50] if record.work_done else 'Other'
                
                if service_type in service_costs:
                    service_costs[service_type] += total_cost
                else:
                    service_costs[service_type] = total_cost
            
            return service_costs
            
        except Exception as e:
            logger.error(f"Error calculating costs by service type for vehicle {vehicle.id}: {str(e)}")
            return {}
    
    @staticmethod
    def store_monthly_analytics(vehicle: Vehicle, year: int, month: int) -> Optional[VehicleCostAnalytics]:
        """
        Calculate and store monthly cost analytics in the database.
        
        Args:
            vehicle: Vehicle instance
            year: Year
            month: Month
            
        Returns:
            VehicleCostAnalytics instance or None if error
        """
        try:
            monthly_costs = CostCalculationUtils.calculate_monthly_costs(vehicle, year, month)
            month_date = date(year, month, 1)
            
            # Update or create the analytics record
            analytics, created = VehicleCostAnalytics.objects.update_or_create(
                vehicle=vehicle,
                month=month_date,
                defaults={
                    'total_cost': monthly_costs['total_cost'],
                    'maintenance_cost': monthly_costs['maintenance_cost'],
                    'parts_cost': monthly_costs['parts_cost'],
                    'labor_cost': monthly_costs['labor_cost']
                }
            )
            
            logger.info(f"{'Created' if created else 'Updated'} cost analytics for vehicle {vehicle.id}, {year}-{month}")
            return analytics
            
        except Exception as e:
            logger.error(f"Error storing monthly analytics for vehicle {vehicle.id}, {year}-{month}: {str(e)}")
            return None
    
    @staticmethod
    def bulk_calculate_analytics(vehicle: Vehicle, months: int = 12) -> int:
        """
        Calculate and store analytics for multiple months.
        
        Args:
            vehicle: Vehicle instance
            months: Number of months to calculate (working backwards from current month)
            
        Returns:
            Number of analytics records created/updated
        """
        try:
            count = 0
            end_date = date.today()
            
            for i in range(months):
                month_date = end_date - relativedelta(months=i)
                analytics = CostCalculationUtils.store_monthly_analytics(
                    vehicle, month_date.year, month_date.month
                )
                if analytics:
                    count += 1
            
            logger.info(f"Bulk calculated analytics for {count} months for vehicle {vehicle.id}")
            return count
            
        except Exception as e:
            logger.error(f"Error in bulk calculate analytics for vehicle {vehicle.id}: {str(e)}")
            return 0