from django.contrib import admin
from .models import Organization,OrganizationUser, OrganizationVehicle

# Register your models here.
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'created_at')
    search_fields = ('name', 'contact_email')
    list_filter = ('created_at',)

@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active')
    search_fields = ('user__email', 'organization__name')
    list_filter = ('role', 'is_active')

@admin.register(OrganizationVehicle)
class OrganizationVehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'organization', 'assigned_to', 'is_active')
    search_fields = ('vehicle__VIN', 'organization__name')
    list_filter = ('is_active',)