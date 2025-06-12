from django.urls import path
from . import views

urlpatterns = [
    path('technician-dashboard/', 
         views.TechnicianDashboardView.as_view(), 
         name='technician_dashboard'),
    path('create-record/', 
         views.CreateMaintenanceRecordView.as_view(), 
         name='create_record'),
   
]
