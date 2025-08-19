from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    # Template URLs
    path('', views.organization_list, name='organization_list'),
    path('<int:pk>/', views.organization_detail, name='organization_detail'),
    path('insurance/dashboard/', views.insurance_dashboard, name='insurance_dashboard'),
    
    # AJAX URLs
    path('ajax/available-groups/', views.available_groups, name='available_groups'),
    path('ajax/<int:org_id>/link-group/', views.link_group_to_organization, name='link_group_to_organization'),
]