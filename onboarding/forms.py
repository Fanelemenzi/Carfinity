from django import forms
from django.contrib.auth.models import User
# from django_countries.fields import CountryField
from vehicles.models import Vehicle, VehicleImage
from onboarding.models import PendingVehicleOnboarding, CustomerOnboarding, VehicleOnboarding
from django.core.serializers import serialize
import datetime
import cloudinary.uploader

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

# --- Step 5: Vehicle Images ---
class VehicleImagesForm(forms.Form):
    front_image = forms.ImageField(
        required=False,
        label="Front View",
        help_text="Front view of the vehicle"
    )
    rear_image = forms.ImageField(
        required=False,
        label="Rear View", 
        help_text="Rear view of the vehicle"
    )
    left_side_image = forms.ImageField(
        required=False,
        label="Left Side View",
        help_text="Left side view of the vehicle"
    )
    right_side_image = forms.ImageField(
        required=False,
        label="Right Side View",
        help_text="Right side view of the vehicle"
    )
    interior_image = forms.ImageField(
        required=False,
        label="Interior View",
        help_text="Interior view of the vehicle"
    )
    engine_bay_image = forms.ImageField(
        required=False,
        label="Engine Bay",
        help_text="Engine bay view"
    )
    dashboard_image = forms.ImageField(
        required=False,
        label="Dashboard",
        help_text="Dashboard and instrument cluster"
    )
    damage_images = forms.ImageField(
        required=False,
        label="Damage/Issues",
        help_text="Any visible damage or issues"
    )
    document_images = forms.ImageField(
        required=False,
        label="Documents",
        help_text="Registration, title, or other documents"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure at least one image is uploaded
        image_fields = ['front_image', 'rear_image', 'left_side_image', 'right_side_image', 
                       'interior_image', 'engine_bay_image', 'dashboard_image', 
                       'damage_images', 'document_images']
        
        has_images = any(cleaned_data.get(field) for field in image_fields)
        if not has_images:
            raise forms.ValidationError("Please upload at least one image of the vehicle.")
        
        return cleaned_data


# --- Customer Onboarding Form ---
class CustomerOnboardingForm(forms.ModelForm):
    """Comprehensive form for customer onboarding questionnaire"""
    
    class Meta:
        model = CustomerOnboarding
        exclude = ['user', 'completed_at', 'updated_at']
        
        widgets = {
            'customer_type': forms.Select(attrs={'class': 'form-control'}),
            'preferred_communication': forms.Select(attrs={'class': 'form-control'}),
            'reminder_frequency': forms.Select(attrs={'class': 'form-control'}),
            'service_radius': forms.Select(attrs={'class': 'form-control'}),
            'monthly_maintenance_budget': forms.Select(attrs={'class': 'form-control'}),
            'mobile_service_interest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'emergency_service_interest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_knowledge': forms.Select(attrs={'class': 'form-control'}),
            'current_mechanic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Joe\'s Auto Shop'}),
            'maintenance_tracking_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Excel spreadsheet, paper records'}),
            'biggest_maintenance_challenge': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your biggest challenge...'}),
            'primary_goal': forms.Select(attrs={'class': 'form-control'}),
            'service_priority': forms.Select(attrs={'class': 'form-control'}),
            'preferred_payment_model': forms.Select(attrs={'class': 'form-control'}),
            'parts_preference': forms.Select(attrs={'class': 'form-control'}),
            'auto_insurance_provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., State Farm, Geico'}),
            'vehicle_under_warranty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'extended_warranty_interest': forms.Select(attrs={'class': 'form-control'}),
            'how_heard_about_service': forms.Select(attrs={'class': 'form-control'}),
            'potential_referrals': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'interested_in_referral_rewards': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        labels = {
            'customer_type': 'What type of customer are you?',
            'preferred_communication': 'How would you prefer to receive maintenance reminders?',
            'reminder_frequency': 'How often would you like maintenance reminders?',
            'service_radius': 'How far are you willing to travel for service?',
            'monthly_maintenance_budget': 'What\'s your approximate monthly budget for vehicle maintenance?',
            'mobile_service_interest': 'Are you interested in mobile mechanic services?',
            'emergency_service_interest': 'Would you like 24/7 emergency roadside assistance?',
            'maintenance_knowledge': 'How would you describe your car maintenance knowledge?',
            'current_mechanic': 'Do you currently have a trusted mechanic or service center?',
            'maintenance_tracking_method': 'How do you currently track vehicle maintenance?',
            'biggest_maintenance_challenge': 'What\'s your biggest challenge with vehicle maintenance?',
            'primary_goal': 'What\'s your primary goal for vehicle maintenance?',
            'service_priority': 'What\'s most important to you?',
            'preferred_payment_model': 'Payment preference',
            'parts_preference': 'Parts preference',
            'auto_insurance_provider': 'Current auto insurance provider',
            'vehicle_under_warranty': 'Is your vehicle still under manufacturer warranty?',
            'extended_warranty_interest': 'Interest in extended warranty or service protection plans',
            'how_heard_about_service': 'How did you hear about our service?',
            'potential_referrals': 'Do you know others who might benefit from our services?',
            'interested_in_referral_rewards': 'Would you be interested in earning referral rewards?',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text and styling to fields
        self.fields['customer_type'].help_text = "This helps us tailor our services to your needs"
        self.fields['preferred_communication'].help_text = "We'll use this method for maintenance reminders and updates"
        self.fields['service_radius'].help_text = "This helps us recommend nearby service providers"
        self.fields['monthly_maintenance_budget'].help_text = "This helps us recommend appropriate service plans"
        self.fields['maintenance_knowledge'].help_text = "This helps us provide appropriate guidance and explanations"
        self.fields['primary_goal'].help_text = "This helps us prioritize recommendations for you"
        self.fields['service_priority'].help_text = "This helps us match you with the right service providers"
        
        # Make certain fields required for better user experience
        self.fields['customer_type'].required = True
        self.fields['preferred_communication'].required = True
        self.fields['primary_goal'].required = True
        self.fields['service_priority'].required = True
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Custom validation logic
        customer_type = cleaned_data.get('customer_type')
        monthly_budget = cleaned_data.get('monthly_maintenance_budget')
        
        # Suggest higher budget for fleet customers
        if customer_type in ['large_fleet', 'medium_business'] and monthly_budget == 'under_50':
            self.add_error('monthly_maintenance_budget', 
                          'Fleet customers typically require higher maintenance budgets. Please consider a higher range.')
        
        return cleaned_data


# --- Vehicle Onboarding Form ---
class VehicleOnboardingForm(forms.ModelForm):
    """Form for vehicle-specific onboarding questions"""
    
    class Meta:
        model = VehicleOnboarding
        exclude = ['customer_onboarding', 'added_at', 'updated_at']
        
        widgets = {
            'vin_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 17-character VIN',
                'maxlength': '17',
                'style': 'text-transform: uppercase;'
            }),
            'make': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Toyota, Ford, Honda'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Camry, F-150, Civic'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2030',
                'placeholder': 'e.g., 2020'
            }),
            'primary_usage': forms.Select(attrs={'class': 'form-control'}),
            'current_odometer': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Current mileage',
                'min': '0'
            }),
            'estimated_annual_mileage': forms.Select(attrs={'class': 'form-control'}),
            'typical_driving_conditions': forms.Select(attrs={'class': 'form-control'}),
            'current_condition': forms.Select(attrs={'class': 'form-control'}),
            'last_oil_change': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'last_major_service': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'current_problems': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe any current issues or concerns...'
            }),
            'under_warranty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'warranty_expires': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'maintenance_preference': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Work Truck, Family Car (optional)'
            }),
        }
        
        labels = {
            'vin_number': 'Vehicle Identification Number (VIN)',
            'make': 'Vehicle Make',
            'model': 'Vehicle Model',
            'year': 'Model Year',
            'primary_usage': 'How do you primarily use this vehicle?',
            'current_odometer': 'Current Odometer Reading (miles)',
            'estimated_annual_mileage': 'Estimated Annual Mileage',
            'typical_driving_conditions': 'Typical Driving Conditions',
            'current_condition': 'Current Vehicle Condition',
            'last_oil_change': 'Last Oil Change Date',
            'last_major_service': 'Last Major Service Date',
            'current_problems': 'Current Problems or Concerns',
            'under_warranty': 'Currently Under Manufacturer Warranty',
            'warranty_expires': 'Warranty Expiration Date',
            'maintenance_preference': 'Maintenance Priority for This Vehicle',
            'vehicle_nickname': 'Vehicle Nickname',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text for key fields
        self.fields['vin_number'].help_text = "17-character Vehicle Identification Number (usually found on dashboard or driver's door)"
        self.fields['primary_usage'].help_text = "This helps us recommend appropriate maintenance schedules"
        self.fields['current_odometer'].help_text = "Current mileage reading from your odometer"
        self.fields['estimated_annual_mileage'].help_text = "This affects maintenance frequency recommendations"
        self.fields['typical_driving_conditions'].help_text = "Different conditions require different maintenance approaches"
        self.fields['current_condition'].help_text = "Honest assessment helps us provide better recommendations"
        self.fields['last_oil_change'].help_text = "Leave blank if unknown"
        self.fields['last_major_service'].help_text = "Leave blank if unknown"
        self.fields['current_problems'].help_text = "Any issues you've noticed - helps prioritize maintenance"
        self.fields['warranty_expires'].help_text = "Only fill if vehicle is under warranty"
        self.fields['maintenance_preference'].help_text = "What's most important for this specific vehicle"
        self.fields['vehicle_nickname'].help_text = "Helpful for households with multiple vehicles"
        
        # Make essential fields required
        self.fields['vin_number'].required = True
        self.fields['primary_usage'].required = True
        self.fields['current_odometer'].required = True
        self.fields['estimated_annual_mileage'].required = True
        self.fields['typical_driving_conditions'].required = True
        self.fields['current_condition'].required = True
        self.fields['maintenance_preference'].required = True
        
        # Add JavaScript for VIN validation
        self.fields['vin_number'].widget.attrs.update({
            'pattern': '[A-HJ-NPR-Z0-9]{17}',
            'title': 'Please enter a valid 17-character VIN (no I, O, or Q)'
        })
    
    def clean_vin_number(self):
        vin = self.cleaned_data.get('vin_number', '').upper()
        
        # Basic VIN validation
        if len(vin) != 17:
            raise forms.ValidationError("VIN must be exactly 17 characters long.")
        
        # Check for invalid characters
        invalid_chars = set('IOQ')
        if any(char in invalid_chars for char in vin):
            raise forms.ValidationError("VIN cannot contain the letters I, O, or Q.")
        
        # Check for valid characters only
        valid_chars = set('ABCDEFGHJKLMNPRSTUVWXYZ0123456789')
        if not all(char in valid_chars for char in vin):
            raise forms.ValidationError("VIN contains invalid characters.")
        
        return vin
    
    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year:
            current_year = datetime.datetime.now().year
            if year < 1900 or year > current_year + 1:
                raise forms.ValidationError(f"Please enter a valid year between 1900 and {current_year + 1}.")
        return year
    
    def clean_current_odometer(self):
        odometer = self.cleaned_data.get('current_odometer')
        if odometer is not None and odometer < 0:
            raise forms.ValidationError("Odometer reading cannot be negative.")
        if odometer is not None and odometer > 999999:
            raise forms.ValidationError("Odometer reading seems unusually high. Please verify.")
        return odometer
    
    def clean_warranty_expires(self):
        warranty_expires = self.cleaned_data.get('warranty_expires')
        under_warranty = self.cleaned_data.get('under_warranty')
        
        if under_warranty and not warranty_expires:
            raise forms.ValidationError("Please provide warranty expiration date if vehicle is under warranty.")
        
        if warranty_expires and warranty_expires < datetime.date.today():
            raise forms.ValidationError("Warranty expiration date cannot be in the past.")
        
        return warranty_expires
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Cross-field validation
        make = cleaned_data.get('make')
        model = cleaned_data.get('model')
        year = cleaned_data.get('year')
        vin = cleaned_data.get('vin_number')
        
        # Only suggest VIN lookup if VIN is provided but make/model/year are ALL missing
        # Don't block form submission if some fields are filled
        if vin and not any([make, model, year]):
            # This is just a suggestion, not an error
            pass
        
        # Validate service dates make sense
        last_oil_change = cleaned_data.get('last_oil_change')
        last_major_service = cleaned_data.get('last_major_service')
        
        if last_oil_change and last_oil_change > datetime.date.today():
            self.add_error('last_oil_change', "Oil change date cannot be in the future.")
        
        if last_major_service and last_major_service > datetime.date.today():
            self.add_error('last_major_service', "Service date cannot be in the future.")
        
        return cleaned_data
