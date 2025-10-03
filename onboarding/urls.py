from django.urls import path
from . import views
from .forms import ClientForm, VehicleForm, VehicleStatusForm, VehicleEquipmentForm, VehicleImagesForm

app_name = 'onboarding'

urlpatterns = [
    # Multi-step onboarding workflow
    path('step-1/', views.onboarding_step_1, name='onboarding_step_1'),
    path('step-2/', views.onboarding_step_2, name='onboarding_step_2'),
    path('step-3/', views.onboarding_step_3, name='onboarding_step_3'),
    path('step-4/', views.onboarding_step_4, name='onboarding_step_4'),
    path('complete/', views.onboarding_complete, name='onboarding_complete'),
    
    # Legacy customer & vehicle survey (kept for compatibility)
    path('survey/', views.customer_vehicle_survey, name='customer_vehicle_survey'),
    path('survey/complete/', views.onboarding_complete_view, name='onboarding_complete_view'),
    
    # Technician vehicle onboarding
    path('technician/vehicle/', views.technician_vehicle_onboarding, name='technician_vehicle_onboarding'),
    
    # Existing vehicle onboarding (for admin/staff use)
    path('onboarding/client/', views.onboard_client, name='onboard_client'),
    path('onboarding/vehicle/', views.onboard_vehicle, name='onboard_vehicle'),
    path('onboarding/status/', views.onboard_status, name='onboard_status'),
    path('onboarding/equipment/', views.onboard_equipment, name='onboard_equipment'),
    path('onboarding/images/', views.onboard_images, name='onboard_images'),
    path('onboarding/complete/', views.onboard_complete, name='onboard_complete'),
]
