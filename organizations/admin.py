from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import Organization, OrganizationUser, OrganizationVehicle, InsuranceOrganization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_type', 'is_insurance_provider', 'linked_groups_display', 'contact_email', 'created_at')
    search_fields = ('name', 'contact_email', 'insurance_license_number')
    list_filter = ('organization_type', 'is_insurance_provider', 'created_at')
    filter_horizontal = ('linked_groups',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'organization_type', 'contact_email', 'contact_phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Insurance Details', {
            'fields': ('is_insurance_provider', 'insurance_license_number', 'insurance_rating'),
            'classes': ('collapse',)
        }),
        ('Group Management', {
            'fields': ('linked_groups',),
            'description': 'Select Django groups that members of this organization should automatically join'
        }),
    )
    
    actions = ['sync_members_to_groups', 'create_insurance_details']
    
    def linked_groups_display(self, obj):
        """Display linked groups in list view"""
        groups = obj.linked_groups.all()
        if groups:
            group_names = [group.name for group in groups]
            return ', '.join(group_names)
        return 'None'
    linked_groups_display.short_description = 'Linked Groups'
    
    def sync_members_to_groups(self, request, queryset):
        """Admin action to sync all members to linked groups"""
        count = 0
        for org in queryset:
            org.sync_all_members_to_groups()
            count += 1
        
        self.message_user(request, f'Successfully synced members for {count} organizations to their linked groups.')
    sync_members_to_groups.short_description = 'Sync members to linked groups'
    
    def create_insurance_details(self, request, queryset):
        """Admin action to create insurance details for insurance providers"""
        count = 0
        for org in queryset.filter(is_insurance_provider=True):
            insurance_org, created = InsuranceOrganization.objects.get_or_create(organization=org)
            if created:
                count += 1
        
        self.message_user(request, f'Created insurance details for {count} organizations.')
    create_insurance_details.short_description = 'Create insurance details for insurance providers'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Create InsuranceOrganization if this is an insurance provider
        if obj.is_insurance_provider:
            InsuranceOrganization.objects.get_or_create(organization=obj)
    
    def save_related(self, request, form, formsets, change):
        """Called after saving the main object and its related objects"""
        super().save_related(request, form, formsets, change)
        # Sync all members to newly linked groups
        if 'linked_groups' in form.changed_data:
            form.instance.sync_all_members_to_groups()


@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'user_groups_display', 'joined_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'organization__name')
    list_filter = ('role', 'is_active', 'organization__organization_type', 'organization__is_insurance_provider')
    
    def user_groups_display(self, obj):
        """Display user's current groups"""
        groups = obj.user.groups.all()
        if groups:
            group_names = [group.name for group in groups]
            return ', '.join(group_names)
        return 'None'
    user_groups_display.short_description = 'User Groups'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger group management
        if obj.is_active:
            obj.organization.add_user_to_groups(obj.user)


@admin.register(OrganizationVehicle)
class OrganizationVehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'organization', 'assigned_to', 'is_active')
    search_fields = ('vehicle__VIN', 'organization__name')
    list_filter = ('is_active', 'organization__organization_type')


@admin.register(InsuranceOrganization)
class InsuranceOrganizationAdmin(admin.ModelAdmin):
    list_display = ('organization', 'naic_number', 'am_best_rating', 'total_policies', 'total_premium_volume')
    search_fields = ('organization__name', 'naic_number')
    list_filter = ('am_best_rating', 'auto_approve_low_risk', 'send_maintenance_alerts')
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Insurance Details', {
            'fields': ('naic_number', 'am_best_rating', 'states_licensed')
        }),
        ('Business Metrics', {
            'fields': ('total_policies', 'total_premium_volume'),
            'classes': ('collapse',)
        }),
        ('Risk Management', {
            'fields': ('max_risk_score_threshold', 'auto_approve_low_risk', 'require_inspection_threshold')
        }),
        ('Notifications', {
            'fields': ('send_maintenance_alerts', 'send_risk_alerts', 'alert_email'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('total_policies', 'total_premium_volume')
    actions = ['update_business_metrics']
    
    def update_business_metrics(self, request, queryset):
        """Admin action to update business metrics"""
        count = 0
        for insurance_org in queryset:
            insurance_org.update_business_metrics()
            count += 1
        
        self.message_user(request, f'Updated business metrics for {count} insurance organizations.')
    update_business_metrics.short_description = 'Update business metrics'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update_business_metrics()