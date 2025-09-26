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


# Simplified authentication system - removed complex AuthenticationGroup model
# Authentication now uses only 3 groups: Staff, AutoCare, AutoAssess