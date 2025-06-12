from django.contrib import admin
from .models import Vehicle, VehicleOwnership, VehicleHistory, VehicleStatus
# Register your models here.


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vin', 'make', 'model', 'manufacture_year')
    search_fields = ('vin', 'make', 'model')
    list_filter = ('fuel_type', 'transmission_type')

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