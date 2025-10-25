# models.py - Vehicle Assessment App
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal

# Import external models to avoid lazy references
try:
    from vehicles.models import Vehicle
except ImportError:
    Vehicle = None

try:
    from maintenance_history.models import MaintenanceRecord
except ImportError:
    MaintenanceRecord = None

try:
    from organizations.models import Organization
except ImportError:
    Organization = None


# Custom Manager for VehicleAssessment
class VehicleAssessmentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user', 'vehicle', 'exterior_damage', 'wheels_tires', 
            'interior_damage', 'mechanical_systems', 'electrical_systems',
            'safety_systems', 'frame_structural', 'fluid_systems', 'documentation'
        )
    
    def pending_assessments(self):
        return self.filter(status='pending')
    
    def completed_this_week(self):
        from django.utils import timezone
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        return self.filter(completed_date__gte=week_ago, status='completed')
    
    def total_loss_candidates(self):
        return self.filter(
            models.Q(overall_severity='total_loss') |
            models.Q(uk_write_off_category__in=['cat_a', 'cat_b']) |
            models.Q(south_africa_70_percent_rule=True)
        )
    
    def for_organization(self, organization):
        """Filter assessments for a specific organization"""
        return self.filter(organization=organization)
    
    def for_user_organizations(self, user):
        """Filter assessments for organizations the user belongs to"""
        if user.is_superuser:
            return self.all()
        
        try:
            from organizations.models import Organization
            user_orgs = Organization.objects.filter(
                organization_members__user=user,
                organization_members__is_active=True
            )
            return self.filter(organization__in=user_orgs)
        except ImportError:
            return self.filter(user=user)
    
    def insurance_assessments(self):
        """Filter assessments for insurance organizations"""
        return self.filter(
            models.Q(assessment_type='insurance_claim') |
            models.Q(organization__is_insurance_provider=True)
        )


class VehicleAssessment(models.Model):
    """Main assessment model linking to user, vehicle and maintenance history"""
    
    # Assessment Types
    ASSESSMENT_TYPES = [
        ('crash', 'Crash Assessment'),
        ('pre_purchase', 'Pre-Purchase Assessment'),
        ('periodic', 'Periodic Assessment'),
        ('insurance_claim', 'Insurance Claim'),
        ('total_loss', 'Total Loss Assessment'),
    ]
    
    # UK Write-off Categories
    UK_CATEGORIES = [
        ('cat_a', 'Category A - Total Loss/Scrap Only'),
        ('cat_b', 'Category B - Break for Parts Only'),
        ('cat_s', 'Category S - Structural Damage'),
        ('cat_n', 'Category N - Non-Structural Damage'),
        ('not_applicable', 'Not Applicable'),
    ]
    
    # Assessment Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Agent Status Choices
    AGENT_STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
        ('on_hold', 'On Hold'),
    ]
    
    # Damage Severity
    SEVERITY_CHOICES = [
        ('cosmetic', 'Cosmetic'),
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('total_loss', 'Total Loss'),
    ]
    
    # Core Assessment Information
    assessment_id = models.CharField(max_length=50, unique=True, db_index=True)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related Models
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assessments')
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='assessments',
        null=True,
        blank=True,
        help_text="Organization this assessment is being conducted for"
    )
    maintenance_history = models.ManyToManyField(MaintenanceRecord, blank=True)
    
    # Assessment Details
    assessment_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    assessor_name = models.CharField(max_length=100)
    assessor_certification = models.CharField(max_length=100, blank=True)
    
    # Location and Context
    incident_location = models.CharField(max_length=255, blank=True)
    incident_date = models.DateTimeField(null=True, blank=True)
    weather_conditions = models.CharField(max_length=100, blank=True)
    
    # Overall Assessment
    overall_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    uk_write_off_category = models.CharField(max_length=20, choices=UK_CATEGORIES, blank=True)
    south_africa_70_percent_rule = models.BooleanField(default=False, help_text="Exceeds 70% repair cost threshold")
    
    # Financial Information
    estimated_repair_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vehicle_market_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salvage_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Assessment Notes
    overall_notes = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Agent-specific fields for insurance workflow
    assigned_agent = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_assessments',
        help_text="Insurance agent assigned to review this assessment"
    )
    agent_status = models.CharField(
        max_length=20, 
        choices=AGENT_STATUS_CHOICES, 
        default='pending_review',
        help_text="Current status of agent review process"
    )
    agent_notes = models.TextField(
        blank=True,
        help_text="Notes and comments from the assigned insurance agent"
    )
    review_deadline = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Deadline for agent review completion"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager
    objects = VehicleAssessmentManager()
    
    class Meta:
        ordering = ['-assessment_date']
        indexes = [
            models.Index(fields=['assessment_id']),
            models.Index(fields=['status', 'assessment_date']),
            models.Index(fields=['vehicle', 'assessment_date']),
        ]
    
    def __str__(self):
        return f"Assessment {self.assessment_id} - {self.vehicle}"
    
    def get_organization_display(self):
        """Get formatted organization display with type"""
        if self.organization:
            return f"{self.organization.name} ({self.organization.get_organization_type_display()})"
        return "No Organization"
    
    def is_insurance_assessment(self):
        """Check if this is an insurance-related assessment"""
        return (
            self.assessment_type == 'insurance_claim' or 
            (self.organization and self.organization.is_insurance_provider)
        )
    
    def get_workflow_permissions(self):
        """Get workflow permissions based on organization type"""
        if not self.organization:
            return {'can_approve': False, 'requires_agent_review': False}
        
        return {
            'can_approve': self.organization.organization_type in ['insurance', 'fleet'],
            'requires_agent_review': self.organization.is_insurance_provider,
            'auto_approve_threshold': getattr(self.organization, 'insurance_details', None) and 
                                    self.organization.insurance_details.auto_approve_low_risk
        }


class ExteriorBodyDamage(models.Model):
    """Exterior body damage assessment points"""
    
    DAMAGE_SEVERITY = [
        ('none', 'No Damage'),
        ('light', 'Light Damage'),
        ('moderate', 'Moderate Damage'),
        ('severe', 'Severe Damage'),
        ('destroyed', 'Destroyed'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='exterior_damage')
    
    # Front End Assessment (Points 1-10)
    front_bumper = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_bumper_notes = models.TextField(blank=True)
    
    hood = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    hood_notes = models.TextField(blank=True)
    
    front_grille = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_grille_notes = models.TextField(blank=True)
    
    headlight_housings = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    headlight_housings_notes = models.TextField(blank=True)
    
    headlight_lenses = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    headlight_lenses_notes = models.TextField(blank=True)
    
    front_fenders = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_fenders_notes = models.TextField(blank=True)
    
    front_quarter_panels = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_quarter_panels_notes = models.TextField(blank=True)
    
    fog_light_housings = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    fog_light_housings_notes = models.TextField(blank=True)
    
    license_plate_bracket = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    license_plate_bracket_notes = models.TextField(blank=True)
    
    front_spoiler_air_dam = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_spoiler_air_dam_notes = models.TextField(blank=True)
    
    # Side Panel Assessment (Points 11-20)
    driver_side_door = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    driver_side_door_notes = models.TextField(blank=True)
    
    passenger_side_door = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    passenger_side_door_notes = models.TextField(blank=True)
    
    rear_doors = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_doors_notes = models.TextField(blank=True)
    
    door_frames = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    door_frames_notes = models.TextField(blank=True)
    
    side_mirrors = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    side_mirrors_notes = models.TextField(blank=True)
    
    side_moldings_trim = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    side_moldings_trim_notes = models.TextField(blank=True)
    
    rocker_panels = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rocker_panels_notes = models.TextField(blank=True)
    
    wheel_well_liners = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    wheel_well_liners_notes = models.TextField(blank=True)
    
    side_windows = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    side_windows_notes = models.TextField(blank=True)
    
    door_handles = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    door_handles_notes = models.TextField(blank=True)
    
    # Rear End Assessment (Points 21-30)
    rear_bumper = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_bumper_notes = models.TextField(blank=True)
    
    trunk_hatch = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    trunk_hatch_notes = models.TextField(blank=True)
    
    rear_quarter_panels = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_quarter_panels_notes = models.TextField(blank=True)
    
    taillight_housings = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    taillight_housings_notes = models.TextField(blank=True)
    
    taillight_lenses = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    taillight_lenses_notes = models.TextField(blank=True)
    
    rear_window = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_window_notes = models.TextField(blank=True)
    
    rear_spoiler = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_spoiler_notes = models.TextField(blank=True)
    
    exhaust_tips = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    exhaust_tips_notes = models.TextField(blank=True)
    
    rear_license_plate_area = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_license_plate_area_notes = models.TextField(blank=True)
    
    backup_camera = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    backup_camera_notes = models.TextField(blank=True)
    
    # Roof and Pillars (Points 31-38)
    roof_panel = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    roof_panel_notes = models.TextField(blank=True)
    
    a_pillars = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    a_pillars_notes = models.TextField(blank=True)
    
    b_pillars = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    b_pillars_notes = models.TextField(blank=True)
    
    c_pillars = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    c_pillars_notes = models.TextField(blank=True)
    
    d_pillars = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    d_pillars_notes = models.TextField(blank=True)
    
    roof_rails = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    roof_rails_notes = models.TextField(blank=True)
    
    sunroof_moonroof = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    sunroof_moonroof_notes = models.TextField(blank=True)
    
    antenna = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    antenna_notes = models.TextField(blank=True)


class WheelsAndTires(models.Model):
    """Wheels and tires assessment points (39-50)"""
    
    DAMAGE_SEVERITY = [
        ('none', 'No Damage'),
        ('light', 'Light Damage'),
        ('moderate', 'Moderate Damage'),
        ('severe', 'Severe Damage'),
        ('destroyed', 'Destroyed'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='wheels_tires')
    
    # Tires (Points 39-42)
    front_left_tire = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_left_tire_notes = models.TextField(blank=True)
    
    front_right_tire = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_right_tire_notes = models.TextField(blank=True)
    
    rear_left_tire = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_left_tire_notes = models.TextField(blank=True)
    
    rear_right_tire = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_right_tire_notes = models.TextField(blank=True)
    
    # Wheels (Points 43-46)
    front_left_wheel = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_left_wheel_notes = models.TextField(blank=True)
    
    front_right_wheel = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    front_right_wheel_notes = models.TextField(blank=True)
    
    rear_left_wheel = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_left_wheel_notes = models.TextField(blank=True)
    
    rear_right_wheel = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_right_wheel_notes = models.TextField(blank=True)
    
    # Additional Components (Points 47-50)
    spare_tire = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    spare_tire_notes = models.TextField(blank=True)
    
    wheel_lug_nuts = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    wheel_lug_nuts_notes = models.TextField(blank=True)
    
    tire_pressure_sensors = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    tire_pressure_sensors_notes = models.TextField(blank=True)
    
    center_caps = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    center_caps_notes = models.TextField(blank=True)


class InteriorDamage(models.Model):
    """Interior damage assessment points (51-69)"""
    
    DAMAGE_SEVERITY = [
        ('none', 'No Damage'),
        ('light', 'Light Damage'),
        ('moderate', 'Moderate Damage'),
        ('severe', 'Severe Damage'),
        ('destroyed', 'Destroyed'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='interior_damage')
    
    # Seating and Upholstery (Points 51-57)
    driver_seat = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    driver_seat_notes = models.TextField(blank=True)
    
    passenger_seat = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    passenger_seat_notes = models.TextField(blank=True)
    
    rear_seats = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    rear_seats_notes = models.TextField(blank=True)
    
    seat_belts = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    seat_belts_notes = models.TextField(blank=True)
    
    headrests = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    headrests_notes = models.TextField(blank=True)
    
    armrests = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    armrests_notes = models.TextField(blank=True)
    
    floor_mats = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    floor_mats_notes = models.TextField(blank=True)
    
    # Dashboard and Controls (Points 58-65)
    dashboard = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    dashboard_notes = models.TextField(blank=True)
    
    steering_wheel = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    steering_wheel_notes = models.TextField(blank=True)
    
    instrument_cluster = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    instrument_cluster_notes = models.TextField(blank=True)
    
    center_console = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    center_console_notes = models.TextField(blank=True)
    
    climate_controls = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    climate_controls_notes = models.TextField(blank=True)
    
    radio_infotainment = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    radio_infotainment_notes = models.TextField(blank=True)
    
    glove_compartment = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    glove_compartment_notes = models.TextField(blank=True)
    
    door_panels = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    door_panels_notes = models.TextField(blank=True)
    
    # Glass and Visibility (Points 66-69)
    windshield = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    windshield_notes = models.TextField(blank=True)
    
    side_windows_interior = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    side_windows_interior_notes = models.TextField(blank=True)
    
    interior_mirrors = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    interior_mirrors_notes = models.TextField(blank=True)
    
    visors = models.CharField(max_length=20, choices=DAMAGE_SEVERITY, default='none')
    visors_notes = models.TextField(blank=True)


class MechanicalSystems(models.Model):
    """Mechanical systems assessment points (70-89)"""
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('failed', 'Failed'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='mechanical_systems')
    
    # Engine Bay (Points 70-77)
    engine_block = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    engine_block_notes = models.TextField(blank=True)
    
    radiator = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    radiator_notes = models.TextField(blank=True)
    
    battery = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    battery_notes = models.TextField(blank=True)
    
    air_filter_housing = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    air_filter_housing_notes = models.TextField(blank=True)
    
    belts_and_hoses = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    belts_and_hoses_notes = models.TextField(blank=True)
    
    fluid_reservoirs = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    fluid_reservoirs_notes = models.TextField(blank=True)
    
    wiring_harnesses = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    wiring_harnesses_notes = models.TextField(blank=True)
    
    engine_mounts = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    engine_mounts_notes = models.TextField(blank=True)
    
    # Suspension and Steering (Points 78-84)
    shock_absorbers = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    shock_absorbers_notes = models.TextField(blank=True)
    
    struts = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    struts_notes = models.TextField(blank=True)
    
    springs = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    springs_notes = models.TextField(blank=True)
    
    control_arms = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    control_arms_notes = models.TextField(blank=True)
    
    tie_rods = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    tie_rods_notes = models.TextField(blank=True)
    
    steering_rack = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    steering_rack_notes = models.TextField(blank=True)
    
    brake_lines = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    brake_lines_notes = models.TextField(blank=True)
    
    # Exhaust System (Points 85-89)
    exhaust_manifold = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    exhaust_manifold_notes = models.TextField(blank=True)
    
    catalytic_converter = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    catalytic_converter_notes = models.TextField(blank=True)
    
    muffler = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    muffler_notes = models.TextField(blank=True)
    
    exhaust_pipes = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    exhaust_pipes_notes = models.TextField(blank=True)
    
    heat_shields = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    heat_shields_notes = models.TextField(blank=True)


class ElectricalSystems(models.Model):
    """Electrical systems assessment points (90-98)"""
    
    FUNCTION_STATUS = [
        ('working', 'Working'),
        ('intermittent', 'Intermittent'),
        ('not_working', 'Not Working'),
        ('not_tested', 'Not Tested'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='electrical_systems')
    
    # Lighting and Electronics (Points 90-98)
    headlight_function = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    headlight_function_notes = models.TextField(blank=True)
    
    taillight_function = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    taillight_function_notes = models.TextField(blank=True)
    
    interior_lighting = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    interior_lighting_notes = models.TextField(blank=True)
    
    warning_lights = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    warning_lights_notes = models.TextField(blank=True)
    
    horn = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    horn_notes = models.TextField(blank=True)
    
    power_windows = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    power_windows_notes = models.TextField(blank=True)
    
    power_locks = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    power_locks_notes = models.TextField(blank=True)
    
    air_conditioning = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    air_conditioning_notes = models.TextField(blank=True)
    
    heating_system = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    heating_system_notes = models.TextField(blank=True)


class SafetySystems(models.Model):
    """Safety systems assessment points (99-104)"""
    
    FUNCTION_STATUS = [
        ('working', 'Working'),
        ('fault', 'Fault Detected'),
        ('deployed', 'Deployed/Activated'),
        ('not_working', 'Not Working'),
        ('not_tested', 'Not Tested'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='safety_systems')
    
    # Safety Systems (Points 99-104)
    airbag_systems = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    airbag_systems_notes = models.TextField(blank=True)
    
    abs_system = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    abs_system_notes = models.TextField(blank=True)
    
    stability_control = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    stability_control_notes = models.TextField(blank=True)
    
    parking_sensors = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    parking_sensors_notes = models.TextField(blank=True)
    
    backup_camera_system = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    backup_camera_system_notes = models.TextField(blank=True)
    
    emergency_brake = models.CharField(max_length=20, choices=FUNCTION_STATUS, default='working')
    emergency_brake_notes = models.TextField(blank=True)


class FrameAndStructural(models.Model):
    """Frame and structural assessment points (105-110)"""
    
    STRUCTURAL_STATUS = [
        ('intact', 'Intact'),
        ('minor_damage', 'Minor Damage'),
        ('moderate_damage', 'Moderate Damage'),
        ('severe_damage', 'Severe Damage'),
        ('compromised', 'Structurally Compromised'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='frame_structural')
    
    # Structural Components (Points 105-110)
    frame_rails = models.CharField(max_length=20, choices=STRUCTURAL_STATUS, default='intact')
    frame_rails_notes = models.TextField(blank=True)
    
    cross_members = models.CharField(max_length=20, choices=STRUCTURAL_STATUS, default='intact')
    cross_members_notes = models.TextField(blank=True)
    
    firewall = models.CharField(max_length=20, choices=STRUCTURAL_STATUS, default='intact')
    firewall_notes = models.TextField(blank=True)
    
    floor_pans = models.CharField(max_length=20, choices=STRUCTURAL_STATUS, default='intact')
    floor_pans_notes = models.TextField(blank=True)
    
    door_jambs = models.CharField(max_length=20, choices=STRUCTURAL_STATUS, default='intact')
    door_jambs_notes = models.TextField(blank=True)
    
    trunk_floor = models.CharField(max_length=20, choices=STRUCTURAL_STATUS, default='intact')
    trunk_floor_notes = models.TextField(blank=True)


class FluidSystems(models.Model):
    """Fluid systems assessment points (111-116)"""
    
    FLUID_CONDITION = [
        ('good', 'Good'),
        ('low', 'Low Level'),
        ('contaminated', 'Contaminated'),
        ('leaking', 'Leaking'),
        ('empty', 'Empty'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='fluid_systems')
    
    # Fluid Systems (Points 111-116)
    engine_oil = models.CharField(max_length=20, choices=FLUID_CONDITION, default='good')
    engine_oil_notes = models.TextField(blank=True)
    
    transmission_fluid = models.CharField(max_length=20, choices=FLUID_CONDITION, default='good')
    transmission_fluid_notes = models.TextField(blank=True)
    
    brake_fluid = models.CharField(max_length=20, choices=FLUID_CONDITION, default='good')
    brake_fluid_notes = models.TextField(blank=True)
    
    coolant = models.CharField(max_length=20, choices=FLUID_CONDITION, default='good')
    coolant_notes = models.TextField(blank=True)
    
    power_steering_fluid = models.CharField(max_length=20, choices=FLUID_CONDITION, default='good')
    power_steering_fluid_notes = models.TextField(blank=True)
    
    windshield_washer_fluid = models.CharField(max_length=20, choices=FLUID_CONDITION, default='good')
    windshield_washer_fluid_notes = models.TextField(blank=True)


class DocumentationAndIdentification(models.Model):
    """Documentation and identification assessment points (117-120)"""
    
    DOCUMENT_STATUS = [
        ('present', 'Present and Readable'),
        ('damaged', 'Present but Damaged'),
        ('missing', 'Missing'),
        ('tampered', 'Evidence of Tampering'),
    ]
    
    assessment = models.OneToOneField(VehicleAssessment, on_delete=models.CASCADE, related_name='documentation')
    
    # Documentation (Points 117-120)
    vin_plate = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='present')
    vin_plate_notes = models.TextField(blank=True)
    
    door_jamb_stickers = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='present')
    door_jamb_stickers_notes = models.TextField(blank=True)
    
    emissions_stickers = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='present')
    emissions_stickers_notes = models.TextField(blank=True)
    
    maintenance_records = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='present')
    maintenance_records_notes = models.TextField(blank=True)



    
    def __str__(self):
        return f"Workflow {self.assessment.assessment_id} - {self.step} ({self.status})"


class AgentAssignment(models.Model):
    """Agent assignment model to link agents with assessments"""
    
    ASSIGNMENT_ROLES = [
        ('primary_reviewer', 'Primary Reviewer'),
        ('secondary_reviewer', 'Secondary Reviewer'),
        ('specialist', 'Specialist'),
        ('supervisor', 'Supervisor'),
        ('final_approver', 'Final Approver'),
    ]
    
    ASSIGNMENT_STATUS = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reassigned', 'Reassigned'),
        ('declined', 'Declined'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_assignments')
    assessment = models.ForeignKey(VehicleAssessment, on_delete=models.CASCADE, related_name='agent_assignments')
    role = models.CharField(max_length=20, choices=ASSIGNMENT_ROLES, default='primary_reviewer')
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='assigned')
    assigned_date = models.DateTimeField(auto_now_add=True)
    accepted_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    is_primary = models.BooleanField(default=True)
    
    # Assignment metadata
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments_made')
    deadline = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['agent', 'assessment', 'role']
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['assessment', 'is_primary']),
        ]
    
    def __str__(self):
        return f"{self.agent.username} - {self.assessment.assessment_id} ({self.role})"


class AssessmentPhoto(models.Model):
    """Photos and media attachments for assessments"""
    
    PHOTO_CATEGORIES = [
        ('overall', 'Overall Vehicle'),
        ('damage', 'Damage Detail'),
        ('interior', 'Interior'),
        ('engine', 'Engine Bay'),
        ('undercarriage', 'Undercarriage'),
        ('documents', 'Documentation'),
        ('vin', 'VIN Plate'),
        ('odometer', 'Odometer Reading'),
        ('other', 'Other'),
    ]
    
    # Assessment section reference choices for linking photos to specific assessment points
    SECTION_REFERENCE_CHOICES = [
        ('exterior_damage', 'Exterior Body Damage'),
        ('wheels_tires', 'Wheels and Tires'),
        ('interior_damage', 'Interior Damage'),
        ('mechanical_systems', 'Mechanical Systems'),
        ('electrical_systems', 'Electrical Systems'),
        ('safety_systems', 'Safety Systems'),
        ('frame_structural', 'Frame and Structural'),
        ('fluid_systems', 'Fluid Systems'),
        ('documentation', 'Documentation and Identification'),
        ('overall', 'Overall Vehicle'),
    ]
    
    assessment = models.ForeignKey(VehicleAssessment, on_delete=models.CASCADE, related_name='photos')
    category = models.CharField(max_length=20, choices=PHOTO_CATEGORIES, blank=True)
    image = models.ImageField(upload_to='assessment_photos/%Y/%m/%d/', blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    
    # Section linking fields for enhanced photo organization
    section_reference = models.CharField(
        max_length=30, 
        choices=SECTION_REFERENCE_CHOICES, 
        null=True, 
        blank=True,
        help_text="Links photo to specific assessment section"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Indicates if this is the main photo for the assessment section"
    )
    damage_point_id = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Specific damage location reference (e.g., 'front_bumper', 'driver_side_door')"
    )
    
    # Metadata
    taken_at = models.DateTimeField(auto_now_add=True)
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    device_info = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['section_reference', 'is_primary', 'category', 'taken_at']
        indexes = [
            models.Index(fields=['assessment', 'section_reference']),
            models.Index(fields=['section_reference', 'is_primary']),
            models.Index(fields=['damage_point_id']),
        ]


class AssessmentReport(models.Model):
    """Generated assessment reports and documents"""
    
    REPORT_TYPES = [
        ('preliminary', 'Preliminary Assessment'),
        ('detailed', 'Detailed Assessment'),
        ('insurance_claim', 'Insurance Claim Report'),
        ('pre_purchase', 'Pre-Purchase Report'),
        ('expert_witness', 'Expert Witness Report'),
        ('total_loss', 'Total Loss Assessment'),
    ]
    
    REPORT_STATUS = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Client'),
        ('disputed', 'Disputed'),
    ]
    
    assessment = models.ForeignKey(VehicleAssessment, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='draft')
    
    # Report Content
    title = models.CharField(max_length=200)
    executive_summary = models.TextField()
    detailed_findings = models.TextField()
    recommendations = models.TextField()
    
    # Financial Summary
    total_damage_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    repair_cost_breakdown = models.JSONField(default=dict, blank=True)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Report Generation
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reports')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # File Storage
    pdf_report = models.FileField(upload_to='assessment_reports/%Y/%m/', null=True, blank=True)
    
    class Meta:
        ordering = ['-generated_at']


class AssessmentComment(models.Model):
    """Comments and notes on assessments from various stakeholders"""
    
    COMMENT_TYPES = [
        ('internal', 'Internal Note'),
        ('customer', 'Customer Communication'),
        ('adjuster', 'Adjuster Note'),
        ('repair_shop', 'Repair Shop Input'),
        ('expert', 'Expert Opinion'),
        ('dispute', 'Dispute Resolution'),
    ]
    
    assessment = models.ForeignKey(VehicleAssessment, on_delete=models.CASCADE, related_name='comments')
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPES)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Internal flags
    is_important = models.BooleanField(default=False)
    requires_action = models.BooleanField(default=False)
    is_customer_visible = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']


class AssessmentWorkflow(models.Model):
    """Workflow tracking for assessments"""
    
    WORKFLOW_STEPS = [
        ('submitted', 'Assessment Submitted'),
        ('assigned', 'Assigned to Assessor'),
        ('photos_uploaded', 'Photos Uploaded'),
        ('ai_analysis_complete', 'AI Analysis Complete'),
        ('human_review', 'Human Review'),
        ('quality_check', 'Quality Check'),
        ('customer_notification', 'Customer Notified'),
        ('insurance_submitted', 'Submitted to Insurance'),
        ('completed', 'Assessment Completed'),
        ('disputed', 'Assessment Disputed'),
        ('revised', 'Assessment Revised'),
        ('closed', 'Assessment Closed'),
    ]
    
    assessment = models.ForeignKey(VehicleAssessment, on_delete=models.CASCADE, related_name='workflow_steps')
    step = models.CharField(max_length=30, choices=WORKFLOW_STEPS)
    completed_at = models.DateTimeField(auto_now_add=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Time spent on this step")
    
    class Meta:
        ordering = ['assessment', 'completed_at']


class RepairEstimate(models.Model):
    """Repair estimates from different sources"""
    
    ESTIMATE_SOURCES = [
        ('ai_generated', 'AI Generated'),
        ('assessor', 'Professional Assessor'),
        ('repair_shop', 'Repair Shop'),
        ('dealer', 'Dealer Service'),
        ('independent', 'Independent Mechanic'),
        ('insurance', 'Insurance Adjuster'),
    ]
    
    ESTIMATE_STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revised', 'Revised'),
    ]
    
    assessment = models.ForeignKey(VehicleAssessment, on_delete=models.CASCADE, related_name='repair_estimates')
    source_type = models.CharField(max_length=20, choices=ESTIMATE_SOURCES)
    status = models.CharField(max_length=20, choices=ESTIMATE_STATUS, default='draft')
    
    # Estimate Details
    shop_name = models.CharField(max_length=200, blank=True)
    shop_contact = models.CharField(max_length=200, blank=True)
    estimate_number = models.CharField(max_length=50, blank=True)
    
    # Cost Breakdown
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    paint_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_costs = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timing
    estimated_repair_days = models.PositiveIntegerField(null=True, blank=True)
    parts_availability_days = models.PositiveIntegerField(null=True, blank=True)
    
    # Detailed breakdown
    repair_items = models.JSONField(default=list, help_text="Detailed list of repair items with costs")
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['total_cost']


class AssessmentIntegration(models.Model):
    """Integration with external systems"""
    
    INTEGRATION_TYPES = [
        ('insurance_system', 'Insurance System'),
        ('dvla', 'DVLA System'),
        ('hpi_check', 'HPI Check'),
        ('vin_decoder', 'VIN Decoder'),
        ('parts_system', 'Parts Pricing System'),
        ('repair_network', 'Repair Network'),
        ('rental_car', 'Rental Car System'),
        ('towing', 'Towing Service'),
    ]
    
    INTEGRATION_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]
    
    assessment = models.ForeignKey(VehicleAssessment, on_delete=models.CASCADE, related_name='integrations')
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    status = models.CharField(max_length=20, choices=INTEGRATION_STATUS, default='pending')
    
    # Integration Details
    external_reference = models.CharField(max_length=100, blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-initiated_at']








# Signals for automation
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=VehicleAssessment)
def create_related_assessment_objects(sender, instance, created, **kwargs):
    """Automatically create related assessment objects when a new assessment is created"""
    if created:
        # Create all related assessment detail objects
        ExteriorBodyDamage.objects.create(assessment=instance)
        WheelsAndTires.objects.create(assessment=instance)
        InteriorDamage.objects.create(assessment=instance)
        MechanicalSystems.objects.create(assessment=instance)
        ElectricalSystems.objects.create(assessment=instance)
        SafetySystems.objects.create(assessment=instance)
        FrameAndStructural.objects.create(assessment=instance)
        FluidSystems.objects.create(assessment=instance)
        DocumentationAndIdentification.objects.create(assessment=instance)
        
        # Create initial workflow step
        AssessmentWorkflow.objects.create(
            assessment=instance,
            step='submitted',
            notes='Assessment submitted to system',
            completed_by=instance.user
        )

@receiver(post_save, sender=VehicleAssessment)
def update_assessment_status(sender, instance, **kwargs):
    """Update assessment status based on completion criteria"""
    if instance.status != 'completed' and instance.completed_date:
        instance.status = 'completed'
        instance.save(update_fields=['status'])
        
        # Create completion workflow step
        AssessmentWorkflow.objects.create(
            assessment=instance,
            step='completed',
            notes='Assessment automatically marked as completed',
            completed_by=instance.user
        )