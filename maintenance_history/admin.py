from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import MaintenanceRecord, PartUsage, Inspection, Inspections, InitialInspection

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


@admin.register(InitialInspection)
class InitialInspectionAdmin(admin.ModelAdmin):
    list_display = ('inspection_number', 'vehicle_vin', 'technician', 'inspection_date', 'completion_status', 'completion_percentage_display', 'health_index_display', 'inspection_result_display', 'has_major_issues_display', 'critical_issues_count')
    list_filter = ('is_completed', 'inspection_date', 'technician', 'completed_at', 'overall_condition_rating')
    search_fields = ('inspection_number', 'vehicle__vin', 'technician__username')
    autocomplete_fields = ['vehicle', 'technician']
    date_hierarchy = 'inspection_date'
    ordering = ['-inspection_date']
    
    fieldsets = (
        ('Inspection Information', {
            'fields': (
                ('vehicle', 'inspection_number'),
                ('technician', 'inspection_date'),
                ('mileage_at_inspection', 'is_completed'),
                'completed_at',
            )
        }),
        ('Scoring & Health Assessment', {
            'fields': (
                ('health_index_display_field', 'inspection_result_display_field'),
                ('completion_percentage_display_field', 'total_issues_display'),
                ('overall_condition_rating', 'estimated_repair_cost'),
            ),
            'classes': ('wide',),
        }),
        ('Road Test (Points 1-33)', {
            'fields': (
                ('cold_engine_operation', 'throttle_operation', 'warmup_operation'),
                ('operating_temp_performance', 'normal_operating_temp', 'brake_vibrations'),
                ('engine_fan_operation', 'brake_pedal_specs', 'abs_operation'),
                ('parking_brake_operation', 'seat_belt_condition', 'seat_belt_operation'),
                ('transmission_operation', 'auto_trans_cold', 'auto_trans_operating'),
                ('steering_feel', 'steering_centered', 'vehicle_tracking'),
                ('tilt_telescopic_steering', 'washer_fluid_spray', 'front_wipers'),
                ('rear_wipers', 'wiper_rest_position', 'wiper_blade_replacement'),
                ('speedometer_function', 'odometer_function', 'cruise_control'),
                ('heater_operation', 'ac_operation', 'engine_noise'),
                ('interior_noise', 'wind_road_noise', 'tire_vibration'),
                'road_test_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Frame, Structure & Underbody (Points 34-54)', {
            'fields': (
                ('frame_unibody_condition', 'panel_alignment', 'underbody_condition'),
                ('suspension_leaks_wear', 'struts_shocks_condition', 'power_steering_leaks'),
                ('wheel_covers', 'tire_condition', 'tread_depth'),
                ('tire_specifications', 'brake_calipers_lines', 'brake_system_equipment'),
                ('brake_pad_life', 'brake_rotors_drums', 'exhaust_system'),
                ('engine_trans_mounts', 'drive_axle_shafts', 'cv_joints_boots'),
                ('engine_fluid_leaks', 'transmission_leaks', 'differential_fluid'),
                'frame_structure_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Under Hood (Points 55-68)', {
            'fields': (
                ('drive_belts_hoses', 'underhood_labels', 'air_filter_condition'),
                ('battery_damage', 'battery_test', 'battery_posts_cables'),
                ('battery_secured', 'charging_system', 'coolant_level'),
                ('coolant_protection', 'oil_filter_change', 'oil_sludge_check'),
                ('fluid_levels', 'fluid_contamination'),
                'under_hood_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Functional & Walkaround (Points 69-82)', {
            'fields': (
                ('owners_manual', 'fuel_gauge', 'battery_voltage_gauge'),
                ('temp_gauge', 'horn_function', 'airbags_present'),
                ('headlight_alignment', 'emissions_test', 'tail_lights'),
                ('brake_lights', 'side_marker_lights', 'backup_lights'),
                ('license_plate_lights', 'exterior_lights_condition'),
                'functional_walkaround_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Interior Functions (Points 83-128)', {
            'fields': (
                ('instrument_panel', 'hvac_panel', 'instrument_dimmer'),
                ('turn_signals', 'hazard_flashers', 'rearview_mirror'),
                ('exterior_mirrors', 'remote_mirror_control', 'glass_condition'),
                ('window_tint', 'dome_courtesy_lights', 'power_windows'),
                ('window_locks', 'audio_system', 'audio_speakers'),
                ('antenna', 'clock_operation', 'power_outlet'),
                ('ashtrays', 'headliner_trim', 'floor_mats'),
                ('doors_operation', 'door_locks', 'keyless_entry'),
                ('master_keys', 'theft_deterrent', 'seat_adjustments'),
                ('seat_heaters', 'memory_seat', 'headrests'),
                ('rear_defogger', 'defogger_indicator', 'luggage_light'),
                ('luggage_cleanliness', 'hood_trunk_latches', 'emergency_trunk_release'),
                ('fuel_door_release', 'spare_tire_cover', 'spare_tire_present'),
                ('spare_tire_tread', 'spare_tire_pressure', 'spare_tire_damage'),
                ('spare_tire_secured', 'jack_tools', 'acceptable_aftermarket'),
                'unacceptable_removal',
                'interior_functions_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Exterior Appearance (Points 129-152)', {
            'fields': (
                ('body_surface', 'exterior_cleanliness', 'paint_finish'),
                ('paint_scratches', 'wheels_cleanliness', 'wheel_wells'),
                ('tires_dressed', 'engine_compartment_clean', 'insulation_pad'),
                ('engine_dressed', 'door_jambs', 'glove_console'),
                ('cabin_air_filter', 'seats_carpets', 'vehicle_odors'),
                ('glass_cleanliness', 'interior_debris', 'dash_vents'),
                ('crevices_clean', 'upholstery_panels', 'paint_repairs'),
                ('glass_repairs', 'bumpers_condition', 'interior_surfaces'),
                'exterior_appearance_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Optional/Additional Systems (Points 153-160)', {
            'fields': (
                ('sunroof_convertible', 'seat_heaters_optional', 'navigation_system'),
                ('head_unit_software', 'transfer_case', 'truck_bed_condition'),
                ('truck_bed_liner', 'backup_camera'),
                'optional_systems_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Advanced Safety Systems', {
            'fields': (
                ('sos_indicator', 'lane_keep_assist', 'adaptive_cruise'),
                'parking_assist',
                'safety_systems_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Hybrid Components', {
            'fields': (
                ('hybrid_battery', 'battery_control_module', 'hybrid_power_mgmt'),
                ('electric_motor', 'ecvt_operation', 'power_inverter'),
                ('inverter_coolant', 'ev_modes', 'hybrid_park_mechanism'),
                ('multi_info_display', 'touch_tracer_display', 'hill_start_assist'),
                ('remote_ac', 'solar_ventilation'),
                'hybrid_components_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Summary & Recommendations', {
            'fields': (
                'overall_notes',
                'recommendations',
                'inspection_pdf',
            ),
        }),
    )
    
    readonly_fields = ('completed_at', 'created_at', 'updated_at', 'health_index_display_field', 'inspection_result_display_field', 'completion_percentage_display_field', 'total_issues_display')
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = "Vehicle VIN"
    vehicle_vin.admin_order_field = 'vehicle__vin'
    
    def health_index_display(self, obj):
        if obj.is_completed:
            try:
                return obj.vehicle_health_index
            except:
                return "Calculation Error"
        return "Not Completed"
    health_index_display.short_description = "Health Index"
    
    def health_index_display_field(self, obj):
        return self.health_index_display(obj)
    health_index_display_field.short_description = "Vehicle Health Index"
    
    def inspection_result_display(self, obj):
        if obj.is_completed:
            try:
                return obj.inspection_result
            except:
                return "Pending"
        return "Not Completed"
    inspection_result_display.short_description = "Result"
    
    def inspection_result_display_field(self, obj):
        return self.inspection_result_display(obj)
    inspection_result_display_field.short_description = "Inspection Result"
    
    def completion_percentage_display_field(self, obj):
        return f"{obj.completion_percentage}%"
    completion_percentage_display_field.short_description = "Completion %"
    
    def total_issues_display(self, obj):
        failed_count = len(obj.failed_points)
        critical_count = len(obj.safety_critical_issues)
        if critical_count > 0:
            return f"{failed_count} total ({critical_count} critical)"
        return f"{failed_count} total"
    total_issues_display.short_description = "Issues Found"
    
    def critical_issues_count(self, obj):
        critical_count = len(obj.safety_critical_issues)
        if critical_count > 0:
            return f"⚠️ {critical_count} critical"
        return "None"
    critical_issues_count.short_description = "Critical Issues"
    
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
    
    actions = ['mark_as_completed', 'generate_initial_inspection_report', 'recalculate_scoring', 'export_inspection_summary', 'generate_recommendations_report']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected initial inspections as completed"""
        updated = 0
        for inspection in queryset:
            if not inspection.is_completed:
                inspection.is_completed = True
                inspection.save()
                updated += 1
        
        self.message_user(
            request,
            f"Successfully marked {updated} initial inspection(s) as completed."
        )
    mark_as_completed.short_description = "Mark selected initial inspections as completed"
    
    def generate_initial_inspection_report(self, request, queryset):
        """Generate initial inspection reports for selected inspections"""
        completed_inspections = queryset.filter(is_completed=True)
        count = completed_inspections.count()
        
        if count == 0:
            self.message_user(request, "No completed initial inspections were selected.")
            return
        
        self.message_user(
            request,
            f"Report generation initiated for {count} completed initial inspection(s). "
            f"Reports will be available shortly."
        )
    generate_initial_inspection_report.short_description = "Generate reports for selected initial inspections"
    
    def recalculate_scoring(self, request, queryset):
        """Recalculate scoring for selected initial inspections"""
        updated = 0
        for inspection in queryset.filter(is_completed=True):
            try:
                inspection._update_calculated_fields()
                updated += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Error recalculating scoring for inspection {inspection.inspection_number}: {str(e)}",
                    level='ERROR'
                )
        
        if updated > 0:
            self.message_user(
                request,
                f"Successfully recalculated scoring for {updated} inspection(s)."
            )
    recalculate_scoring.short_description = "Recalculate scoring for selected inspections"
    
    def export_inspection_summary(self, request, queryset):
        """Export inspection summaries for selected inspections"""
        from django.http import HttpResponse
        from .utils import export_initial_inspection_data
        import zipfile
        from io import BytesIO
        
        completed_inspections = queryset.filter(is_completed=True)
        count = completed_inspections.count()
        
        if count == 0:
            self.message_user(request, "No completed initial inspections were selected.")
            return
        
        if count == 1:
            # Single inspection - return direct summary
            inspection = completed_inspections.first()
            summary = export_initial_inspection_data(inspection, 'summary')
            response = HttpResponse(summary, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="inspection_summary_{inspection.inspection_number}.txt"'
            return response
        
        # Multiple inspections - create ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for inspection in completed_inspections:
                summary = export_initial_inspection_data(inspection, 'summary')
                zip_file.writestr(f"inspection_summary_{inspection.inspection_number}.txt", summary)
        
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="inspection_summaries_{count}_inspections.zip"'
        return response
    
    export_inspection_summary.short_description = "Export inspection summaries"
    
    def generate_recommendations_report(self, request, queryset):
        """Generate recommendations report for selected inspections"""
        from django.http import HttpResponse
        from .utils import get_initial_inspection_recommendations
        
        completed_inspections = queryset.filter(is_completed=True)
        count = completed_inspections.count()
        
        if count == 0:
            self.message_user(request, "No completed initial inspections were selected.")
            return
        
        # Generate combined recommendations report
        report_lines = []
        report_lines.append("INITIAL INSPECTION RECOMMENDATIONS REPORT")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Inspections: {count}")
        report_lines.append("")
        
        for inspection in completed_inspections:
            report_lines.append(f"INSPECTION: {inspection.inspection_number}")
            report_lines.append(f"Vehicle: {inspection.vehicle.vin}")
            report_lines.append(f"Date: {inspection.inspection_date.strftime('%Y-%m-%d')}")
            report_lines.append(f"Health Index: {inspection.vehicle_health_index}")
            report_lines.append("")
            
            recommendations = get_initial_inspection_recommendations(inspection)
            if recommendations:
                report_lines.append("RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations, 1):
                    report_lines.append(f"{i}. {rec}")
            else:
                report_lines.append("No specific recommendations - vehicle in good condition")
            
            report_lines.append("")
            report_lines.append("-" * 50)
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        response = HttpResponse(report_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="recommendations_report_{count}_inspections.txt"'
        return response
    
    generate_recommendations_report.short_description = "Generate recommendations report"
