from django.contrib import admin
from .models import MaintenanceRecord, PartUsage, Inspection

class PartUsageInline(admin.TabularInline):
    model = PartUsage
    extra = 1
    autocomplete_fields = ['part']
    fields = ('part', 'quantity', 'unit_cost', 'total_cost')
    readonly_fields = ('total_cost',)

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date_performed', 'technician', 'mileage', 'work_summary')
    list_filter = ('date_performed', 'technician')
    search_fields = ('vehicle__VIN', 'work_done')
    autocomplete_fields = ['vehicle', 'technician', 'scheduled_maintenance']
    inlines = [PartUsageInline]
    fieldsets = (
        (None, {
            'fields': (
                ('vehicle', 'technician'),
                ('scheduled_maintenance', 'mileage'),
                'date_performed',
                'work_done',
                'notes'
            )
        }),
    )
    
    def work_summary(self, obj):
        return obj.work_done[:50] + '...' if len(obj.work_done) > 50 else obj.work_done
    work_summary.short_description = "Work Summary"

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('inspection_number', 'vehicle_vin', 'inspection_date', 'inspection_result', 'carfinity_rating', 'has_pdf_display', 'pdf_size_display')
    list_filter = ('inspection_date', 'inspection_result', 'year')
    search_fields = ('vehicle__vin', 'inspection_number', 'carfinity_rating')
    autocomplete_fields = ['vehicle']
    date_hierarchy = 'inspection_date'
    ordering = ['-inspection_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('vehicle', 'inspection_number'),
                ('inspection_date', 'year'),
                ('inspection_result', 'carfinity_rating'),
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
        if obj.has_pdf:
            return "✓ Yes"
        return "✗ No"
    has_pdf_display.short_description = "PDF Report"
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
