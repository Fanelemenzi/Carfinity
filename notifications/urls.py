"""
URL configuration for notifications app
Provides dashboard views and API endpoints for AutoCare dashboard functionality
"""

from django.urls import path
from .views import (
    AutoCareDashboardView,
    DashboardAPIView,
    VehicleSwitchAPIView,
    VehicleOverviewAPIView,
    UpcomingMaintenanceAPIView,
    VehicleAlertsAPIView,
    ServiceHistoryAPIView,
    CostAnalyticsAPIView,
    VehicleValuationAPIView,
)

app_name = 'notifications'

urlpatterns = [
    # Dashboard views
    path('dashboard/', AutoCareDashboardView.as_view(), name='autocare_dashboard'),
    path('dashboard/<int:vehicle_id>/', AutoCareDashboardView.as_view(), name='autocare_dashboard_vehicle'),
    
    # API endpoints
    path('api/dashboard/<int:vehicle_id>/', DashboardAPIView.as_view(), name='dashboard_api'),
    path('api/vehicle/switch/<int:vehicle_id>/', VehicleSwitchAPIView.as_view(), name='vehicle_switch_api'),
    path('api/vehicle/<int:vehicle_id>/overview/', VehicleOverviewAPIView.as_view(), name='vehicle_overview_api'),
    path('api/vehicle/<int:vehicle_id>/maintenance/', UpcomingMaintenanceAPIView.as_view(), name='upcoming_maintenance_api'),
    path('api/vehicle/<int:vehicle_id>/alerts/', VehicleAlertsAPIView.as_view(), name='vehicle_alerts_api'),
    path('api/vehicle/<int:vehicle_id>/history/', ServiceHistoryAPIView.as_view(), name='service_history_api'),
    path('api/vehicle/<int:vehicle_id>/costs/', CostAnalyticsAPIView.as_view(), name='cost_analytics_api'),
    path('api/vehicle/<int:vehicle_id>/valuation/', VehicleValuationAPIView.as_view(), name='vehicle_valuation_api'),
    
    # VIN decoding endpoint will be added later when VIN functionality is implemented
    # path('api/vin/decode/', VINDecodeAPIView.as_view(), name='vin_decode_api'),
]