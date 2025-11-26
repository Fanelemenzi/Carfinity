from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from maintenance.models import ScheduledMaintenance
from .models import (
    InsurancePolicy, Vehicle, MaintenanceSchedule, MaintenanceCompliance,
    Accident, VehicleConditionScore, RiskAlert, RiskAssessmentMetrics,
    # Quote System Models
    DamagedPart, PartQuoteRequest, PartQuote, PartMarketAverage, 
    AssessmentQuoteSummary, QuoteSystemConfiguration, ProviderConfiguration,
    QuoteSystemHealthMetrics, QuoteSystemAuditLog
)

# Inline admin classes
class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 0
    readonly_fields = ['risk_score', 'vehicle_health_index', 'created_at']
    fields = ['vehicle', 'current_condition', 'risk_score', 'vehicle_health_index', 'last_inspection_date']



class AccidentInline(admin.TabularInline):
    model = Accident
    extra = 0
    readonly_fields = ['created_at']
    fields = ['accident_date', 'severity', 'claim_amount', 'maintenance_related']

class MaintenanceScheduleInline(admin.TabularInline):
    model = MaintenanceSchedule
    extra = 0
    readonly_fields = ['created_at', 'is_overdue_display']
    fields = ['maintenance_type', 'priority_level', 'scheduled_date', 'is_completed', 'completed_date', 'is_overdue_display']
    
    def is_overdue_display(self, obj):
        if obj.is_overdue():
            return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        return format_html('<span style="color: green;">On Time</span>')
    is_overdue_display.short_description = 'Status'

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
    list_display = ['vehicle_info', 'maintenance_type', 'priority_level', 'scheduled_date', 'is_completed', 'is_overdue_display', 'linked_maintenance', 'cost']
    list_filter = ['maintenance_type', 'priority_level', 'is_completed', 'scheduled_date', 'created_at', 'scheduled_maintenance__status']
    search_fields = ['vehicle__vehicle__vin', 'vehicle__vehicle__make', 'vehicle__vehicle__model', 'description', 'scheduled_maintenance__task__name']
    readonly_fields = ['created_at', 'is_overdue_display', 'days_overdue_display', 'maintenance_details_display']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Vehicle & Schedule', {
            'fields': ('vehicle', 'maintenance_type', 'priority_level')
        }),
        ('Schedule Details', {
            'fields': ('scheduled_date', 'due_mileage', 'description')
        }),
        ('Maintenance App Link', {
            'fields': ('scheduled_maintenance', 'maintenance_details_display'),
            'description': 'Link to a scheduled maintenance from the maintenance app'
        }),
        ('Completion', {
            'fields': ('is_completed', 'completed_date', 'cost', 'service_provider')
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
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "scheduled_maintenance":
            # Filter scheduled maintenance to show only pending/overdue ones
            kwargs["queryset"] = ScheduledMaintenance.objects.filter(
                status__in=['PENDING', 'OVERDUE']
            ).select_related('task', 'assigned_plan__vehicle')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
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
    
    def linked_maintenance(self, obj):
        if obj.scheduled_maintenance:
            return format_html(
                '<span style="color: green;">✓ {}</span>', 
                obj.scheduled_maintenance.task.name if obj.scheduled_maintenance.task else 'Linked'
            )
        return format_html('<span style="color: red;">✗ Not Linked</span>')
    linked_maintenance.short_description = 'Maintenance Link'
    
    def maintenance_details_display(self, obj):
        details = obj.get_maintenance_details()
        if details:
            info = []
            if details['task_name']:
                info.append(f"Task: {details['task_name']}")
            if details['maintenance_status']:
                info.append(f"Status: {details['maintenance_status']}")
            if details['technician']:
                info.append(f"Technician: {details['technician']}")
            return mark_safe('<br>'.join(info)) if info else 'No details available'
        return 'No maintenance linked'
    maintenance_details_display.short_description = 'Maintenance Details'

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


# ============================================================================
# PARTS-BASED QUOTE SYSTEM ADMIN INTERFACES
# ============================================================================

# Inline admin classes for quote system
class DamagedPartInline(admin.TabularInline):
    model = DamagedPart
    extra = 0
    readonly_fields = ['identified_date', 'estimated_cost_display']
    fields = ['part_name', 'part_category', 'damage_severity', 'estimated_labor_hours', 'estimated_cost_display']
    
    def estimated_cost_display(self, obj):
        if obj.pk:
            cost_range = obj.get_estimated_cost_range()
            return f"£{cost_range['estimated_cost']:.2f}"
        return "Not calculated"
    estimated_cost_display.short_description = 'Est. Cost'

class PartQuoteInline(admin.TabularInline):
    model = PartQuote
    extra = 0
    readonly_fields = ['quote_date', 'total_cost', 'is_valid_display']
    fields = ['provider_type', 'provider_name', 'part_cost', 'labor_cost', 'total_cost', 'is_valid_display']
    
    def is_valid_display(self, obj):
        if obj.pk and obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Expired</span>')
    is_valid_display.short_description = 'Status'

class PartQuoteRequestInline(admin.TabularInline):
    model = PartQuoteRequest
    extra = 0
    readonly_fields = ['request_id', 'request_date', 'status', 'quote_count']
    fields = ['request_id', 'status', 'include_assessor', 'include_dealer', 'include_independent', 'include_network', 'quote_count']
    
    def quote_count(self, obj):
        if obj.pk:
            count = obj.quotes.count()
            return f"{count} quotes"
        return "0 quotes"
    quote_count.short_description = 'Quotes'

# ============================================================================
# QUOTE SYSTEM ADMIN CLASSES
# ============================================================================

@admin.register(DamagedPart)
class DamagedPartAdmin(admin.ModelAdmin):
    list_display = ['part_name', 'assessment_info', 'part_category', 'damage_severity', 'estimated_labor_hours', 'quote_count', 'identified_date']
    list_filter = ['part_category', 'damage_severity', 'section_type', 'requires_replacement', 'identified_date']
    search_fields = ['part_name', 'part_number', 'damage_description', 'assessment__id']
    readonly_fields = ['identified_date', 'quote_count', 'estimated_cost_display', 'market_average_display']
    inlines = [PartQuoteRequestInline, PartQuoteInline]
    
    fieldsets = (
        ('Assessment & Part Info', {
            'fields': ('assessment', 'section_type', 'part_name', 'part_number', 'part_category')
        }),
        ('Damage Details', {
            'fields': ('damage_severity', 'damage_description', 'requires_replacement')
        }),
        ('Labor & Cost', {
            'fields': ('estimated_labor_hours', 'estimated_cost_display', 'market_average_display')
        }),
        ('Images & Notes', {
            'fields': ('damage_images', 'notes')
        }),
        ('Metadata', {
            'fields': ('identified_date',),
            'classes': ('collapse',)
        })
    )
    
    def assessment_info(self, obj):
        if obj.assessment:
            return f"Assessment #{obj.assessment.id}"
        return "No assessment"
    assessment_info.short_description = 'Assessment'
    
    def quote_count(self, obj):
        if obj.pk:
            count = obj.quotes.count()
            if count > 0:
                return format_html('<a href="{}?damaged_part__id__exact={}">{} quotes</a>', 
                                 reverse('admin:insurance_app_partquote_changelist'), obj.id, count)
            return '0 quotes'
        return 'Not saved'
    quote_count.short_description = 'Quotes'
    
    def estimated_cost_display(self, obj):
        if obj.pk:
            try:
                cost_range = obj.get_estimated_cost_range()
                return f"£{cost_range['estimated_cost']:.2f}"
            except:
                return "Not calculated"
        return "Not saved"
    estimated_cost_display.short_description = 'Estimated Cost'
    
    def market_average_display(self, obj):
        if obj.pk:
            try:
                market_avg = obj.market_averages.first()
                if market_avg:
                    return f"£{market_avg.average_total_cost:.2f} (±{market_avg.standard_deviation:.2f})"
                return "No market data"
            except:
                return "Not available"
        return "Not saved"
    market_average_display.short_description = 'Market Average'

@admin.register(PartQuoteRequest)
class PartQuoteRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'damaged_part_info', 'status', 'provider_selection', 'dispatched_by', 'dispatched_at', 'quote_count']
    list_filter = ['status', 'include_assessor', 'include_dealer', 'include_independent', 'include_network', 'request_date', 'expiry_date']
    search_fields = ['request_id', 'damaged_part__part_name', 'assessment__id', 'vehicle_make', 'vehicle_model']
    readonly_fields = ['request_id', 'request_date', 'quote_count', 'is_expired_display', 'days_until_expiry']
    inlines = [PartQuoteInline]
    date_hierarchy = 'request_date'
    
    fieldsets = (
        ('Request Info', {
            'fields': ('request_id', 'damaged_part', 'assessment', 'status')
        }),
        ('Vehicle Context', {
            'fields': ('vehicle_make', 'vehicle_model', 'vehicle_year')
        }),
        ('Provider Selection', {
            'fields': ('include_assessor', 'include_dealer', 'include_independent', 'include_network')
        }),
        ('Timeline', {
            'fields': ('request_date', 'expiry_date', 'is_expired_display', 'days_until_expiry')
        }),
        ('Dispatch Info', {
            'fields': ('dispatched_by', 'dispatched_at')
        }),
        ('Statistics', {
            'fields': ('quote_count',),
            'classes': ('collapse',)
        })
    )
    
    def damaged_part_info(self, obj):
        if obj.damaged_part:
            return f"{obj.damaged_part.part_name} ({obj.damaged_part.damage_severity})"
        return "No part"
    damaged_part_info.short_description = 'Damaged Part'
    
    def provider_selection(self, obj):
        providers = []
        if obj.include_assessor:
            providers.append("Assessor")
        if obj.include_dealer:
            providers.append("Dealer")
        if obj.include_independent:
            providers.append("Independent")
        if obj.include_network:
            providers.append("Network")
        return ", ".join(providers) if providers else "None selected"
    provider_selection.short_description = 'Providers'
    
    def quote_count(self, obj):
        if obj.pk:
            count = obj.quotes.count()
            if count > 0:
                return format_html('<a href="{}?quote_request__id__exact={}">{} quotes</a>', 
                                 reverse('admin:insurance_app_partquote_changelist'), obj.id, count)
            return '0 quotes'
        return 'Not saved'
    quote_count.short_description = 'Quotes'
    
    def is_expired_display(self, obj):
        if obj.pk and obj.is_expired():
            return format_html('<span style="color: red; font-weight: bold;">EXPIRED</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired_display.short_description = 'Status'
    
    def days_until_expiry(self, obj):
        if obj.pk:
            days = obj.days_until_expiry()
            if days < 0:
                return format_html('<span style="color: red;">{} days ago</span>', abs(days))
            elif days <= 1:
                return format_html('<span style="color: orange;">{} days</span>', days)
            else:
                return f"{days} days"
        return "Not saved"
    days_until_expiry.short_description = 'Days Until Expiry'

@admin.register(PartQuote)
class PartQuoteAdmin(admin.ModelAdmin):
    list_display = ['provider_info', 'damaged_part_info', 'total_cost', 'part_type', 'quote_date', 'is_valid_display', 'confidence_score']
    list_filter = ['provider_type', 'part_type', 'quote_date', 'valid_until']
    search_fields = ['provider_name', 'damaged_part__part_name', 'quote_request__request_id']
    readonly_fields = ['quote_date', 'is_valid_display', 'days_until_expiry', 'cost_breakdown_display']
    date_hierarchy = 'quote_date'
    
    fieldsets = (
        ('Provider Info', {
            'fields': ('quote_request', 'damaged_part', 'provider_type', 'provider_name', 'provider_contact')
        }),
        ('Cost Breakdown', {
            'fields': ('part_cost', 'labor_cost', 'paint_cost', 'additional_costs', 'total_cost', 'cost_breakdown_display')
        }),
        ('Part Specifications', {
            'fields': ('part_type',)
        }),
        ('Timeline & Warranty', {
            'fields': ('estimated_delivery_days', 'estimated_completion_days', 'part_warranty_months', 'labor_warranty_months')
        }),
        ('Validity', {
            'fields': ('quote_date', 'valid_until', 'is_valid_display', 'days_until_expiry')
        }),
        ('Quality', {
            'fields': ('confidence_score', 'notes')
        })
    )
    
    def provider_info(self, obj):
        return f"{obj.get_provider_type_display()} - {obj.provider_name}"
    provider_info.short_description = 'Provider'
    
    def damaged_part_info(self, obj):
        if obj.damaged_part:
            return f"{obj.damaged_part.part_name}"
        return "No part"
    damaged_part_info.short_description = 'Part'
    
    def is_valid_display(self, obj):
        if obj.pk and obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Expired</span>')
    is_valid_display.short_description = 'Status'
    
    def days_until_expiry(self, obj):
        if obj.pk:
            days = obj.days_until_expiry()
            if days < 0:
                return format_html('<span style="color: red;">Expired {} days ago</span>', abs(days))
            elif days <= 1:
                return format_html('<span style="color: orange;">Expires in {} days</span>', days)
            else:
                return f"Expires in {days} days"
        return "Not saved"
    days_until_expiry.short_description = 'Expiry'
    
    def cost_breakdown_display(self, obj):
        if obj.pk:
            breakdown = [
                f"Part: £{obj.part_cost:.2f}",
                f"Labor: £{obj.labor_cost:.2f}",
            ]
            if obj.paint_cost > 0:
                breakdown.append(f"Paint: £{obj.paint_cost:.2f}")
            if obj.additional_costs > 0:
                breakdown.append(f"Additional: £{obj.additional_costs:.2f}")
            breakdown.append(f"<strong>Total: £{obj.total_cost:.2f}</strong>")
            return mark_safe('<br>'.join(breakdown))
        return "Not saved"
    cost_breakdown_display.short_description = 'Cost Breakdown'

@admin.register(PartMarketAverage)
class PartMarketAverageAdmin(admin.ModelAdmin):
    list_display = ['damaged_part_info', 'average_total_cost', 'quote_count', 'confidence_level', 'variance_display', 'calculated_date']
    list_filter = ['confidence_level', 'calculated_date']
    search_fields = ['damaged_part__part_name', 'damaged_part__assessment__id']
    readonly_fields = ['calculated_date', 'variance_display', 'outlier_info', 'statistics_display']
    date_hierarchy = 'calculated_date'
    
    fieldsets = (
        ('Part Info', {
            'fields': ('damaged_part',)
        }),
        ('Market Statistics', {
            'fields': ('average_total_cost', 'min_total_cost', 'max_total_cost', 'standard_deviation', 'variance_display')
        }),
        ('Data Quality', {
            'fields': ('quote_count', 'confidence_level', 'outlier_info')
        }),
        ('Detailed Statistics', {
            'fields': ('statistics_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('calculated_date',),
            'classes': ('collapse',)
        })
    )
    
    def damaged_part_info(self, obj):
        if obj.damaged_part:
            return f"{obj.damaged_part.part_name} (Assessment #{obj.damaged_part.assessment.id})"
        return "No part"
    damaged_part_info.short_description = 'Damaged Part'
    
    def variance_display(self, obj):
        if obj.pk and obj.average_total_cost > 0:
            variance_pct = (obj.standard_deviation / obj.average_total_cost) * 100
            if variance_pct <= 10:
                color = "green"
                status = "Low"
            elif variance_pct <= 25:
                color = "orange"
                status = "Medium"
            else:
                color = "red"
                status = "High"
            return format_html('<span style="color: {};">{} ({:.1f}%)</span>', color, status, variance_pct)
        return "Not calculated"
    variance_display.short_description = 'Variance'
    
    def outlier_info(self, obj):
        if obj.pk:
            try:
                outliers = obj.get_outlier_quotes()
                if outliers:
                    return f"{len(outliers)} outlier(s) detected"
                return "No outliers"
            except:
                return "Not available"
        return "Not saved"
    outlier_info.short_description = 'Outliers'
    
    def statistics_display(self, obj):
        if obj.pk:
            stats = [
                f"Average: £{obj.average_total_cost:.2f}",
                f"Range: £{obj.min_total_cost:.2f} - £{obj.max_total_cost:.2f}",
                f"Standard Deviation: £{obj.standard_deviation:.2f}",
                f"Quotes Used: {obj.quote_count}",
                f"Confidence: {obj.confidence_level}%"
            ]
            return mark_safe('<br>'.join(stats))
        return "Not saved"
    statistics_display.short_description = 'Statistics Summary'

@admin.register(AssessmentQuoteSummary)
class AssessmentQuoteSummaryAdmin(admin.ModelAdmin):
    list_display = ['assessment_info', 'total_parts_identified', 'recommended_total', 'status', 'recommendation_status', 'created_date']
    list_filter = ['status', 'created_date']
    search_fields = ['assessment__id']
    readonly_fields = ['created_date', 'last_updated', 'cost_breakdown_display', 'provider_summary_display']
    date_hierarchy = 'created_date'
    
    fieldsets = (
        ('Assessment Info', {
            'fields': ('assessment',)
        }),
        ('Summary Statistics', {
            'fields': ('status', 'total_parts_identified', 'parts_with_quotes', 'total_quote_requests', 'quotes_received')
        }),
        ('Provider Totals', {
            'fields': ('assessor_total', 'dealer_total', 'independent_total', 'network_total')
        }),
        ('Recommendations', {
            'fields': ('market_average_total', 'recommended_total', 'potential_savings', 'recommended_provider_mix', 'recommendation_reasoning')
        }),
        ('Detailed Breakdown', {
            'fields': ('cost_breakdown_display', 'provider_summary_display'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_date', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def assessment_info(self, obj):
        if obj.assessment:
            return f"Assessment #{obj.assessment.id}"
        return "No assessment"
    assessment_info.short_description = 'Assessment'
    
    def recommendation_status(self, obj):
        if obj.recommended_total:
            return format_html('<span style="color: green;">✓ Available</span>')
        return format_html('<span style="color: orange;">Pending</span>')
    recommendation_status.short_description = 'Recommendations'
    
    def cost_breakdown_display(self, obj):
        if obj.pk:
            breakdown = []
            if obj.market_average_total:
                breakdown.append(f"Market Average: £{obj.market_average_total:.2f}")
            if obj.recommended_total:
                breakdown.append(f"Recommended Total: £{obj.recommended_total:.2f}")
            if obj.assessor_total:
                breakdown.append(f"Assessor: £{obj.assessor_total:.2f}")
            if obj.dealer_total:
                breakdown.append(f"Dealer: £{obj.dealer_total:.2f}")
            if obj.independent_total:
                breakdown.append(f"Independent: £{obj.independent_total:.2f}")
            if obj.network_total:
                breakdown.append(f"Network: £{obj.network_total:.2f}")
            if obj.potential_savings:
                breakdown.append(f"<strong>Potential Savings: £{obj.potential_savings:.2f}</strong>")
            return mark_safe('<br>'.join(breakdown)) if breakdown else "No cost data"
        return "Not saved"
    cost_breakdown_display.short_description = 'Cost Breakdown'
    
    def provider_summary_display(self, obj):
        if obj.pk:
            summary = []
            providers = [
                ('Assessor', obj.assessor_total),
                ('Dealer', obj.dealer_total),
                ('Independent', obj.independent_total),
                ('Network', obj.network_total)
            ]
            for name, cost in providers:
                if cost and cost > 0:
                    summary.append(f"{name}: £{cost:.2f}")
            return mark_safe('<br>'.join(summary)) if summary else "No provider quotes"
        return "Not saved"
    provider_summary_display.short_description = 'Provider Summary'

@admin.register(QuoteSystemConfiguration)
class QuoteSystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'default_labor_rate', 'provider_status', 'recommendation_weights', 'updated_by', 'updated_at']
    readonly_fields = ['created_at', 'updated_at', 'recommendation_weights_display', 'provider_status_display']
    
    fieldsets = (
        ('Cost Calculation Settings', {
            'fields': ('default_labor_rate', 'paint_cost_percentage', 'additional_cost_percentage')
        }),
        ('Quote Request Settings', {
            'fields': ('default_quote_expiry_days', 'minimum_quotes_required', 'confidence_threshold')
        }),
        ('Provider Settings', {
            'fields': ('enable_assessor_estimates', 'enable_dealer_quotes', 'enable_independent_quotes', 'enable_network_quotes', 'provider_status_display')
        }),
        ('Recommendation Engine Settings', {
            'fields': ('price_weight', 'quality_weight', 'timeline_weight', 'warranty_weight', 'reliability_weight', 'recommendation_weights_display')
        }),
        ('System Monitoring Settings', {
            'fields': ('enable_performance_logging', 'log_retention_days', 'enable_health_monitoring')
        }),
        ('Metadata', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not QuoteSystemConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the configuration
        return False
    
    def provider_status(self, obj):
        enabled = []
        if obj.enable_assessor_estimates:
            enabled.append("Assessor")
        if obj.enable_dealer_quotes:
            enabled.append("Dealer")
        if obj.enable_independent_quotes:
            enabled.append("Independent")
        if obj.enable_network_quotes:
            enabled.append("Network")
        return f"{len(enabled)}/4 enabled"
    provider_status.short_description = 'Providers'
    
    def recommendation_weights(self, obj):
        return f"P:{obj.price_weight} Q:{obj.quality_weight} T:{obj.timeline_weight}"
    recommendation_weights.short_description = 'Weights (P/Q/T)'
    
    def provider_status_display(self, obj):
        providers = [
            ('Assessor Estimates', obj.enable_assessor_estimates),
            ('Dealer Quotes', obj.enable_dealer_quotes),
            ('Independent Quotes', obj.enable_independent_quotes),
            ('Network Quotes', obj.enable_network_quotes)
        ]
        status_list = []
        for name, enabled in providers:
            status = "✓ Enabled" if enabled else "✗ Disabled"
            color = "green" if enabled else "red"
            status_list.append(f'<span style="color: {color};">{name}: {status}</span>')
        return mark_safe('<br>'.join(status_list))
    provider_status_display.short_description = 'Provider Status'
    
    def recommendation_weights_display(self, obj):
        weights = [
            f"Price: {obj.price_weight} ({float(obj.price_weight)*100:.0f}%)",
            f"Quality: {obj.quality_weight} ({float(obj.quality_weight)*100:.0f}%)",
            f"Timeline: {obj.timeline_weight} ({float(obj.timeline_weight)*100:.0f}%)",
            f"Warranty: {obj.warranty_weight} ({float(obj.warranty_weight)*100:.0f}%)",
            f"Reliability: {obj.reliability_weight} ({float(obj.reliability_weight)*100:.0f}%)"
        ]
        total = float(obj.price_weight + obj.quality_weight + obj.timeline_weight + obj.warranty_weight + obj.reliability_weight)
        weights.append(f"<strong>Total: {total:.2f} (should be 1.00)</strong>")
        return mark_safe('<br>'.join(weights))
    recommendation_weights_display.short_description = 'Weight Breakdown'
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ProviderConfiguration)
class ProviderConfigurationAdmin(admin.ModelAdmin):
    list_display = ['provider_type', 'is_enabled', 'reliability_score', 'average_response_time_hours', 'cost_multiplier', 'api_status']
    list_filter = ['provider_type', 'is_enabled', 'email_enabled']
    readonly_fields = ['created_at', 'updated_at', 'configuration_summary']
    
    fieldsets = (
        ('Provider Info', {
            'fields': ('provider_type', 'is_enabled')
        }),
        ('API Configuration', {
            'fields': ('api_endpoint', 'api_key', 'api_timeout_seconds')
        }),
        ('Email Configuration', {
            'fields': ('email_enabled', 'email_template')
        }),
        ('Performance Settings', {
            'fields': ('max_concurrent_requests', 'retry_attempts', 'retry_delay_seconds')
        }),
        ('Quality Metrics', {
            'fields': ('reliability_score', 'average_response_time_hours', 'cost_multiplier')
        }),
        ('Summary', {
            'fields': ('configuration_summary',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def api_status(self, obj):
        if obj.api_endpoint and obj.api_key:
            return format_html('<span style="color: green;">✓ Configured</span>')
        elif obj.email_enabled:
            return format_html('<span style="color: orange;">Email Only</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Configured</span>')
    api_status.short_description = 'Integration'
    
    def configuration_summary(self, obj):
        summary = [
            f"Provider: {obj.get_provider_type_display()}",
            f"Status: {'Enabled' if obj.is_enabled else 'Disabled'}",
            f"Reliability: {obj.reliability_score}/100",
            f"Response Time: {obj.average_response_time_hours}h",
            f"Cost Multiplier: {obj.cost_multiplier}x"
        ]
        if obj.api_endpoint:
            summary.append(f"API: {obj.api_endpoint}")
        if obj.email_enabled:
            summary.append("Email: Enabled")
        return mark_safe('<br>'.join(summary))
    configuration_summary.short_description = 'Configuration Summary'

@admin.register(QuoteSystemHealthMetrics)
class QuoteSystemHealthMetricsAdmin(admin.ModelAdmin):
    list_display = ['recorded_at', 'system_health_status_display', 'overall_success_rate_display', 'total_quote_requests_24h', 'error_summary']
    list_filter = ['recorded_at']
    readonly_fields = ['recorded_at', 'system_health_status_display', 'overall_success_rate_display', 'provider_performance_display', 'error_summary_display', 'performance_summary_display']
    date_hierarchy = 'recorded_at'
    
    fieldsets = (
        ('Timestamp', {
            'fields': ('recorded_at',)
        }),
        ('Overall Health', {
            'fields': ('system_health_status_display', 'overall_success_rate_display')
        }),
        ('Quote Request Metrics', {
            'fields': ('total_quote_requests_24h', 'successful_quote_requests_24h', 'failed_quote_requests_24h')
        }),
        ('Quote Response Metrics', {
            'fields': ('total_quotes_received_24h', 'average_response_time_hours')
        }),
        ('Provider Performance', {
            'fields': ('assessor_success_rate', 'dealer_success_rate', 'independent_success_rate', 'network_success_rate', 'provider_performance_display')
        }),
        ('System Performance', {
            'fields': ('average_parts_identification_time_seconds', 'average_market_calculation_time_seconds', 'average_recommendation_time_seconds', 'performance_summary_display')
        }),
        ('Error Tracking', {
            'fields': ('api_errors_24h', 'database_errors_24h', 'validation_errors_24h', 'error_summary_display')
        }),
        ('Data Quality', {
            'fields': ('high_confidence_market_averages', 'low_confidence_market_averages', 'outlier_quotes_detected')
        })
    )
    
    def has_add_permission(self, request):
        # These are system-generated metrics
        return False
    
    def has_change_permission(self, request, obj=None):
        # These are read-only metrics
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion for cleanup
        return True
    
    def system_health_status_display(self, obj):
        status = obj.get_system_health_status()
        colors = {
            'excellent': 'green',
            'good': 'blue',
            'fair': 'orange',
            'poor': 'red'
        }
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                         colors.get(status, 'black'), status.upper())
    system_health_status_display.short_description = 'Health Status'
    
    def overall_success_rate_display(self, obj):
        rate = obj.get_overall_success_rate()
        color = 'green' if rate >= 95 else 'orange' if rate >= 80 else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    overall_success_rate_display.short_description = 'Success Rate'
    
    def total_requests_24h(self, obj):
        return f"{obj.total_quote_requests_24h} requests"
    total_requests_24h.short_description = 'Total Requests (24h)'
    
    def error_summary(self, obj):
        total_errors = obj.api_errors_24h + obj.database_errors_24h + obj.validation_errors_24h
        if total_errors == 0:
            return format_html('<span style="color: green;">No errors</span>')
        else:
            return format_html('<span style="color: red;">{} errors</span>', total_errors)
    error_summary.short_description = 'Errors (24h)'
    
    def provider_performance_display(self, obj):
        providers = [
            ('Assessor', obj.assessor_success_rate),
            ('Dealer', obj.dealer_success_rate),
            ('Independent', obj.independent_success_rate),
            ('Network', obj.network_success_rate)
        ]
        performance_list = []
        for name, rate in providers:
            color = 'green' if rate >= 95 else 'orange' if rate >= 80 else 'red'
            performance_list.append(f'<span style="color: {color};">{name}: {rate:.1f}%</span>')
        return mark_safe('<br>'.join(performance_list))
    provider_performance_display.short_description = 'Provider Performance'
    
    def error_summary_display(self, obj):
        errors = [
            f"API Errors: {obj.api_errors_24h}",
            f"Database Errors: {obj.database_errors_24h}",
            f"Validation Errors: {obj.validation_errors_24h}"
        ]
        total = obj.api_errors_24h + obj.database_errors_24h + obj.validation_errors_24h
        errors.append(f"<strong>Total: {total}</strong>")
        return mark_safe('<br>'.join(errors))
    error_summary_display.short_description = 'Error Breakdown'
    
    def performance_summary_display(self, obj):
        performance = [
            f"Parts Identification: {obj.average_parts_identification_time_seconds:.2f}s",
            f"Market Calculation: {obj.average_market_calculation_time_seconds:.2f}s",
            f"Recommendation: {obj.average_recommendation_time_seconds:.2f}s",
            f"Quote Response Time: {obj.average_response_time_hours:.1f}h"
        ]
        return mark_safe('<br>'.join(performance))
    performance_summary_display.short_description = 'Performance Summary'

@admin.register(QuoteSystemAuditLog)
class QuoteSystemAuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'action_type', 'severity', 'user', 'object_info', 'ip_address']
    list_filter = ['action_type', 'severity', 'timestamp']
    search_fields = ['user__username', 'object_id', 'description', 'ip_address']
    readonly_fields = ['timestamp', 'details_display']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Info', {
            'fields': ('timestamp', 'action_type', 'severity')
        }),
        ('User & Session', {
            'fields': ('user', 'session_key', 'ip_address', 'user_agent')
        }),
        ('Object Info', {
            'fields': ('object_type', 'object_id', 'object_repr')
        }),
        ('Details', {
            'fields': ('description', 'additional_data', 'details_display')
        })
    )
    
    def has_add_permission(self, request):
        # These are system-generated logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # These are read-only logs
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion for log cleanup
        return True
    
    def object_info(self, obj):
        if obj.object_type and obj.object_id:
            return f"{obj.object_type} #{obj.object_id}"
        return "System action"
    object_info.short_description = 'Object'
    
    def details_display(self, obj):
        details = []
        if obj.description:
            details.append(f"Description: {obj.description}")
        if obj.additional_data:
            details.append(f"Data: {obj.additional_data}")
        if obj.user_agent:
            details.append(f"User Agent: {obj.user_agent}")
        return mark_safe('<br>'.join(details)) if details else "No additional details"
    details_display.short_description = 'Additional Details'

# Custom admin actions for quote system
def recalculate_market_averages(modeladmin, request, queryset):
    """Recalculate market averages for selected damaged parts"""
    from insurance_app.market_analysis import MarketAverageCalculator
    
    calculator = MarketAverageCalculator()
    updated_count = 0
    
    for damaged_part in queryset:
        try:
            calculator.calculate_market_average(damaged_part)
            updated_count += 1
        except Exception as e:
            modeladmin.message_user(request, f'Error calculating market average for {damaged_part}: {str(e)}', level='ERROR')
    
    if updated_count > 0:
        modeladmin.message_user(request, f'Market averages recalculated for {updated_count} damaged parts.')

recalculate_market_averages.short_description = 'Recalculate market averages'

def generate_recommendations(modeladmin, request, queryset):
    """Generate recommendations for selected assessments"""
    from insurance_app.recommendation_engine import QuoteRecommendationEngine
    
    engine = QuoteRecommendationEngine()
    updated_count = 0
    
    for assessment in queryset:
        try:
            engine.generate_assessment_recommendations(assessment)
            updated_count += 1
        except Exception as e:
            modeladmin.message_user(request, f'Error generating recommendations for {assessment}: {str(e)}', level='ERROR')
    
    if updated_count > 0:
        modeladmin.message_user(request, f'Recommendations generated for {updated_count} assessments.')

generate_recommendations.short_description = 'Generate recommendations'

def expire_old_quotes(modeladmin, request, queryset):
    """Mark expired quotes as invalid"""
    from django.utils import timezone
    
    expired_count = 0
    for quote in queryset:
        if quote.valid_until < timezone.now():
            # Mark as expired (you might want to add an is_expired field)
            expired_count += 1
    
    modeladmin.message_user(request, f'{expired_count} expired quotes processed.')

expire_old_quotes.short_description = 'Process expired quotes'

# Add actions to relevant admin classes
DamagedPartAdmin.actions = [recalculate_market_averages]
PartQuoteAdmin.actions = [expire_old_quotes]

# Update admin site configuration
admin.site.site_header = 'Carfinity Insurance & Quote Management'
admin.site.site_title = 'Insurance & Quote Admin'
admin.site.index_title = 'Insurance Risk Assessment & Parts-Based Quote Administration'
