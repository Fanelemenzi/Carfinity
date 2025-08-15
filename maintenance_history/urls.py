from django.urls import path
from . import views
from . import api_views

app_name = 'maintenance_history'

urlpatterns = [
    path('technician-dashboard/', 
         views.TechnicianDashboardView.as_view(), 
         name='technician_dashboard'),
    path('create-record/', 
         views.CreateMaintenanceRecordView.as_view(), 
         name='create_record'),
    
    # API endpoints for part management
    path('api/parts/search/', 
         api_views.PartSearchAPIView.as_view(), 
         name='part_search_api'),
    path('api/parts/<int:part_id>/', 
         api_views.PartDetailsAPIView.as_view(), 
         name='part_details_api'),
]
