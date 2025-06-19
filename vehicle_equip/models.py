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
    vehicle = models.OneToOneField(Vehicle,on_delete=models.CASCADE,related_name='chassis',primary_key=True)
    
    # Suspension Systems
    SUSPENSION_TYPES = [
        ('MACP', 'MacPherson Strut'),
        ('DUBL', 'Double Wishbone'),
        ('MULT', 'Multi-Link'),
        ('LEAF', 'Leaf Spring'),
        ('AIR', 'Air Suspension'),
        ('ADAP', 'Adaptive Suspension'),
    ]
    
    front_suspension = models.CharField(max_length=4,choices=SUSPENSION_TYPES,verbose_name="Front Suspension Type")
    rear_suspension = models.CharField(max_length=4,choices=SUSPENSION_TYPES, verbose_name="Rear Suspension Type")
    
    # Brake Systems
    BRAKE_TYPES = [
        ('DISC', 'Disc Brakes'),
        ('DRUM', 'Drum Brakes'),
        ('CERM', 'Ceramic Discs'),
        ('CARB', 'Carbon Ceramic'),
    ]
    
    front_brake_type = models.CharField(max_length=4,choices=BRAKE_TYPES,verbose_name="Front Brake Type")
    rear_brake_type = models.CharField(max_length=4,choices=BRAKE_TYPES,verbose_name="Rear Brake Type")
    
    BRAKE_SYSTEMS = [
        ('ABS', 'Anti-lock Braking System'),
        ('EBD', 'Electronic Brakeforce Distribution'),
        ('BAS', 'Brake Assist System'),
        ('REGEN', 'Regenerative Braking'),
    ]
    brake_systems = models.CharField(max_length=5,choices=BRAKE_SYSTEMS,verbose_name="Primary Brake System")
    
    PARKING_BRAKE_TYPES = [
        ('EPB', 'Electronic Parking Brake'),
        ('MECH', 'Mechanical Lever'),
        ('PEDAL', 'Foot Pedal'),
        ('INTEG', 'Integrated with Service Brakes'),
    ]
    parking_brake_type = models.CharField(max_length=5,choices=PARKING_BRAKE_TYPES,verbose_name="Parking Brake Type")
    
    # Steering Systems
    STEERING_TYPES = [
        ('RACK', 'Rack and Pinion'),
        ('RECIRC', 'Recirculating Ball'),
        ('EPAS', 'Electric Power Assist'),
        ('HPAS', 'Hydraulic Power Assist'),
    ]
    steering_system = models.CharField(max_length=6,choices=STEERING_TYPES,verbose_name="Steering System Type")
    
    STEERING_WHEEL_FEATURES = [
        ('TILT', 'Tilt Adjustment'),
        ('TEL', 'Telescopic Adjustment'),
        ('HEAT', 'Heated'),
        ('PADDLE', 'Paddle Shifters'),
        ('CONTROLS', 'Integrated Controls'),
    ]
    steering_wheel_features = models.CharField(max_length=30,choices=STEERING_WHEEL_FEATURES,verbose_name="Steering Wheel Features")
    
    # Additional Features
    has_park_distance_control = models.BooleanField(default=False,verbose_name="Park Distance Control")
    
    class Meta:
        verbose_name = "Chassis, Suspension & Braking"
        verbose_name_plural = "Chassis, Suspension & Braking Systems"
    
    def __str__(self):
        return f"{self.vehicle} - {self.get_front_suspension_display()}/{self.get_rear_suspension_display()}"

class ElectricalSystem(models.Model):
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE,related_name='electrical',primary_key=True)

    # Battery System
    BATTERY_TYPES = [
        ('FLA', 'Flooded Lead Acid'),
        ('AGM', 'Absorbent Glass Mat'),
        ('GEL', 'Gel Cell'),
        ('LITH', 'Lithium-Ion'),
        ('EFB', 'Enhanced Flooded Battery'),
    ]
    
    primary_battery_type = models.CharField(max_length=4, choices=BATTERY_TYPES, verbose_name="Primary Battery Type")
    primary_battery_capacity = models.PositiveIntegerField(verbose_name="Capacity (Ah)",help_text="Primary battery capacity in amp-hours")
    has_second_battery = models.BooleanField(default=False,verbose_name="Second Battery Installed")
    second_battery_type = models.CharField(max_length=4,choices=BATTERY_TYPES, blank=True,null=True,verbose_name="Second Battery Type")
    second_battery_capacity = models.PositiveIntegerField(null=True,blank=True,verbose_name="Capacity (Ah)",help_text="Secondary battery capacity in amp-hours")
    
    # Charging System
    alternator_output = models.PositiveIntegerField(verbose_name="Alternator Output (A)",help_text="Maximum alternator output in amps")
    
    VOLTAGE_SYSTEMS = [
        (12, '12V System'),
        (24, '24V System'),
        (48, '48V System (Mild Hybrid)'),
        (400, '400V System (EV)'),
        (800, '800V System (High Performance EV)'),
    ]
    operating_voltage = models.PositiveIntegerField(choices=VOLTAGE_SYSTEMS,default=12,verbose_name="Operating Voltage")
    
    # Lighting Systems
    HEADLIGHT_TYPES = [
        ('HALO', 'Halogen'),
        ('HID', 'Xenon HID'),
        ('LED', 'LED'),
        ('LASER', 'Laser'),
        ('MATRIX', 'Matrix LED'),
    ]
    
    headlight_type = models.CharField(max_length=6,choices=HEADLIGHT_TYPES,verbose_name="Headlight Type")
    headlight_control = models.BooleanField(default=False,verbose_name="Automatic Headlight Control")
    headlight_range_control = models.BooleanField(default=False,verbose_name="Automatic Headlight Range Control")
    
    # Instrumentation
    instrument_cluster_type = models.CharField(
        max_length=20,
        choices=[
            ('ANALOG', 'Analog Gauges'),
            ('DIGITAL', 'Digital Display'),
            ('HYBRID', 'Hybrid Analog/Digital'),
            ('HUD', 'Head-Up Display'),
        ],
        verbose_name="Instrument Cluster Type")
    
    # Additional Electrical Components
    SOCKET_TYPES = [
        ('12V', '12V Power Socket'),
        ('USB', 'USB Port'),
        ('USB_C', 'USB-C Port'),
        ('110V', '110V AC Outlet'),
        ('230V', '230V AC Outlet'),
    ]
    socket_type = models.CharField(max_length=20,choices=SOCKET_TYPES,verbose_name="Primary Socket Type")
    
    HORN_TYPES = [
        ('SINGLE', 'Single Tone'),
        ('DUAL', 'Dual Tone'),
        ('AIR', 'Air Horn'),
        ('ELECT', 'Electronic Horn'),
    ]
    horn_type = models.CharField(max_length=6,choices=HORN_TYPES,verbose_name="Horn Type")
    
    class Meta:
        verbose_name = "Electrical System"
        verbose_name_plural = "Electrical Systems"
    
    def __str__(self):
        return f"{self.vehicle} - {self.get_operating_voltage_display()} System"

class ExteriorFeaturesAndBody(models.Model):
    vehicle = models.OneToOneField(Vehicle,on_delete=models.CASCADE,related_name='exterior',primary_key=True)
    
    # Body Structure
    BODY_STYLES = [
        ('SEDAN', 'Sedan'),
        ('COUPE', 'Coupe'),
        ('HATCH', 'Hatchback'),
        ('SUV', 'SUV'),
        ('TRUCK', 'Pickup Truck'),
        ('VAN', 'Van/Minivan'),
        ('CONV', 'Convertible'),
        ('WAGON', 'Station Wagon'),
    ]
    body_style = models.CharField(max_length=5,choices=BODY_STYLES,verbose_name="Body Style")
    
    # Glass and Windows
    WINDSHIELD_TYPES = [
        ('LAM', 'Laminated Glass'),
        ('TEM', 'Tempered Glass'),
        ('ACOU', 'Acoustic Glass'),
        ('HEAT', 'Heated Windshield'),
    ]
    windshield_type = models.CharField(max_length=4,choices=WINDSHIELD_TYPES,verbose_name="Windshield Glass Type")
    side_windows_type = models.CharField(max_length=4,choices=WINDSHIELD_TYPES,verbose_name="Side/Rear Windows Type")

    # Exterior Features
    has_chrome_package = models.BooleanField(default=False, verbose_name="Chrome Package")
    has_roof_rails = models.BooleanField(default=False, verbose_name="Roof Rails/Load Rack")
    
    ROOF_TYPES = [
        ('FIXED', 'Fixed Roof'),
        ('SUN', 'Sunroof'),
        ('PAN', 'Panoramic Roof'),
        ('SOFT', 'Soft Top'),
        ('HARD', 'Hard Top Convertible'),
        ('TARGA', 'Targa Top'),
    ]
    roof_type = models.CharField(max_length=5,choices=ROOF_TYPES,verbose_name="Roof Type")
    
    # Lighting
    has_front_fog_lamp = models.BooleanField(default=False,verbose_name="Front Fog Lamps")
    has_rear_fog_lamp = models.BooleanField(default=False,verbose_name="Rear Fog Lamp")
    has_headlight_range_control = models.BooleanField(default=False,verbose_name="Headlight Range Control")
    
    # Protection Features
    has_scuff_plates = models.BooleanField(default=False,verbose_name="Scuff Plates")
    has_loading_edge_protection = models.BooleanField(default=False,verbose_name="Loading Edge Protection")
    has_front_underbody_guard = models.BooleanField(default=False,verbose_name="Front Underbody Guard")
    
    # Wheel and Tire
    WHEEL_TYPES = [
        ('STEEL', 'Steel Wheels'),
        ('ALLOY', 'Alloy Wheels'),
        ('FORGED', 'Forged Wheels'),
        ('CARBON', 'Carbon Fiber'),
    ]
    wheel_type = models.CharField(max_length=6,choices=WHEEL_TYPES,verbose_name="Wheel Material")
    has_wheel_covers = models.BooleanField(default=False,verbose_name="Wheel Covers")
    has_lockable_wheel_bolts = models.BooleanField(default=False,verbose_name="Lockable Wheel Bolts")
    has_spare_wheel = models.BooleanField(default=False,verbose_name="Spare Wheel/Kit")
    
    # Functional Features
    has_trailer_hitch = models.BooleanField(default=False,verbose_name="Trailer Hitch")
    TAILGATE_LOCK_TYPES = [
        ('MAN', 'Manual Lock'),
        ('PWR', 'Power Lock'),
        ('HAND', 'Hands-Free'),
        ('APP', 'App Controlled'),
    ]
    tailgate_lock_type = models.CharField(max_length=4,choices=TAILGATE_LOCK_TYPES,verbose_name="Tailgate Lock Type")
    
    # Mirrors and Antennas
    MIRROR_TYPES = [
        ('MAN', 'Manual'),
        ('PWR', 'Power'),
        ('HTD', 'Heated'),
        ('AUTO', 'Auto-Dimming'),
        ('MEM', 'Memory'),
    ]
    left_mirror_type = models.CharField(max_length=4,choices=MIRROR_TYPES,verbose_name="Left Mirror Type")
    right_mirror_type = models.CharField(max_length=4,choices=MIRROR_TYPES,verbose_name="Right Mirror Type")
    
    ANTENNA_TYPES = [
        ('FIX', 'Fixed Mast'),
        ('PWR', 'Power Antenna'),
        ('SHARK', 'Shark Fin'),
        ('INT', 'Integrated'),
        ('NONE', 'No Visible Antenna'),
    ]
    antenna_type = models.CharField(max_length=5,choices=ANTENNA_TYPES,verbose_name="Antenna Type")
    
    class Meta:
        verbose_name = "Exterior Features & Body"
        verbose_name_plural = "Exterior Features & Body Components"
    
    def __str__(self):
        return f"{self.vehicle} - {self.get_body_style_display()}"

class ActiveSafetyAndADAS(models.Model):
    vehicle = models.OneToOneField(Vehicle,on_delete=models.CASCADE,related_name='active_safety',primary_key=True)
    
    # Cruise Control Systems
    CRUISE_CONTROL_TYPES = [
        ('NONE', 'No Cruise Control'),
        ('STD', 'Standard Cruise Control'),
        ('ACC', 'Adaptive Cruise Control'),
        ('ICC', 'Intelligent Cruise Control'),
        ('TJA', 'Traffic Jam Assist'),
    ]
    cruise_control_system = models.CharField(max_length=4,choices=CRUISE_CONTROL_TYPES, default='NONE',verbose_name="Cruise Control Type")
    has_speed_limiter = models.BooleanField(default=False,verbose_name="Speed Limiter Function")
    
    # Parking Assistance
    PARK_ASSIST_TYPES = [
        ('NONE', 'No Parking Assist'),
        ('REAR', 'Rear Parking Sensors'),
        ('FULL', 'Front/Rear Sensors'),
        ('CAM', 'Parking Camera'),
        ('AUTO', 'Automatic Parking'),
    ]
    park_distance_control = models.CharField(max_length=4,choices=PARK_ASSIST_TYPES,default='NONE',verbose_name="Park Distance Control")
    
    # Driver Monitoring
    DRIVER_ALERT_TYPES = [
        ('NONE', 'No Alert System'),
        ('FAT', 'Fatigue Detection'),
        ('DROWSY', 'Drowsiness Alert'),
        ('ATTN', 'Attention Monitoring'),
        ('DIST', 'Distraction Warning'),
    ]
    driver_alert_system = models.CharField(max_length=6,choices=DRIVER_ALERT_TYPES,default='NONE',verbose_name="Driver Alert System")
    
    # Tire Monitoring
    TIRE_MONITOR_TYPES = [
        ('NONE', 'No TPMS'),
        ('IND', 'Indirect TPMS'),
        ('DIR', 'Direct TPMS'),
        ('ADV', 'Advanced TPMS with Location'),
    ]
    tire_pressure_monitoring = models.CharField(max_length=4,choices=TIRE_MONITOR_TYPES,default='NONE',verbose_name="Tire Pressure Monitoring")
    
    # Lane Assistance
    LANE_ASSIST_TYPES = [
        ('NONE', 'No Lane Assist'),
        ('LDW', 'Lane Departure Warning'),
        ('LKA', 'Lane Keeping Assist'),
        ('LCA', 'Lane Centering Assist'),
        ('ELK', 'Emergency Lane Keeping'),
    ]
    lane_assist_system = models.CharField(max_length=4,choices=LANE_ASSIST_TYPES,default='NONE',verbose_name="Lane Assist System")
    
    # Warning Systems
    BLIND_SPOT_TYPES = [
        ('NONE', 'No Blind Spot Monitor'),
        ('WARN', 'Blind Spot Warning'),
        ('INT', 'Blind Spot Intervention'),
        ('CAM', 'Blind Spot Camera'),
    ]
    blind_spot_monitoring = models.CharField(max_length=4,choices=BLIND_SPOT_TYPES,default='NONE',verbose_name="Blind Spot Monitoring")
    
    COLLISION_WARNING_TYPES = [
        ('NONE', 'No Collision Warning'),
        ('FCW', 'Forward Collision Warning'),
        ('AEB', 'Automatic Emergency Braking'),
        ('PED', 'Pedestrian Detection'),
        ('CYC', 'Cyclist Detection'),
    ]
    collision_warning_system = models.CharField(max_length=4,choices=COLLISION_WARNING_TYPES,default='NONE',verbose_name="Collision Warning System")
    # Additional Features
    has_cross_traffic_alert = models.BooleanField(default=False,verbose_name="Rear Cross Traffic Alert")
    has_traffic_sign_recognition = models.BooleanField(default=False,verbose_name="Traffic Sign Recognition")
    
    class Meta:
        verbose_name = "Active Safety & ADAS"
        verbose_name_plural = "Active Safety & ADAS Systems"
    
    def __str__(self):
        return f"{self.vehicle} - {self.get_cruise_control_system_display()} | {self.get_lane_assist_system_display()}"
   