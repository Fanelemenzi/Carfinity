from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Organization, OrganizationUser, OrganizationVehicle, InsuranceOrganization


class OrganizationUserInline(admin.TabularInline):
    """Inline for managing organization members"""
    model = OrganizationUser
    extra = 0
    fields = ('user', 'role', 'is_active', 'joined_at')
    readonly_fields = ('joined_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_type', 'is_insurance_provider', 'linked_groups_display', 
                   'member_count', 'contact_email', 'created_at')
    search_fields = ('name', 'contact_email', 'insurance_license_number')
    list_filter = ('organization_type', 'is_insurance_provider', 'linked_groups', 'created_at')
    filter_horizontal = ('linked_groups',)
    inlines = [OrganizationUserInline]
    
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
            'fields': ('linked_groups', 'group_management_info'),
            'description': 'Select Django groups that members of this organization should automatically join. '
                          'When users join this organization, they will be automatically added to these groups.'
        }),
    )
    
    readonly_fields = ('group_management_info',)
    
    actions = ['sync_members_to_groups', 'create_insurance_details', 'auto_assign_recommended_groups']
    
    def linked_groups_display(self, obj):
        """Display linked groups in list view with color coding"""
        groups = obj.linked_groups.all()
        if not groups:
            return format_html('<span style="color: red;">No Groups</span>')
        
        group_html = []
        for group in groups:
            color = 'green' if group.name in ['customers', 'insurance_company'] else 'blue'
            group_html.append(f'<span style="color: {color}; font-weight: bold;">{group.name}</span>')
        
        return format_html(', '.join(group_html))
    linked_groups_display.short_description = 'Linked Groups'
    
    def member_count(self, obj):
        """Display number of active members"""
        count = obj.organization_members.filter(is_active=True).count()
        if count == 0:
            return format_html('<span style="color: gray;">0 members</span>')
        return format_html('<span style="color: green;">{} members</span>', count)
    member_count.short_description = 'Active Members'
    
    def group_management_info(self, obj):
        """Display detailed group management information"""
        if not obj.pk:
            return "Save organization first to see group management information"
        
        groups = obj.linked_groups.all()
        members = obj.organization_members.filter(is_active=True)
        
        info_html = []
        
        # Show linked groups
        if groups:
            info_html.append('<h4>Linked Groups:</h4>')
            info_html.append('<ul>')
            for group in groups:
                member_count = group.user_set.count()
                dashboard_access = self._get_dashboard_for_group(group.name)
                info_html.append(
                    f'<li><strong>{group.name}</strong> ({member_count} total members) - {dashboard_access}</li>'
                )
            info_html.append('</ul>')
        else:
            info_html.append('<p style="color: red;"><strong>No groups linked!</strong> Members will not have automatic dashboard access.</p>')
        
        # Show recommended groups based on organization type
        recommended = self._get_recommended_groups(obj.organization_type)
        if recommended:
            current_group_names = [g.name for g in groups]
            missing_recommended = [g for g in recommended if g not in current_group_names]
            
            if missing_recommended:
                info_html.append('<h4 style="color: orange;">Recommended Groups (not linked):</h4>')
                info_html.append('<ul>')
                for group_name in missing_recommended:
                    dashboard_access = self._get_dashboard_for_group(group_name)
                    info_html.append(f'<li><strong>{group_name}</strong> - {dashboard_access}</li>')
                info_html.append('</ul>')
        
        # Show member sync status
        if members.exists():
            info_html.append(f'<h4>Member Sync Status:</h4>')
            synced_count = 0
            for member in members:
                user_groups = set(member.user.groups.values_list('name', flat=True))
                org_groups = set(groups.values_list('name', flat=True))
                if org_groups.issubset(user_groups):
                    synced_count += 1
            
            if synced_count == members.count():
                info_html.append(f'<p style="color: green;">✓ All {members.count()} members are synced with linked groups</p>')
            else:
                unsynced = members.count() - synced_count
                info_html.append(f'<p style="color: orange;">⚠ {unsynced} of {members.count()} members need group sync</p>')
                info_html.append('<p><em>Use "Sync members to linked groups" action to fix this.</em></p>')
        
        return format_html(''.join(info_html))
    group_management_info.short_description = 'Group Management Details'
    
    def _get_dashboard_for_group(self, group_name):
        """Get dashboard access description for a group"""
        dashboard_mapping = {
            'customers': 'Customer Dashboard Access',
            'insurance_company': 'Insurance Dashboard Access'
        }
        return dashboard_mapping.get(group_name, 'No specific dashboard access')
    
    def _get_recommended_groups(self, org_type):
        """Get recommended groups based on organization type using configurable system"""
        try:
            from users.models import AuthenticationGroup
            return AuthenticationGroup.get_recommended_groups_for_org_type(org_type)
        except ImportError:
            # Fallback to hardcoded recommendations if AuthenticationGroup not available
            recommendations = {
                'insurance': ['insurance_company'],
                'fleet': ['customers'],
                'dealership': ['customers'],
                'service': ['customers'],
                'other': ['customers']
            }
            return recommendations.get(org_type, [])
    
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
    
    def auto_assign_recommended_groups(self, request, queryset):
        """Admin action to automatically assign recommended groups based on organization type"""
        updated_count = 0
        groups_added = 0
        
        for org in queryset:
            recommended_groups = self._get_recommended_groups(org.organization_type)
            current_groups = set(org.linked_groups.values_list('name', flat=True))
            
            groups_to_add = []
            for group_name in recommended_groups:
                if group_name not in current_groups:
                    try:
                        group = Group.objects.get(name=group_name)
                        groups_to_add.append(group)
                    except Group.DoesNotExist:
                        continue
            
            if groups_to_add:
                for group in groups_to_add:
                    org.linked_groups.add(group)
                    groups_added += 1
                
                # Sync existing members to new groups
                org.sync_all_members_to_groups()
                updated_count += 1
        
        if updated_count > 0:
            self.message_user(
                request, 
                f'Updated {updated_count} organizations with {groups_added} recommended groups and synced members.'
            )
        else:
            self.message_user(request, 'No organizations needed group updates.')
    auto_assign_recommended_groups.short_description = 'Auto-assign recommended groups'
    
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
    list_display = ('user', 'organization', 'role', 'is_active', 'user_groups_display', 
                   'group_sync_status', 'joined_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'organization__name')
    list_filter = ('role', 'is_active', 'organization__organization_type', 
                  'organization__is_insurance_provider', 'organization__linked_groups')
    
    actions = ['sync_users_to_org_groups', 'activate_users', 'deactivate_users']
    
    fieldsets = (
        ('User & Organization', {
            'fields': ('user', 'organization', 'role', 'is_active')
        }),
        ('Group Management Info', {
            'fields': ('group_sync_info',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('group_sync_info',)
    
    def user_groups_display(self, obj):
        """Display user's current groups with color coding"""
        groups = obj.user.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No Groups</span>')
        
        group_html = []
        for group in groups:
            color = 'green' if group.name in ['customers', 'insurance_company'] else 'blue'
            group_html.append(f'<span style="color: {color};">{group.name}</span>')
        
        return format_html(', '.join(group_html))
    user_groups_display.short_description = 'User Groups'
    
    def group_sync_status(self, obj):
        """Show if user's groups are synced with organization's linked groups"""
        if not obj.is_active:
            return format_html('<span style="color: gray;">Inactive</span>')
        
        user_groups = set(obj.user.groups.values_list('name', flat=True))
        org_groups = set(obj.organization.linked_groups.values_list('name', flat=True))
        
        if not org_groups:
            return format_html('<span style="color: orange;">No Org Groups</span>')
        
        if org_groups.issubset(user_groups):
            return format_html('<span style="color: green;">✓ Synced</span>')
        else:
            missing = org_groups - user_groups
            return format_html(
                '<span style="color: red;">⚠ Missing: {}</span>', 
                ', '.join(missing)
            )
    group_sync_status.short_description = 'Group Sync'
    
    def group_sync_info(self, obj):
        """Detailed group sync information"""
        if not obj.pk:
            return "Save user first to see group sync information"
        
        info_html = []
        
        # Organization's linked groups
        org_groups = obj.organization.linked_groups.all()
        if org_groups:
            info_html.append('<h4>Organization\'s Linked Groups:</h4>')
            info_html.append('<ul>')
            for group in org_groups:
                dashboard_access = self._get_dashboard_for_group(group.name)
                info_html.append(f'<li><strong>{group.name}</strong> - {dashboard_access}</li>')
            info_html.append('</ul>')
        else:
            info_html.append('<p style="color: red;">Organization has no linked groups!</p>')
        
        # User's current groups
        user_groups = obj.user.groups.all()
        if user_groups:
            info_html.append('<h4>User\'s Current Groups:</h4>')
            info_html.append('<ul>')
            for group in user_groups:
                is_from_org = group in org_groups
                color = 'green' if is_from_org else 'blue'
                source = '(from organization)' if is_from_org else '(manually assigned)'
                info_html.append(f'<li style="color: {color};"><strong>{group.name}</strong> {source}</li>')
            info_html.append('</ul>')
        else:
            info_html.append('<p style="color: red;">User has no groups!</p>')
        
        # Sync status
        if obj.is_active and org_groups:
            user_group_names = set(user_groups.values_list('name', flat=True))
            org_group_names = set(org_groups.values_list('name', flat=True))
            
            missing = org_group_names - user_group_names
            extra = user_group_names - org_group_names
            
            if not missing and not extra:
                info_html.append('<p style="color: green;"><strong>✓ Perfect sync!</strong></p>')
            else:
                if missing:
                    info_html.append(f'<p style="color: red;"><strong>Missing groups:</strong> {", ".join(missing)}</p>')
                if extra:
                    info_html.append(f'<p style="color: blue;"><strong>Extra groups:</strong> {", ".join(extra)}</p>')
                info_html.append('<p><em>Use "Sync users to org groups" action to fix sync issues.</em></p>')
        
        return format_html(''.join(info_html))
    group_sync_info.short_description = 'Group Sync Details'
    
    def _get_dashboard_for_group(self, group_name):
        """Get dashboard access description for a group"""
        dashboard_mapping = {
            'customers': 'Customer Dashboard Access',
            'insurance_company': 'Insurance Dashboard Access'
        }
        return dashboard_mapping.get(group_name, 'No specific dashboard access')
    
    def sync_users_to_org_groups(self, request, queryset):
        """Admin action to sync selected users to their organization's linked groups"""
        synced_count = 0
        for org_user in queryset.filter(is_active=True):
            org_user.organization.add_user_to_groups(org_user.user)
            synced_count += 1
        
        self.message_user(request, f'Synced {synced_count} users to their organization groups.')
    sync_users_to_org_groups.short_description = 'Sync users to organization groups'
    
    def activate_users(self, request, queryset):
        """Admin action to activate users and sync them to groups"""
        activated_count = 0
        for org_user in queryset.filter(is_active=False):
            org_user.is_active = True
            org_user.save()  # This will trigger group sync
            activated_count += 1
        
        self.message_user(request, f'Activated {activated_count} users and synced them to organization groups.')
    activate_users.short_description = 'Activate users and sync to groups'
    
    def deactivate_users(self, request, queryset):
        """Admin action to deactivate users and remove from org groups"""
        deactivated_count = 0
        for org_user in queryset.filter(is_active=True):
            org_user.is_active = False
            org_user.save()  # This will trigger group removal
            deactivated_count += 1
        
        self.message_user(request, f'Deactivated {deactivated_count} users and removed them from organization groups.')
    deactivate_users.short_description = 'Deactivate users and remove from org groups'
    
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