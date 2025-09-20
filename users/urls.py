from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login-dashboard/', views.login_dashboard, name='login_dashboard'),
    path('test-auth/', views.test_auth, name='test_auth'),
    path('register/', views.register_user, name='register'),
    path('search/', views.search, name='search'),
    path('search-results/', views.search_results, name='search_results'),
    path('onboarding/', views.typeform_redirect, name='typeform_onboarding'),
    path('check-onboarding/', views.check_onboarding_status, name='check_onboarding_status'),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('no-groups/', views.no_groups_error, name='no_groups_error'),
    path('no-organization/', views.no_organization_error, name='no_organization_error'),
    path('system-error/', views.system_error, name='system_error'),
    path('dashboard-selector/', views.dashboard_selector, name='dashboard_selector'),
    path('switch-dashboard/<str:dashboard_name>/', views.switch_dashboard, name='switch_dashboard'),
    path('api/dashboard-switch/', views.dashboard_switch_api, name='dashboard_switch_api'),
    #path('create-record/', views.create_record, name='create_record'),
   
]
