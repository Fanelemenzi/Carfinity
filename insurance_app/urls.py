# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()
router.register(r'vehicles', views.VehicleViewSet, basename='insurance-vehicle')
router.register(r'maintenance-schedules', views.MaintenanceScheduleViewSet, basename='insurance-maintenance-schedule')
router.register(r'maintenance-compliance', views.MaintenanceComplianceViewSet, basename='insurance-maintenance-compliance')
router.register(r'risk-alerts', views.RiskAlertViewSet, basename='insurance-risk-alert')

app_name = 'insurance'

urlpatterns = [
    # Dashboard Views
    path('', views.DashboardView.as_view(), name='insurance_dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard-view/', views.insurance_dashboard_view, name='insurance_dashboard_function'),
    path('assessments/', views.AssessmentDashboardView.as_view(), name='assessment_dashboard'),
    path('assessments/<str:claim_id>/', views.AssessmentDetailView.as_view(), name='assessment_detail'),
    path('assessments/<str:claim_id>/section/<str:section_id>/', views.AssessmentSectionDetailView.as_view(), name='assessment_section_detail'),
    path('book-assessment/', views.BookAssessmentView.as_view(), name='book_assessment'),
    path('vehicle/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vehicle/<int:pk>/detail/', views.VehicleDetailView.as_view(), name='insurance_vehicle_detail'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/calculate-portfolio-metrics/', views.calculate_portfolio_metrics, name='calculate_metrics'),
    path('api/vehicles/<int:vehicle_id>/comprehensive-accidents/', 
         views.get_comprehensive_accident_data, name='comprehensive_accidents'),
    
    # Additional API endpoints
    path('api/vehicles/<int:pk>/risk-assessment/', 
         views.VehicleViewSet.as_view({'get': 'risk_assessment'}), 
         name='vehicle_risk_assessment'),
]
