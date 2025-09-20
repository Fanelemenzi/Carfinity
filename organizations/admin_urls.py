"""
URL configuration for custom organization admin views.
"""

from django.urls import path
from . import admin_views

app_name = 'organizations_admin'

urlpatterns = [
    path('group-management/', admin_views.organization_group_management, name='group_management'),
    path('ajax/sync-groups/', admin_views.ajax_sync_organization_groups, name='ajax_sync_groups'),
]