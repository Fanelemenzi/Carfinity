from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class PendingVehicleOnboarding(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Who submitted the onboarding request
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pending_vehicle_onboardings')
    # Which client is this for
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pending_client_vehicles')
    # Data fields (store as JSON for flexibility)
    vehicle_data = models.JSONField()
    ownership_data = models.JSONField()
    status_data = models.JSONField()
    history_data = models.JSONField(blank=True, null=True)
    equipment_data = models.JSONField()
    # New field for image data
    image_data = models.JSONField(blank=True, null=True, help_text="Stores image URLs and metadata")
    # Approval status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_vehicle_onboardings')

    def __str__(self):
        return f"Pending Vehicle for {self.client.username} (by {self.submitted_by.username if self.submitted_by else 'Unknown'})"

