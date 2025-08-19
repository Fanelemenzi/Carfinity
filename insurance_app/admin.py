from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    InsurancePolicy, Vehicle, MaintenanceSchedule, MaintenanceCompliance,
    Accident, VehicleConditionScore, RiskAlert, RiskAssessmentMetrics
)

# Inline admin classes
class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 0
    readonly_fields = ['risk_score', 'vehicle_health_index', 'created_at']
    fields = ['vehicle', 'current_condition', 'risk_score', 'vehicle_health_index', 'last_inspection_date']

class MaintenanceScheduleInline(admin.TabularInline):
    model = MaintenanceSchedule
    extra = 0
    readonly_fields = ['created_at']
    fields = ['maintenance_type', 'priority_level', 'scheduled_date', 'is_completed', 'cost']

class AccidentInline(admin.TabularInline):
    model = Accident
    extra = 0
    readonly_fields = ['created_at']
    fields = ['accident_date', 'severity', 'claim_amount', 'maintenance_related']

class RiskAlertInline(admin.TabularInline):
    model = RiskAlert
    extra = 0
    readonly_fields = ['created_at']
    fields = ['alert_type', 'severity', 'title', 'is_resolved']

@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_number', 'policy_holder', 'status', 'start_date', 'end_date', 'premium_amount', 'vehicle_count']
    list_filter = ['status', 'start_date', 'end_date', 'created_at']
    search_fields = ['policy_number', 'policy_holder__username', 'policy_holder__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    inlines = [VehicleInline]
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('policy_number', 'policy_holder', 'status')
        }),
        ('Coverage Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Financial', {
            'fields': ('premium_amount',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def vehicle_count(self, obj):
        count = obj.vehicles.count()
        if count > 0:
            url = reverse('admin:insurance_app_vehicle_changelist') + f'?policy__id__exact={obj.id}'
            return format_html('<a href="{}">{} vehicles</a>', url, count)
        return '0 vehicles'
    vehicle_count.short_description = 'Vehicles'

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_info', 'policy', 'risk_score', 'vehicle_health_index', 'current_condition', 'last_inspection_date']
    list_filter = ['current_condition', 'policy__status', 'created_at']
    search_fields = ['vehicle__vin', 'vehicle__make', 'vehicle__model', 'policy__policy_number']
    readonly_fields = ['created_at', 'updated_at', 'maintenance_count', 'accident_count', 'alert_count']
    inlines = [MaintenanceScheduleInline, AccidentInline, RiskAlertInline]
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('policy', 'vehicle', 'purchase_date')
        }),
        ('Condition & Risk', {
            'fields': ('current_condition', 'vehicle_health_index', 'risk_score', 'last_inspection_date')
        }),
        ('Statistics', {
            'fields': ('maintenance_count', 'accident_count', 'alert_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def vehicle_info(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.manufacture_year} {obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.vin})"
        return "No vehicle linked"
    vehicle_info.short_description = 'Vehicle'
    
    def maintenance_count(self, obj):
        count = obj.maintenance_schedules.count()
        if count > 0:
            url = reverse('admin:insurance_app_maintenanceschedule_changelist') + f'?vehicle__id__exact={obj.id}'
            return format_html('<a href="{}">{} schedules</a>', url, count)
        return '0 schedules'
    maintenance_count.short_description = 'Maintenance Schedules'
    
    def accident_count(self, obj):
        count = obj.accidents.count()
        if count > 0:
            url = reverse('admin:insurance_app_accident_changelist') + f'?vehicle__id__exact={obj.id}'
            return format_html('<a href="{}">{} accidents</a>', url, count)
        return '0 accidents'
    accident_count.short_description = 'Accidents'
    
    def alert_count(self, obj):
        count = obj.risk_alerts.filter(is_resolved=False).count()
        if count > 0:
            url = reverse('admin:insurance_app_riskalert_changelist') + f'?vehicle__id__exact={obj.id}&is_resolved__exact=0'
            return format_html('<a href="{}" style="color: red;">{} active alerts</a>', url, count)
        return '0 active alerts'
    alert_count.short_description = 'Active Alerts'

@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_info', 'maintenance_type', 'priority_level', 'scheduled_date', 'is_completed', 'is_overdue_display', 'cost']
    list_filter = ['maintenance_type', 'priority_level', 'is_completed', 'scheduled_date', 'created_at']
    search_fields = ['vehicle__vehicle__vin', 'vehicle__vehicle__make', 'vehicle__vehicle__model', 'description']
    readonly_fields = ['created_at', 'is_overdue_display', 'days_overdue_display']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Vehicle & Schedule', {
            'fields': ('vehicle', 'maintenance_type', 'priority_level')
        }),
        ('Schedule Details', {
            'fields': ('scheduled_date', 'due_mileage', 'description')
        }),
        ('Completion', {
            'fields': ('is_completed', 'completed_date', 'cost', 'service_provider')
        }),
        ('Maintenance App Link', {
            'fields': ('scheduled_maintenance',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_overdue_display', 'days_overdue_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def vehicle_info(self, obj):
        if obj.vehicle and obj.vehicle.vehicle:
            return f"{obj.vehicle.vehicle.make} {obj.vehicle.vehicle.model} ({obj.vehicle.vehicle.vin})"
        return "No vehicle"
    vehicle_info.short_description = 'Vehicle'
    
    def is_overdue_display(self, obj):
        if obj.is_overdue():
            return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        return format_html('<span style="color: green;">On Time</span>')
    is_overdue_display.short_description = 'Status'
    
    def days_overdue_display(self, obj):
        days = obj.days_overdue()
        if days > 0:
            return format_html('<span style="color: red;">{} days</span>', days)
        return '0 days'
    days_overdue_display.short_description = 'Days Overdue'

@admin.register(MaintenanceCompliance)
class MaintenanceComplianceAdmin(admin.ModelAdmin):
    list_display = ['vehicle_info', 'overall_compliance_rate', 'critical_maintenance_compliance', 'overdue_count', 'last_calculated']
    list_filter = ['last_calculated']
    search_fields = ['vehicle__vehicle__vin', 'vehicle__vehicle__make', 'vehicle__vehicle__model']
    readonly_fields = ['last_calculated', 'compliance_grade']
    
    fieldsets = (
        ('Vehicle', {
            'fields': ('vehicle',)
        }),
        ('Compliance Metrics', {
            'fields': ('overall_compliance_rate', 'critical_maintenance_compliance', 'compliance_grade')
        }),
        ('Counts', {
            'fields': ('overdue_count', 'completed_on_time_count', 'total_scheduled_count')
        }),
        ('Timestamps', {
            'fields': ('last_calculated',)
        })
    )
    
    def vehicle_info(self, obj):
        if obj.vehicle and obj.vehicle.vehicle:
            return f"{obj.vehicle.vehicle.make} {obj.vehicle.vehicle.model} ({obj.vehicle.vehicle.vin})"
        return "No vehicle"
    vehicle_info.short_description = 'Vehicle'
    
    def compliance_grade(self, obj):
        rate = obj.overall_compliance_rate
        if rate >= 90:
            return format_html('<span style="color: green; font-weight: bold;">Excellent ({}%)</span>', rate)
        elif rate >= 75:
            return format_html('<span style="color: orange; font-weight: bold;">Good ({}%)</span>', rate)
        elif rate >= 60:
            return format_html('<span style="color: red;">Fair ({}%)</span>', rate)
        else:
            return format_html('<span style="color: darkred; font-weight: bold;">Poor ({}%)</span>', rate)
    compliance_grade.short_description = 'Grade'

@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    list_display = ['vehicle_info', 'accident_date', 'severity', 'claim_amount', 'maintenance_related', 'has_vehicle_history']
    list_filter = ['severity', 'maintenance_related', 'accident_date', 'created_at']
    search_fields = ['vehicle__vehicle__vin', 'vehicle__vehicle__make', 'vehicle__vehicle__model', 'description', 'location']
    readonly_fields = ['created_at', 'detailed_info_display']
    date_hierarchy = 'accident_date'
    
    fieldsets = (
        ('Vehicle & Basic Info', {
            'fields': ('vehicle', 'accident_date', 'severity', 'location')
        }),
        ('Financial', {
            'fields': ('claim_amount',)
        }),
        ('Details', {
            'fields': ('description', 'weather_conditions', 'fault_determination')
        }),
        ('Maintenance Correlation', {
            'fields': ('maintenance_related', 'related_maintenance_type', 'days_since_last_maintenance')
        }),
        ('Vehicle History Link', {
            'fields': ('vehicle_history', 'detailed_info_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def vehicle_info(self, obj):
        if obj.vehicle and obj.vehicle.vehicle:
            return f"{obj.vehicle.vehicle.make} {obj.vehicle.vehicle.model} ({obj.vehicle.vehicle.vin})"
        return "No vehicle"
    vehicle_info.short_description = 'Vehicle'
    
    def has_vehicle_history(self, obj):
        if obj.vehicle_history:
            return format_html('<span style="color: green;">✓ Linked</span>')
        return format_html('<span style="color: red;">✗ Not Linked</span>')
    has_vehicle_history.short_description = 'Vehicle History'
    
    def detailed_info_display(self, obj):
        info = obj.get_detailed_accident_info()
        if info:
            details = []
            if info.get('police_report_number'):
                details.append(f"Police Report: {info['police_report_number']}")
            if info.get('insurance_claim_number'):
                details.append(f"Insurance Claim: {info['insurance_claim_number']}")
            if info.get('verified'):
                details.append("✓ Verified")
            return mark_safe('<br>'.join(details)) if details else 'No additional details'
        return 'No vehicle history linked'
    detailed_info_display.short_description = 'Additional Details'

@admin.register(VehicleConditionScore)
class VehicleConditionScoreAdmin(admin.ModelAdmin):
    list_display = ['vehicle_info', 'assessment_date', 'overall_score', 'assessment_type', 'score_breakdown']
    list_filter = ['assessment_type', 'assessment_date', 'created_at']
    search_fields = ['vehicle__vehicle__vin', 'vehicle__vehicle__make', 'vehicle__vehicle__model']
    readonly_fields = ['created_at', 'overall_score', 'score_breakdown']
    date_hierarchy = 'assessment_date'
    
    fieldsets = (
        ('Vehicle & Assessment', {
            'fields': ('vehicle', 'assessment_date', 'assessment_type')
        }),
        ('Component Scores', {
            'fields': ('engine_score', 'transmission_score', 'brake_score', 'tire_score', 'suspension_score', 'electrical_score')
        }),
        ('Overall', {
            'fields': ('overall_score', 'score_breakdown')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def vehicle_info(self, obj):
        if obj.vehicle and obj.vehicle.vehicle:
            return f"{obj.vehicle.vehicle.make} {obj.vehicle.vehicle.model} ({obj.vehicle.vehicle.vin})"
        return "No vehicle"
    vehicle_info.short_description = 'Vehicle'
    
    def score_breakdown(self, obj):
        scores = [
            f"Engine: {obj.engine_score}",
            f"Transmission: {obj.transmission_score}",
            f"Brakes: {obj.brake_score}",
            f"Tires: {obj.tire_score}",
            f"Suspension: {obj.suspension_score}",
            f"Electrical: {obj.electrical_score}"
        ]
        return mark_safe('<br>'.join(scores))
    score_breakdown.short_description = 'Component Breakdown'

@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = ['vehicle_info', 'alert_type', 'severity', 'title', 'is_resolved', 'created_at', 'risk_score_impact']
    list_filter = ['alert_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['vehicle__vehicle__vin', 'vehicle__vehicle__make', 'vehicle__vehicle__model', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'resolved_date']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Vehicle & Alert', {
            'fields': ('vehicle', 'alert_type', 'severity', 'title')
        }),
        ('Details', {
            'fields': ('description', 'risk_score_impact')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_date', 'resolution_notes')
        }),
        ('System Info', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def vehicle_info(self, obj):
        if obj.vehicle and obj.vehicle.vehicle:
            return f"{obj.vehicle.vehicle.make} {obj.vehicle.vehicle.model} ({obj.vehicle.vehicle.vin})"
        return "No vehicle"
    vehicle_info.short_description = 'Vehicle'
    
    actions = ['mark_resolved', 'mark_unresolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_date=timezone.now())
        self.message_user(request, f'{updated} alerts marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False, resolved_date=None)
        self.message_user(request, f'{updated} alerts marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected alerts as unresolved'

@admin.register(RiskAssessmentMetrics)
class RiskAssessmentMetricsAdmin(admin.ModelAdmin):
    list_display = ['policy', 'calculation_date', 'portfolio_compliance_rate', 'avg_vehicle_health_index', 'high_risk_vehicles', 'active_alerts']
    list_filter = ['calculation_date']
    search_fields = ['policy__policy_number', 'policy__policy_holder__username']
    readonly_fields = ['calculation_date', 'metrics_summary']
    date_hierarchy = 'calculation_date'
    
    fieldsets = (
        ('Policy & Date', {
            'fields': ('policy', 'calculation_date')
        }),
        ('Compliance Metrics', {
            'fields': ('portfolio_compliance_rate', 'critical_maintenance_compliance')
        }),
        ('Vehicle Condition', {
            'fields': ('avg_vehicle_health_index', 'vehicles_excellent_condition', 'vehicles_poor_condition')
        }),
        ('Accident Correlation', {
            'fields': ('maintenance_related_accidents', 'total_accidents', 'accident_correlation_rate')
        }),
        ('Risk Assessment', {
            'fields': ('high_risk_vehicles', 'active_alerts', 'resolved_alerts_30d')
        }),
        ('Summary', {
            'fields': ('metrics_summary',),
            'classes': ('collapse',)
        })
    )
    
    def metrics_summary(self, obj):
        summary = [
            f"Portfolio Health: {obj.avg_vehicle_health_index:.1f}/100",
            f"Compliance Rate: {obj.portfolio_compliance_rate:.1f}%",
            f"High Risk Vehicles: {obj.high_risk_vehicles}",
            f"Active Alerts: {obj.active_alerts}",
            f"Accident Correlation: {obj.accident_correlation_rate:.1f}%"
        ]
        return mark_safe('<br>'.join(summary))
    metrics_summary.short_description = 'Metrics Summary'

# Custom admin actions
def calculate_risk_scores(modeladmin, request, queryset):
    """Calculate risk scores for selected vehicles"""
    from django.core.management import call_command
    from io import StringIO
    import sys
    
    # Capture command output
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    
    try:
        for vehicle in queryset:
            call_command('calculate_risk_scores', policy_id=vehicle.policy.id)
        
        output = buffer.getvalue()
        modeladmin.message_user(request, f'Risk scores calculated for {queryset.count()} vehicles. {output}')
    except Exception as e:
        modeladmin.message_user(request, f'Error calculating risk scores: {str(e)}', level='ERROR')
    finally:
        sys.stdout = old_stdout

calculate_risk_scores.short_description = 'Calculate risk scores for selected vehicles'

def update_compliance_scores(modeladmin, request, queryset):
    """Update compliance scores for selected vehicles"""
    from django.core.management import call_command
    
    try:
        call_command('update_compliance_scores')
        modeladmin.message_user(request, f'Compliance scores updated for all vehicles.')
    except Exception as e:
        modeladmin.message_user(request, f'Error updating compliance scores: {str(e)}', level='ERROR')

update_compliance_scores.short_description = 'Update compliance scores'

def sync_maintenance_schedules(modeladmin, request, queryset):
    """Sync maintenance schedules with maintenance app"""
    from django.core.management import call_command
    
    try:
        for vehicle in queryset:
            call_command('sync_maintenance_schedules', vehicle_id=vehicle.id, create_missing=True, update_existing=True)
        
        modeladmin.message_user(request, f'Maintenance schedules synced for {queryset.count()} vehicles.')
    except Exception as e:
        modeladmin.message_user(request, f'Error syncing maintenance schedules: {str(e)}', level='ERROR')

sync_maintenance_schedules.short_description = 'Sync maintenance schedules'

def sync_accident_history(modeladmin, request, queryset):
    """Sync accident history with vehicle history app"""
    from django.core.management import call_command
    
    try:
        for vehicle in queryset:
            call_command('sync_accident_history', vehicle_id=vehicle.id, import_history=True, create_history=True)
        
        modeladmin.message_user(request, f'Accident history synced for {queryset.count()} vehicles.')
    except Exception as e:
        modeladmin.message_user(request, f'Error syncing accident history: {str(e)}', level='ERROR')

sync_accident_history.short_description = 'Sync accident history'

# Add actions to VehicleAdmin
VehicleAdmin.actions = [calculate_risk_scores, update_compliance_scores, sync_maintenance_schedules, sync_accident_history]

# Custom admin views and utilities
class InsuranceAdminMixin:
    """Mixin to add common insurance admin functionality"""
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(self.model, 'vehicle'):
            return qs.select_related('vehicle__vehicle', 'vehicle__policy')
        elif hasattr(self.model, 'policy'):
            return qs.select_related('policy__policy_holder')
        return qs

# Apply mixin to relevant admin classes
MaintenanceScheduleAdmin.__bases__ = (InsuranceAdminMixin,) + MaintenanceScheduleAdmin.__bases__
AccidentAdmin.__bases__ = (InsuranceAdminMixin,) + AccidentAdmin.__bases__
VehicleConditionScoreAdmin.__bases__ = (InsuranceAdminMixin,) + VehicleConditionScoreAdmin.__bases__
RiskAlertAdmin.__bases__ = (InsuranceAdminMixin,) + RiskAlertAdmin.__bases__

# Customize admin site header and title
admin.site.site_header = 'Carfinity Insurance Risk Management'
admin.site.site_title = 'Insurance Admin'
admin.site.index_title = 'Insurance Risk Assessment Administration'

# Add custom CSS for better admin interface
class Media:
    css = {
        'all': ('admin/css/insurance_admin.css',)
    }

# Apply media to admin classes
for admin_class in [InsurancePolicyAdmin, VehicleAdmin, MaintenanceScheduleAdmin, 
                   MaintenanceComplianceAdmin, AccidentAdmin, VehicleConditionScoreAdmin, 
                   RiskAlertAdmin, RiskAssessmentMetricsAdmin]:
    admin_class.Media = Media
