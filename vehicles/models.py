from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField
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
    plant_location = CountryField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    def __str__(self):
        return f"Vehicle Status for VIN {self.vin}"

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"


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