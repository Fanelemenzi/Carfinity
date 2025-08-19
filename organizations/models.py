from django.db import models
from django.contrib.auth.models import Group
from users.models import User
from vehicles.models import Vehicle

# Create your models here.
class Organization(models.Model):
    ORGANIZATION_TYPES = [
        ('insurance', 'Insurance Company'),
        ('fleet', 'Fleet Management'),
        ('dealership', 'Dealership'),
        ('service', 'Service Provider'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    organization_type = models.CharField(max_length=20, choices=ORGANIZATION_TYPES, default='other')
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Link to Django Groups for permissions
    linked_groups = models.ManyToManyField(
        Group, 
        blank=True, 
        related_name='organizations',
        help_text="Django groups linked to this organization for permission management"
    )
    
    # Insurance-specific fields
    is_insurance_provider = models.BooleanField(default=False)
    insurance_license_number = models.CharField(max_length=100, blank=True, null=True)
    insurance_rating = models.CharField(max_length=10, blank=True, null=True, help_text="A.M. Best rating or similar")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def add_user_to_groups(self, user):
        """Add user to all linked groups when they join the organization"""
        for group in self.linked_groups.all():
            user.groups.add(group)
    
    def remove_user_from_groups(self, user):
        """Remove user from all linked groups when they leave the organization"""
        for group in self.linked_groups.all():
            user.groups.remove(group)
    
    def sync_all_members_to_groups(self):
        """Sync all active organization members to linked groups"""
        for org_user in self.organization_members.filter(is_active=True):
            self.add_user_to_groups(org_user.user)


class OrganizationUser(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('DRIVER', 'Driver'),
        ('AGENT', 'Insurance Agent'),
        ('UNDERWRITER', 'Underwriter'),
        ('CLAIMS_ADJUSTER', 'Claims Adjuster'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_organization_users')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organization_members')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'organization']

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_active = None
        
        if not is_new:
            try:
                old_instance = OrganizationUser.objects.get(pk=self.pk)
                was_active = old_instance.is_active
            except OrganizationUser.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Manage group membership based on organization membership
        if is_new or (was_active != self.is_active):
            if self.is_active:
                self.organization.add_user_to_groups(self.user)
            else:
                self.organization.remove_user_from_groups(self.user)
    
    def delete(self, *args, **kwargs):
        # Remove user from organization groups when membership is deleted
        self.organization.remove_user_from_groups(self.user)
        super().delete(*args, **kwargs)

class OrganizationVehicle(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='organization_vehicles')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organization_vehicles')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_vehicles')
    assigned_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle.vin} - {self.organization.name}"


class InsuranceOrganization(models.Model):
    """Extended model for insurance-specific organization data"""
    organization = models.OneToOneField(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='insurance_details'
    )
    
    # Insurance company details
    naic_number = models.CharField(max_length=20, blank=True, null=True, help_text="NAIC Company Code")
    am_best_rating = models.CharField(max_length=10, blank=True, null=True, help_text="A.M. Best Financial Strength Rating")
    states_licensed = models.TextField(blank=True, help_text="Comma-separated list of states where licensed")
    
    # Business metrics
    total_policies = models.IntegerField(default=0)
    total_premium_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Risk management settings
    max_risk_score_threshold = models.FloatField(default=7.0, help_text="Maximum acceptable risk score")
    auto_approve_low_risk = models.BooleanField(default=True)
    require_inspection_threshold = models.FloatField(default=5.0, help_text="Risk score requiring mandatory inspection")
    
    # Notification settings
    send_maintenance_alerts = models.BooleanField(default=True)
    send_risk_alerts = models.BooleanField(default=True)
    alert_email = models.EmailField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Insurance Details - {self.organization.name}"
    
    def update_business_metrics(self):
        """Update business metrics from related insurance policies"""
        try:
            from insurance_app.models import InsurancePolicy
            policies = InsurancePolicy.objects.filter(organization=self.organization)
            
            self.total_policies = policies.count()
            self.total_premium_volume = sum(policy.premium_amount for policy in policies)
            self.save()
        except ImportError:
            # Handle case where insurance_app models aren't available yet
            pass

