from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Dashboard and main views
    path('', views.assessment_dashboard, name='dashboard'),
    path('start/', views.start_assessment, name='start_assessment'),
    
    # Assessment workflow steps
    path('<int:assessment_id>/location/', views.incident_location, name='incident_location'),
    path('<int:assessment_id>/exterior-damage/', views.exterior_damage_assessment, name='exterior_damage'),
    path('<int:assessment_id>/wheels-tires/', views.wheels_tires_assessment, name='wheels_tires'),
    path('<int:assessment_id>/interior-damage/', views.interior_damage_assessment, name='interior_damage'),
    path('<int:assessment_id>/mechanical/', views.mechanical_systems_assessment, name='mechanical_systems'),
    path('<int:assessment_id>/electrical/', views.electrical_systems_assessment, name='electrical_systems'),
    path('<int:assessment_id>/safety/', views.safety_systems_assessment, name='safety_systems'),
    path('<int:assessment_id>/structural/', views.structural_assessment, name='structural_assessment'),
    path('<int:assessment_id>/fluids/', views.fluid_systems_assessment, name='fluid_systems'),
    path('<int:assessment_id>/documentation/', views.documentation_assessment, name='documentation_assessment'),
    path('<int:assessment_id>/categorization/', views.assessment_categorization, name='categorization'),
    path('<int:assessment_id>/financial/', views.financial_information, name='financial_information'),
    path('<int:assessment_id>/notes/', views.assessment_notes, name='assessment_notes'),
    
    # Assessment management
    path('<int:assessment_id>/', views.assessment_detail, name='assessment_detail'),
    path('<int:assessment_id>/continue/', views.continue_assessment, name='continue_assessment'),
    path('<int:assessment_id>/update-status/', views.update_assessment_status, name='update_status'),
    path('<int:assessment_id>/photos/', views.upload_photos, name='upload_photos'),
    path('<int:assessment_id>/delete-photo/', views.delete_photo, name='delete_photo'),
    path('<int:assessment_id>/report/', views.generate_report, name='generate_report'),
    path('<int:assessment_id>/delete/', views.delete_assessment, name='delete_assessment'),
]