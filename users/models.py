from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, Group
import datetime
from django.db.models import JSONField
import json

# Create your models here.

class Profile(models.Model):
     # One-to-One relationship with the User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Optional fields
    address = models.CharField(max_length=255, blank=True, null=True, help_text="User's address.")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="User's city.")
    state = models.CharField(max_length=100, blank=True, null=True, help_text="User's state.")
    country = models.CharField(max_length=100, blank=True, null=True, help_text="User's country.")
    postal_code = models.CharField(max_length=20, blank=True, null=True, help_text="User's postal code.")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, help_text="URL or file path to the user's profile picture.")
    date_of_birth = models.DateField(blank=True, null=True, help_text="User's date of birth.")
    preferred_language = models.CharField(max_length=10, blank=True, null=True, default='en', help_text="User's preferred language (e.g., 'en', 'es').")

    def __str__(self):
        return f"Profile of {self.user.email}"

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

class Role(models.Model):
    # Name of the role (e.g., "Admin", "Fleet Manager")
    name = models.CharField(max_length=100, unique=True, help_text="Name of the role (e.g., 'Admin', 'Fleet Manager').")
    # Description of the role (optional)
    description = models.TextField(blank=True, null=True, help_text="Description of the role.")
    # JSON field to store role-specific permissions (optional)
    permissions = models.JSONField(default=dict, blank=True, null=True, help_text="JSON field to store role-specific permissions.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

class UserRole(models.Model):
    # ForeignKey to the User model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')

    # ForeignKey to the Role model
    role = models.ForeignKey('Role', on_delete=models.CASCADE, related_name='user_roles')

    # Timestamp when the role was assigned
    assigned_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the role was assigned.")

    def __str__(self):
        return f"{self.user.email} - {self.role.name}"

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        unique_together = ('user', 'role')  # Ensure a user can't have the same role assigned multiple times

class DataConsent(models.Model):

    CONSENT_TYPES = [
        ('PRIVACY', 'Privacy Policy'),
        ('EMAIL', 'Email Notifications'),
        ('DATA', 'Data Collection'),
        ('DATA_ANALYTICS', 'Data Usage Analytics and Service Improvement')
    ]

    # ForeignKey to the User model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_consents')
    # Type of consent (e.g., "privacy_policy", "email_notifications")
    consent_type = models.CharField(max_length=100, choices=CONSENT_TYPES, help_text="Type of consent (e.g., 'privacy_policy', 'email_notifications').")
    # Timestamp when the consent was granted
    granted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the consent was granted.")
    # Timestamp when the consent was revoked (optional)
    revoked_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the consent was revoked.")

    def __str__(self):
        return f"{self.user.email} - {self.consent_type}"

    class Meta:
        verbose_name = "Data Consent"
        verbose_name_plural = "Data Consents"
        unique_together = ('user', 'consent_type')  # Ensure a user can't have duplicate consent types


class OrganizationUser(models.Model):
    # ForeignKey to the User model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_organization_users')
    # ForeignKey to the Organization model (assuming it exists in an organizations app)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='organization_users')
    # Timestamp when the user joined the organization
    joined_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the user joined the organization.")
    left_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.organization.name}"

    class Meta:
        verbose_name = "Organization User"
        verbose_name_plural = "Organization Users"
        unique_together = ('user', 'organization')  # Ensure a user can't join the same organization multiple times


class AuthenticationGroup(models.Model):
    """
    Model to configure which Django groups are used for authentication and dashboard access.
    This allows administrators to dynamically configure authentication groups without code changes.
    """
    
    DASHBOARD_CHOICES = [
        ('customer', 'Customer Dashboard'),
        ('insurance', 'Insurance Dashboard'),
        ('admin', 'Admin Dashboard'),
        ('technician', 'Technician Dashboard'),
        ('custom', 'Custom Dashboard'),
    ]
    
    # Link to Django Group
    group = models.OneToOneField(
        Group, 
        on_delete=models.CASCADE, 
        related_name='auth_config',
        help_text="Django group that this configuration applies to"
    )
    
    # Dashboard configuration
    dashboard_type = models.CharField(
        max_length=20, 
        choices=DASHBOARD_CHOICES,
        help_text="Type of dashboard this group provides access to"
    )
    
    dashboard_url = models.CharField(
        max_length=200,
        help_text="""
        URL path where users will be redirected after login. Must be a valid Django URL pattern.
        
        SYNTAX RULES:
        • Must start with forward slash (/) - e.g., '/dashboard/' not 'dashboard/'
        • Should end with forward slash (/) for consistency - e.g., '/insurance/' not '/insurance'
        • Use lowercase with hyphens for multi-word URLs - e.g., '/technician-dashboard/' not '/TechnicianDashboard/'
        • No spaces or special characters except hyphens and underscores
        
        AVAILABLE DASHBOARDS IN THIS PROJECT:
        • Customer Dashboard: '/dashboard/' - Main customer portal for vehicle/maintenance info
        • Insurance Dashboard: '/insurance/' - Insurance company portal for policies and claims  
        • Technician Dashboard: '/technician-dashboard/' - Service technician tools and maintenance records
        • Admin Dashboard: '/admin/' - Django admin interface (use with caution for regular users)
        
        OTHER POSSIBLE DASHBOARD URLS:
        • Fleet Management: '/fleet-dashboard/' - Fleet management tools and reporting
        • Manager Dashboard: '/manager/' - Management oversight and reporting tools
        • Service Portal: '/service/' - Service center management interface
        • Claims Processing: '/claims/' - Insurance claims processing interface
        • Risk Assessment: '/risk-assessment/' - Risk analysis and assessment tools
        • Quality Control: '/quality-control/' - Quality assurance and control interface
        
        CUSTOM DASHBOARD EXAMPLES:
        • Parts Inventory: '/parts-inventory/'
        • Customer Service: '/customer-service/'
        • Scheduling: '/scheduling/'
        • Reporting: '/reporting/'
        • Analytics: '/analytics/'
        • Compliance: '/compliance/'
        
        IMPORTANT NOTES:
        • Ensure the URL pattern exists in your Django urls.py files before using
        • Test the URL manually in your browser before saving to avoid 404 errors
        • Use the 'Test Config' button in Authentication Group Management to validate URL accessibility
        • Dashboard URLs must be unique across all authentication groups to prevent conflicts
        • Consider user permissions and access levels when setting dashboard URLs
        • URLs are case-sensitive - use lowercase for consistency
        
        EXAMPLES OF CORRECT SYNTAX:
        ✓ '/dashboard/' - Customer dashboard (verified to exist)
        ✓ '/insurance/' - Insurance dashboard (verified to exist)
        ✓ '/technician-dashboard/' - Technician dashboard (verified to exist)
        ✓ '/admin/' - Django admin (verified to exist)
        ✓ '/custom-app/dashboard/' - Custom app dashboard
        
        EXAMPLES OF INCORRECT SYNTAX:
        ✗ 'dashboard' (missing leading slash)
        ✗ '/dashboard' (missing trailing slash - recommended for consistency)
        ✗ '/Dashboard/' (uppercase letters)
        ✗ '/dash board/' (contains space)
        ✗ '/dashboard/?' (contains query parameters)
        ✗ '/dashboard/#section' (contains fragment identifier)
        
        TESTING YOUR URL:
        1. Save this configuration
        2. Go to Authentication Group Management
        3. Click 'Test Config' button for this group
        4. Verify the URL is accessible and loads correctly
        5. Test with actual users to ensure proper permissions
        """
    )
    
    # Display configuration
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable name for this group (e.g., 'Customer Users', 'Insurance Agents')"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Description of what this group provides access to"
    )
    
    # Priority for dashboard selection (higher number = higher priority)
    priority = models.IntegerField(
        default=1,
        help_text="Priority when user has multiple groups (higher number = default dashboard)"
    )
    
    # Active status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this group configuration is active"
    )
    
    # Organization type compatibility
    compatible_org_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of organization types compatible with this group (e.g., ['insurance', 'fleet'])"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Authentication Group Configuration"
        verbose_name_plural = "Authentication Group Configurations"
        ordering = ['-priority', 'display_name']
    
    def __str__(self):
        return f"{self.display_name} ({self.group.name})"
    
    def get_dashboard_display(self):
        """Get human-readable dashboard type"""
        return dict(self.DASHBOARD_CHOICES).get(self.dashboard_type, self.dashboard_type)
    
    @classmethod
    def get_active_auth_groups(cls):
        """Get all active authentication groups"""
        return cls.objects.filter(is_active=True).select_related('group')
    
    @classmethod
    def get_group_dashboard_mapping(cls):
        """Get mapping of group names to dashboard URLs"""
        mapping = {}
        for auth_group in cls.get_active_auth_groups():
            mapping[auth_group.group.name] = {
                'url': auth_group.dashboard_url,
                'type': auth_group.dashboard_type,
                'display_name': auth_group.display_name,
                'priority': auth_group.priority
            }
        return mapping
    
    @classmethod
    def get_recommended_groups_for_org_type(cls, org_type):
        """Get recommended groups for a given organization type"""
        recommended = []
        for auth_group in cls.get_active_auth_groups():
            if org_type in auth_group.compatible_org_types:
                recommended.append(auth_group.group.name)
        return recommended
    
    def save(self, *args, **kwargs):
        # Ensure dashboard_url starts with /
        if self.dashboard_url and not self.dashboard_url.startswith('/'):
            self.dashboard_url = '/' + self.dashboard_url
        
        # Ensure dashboard_url ends with /
        if self.dashboard_url and not self.dashboard_url.endswith('/'):
            self.dashboard_url = self.dashboard_url + '/'
            
        super().save(*args, **kwargs)