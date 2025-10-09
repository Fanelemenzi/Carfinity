from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.utils.html import format_html
from organizations.models import Organization, OrganizationUser
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
    """Custom form for VehicleAssessment admin with enhanced organization selection"""
    
    class Meta:
        model = VehicleAssessment
        fields = '__all__'
        widgets = {
            'organization': forms.Select(attrs={
                'class': 'form-control organization-select',
                'style': 'width: 100%; font-size: 16px; padding: 10px; border: 2px solid #007cba;',
                'data-placeholder': '🏢 Select an organization for this assessment...',
                'required': True
            }),
            'assessment_type': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'overall_severity': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'uk_write_off_category': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'agent_status': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'overall_notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Enter overall assessment notes...'
            }),
            'recommendations': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Enter recommendations...'
            }),
            'assessor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter assessor name...'
            }),
            'assessor_certification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter certification details...'
            }),
            'incident_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter incident location...'
            }),
            'weather_conditions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter weather conditions...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the current user from the request (if available)
        request = getattr(self, '_request', None)
        if hasattr(self, '_request') and self._request:
            user = self._request.user
        else:
            # Fallback: try to get user from the instance or use all organizations
            user = None
        
        # Filter organizations based on user permissions
        if user and not user.is_superuser:
            # For non-superusers, show only organizations they belong to
            user_organizations = Organization.objects.filter(
                organization_members__user=user,
                organization_members__is_active=True
            ).distinct()
            self.fields['organization'].queryset = user_organizations
        else:
            # For superusers, show all organizations
            self.fields['organization'].queryset = Organization.objects.all()
        
        # Add help text for organization field
        self.fields['organization'].help_text = (
            "Select the organization this assessment is being conducted for. "
            "Only organizations you are a member of will be shown."
        )
        
        # Make organization field required
        self.fields['organization'].required = True
        
        # Add help text for other important fields
        self.fields['assessment_type'].help_text = "Type of assessment being conducted"
        self.fields['assessor_name'].help_text = "Name of the person conducting the assessment"
        self.fields['vehicle'].help_text = "Vehicle being assessed"
        
        # Set initial values for new assessments
        if not self.instance.pk:  # New assessment
            # Auto-generate assessment ID if not provided
            if not self.instance.assessment_id:
                import uuid
                self.fields['assessment_id'] = forms.CharField(
                    initial=f"ASS-{uuid.uuid4().hex[:8].upper()}",
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'readonly': 'readonly'
                    }),
                    help_text="Auto-generated assessment ID"
                )
            
            # Set default status
            self.fields['status'].initial = 'pending'
            self.fields['agent_status'].initial = 'pending_review'
    
    def clean_organization(self):
        """Validate organization selection"""
        organization = self.cleaned_data.get('organization')
        
        if not organization:
            raise forms.ValidationError("Organization is required for all assessments.")
        
        # Additional validation: check if user has access to this organization
        request = getattr(self, '_request', None)
        if hasattr(self, '_request') and self._request and not self._request.user.is_superuser:
            user = self._request.user
            user_organizations = Organization.objects.filter(
                organization_members__user=user,
                organization_members__is_active=True
            ).distinct()
            
            if organization not in user_organizations:
                raise forms.ValidationError(
                    "You don't have permission to create assessments for this organization."
                )
        
        return organization
    
    def clean(self):
        """Additional form validation"""
        cleaned_data = super().clean()
        
        # Validate that assessment_type and organization are compatible
        assessment_type = cleaned_data.get('assessment_type')
        organization = cleaned_data.get('organization')
        
        if assessment_type == 'insurance_claim' and organization:
            if not organization.is_insurance_provider:
                self.add_error('organization', 
                    "Insurance claim assessments require an insurance provider organization.")
        
        return cleaned_data


@admin.register(VehicleAssessment)
class VehicleAssessmentAdmin(admin.ModelAdmin):
    form = VehicleAssessmentAdminForm
    list_display = [
        'assessment_id', 
        'assessment_type', 
        'organization_display', 
        'status', 
        'vehicle_display', 
        'assessor_name', 
        'assessment_date',
        'agent_status_display'
    ]
    list_filter = [
        'assessment_type', 
        'organization', 
        'status', 
        'agent_status',
        'overall_severity', 
        'assessment_date',
        ('organization__organization_type', admin.ChoicesFieldListFilter),
    ]
    search_fields = [
        'assessment_id', 
        'vehicle__make', 
        'vehicle__model', 
        'vehicle__vin',
        'assessor_name', 
        'organization__name',
        'user__first_name',
        'user__last_name',
        'user__email'
    ]
    readonly_fields = ['assessment_date', 'created_at', 'updated_at']
    list_per_page = 25
    date_hierarchy = 'assessment_date'
    
    fieldsets = (
        ('Organization & Assessment Type', {
            'fields': ('organization', 'assessment_type'),
            'description': '🏢 Select the organization and type of assessment being conducted',
            'classes': ('wide',)
        }),
        ('Basic Information', {
            'fields': ('assessment_id', 'status', 'user', 'vehicle'),
            'description': 'Core assessment information'
        }),
        ('Assessment Details', {
            'fields': ('assessor_name', 'assessor_certification', 'assessment_date', 'completed_date'),
            'description': 'Details about the assessor and timing'
        }),
        ('Agent Review', {
            'fields': ('assigned_agent', 'agent_status', 'agent_notes', 'review_deadline'),
            'description': 'Insurance agent review and approval workflow',
            'classes': ('collapse',)
        }),
        ('Incident Information', {
            'fields': ('incident_location', 'incident_date', 'weather_conditions'),
            'description': 'Context about the incident or assessment circumstances'
        }),
        ('Assessment Results', {
            'fields': ('overall_severity', 'uk_write_off_category', 'south_africa_70_percent_rule'),
            'description': 'Assessment outcomes and classifications'
        }),
        ('Financial Information', {
            'fields': ('estimated_repair_cost', 'vehicle_market_value', 'salvage_value'),
            'description': 'Financial estimates and valuations'
        }),
        ('Notes and Recommendations', {
            'fields': ('overall_notes', 'recommendations'),
            'description': 'Detailed notes and professional recommendations'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'System timestamps and metadata'
        })
    )
    
    actions = ['mark_as_completed', 'assign_to_agent', 'export_selected_assessments', 'change_organization']
    
    def get_form(self, request, obj=None, **kwargs):
        """Pass request to form for user-based filtering"""
        form = super().get_form(request, obj, **kwargs)
        form._request = request
        return form
    
    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on whether this is a new assessment"""
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj is None:  # New assessment
            # Make organization selection more prominent for new assessments
            return (
                ('🏢 ORGANIZATION SELECTION', {
                    'fields': ('organization',),
                    'description': 'REQUIRED: Select the organization this assessment is being conducted for. This determines workflow, permissions, and reporting.',
                    'classes': ('wide', 'extrapretty')
                }),
                ('Assessment Type & Basic Info', {
                    'fields': ('assessment_type', 'assessment_id', 'status', 'user', 'vehicle'),
                    'description': 'Assessment classification and basic information'
                }),
                ('Assessment Details', {
                    'fields': ('assessor_name', 'assessor_certification'),
                    'description': 'Details about the assessor'
                }),
                ('Incident Information', {
                    'fields': ('incident_location', 'incident_date', 'weather_conditions'),
                    'description': 'Context about the incident or assessment circumstances',
                    'classes': ('collapse',)
                }),
            )
        
        return fieldsets
    
    def organization_display(self, obj):
        """Enhanced organization display with type and visual indicator"""
        if obj.organization:
            org_type_colors = {
                'insurance': '#28a745',  # green
                'fleet': '#007bff',      # blue
                'dealership': '#ffc107', # yellow
                'service': '#6c757d',    # gray
                'other': '#6f42c1'       # purple
            }
            color = org_type_colors.get(obj.organization.organization_type, '#6c757d')
            
            # Add insurance provider indicator
            insurance_indicator = ''
            if obj.organization.is_insurance_provider:
                insurance_indicator = ' <span style="color: #28a745;">🛡️</span>'
            
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<span style="display: inline-block; width: 12px; height: 12px; '
                'background-color: {}; border-radius: 50%; margin-right: 8px;"></span>'
                '<strong>{}</strong>{}<br><small style="color: #666;">{}</small>'
                '</div>',
                color,
                obj.organization.name,
                insurance_indicator,
                obj.organization.get_organization_type_display()
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">⚠️ No Organization</span>'
        )
    organization_display.short_description = "🏢 Organization"
    organization_display.admin_order_field = 'organization__name'
    
    def vehicle_display(self, obj):
        """Enhanced vehicle display"""
        if obj.vehicle:
            return f"{obj.vehicle.manufacture_year} {obj.vehicle.make} {obj.vehicle.model}"
        return "No Vehicle"
    vehicle_display.short_description = "Vehicle"
    vehicle_display.admin_order_field = 'vehicle__make'
    
    def agent_status_display(self, obj):
        """Colored agent status display"""
        status_colors = {
            'pending_review': '#fbbf24',  # yellow
            'under_review': '#3b82f6',   # blue
            'approved': '#10b981',       # green
            'rejected': '#ef4444',       # red
            'changes_requested': '#f97316',  # orange
            'on_hold': '#6b7280',        # gray
        }
        color = status_colors.get(obj.agent_status, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_agent_status_display()
        )
    agent_status_display.short_description = "Agent Status"
    agent_status_display.admin_order_field = 'agent_status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('organization', 'vehicle', 'user', 'assigned_agent')
    
    def changelist_view(self, request, extra_context=None):
        """Add organization statistics to the changelist view"""
        extra_context = extra_context or {}
        
        # Get organization statistics
        from django.db.models import Count
        org_stats = Organization.objects.annotate(
            assessment_count=Count('assessments')
        ).order_by('-assessment_count')[:5]
        
        extra_context['organization_stats'] = org_stats
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "organization":
            if not request.user.is_superuser:
                # Filter organizations for non-superusers
                kwargs["queryset"] = Organization.objects.filter(
                    organization_members__user=request.user,
                    organization_members__is_active=True
                ).distinct().select_related()
            else:
                kwargs["queryset"] = Organization.objects.all().select_related()
        
        elif db_field.name == "vehicle":
            # Optimize vehicle queryset with select_related
            kwargs["queryset"] = kwargs.get("queryset", db_field.related_model.objects.all()).select_related()
        
        elif db_field.name == "assigned_agent":
            # Show only users who are insurance agents
            kwargs["queryset"] = User.objects.filter(
                org_organization_users__role__in=['AGENT', 'CLAIMS_ADJUSTER'],
                org_organization_users__is_active=True
            ).distinct().select_related()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Custom save logic"""
        if not change:  # New object
            # Set the user if not already set
            if not obj.user:
                obj.user = request.user
            
            # Auto-generate assessment ID if not provided
            if not obj.assessment_id:
                import uuid
                obj.assessment_id = f"ASS-{uuid.uuid4().hex[:8].upper()}"
            
            # Auto-assign organization if not set
            if not obj.organization:
                user_org = Organization.objects.filter(
                    organization_members__user=request.user,
                    organization_members__is_active=True
                ).first()
                if user_org:
                    obj.organization = user_org
            
            # Auto-assign user as agent if not set
            if not obj.assigned_agent:
                obj.assigned_agent = request.user
        
        super().save_model(request, obj, form, change)
    
    # Custom admin actions
    def mark_as_completed(self, request, queryset):
        """Mark selected assessments as completed"""
        from django.utils import timezone
        updated = queryset.update(
            status='completed',
            completed_date=timezone.now()
        )
        self.message_user(
            request,
            f"{updated} assessment(s) marked as completed."
        )
    mark_as_completed.short_description = "Mark selected assessments as completed"
    
    def assign_to_agent(self, request, queryset):
        """Assign selected assessments to an agent"""
        # This would open a form to select an agent
        # For now, we'll just show a message
        self.message_user(
            request,
            "Agent assignment feature - would open agent selection form."
        )
    assign_to_agent.short_description = "Assign to insurance agent"
    
    def export_selected_assessments(self, request, queryset):
        """Export selected assessments"""
        # This would generate a CSV or Excel export
        self.message_user(
            request,
            f"Export feature - would export {queryset.count()} assessment(s)."
        )
    export_selected_assessments.short_description = "Export selected assessments"
    
    def change_organization(self, request, queryset):
        """Change organization for selected assessments"""
        if request.user.is_superuser:
            self.message_user(
                request,
                f"Organization change feature - would allow changing organization for {queryset.count()} assessment(s)."
            )
        else:
            self.message_user(
                request,
                "Only superusers can change assessment organizations.",
                level='ERROR'
            )
    change_organization.short_description = "Change organization for selected assessments"


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
