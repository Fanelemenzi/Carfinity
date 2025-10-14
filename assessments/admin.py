from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.utils.html import format_html
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


class VehicleAssessmentAdminForm(forms.ModelForm):
    """Simplified form for VehicleAssessment admin"""
    
    class Meta:
        model = VehicleAssessment
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for new assessments
        if not self.instance.pk:
            import uuid
            self.initial['assessment_id'] = f"ASS-{uuid.uuid4().hex[:8].upper()}"
            self.initial['status'] = 'pending'
            self.initial['agent_status'] = 'pending_review'


@admin.register(VehicleAssessment)
class VehicleAssessmentAdmin(admin.ModelAdmin):
    form = VehicleAssessmentAdminForm
    list_display = [
        'assessment_id', 
        'assessment_type', 
        'organization', 
        'status', 
        'vehicle', 
        'assessor_name', 
        'assessment_date'
    ]
    list_filter = [
        'assessment_type', 
        'status', 
        'agent_status',
        'overall_severity', 
        'assessment_date'
    ]
    search_fields = [
        'assessment_id', 
        'assessor_name'
    ]
    readonly_fields = ['assessment_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('assessment_id', 'assessment_type', 'status', 'user', 'vehicle', 'organization')
        }),
        ('Assessment Details', {
            'fields': ('assessor_name', 'assessor_certification', 'assessment_date', 'completed_date')
        }),
        ('Agent Review', {
            'fields': ('assigned_agent', 'agent_status', 'agent_notes', 'review_deadline'),
            'classes': ('collapse',)
        }),
        ('Incident Information', {
            'fields': ('incident_location', 'incident_date', 'weather_conditions'),
            'classes': ('collapse',)
        }),
        ('Assessment Results', {
            'fields': ('overall_severity', 'uk_write_off_category', 'south_africa_70_percent_rule')
        }),
        ('Financial Information', {
            'fields': ('estimated_repair_cost', 'vehicle_market_value', 'salvage_value'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('overall_notes', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set user and generate ID for new assessments"""
        if not change:  # New object
            if not obj.user:
                obj.user = request.user
            if not obj.assessment_id:
                import uuid
                obj.assessment_id = f"ASS-{uuid.uuid4().hex[:8].upper()}"
        super().save_model(request, obj, form, change)


# Simplified admin classes for assessment components
@admin.register(ExteriorBodyDamage)
class ExteriorBodyDamageAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'front_bumper', 'hood', 'rear_bumper']
    list_filter = ['front_bumper', 'hood', 'rear_bumper']


@admin.register(WheelsAndTires)
class WheelsAndTiresAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'front_left_tire', 'front_right_tire', 'rear_left_tire', 'rear_right_tire']
    list_filter = ['front_left_tire', 'front_right_tire']


@admin.register(InteriorDamage)
class InteriorDamageAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'driver_seat', 'dashboard', 'steering_wheel']
    list_filter = ['driver_seat', 'dashboard']


@admin.register(MechanicalSystems)
class MechanicalSystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'engine_block', 'radiator', 'battery']
    list_filter = ['engine_block', 'radiator']


@admin.register(ElectricalSystems)
class ElectricalSystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'headlight_function', 'taillight_function', 'air_conditioning']
    list_filter = ['headlight_function', 'taillight_function']


@admin.register(SafetySystems)
class SafetySystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'airbag_systems', 'abs_system', 'stability_control']
    list_filter = ['airbag_systems', 'abs_system']


@admin.register(FrameAndStructural)
class FrameAndStructuralAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'frame_rails', 'cross_members', 'firewall']
    list_filter = ['frame_rails', 'cross_members']


@admin.register(FluidSystems)
class FluidSystemsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'engine_oil', 'transmission_fluid', 'brake_fluid']
    list_filter = ['engine_oil', 'transmission_fluid']


@admin.register(DocumentationAndIdentification)
class DocumentationAndIdentificationAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'vin_plate', 'door_jamb_stickers']
    list_filter = ['vin_plate', 'door_jamb_stickers']


@admin.register(AssessmentPhoto)
class AssessmentPhotoAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'category', 'description', 'taken_at']
    list_filter = ['category']
    readonly_fields = ['taken_at']


@admin.register(AssessmentReport)
class AssessmentReportAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'report_type', 'status', 'title']
    list_filter = ['report_type', 'status']
