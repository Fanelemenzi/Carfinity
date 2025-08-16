from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from vehicles.models import Vehicle  # Import from your vehicles app
from maintenance.models import ScheduledMaintenance, Part  # Import from your maintenance app
from django.contrib.auth.models import User
import os


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


def inspection_pdf_upload_path(instance, filename):
    """Generate upload path for inspection PDFs"""
    return f'inspections/{instance.vehicle.vin}/{instance.inspection_number}_{filename}'

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
    link_to_results = models.URLField(max_length=400, blank=True, null=True, 
        verbose_name="External Link to Results")
    
    # PDF attachment field
    inspection_pdf = models.FileField(
        upload_to=inspection_pdf_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        verbose_name="Inspection Report PDF",
        help_text="Upload the inspection report as a PDF file",
        blank=True,
        null=True
    )
    
    # Additional metadata
    pdf_uploaded_at = models.DateTimeField(null=True, blank=True, verbose_name="PDF Upload Date")
    pdf_file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name="File Size (bytes)")
    
    created_at = models.DateTimeField(null=True, blank=True,)
    updated_at = models.DateTimeField(null=True, blank=True,)

    class Meta:
        ordering = ['-inspection_date']
        verbose_name = "Inspection"
        verbose_name_plural = "Inspections"

    def __str__(self):
        return f"{self.inspection_number} - {self.vehicle.vin}"
    
    def save(self, *args, **kwargs):
        # Store file size when saving
        if self.inspection_pdf:
            self.pdf_file_size = self.inspection_pdf.size
        super().save(*args, **kwargs)
    
    @property
    def pdf_file_size_mb(self):
        """Return file size in MB"""
        if self.pdf_file_size:
            return round(self.pdf_file_size / (1024 * 1024), 2)
        return None
    
    @property
    def has_pdf(self):
        """Check if inspection has a PDF attached"""
        return bool(self.inspection_pdf)
