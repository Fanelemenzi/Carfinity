from django.db import models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from users.models import User
from vehicles.models import Vehicle  # Import from your vehicles app
from maintenance.models import ScheduledMaintenance, Part  # Import from your maintenance app


class MaintenanceRecord(models.Model):
    vehicle = models.ForeignKey(Vehicle,on_delete=models.CASCADE, related_name='maintenance_history', 
    verbose_name="Vehicle (VIN)")
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_maintenance',
        verbose_name="Technician")
    scheduled_maintenance = models.ForeignKey(ScheduledMaintenance, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_records',
        verbose_name="Scheduled Maintenance"
    )
    work_done = models.TextField(verbose_name="Work Performed")
    date_performed = models.DateTimeField(default=timezone.now,verbose_name="Date/Time of Service")
    mileage = models.PositiveIntegerField(verbose_name="Vehicle Mileage at Service")
    notes = models.TextField(blank=True, verbose_name="Additional Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_performed']
        verbose_name = "Maintenance Record"
        verbose_name_plural = "Maintenance Records"

    def __str__(self):
        return f"{self.vehicle.vin} - {self.date_performed.strftime('%Y-%m-%d')}"

class PartUsage(models.Model):
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='parts_used')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='usage_records')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Cost per Unit")

    @property
    def total_cost(self):
        if self.unit_cost:
            return self.unit_cost * self.quantity
        return None

    def __str__(self):
        return f"{self.part.name} x {self.quantity}"

    class Meta:
        verbose_name = "Part Usage"
        verbose_name_plural = "Parts Used"
        unique_together = ('maintenance_record', 'part')


class Inspection(models.Model):

    RESULT_CHOICES = [
        ("PAS", "Passed"),
        ("PMD",  "Passed with minor Defects"),
        ("PJD", "Passed with major Defects"),
        ("FMD",  "Failed due to minor Defects"),
        ("FJD",  "Failed due to major Defects"),
        ("FAI",  "Failed"),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='inspections')
    inspection_number = models.CharField(max_length=20, unique=True)
    year = models.IntegerField(
    validators=[
        MinValueValidator(1900),
        MaxValueValidator(2100)
    ]
    )
    inspection_result = models.CharField(max_length=30, 
    choices=RESULT_CHOICES, verbose_name="Inspection Result")
    carfinity_rating = models.CharField(max_length=30)
    inspection_date = models.DateField()
    link_to_results = models.URLField(max_length=400)

    def __str__(self):
        return self.inspection_number
