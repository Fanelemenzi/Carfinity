from django.db import models
from django.contrib.auth.models import User
# from django_countries.fields import CountryField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

# Create your models here.
class Vehicle(models.Model):
    vin = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    manufacture_year = models.PositiveIntegerField()
    body_type = models.CharField(max_length=20, blank=True, null=True)
    engine_code = models.CharField(max_length=20, blank=True, null=True)
    interior_color =  models.CharField(max_length=30, null=True)
    exterior_color =  models.CharField(max_length=30, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    license_plate = models.CharField(max_length=20, blank=True, null=True)
    fuel_type = models.CharField(max_length=50, blank=True, null=True)
    transmission_type = models.CharField(max_length=50, blank=True, null=True)
    powertrain_displacement = models.CharField(max_length=50, blank=True, null=True)
    powertrain_power =  models.CharField(max_length=5, null=True)
    plant_location = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    def __str__(self):
        return f"Vehicle Status for VIN {self.vin}"

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
    
    @property
    def current_mileage(self):
        """Get the latest mileage from maintenance records or inspections"""
        # Check maintenance records first
        latest_maintenance = self.maintenance_history.order_by('-date_performed').first()
        if latest_maintenance and latest_maintenance.mileage:
            return latest_maintenance.mileage
            
        # Fallback to inspection records
        latest_inspection = self.inspections.order_by('-inspection_date').first()
        if latest_inspection and hasattr(latest_inspection, 'inspections_form'):
            inspections_form = latest_inspection.inspections_form
            if inspections_form and inspections_form.mileage_at_inspection:
                return inspections_form.mileage_at_inspection
                
        # Fallback to initial inspection records
        latest_initial_inspection = self.initial_inspections.order_by('-inspection_date').first()
        if latest_initial_inspection and latest_initial_inspection.mileage_at_inspection:
            return latest_initial_inspection.mileage_at_inspection
            
        return None
    
    @property
    def mileage_last_updated(self):
        """Get the date when mileage was last recorded"""
        latest_maintenance = self.maintenance_history.order_by('-date_performed').first()
        if latest_maintenance and latest_maintenance.mileage:
            return latest_maintenance.date_performed
            
        latest_inspection = self.inspections.order_by('-inspection_date').first()
        if latest_inspection and hasattr(latest_inspection, 'inspections_form'):
            inspections_form = latest_inspection.inspections_form
            if inspections_form and inspections_form.mileage_at_inspection:
                return latest_inspection.inspection_date
                
        latest_initial_inspection = self.initial_inspections.order_by('-inspection_date').first()
        if latest_initial_inspection and latest_initial_inspection.mileage_at_inspection:
            return latest_initial_inspection.inspection_date
            
        return None
    
    @property
    def health_score(self):
        """Get the latest vehicle health score from inspections"""
        latest_inspection = self.inspections.order_by('-inspection_date').first()
        if latest_inspection and latest_inspection.vehicle_health_index:
            # Extract numeric score from health index string
            try:
                # Assuming health index format like "87/100" or "87"
                score_str = latest_inspection.vehicle_health_index.split('/')[0]
                return int(score_str)
            except (ValueError, AttributeError):
                pass
        return None
    
    @property
    def health_status(self):
        """Get vehicle health status based on latest inspection result"""
        latest_inspection = self.inspections.order_by('-inspection_date').first()
        if latest_inspection and latest_inspection.inspection_result:
            result = latest_inspection.inspection_result
            if result in ['PAS', 'PMD']:  # Passed or Passed with minor defects
                return 'Healthy'
            elif result in ['PJD']:  # Passed with major defects
                return 'Needs Attention'
            elif result in ['FMD', 'FJD', 'FAI']:  # Failed
                return 'Critical'
        return 'Unknown'
    
    @property
    def last_inspection_date(self):
        """Get the date of the last inspection"""
        latest_inspection = self.inspections.order_by('-inspection_date').first()
        if latest_inspection:
            return latest_inspection.inspection_date
        return None


class VehicleOwnership(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='ownerships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_vehicles')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current_owner = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.vehicle.make} - {self.vehicle.model} - {self.vehicle.vin}"

    class Meta:
        verbose_name = "Vehicle Onwership"
        verbose_name_plural = "Vehicle Onwership"

# vehicle statuses on accident history, odometer fraud and theft involvement
class VehicleStatus(models.Model):
    """
    Represents the status of a vehicle, including accident history, odometer fraud, and theft involvement.
    """
    ACCIDENT_HISTORY = [
        ("NHA","No History of Accidents"),
        ("OIIA", "Once Involved In Accident"),
        ("CAD", "Currently Accident Damaged"),
    ]

    ODOMETER_FRAUD = [
        ("NOF", "No Odometer Fraud"),
        ("SOF",  "Suspected Odometer Fraud"),
    ]

    THEFT_INVOLVEMENT = [
        ("NHT", "No History of Theft"),
        ("OIT",  "Once Involved In Theft"),
        ("STI", "Suspected Theft Involvement"),
    ]

    LEGAL_STATUS = [
        ("LG", "Looks Good"),
        ("ILA",  "Involved Legal Action"),
    ]

    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, related_name='vehiclestatus', db_index=True, help_text="Vehicle Identification Number")
    accident_history = models.CharField(max_length=30, choices=ACCIDENT_HISTORY, default='NHA', help_text="History of accidents involving the vehicle")
    odometer_fraud = models.CharField(max_length=30, choices=ODOMETER_FRAUD, default='NOF', help_text="Indicates if the vehicle has suspected odometer fraud")
    theft_involvement = models.CharField(max_length=30, choices=THEFT_INVOLVEMENT, default='NHT', help_text="Indicates if the vehicle has been involved in theft")
    legal_status = models.CharField(max_length=30, choices=LEGAL_STATUS, default='LG', help_text="Indicates if the vehicle is involved in any legal action or attached to bank")
    owner_history = models.IntegerField(
        validators=[
        MinValueValidator(1),
        MaxValueValidator(100)
            ],
        help_text="Number of previous owners of the vehicle", default=0)
    
    
    def __str__(self):
        return f"Vehicle Status for VIN {self.vehicle}"

    class Meta:
        verbose_name = "Vehicle Status"
        verbose_name_plural = "Vehicle Statuses"

class VehicleHistory(models.Model):
    # Event Types
    EVENT_TYPES = [
        ('ACCIDENT', 'Accident'),
        ('ODOMETER_FRAUD', 'Odometer Fraud'),
        ('THEFT', 'Theft'),
        ('RECALL', 'Recall'),
        ('REPAIR', 'Repair'),
        ('OTHER', 'Other'),
    ]

    # Severity Levels
    SEVERITY_LEVELS = [
        ('MINOR', 'Minor'),
        ('MAJOR', 'Major'),
        ('TOTAL_LOSS', 'Total Loss'),
    ]

    # Fraud Types
    FRAUD_TYPES = [
        ('ROLLBACK', 'Rollback'),
        ('TAMPERING', 'Tampering'),
    ]

    # Core Fields
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='history',null=True)
    owner_history = models.IntegerField(
        validators=[
        MinValueValidator(1),
        MaxValueValidator(100)
            ],
        help_text="Number of previous owners of the vehicle", default=0)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, blank=True)
    event_date = models.DateField(blank=True)
    reported_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='reported_events')
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='verified_events')
    verified_at = models.DateTimeField(blank=True, null=True)

    # Accident-Specific Fields
    accident_severity = models.CharField(max_length=50, choices=SEVERITY_LEVELS, blank=True, null=True)
    accident_location = models.CharField(max_length=255, blank=True, null=True)
    police_report_number = models.CharField(max_length=100, blank=True, null=True)
    insurance_claim_number = models.CharField(max_length=100, blank=True, null=True)

    # Odometer Fraud-Specific Fields
    odometer_reading = models.PositiveIntegerField(blank=True, null=True)
    fraud_type = models.CharField(max_length=50, choices=FRAUD_TYPES, blank=True, null=True)
    reported_mileage = models.PositiveIntegerField(blank=True, null=True)

    # Theft-Specific Fields
    theft_location = models.CharField(max_length=255, blank=True, null=True)
    recovery_date = models.DateField(blank=True, null=True)
    recovery_location = models.CharField(max_length=255, blank=True, null=True)
    damage_during_theft = models.TextField(blank=True, null=True)

    # Other Fields
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.vehicle.vin} ({self.event_date})"

    class Meta:
        verbose_name = "Vehicle History"
        verbose_name_plural = "Vehicle History"

class VehicleImage(models.Model):
    """
    Model to store vehicle images with categorization
    """
    IMAGE_TYPES = [
        ('FRONT', 'Front View'),
        ('REAR', 'Rear View'),
        ('SIDE_LEFT', 'Left Side'),
        ('SIDE_RIGHT', 'Right Side'),
        ('INTERIOR', 'Interior'),
        ('ENGINE', 'Engine Bay'),
        ('DASHBOARD', 'Dashboard'),
        ('TRUNK', 'Trunk/Cargo Area'),
        ('WHEELS', 'Wheels/Tires'),
        ('DAMAGE', 'Damage/Issues'),
        ('DOCUMENTS', 'Documents'),
        ('OTHER', 'Other'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='vehicle_images/')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPES)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_vehicle_images')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False, help_text="Mark as primary image for the vehicle")
    
    class Meta:
        verbose_name = "Vehicle Image"
        verbose_name_plural = "Vehicle Images"
        ordering = ['-is_primary', '-uploaded_at']
    
    def __str__(self):
        return f"{self.get_image_type_display()} - {self.vehicle.vin}"
    
    def save(self, *args, **kwargs):
        # If this image is marked as primary, unmark others
        if self.is_primary:
            VehicleImage.objects.filter(vehicle=self.vehicle, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class VehicleValuation(models.Model):
    """
    Model to store vehicle valuation information including estimated market value,
    condition rating, and valuation source data
    """
    CONDITION_RATINGS = [
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    VALUATION_SOURCES = [
        ('kbb', 'Kelley Blue Book'),
        ('edmunds', 'Edmunds'),
        ('nada', 'NADA Guides'),
        ('autotrader', 'AutoTrader'),
        ('cargurus', 'CarGurus'),
        ('manual', 'Manual Assessment'),
        ('insurance', 'Insurance Appraisal'),
        ('dealer', 'Dealer Assessment'),
    ]
    
    vehicle = models.OneToOneField(
        Vehicle, 
        on_delete=models.CASCADE, 
        related_name='valuation',
        help_text="Vehicle this valuation belongs to"
    )
    estimated_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Estimated market value in local currency"
    )
    condition_rating = models.CharField(
        max_length=20, 
        choices=CONDITION_RATINGS,
        help_text="Overall condition rating of the vehicle"
    )
    valuation_source = models.CharField(
        max_length=20, 
        choices=VALUATION_SOURCES,
        help_text="Source of the valuation data"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When this valuation was last updated"
    )
    
    # Additional valuation details
    mileage_at_valuation = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Vehicle mileage when valuation was performed"
    )
    valuation_notes = models.TextField(
        blank=True,
        help_text="Additional notes about the valuation"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Vehicle Valuation"
        verbose_name_plural = "Vehicle Valuations"
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"Valuation for {self.vehicle.vin} - ${self.estimated_value}"
    
    @property
    def is_recent(self):
        """Check if valuation is recent (within last 30 days)"""
        from datetime import datetime, timedelta
        from django.utils import timezone
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return self.last_updated >= thirty_days_ago
    
    @property
    def formatted_value(self):
        """Return formatted currency value"""
        return f"${self.estimated_value:,.2f}"