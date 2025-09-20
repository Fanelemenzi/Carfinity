from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils.safestring import mark_safe
from .models import Profile, Role, UserRole, DataConsent, OrganizationUser, AuthenticationGroup
from .services import AuthenticationService, OrganizationService
from organizations.models import Organization
import logging

logger = logging.getLogger(__name__)

# Unregister the default User and Group admins to customize them
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced User admin with group-based authentication features"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 
                   'user_groups_display', 'organization_display', 'dashboard_access_display', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')
    
    # Add custom fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Group & Organization Info', {
            'fields': ('groups_info', 'organization_info', 'dashboard_permissions'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = BaseUserAdmin.readonly_fields + ('groups_info', 'organization_info', 'dashboard_permissions')
    
    actions = ['sync_user_groups', 'check_permissions', 'bulk_add_to_group', 'bulk_remove_from_group']
    
    def user_groups_display(self, obj):
        """Display user's groups with color coding"""
        groups = obj.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No Groups</span>')
        
        group_html = []
        for group in groups:
            color = 'green' if group.name in ['customers', 'insurance_company'] else 'blue'
            group_html.append(f'<span style="color: {color}; font-weight: bold;">{group.name}</span>')
        
        return format_html(', '.join(group_html))
    user_groups_display.short_description = 'Groups'
    
    def organization_display(self, obj):
        """Display user's organization with type"""
        org = OrganizationService.get_user_organization(obj)
        if not org:
            return format_html('<span style="color: red;">No Organization</span>')
        
        org_url = reverse('admin:organizations_organization_change', args=[org.id])
        return format_html(
            '<a href="{}" style="color: blue;">{}</a> <span style="color: gray;">({} - {})</span>',
            org_url, org.name, org.organization_type, org.get_organization_type_display()
        )
    organization_display.short_description = 'Organization'
    
    def dashboard_access_display(self, obj):
        """Display available dashboards for user"""
        permissions = AuthenticationService.get_user_permissions(obj)
        
        if not permissions.available_dashboards:
            return format_html('<span style="color: red;">No Access</span>')
        
        dashboard_html = []
        for dashboard in permissions.available_dashboards:
            color = 'green' if dashboard == permissions.default_dashboard else 'orange'
            dashboard_html.append(f'<span style="color: {color};">{dashboard.title()}</span>')
        
        result = ', '.join(dashboard_html)
        
        if permissions.has_conflicts:
            result += format_html(' <span style="color: red; font-size: 0.8em;">⚠ Conflicts</span>')
        
        return format_html(result)
    dashboard_access_display.short_description = 'Dashboard Access'
    
    def groups_info(self, obj):
        """Detailed group information for readonly field"""
        if not obj.pk:
            return "Save user first to see group information"
        
        groups = obj.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No groups assigned</span>')
        
        info_html = []
        for group in groups:
            # Get group member count
            member_count = group.user_set.count()
            info_html.append(f'<li><strong>{group.name}</strong> ({member_count} members)</li>')
        
        return format_html('<ul>{}</ul>', ''.join(info_html))
    groups_info.short_description = 'Group Details'
    
    def organization_info(self, obj):
        """Detailed organization information for readonly field"""
        if not obj.pk:
            return "Save user first to see organization information"
        
        org = OrganizationService.get_user_organization(obj)
        if not org:
            return format_html('<span style="color: red;">No organization assigned</span>')
        
        role = OrganizationService.get_user_organization_role(obj)
        org_url = reverse('admin:organizations_organization_change', args=[org.id])
        
        return format_html(
            '<p><strong>Organization:</strong> <a href="{}">{}</a></p>'
            '<p><strong>Type:</strong> {} ({})</p>'
            '<p><strong>Role:</strong> {}</p>'
            '<p><strong>Contact:</strong> {}</p>',
            org_url, org.name,
            org.organization_type, org.get_organization_type_display(),
            role or 'Not specified',
            org.contact_email or 'Not specified'
        )
    organization_info.short_description = 'Organization Details'
    
    def dashboard_permissions(self, obj):
        """Detailed dashboard permissions for readonly field"""
        if not obj.pk:
            return "Save user first to see dashboard permissions"
        
        permissions = AuthenticationService.get_user_permissions(obj)
        
        info_html = []
        info_html.append(f'<p><strong>Available Dashboards:</strong> {", ".join(permissions.available_dashboards) or "None"}</p>')
        info_html.append(f'<p><strong>Default Dashboard:</strong> {permissions.default_dashboard or "None"}</p>')
        
        if permissions.has_conflicts:
            info_html.append(f'<p style="color: red;"><strong>Conflicts:</strong> {permissions.conflict_details}</p>')
        
        return format_html(''.join(info_html))
    dashboard_permissions.short_description = 'Dashboard Permissions'
    
    def sync_user_groups(self, request, queryset):
        """Admin action to sync users with their organization groups"""
        synced_count = 0
        for user in queryset:
            org = OrganizationService.get_user_organization(user)
            if org:
                org.add_user_to_groups(user)
                synced_count += 1
        
        self.message_user(request, f'Successfully synced {synced_count} users with their organization groups.')
    sync_user_groups.short_description = 'Sync users with organization groups'
    
    def check_permissions(self, request, queryset):
        """Admin action to check user permissions and log conflicts"""
        checked_count = 0
        conflict_count = 0
        
        for user in queryset:
            permissions = AuthenticationService.get_user_permissions(user)
            checked_count += 1
            
            if permissions.has_conflicts:
                conflict_count += 1
                logger.warning(f"Permission conflict for user {user.username}: {permissions.conflict_details}")
        
        message = f'Checked permissions for {checked_count} users. Found {conflict_count} conflicts.'
        if conflict_count > 0:
            message += ' Check logs for details.'
        
        self.message_user(request, message)
    check_permissions.short_description = 'Check user permissions'
    
    def bulk_add_to_group(self, request, queryset):
        """Admin action to bulk add users to a group"""
        # This would typically open a form to select the group
        # For now, we'll add a message about using the groups field
        self.message_user(request, 'To bulk add users to groups, use the "groups" field in the user edit form or use Django\'s built-in group management.')
    bulk_add_to_group.short_description = 'Bulk add to group (use groups field)'
    
    def bulk_remove_from_group(self, request, queryset):
        """Admin action to bulk remove users from a group"""
        # This would typically open a form to select the group
        # For now, we'll add a message about using the groups field
        self.message_user(request, 'To bulk remove users from groups, use the "groups" field in the user edit form or use Django\'s built-in group management.')
    bulk_remove_from_group.short_description = 'Bulk remove from group (use groups field)'


@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    """Enhanced Group admin with authentication system integration"""
    
    list_display = ('name', 'member_count', 'linked_organizations_display', 'dashboard_access')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    def member_count(self, obj):
        """Display number of users in the group"""
        count = obj.user_set.count()
        if count == 0:
            return format_html('<span style="color: red;">0 members</span>')
        return format_html('<span style="color: green;">{} members</span>', count)
    member_count.short_description = 'Members'
    
    def linked_organizations_display(self, obj):
        """Display organizations linked to this group"""
        try:
            orgs = Organization.objects.filter(linked_groups=obj)
            if not orgs:
                return format_html('<span style="color: gray;">No linked organizations</span>')
            
            org_links = []
            for org in orgs:
                org_url = reverse('admin:organizations_organization_change', args=[org.id])
                org_links.append(f'<a href="{org_url}">{org.name}</a>')
            
            return format_html(', '.join(org_links))
        except Exception:
            return 'N/A'
    linked_organizations_display.short_description = 'Linked Organizations'
    
    def dashboard_access(self, obj):
        """Display which dashboards this group provides access to"""
        dashboard_mapping = {
            'customers': 'Customer Dashboard',
            'insurance_company': 'Insurance Dashboard'
        }
        
        dashboard = dashboard_mapping.get(obj.name)
        if dashboard:
            return format_html('<span style="color: green;">{}</span>', dashboard)
        
        return format_html('<span style="color: gray;">No specific dashboard</span>')
    dashboard_access.short_description = 'Dashboard Access'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'user_groups_display', 'organization_display')
    search_fields = ('user__email', 'user__username', 'city', 'country')
    list_filter = ('country', 'city', 'user__groups')
    raw_id_fields = ('user',)
    
    def user_groups_display(self, obj):
        """Display user's groups"""
        groups = obj.user.groups.all()
        if not groups:
            return 'No Groups'
        return ', '.join([group.name for group in groups])
    user_groups_display.short_description = 'User Groups'
    
    def organization_display(self, obj):
        """Display user's organization"""
        org = OrganizationService.get_user_organization(obj.user)
        return org.name if org else 'No Organization'
    organization_display.short_description = 'Organization'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'user_count')
    search_fields = ('name', 'description')
    
    def user_count(self, obj):
        """Display number of users with this role"""
        count = obj.user_roles.count()
        return format_html('<span style="color: green;">{} users</span>', count)
    user_count.short_description = 'Users'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at', 'user_groups_display', 'organization_display')
    search_fields = ('user__email', 'user__username', 'role__name')
    list_filter = ('role', 'assigned_at', 'user__groups')
    raw_id_fields = ('user',)
    
    def user_groups_display(self, obj):
        """Display user's groups"""
        groups = obj.user.groups.all()
        return ', '.join([group.name for group in groups]) if groups else 'No Groups'
    user_groups_display.short_description = 'User Groups'
    
    def organization_display(self, obj):
        """Display user's organization"""
        org = OrganizationService.get_user_organization(obj.user)
        return org.name if org else 'No Organization'
    organization_display.short_description = 'Organization'


@admin.register(DataConsent)
class DataConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'granted_at', 'revoked_at', 'is_active')
    search_fields = ('user__email', 'user__username', 'consent_type')
    list_filter = ('consent_type', 'granted_at', 'revoked_at')
    raw_id_fields = ('user',)
    
    def is_active(self, obj):
        """Display if consent is currently active"""
        if obj.revoked_at:
            return format_html('<span style="color: red;">Revoked</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_active.short_description = 'Status'


@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'organization_type_display', 'user_groups_display', 
                   'groups_org_compatibility', 'joined_at')
    list_filter = ('organization', 'joined_at', 'organization__organization_type', 'user__groups')
    search_fields = ('user__email', 'user__username', 'organization__name')
    raw_id_fields = ('user', 'organization')
    
    actions = ['sync_with_organization_groups', 'check_group_compatibility']
    
    def organization_type_display(self, obj):
        """Display organization type"""
        return obj.organization.get_organization_type_display()
    organization_type_display.short_description = 'Org Type'
    
    def user_groups_display(self, obj):
        """Display user's groups with color coding"""
        groups = obj.user.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No Groups</span>')
        
        group_html = []
        for group in groups:
            color = 'green' if group.name in ['customers', 'insurance_company'] else 'blue'
            group_html.append(f'<span style="color: {color};">{group.name}</span>')
        
        return format_html(', '.join(group_html))
    user_groups_display.short_description = 'User Groups'
    
    def groups_org_compatibility(self, obj):
        """Check if user's groups are compatible with organization type"""
        compatibility = OrganizationService.check_group_organization_compatibility(obj.user)
        
        if compatibility['is_compatible']:
            return format_html('<span style="color: green;">✓ Compatible</span>')
        else:
            return format_html(
                '<span style="color: red;">⚠ Incompatible</span><br>'
                '<small style="color: gray;">{}</small>',
                compatibility.get('details', 'Unknown issue')
            )
    groups_org_compatibility.short_description = 'Group Compatibility'
    
    def sync_with_organization_groups(self, request, queryset):
        """Admin action to sync users with their organization groups"""
        synced_count = 0
        for org_user in queryset:
            org_user.organization.add_user_to_groups(org_user.user)
            synced_count += 1
        
        self.message_user(request, f'Successfully synced {synced_count} users with their organization groups.')
    sync_with_organization_groups.short_description = 'Sync with organization groups'
    
    def check_group_compatibility(self, request, queryset):
        """Admin action to check group-organization compatibility"""
        checked_count = 0
        incompatible_count = 0
        
        for org_user in queryset:
            compatibility = OrganizationService.check_group_organization_compatibility(org_user.user)
            checked_count += 1
            
            if not compatibility['is_compatible']:
                incompatible_count += 1
                logger.warning(f"Group-organization incompatibility for user {org_user.user.username}: {compatibility.get('details')}")
        
        message = f'Checked {checked_count} user-organization relationships. Found {incompatible_count} incompatibilities.'
        if incompatible_count > 0:
            message += ' Check logs for details.'
        
        self.message_user(request, message)
    check_group_compatibility.short_description = 'Check group compatibility'


@admin.register(AuthenticationGroup)
class AuthenticationGroupAdmin(admin.ModelAdmin):
    """Admin interface for managing authentication group configurations"""
    
    list_display = ('display_name', 'group', 'dashboard_type', 'dashboard_url', 'priority', 
                   'is_active', 'compatible_org_types_display', 'user_count')
    list_filter = ('dashboard_type', 'is_active', 'priority')
    search_fields = ('display_name', 'group__name', 'description')
    ordering = ['-priority', 'display_name']
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('group', 'display_name', 'description', 'is_active')
        }),
        ('Dashboard Configuration', {
            'fields': ('dashboard_type', 'dashboard_url', 'priority')
        }),
        ('Organization Compatibility', {
            'fields': ('compatible_org_types',),
            'description': 'List of organization types that should be automatically assigned to this group. '
                          'Use format: ["insurance", "fleet", "dealership"]'
        }),
    )
    
    actions = ['activate_groups', 'deactivate_groups', 'sync_organization_recommendations']
    
    def compatible_org_types_display(self, obj):
        """Display compatible organization types"""
        if obj.compatible_org_types:
            return ', '.join(obj.compatible_org_types)
        return 'None'
    compatible_org_types_display.short_description = 'Compatible Org Types'
    
    def user_count(self, obj):
        """Display number of users in this group"""
        count = obj.group.user_set.count()
        if count == 0:
            return format_html('<span style="color: red;">0 users</span>')
        return format_html('<span style="color: green;">{} users</span>', count)
    user_count.short_description = 'Users'
    
    def activate_groups(self, request, queryset):
        """Admin action to activate selected authentication groups"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Activated {updated} authentication groups.')
    activate_groups.short_description = 'Activate selected groups'
    
    def deactivate_groups(self, request, queryset):
        """Admin action to deactivate selected authentication groups"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {updated} authentication groups.')
    deactivate_groups.short_description = 'Deactivate selected groups'
    
    def sync_organization_recommendations(self, request, queryset):
        """Admin action to sync organization group recommendations based on auth group configs"""
        from organizations.models import Organization
        
        synced_count = 0
        for auth_group in queryset.filter(is_active=True):
            for org_type in auth_group.compatible_org_types:
                orgs = Organization.objects.filter(organization_type=org_type)
                for org in orgs:
                    if not org.linked_groups.filter(name=auth_group.group.name).exists():
                        org.linked_groups.add(auth_group.group)
                        synced_count += 1
        
        self.message_user(request, f'Synced {synced_count} organization-group links based on compatibility settings.')
    sync_organization_recommendations.short_description = 'Sync organization recommendations'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Log the configuration change
        action = 'updated' if change else 'created'
        logger.info(f"Authentication group configuration {action}: {obj.display_name} -> {obj.dashboard_url}")


# Custom admin site configuration
admin.site.site_header = 'Carfinity Administration'
admin.site.site_title = 'Carfinity Admin'
admin.site.index_title = 'Welcome to Carfinity Administration'

