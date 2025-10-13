from django.db import models
from vehicles.models import Vehicle

# Create your models here.

class VehicleAlert(models.Model):
    """
    Model to store vehicle alerts and notifications for maintenance, 
    part replacement, insurance expiry, and other vehicle-related alerts
    """
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    ALERT_TYPES = [
        ('MAINTENANCE_OVERDUE', 'Maintenance Overdue'),
        ('PART_REPLACEMENT', 'Part Replacement'),
        ('INSURANCE_EXPIRY', 'Insurance Expiry'),
        ('INSPECTION_DUE', 'Inspection Due'),
    ]
    
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE, 
        related_name='alerts',
        help_text="Vehicle this alert belongs to"
    )
    alert_type = models.CharField(
        max_length=50, 
        choices=ALERT_TYPES,
        help_text="Type of alert"
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES,
        help_text="Priority level of the alert"
    )
    title = models.CharField(
        max_length=200,
        help_text="Alert title/summary"
    )
    description = models.TextField(
        help_text="Detailed description of the alert"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this alert is currently active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this alert was created"
    )
    resolved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this alert was resolved"
    )

    class Meta:
        verbose_name = "Vehicle Alert"
        verbose_name_plural = "Vehicle Alerts"
        ordering = ['-created_at', '-priority']
        indexes = [
            models.Index(fields=['vehicle', 'is_active']),
            models.Index(fields=['vehicle', 'alert_type', 'is_active']),
            models.Index(fields=['priority', 'created_at']),
            models.Index(fields=['is_active', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_priority_display()} Alert: {self.title} - {self.vehicle.vin}"

    def resolve(self):
        """Mark this alert as resolved"""
        from django.utils import timezone
        self.is_active = False
        self.resolved_at = timezone.now()
        self.save()


class VehicleCostAnalytics(models.Model):
    """
    Model to store monthly cost analytics for vehicle maintenance and expenses
    """
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE, 
        related_name='cost_analytics',
        help_text="Vehicle this cost analytics belongs to"
    )
    month = models.DateField(
        help_text="Month for which these analytics are calculated (first day of month)"
    )
    total_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Total cost for the month"
    )
    maintenance_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Total maintenance cost for the month"
    )
    parts_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Total parts cost for the month"
    )
    labor_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Total labor cost for the month"
    )

    class Meta:
        verbose_name = "Vehicle Cost Analytics"
        verbose_name_plural = "Vehicle Cost Analytics"
        ordering = ['-month']
        unique_together = ['vehicle', 'month']
        indexes = [
            models.Index(fields=['vehicle', 'month']),
            models.Index(fields=['month']),
        ]

    def __str__(self):
        return f"Cost Analytics for {self.vehicle.vin} - {self.month.strftime('%B %Y')}"

    @property
    def formatted_total_cost(self):
        """Return formatted total cost"""
        return f"${self.total_cost:,.2f}"

    @property
    def formatted_maintenance_cost(self):
        """Return formatted maintenance cost"""
        return f"${self.maintenance_cost:,.2f}"

    @property
    def formatted_parts_cost(self):
        """Return formatted parts cost"""
        return f"${self.parts_cost:,.2f}"

    @property
    def formatted_labor_cost(self):
        """Return formatted labor cost"""
        return f"${self.labor_cost:,.2f}"
