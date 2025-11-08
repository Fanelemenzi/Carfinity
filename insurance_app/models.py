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
        ('transmission_service', 'Transmission Service'),
        ('engine_tune_up', 'Engine Tune-up'),
        ('air_filter', 'Air Filter Replacement'),
        ('coolant_flush', 'Coolant Flush'),
        ('battery_service', 'Battery Service'),
        ('inspection', 'Safety Inspection'),
        ('other', 'Other')
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_schedules')
    maintenance_type = models.CharField(max_length=30, choices=MAINTENANCE_TYPES)
    priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    scheduled_date = models.DateField()
    due_mileage = models.PositiveIntegerField(null=True, blank=True, help_text="Mileage when maintenance is due")
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    service_provider = models.CharField(max_length=100, blank=True)
    
    # Foreign key relationship with maintenance app
    scheduled_maintenance = models.ForeignKey(
        'maintenance.ScheduledMaintenance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_schedules',
        help_text="Link to scheduled maintenance in maintenance app"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_date', 'priority_level']
        indexes = [
            models.Index(fields=['scheduled_date', 'is_completed']),
            models.Index(fields=['vehicle', 'maintenance_type']),
        ]
    
    def __str__(self):
        vehicle_info = f"{self.vehicle.vehicle.make} {self.vehicle.vehicle.model}" if self.vehicle.vehicle else "Unknown Vehicle"
        return f"{vehicle_info} - {self.get_maintenance_type_display()} ({self.scheduled_date})"
    
    def is_overdue(self):
        """Check if maintenance is overdue"""
        if self.is_completed:
            return False
        return self.scheduled_date < timezone.now().date()
    
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.is_overdue():
            return 0
        return (timezone.now().date() - self.scheduled_date).days
    
    def get_maintenance_details(self):
        """Get details from linked maintenance app record"""
        if self.scheduled_maintenance:
            return {
                'task_name': self.scheduled_maintenance.task.name if self.scheduled_maintenance.task else None,
                'maintenance_status': self.scheduled_maintenance.status,
                'technician': self.scheduled_maintenance.technician.username if self.scheduled_maintenance.technician else None,
                'due_mileage': self.scheduled_maintenance.due_mileage,
                'completed_mileage': self.scheduled_maintenance.completed_mileage,
                'notes': self.scheduled_maintenance.notes,
            }
        return None
    
    def sync_with_maintenance_app(self):
        """Sync completion status with maintenance app"""
        if self.scheduled_maintenance:
            maintenance = self.scheduled_maintenance
            if maintenance.status == 'COMPLETED' and not self.is_completed:
                self.is_completed = True
                self.completed_date = maintenance.completed_date
                self.save()
            elif maintenance.status != 'COMPLETED' and self.is_completed:
                self.is_completed = False
                self.completed_date = None
                self.save()

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


# Assessment History and Audit Trail Models

class AssessmentHistory(models.Model):
    """Track all changes and activities for vehicle assessments"""
    
    ACTIVITY_TYPES = [
        ('status_change', 'Status Change'),
        ('cost_adjustment', 'Cost Adjustment'),
        ('document_update', 'Document Update'),
        ('agent_assignment', 'Agent Assignment'),
        ('comment_added', 'Comment Added'),
        ('photo_uploaded', 'Photo Uploaded'),
        ('photo_deleted', 'Photo Deleted'),
        ('section_updated', 'Section Updated'),
        ('workflow_action', 'Workflow Action'),
        ('report_generated', 'Report Generated'),
        ('approval_granted', 'Approval Granted'),
        ('rejection_issued', 'Rejection Issued'),
        ('changes_requested', 'Changes Requested'),
    ]
    
    assessment = models.ForeignKey(
        'assessments.VehicleAssessment', 
        on_delete=models.CASCADE, 
        related_name='history_entries'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_activities')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Change tracking
    field_name = models.CharField(max_length=100, blank=True, help_text="Field that was changed")
    old_value = models.TextField(blank=True, help_text="Previous value")
    new_value = models.TextField(blank=True, help_text="New value")
    
    # Activity details
    description = models.TextField(help_text="Description of the activity")
    notes = models.TextField(blank=True, help_text="Additional notes or context")
    
    # Related objects
    related_comment_id = models.PositiveIntegerField(null=True, blank=True)
    related_photo_id = models.PositiveIntegerField(null=True, blank=True)
    related_section = models.CharField(max_length=50, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['assessment', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.assessment.assessment_id} - {self.get_activity_type_display()} by {self.user.username}"


class AssessmentVersion(models.Model):
    """Version control for assessment data"""
    
    assessment = models.ForeignKey(
        'assessments.VehicleAssessment', 
        on_delete=models.CASCADE, 
        related_name='versions'
    )
    version_number = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Snapshot of assessment data
    assessment_data = models.JSONField(help_text="Complete snapshot of assessment data")
    
    # Version metadata
    change_summary = models.TextField(help_text="Summary of changes in this version")
    is_major_version = models.BooleanField(default=False, help_text="Major version change")
    
    # Related history entry
    history_entry = models.OneToOneField(
        AssessmentHistory, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='version_snapshot'
    )
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['assessment', 'version_number']
        indexes = [
            models.Index(fields=['assessment', 'version_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.assessment.assessment_id} v{self.version_number}"


# Import existing models from assessments app
from assessments.models import AssessmentComment, AssessmentWorkflow, VehicleAssessment, AssessmentPhoto


class AssessmentNotification(models.Model):
    """Notification system for assessment status changes"""
    
    NOTIFICATION_TYPES = [
        ('status_change', 'Status Change'),
        ('comment_added', 'Comment Added'),
        ('deadline_reminder', 'Deadline Reminder'),
        ('approval_required', 'Approval Required'),
        ('rejection_notice', 'Rejection Notice'),
        ('changes_requested', 'Changes Requested'),
    ]
    
    NOTIFICATION_STATUS = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('dismissed', 'Dismissed'),
    ]
    
    assessment = models.ForeignKey(
        'assessments.VehicleAssessment', 
        on_delete=models.CASCADE, 
        related_name='insurance_notifications'
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insurance_assessment_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS, default='unread')
    related_comment = models.ForeignKey(
        AssessmentComment, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status', 'created_at']),
            models.Index(fields=['assessment', 'created_at']),
        ]
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()


# Parts-Based Quote System Models

class DamagedPart(models.Model):
    """Model for tracking damaged parts identified from vehicle assessments"""
    
    PART_CATEGORIES = [
        ('body', 'Body Panel'),
        ('mechanical', 'Mechanical Component'),
        ('electrical', 'Electrical Component'),
        ('glass', 'Glass/Windows'),
        ('interior', 'Interior Component'),
        ('trim', 'Trim/Cosmetic'),
        ('wheels', 'Wheels/Tires'),
        ('safety', 'Safety System'),
        ('structural', 'Structural Component'),
        ('fluid', 'Fluid System'),
    ]
    
    DAMAGE_SEVERITY = [
        ('minor', 'Minor Damage'),
        ('moderate', 'Moderate Damage'),
        ('severe', 'Severe Damage'),
        ('replace', 'Requires Replacement'),
    ]
    
    SECTION_TYPES = [
        ('exterior', 'Exterior'),
        ('mechanical', 'Mechanical'),
        ('interior', 'Interior'),
        ('electrical', 'Electrical'),
        ('wheels', 'Wheels'),
        ('safety', 'Safety'),
        ('structural', 'Structural'),
        ('fluids', 'Fluids'),
    ]
    
    assessment = models.ForeignKey(
        VehicleAssessment, 
        on_delete=models.CASCADE, 
        related_name='damaged_parts'
    )
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    part_name = models.CharField(max_length=200)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    part_category = models.CharField(max_length=20, choices=PART_CATEGORIES)
    damage_severity = models.CharField(max_length=20, choices=DAMAGE_SEVERITY)
    damage_description = models.TextField()
    requires_replacement = models.BooleanField(default=False)
    estimated_labor_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    damage_images = models.ManyToManyField(AssessmentPhoto, blank=True)
    identified_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['section_type', 'part_category', 'part_name']
        indexes = [
            models.Index(fields=['assessment', 'section_type']),
            models.Index(fields=['part_category', 'damage_severity']),
            models.Index(fields=['identified_date']),
        ]
    
    def __str__(self):
        return f"{self.assessment.assessment_id} - {self.part_name} ({self.get_damage_severity_display()})"
    
    def get_estimated_cost_range(self):
        """Get estimated cost range based on part category and damage severity"""
        # Base cost multipliers by category
        base_costs = {
            'body': 500,
            'mechanical': 800,
            'electrical': 300,
            'glass': 200,
            'interior': 150,
            'trim': 100,
            'wheels': 400,
            'safety': 600,
            'structural': 1200,
            'fluid': 250,
        }
        
        # Severity multipliers
        severity_multipliers = {
            'minor': 0.3,
            'moderate': 0.6,
            'severe': 1.0,
            'replace': 1.5,
        }
        
        base_cost = base_costs.get(self.part_category, 300)
        multiplier = severity_multipliers.get(self.damage_severity, 1.0)
        
        estimated_cost = base_cost * multiplier
        labor_cost = float(self.estimated_labor_hours) * 45  # £45/hour
        
        return {
            'min_cost': estimated_cost * 0.8 + labor_cost,
            'max_cost': estimated_cost * 1.2 + labor_cost,
            'estimated_cost': estimated_cost + labor_cost
        }


class PartQuoteRequest(models.Model):
    """Model for managing quote requests sent to providers"""
    
    REQUEST_STATUS = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('sent', 'Sent to Provider'),
        ('received', 'Quote Received'),
        ('expired', 'Request Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    damaged_part = models.ForeignKey(
        DamagedPart, 
        on_delete=models.CASCADE, 
        related_name='quote_requests'
    )
    assessment = models.ForeignKey(
        VehicleAssessment, 
        on_delete=models.CASCADE, 
        related_name='part_quote_requests'
    )
    request_id = models.CharField(max_length=50, unique=True, db_index=True)
    request_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='draft')
    
    # Provider selection (manual by assessor)
    include_assessor = models.BooleanField(default=False)
    include_dealer = models.BooleanField(default=False)
    include_independent = models.BooleanField(default=False)
    include_network = models.BooleanField(default=False)
    
    # Vehicle context for providers
    vehicle_make = models.CharField(max_length=100)
    vehicle_model = models.CharField(max_length=100)
    vehicle_year = models.IntegerField()
    vehicle_vin = models.CharField(max_length=17, blank=True)
    
    # Dispatch tracking
    dispatched_by = models.ForeignKey(User, on_delete=models.CASCADE)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['assessment', 'status']),
            models.Index(fields=['expiry_date', 'status']),
            models.Index(fields=['dispatched_by', 'request_date']),
        ]
    
    def __str__(self):
        return f"Quote Request {self.request_id} - {self.damaged_part.part_name}"
    
    def generate_request_id(self):
        """Generate unique request ID"""
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        unique_id = str(uuid.uuid4())[:8]
        return f"QR-{timestamp}-{unique_id}"
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = self.generate_request_id()
        
        # Set vehicle context from assessment
        if self.assessment and self.assessment.vehicle:
            vehicle = self.assessment.vehicle
            self.vehicle_make = vehicle.make
            self.vehicle_model = vehicle.model
            self.vehicle_year = vehicle.manufacture_year
            if hasattr(vehicle, 'vin'):
                self.vehicle_vin = vehicle.vin
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if request has expired"""
        return timezone.now() > self.expiry_date
    
    def days_until_expiry(self):
        """Get number of days until expiry (negative if expired)"""
        delta = self.expiry_date.date() - timezone.now().date()
        return delta.days
    
    def get_selected_providers(self):
        """Get list of selected provider types"""
        providers = []
        if self.include_assessor:
            providers.append('assessor')
        if self.include_dealer:
            providers.append('dealer')
        if self.include_independent:
            providers.append('independent')
        if self.include_network:
            providers.append('network')
        return providers


class PartQuote(models.Model):
    """Model for storing quotes received from providers"""
    
    PROVIDER_TYPES = [
        ('assessor', 'Assessor Estimate'),
        ('dealer', 'Authorized Dealer'),
        ('independent', 'Independent Garage'),
        ('network', 'Insurance Network'),
    ]
    
    PART_TYPES = [
        ('oem', 'OEM (Original Equipment)'),
        ('oem_equivalent', 'OEM Equivalent'),
        ('aftermarket', 'Aftermarket'),
        ('used', 'Used/Reconditioned'),
    ]
    
    QUOTE_STATUS = [
        ('submitted', 'Submitted'),
        ('validated', 'Validated'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    quote_request = models.ForeignKey(
        PartQuoteRequest, 
        on_delete=models.CASCADE, 
        related_name='quotes'
    )
    damaged_part = models.ForeignKey(
        DamagedPart, 
        on_delete=models.CASCADE, 
        related_name='quotes'
    )
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    provider_name = models.CharField(max_length=200)
    provider_contact = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=QUOTE_STATUS, default='submitted')
    
    # Cost breakdown
    part_cost = models.DecimalField(max_digits=10, decimal_places=2)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2)
    paint_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    additional_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Part specifications
    part_type = models.CharField(max_length=50, choices=PART_TYPES, default='oem')
    part_manufacturer = models.CharField(max_length=100, blank=True)
    part_number_quoted = models.CharField(max_length=100, blank=True)
    
    # Timeline and warranty
    estimated_delivery_days = models.IntegerField()
    estimated_completion_days = models.IntegerField()
    part_warranty_months = models.IntegerField(default=12)
    labor_warranty_months = models.IntegerField(default=12)
    
    # Quality metrics
    confidence_score = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Metadata
    quote_date = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['total_cost']
        indexes = [
            models.Index(fields=['quote_request', 'provider_type']),
            models.Index(fields=['damaged_part', 'total_cost']),
            models.Index(fields=['quote_date']),
            models.Index(fields=['valid_until', 'status']),
        ]
    
    def __str__(self):
        return f"{self.provider_name} - {self.damaged_part.part_name} - £{self.total_cost}"
    
    def save(self, *args, **kwargs):
        # Calculate total cost if not provided
        if not self.total_cost:
            self.total_cost = (
                self.part_cost + 
                self.labor_cost + 
                self.paint_cost + 
                self.additional_costs
            )
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if quote is still valid"""
        return timezone.now() <= self.valid_until and self.status != 'expired'
    
    def days_until_expiry(self):
        """Get number of days until expiry (negative if expired)"""
        delta = self.valid_until.date() - timezone.now().date()
        return delta.days
    
    def get_cost_breakdown(self):
        """Get detailed cost breakdown"""
        return {
            'part_cost': float(self.part_cost),
            'labor_cost': float(self.labor_cost),
            'paint_cost': float(self.paint_cost),
            'additional_costs': float(self.additional_costs),
            'total_cost': float(self.total_cost)
        }
    
    def calculate_price_score(self, market_average):
        """Calculate price competitiveness score (0-100)"""
        if market_average <= 0:
            return 50
        
        ratio = float(self.total_cost) / market_average
        if ratio <= 0.8:
            return 100  # Excellent price
        elif ratio <= 0.9:
            return 80   # Good price
        elif ratio <= 1.1:
            return 60   # Fair price
        elif ratio <= 1.2:
            return 40   # Above average
        else:
            return 20   # Expensive


class PartMarketAverage(models.Model):
    """Model for storing market average calculations and statistics"""
    
    damaged_part = models.OneToOneField(
        DamagedPart, 
        on_delete=models.CASCADE, 
        related_name='market_average'
    )
    
    # Statistical data
    average_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    average_part_cost = models.DecimalField(max_digits=10, decimal_places=2)
    average_labor_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Price range
    min_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    max_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Statistical measures
    standard_deviation = models.DecimalField(max_digits=10, decimal_places=2)
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Data quality metrics
    quote_count = models.IntegerField()
    confidence_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Outlier identification
    outlier_quotes = models.JSONField(default=list, blank=True)
    
    # Metadata
    calculated_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['damaged_part']),
            models.Index(fields=['calculated_date']),
            models.Index(fields=['confidence_level']),
        ]
    
    def __str__(self):
        return f"Market Average - {self.damaged_part.part_name} - £{self.average_total_cost}"
    
    def get_price_range_display(self):
        """Get formatted price range"""
        return f"£{self.min_total_cost} - £{self.max_total_cost}"
    
    def is_high_confidence(self):
        """Check if market data has high confidence"""
        return self.confidence_level >= 70 and self.quote_count >= 3
    
    def get_outlier_quotes(self):
        """Get quotes that are statistical outliers"""
        if not self.outlier_quotes:
            return []
        
        # Return PartQuote objects for outlier quote IDs
        from .models import PartQuote
        outlier_ids = self.outlier_quotes
        return PartQuote.objects.filter(id__in=outlier_ids)
    
    def get_variance_category(self):
        """Categorize price variance"""
        variance = float(self.variance_percentage)
        if variance <= 10:
            return 'low'
        elif variance <= 25:
            return 'moderate'
        else:
            return 'high'


class AssessmentQuoteSummary(models.Model):
    """Model for overall assessment quote management and summaries"""
    
    SUMMARY_STATUS = [
        ('collecting', 'Collecting Quotes'),
        ('analysis', 'Analyzing Quotes'),
        ('ready', 'Ready for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    assessment = models.OneToOneField(
        VehicleAssessment, 
        on_delete=models.CASCADE, 
        related_name='quote_summary'
    )
    status = models.CharField(max_length=20, choices=SUMMARY_STATUS, default='collecting')
    
    # Quote collection metrics
    total_parts_identified = models.IntegerField(default=0)
    parts_with_quotes = models.IntegerField(default=0)
    total_quote_requests = models.IntegerField(default=0)
    quotes_received = models.IntegerField(default=0)
    
    # Cost summaries by provider type
    assessor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dealer_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    independent_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    network_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Market analysis
    market_average_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    recommended_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    potential_savings = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Recommendation
    recommended_provider_mix = models.JSONField(default=dict, blank=True)
    recommendation_reasoning = models.TextField(blank=True)
    
    # Metadata
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    completed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='completed_quote_summaries'
    )
    
    class Meta:
        verbose_name_plural = "Assessment Quote Summaries"
        indexes = [
            models.Index(fields=['assessment']),
            models.Index(fields=['status', 'last_updated']),
            models.Index(fields=['created_date']),
        ]
    
    def __str__(self):
        return f"Quote Summary - {self.assessment.assessment_id}"
    
    def calculate_completion_percentage(self):
        """Calculate quote collection completion percentage"""
        if self.total_parts_identified == 0:
            return 0
        return (self.parts_with_quotes / self.total_parts_identified) * 100
    
    def get_best_provider_total(self):
        """Get the lowest total cost among all providers"""
        totals = [
            self.assessor_total,
            self.dealer_total,
            self.independent_total,
            self.network_total
        ]
        valid_totals = [t for t in totals if t is not None]
        return min(valid_totals) if valid_totals else None
    
    def calculate_potential_savings(self):
        """Calculate potential savings compared to highest quote"""
        totals = [
            self.assessor_total,
            self.dealer_total,
            self.independent_total,
            self.network_total
        ]
        valid_totals = [t for t in totals if t is not None]
        
        if len(valid_totals) < 2:
            return 0
        
        highest = max(valid_totals)
        lowest = min(valid_totals)
        return highest - lowest
    
    def update_summary_metrics(self):
        """Update summary metrics from related data"""
        # Count parts and quotes
        self.total_parts_identified = self.assessment.damaged_parts.count()
        self.parts_with_quotes = self.assessment.damaged_parts.filter(
            quotes__isnull=False
        ).distinct().count()
        
        self.total_quote_requests = self.assessment.part_quote_requests.count()
        self.quotes_received = PartQuote.objects.filter(
            quote_request__assessment=self.assessment
        ).count()
        
        # Calculate provider totals
        provider_totals = {}
        for provider_type in ['assessor', 'dealer', 'independent', 'network']:
            quotes = PartQuote.objects.filter(
                quote_request__assessment=self.assessment,
                provider_type=provider_type,
                status='validated'
            )
            if quotes.exists():
                provider_totals[provider_type] = sum(q.total_cost for q in quotes)
        
        self.assessor_total = provider_totals.get('assessor')
        self.dealer_total = provider_totals.get('dealer')
        self.independent_total = provider_totals.get('independent')
        self.network_total = provider_totals.get('network')
        
        # Calculate market average
        market_averages = PartMarketAverage.objects.filter(
            damaged_part__assessment=self.assessment
        )
        if market_averages.exists():
            self.market_average_total = sum(ma.average_total_cost for ma in market_averages)
        
        # Calculate potential savings
        self.potential_savings = self.calculate_potential_savings()
        
        self.save()


# Quote System Configuration Models

class QuoteSystemConfiguration(models.Model):
    """System-wide configuration for the parts-based quote system"""
    
    # Singleton pattern - only one configuration record
    id = models.AutoField(primary_key=True)
    
    # Cost calculation settings
    default_labor_rate = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=45.00,
        help_text="Default hourly labor rate in GBP"
    )
    paint_cost_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=15.00,
        help_text="Paint cost as percentage of part cost for body panels"
    )
    additional_cost_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        help_text="Additional costs percentage (consumables, shop supplies)"
    )
    
    # Quote request settings
    default_quote_expiry_days = models.IntegerField(
        default=7,
        help_text="Default number of days before quote requests expire"
    )
    minimum_quotes_required = models.IntegerField(
        default=2,
        help_text="Minimum number of quotes required for market analysis"
    )
    confidence_threshold = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum confidence level for market averages (0-100)"
    )
    
    # Provider settings
    enable_assessor_estimates = models.BooleanField(
        default=True,
        help_text="Enable internal assessor estimates"
    )
    enable_dealer_quotes = models.BooleanField(
        default=True,
        help_text="Enable authorized dealer quote requests"
    )
    enable_independent_quotes = models.BooleanField(
        default=True,
        help_text="Enable independent garage quote requests"
    )
    enable_network_quotes = models.BooleanField(
        default=True,
        help_text="Enable insurance network quote requests"
    )
    
    # Recommendation engine settings
    price_weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.40,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for price in recommendation scoring (0.0-1.0)"
    )
    quality_weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.25,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for quality in recommendation scoring (0.0-1.0)"
    )
    timeline_weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.15,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for timeline in recommendation scoring (0.0-1.0)"
    )
    warranty_weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.10,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for warranty in recommendation scoring (0.0-1.0)"
    )
    reliability_weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.10,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight for reliability in recommendation scoring (0.0-1.0)"
    )
    
    # System monitoring settings
    enable_performance_logging = models.BooleanField(
        default=True,
        help_text="Enable detailed performance logging for quote operations"
    )
    log_retention_days = models.IntegerField(
        default=90,
        help_text="Number of days to retain detailed logs"
    )
    enable_health_monitoring = models.BooleanField(
        default=True,
        help_text="Enable system health monitoring and alerts"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User who last updated the configuration"
    )
    
    class Meta:
        verbose_name = "Quote System Configuration"
        verbose_name_plural = "Quote System Configuration"
    
    def __str__(self):
        return f"Quote System Configuration (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration record exists
        if not self.pk and QuoteSystemConfiguration.objects.exists():
            raise ValueError("Only one QuoteSystemConfiguration instance is allowed")
        
        # Validate recommendation weights sum to 1.0
        total_weight = (
            self.price_weight + 
            self.quality_weight + 
            self.timeline_weight + 
            self.warranty_weight + 
            self.reliability_weight
        )
        if abs(float(total_weight) - 1.0) > 0.01:
            raise ValueError("Recommendation weights must sum to 1.0")
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get the current system configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class ProviderConfiguration(models.Model):
    """Configuration for individual provider types"""
    
    PROVIDER_TYPES = [
        ('assessor', 'Assessor Estimates'),
        ('dealer', 'Authorized Dealers'),
        ('independent', 'Independent Garages'),
        ('network', 'Insurance Networks'),
    ]
    
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES, unique=True)
    is_enabled = models.BooleanField(default=True)
    
    # API configuration
    api_endpoint = models.URLField(blank=True, null=True, help_text="API endpoint for provider integration")
    api_key = models.CharField(max_length=255, blank=True, help_text="API key for authentication")
    api_timeout_seconds = models.IntegerField(default=30, help_text="API request timeout in seconds")
    
    # Email configuration
    email_enabled = models.BooleanField(default=False, help_text="Enable email-based quote requests")
    email_template = models.TextField(blank=True, help_text="Email template for quote requests")
    
    # Performance settings
    max_concurrent_requests = models.IntegerField(default=5, help_text="Maximum concurrent requests to this provider")
    retry_attempts = models.IntegerField(default=3, help_text="Number of retry attempts for failed requests")
    retry_delay_seconds = models.IntegerField(default=60, help_text="Delay between retry attempts")
    
    # Quality metrics
    reliability_score = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Provider reliability score (0-100)"
    )
    average_response_time_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=24.00,
        help_text="Average response time in hours"
    )
    
    # Cost adjustments
    cost_multiplier = models.DecimalField(
        max_digits=4, 
        decimal_places=3, 
        default=1.000,
        help_text="Multiplier applied to provider quotes (e.g., 1.1 for 10% markup)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Provider Configuration"
        verbose_name_plural = "Provider Configurations"
        ordering = ['provider_type']
    
    def __str__(self):
        status = "Enabled" if self.is_enabled else "Disabled"
        return f"{self.get_provider_type_display()} - {status}"


class QuoteSystemHealthMetrics(models.Model):
    """System health monitoring for the quote system"""
    
    # Timestamp
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    # Quote request metrics
    total_quote_requests_24h = models.IntegerField(default=0)
    successful_quote_requests_24h = models.IntegerField(default=0)
    failed_quote_requests_24h = models.IntegerField(default=0)
    
    # Quote response metrics
    total_quotes_received_24h = models.IntegerField(default=0)
    average_response_time_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Provider performance
    assessor_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    dealer_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    independent_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    network_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # System performance
    average_parts_identification_time_seconds = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    average_market_calculation_time_seconds = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    average_recommendation_time_seconds = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Error tracking
    api_errors_24h = models.IntegerField(default=0)
    database_errors_24h = models.IntegerField(default=0)
    validation_errors_24h = models.IntegerField(default=0)
    
    # Data quality metrics
    high_confidence_market_averages = models.IntegerField(default=0)
    low_confidence_market_averages = models.IntegerField(default=0)
    outlier_quotes_detected = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Quote System Health Metrics"
        verbose_name_plural = "Quote System Health Metrics"
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"Health Metrics - {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_overall_success_rate(self):
        """Calculate overall system success rate"""
        if self.total_quote_requests_24h == 0:
            return 0
        return (self.successful_quote_requests_24h / self.total_quote_requests_24h) * 100
    
    def get_system_health_status(self):
        """Get overall system health status"""
        success_rate = self.get_overall_success_rate()
        error_rate = (self.api_errors_24h + self.database_errors_24h + self.validation_errors_24h) / max(1, self.total_quote_requests_24h) * 100
        
        if success_rate >= 95 and error_rate <= 1:
            return 'excellent'
        elif success_rate >= 90 and error_rate <= 5:
            return 'good'
        elif success_rate >= 80 and error_rate <= 10:
            return 'fair'
        else:
            return 'poor'


class QuoteSystemAuditLog(models.Model):
    """Audit log for all quote system operations"""
    
    ACTION_TYPES = [
        ('parts_identification', 'Parts Identification'),
        ('quote_request_created', 'Quote Request Created'),
        ('quote_request_dispatched', 'Quote Request Dispatched'),
        ('quote_received', 'Quote Received'),
        ('quote_validated', 'Quote Validated'),
        ('quote_rejected', 'Quote Rejected'),
        ('market_average_calculated', 'Market Average Calculated'),
        ('recommendation_generated', 'Recommendation Generated'),
        ('configuration_updated', 'Configuration Updated'),
        ('provider_enabled', 'Provider Enabled'),
        ('provider_disabled', 'Provider Disabled'),
        ('system_error', 'System Error'),
        ('user_action', 'User Action'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    # Core fields
    timestamp = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    
    # User and session info
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Related objects
    assessment_id = models.CharField(max_length=50, blank=True, db_index=True)
    quote_request_id = models.CharField(max_length=50, blank=True, db_index=True)
    quote_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    
    # Action details
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Performance metrics
    execution_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Quote System Audit Log"
        verbose_name_plural = "Quote System Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action_type']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['assessment_id', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.get_action_type_display()}"
    
    @classmethod
    def log_action(cls, action_type, message, user=None, assessment_id=None, 
                   quote_request_id=None, quote_id=None, severity='info', 
                   details=None, execution_time_ms=None, request=None):
        """Convenience method to create audit log entries"""
        log_entry = cls(
            action_type=action_type,
            severity=severity,
            user=user,
            assessment_id=assessment_id,
            quote_request_id=quote_request_id,
            quote_id=quote_id,
            message=message,
            details=details or {},
            execution_time_ms=execution_time_ms
        )
        
        if request:
            log_entry.session_key = request.session.session_key or ''
            log_entry.ip_address = request.META.get('REMOTE_ADDR')
            log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        log_entry.save()
        return log_entry
