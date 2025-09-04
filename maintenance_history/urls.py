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
    
    # Inspection Record URLs
    path('inspections/', 
         views.InspectionListView.as_view(), 
         name='inspection_list'),
    path('inspections/<int:pk>/', 
         views.InspectionDetailView.as_view(), 
         name='inspection_detail'),
    path('inspections/<int:pk>/pdf/', 
         views.InspectionPDFViewerView.as_view(), 
         name='inspection_pdf_viewer'),
    path('inspections/<int:pk>/download/', 
         views.InspectionPDFDownloadView.as_view(), 
         name='inspection_pdf_download'),
    path('inspections/create/', 
         views.CreateInspectionRecordView.as_view(), 
         name='create_inspection_record'),
    
    # New Inspection Workflow (starts with form)
    path('inspections/start/', 
         views.StartInspectionWorkflowView.as_view(), 
         name='start_inspection_workflow'),
    
    # Inspection Form URLs (50-point checklist)
    path('inspection-forms/', 
         views.InspectionFormListView.as_view(), 
         name='inspection_form_list'),
    path('inspection-forms/<int:pk>/', 
         views.InspectionFormDetailView.as_view(), 
         name='inspection_form_detail'),
    path('inspection-forms/create/', 
         views.CreateInspectionFormView.as_view(), 
         name='create_inspection_form'),
    path('inspection-forms/create/<int:inspection_id>/', 
         views.CreateInspectionFormView.as_view(), 
         name='create_inspection_form'),
    path('inspection-forms/<int:pk>/update/', 
         views.UpdateInspectionFormView.as_view(), 
         name='update_inspection_form'),
    path('inspection-form/ajax/<int:pk>/', 
         views.InspectionFormAjaxView.as_view(), 
         name='inspection_form_ajax'),
    
    # API endpoints for part management
    path('api/parts/search/', 
         api_views.PartSearchAPIView.as_view(), 
         name='part_search_api'),
    path('api/parts/<int:part_id>/', 
         api_views.PartDetailsAPIView.as_view(), 
         name='part_details_api'),
    
    # Initial Inspection URLs (160-point pre-purchase inspections)
    path('initial-inspections/', 
         views.InitialInspectionListView.as_view(), 
         name='initial_inspection_list'),
    path('initial-inspections/<int:pk>/', 
         views.InitialInspectionDetailView.as_view(), 
         name='initial_inspection_detail'),
    path('initial-inspections/create/', 
         views.CreateInitialInspectionView.as_view(), 
         name='create_initial_inspection'),
    path('initial-inspections/<int:pk>/update/', 
         views.UpdateInitialInspectionView.as_view(), 
         name='update_initial_inspection'),
    path('initial-inspection/ajax/<int:pk>/', 
         views.InitialInspectionAjaxView.as_view(), 
         name='initial_inspection_ajax'),
    
    # API endpoint for scheduled maintenance
    path('api/scheduled-maintenance/', 
         api_views.ScheduledMaintenanceAPIView.as_view(), 
         name='scheduled_maintenance_api'),
]
