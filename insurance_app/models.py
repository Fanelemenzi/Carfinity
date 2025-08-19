# models.py
from django.db import models
from django.contrib.auth.models import User
from vehicles.models import Vehicle
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class InsurancePolicy(models.Model):
    policy_number = models.CharField(max_length=20, unique=True)
    policy_holder = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Link to insurance organization
    organization = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.CASCADE, 
        related_name='insurance_policies',
        limit_choices_to={'is_insurance_provider': True},
        help_text="Insurance company providing this policy",
        null=True, blank=True  # Make optional for existing data
    )
    
    start_date = models.DateField()
    end_date = models.DateField()
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled')
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.organization:
            return f"Policy {self.policy_number} - {self.organization.name}"
        return f"Policy {self.policy_number}"

class Vehicle(models.Model):
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ]
    
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE, related_name='vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='vehicles')
    purchase_date = models.DateField()
    current_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    vehicle_health_index = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100.0,
        help_text="Vehicle Health Index (0-100)"
    )
    risk_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=1.0,
        help_text="Risk Score (0-10, higher is riskier)"
    )
    last_inspection_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.vin}"

class MaintenanceSchedule(models.Model):
    MAINTENANCE_TYPES = [
        ('oil_change', 'Oil Change'),
        ('brake_service', 'Brake Service'),
        ('tire_rotation', 'Tire Rotation'),
        ('transmission', 'Transmission Service'),
        ('engine_tune', 'Engine Tune-up'),
        ('inspection', 'Safety Inspection'),
        ('other', 'Other')
    ]
    
    PRIORITY_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_schedules')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    scheduled_date = models.DateField()
    due_mileage = models.IntegerField()
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    service_provider = models.CharField(max_length=100, blank=True)
    
    # Connection to maintenance app
    scheduled_maintenance = models.OneToOneField(
        'maintenance.ScheduledMaintenance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_schedule',
        help_text="Link to the detailed maintenance schedule"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date']

    def is_overdue(self):
        return not self.is_completed and self.scheduled_date < timezone.now().date()

    def days_overdue(self):
        if self.is_overdue():
            return (timezone.now().date() - self.scheduled_date).days
        return 0
    
    def sync_with_maintenance_app(self):
        """Synchronize data with the maintenance app's ScheduledMaintenance"""
        if self.scheduled_maintenance:
            # Update status based on maintenance app
            if self.scheduled_maintenance.status == 'COMPLETED':
                self.is_completed = True
                self.completed_date = self.scheduled_maintenance.completed_date
            elif self.scheduled_maintenance.status == 'OVERDUE':
                self.is_completed = False
            
            # Update dates and mileage
            self.scheduled_date = self.scheduled_maintenance.due_date
            self.due_mileage = self.scheduled_maintenance.due_mileage
            
            # Update description from task details
            if self.scheduled_maintenance.task:
                self.description = self.scheduled_maintenance.task.description or self.scheduled_maintenance.task.name
            
            self.save()
    
    @classmethod
    def create_from_scheduled_maintenance(cls, scheduled_maintenance, vehicle=None):
        """Create insurance schedule from maintenance app's scheduled maintenance"""
        from .utils import MaintenanceSyncManager
        return MaintenanceSyncManager.create_insurance_schedule_from_maintenance(
            scheduled_maintenance, vehicle
        )

class MaintenanceCompliance(models.Model):
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, related_name='compliance')
    overall_compliance_rate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100.0
    )
    critical_maintenance_compliance = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100.0
    )
    overdue_count = models.IntegerField(default=0)
    completed_on_time_count = models.IntegerField(default=0)
    total_scheduled_count = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(auto_now=True)

    def calculate_compliance(self):
        schedules = self.vehicle.maintenance_schedules.all()
        total = schedules.count()
        completed_on_time = schedules.filter(
            is_completed=True,
            completed_date__lte=models.F('scheduled_date')
        ).count()
        
        critical_schedules = schedules.filter(priority_level='critical')
        critical_total = critical_schedules.count()
        critical_on_time = critical_schedules.filter(
            is_completed=True,
            completed_date__lte=models.F('scheduled_date')
        ).count()
        
        self.total_scheduled_count = total
        self.completed_on_time_count = completed_on_time
        self.overdue_count = schedules.filter(
            is_completed=False,
            scheduled_date__lt=timezone.now().date()
        ).count()
        
        self.overall_compliance_rate = (completed_on_time / total * 100) if total > 0 else 100
        self.critical_maintenance_compliance = (critical_on_time / critical_total * 100) if critical_total > 0 else 100
        self.save()

class Accident(models.Model):
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('total_loss', 'Total Loss')
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='accidents')
    accident_date = models.DateTimeField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    maintenance_related = models.BooleanField(default=False)
    related_maintenance_type = models.CharField(max_length=20, blank=True)
    days_since_last_maintenance = models.IntegerField(null=True, blank=True)
    fault_determination = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200)
    weather_conditions = models.CharField(max_length=50, blank=True)
    
    # Link to detailed vehicle history record
    vehicle_history = models.OneToOneField(
        'vehicles.VehicleHistory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_accident',
        help_text="Link to detailed vehicle history record for this accident"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_detailed_accident_info(self):
        """Get detailed accident information from vehicle history"""
        if self.vehicle_history and self.vehicle_history.event_type == 'ACCIDENT':
            return {
                'police_report_number': self.vehicle_history.police_report_number,
                'insurance_claim_number': self.vehicle_history.insurance_claim_number,
                'accident_location': self.vehicle_history.accident_location,
                'accident_severity': self.vehicle_history.accident_severity,
                'reported_by': self.vehicle_history.reported_by,
                'verified': self.vehicle_history.verified,
                'verified_by': self.vehicle_history.verified_by,
                'notes': self.vehicle_history.notes,
                'reported_date': self.vehicle_history.reported_date,
            }
        return None
    
    def sync_with_vehicle_history(self):
        """Synchronize accident data with vehicle history record"""
        if self.vehicle_history:
            # Update vehicle history with insurance data
            history = self.vehicle_history
            history.event_date = self.accident_date.date()
            history.description = self.description
            history.accident_location = self.location
            
            # Map insurance severity to vehicle history severity
            severity_mapping = {
                'minor': 'MINOR',
                'moderate': 'MAJOR',
                'major': 'MAJOR',
                'total_loss': 'TOTAL_LOSS'
            }
            history.accident_severity = severity_mapping.get(self.severity, 'MAJOR')
            history.save()
    
    @classmethod
    def create_from_vehicle_history(cls, vehicle_history, claim_amount=0):
        """Create insurance accident record from vehicle history"""
        if vehicle_history.event_type != 'ACCIDENT':
            raise ValueError("Vehicle history record must be of type ACCIDENT")
        
        # Map vehicle history severity to insurance severity
        severity_mapping = {
            'MINOR': 'minor',
            'MAJOR': 'major',
            'TOTAL_LOSS': 'total_loss'
        }
        
        accident = cls.objects.create(
            vehicle=vehicle_history.vehicle,
            accident_date=timezone.make_aware(
                timezone.datetime.combine(vehicle_history.event_date, timezone.datetime.min.time())
            ),
            severity=severity_mapping.get(vehicle_history.accident_severity, 'moderate'),
            claim_amount=claim_amount,
            description=vehicle_history.description or 'Accident imported from vehicle history',
            location=vehicle_history.accident_location or 'Unknown',
            vehicle_history=vehicle_history
        )
        
        return accident

class VehicleConditionScore(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='condition_scores')
    assessment_date = models.DateField()
    engine_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    transmission_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    brake_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    tire_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    suspension_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    electrical_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    overall_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    assessment_type = models.CharField(max_length=20, choices=[
        ('inspection', 'Professional Inspection'),
        ('telematics', 'Telematics Data'),
        ('obd', 'OBD-II Diagnostic'),
        ('self_report', 'Self Reported')
    ])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessment_date']

    def calculate_overall_score(self):
        scores = [
            self.engine_score * 0.25,
            self.transmission_score * 0.20,
            self.brake_score * 0.25,
            self.tire_score * 0.15,
            self.suspension_score * 0.10,
            self.electrical_score * 0.05
        ]
        self.overall_score = sum(scores)
        return self.overall_score

class RiskAlert(models.Model):
    ALERT_TYPES = [
        ('high_risk_vehicle', 'High Risk Vehicle'),
        ('maintenance_overdue', 'Maintenance Overdue'),
        ('condition_deterioration', 'Condition Deterioration'),
        ('accident_pattern', 'Accident Pattern'),
        ('compliance_drop', 'Compliance Drop')
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='risk_alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    title = models.CharField(max_length=200)
    description = models.TextField()
    risk_score_impact = models.FloatField()
    is_resolved = models.BooleanField(default=False)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class RiskAssessmentMetrics(models.Model):
    """Aggregated metrics for dashboard reporting"""
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE, related_name='metrics')
    calculation_date = models.DateField(auto_now_add=True)
    
    # Portfolio Maintenance Compliance
    portfolio_compliance_rate = models.FloatField()
    critical_maintenance_compliance = models.FloatField()
    
    # Vehicle Condition Metrics
    avg_vehicle_health_index = models.FloatField()
    vehicles_excellent_condition = models.IntegerField()
    vehicles_poor_condition = models.IntegerField()
    
    # Accident Correlation
    maintenance_related_accidents = models.IntegerField()
    total_accidents = models.IntegerField()
    accident_correlation_rate = models.FloatField()
    
    # Risk Metrics
    high_risk_vehicles = models.IntegerField()
    active_alerts = models.IntegerField()
    resolved_alerts_30d = models.IntegerField()
    
    class Meta:
        ordering = ['-calculation_date']
        unique_together = ['policy', 'calculation_date']