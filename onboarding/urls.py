from django.urls import path
from . import views
from .forms import ClientForm, VehicleForm, VehicleStatusForm, VehicleEquipmentForm, VehicleImagesForm

app_name = 'onboarding'

urlpatterns = [
    # Onboarding Dashboard
    path('', views.onboarding_dashboard, name='onboarding_dashboard'),
    path('dashboard/', views.onboarding_dashboard, name='dashboard'),
    
    # New Multi-step onboarding workflow (Assessment-style)
    path('start/', views.start_onboarding, name='start_onboarding'),
    path('<int:onboarding_id>/service-preferences/', views.service_preferences, name='service_preferences'),
    path('<int:onboarding_id>/vehicle-information/', views.vehicle_information, name='vehicle_information'),
    path('<int:onboarding_id>/maintenance-preferences/', views.maintenance_preferences, name='maintenance_preferences'),
    path('<int:onboarding_id>/payment-preferences/', views.payment_preferences, name='payment_preferences'),
    path('<int:onboarding_id>/review/', views.onboarding_review, name='onboarding_review'),
    path('<int:onboarding_id>/continue/', views.continue_onboarding, name='continue_onboarding'),
    path('<int:onboarding_id>/detail/', views.onboarding_detail, name='onboarding_detail'),
    path('<int:onboarding_id>/update-status/', views.update_onboarding_status, name='update_onboarding_status'),
    path('<int:onboarding_id>/delete/', views.delete_onboarding, name='delete_onboarding'),
    path('complete/', views.onboarding_complete, name='onboarding_complete'),
    
    # Legacy URLs (redirected to new workflow)
    path('step-1/', views.start_onboarding, name='onboarding_step_1'),
    path('step-2/', views.start_onboarding, name='onboarding_step_2'),
    path('step-3/', views.start_onboarding, name='onboarding_step_3'),
    path('step-4/', views.start_onboarding, name='onboarding_step_4'),
    
    # Legacy customer & vehicle survey (updated for compatibility)
    path('survey/', views.customer_vehicle_survey, name='customer_vehicle_survey'),
    path('survey/complete/', views.onboarding_complete_view, name='onboarding_complete_view'),
    
    # Technician vehicle onboarding (updated)
    path('technician/vehicle/', views.technician_vehicle_onboarding, name='technician_vehicle_onboarding'),
    
    # Existing vehicle onboarding (for admin/staff use - kept for compatibility)
    path('admin/client/', views.onboard_client, name='onboard_client'),
    path('admin/vehicle/', views.onboard_vehicle, name='onboard_vehicle'),
    path('admin/status/', views.onboard_status, name='onboard_status'),
    path('admin/equipment/', views.onboard_equipment, name='onboard_equipment'),
    path('admin/images/', views.onboard_images, name='onboard_images'),
    path('admin/complete/', views.onboard_complete, name='onboard_complete'),
]
