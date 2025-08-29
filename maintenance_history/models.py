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


def maintenance_image_upload_path(instance, filename):
    """Generate upload path for maintenance images"""
    return f'maintenance/{instance.vehicle.vin}/{instance.date_performed.strftime("%Y-%m-%d")}_{filename}'


class MaintenanceRecord(models.Model):
    IMAGE_TYPE_CHOICES = [
        ('before', 'Before Service'),
        ('during', 'During Service'),
        ('after', 'After Service'),
        ('parts', 'Parts/Components'),
        ('tools', 'Tools Used'),
        ('damage', 'Damage/Issue Found'),
        ('repair', 'Repair Process'),
        ('completion', 'Work Completion'),
        ('other', 'Other'),
    ]

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
    
    # Image fields for proof of work
    service_image = models.ImageField(
        upload_to=maintenance_image_upload_path,
        blank=True,
        null=True,
        verbose_name="Service Image",
        help_text="Upload an image as proof of service work performed"
    )
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPE_CHOICES,
        blank=True,
        verbose_name="Image Type",
        help_text="Select what type of image this is"
    )
    image_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Image Description",
        help_text="Brief description of what the image shows"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_performed']
        verbose_name = "Maintenance Record"
        verbose_name_plural = "Maintenance Records"

    def __str__(self):
        return f"{self.vehicle.vin} - {self.date_performed.strftime('%Y-%m-%d')}"
    
    @property
    def has_service_image(self):
        """Check if maintenance record has a service image attached"""
        return bool(self.service_image)
    
    @property
    def image_type_display(self):
        """Get the display name for the image type"""
        return dict(self.IMAGE_TYPE_CHOICES).get(self.image_type, '')

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
    vehicle_health_index = models.CharField(max_length=50, blank=True, verbose_name="Vehicle Health Index")
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


class Inspections(models.Model):
    """
    50-Point Quarterly Vehicle Health Inspection Checklist Form
    Used by technicians to perform detailed vehicle inspections
    """
    
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable'),
        ('minor', 'Minor Issue'),
        ('major', 'Major Issue'),
    ]
    
    # Link to the main inspection record
    inspection = models.OneToOneField(
        Inspection, 
        on_delete=models.CASCADE, 
        related_name='inspections_form',
        verbose_name="Related Inspection"
    )
    
    # Technician performing the inspection
    technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='inspections_forms',
        verbose_name="Inspecting Technician"
    )
    
    # Inspection metadata
    inspection_date = models.DateTimeField(default=timezone.now, verbose_name="Inspection Date/Time")
    mileage_at_inspection = models.PositiveIntegerField(verbose_name="Vehicle Mileage")
    
    # 1. Engine & Powertrain (Points 1-10)
    engine_oil_level = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Engine oil level & quality")
    oil_filter_condition = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Oil filter condition")
    coolant_level = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Coolant level & leaks")
    drive_belts = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Drive belts for cracks/wear")
    hoses_condition = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Hoses for leaks or soft spots")
    air_filter = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Air filter condition")
    cabin_air_filter = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Cabin air filter condition")
    transmission_fluid = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Transmission fluid level & leaks")
    engine_mounts = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Engine/transmission mounts")
    fluid_leaks = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Fluid leaks under engine & gearbox")
    
    # 2. Electrical & Battery (Points 11-15)
    battery_voltage = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Battery voltage & charging system")
    battery_terminals = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Battery terminals for corrosion")
    alternator_output = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Alternator output")
    starter_motor = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Starter motor performance")
    fuses_relays = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="All fuses and relays")
    
    # 3. Brakes & Suspension (Points 16-22)
    brake_pads = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Brake pads/shoes thickness")
    brake_discs = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Brake discs/drums damage/warping")
    brake_fluid = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Brake fluid level & condition")
    parking_brake = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Parking brake function")
    shocks_struts = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Shocks/struts for leaks")
    suspension_bushings = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Suspension bushings & joints")
    wheel_bearings = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Wheel bearings for noise/play")
    
    # 4. Steering & Tires (Points 23-28)
    steering_response = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Steering response & play")
    steering_fluid = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Steering fluid level & leaks")
    tire_tread_depth = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Tire tread depth (>5/32\")")
    tire_pressure = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Tire pressure (all tires + spare)")
    tire_wear_patterns = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Tire wear patterns")
    wheels_rims = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Wheels & rims for damage")
    
    # 5. Exhaust & Emissions (Points 29-31)
    exhaust_system = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Exhaust for leaks/damage")
    catalytic_converter = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Catalytic converter/muffler condition")
    exhaust_warning_lights = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="No exhaust warning lights")
    
    # 6. Safety Equipment (Points 32-36)
    seat_belts = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Seat belts operation & condition")
    airbags = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Airbags (warning light off)")
    horn_function = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Horn function")
    first_aid_kit = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="First-aid kit contents")
    warning_triangle = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Warning triangle/reflective vest present")
    
    # 7. Lighting & Visibility (Points 37-44)
    headlights = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Headlights (low/high beam)")
    brake_lights = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Brake/reverse/fog lights")
    turn_signals = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Turn signals & hazard lights")
    interior_lights = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Interior dome/courtesy lights")
    windshield = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Windshield for cracks/chips")
    wiper_blades = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Wiper blades & washer spray")
    rear_defogger = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Rear defogger/heater operation")
    mirrors = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Mirrors adjustment & condition")
    
    # 8. HVAC & Interior (Points 45-48)
    air_conditioning = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Air conditioning & heating performance")
    ventilation = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Ventilation airflow")
    seat_adjustments = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Seat adjustments & seat heaters")
    power_windows = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Power windows & locks")
    
    # 9. Technology & Driver Assist (Points 49-50)
    infotainment_system = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Infotainment system & Bluetooth/USB")
    rear_view_camera = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True, verbose_name="Rear-view camera/parking sensors")
    
    # Additional notes for each section
    engine_notes = models.TextField(blank=True, verbose_name="Engine & Powertrain Notes")
    electrical_notes = models.TextField(blank=True, verbose_name="Electrical & Battery Notes")
    brakes_notes = models.TextField(blank=True, verbose_name="Brakes & Suspension Notes")
    steering_notes = models.TextField(blank=True, verbose_name="Steering & Tires Notes")
    exhaust_notes = models.TextField(blank=True, verbose_name="Exhaust & Emissions Notes")
    safety_notes = models.TextField(blank=True, verbose_name="Safety Equipment Notes")
    lighting_notes = models.TextField(blank=True, verbose_name="Lighting & Visibility Notes")
    hvac_notes = models.TextField(blank=True, verbose_name="HVAC & Interior Notes")
    technology_notes = models.TextField(blank=True, verbose_name="Technology & Driver Assist Notes")
    
    # Overall inspection summary
    overall_notes = models.TextField(blank=True, verbose_name="Overall Inspection Notes")
    recommendations = models.TextField(blank=True, verbose_name="Recommendations for Future Maintenance")
    
    # Form completion tracking
    is_completed = models.BooleanField(default=False, verbose_name="Inspection Form Completed")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completion Date/Time")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-inspection_date']
        verbose_name = "Inspections Form"
        verbose_name_plural = "Inspections Forms"
    
    def __str__(self):
        return f"Inspections - {self.inspection.inspection_number} ({self.inspection.vehicle.vin})"
    
    def save(self, *args, **kwargs):
        # Set completion timestamp when form is marked as completed
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Auto-update the related Inspection record with calculated health index
        if self.is_completed:
            self._update_inspection_record()
    
    @property
    def total_points_checked(self):
        """Count how many inspection points have been checked (not empty)"""
        inspection_fields = [
            'engine_oil_level', 'oil_filter_condition', 'coolant_level', 'drive_belts', 'hoses_condition',
            'air_filter', 'cabin_air_filter', 'transmission_fluid', 'engine_mounts', 'fluid_leaks',
            'battery_voltage', 'battery_terminals', 'alternator_output', 'starter_motor', 'fuses_relays',
            'brake_pads', 'brake_discs', 'brake_fluid', 'parking_brake', 'shocks_struts',
            'suspension_bushings', 'wheel_bearings', 'steering_response', 'steering_fluid', 'tire_tread_depth',
            'tire_pressure', 'tire_wear_patterns', 'wheels_rims', 'exhaust_system', 'catalytic_converter',
            'exhaust_warning_lights', 'seat_belts', 'airbags', 'horn_function', 'first_aid_kit',
            'warning_triangle', 'headlights', 'brake_lights', 'turn_signals', 'interior_lights',
            'windshield', 'wiper_blades', 'rear_defogger', 'mirrors', 'air_conditioning',
            'ventilation', 'seat_adjustments', 'power_windows', 'infotainment_system', 'rear_view_camera'
        ]
        
        checked_count = 0
        for field in inspection_fields:
            if getattr(self, field):
                checked_count += 1
        return checked_count
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage of the inspection form"""
        return round((self.total_points_checked / 50) * 100, 1)
    
    @property
    def failed_points(self):
        """Get list of failed inspection points"""
        inspection_fields = [
            ('engine_oil_level', 'Engine oil level & quality'),
            ('oil_filter_condition', 'Oil filter condition'),
            ('coolant_level', 'Coolant level & leaks'),
            ('drive_belts', 'Drive belts for cracks/wear'),
            ('hoses_condition', 'Hoses for leaks or soft spots'),
            ('air_filter', 'Air filter condition'),
            ('cabin_air_filter', 'Cabin air filter condition'),
            ('transmission_fluid', 'Transmission fluid level & leaks'),
            ('engine_mounts', 'Engine/transmission mounts'),
            ('fluid_leaks', 'Fluid leaks under engine & gearbox'),
            ('battery_voltage', 'Battery voltage & charging system'),
            ('battery_terminals', 'Battery terminals for corrosion'),
            ('alternator_output', 'Alternator output'),
            ('starter_motor', 'Starter motor performance'),
            ('fuses_relays', 'All fuses and relays'),
            ('brake_pads', 'Brake pads/shoes thickness'),
            ('brake_discs', 'Brake discs/drums damage/warping'),
            ('brake_fluid', 'Brake fluid level & condition'),
            ('parking_brake', 'Parking brake function'),
            ('shocks_struts', 'Shocks/struts for leaks'),
            ('suspension_bushings', 'Suspension bushings & joints'),
            ('wheel_bearings', 'Wheel bearings for noise/play'),
            ('steering_response', 'Steering response & play'),
            ('steering_fluid', 'Steering fluid level & leaks'),
            ('tire_tread_depth', 'Tire tread depth (>5/32")'),
            ('tire_pressure', 'Tire pressure (all tires + spare)'),
            ('tire_wear_patterns', 'Tire wear patterns'),
            ('wheels_rims', 'Wheels & rims for damage'),
            ('exhaust_system', 'Exhaust for leaks/damage'),
            ('catalytic_converter', 'Catalytic converter/muffler condition'),
            ('exhaust_warning_lights', 'No exhaust warning lights'),
            ('seat_belts', 'Seat belts operation & condition'),
            ('airbags', 'Airbags (warning light off)'),
            ('horn_function', 'Horn function'),
            ('first_aid_kit', 'First-aid kit contents'),
            ('warning_triangle', 'Warning triangle/reflective vest present'),
            ('headlights', 'Headlights (low/high beam)'),
            ('brake_lights', 'Brake/reverse/fog lights'),
            ('turn_signals', 'Turn signals & hazard lights'),
            ('interior_lights', 'Interior dome/courtesy lights'),
            ('windshield', 'Windshield for cracks/chips'),
            ('wiper_blades', 'Wiper blades & washer spray'),
            ('rear_defogger', 'Rear defogger/heater operation'),
            ('mirrors', 'Mirrors adjustment & condition'),
            ('air_conditioning', 'Air conditioning & heating performance'),
            ('ventilation', 'Ventilation airflow'),
            ('seat_adjustments', 'Seat adjustments & seat heaters'),
            ('power_windows', 'Power windows & locks'),
            ('infotainment_system', 'Infotainment system & Bluetooth/USB'),
            ('rear_view_camera', 'Rear-view camera/parking sensors'),
        ]
        
        failed_items = []
        for field_name, description in inspection_fields:
            field_value = getattr(self, field_name)
            if field_value in ['fail', 'major']:
                failed_items.append(description)
        
        return failed_items
    
    @property
    def has_major_issues(self):
        """Check if inspection has any major issues"""
        return len(self.failed_points) > 0
    
    def _update_inspection_record(self):
        """Update the related Inspection record with calculated health index and result"""
        from .utils import calculate_vehicle_health_index
        
        try:
            health_index, inspection_result = calculate_vehicle_health_index(self)
            
            # Update the related Inspection record
            self.inspection.vehicle_health_index = health_index
            self.inspection.inspection_result = inspection_result
            self.inspection.save(update_fields=['vehicle_health_index', 'inspection_result'])
            
        except Exception as e:
            # Log the error but don't prevent the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating inspection record {self.inspection.id}: {str(e)}")
    
    def get_health_index_calculation(self):
        """Get the calculated health index and result for this inspection form"""
        from .utils import calculate_vehicle_health_index
        return calculate_vehicle_health_index(self)


class InitialInspection(models.Model):
    """
    160-Point Initial Vehicle Inspection for Second-Hand Vehicles
    Based on comprehensive pre-purchase inspection checklist
    """
    
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable'),
        ('minor', 'Minor Issue'),
        ('major', 'Major Issue'),
        ('needs_attention', 'Needs Attention'),
    ]
    
    # Basic inspection information
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE, 
        related_name='initial_inspections',
        verbose_name="Vehicle"
    )
    inspection_number = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Inspection Number"
    )
    technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='initial_inspections',
        verbose_name="Inspecting Technician"
    )
    inspection_date = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Inspection Date/Time"
    )
    mileage_at_inspection = models.PositiveIntegerField(
        verbose_name="Vehicle Mileage"
    )
    
    # 1. Road Test (Points 1-33)
    cold_engine_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Cold engine operation performs properly")
    throttle_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Throttle operates properly during cold start")
    warmup_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Vehicle operates properly during warm-up conditions")
    operating_temp_performance = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine performs properly at operating temperature")
    normal_operating_temp = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine reaches normal operating temperature")
    brake_vibrations = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="No abnormal vibrations or noises during brake applications")
    engine_fan_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine fan(s) operate properly")
    brake_pedal_specs = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Brake pedal free play and travel within specifications")
    abs_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="ABS operates properly (via diagnostic check)")
    parking_brake_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Parking brake operates properly and within specification")
    seat_belt_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Seat belt material condition")
    seat_belt_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Seat belts operate properly with smooth extension/retraction")
    transmission_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Transmission/clutch operates smoothly")
    auto_trans_cold = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Automatic transmission functions at cold temperature")
    auto_trans_operating = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Automatic transmission functions at operating temperature")
    steering_feel = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Steering feels normal during lock-to-lock turning")
    steering_centered = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Steering wheel centered in straight driving")
    vehicle_tracking = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Vehicle tracks straight on level road")
    tilt_telescopic_steering = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Tilt & telescopic steering operates properly")
    washer_fluid_spray = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Windshield washer fluid sprays properly")
    front_wipers = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Front windshield wiper operates properly in all modes")
    rear_wipers = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Rear windshield wiper operates properly in all modes")
    wiper_rest_position = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Wipers return to rest position correctly")
    wiper_blade_replacement = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Replace wiper blades/inserts if needed")
    speedometer_function = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Speedometer functions properly")
    odometer_function = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Odometer registers mileage correctly")
    cruise_control = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Cruise control operates properly")
    heater_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Heater operates properly")
    ac_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="A/C operates properly")
    engine_noise = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="No abnormal engine noise during driving")
    interior_noise = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="No interior squeaks/rattles")
    wind_road_noise = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="No excessive wind or road noise")
    tire_vibration = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="No tire vibration/steering wheel shimmy during road test")
    
    # 2. Frame, Structure & Underbody (Points 34-54)
    frame_unibody_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Frame/Unibody condition")
    panel_alignment = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Panel alignment and fit")
    underbody_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Lower body and underbody condition")
    suspension_leaks_wear = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Suspension items free from leaks & wear")
    struts_shocks_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Inspect struts/shocks for leaks/wear")
    power_steering_leaks = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Power steering system free from leaks")
    wheel_covers = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Wheel covers secure and undamaged")
    tire_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Tires inflated, free of damage/defects")
    tread_depth = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Minimum 5/32\" tread depth across width")
    tire_specifications = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="All tires same brand, size, rating per OEM specs")
    brake_calipers_lines = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Brake calipers & lines free from damage/leaks")
    brake_system_equipment = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Brake system fully equipped (shims, pins, clips)")
    brake_pad_life = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Brake pads/shoes have min. 50% life remaining")
    brake_rotors_drums = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Brake rotors/drums within spec, no abnormal wear")
    exhaust_system = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Exhaust system secure & free of leaks")
    engine_trans_mounts = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine/transmission mounts in good condition")
    drive_axle_shafts = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Drive/axle shafts operate properly, no damage")
    cv_joints_boots = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="CV joints/boots free from wear/leaks")
    engine_fluid_leaks = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine free from fluid leaks")
    transmission_leaks = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Transmission case/pan free from leaks")
    differential_fluid = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Differential fluid correct, no leaks")
    
    # 3. Under Hood (Points 55-68)
    drive_belts_hoses = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Drive belts and hoses free from cracks/damage")
    underhood_labels = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Confirm under-hood labels and decals present")
    air_filter_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Air filter in good condition")
    battery_damage = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Battery free of visible damage")
    battery_test = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Battery test performed (Midtronics)")
    battery_posts_cables = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Battery posts & cables free from corrosion/damage")
    battery_secured = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Battery properly sized & secured")
    charging_system = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Charging system working within spec")
    coolant_level = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine coolant level correct")
    coolant_protection = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Coolant protection level (-31°F)")
    oil_filter_change = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Change engine oil and filter")
    oil_sludge_check = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Check for oil sludge/gel evidence")
    fluid_levels = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Check all fluid levels (brake, clutch, power steering, transmission, washer, coolant)")
    fluid_contamination = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Fluids clear & uncontaminated")
    
    # 4. Functional & Walkaround (Points 69-82)
    owners_manual = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Owner's Manual and warranty booklet present")
    fuel_gauge = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Fuel gauge operational")
    battery_voltage_gauge = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Battery voltage gauge operational")
    temp_gauge = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine temperature gauge operational")
    horn_function = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Horn operates properly")
    airbags_present = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Airbag(s) present, no deployment signs")
    headlight_alignment = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Headlights aligned & functioning (low/high)")
    emissions_test = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Emissions test performed if required")
    tail_lights = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Tail lights function correctly")
    brake_lights = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Brake lights function correctly")
    side_marker_lights = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Side marker lights function correctly")
    backup_lights = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Backup lights function correctly")
    license_plate_lights = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="License plate lights function correctly")
    exterior_lights_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Exterior lights free of cracks/haze/damage")
    
    # 5. Interior Functions (Points 83-128)
    instrument_panel = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Instrument panel/warning lights function properly")
    hvac_panel = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="HVAC panel/lights operate properly")
    instrument_dimmer = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Instrument light dimmer functions correctly")
    turn_signals = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Turn signals operate & self-cancel")
    hazard_flashers = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Hazard flashers operate properly")
    rearview_mirror = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Rear-view interior mirror intact & adjustable")
    exterior_mirrors = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Exterior mirrors adjust & in good condition")
    remote_mirror_control = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Remote mirror control functions correctly")
    glass_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Glass free from cracks/large chips")
    window_tint = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Window tint compliant with laws")
    dome_courtesy_lights = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Dome/courtesy lights operate properly")
    power_windows = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Power windows operate from all switches")
    window_locks = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Window locks function properly")
    audio_system = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Audio/CD/Aux system operational")
    audio_speakers = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Audio speakers function without distortion")
    antenna = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Antenna present & functional")
    clock_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Clock operates correctly")
    power_outlet = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="12v power outlet operational")
    ashtrays = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Ashtrays (if equipped) intact & clean")
    headliner_trim = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Headliner, sun visors, trim panels in place & good condition")
    floor_mats = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Floor mats OEM, properly secured")
    doors_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Doors open/close properly")
    door_locks = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Door locks incl. child locks function properly")
    keyless_entry = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Remote keyless entry works properly")
    master_keys = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="2 Master keys present")
    theft_deterrent = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Theft deterrent system functions correctly")
    seat_adjustments = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Seat adjustments work properly")
    seat_heaters = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Seat heaters (if equipped) function properly")
    memory_seat = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Memory seat control operates properly")
    headrests = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Headrests function properly")
    rear_defogger = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Rear defogger works properly")
    defogger_indicator = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Defogger indicator light works")
    luggage_light = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Luggage compartment light functions")
    luggage_cleanliness = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Luggage compartment clean, free of debris")
    hood_trunk_latches = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Hood and trunk latches operate properly")
    emergency_trunk_release = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Emergency trunk release functional")
    fuel_door_release = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Fuel door release functions properly")
    spare_tire_cover = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Spare tire cover present and in good condition")
    spare_tire_present = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Spare tire or inflator kit present")
    spare_tire_tread = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Spare tire tread depth >5/32\"")
    spare_tire_pressure = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Spare tire inflated to correct pressure")
    spare_tire_damage = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Spare tire undamaged")
    spare_tire_secured = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Spare tire secured properly")
    jack_tools = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Jack and tools present & secured")
    acceptable_aftermarket = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Acceptable aftermarket items only")
    unacceptable_removal = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Removal of unacceptable aftermarket items")
    
    # 6. Exterior Appearance (Points 129-152)
    body_surface = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Body surface condition good")
    exterior_cleanliness = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Exterior washed & clean")
    paint_finish = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Paint free of swirl marks, high luster finish")
    paint_scratches = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Paint free of scratches/chips (reasonable)")
    wheels_cleanliness = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Wheels/wheel covers clean")
    wheel_wells = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Wheel wells clean")
    tires_dressed = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Tires clean & dressed")
    engine_compartment_clean = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine compartment clean")
    insulation_pad = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Under-hood insulation pad clean")
    engine_dressed = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Engine & compartment dressed properly")
    door_jambs = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Door jambs clean")
    glove_console = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Glove box & console compartments clean")
    cabin_air_filter = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Cabin air filter condition checked")
    seats_carpets = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Seats, carpets, mats free of stains")
    vehicle_odors = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Vehicle free from odors/heavy fragrances")
    glass_cleanliness = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Glass clean & streak-free")
    interior_debris = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Interior free of debris")
    dash_vents = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Dash & vents clean/dressed")
    crevices_clean = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="All crevices clean")
    upholstery_panels = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Upholstery and panels in good condition")
    paint_repairs = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Vehicle free of improper paint repairs")
    glass_repairs = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Glass free of improper repairs")
    bumpers_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Bumpers free from cuts/gouges")
    interior_surfaces = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Interior surfaces (leather/vinyl/plastic) free from excessive wear")
    
    # 7. Optional/Additional Systems (Points 153-160)
    sunroof_convertible = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Sunroof/convertible top operates fully")
    seat_heaters_optional = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Seat heaters function correctly")
    navigation_system = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Navigation system works properly, memory cleared")
    head_unit_software = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Head unit software updated")
    transfer_case = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Transfer case (4WD) switches smoothly")
    truck_bed_condition = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Truck bed condition good")
    truck_bed_liner = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Truck bed liner secure & intact")
    backup_camera = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Backup camera functions properly")
    
    # Advanced Safety Systems (if equipped)
    sos_indicator = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="SOS (Safety Connect) indicator green")
    lane_keep_assist = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Lane Keep Assist operates properly")
    adaptive_cruise = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Adaptive Cruise/Pre-Collision Systems work properly")
    parking_assist = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Intelligent Parking Assist functions correctly")
    
    # Hybrid Components (if applicable)
    hybrid_battery = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Hybrid battery condition")
    battery_control_module = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Battery control module operational")
    hybrid_power_mgmt = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Hybrid power management system functional")
    electric_motor = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Electric motor/generator functions correctly")
    ecvt_operation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="ECVT operates smoothly")
    power_inverter = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Power inverter functions correctly")
    inverter_coolant = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Inverter coolant level correct")
    ev_modes = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="EV/Eco/Power modes function correctly")
    hybrid_park_mechanism = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Hybrid transaxle 'park' mechanism functional")
    multi_info_display = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Multi-information display operates correctly")
    touch_tracer_display = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Touch Tracer display operates correctly")
    hill_start_assist = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Hill Start Assist functions correctly")
    remote_ac = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Remote air conditioning works (if equipped)")
    solar_ventilation = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True, verbose_name="Solar ventilation system works (if equipped)")
    
    # Section notes for detailed observations
    road_test_notes = models.TextField(blank=True, verbose_name="Road Test Notes")
    frame_structure_notes = models.TextField(blank=True, verbose_name="Frame, Structure & Underbody Notes")
    under_hood_notes = models.TextField(blank=True, verbose_name="Under Hood Notes")
    functional_walkaround_notes = models.TextField(blank=True, verbose_name="Functional & Walkaround Notes")
    interior_functions_notes = models.TextField(blank=True, verbose_name="Interior Functions Notes")
    exterior_appearance_notes = models.TextField(blank=True, verbose_name="Exterior Appearance Notes")
    optional_systems_notes = models.TextField(blank=True, verbose_name="Optional/Additional Systems Notes")
    safety_systems_notes = models.TextField(blank=True, verbose_name="Advanced Safety Systems Notes")
    hybrid_components_notes = models.TextField(blank=True, verbose_name="Hybrid Components Notes")
    
    # Overall inspection summary
    overall_condition_rating = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('very_good', 'Very Good'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('needs_major_work', 'Needs Major Work'),
        ],
        blank=True,
        verbose_name="Overall Condition Rating"
    )
    overall_notes = models.TextField(blank=True, verbose_name="Overall Inspection Summary")
    recommendations = models.TextField(blank=True, verbose_name="Recommendations & Required Repairs")
    estimated_repair_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Estimated Repair Cost"
    )
    
    # Inspection completion tracking
    is_completed = models.BooleanField(default=False, verbose_name="Inspection Completed")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completion Date/Time")
    
    # PDF report generation
    inspection_pdf = models.FileField(
        upload_to='initial_inspections/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        verbose_name="Inspection Report PDF",
        help_text="Generated inspection report PDF",
        blank=True,
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-inspection_date']
        verbose_name = "Initial Inspection (160-Point)"
        verbose_name_plural = "Initial Inspections (160-Point)"
    
    def __str__(self):
        return f"Initial Inspection {self.inspection_number} - {self.vehicle.vin}"
    
    def save(self, *args, **kwargs):
        # Set completion timestamp when inspection is marked as completed
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Auto-update calculated fields when inspection is completed
        if self.is_completed:
            self._update_calculated_fields()
    
    def _update_calculated_fields(self):
        """Update calculated fields like health index and inspection result"""
        try:
            from .utils import calculate_initial_inspection_health_index
            health_index, inspection_result = calculate_initial_inspection_health_index(self)
            
            # Update the overall condition rating based on health index
            if "Excellent" in health_index:
                self.overall_condition_rating = 'excellent'
            elif "Good" in health_index:
                self.overall_condition_rating = 'very_good' if "90" in health_index else 'good'
            elif "Fair" in health_index:
                self.overall_condition_rating = 'fair'
            elif "Poor" in health_index:
                self.overall_condition_rating = 'poor'
            else:
                self.overall_condition_rating = 'needs_major_work'
            
            # Save without triggering recursion
            InitialInspection.objects.filter(pk=self.pk).update(
                overall_condition_rating=self.overall_condition_rating
            )
            
        except Exception as e:
            # Log the error but don't prevent the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating calculated fields for initial inspection {self.pk}: {str(e)}")
    
    def clean(self):
        """Validate the inspection data"""
        from django.core.exceptions import ValidationError
        
        # Ensure minimum completion for scoring
        if self.is_completed and self.completion_percentage < 80:
            raise ValidationError(
                "Inspection must be at least 80% complete before marking as completed. "
                f"Current completion: {self.completion_percentage}%"
            )
        
        # Ensure critical safety systems are inspected if marking as completed
        if self.is_completed:
            critical_fields = [
                'brake_vibrations', 'brake_pedal_specs', 'abs_operation', 'parking_brake_operation',
                'seat_belt_condition', 'seat_belt_operation', 'steering_feel', 'vehicle_tracking',
                'tire_condition', 'tread_depth', 'brake_pad_life', 'headlight_alignment'
            ]
            
            missing_critical = []
            for field in critical_fields:
                if not getattr(self, field):
                    field_obj = self._meta.get_field(field)
                    missing_critical.append(field_obj.verbose_name)
            
            if missing_critical:
                raise ValidationError(
                    f"The following critical safety systems must be inspected before completion: "
                    f"{', '.join(missing_critical[:3])}{'...' if len(missing_critical) > 3 else ''}"
                )
    
    def get_scoring_summary(self):
        """Get a quick scoring summary for display purposes"""
        if not self.is_completed:
            return {
                'status': 'incomplete',
                'message': f'Inspection {self.completion_percentage}% complete'
            }
        
        try:
            health_index = self.vehicle_health_index
            failed_count = len(self.failed_points)
            critical_count = len(self.safety_critical_issues)
            
            return {
                'status': 'completed',
                'health_index': health_index,
                'total_issues': failed_count,
                'critical_issues': critical_count,
                'message': f'{health_index} - {failed_count} issues found'
            }
        except:
            return {
                'status': 'error',
                'message': 'Error calculating scores'
            }
    
    @property
    def total_points_inspected(self):
        """Count how many inspection points have been checked (not empty)"""
        inspection_fields = [
            # Road Test (33 points)
            'cold_engine_operation', 'throttle_operation', 'warmup_operation', 'operating_temp_performance',
            'normal_operating_temp', 'brake_vibrations', 'engine_fan_operation', 'brake_pedal_specs',
            'abs_operation', 'parking_brake_operation', 'seat_belt_condition', 'seat_belt_operation',
            'transmission_operation', 'auto_trans_cold', 'auto_trans_operating', 'steering_feel',
            'steering_centered', 'vehicle_tracking', 'tilt_telescopic_steering', 'washer_fluid_spray',
            'front_wipers', 'rear_wipers', 'wiper_rest_position', 'wiper_blade_replacement',
            'speedometer_function', 'odometer_function', 'cruise_control', 'heater_operation',
            'ac_operation', 'engine_noise', 'interior_noise', 'wind_road_noise', 'tire_vibration',
            
            # Frame, Structure & Underbody (21 points)
            'frame_unibody_condition', 'panel_alignment', 'underbody_condition', 'suspension_leaks_wear',
            'struts_shocks_condition', 'power_steering_leaks', 'wheel_covers', 'tire_condition',
            'tread_depth', 'tire_specifications', 'brake_calipers_lines', 'brake_system_equipment',
            'brake_pad_life', 'brake_rotors_drums', 'exhaust_system', 'engine_trans_mounts',
            'drive_axle_shafts', 'cv_joints_boots', 'engine_fluid_leaks', 'transmission_leaks',
            'differential_fluid',
            
            # Under Hood (14 points)
            'drive_belts_hoses', 'underhood_labels', 'air_filter_condition', 'battery_damage',
            'battery_test', 'battery_posts_cables', 'battery_secured', 'charging_system',
            'coolant_level', 'coolant_protection', 'oil_filter_change', 'oil_sludge_check',
            'fluid_levels', 'fluid_contamination',
            
            # Functional & Walkaround (14 points)
            'owners_manual', 'fuel_gauge', 'battery_voltage_gauge', 'temp_gauge', 'horn_function',
            'airbags_present', 'headlight_alignment', 'emissions_test', 'tail_lights', 'brake_lights',
            'side_marker_lights', 'backup_lights', 'license_plate_lights', 'exterior_lights_condition',
            
            # Interior Functions (46 points)
            'instrument_panel', 'hvac_panel', 'instrument_dimmer', 'turn_signals', 'hazard_flashers',
            'rearview_mirror', 'exterior_mirrors', 'remote_mirror_control', 'glass_condition',
            'window_tint', 'dome_courtesy_lights', 'power_windows', 'window_locks', 'audio_system',
            'audio_speakers', 'antenna', 'clock_operation', 'power_outlet', 'ashtrays',
            'headliner_trim', 'floor_mats', 'doors_operation', 'door_locks', 'keyless_entry',
            'master_keys', 'theft_deterrent', 'seat_adjustments', 'seat_heaters', 'memory_seat',
            'headrests', 'rear_defogger', 'defogger_indicator', 'luggage_light', 'luggage_cleanliness',
            'hood_trunk_latches', 'emergency_trunk_release', 'fuel_door_release', 'spare_tire_cover',
            'spare_tire_present', 'spare_tire_tread', 'spare_tire_pressure', 'spare_tire_damage',
            'spare_tire_secured', 'jack_tools', 'acceptable_aftermarket', 'unacceptable_removal',
            
            # Exterior Appearance (24 points)
            'body_surface', 'exterior_cleanliness', 'paint_finish', 'paint_scratches', 'wheels_cleanliness',
            'wheel_wells', 'tires_dressed', 'engine_compartment_clean', 'insulation_pad', 'engine_dressed',
            'door_jambs', 'glove_console', 'cabin_air_filter', 'seats_carpets', 'vehicle_odors',
            'glass_cleanliness', 'interior_debris', 'dash_vents', 'crevices_clean', 'upholstery_panels',
            'paint_repairs', 'glass_repairs', 'bumpers_condition', 'interior_surfaces',
            
            # Optional/Additional Systems (8 points)
            'sunroof_convertible', 'seat_heaters_optional', 'navigation_system', 'head_unit_software',
            'transfer_case', 'truck_bed_condition', 'truck_bed_liner', 'backup_camera',
        ]
        
        checked_count = 0
        for field in inspection_fields:
            if getattr(self, field):
                checked_count += 1
        return checked_count
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage of the inspection (160 points total)"""
        return round((self.total_points_inspected / 160) * 100, 1)
    
    @property
    def failed_points(self):
        """Get list of failed inspection points"""
        # Get all inspection field names and their verbose names from the model
        failed_items = []
        
        # Get all fields that are inspection points (CharField with STATUS_CHOICES)
        for field in self._meta.fields:
            if (hasattr(field, 'choices') and 
                field.choices == self.STATUS_CHOICES and 
                field.name not in ['overall_condition_rating']):
                
                field_value = getattr(self, field.name)
                if field_value in ['fail', 'major']:
                    # Use the verbose_name from the field definition
                    description = field.verbose_name or field.name.replace('_', ' ').title()
                    failed_items.append(description)
        
        return failed_items
    
    @property
    def has_major_issues(self):
        """Check if inspection has any major issues"""
        return len(self.failed_points) > 0
    
    @property
    def safety_critical_issues(self):
        """Get list of safety-critical failed points"""
        safety_critical_fields = [
            ('brake_vibrations', 'Brake vibrations/noises'),
            ('brake_pedal_specs', 'Brake pedal specifications'),
            ('abs_operation', 'ABS operation'),
            ('parking_brake_operation', 'Parking brake operation'),
            ('seat_belt_condition', 'Seat belt condition'),
            ('seat_belt_operation', 'Seat belt operation'),
            ('steering_feel', 'Steering response'),
            ('vehicle_tracking', 'Vehicle tracking'),
            ('tire_condition', 'Tire condition'),
            ('tread_depth', 'Tire tread depth'),
            ('brake_calipers_lines', 'Brake calipers & lines'),
            ('brake_pad_life', 'Brake pad life'),
            ('brake_rotors_drums', 'Brake rotors/drums'),
            ('headlight_alignment', 'Headlight alignment'),
            ('brake_lights', 'Brake lights'),
            ('turn_signals', 'Turn signals'),
            ('airbags_present', 'Airbags present'),
        ]
        
        critical_issues = []
        for field_name, description in safety_critical_fields:
            field_value = getattr(self, field_name)
            if field_value in ['fail', 'major']:
                critical_issues.append(description)
        
        return critical_issues
    
    @property
    def total_points_checked(self):
        """Alias for total_points_inspected to match Inspections model interface"""
        return self.total_points_inspected
    
    def get_health_index_calculation(self):
        """Get the calculated health index and result for this initial inspection"""
        from .utils import calculate_initial_inspection_health_index
        return calculate_initial_inspection_health_index(self)
    
    @property
    def vehicle_health_index(self):
        """Get the vehicle health index string"""
        try:
            health_index, _ = self.get_health_index_calculation()
            return health_index
        except:
            return "Not Calculated"
    
    @property
    def inspection_result(self):
        """Get the inspection result based on scoring"""
        try:
            _, inspection_result = self.get_health_index_calculation()
            return inspection_result
        except:
            return "Pending"
