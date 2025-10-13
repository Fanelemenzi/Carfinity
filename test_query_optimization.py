"""
Test script to verify query optimization improvements for task 13.1
"""
import os
import sys
import django
from django.test import TestCase
from django.db import connection
from django.test.utils import override_settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleOwnership
from notifications.services import DashboardService
from notifications.models import VehicleAlert, VehicleCostAnalytics
from maintenance.models import ScheduledMaintenance, MaintenanceTask, MaintenancePlan, AssignedVehiclePlan
from maintenance_history.models import MaintenanceRecord
from datetime import datetime, timedelta
from django.utils import timezone


def test_query_optimization():
    """Test that the optimized queries reduce database hits"""
    
    print("Testing query optimization for DashboardService...")
    
    # Create test data
    user, created = User.objects.get_or_create(
        username='testuser_opt',
        defaults={'password': 'testpass'}
    )
    
    vehicle, created = Vehicle.objects.get_or_create(
        vin='1HGCM82633A123456',
        defaults={
            'make': 'Toyota',
            'model': 'Corolla',
            'manufacture_year': 2018
        }
    )
    
    VehicleOwnership.objects.get_or_create(
        user=user,
        vehicle=vehicle,
        defaults={
            'is_current_owner': True,
            'start_date': timezone.now().date()
        }
    )
    
    # Create some test maintenance records
    for i in range(5):
        MaintenanceRecord.objects.get_or_create(
            vehicle=vehicle,
            work_done=f'Service {i}',
            defaults={
                'date_performed': timezone.now() - timedelta(days=i*30),
                'mileage': 100000 + (i * 1000)
            }
        )
    
    # Create test alerts
    for i in range(3):
        VehicleAlert.objects.get_or_create(
            vehicle=vehicle,
            title=f'Test Alert {i}',
            defaults={
                'alert_type': 'MAINTENANCE_OVERDUE',
                'priority': 'HIGH' if i == 0 else 'MEDIUM',
                'description': f'Test alert description {i}',
                'is_active': True
            }
        )
    
    # Create test cost analytics
    for i in range(6):
        month_date = timezone.now().date().replace(day=1) - timedelta(days=i*30)
        VehicleCostAnalytics.objects.get_or_create(
            vehicle=vehicle,
            month=month_date,
            defaults={
                'total_cost': 200.00 + (i * 20),
                'maintenance_cost': 150.00 + (i * 15),
                'parts_cost': 100.00 + (i * 10),
                'labor_cost': 50.00 + (i * 5)
            }
        )
    
    dashboard_service = DashboardService()
    
    # Test the optimized complete dashboard data method
    print("\n1. Testing get_complete_dashboard_data (optimized single query)...")
    
    # Reset query count
    connection.queries_log.clear()
    
    dashboard_data = dashboard_service.get_complete_dashboard_data(vehicle.id, user)
    
    query_count_optimized = len(connection.queries)
    print(f"   Queries executed: {query_count_optimized}")
    
    if dashboard_data:
        print("   ✓ Dashboard data retrieved successfully")
        print(f"   ✓ Vehicle overview: {dashboard_data['vehicle_overview']['make']} {dashboard_data['vehicle_overview']['model']}")
        print(f"   ✓ Active alerts: {len(dashboard_data['alerts'])}")
        print(f"   ✓ Service history records: {len(dashboard_data['service_history'])}")
        print(f"   ✓ Monthly analytics: {len(dashboard_data['cost_analytics']['monthly_data'])}")
    else:
        print("   ✗ Failed to retrieve dashboard data")
    
    # Test individual methods for comparison
    print("\n2. Testing individual methods (for comparison)...")
    
    connection.queries_log.clear()
    
    overview = dashboard_service.get_vehicle_overview(vehicle.id, user)
    alerts = dashboard_service.get_vehicle_alerts(vehicle.id, user)
    history = dashboard_service.get_service_history(vehicle.id, user, limit=5)
    analytics = dashboard_service.get_cost_analytics(vehicle.id, user)
    
    query_count_individual = len(connection.queries)
    print(f"   Queries executed: {query_count_individual}")
    
    print(f"\n3. Query optimization results:")
    print(f"   Single optimized query: {query_count_optimized} queries")
    print(f"   Individual method calls: {query_count_individual} queries")
    
    if query_count_optimized < query_count_individual:
        print(f"   ✓ Optimization successful! Reduced queries by {query_count_individual - query_count_optimized}")
    else:
        print(f"   ⚠ Optimization may need improvement")
    
    # Test database indexes by checking query plans (if PostgreSQL)
    print("\n4. Testing database indexes...")
    
    # Test alert queries with indexes
    connection.queries_log.clear()
    
    alerts_with_filter = VehicleAlert.objects.filter(
        vehicle_id=vehicle.id,
        is_active=True,
        alert_type='MAINTENANCE_OVERDUE'
    ).count()
    
    print(f"   Alert query with indexes executed: {len(connection.queries)} queries")
    print(f"   Found {alerts_with_filter} matching alerts")
    
    # Test cost analytics queries with indexes
    connection.queries_log.clear()
    
    recent_analytics = VehicleCostAnalytics.objects.filter(
        vehicle_id=vehicle.id,
        month__gte=timezone.now().date().replace(day=1) - timedelta(days=180)
    ).count()
    
    print(f"   Cost analytics query with indexes executed: {len(connection.queries)} queries")
    print(f"   Found {recent_analytics} recent analytics records")
    
    print("\n✓ Query optimization tests completed!")
    
    # Cleanup
    VehicleAlert.objects.filter(vehicle=vehicle).delete()
    VehicleCostAnalytics.objects.filter(vehicle=vehicle).delete()
    MaintenanceRecord.objects.filter(vehicle=vehicle).delete()
    VehicleOwnership.objects.filter(vehicle=vehicle).delete()
    vehicle.delete()
    user.delete()


if __name__ == '__main__':
    test_query_optimization()