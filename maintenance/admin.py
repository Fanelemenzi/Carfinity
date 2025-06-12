from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'recommended_interval_mileage', 'recommended_interval_time')
    search_fields = ('name',)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'part_number', 'cost')
    search_fields = ('name', 'part_number')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('maintenance_record', 'document_type', 'uploaded_at')
    search_fields = ('maintenance_record__vehicle__VIN', 'document_type')
    

class ScheduledMaintenanceInline(admin.TabularInline):
    model = ScheduledMaintenance
    readonly_fields = ('status',)
    extra = 0

@admin.register(AssignedVehiclePlan)
class AssignedVehiclePlanAdmin(admin.ModelAdmin):
    inlines = [ScheduledMaintenanceInline]
    list_display = ('vehicle', 'plan', 'owner', 'is_active')
    list_select_related = ('vehicle', 'plan', 'owner')

@admin.register(ScheduledMaintenance)
class ScheduledMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('task', 'assigned_plan', 'due_date', 'status')
    list_filter = ('status', 'due_date')
    search_fields = ('assigned_plan__vehicle__license_plate',)

class TaskPartRequirementInline(admin.TabularInline):  # or admin.StackedInline
    model = TaskPartRequirement
    extra = 1  # Number of empty forms to display
    fields = ('part', 'quantity', 'notes')  # Customize visible fields
    autocomplete_fields = ['part']  # Enable search for Part model

# Inline for MaintenanceTask (nested with TaskPartRequirement)
class MaintenanceTaskInline(admin.TabularInline):
    model = MaintenanceTask
    extra = 1
    show_change_link = True  # Allows editing tasks in a separate page

# Main Admin for MaintenancePlan
@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle_model', 'is_active')

# Main Admin for MaintenanceTask (with parts requirements)
@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    inlines = [TaskPartRequirementInline]  # Shows parts under tasks
    list_display = ('name', 'plan', 'interval_miles', 'interval_months')
    list_filter = ('plan__vehicle_model',)
    search_fields = ('name', 'plan__name')
