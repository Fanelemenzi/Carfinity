# inspection/models.py
from django.db import models
from vehicles.models import Vehicle
from django.core.validators import MinValueValidator, MaxValueValidator

class PowertrainAndDrivetrain(models.Model):
    #Connection to vehicle
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, related_name='powertrain', primary_key=True)
    # Engine Specifications
    base_engine = models.CharField(max_length=100, null=True, blank=True, help_text="Type and specifications of the base engine (e.g., '2.0L Turbo I4')")
    engine_displacement = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text="Engine displacement in liters")
    engine_power = models.PositiveIntegerField(null=True, blank=True, help_text="Engine power in horsepower")
    
    # Transmission Details
    transmission_specifications = models.CharField(max_length=100, null=True, blank=True, help_text="Detailed transmission specifications")
    TRANSMISSION_TYPES = [
        ('MT', 'Manual Transmission'),
        ('AT', 'Automatic Transmission'),
        ('CVT', 'Continuously Variable Transmission'),
        ('DCT', 'Dual-Clutch Transmission'),
        ('AMT', 'Automated Manual Transmission'),
    ]
    transmission_type = models.CharField(max_length=3, null=True, blank=True, choices=TRANSMISSION_TYPES, help_text="Type of transmission system")
    gear_count = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)], help_text="Number of gears")
    
    # Drivetrain Configuration
    DRIVE_LAYOUTS = [
        ('FWD', 'Front-Wheel Drive'),
        ('RWD', 'Rear-Wheel Drive'),
        ('AWD', 'All-Wheel Drive'),
        ('4WD', 'Four-Wheel Drive'),
    ]
    drive_layout = models.CharField(max_length=3,choices=DRIVE_LAYOUTS,help_text="Vehicle's drive configuration")
    
    # Fuel System
    FUEL_TYPES = [
        ('G', 'Gasoline'),
        ('D', 'Diesel'),
        ('E', 'Electric'),
        ('H', 'Hybrid'),
        ('P', 'Plug-in Hybrid'),
        ('F', 'Fuel Cell'),
    ]
    fuel_system = models.CharField(max_length=1,choices=FUEL_TYPES,help_text="Type of fuel system")
    
    # Emissions
    EMISSIONS_STANDARDS = [
        ('EU1', 'Euro 1'),
        ('EU2', 'Euro 2'),
        ('EU3', 'Euro 3'),
        ('EU4', 'Euro 4'),
        ('EU5', 'Euro 5'),
        ('EU6', 'Euro 6'),
        ('EPA1', 'EPA Tier 1'),
        # Add more standards as needed
    ]
    emissions_standard = models.CharField(max_length=4,choices=EMISSIONS_STANDARDS,help_text="Vehicle emissions standard compliance")
    
    # Advanced Features
    has_start_stop = models.BooleanField(default=False,help_text="Has automatic start-stop system")
    has_regenerative_braking = models.BooleanField(default=False,help_text="Has regenerative braking system")
    
    # Gearshift Interface
    GEARSHIFT_POSITIONS = [
        ('C', 'Center Console'),
        ('S', 'Steering Column'),
        ('D', 'Dashboard'),
    ]
    gearshift_position = models.CharField(max_length=1,choices=GEARSHIFT_POSITIONS,help_text="Location of gearshift mechanism")
    gearshift_material = models.CharField(max_length=50,blank=True, help_text="Material of gearshift knob/handle (e.g., 'Leather-wrapped')")
    
    # Additional Notes
    notes = models.TextField( blank=True, help_text="Additional powertrain notes or special features")
    
    class Meta:
        verbose_name = "Powertrain & Drivetrain"
        verbose_name_plural = "Powertrain & Drivetrain Systems"
        ordering = ['base_engine']
    
    def __str__(self):
        return f"{self.base_engine} - {self.get_transmission_type_display()} - {self.get_drive_layout_display()}"


class ChassisSuspensionAndBraking(models.Model):
    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='chassis',
        primary_key=True
    )
    
    # Suspension Systems
    SUSPENSION_TYPES = [
        ('MACP', 'MacPherson Strut'),
        ('DUBL', 'Double Wishbone'),
        ('MULT', 'Multi-Link'),
        ('LEAF', 'Leaf Spring'),
        ('AIR', 'Air Suspension'),
        ('ADAP', 'Adaptive Suspension'),
    ]
    
    front_suspension = models.CharField(
        max_length=4,
        choices=SUSPENSION_TYPES,
        verbose_name="Front Suspension Type"
    )
    rear_suspension = models.CharField(
        max_length=4,
        choices=SUSPENSION_TYPES,
        verbose_name="Rear Suspension Type"
    )
    
    # Brake Systems
    BRAKE_TYPES = [
        ('DISC', 'Disc Brakes'),
        ('DRUM', 'Drum Brakes'),
        ('CERM', 'Ceramic Discs'),
        ('CARB', 'Carbon Ceramic'),
    ]
    
    front_brake_type = models.CharField(
        max_length=4,
        choices=BRAKE_TYPES,
        verbose_name="Front Brake Type"
    )
    rear_brake_type = models.CharField(
        max_length=4,
        choices=BRAKE_TYPES,
        verbose_name="Rear Brake Type"
    )
    
    BRAKE_SYSTEMS = [
        ('ABS', 'Anti-lock Braking System'),
        ('EBD', 'Electronic Brakeforce Distribution'),
        ('BAS', 'Brake Assist System'),
        ('REGEN', 'Regenerative Braking'),
    ]
    brake_systems = models.CharField(
        max_length=5,
        choices=BRAKE_SYSTEMS,
        verbose_name="Primary Brake System"
    )
    
    PARKING_BRAKE_TYPES = [
        ('EPB', 'Electronic Parking Brake'),
        ('MECH', 'Mechanical Lever'),
        ('PEDAL', 'Foot Pedal'),
        ('INTEG', 'Integrated with Service Brakes'),
    ]
    parking_brake_type = models.CharField(
        max_length=5,
        choices=PARKING_BRAKE_TYPES,
        verbose_name="Parking Brake Type"
    )
    
    # Steering Systems
    STEERING_TYPES = [
        ('RACK', 'Rack and Pinion'),
        ('RECIRC', 'Recirculating Ball'),
        ('EPAS', 'Electric Power Assist'),
        ('HPAS', 'Hydraulic Power Assist'),
    ]
    steering_system = models.CharField(
        max_length=6,
        choices=STEERING_TYPES,
        verbose_name="Steering System Type"
    )
    
    STEERING_WHEEL_FEATURES = [
        ('TILT', 'Tilt Adjustment'),
        ('TEL', 'Telescopic Adjustment'),
        ('HEAT', 'Heated'),
        ('PADDLE', 'Paddle Shifters'),
        ('CONTROLS', 'Integrated Controls'),
    ]
    steering_wheel_features = models.CharField(
        max_length=30,
        choices=STEERING_WHEEL_FEATURES,
        verbose_name="Steering Wheel Features"
    )
    
    # Additional Features
    has_park_distance_control = models.BooleanField(
        default=False,
        verbose_name="Park Distance Control"
    )
    
    class Meta:
        verbose_name = "Chassis, Suspension & Braking"
        verbose_name_plural = "Chassis, Suspension & Braking Systems"
    
    def __str__(self):
        return f"{self.vehicle} - {self.get_front_suspension_display()}/{self.get_rear_suspension_display()}"


