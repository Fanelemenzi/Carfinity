from django.contrib import admin
from django import forms
from .models import MaintenanceRecord, PartUsage, Inspection, Inspections

class MaintenanceRecordAdminForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = '__all__'
        widgets = {
            'image_description': forms.TextInput(attrs={
                'placeholder': 'Brief description of what the image shows (optional)',
                'size': 60
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image fields clearly optional in the form
        if 'service_image' in self.fields:
            self.fields['service_image'].help_text = "Optional: Upload an image to document the service work"
        if 'image_type' in self.fields:
            self.fields['image_type'].help_text = "Optional: Select what type of image this is"
        if 'image_description' in self.fields:
            self.fields['image_description'].help_text = "Optional: Brief description of the image"

class PartUsageInline(admin.TabularInline):
    model = PartUsage
    extra = 1
    autocomplete_fields = ['part']
    fields = ('part', 'quantity', 'unit_cost', 'total_cost')
    readonly_fields = ('total_cost',)

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    form = MaintenanceRecordAdminForm
    list_display = ('vehicle', 'date_performed', 'technician', 'mileage', 'work_summary', 'has_image_display', 'image_details')
    list_filter = ('date_performed', 'technician', 'image_type')
    search_fields = ('vehicle__VIN', 'work_done')
    autocomplete_fields = ['vehicle', 'technician', 'scheduled_maintenance']
    inlines = [PartUsageInline]
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Service Information', {
            'fields': (
                ('vehicle', 'technician'),
                ('scheduled_maintenance', 'mileage'),
                'date_performed',
                'work_done',
                'notes'
            )
        }),
        ('Service Documentation (Optional)', {
            'fields': (
                'service_image',
                'image_preview',
                ('image_type', 'image_description'),
            ),
            'classes': ('collapse',),
            'description': 'Upload an image to document the service work performed. All fields in this section are optional.'
        }),
    )
    
    def work_summary(self, obj):
        return obj.work_done[:50] + '...' if len(obj.work_done) > 50 else obj.work_done
    work_summary.short_description = "Work Summary"
    
    def has_image_display(self, obj):
        return obj.has_service_image
    has_image_display.short_description = "Has Service Image"
    has_image_display.boolean = True
    
    def image_details(self, obj):
        if obj.has_service_image:
            return f"✓ {obj.image_type_display}" if obj.image_type else "✓ Image Available"
        return "No Image"
    image_details.short_description = "Image Details"
    
    def image_preview(self, obj):
        if obj.service_image:
            return f'<img src="{obj.service_image.url}" style="max-height: 100px; max-width: 150px;" />'
        return "No image"
    image_preview.short_description = "Image Preview"
    image_preview.allow_tags = True

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('inspection_number', 'vehicle_vin', 'inspection_date', 'inspection_result', 'vehicle_health_index', 'has_pdf_display', 'pdf_size_display')
    list_filter = ('inspection_date', 'inspection_result', 'year')
    search_fields = ('vehicle__vin', 'inspection_number', 'vehicle_health_index')
    autocomplete_fields = ['vehicle']
    date_hierarchy = 'inspection_date'
    ordering = ['-inspection_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('vehicle', 'inspection_number'),
                ('inspection_date', 'year'),
                ('inspection_result', 'vehicle_health_index'),
            )
        }),
        ('External Links & Files', {
            'fields': (
                'link_to_results',
                'inspection_pdf',
            )
        }),
        ('Metadata', {
            'fields': (
                ('pdf_uploaded_at', 'pdf_file_size'),
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('pdf_uploaded_at', 'pdf_file_size', 'created_at', 'updated_at')
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = "Vehicle VIN"
    vehicle_vin.admin_order_field = 'vehicle__vin'
    
    def has_pdf_display(self, obj):
        return obj.has_pdf
    has_pdf_display.short_description = "Has PDF Report"
    has_pdf_display.boolean = True
    
    def pdf_size_display(self, obj):
        if obj.pdf_file_size_mb:
            return f"{obj.pdf_file_size_mb} MB"
        return "-"
    pdf_size_display.short_description = "File Size"
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['pdf_uploaded_at', 'pdf_file_size'])
        return readonly
    
    actions = ['download_selected_pdfs']
    
    def download_selected_pdfs(self, request, queryset):
        """Custom admin action to download multiple PDFs"""
        inspections_with_pdf = queryset.filter(inspection_pdf__isnull=False)
        count = inspections_with_pdf.count()
        
        if count == 0:
            self.message_user(request, "No inspections with PDF files were selected.")
            return
        
        # For now, just show a message. In a real implementation, you might create a ZIP file
        self.message_user(
            request, 
            f"Selected {count} inspection(s) with PDF files. "
            f"Individual downloads available from the inspection detail pages."
        )
    
    download_selected_pdfs.short_description = "Download PDFs for selected inspections"


@admin.register(Inspections)
class InspectionsAdmin(admin.ModelAdmin):
    list_display = ('inspection_number_display', 'vehicle_vin', 'technician', 'inspection_date', 'completion_status', 'completion_percentage_display', 'has_major_issues_display')
    list_filter = ('is_completed', 'inspection_date', 'technician', 'completed_at')
    search_fields = ('inspection__inspection_number', 'inspection__vehicle__vin', 'technician__username')
    autocomplete_fields = ['inspection', 'technician']
    date_hierarchy = 'inspection_date'
    ordering = ['-inspection_date']
    
    fieldsets = (
        ('Inspection Information', {
            'fields': (
                ('inspection', 'technician'),
                ('inspection_date', 'mileage_at_inspection'),
                ('is_completed', 'completed_at'),
            )
        }),
        ('Engine & Powertrain (Points 1-10)', {
            'fields': (
                ('engine_oil_level', 'oil_filter_condition', 'coolant_level'),
                ('drive_belts', 'hoses_condition', 'air_filter'),
                ('cabin_air_filter', 'transmission_fluid', 'engine_mounts'),
                'fluid_leaks',
                'engine_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Electrical & Battery (Points 11-15)', {
            'fields': (
                ('battery_voltage', 'battery_terminals', 'alternator_output'),
                ('starter_motor', 'fuses_relays'),
                'electrical_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Brakes & Suspension (Points 16-22)', {
            'fields': (
                ('brake_pads', 'brake_discs', 'brake_fluid'),
                ('parking_brake', 'shocks_struts', 'suspension_bushings'),
                'wheel_bearings',
                'brakes_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Steering & Tires (Points 23-28)', {
            'fields': (
                ('steering_response', 'steering_fluid', 'tire_tread_depth'),
                ('tire_pressure', 'tire_wear_patterns', 'wheels_rims'),
                'steering_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Exhaust & Emissions (Points 29-31)', {
            'fields': (
                ('exhaust_system', 'catalytic_converter', 'exhaust_warning_lights'),
                'exhaust_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Safety Equipment (Points 32-36)', {
            'fields': (
                ('seat_belts', 'airbags', 'horn_function'),
                ('first_aid_kit', 'warning_triangle'),
                'safety_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Lighting & Visibility (Points 37-44)', {
            'fields': (
                ('headlights', 'brake_lights', 'turn_signals'),
                ('interior_lights', 'windshield', 'wiper_blades'),
                ('rear_defogger', 'mirrors'),
                'lighting_notes',
            ),
            'classes': ('collapse',),
        }),
        ('HVAC & Interior (Points 45-48)', {
            'fields': (
                ('air_conditioning', 'ventilation', 'seat_adjustments'),
                'power_windows',
                'hvac_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Technology & Driver Assist (Points 49-50)', {
            'fields': (
                ('infotainment_system', 'rear_view_camera'),
                'technology_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Summary & Recommendations', {
            'fields': (
                'overall_notes',
                'recommendations',
            ),
        }),
    )
    
    readonly_fields = ('completed_at', 'created_at', 'updated_at')
    
    def inspection_number_display(self, obj):
        return obj.inspection.inspection_number
    inspection_number_display.short_description = "Inspection Number"
    inspection_number_display.admin_order_field = 'inspection__inspection_number'
    
    def vehicle_vin(self, obj):
        return obj.inspection.vehicle.vin
    vehicle_vin.short_description = "Vehicle VIN"
    vehicle_vin.admin_order_field = 'inspection__vehicle__vin'
    
    def completion_status(self, obj):
        if obj.is_completed:
            return f"Completed ({obj.completed_at.strftime('%Y-%m-%d %H:%M') if obj.completed_at else 'Unknown'})"
        return "In Progress"
    completion_status.short_description = "Status"
    
    def completion_percentage_display(self, obj):
        percentage = obj.completion_percentage
        if percentage == 100:
            return f"{percentage}% (Complete)"
        elif percentage >= 75:
            return f"{percentage}% (Nearly Done)"
        elif percentage >= 50:
            return f"{percentage}% (In Progress)"
        else:
            return f"{percentage}% (Started)"
    completion_percentage_display.short_description = "Progress"
    
    def has_major_issues_display(self, obj):
        if obj.has_major_issues:
            failed_count = len(obj.failed_points)
            return f"{failed_count} issue(s) found"
        return "No major issues"
    has_major_issues_display.short_description = "Issues"
    
    actions = ['mark_as_completed', 'generate_inspection_report']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected inspections as completed"""
        updated = 0
        for inspection in queryset:
            if not inspection.is_completed:
                inspection.is_completed = True
                inspection.save()
                updated += 1
        
        self.message_user(
            request,
            f"Successfully marked {updated} inspection(s) as completed."
        )
    mark_as_completed.short_description = "Mark selected inspections as completed"
    
    def generate_inspection_report(self, request, queryset):
        """Generate inspection reports for selected inspections"""
        completed_inspections = queryset.filter(is_completed=True)
        count = completed_inspections.count()
        
        if count == 0:
            self.message_user(request, "No completed inspections were selected.")
            return
        
        # For now, just show a message. In a real implementation, you might generate PDF reports
        self.message_user(
            request,
            f"Report generation initiated for {count} completed inspection(s). "
            f"Reports will be available shortly."
        )
    generate_inspection_report.short_description = "Generate reports for selected inspections"
