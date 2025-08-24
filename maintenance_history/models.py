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
