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
    list_display = ('vehicle', 'inspection_number', 'year', 'carfinity_rating')
    #list_filter = ('inspection_date')
    #search_fields = ('vehicle', 'inspection_number')
