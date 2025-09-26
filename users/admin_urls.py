"""
URL configuration for custom admin views in the users app.
"""

from django.urls import path
from . import admin_views

app_name = 'users_admin'

urlpatterns = [
    path('user-permissions/', admin_views.UserPermissionsView.as_view(), name='user_permissions'),
    path('bulk-management/', admin_views.bulk_user_management, name='bulk_management'),
    path('users-without-access/', admin_views.users_without_access_report, name='users_without_access'),
    path('export-permissions/', admin_views.export_user_permissions, name='export_permissions'),
    path('group-dashboard-mapping/', admin_views.group_dashboard_mapping, name='group_dashboard_mapping'),
    path('ajax/user-permissions/', admin_views.ajax_user_permissions, name='ajax_user_permissions'),
    path('three-group-management/', admin_views.three_group_management, name='three_group_management'),
    path('ajax/test-group/', admin_views.ajax_test_group_config, name='ajax_test_group'),
]