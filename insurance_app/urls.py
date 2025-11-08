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

# Parts-Based Quote System API Endpoints
from . import api_views
router.register(r'damaged-parts', api_views.DamagedPartViewSet, basename='damaged-part')
router.register(r'quote-requests', api_views.PartQuoteRequestViewSet, basename='quote-request')
router.register(r'quotes', api_views.PartQuoteViewSet, basename='quote')
router.register(r'market-averages', api_views.MarketAverageViewSet, basename='market-average')
router.register(r'recommendations', api_views.QuoteRecommendationViewSet, basename='recommendation')

app_name = 'insurance'

urlpatterns = [
    # Dashboard Views
    path('', views.DashboardView.as_view(), name='insurance_dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard-view/', views.insurance_dashboard_view, name='insurance_dashboard_function'),
    path('assessments/', views.AssessmentDashboardView.as_view(), name='assessment_dashboard'),
    path('assessments/<str:claim_id>/', views.AssessmentDetailView.as_view(), name='assessment_detail'),
    path('assessments/<str:claim_id>/section/<str:section_id>/', views.AssessmentSectionDetailView.as_view(), name='assessment_section_detail'),
    path('assessments/<str:assessment_id>/report/', views.AssessmentReportView.as_view(), name='assessment_report'),
    path('book-assessment/', views.BookAssessmentView.as_view(), name='book_assessment'),
    path('vehicle/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vehicle/<int:pk>/detail/', views.VehicleDetailView.as_view(), name='insurance_vehicle_detail'),
    
    # Comment and Feedback System
    path('assessments/<int:assessment_id>/comments/add/', views.AssessmentCommentCreateView.as_view(), name='add_comment'),
    path('assessments/<int:assessment_id>/comments/<int:parent_comment_id>/reply/', views.add_comment_reply, name='add_comment_reply'),
    path('assessments/<int:assessment_id>/comments/<int:comment_id>/resolve/', views.resolve_comment, name='resolve_comment'),
    
    # Workflow Management
    path('assessments/<str:assessment_id>/workflow/', views.AssessmentWorkflowActionView.as_view(), name='assessment_workflow_action'),
    path('assessments/<str:assessment_id>/workflow/history/', views.AssessmentWorkflowHistoryView.as_view(), name='assessment_workflow_history'),
    
    # Report Sharing
    path('assessments/<str:assessment_id>/report/share/', views.AssessmentReportShareView.as_view(), name='assessment_report_share'),
    path('assessments/<str:assessment_id>/report/history/', views.AssessmentReportHistoryView.as_view(), name='assessment_report_history'),
    
    # Assessment History and Audit Trail
    path('assessments/<str:assessment_id>/history/', views.AssessmentHistoryView.as_view(), name='assessment_history'),
    path('assessments/<str:assessment_id>/versions/compare/', views.AssessmentVersionCompareView.as_view(), name='assessment_version_compare'),
    path('assessments/<str:assessment_id>/versions/rollback/', views.AssessmentRollbackView.as_view(), name='assessment_rollback'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/calculate-portfolio-metrics/', views.calculate_portfolio_metrics, name='calculate_metrics'),
    path('api/vehicles/<int:vehicle_id>/comprehensive-accidents/', 
         views.get_comprehensive_accident_data, name='comprehensive_accidents'),
    path('api/assessments/<int:assessment_id>/comments/', views.assessment_comments_api, name='assessment_comments_api'),
    path('api/notifications/', views.user_notifications, name='user_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Additional API endpoints
    path('api/vehicles/<int:pk>/risk-assessment/', 
         views.VehicleViewSet.as_view({'get': 'risk_assessment'}), 
         name='vehicle_risk_assessment'),
    
    # Parts Review API endpoints
    path('api/assessments/<int:assessment_id>/identify-parts/', 
         api_views.identify_parts_for_assessment, 
         name='identify_parts_for_assessment'),
    path('api/assessments/<int:assessment_id>/damaged-parts/', 
         api_views.create_damaged_part, 
         name='create_damaged_part'),
    path('api/damaged-parts/<int:part_id>/', 
         api_views.manage_damaged_part, 
         name='manage_damaged_part'),
    path('api/assessments/<int:assessment_id>/quote-requests/', 
         api_views.create_quote_requests, 
         name='create_quote_requests'),
]
