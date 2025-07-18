from django.urls import path
from . import views
from .forms import ClientForm, VehicleForm, VehicleStatusForm, VehicleEquipmentForm

urlpatterns = [
    path('onboarding/client/', views.onboard_client, name='onboard_client'),
    path('onboarding/vehicle/', views.onboard_vehicle, name='onboard_vehicle'),
    path('onboarding/status/', views.onboard_status, name='onboard_status'),
    path('onboarding/equipment/', views.onboard_equipment, name='onboard_equipment'),
    path('onboarding/complete/', views.onboard_complete, name='onboard_complete'),
]
