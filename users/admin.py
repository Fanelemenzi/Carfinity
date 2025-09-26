from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.db.models import Count
from .models import Profile, Role, UserRole, DataConsent
from .services import AuthenticationService
import logging

logger = logging.getLogger(__name__)

# Unregister the default User and Group admins to customize them
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced User admin with 3-group authentication system (Staff, AutoCare, AutoAssess)"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 
                   'user_groups_display', 'dashboard_access_display', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')
    
    # Add custom fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Group & Dashboard Info', {
            'fields': ('groups_info', 'dashboard_permissions'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = BaseUserAdmin.readonly_fields + ('groups_info', 'dashboard_permissions')
    
    actions = ['check_permissions', 'assign_to_staff', 'assign_to_autocare', 'assign_to_autoassess']
    
    def user_groups_display(self, obj):
        """Display user's groups with color coding for 3-group system"""
        groups = obj.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No Groups</span>')
        
        group_html = []
        group_colors = {
            'Staff': 'purple',
            'AutoCare': 'blue', 
            'AutoAssess': 'green'
        }
        
        for group in groups:
            color = group_colors.get(group.name, 'gray')
            group_html.append(f'<span style="color: {color}; font-weight: bold;">{group.name}</span>')
        
        return format_html(', '.join(group_html))
    user_groups_display.short_description = 'Groups'
    
    
    def dashboard_access_display(self, obj):
        """Display available dashboards for user in 3-group system"""
        permissions = AuthenticationService.get_user_permissions(obj)
        
        if not permissions.available_dashboards:
            return format_html('<span style="color: red;">No Access</span>')
        
        dashboard_html = []
        dashboard_colors = {
            'Staff': 'purple',
            'AutoCare': 'blue',
            'AutoAssess': 'green'
        }
        
        for dashboard in permissions.available_dashboards:
            color = dashboard_colors.get(dashboard, 'orange')
            is_default = dashboard == permissions.default_dashboard
            style = f'color: {color}; font-weight: {"bold" if is_default else "normal"};'
            dashboard_html.append(f'<span style="{style}">{dashboard}</span>')
        
        return format_html(', '.join(dashboard_html))
    dashboard_access_display.short_description = 'Dashboard Access'
    
    def groups_info(self, obj):
        """Detailed group information for readonly field"""
        if not obj.pk:
            return "Save user first to see group information"
        
        groups = obj.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No groups assigned</span>')
        
        info_html = []
        group_descriptions = {
            'Staff': 'Administrative access to /admin/',
            'AutoCare': 'Vehicle maintenance dashboard access',
            'AutoAssess': 'Vehicle assessment dashboard access'
        }
        
        for group in groups:
            member_count = group.user_set.count()
            description = group_descriptions.get(group.name, 'Unknown group type')
            info_html.append(
                f'<li><strong>{group.name}</strong> - {description} ({member_count} members)</li>'
            )
        
        return format_html('<ul>{}</ul>', ''.join(info_html))
    groups_info.short_description = 'Group Details'
    
    
    def dashboard_permissions(self, obj):
        """Detailed dashboard permissions for readonly field"""
        if not obj.pk:
            return "Save user first to see dashboard permissions"
        
        permissions = AuthenticationService.get_user_permissions(obj)
        
        info_html = []
        info_html.append(f'<p><strong>Available Dashboards:</strong> {", ".join(permissions.available_dashboards) or "None"}</p>')
        info_html.append(f'<p><strong>Default Dashboard:</strong> {permissions.default_dashboard or "None"}</p>')
        info_html.append(f'<p><strong>Groups:</strong> {", ".join(permissions.groups) or "None"}</p>')
        
        return format_html(''.join(info_html))
    dashboard_permissions.short_description = 'Dashboard Permissions'
    
    
    def check_permissions(self, request, queryset):
        """Admin action to check user permissions"""
        checked_count = 0
        no_access_count = 0
        
        for user in queryset:
            permissions = AuthenticationService.get_user_permissions(user)
            checked_count += 1
            
            if not permissions.has_access:
                no_access_count += 1
                logger.warning(f"No dashboard access for user {user.username}: groups={permissions.groups}")
        
        message = f'Checked permissions for {checked_count} users. Found {no_access_count} users without dashboard access.'
        if no_access_count > 0:
            message += ' Check logs for details.'
        
        self.message_user(request, message)
    check_permissions.short_description = 'Check user permissions'
    
    def assign_to_staff(self, request, queryset):
        """Admin action to assign users to Staff group"""
        try:
            staff_group = Group.objects.get(name='Staff')
            count = 0
            for user in queryset:
                user.groups.add(staff_group)
                count += 1
            self.message_user(request, f'Successfully assigned {count} users to Staff group.')
        except Group.DoesNotExist:
            self.message_user(request, 'Staff group does not exist. Run setup_three_groups command first.', level='ERROR')
    assign_to_staff.short_description = 'Assign to Staff group'
    
    def assign_to_autocare(self, request, queryset):
        """Admin action to assign users to AutoCare group"""
        try:
            autocare_group = Group.objects.get(name='AutoCare')
            count = 0
            for user in queryset:
                user.groups.add(autocare_group)
                count += 1
            self.message_user(request, f'Successfully assigned {count} users to AutoCare group.')
        except Group.DoesNotExist:
            self.message_user(request, 'AutoCare group does not exist. Run setup_three_groups command first.', level='ERROR')
    assign_to_autocare.short_description = 'Assign to AutoCare group'
    
    def assign_to_autoassess(self, request, queryset):
        """Admin action to assign users to AutoAssess group"""
        try:
            autoassess_group = Group.objects.get(name='AutoAssess')
            count = 0
            for user in queryset:
                user.groups.add(autoassess_group)
                count += 1
            self.message_user(request, f'Successfully assigned {count} users to AutoAssess group.')
        except Group.DoesNotExist:
            self.message_user(request, 'AutoAssess group does not exist. Run setup_three_groups command first.', level='ERROR')
    assign_to_autoassess.short_description = 'Assign to AutoAssess group'


@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    """Enhanced Group admin for 3-group authentication system"""
    
    list_display = ('name', 'member_count', 'dashboard_access', 'group_description')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    list_filter = ('name',)
    
    def member_count(self, obj):
        """Display number of users in the group"""
        count = obj.user_set.count()
        if count == 0:
            return format_html('<span style="color: red;">0 members</span>')
        return format_html('<span style="color: green;">{} members</span>', count)
    member_count.short_description = 'Members'
    
    
    def dashboard_access(self, obj):
        """Display which dashboards this group provides access to"""
        dashboard_mapping = {
            'Staff': '/admin/ (Administrative Dashboard)',
            'AutoCare': '/dashboard/ (Vehicle Maintenance)',
            'AutoAssess': '/insurance/ (Vehicle Assessment)'
        }
        
        dashboard = dashboard_mapping.get(obj.name)
        if dashboard:
            color = {'Staff': 'purple', 'AutoCare': 'blue', 'AutoAssess': 'green'}.get(obj.name, 'green')
            return format_html('<span style="color: {};">{}</span>', color, dashboard)
        
        return format_html('<span style="color: gray;">No specific dashboard</span>')
    dashboard_access.short_description = 'Dashboard Access'
    
    def group_description(self, obj):
        """Display group description and purpose"""
        descriptions = {
            'Staff': 'Administrative users with full system access',
            'AutoCare': 'Vehicle maintenance technicians and managers',
            'AutoAssess': 'Insurance assessors and claims processors'
        }
        
        description = descriptions.get(obj.name, 'Custom group')
        return format_html('<span style="color: gray; font-style: italic;">{}</span>', description)
    group_description.short_description = 'Description'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'user_groups_display', 'dashboard_access_display')
    search_fields = ('user__email', 'user__username', 'city', 'country')
    list_filter = ('country', 'city', 'user__groups')
    raw_id_fields = ('user',)
    
    def user_groups_display(self, obj):
        """Display user's groups with color coding"""
        groups = obj.user.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No Groups</span>')
        
        group_html = []
        group_colors = {
            'Staff': 'purple',
            'AutoCare': 'blue',
            'AutoAssess': 'green'
        }
        
        for group in groups:
            color = group_colors.get(group.name, 'gray')
            group_html.append(f'<span style="color: {color};">{group.name}</span>')
        
        return format_html(', '.join(group_html))
    user_groups_display.short_description = 'User Groups'
    
    def dashboard_access_display(self, obj):
        """Display user's dashboard access"""
        permissions = AuthenticationService.get_user_permissions(obj.user)
        if not permissions.available_dashboards:
            return format_html('<span style="color: red;">No Access</span>')
        return format_html('<span style="color: green;">{}</span>', ', '.join(permissions.available_dashboards))
    dashboard_access_display.short_description = 'Dashboard Access'


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
    list_display = ('user', 'role', 'assigned_at', 'user_groups_display', 'dashboard_access_display')
    search_fields = ('user__email', 'user__username', 'role__name')
    list_filter = ('role', 'assigned_at', 'user__groups')
    raw_id_fields = ('user',)
    
    def user_groups_display(self, obj):
        """Display user's groups with color coding"""
        groups = obj.user.groups.all()
        if not groups:
            return format_html('<span style="color: red;">No Groups</span>')
        
        group_html = []
        group_colors = {
            'Staff': 'purple',
            'AutoCare': 'blue',
            'AutoAssess': 'green'
        }
        
        for group in groups:
            color = group_colors.get(group.name, 'gray')
            group_html.append(f'<span style="color: {color};">{group.name}</span>')
        
        return format_html(', '.join(group_html))
    user_groups_display.short_description = 'User Groups'
    
    def dashboard_access_display(self, obj):
        """Display user's dashboard access"""
        permissions = AuthenticationService.get_user_permissions(obj.user)
        if not permissions.available_dashboards:
            return format_html('<span style="color: red;">No Access</span>')
        return format_html('<span style="color: green;">{}</span>', ', '.join(permissions.available_dashboards))
    dashboard_access_display.short_description = 'Dashboard Access'


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


# OrganizationUser and AuthenticationGroup admin classes removed
# These are no longer needed in the simplified 3-group authentication system


# Custom admin site configuration
admin.site.site_header = 'Carfinity Administration'
admin.site.site_title = 'Carfinity Admin'
admin.site.index_title = 'Welcome to Carfinity Administration'

