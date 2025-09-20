"""
URL configuration for custom admin views in the users app.
"""

from django.urls import path
from . import admin_views

app_name = 'users_admin'

urlpatterns = [
    path('user-permissions/', admin_views.UserPermissionsView.as_view(), name='user_permissions'),
    path('bulk-management/', admin_views.bulk_user_management, name='bulk_management'),
    path('permission-conflicts/', admin_views.permission_conflicts_report, name='permission_conflicts'),
    path('export-permissions/', admin_views.export_user_permissions, name='export_permissions'),
    path('group-org-mapping/', admin_views.group_organization_mapping, name='group_org_mapping'),
    path('ajax/user-permissions/', admin_views.ajax_user_permissions, name='ajax_user_permissions'),
    path('auth-group-management/', admin_views.authentication_group_management, name='auth_group_management'),
    path('ajax/test-auth-group/', admin_views.ajax_test_auth_group_config, name='ajax_test_auth_group'),
]