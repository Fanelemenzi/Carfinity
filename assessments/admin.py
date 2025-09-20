from django.contrib import admin
from .models import (
    VehicleAssessment,
    ExteriorBodyDamage,
    WheelsAndTires,
    InteriorDamage,
    MechanicalSystems,
    ElectricalSystems,
    SafetySystems,
    FrameAndStructural,
    FluidSystems,
    DocumentationAndIdentification,
    AssessmentPhoto,
    AssessmentReport
)


@admin.register(VehicleAssessment)
class VehicleAssessmentAdmin(admin.ModelAdmin):
    list_display = ['assessment_id', 'assessment_type', 'status', 'vehicle', 'assessor_name', 'assessment_date']
    list_filter = ['assessment_type', 'status', 'overall_severity', 'assessment_date']
    search_fields = ['assessment_id', 'vehicle__make', 'vehicle__model', 'assessor_name']
    readonly_fields = ['assessment_date', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('assessment_id', 'assessment_type', 'status', 'user', 'vehicle')
        }),
        ('Assessment Details', {
            'fields': ('assessor_name', 'assessor_certification', 'assessment_date', 'completed_date')
        }),
        ('Incident Information', {
            'fields': ('incident_location', 'incident_date', 'weather_conditions')
        }),
        ('Assessment Results', {
            'fields': ('overall_severity', 'uk_write_off_category', 'south_africa_70_percent_rule')
        }),
        ('Financial Information', {
            'fields': ('estimated_repair_cost', 'vehicle_market_value', 'salvage_value')
        }),
        ('Notes and Recommendations', {
            'fields': ('overall_notes', 'recommendations')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ExteriorBodyDamage)
class ExteriorBodyDamageAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'front_bumper', 'hood', 'rear_bumper', 'roof_panel']
    list_filter = ['front_bumper', 'hood', 'rear_bumper']
    search_fields = ['assessment__assessment_id']


@admin.register(WheelsAndTires)
class WheelsAndTiresAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'front_left_tire', 'front_right_tire', 'rear_left_tire', 'rear_right_tire']
    list_filter = ['front_left_tire', 'front_right_tire', 'rear_left_tire', 'rear_right_tire']
    search_fields = ['assessment__assessment_id']


@admin.register(InteriorDamage)
class InteriorDamageAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'driver_seat', 'dashboard', 'steering_wheel', 'windshield']
    list_filter = ['driver_seat', 'dashboard', 'steering_wheel']
    search_fields = ['assessment__assessment_id']


@admin.register(MechanicalSystems)
class MechanicalSystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'engine_block', 'radiator', 'battery', 'brake_lines']
    list_filter = ['engine_block', 'radiator', 'battery']
    search_fields = ['assessment__assessment_id']


@admin.register(ElectricalSystems)
class ElectricalSystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'headlight_function', 'taillight_function', 'air_conditioning', 'power_windows']
    list_filter = ['headlight_function', 'taillight_function', 'air_conditioning']
    search_fields = ['assessment__assessment_id']


@admin.register(SafetySystems)
class SafetySystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'airbag_systems', 'abs_system', 'stability_control', 'emergency_brake']
    list_filter = ['airbag_systems', 'abs_system', 'stability_control']
    search_fields = ['assessment__assessment_id']


@admin.register(FrameAndStructural)
class FrameAndStructuralAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'frame_rails', 'cross_members', 'firewall', 'floor_pans']
    list_filter = ['frame_rails', 'cross_members', 'firewall']
    search_fields = ['assessment__assessment_id']


@admin.register(FluidSystems)
class FluidSystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'engine_oil', 'transmission_fluid', 'brake_fluid', 'coolant']
    list_filter = ['engine_oil', 'transmission_fluid', 'brake_fluid']
    search_fields = ['assessment__assessment_id']


@admin.register(DocumentationAndIdentification)
class DocumentationAndIdentificationAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'vin_plate', 'door_jamb_stickers', 'emissions_stickers', 'maintenance_records']
    list_filter = ['vin_plate', 'door_jamb_stickers', 'emissions_stickers']
    search_fields = ['assessment__assessment_id']


@admin.register(AssessmentPhoto)
class AssessmentPhotoAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'category', 'description', 'taken_at']
    list_filter = ['category', 'taken_at']
    search_fields = ['assessment__assessment_id', 'description']
    readonly_fields = ['taken_at']


@admin.register(AssessmentReport)
class AssessmentReportAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'report_type', 'status', 'title']
    list_filter = ['report_type', 'status']
    search_fields = ['assessment__assessment_id', 'title']
