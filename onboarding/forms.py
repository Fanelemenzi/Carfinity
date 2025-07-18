from django import forms
from django.contrib.auth.models import User
from django_countries.fields import CountryField

# --- Step 1: Client Info ---
class ClientForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Client Account",
        help_text="Select the client who will own the vehicle."
    )

# --- Step 2: Vehicle Info ---
class VehicleForm(forms.Form):
    vin = forms.CharField(max_length=20, label="VIN", help_text="Vehicle Identification Number.")
    make = forms.CharField(max_length=50, label="Make", help_text="Vehicle manufacturer (e.g., Toyota, Ford).")
    model = forms.CharField(max_length=50, label="Model", help_text="Vehicle model (e.g., Corolla, F-150).")
    manufacture_year = forms.IntegerField(label="Manufacture Year", help_text="Year the vehicle was manufactured.")
    body_type = forms.CharField(max_length=20, label="Body Type", required=False, help_text="Type of vehicle body (e.g., Sedan, SUV).")
    engine_code = forms.CharField(max_length=20, label="Engine Code", required=False, help_text="Engine code or identifier.")
    interior_color = forms.CharField(max_length=30, label="Interior Color", required=False, help_text="Color of the vehicle's interior.")
    exterior_color = forms.CharField(max_length=30, label="Exterior Color", required=False, help_text="Color of the vehicle's exterior.")
    purchase_date = forms.DateField(label="Purchase Date", required=False, widget=forms.DateInput(attrs={'type': 'date'}), help_text="Date the vehicle was purchased.")
    license_plate = forms.CharField(max_length=20, label="License Plate", required=False, help_text="Vehicle's license plate number.")
    fuel_type = forms.CharField(max_length=50, label="Fuel Type", required=False, help_text="Type of fuel used (e.g., Gasoline, Diesel, Electric).")
    transmission_type = forms.CharField(max_length=50, label="Transmission Type", required=False, help_text="Type of transmission (e.g., Automatic, Manual).")
    powertrain_displacement = forms.CharField(max_length=50, label="Powertrain Displacement", required=False, help_text="Engine displacement (e.g., 2.0L).")
    powertrain_power = forms.CharField(max_length=5, label="Powertrain Power", required=False, help_text="Engine power (e.g., 150hp).")
    plant_location = forms.CharField(max_length=50, label="Plant Location (Country)", required=False, help_text="Country where the vehicle was manufactured.")
    created_at = forms.DateTimeField(label="Created At", required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), help_text="Date and time the record was created. (Usually auto-filled)")
    updated_at = forms.DateTimeField(label="Updated At", required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), help_text="Date and time the record was last updated. (Usually auto-filled)")
    start_date = forms.DateField(label="Ownership Start Date", widget=forms.DateInput(attrs={'type': 'date'}), help_text="Date when the client took ownership.")

# --- Step 3: Vehicle Status ---
class VehicleStatusForm(forms.Form):
    accident_history = forms.ChoiceField(
        choices=[("NHA","No History of Accidents"), ("OIIA", "Once Involved In Accident"), ("CAD", "Currently Accident Damaged")],
        label="Accident History",
        help_text="History of accidents involving the vehicle."
    )
    odometer_fraud = forms.ChoiceField(
        choices=[("NOF", "No Odometer Fraud"), ("SOF",  "Suspected Odometer Fraud")],
        label="Odometer Fraud",
        help_text="Indicates if the vehicle has suspected odometer fraud."
    )
    theft_involvement = forms.ChoiceField(
        choices=[("NHT", "No History of Theft"), ("OIT",  "Once Involved In Theft"), ("STI", "Suspected Theft Involvement")],
        label="Theft Involvement",
        help_text="Indicates if the vehicle has been involved in theft."
    )
    legal_status = forms.ChoiceField(
        choices=[("LG", "Looks Good"), ("ILA",  "Involved Legal Action")],
        label="Legal Status",
        help_text="Indicates if the vehicle is involved in any legal action or attached to bank."
    )
    owner_history = forms.IntegerField(
        label="Owner History",
        min_value=1,
        max_value=100,
        help_text="Number of previous owners of the vehicle."
    )

# --- Step 4: Vehicle Equipment (all remaining fields) ---
class VehicleEquipmentForm(forms.Form):
    # PowertrainAndDrivetrain fields
    base_engine = forms.CharField(max_length=100, required=False, label="Base Engine", help_text="Type and specifications of the base engine.")
    engine_displacement = forms.DecimalField(max_digits=3, decimal_places=1, required=False, label="Engine Displacement (L)")
    engine_power = forms.IntegerField(required=False, label="Engine Power (hp)")
    transmission_specifications = forms.CharField(max_length=100, required=False, label="Transmission Specifications")
    transmission_type = forms.ChoiceField(
        choices=[('MT', 'Manual Transmission'), ('AT', 'Automatic Transmission'), ('CVT', 'Continuously Variable Transmission'), ('DCT', 'Dual-Clutch Transmission'), ('AMT', 'Automated Manual Transmission')],
        required=False, label="Transmission Type"
    )
    gear_count = forms.IntegerField(required=False, min_value=1, max_value=10, label="Gear Count")
    drive_layout = forms.ChoiceField(
        choices=[('FWD', 'Front-Wheel Drive'), ('RWD', 'Rear-Wheel Drive'), ('AWD', 'All-Wheel Drive'), ('4WD', 'Four-Wheel Drive')],
        required=False, label="Drive Layout"
    )
    fuel_system = forms.ChoiceField(
        choices=[('G', 'Gasoline'), ('D', 'Diesel'), ('E', 'Electric'), ('H', 'Hybrid'), ('P', 'Plug-in Hybrid'), ('F', 'Fuel Cell')],
        required=False, label="Fuel System"
    )
    emissions_standard = forms.ChoiceField(
        choices=[('EU1', 'Euro 1'), ('EU2', 'Euro 2'), ('EU3', 'Euro 3'), ('EU4', 'Euro 4'), ('EU5', 'Euro 5'), ('EU6', 'Euro 6'), ('EPA1', 'EPA Tier 1')],
        required=False, label="Emissions Standard"
    )
    has_start_stop = forms.BooleanField(required=False, label="Has Start-Stop System")
    has_regenerative_braking = forms.BooleanField(required=False, label="Has Regenerative Braking")
    gearshift_position = forms.ChoiceField(
        choices=[('C', 'Center Console'), ('S', 'Steering Column'), ('D', 'Dashboard')],
        required=False, label="Gearshift Position"
    )
    gearshift_material = forms.CharField(max_length=50, required=False, label="Gearshift Material")
    notes = forms.CharField(widget=forms.Textarea, required=False, label="Powertrain Notes")
    # ChassisSuspensionAndBraking fields
    front_suspension = forms.ChoiceField(
        choices=[('MACP', 'MacPherson Strut'), ('DUBL', 'Double Wishbone'), ('MULT', 'Multi-Link'), ('LEAF', 'Leaf Spring'), ('AIR', 'Air Suspension'), ('ADAP', 'Adaptive Suspension')],
        required=False, label="Front Suspension Type"
    )
    rear_suspension = forms.ChoiceField(
        choices=[('MACP', 'MacPherson Strut'), ('DUBL', 'Double Wishbone'), ('MULT', 'Multi-Link'), ('LEAF', 'Leaf Spring'), ('AIR', 'Air Suspension'), ('ADAP', 'Adaptive Suspension')],
        required=False, label="Rear Suspension Type"
    )
    front_brake_type = forms.ChoiceField(
        choices=[('DISC', 'Disc Brakes'), ('DRUM', 'Drum Brakes'), ('CERM', 'Ceramic Discs'), ('CARB', 'Carbon Ceramic')],
        required=False, label="Front Brake Type"
    )
    rear_brake_type = forms.ChoiceField(
        choices=[('DISC', 'Disc Brakes'), ('DRUM', 'Drum Brakes'), ('CERM', 'Ceramic Discs'), ('CARB', 'Carbon Ceramic')],
        required=False, label="Rear Brake Type"
    )
    brake_systems = forms.ChoiceField(
        choices=[('ABS', 'Anti-lock Braking System'), ('EBD', 'Electronic Brakeforce Distribution'), ('BAS', 'Brake Assist System'), ('REGEN', 'Regenerative Braking')],
        required=False, label="Primary Brake System"
    )
    parking_brake_type = forms.ChoiceField(
        choices=[('EPB', 'Electronic Parking Brake'), ('MECH', 'Mechanical Lever'), ('PEDAL', 'Foot Pedal'), ('INTEG', 'Integrated with Service Brakes')],
        required=False, label="Parking Brake Type"
    )
    steering_system = forms.ChoiceField(
        choices=[('RACK', 'Rack and Pinion'), ('RECIRC', 'Recirculating Ball'), ('EPAS', 'Electric Power Assist'), ('HPAS', 'Hydraulic Power Assist')],
        required=False, label="Steering System Type"
    )
    steering_wheel_features = forms.ChoiceField(
        choices=[('TILT', 'Tilt Adjustment'), ('TEL', 'Telescopic Adjustment'), ('HEAT', 'Heated'), ('PADDLE', 'Paddle Shifters'), ('CONTROLS', 'Integrated Controls')],
        required=False, label="Steering Wheel Features"
    )
    has_park_distance_control = forms.BooleanField(required=False, label="Park Distance Control")
    # ElectricalSystem fields
    primary_battery_type = forms.ChoiceField(
        choices=[('FLA', 'Flooded Lead Acid'), ('AGM', 'Absorbent Glass Mat'), ('GEL', 'Gel Cell'), ('LITH', 'Lithium-Ion'), ('EFB', 'Enhanced Flooded Battery')],
        required=False, label="Primary Battery Type"
    )
    primary_battery_capacity = forms.IntegerField(required=False, label="Primary Battery Capacity (Ah)")
    has_second_battery = forms.BooleanField(required=False, label="Second Battery Installed")
    second_battery_type = forms.ChoiceField(
        choices=[('FLA', 'Flooded Lead Acid'), ('AGM', 'Absorbent Glass Mat'), ('GEL', 'Gel Cell'), ('LITH', 'Lithium-Ion'), ('EFB', 'Enhanced Flooded Battery')],
        required=False, label="Second Battery Type"
    )
    second_battery_capacity = forms.IntegerField(required=False, label="Second Battery Capacity (Ah)")
    alternator_output = forms.IntegerField(required=False, label="Alternator Output (A)")
    operating_voltage = forms.ChoiceField(
        choices=[(12, '12V System'), (24, '24V System'), (48, '48V System (Mild Hybrid)'), (400, '400V System (EV)'), (800, '800V System (High Performance EV)')],
        required=False, label="Operating Voltage"
    )
    headlight_type = forms.ChoiceField(
        choices=[('HALO', 'Halogen'), ('HID', 'Xenon HID'), ('LED', 'LED'), ('LASER', 'Laser'), ('MATRIX', 'Matrix LED')],
        required=False, label="Headlight Type"
    )
    headlight_control = forms.BooleanField(required=False, label="Automatic Headlight Control")
    headlight_range_control = forms.BooleanField(required=False, label="Automatic Headlight Range Control")
    instrument_cluster_type = forms.ChoiceField(
        choices=[('ANALOG', 'Analog Gauges'), ('DIGITAL', 'Digital Display'), ('HYBRID', 'Hybrid Analog/Digital'), ('HUD', 'Head-Up Display')],
        required=False, label="Instrument Cluster Type"
    )
    socket_type = forms.ChoiceField(
        choices=[('12V', '12V Power Socket'), ('USB', 'USB Port'), ('USB_C', 'USB-C Port'), ('110V', '110V AC Outlet'), ('230V', '230V AC Outlet')],
        required=False, label="Primary Socket Type"
    )
    horn_type = forms.ChoiceField(
        choices=[('SINGLE', 'Single Tone'), ('DUAL', 'Dual Tone'), ('AIR', 'Air Horn'), ('ELECT', 'Electronic Horn')],
        required=False, label="Horn Type"
    )
    # ExteriorFeaturesAndBody fields
    body_style = forms.ChoiceField(
        choices=[('SEDAN', 'Sedan'), ('COUPE', 'Coupe'), ('HATCH', 'Hatchback'), ('SUV', 'SUV'), ('TRUCK', 'Pickup Truck'), ('VAN', 'Van/Minivan'), ('CONV', 'Convertible'), ('WAGON', 'Station Wagon')],
        required=False, label="Body Style"
    )
    windshield_type = forms.ChoiceField(
        choices=[('LAM', 'Laminated Glass'), ('TEM', 'Tempered Glass'), ('ACOU', 'Acoustic Glass'), ('HEAT', 'Heated Windshield')],
        required=False, label="Windshield Glass Type"
    )
    side_windows_type = forms.ChoiceField(
        choices=[('LAM', 'Laminated Glass'), ('TEM', 'Tempered Glass'), ('ACOU', 'Acoustic Glass'), ('HEAT', 'Heated Windshield')],
        required=False, label="Side/Rear Windows Type"
    )
    has_chrome_package = forms.BooleanField(required=False, label="Chrome Package")
    has_roof_rails = forms.BooleanField(required=False, label="Roof Rails/Load Rack")
    roof_type = forms.ChoiceField(
        choices=[('FIXED', 'Fixed Roof'), ('SUN', 'Sunroof'), ('PAN', 'Panoramic Roof'), ('SOFT', 'Soft Top'), ('HARD', 'Hard Top Convertible'), ('TARGA', 'Targa Top')],
        required=False, label="Roof Type"
    )
    has_front_fog_lamp = forms.BooleanField(required=False, label="Front Fog Lamps")
    has_rear_fog_lamp = forms.BooleanField(required=False, label="Rear Fog Lamp")
    has_headlight_range_control = forms.BooleanField(required=False, label="Headlight Range Control")
    has_scuff_plates = forms.BooleanField(required=False, label="Scuff Plates")
    has_loading_edge_protection = forms.BooleanField(required=False, label="Loading Edge Protection")
    has_front_underbody_guard = forms.BooleanField(required=False, label="Front Underbody Guard")
    wheel_type = forms.ChoiceField(
        choices=[('STEEL', 'Steel Wheels'), ('ALLOY', 'Alloy Wheels'), ('FORGED', 'Forged Wheels'), ('CARBON', 'Carbon Fiber')],
        required=False, label="Wheel Material"
    )
    has_wheel_covers = forms.BooleanField(required=False, label="Wheel Covers")
    has_lockable_wheel_bolts = forms.BooleanField(required=False, label="Lockable Wheel Bolts")
    has_spare_wheel = forms.BooleanField(required=False, label="Spare Wheel/Kit")
    has_trailer_hitch = forms.BooleanField(required=False, label="Trailer Hitch")
    tailgate_lock_type = forms.ChoiceField(
        choices=[('MAN', 'Manual Lock'), ('PWR', 'Power Lock'), ('HAND', 'Hands-Free'), ('APP', 'App Controlled')],
        required=False, label="Tailgate Lock Type"
    )
    left_mirror_type = forms.ChoiceField(
        choices=[('MAN', 'Manual'), ('PWR', 'Power'), ('HTD', 'Heated'), ('AUTO', 'Auto-Dimming'), ('MEM', 'Memory')],
        required=False, label="Left Mirror Type"
    )
    right_mirror_type = forms.ChoiceField(
        choices=[('MAN', 'Manual'), ('PWR', 'Power'), ('HTD', 'Heated'), ('AUTO', 'Auto-Dimming'), ('MEM', 'Memory')],
        required=False, label="Right Mirror Type"
    )
    antenna_type = forms.ChoiceField(
        choices=[('FIX', 'Fixed Mast'), ('PWR', 'Power Antenna'), ('SHARK', 'Shark Fin'), ('INT', 'Integrated'), ('NONE', 'No Visible Antenna')],
        required=False, label="Antenna Type"
    )
    # ActiveSafetyAndADAS fields
    cruise_control_system = forms.ChoiceField(
        choices=[('NONE', 'No Cruise Control'), ('STD', 'Standard Cruise Control'), ('ACC', 'Adaptive Cruise Control'), ('ICC', 'Intelligent Cruise Control'), ('TJA', 'Traffic Jam Assist')],
        required=False, label="Cruise Control Type"
    )
    has_speed_limiter = forms.BooleanField(required=False, label="Speed Limiter Function")
    park_distance_control = forms.ChoiceField(
        choices=[('NONE', 'No Parking Assist'), ('REAR', 'Rear Parking Sensors'), ('FULL', 'Front/Rear Sensors'), ('CAM', 'Parking Camera'), ('AUTO', 'Automatic Parking')],
        required=False, label="Park Distance Control"
    )
    driver_alert_system = forms.ChoiceField(
        choices=[('NONE', 'No Alert System'), ('FAT', 'Fatigue Detection'), ('DROWSY', 'Drowsiness Alert'), ('ATTN', 'Attention Monitoring'), ('DIST', 'Distraction Warning')],
        required=False, label="Driver Alert System"
    )
    tire_pressure_monitoring = forms.ChoiceField(
        choices=[('NONE', 'No TPMS'), ('IND', 'Indirect TPMS'), ('DIR', 'Direct TPMS'), ('ADV', 'Advanced TPMS with Location')],
        required=False, label="Tire Pressure Monitoring"
    )
    lane_assist_system = forms.ChoiceField(
        choices=[('NONE', 'No Lane Assist'), ('LDW', 'Lane Departure Warning'), ('LKA', 'Lane Keeping Assist'), ('LCA', 'Lane Centering Assist'), ('ELK', 'Emergency Lane Keeping')],
        required=False, label="Lane Assist System"
    )
    blind_spot_monitoring = forms.ChoiceField(
        choices=[('NONE', 'No Blind Spot Monitor'), ('WARN', 'Blind Spot Warning'), ('INT', 'Blind Spot Intervention'), ('CAM', 'Blind Spot Camera')],
        required=False, label="Blind Spot Monitoring"
    )
    collision_warning_system = forms.ChoiceField(
        choices=[('NONE', 'No Collision Warning'), ('FCW', 'Forward Collision Warning'), ('AEB', 'Automatic Emergency Braking'), ('PED', 'Pedestrian Detection'), ('CYC', 'Cyclist Detection')],
        required=False, label="Collision Warning System"
    )
    has_cross_traffic_alert = forms.BooleanField(required=False, label="Rear Cross Traffic Alert")
    has_traffic_sign_recognition = forms.BooleanField(required=False, label="Traffic Sign Recognition")
