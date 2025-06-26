from django.db import models
from vehicles.models import Vehicle
from django.contrib.auth.models import User

# Create your models here.
class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    recommended_interval_mileage = models.PositiveIntegerField(blank=True, null=True)
    recommended_interval_time = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Part(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MaintenancePlan(models.Model):
    """
    Template for maintenance plans (e.g., "Toyota Camry - Standard Maintenance")
    """
    name = models.CharField(max_length=100, help_text="E.g., 'Toyota 1uz Gasoline Service Plan'")
    vehicle_model = models.CharField(max_length=50, help_text="E.g., 'Toyota Camry 2023'")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_model} - {self.name}"

class MaintenanceTask(models.Model):
    """
    Individual tasks within a maintenance plan (e.g., "Oil Change")
    """
    plan = models.ForeignKey(MaintenancePlan, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=100, help_text="Oil Change, Air Filter Fitting")
    description = models.TextField(blank=True)
    service_type = models.ForeignKey(ServiceType, max_length=100, on_delete=models.CASCADE, help_text="Type of service")
    interval_miles = models.PositiveIntegerField(help_text="Mileage interval (e.g., 5000)")
    interval_months = models.PositiveIntegerField(help_text="Time interval in months (e.g., 6)")
    parts = models.ManyToManyField(Part, blank=True, through='TaskPartRequirement')
    estimated_time = models.DurationField(help_text="Estimated duration (HH:MM:SS)")
    priority = models.CharField(
        max_length=10,
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
        default='MEDIUM'
    )

    class Meta:
        ordering = ['priority', 'interval_miles']

    def __str__(self):
        return f"{self.plan.vehicle_model} - {self.name}"


class TaskPartRequirement(models.Model):
    """
    Specifies exact parts/quantities needed for a task
    """
    task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.task.name} → {self.part.name} x{self.quantity}"

class AssignedVehiclePlan(models.Model):
    """
    Links a maintenance plan to a specific owner's vehicle
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assigned_plans')
    plan = models.ForeignKey(MaintenancePlan, on_delete=models.PROTECT)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    current_mileage = models.PositiveIntegerField(help_text="Mileage at assignment")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.plan.name}"



class ScheduledMaintenance(models.Model):
    """
    Calendar events generated from assigned plans
    """
    assigned_plan = models.ForeignKey(AssignedVehiclePlan, on_delete=models.CASCADE, related_name='schedules')
    task = models.ForeignKey(MaintenanceTask, on_delete=models.CASCADE)
    due_date = models.DateField()
    due_mileage = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('COMPLETED', 'Completed'),
            ('OVERDUE', 'Overdue'),
            ('SKIPPED', 'Skipped')
        ],
        default='PENDING'
    )
    completed_date = models.DateField(blank=True, null=True)
    completed_mileage = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True)
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='services_performed')

    class Meta:
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['due_date', 'status']),
        ]

    def __str__(self):
        return f"{self.assigned_plan.vehicle} - {self.task.name} ({self.status})"


class Document(models.Model):
    maintenance_record = models.ForeignKey(ScheduledMaintenance, on_delete=models.CASCADE, related_name='documents')
    file_url = models.URLField()
    document_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} for {self.maintenance_record}"



