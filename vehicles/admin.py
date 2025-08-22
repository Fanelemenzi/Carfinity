from django.contrib import admin
from .models import Vehicle, VehicleOwnership, VehicleHistory, VehicleStatus
from django.utils.html import format_html
from django.urls import reverse

# Register your models here.

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'manufacture_year')
    search_fields = ('vin', 'make', 'model')
    list_filter = ('fuel_type', 'transmission_type', 'manufacture_year')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('vin', 'make', 'model', 'manufacture_year', 'body_type')
        }),
        ('Technical Details', {
            'fields': ('engine_code', 'fuel_type', 'transmission_type', 'powertrain_displacement', 'powertrain_power')
        }),
        ('Appearance', {
            'fields': ('interior_color', 'exterior_color')
        }),
        ('Additional Information', {
            'fields': ('purchase_date', 'license_plate', 'plant_location')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )



@admin.register(VehicleOwnership)
class VehicleOwnershipAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'user', 'start_date', 'end_date', 'is_current_owner')
    search_fields = ('vehicle__vin', 'user__email')
    list_filter = ('is_current_owner',)

@admin.register(VehicleHistory)
class VehicleHistoryAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'event_type', 'event_date', 'reported_by', 'verified')
    search_fields = ('vehicle__vin', 'event_type', 'description')
    list_filter = ('event_type', 'verified', 'event_date')

@admin.register(VehicleStatus)
class VehicleStatus(admin.ModelAdmin):
    list_display= ('vehicle', 'accident_history', 'odometer_fraud', 'theft_involvement', 'legal_status', 'owner_history')
    #search_fields = ('vehicle__vin')
    #list_filter = ('vehicle__vin')