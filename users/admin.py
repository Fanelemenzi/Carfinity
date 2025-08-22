from django.contrib import admin
from .models import User, Profile, Role, UserRole, DataConsent, OrganizationUser
from django.db import models
# from django_json_widget.widgets import JSONEditorWidget

# Register your models here.


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country')
    search_fields = ('user__email', 'city', 'country')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    # formfield_overrides = {
    #     models.JSONField:{'widget': JSONEditorWidget}
    # }

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at')
    search_fields = ('user__email', 'role__name')

@admin.register(DataConsent)
class DataConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'granted_at', 'revoked_at')
    search_fields = ('user__email', 'consent_type')

@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'joined_at')
    list_filter = ('organization', 'joined_at')
    search_fields = ('user__email', 'organization__name')
    raw_id_fields = ('user', 'organization')

