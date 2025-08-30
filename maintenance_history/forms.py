from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import MaintenanceRecord, PartUsage, Inspection, Inspections, InitialInspection
from maintenance.models import Part, ScheduledMaintenance
import json

class MaintenanceRecordForm(forms.ModelForm):
    # Hidden field to store part selection data from JavaScript
    parts_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'vehicle', 
            'scheduled_maintenance',
            'work_done',
            'mileage',
            'notes',
            'service_image',
            'image_type',
            'image_description'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'scheduled_maintenance': forms.Select(attrs={'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'work_done': forms.Textarea(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Describe work performed...'
            }),
            'mileage': forms.NumberInput(attrs={'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'notes': forms.Textarea(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Additional notes...'
            }),
            'service_image': forms.FileInput(attrs={
                'class': 'w-full mt-1 block text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': 'image/*'
            }),
            'image_type': forms.Select(attrs={'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'}),
            'image_description': forms.TextInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Brief description of the image...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_parts = []
        
        # Set initial empty choice for scheduled maintenance
        self.fields['scheduled_maintenance'].empty_label = "Select a vehicle first"
        self.fields['scheduled_maintenance'].queryset = ScheduledMaintenance.objects.none()
        
    def clean_parts_data(self):
        """Validate and parse parts data from JavaScript"""
        parts_data = self.cleaned_data.get('parts_data', '')
        
        if not parts_data:
            return []
            
        try:
            parts_list = json.loads(parts_data)
        except json.JSONDecodeError:
            raise ValidationError("Invalid parts data format.")
            
        if not isinstance(parts_list, list):
            raise ValidationError("Parts data must be a list.")
            
        validated_parts = []
        for part_data in parts_list:
            if not isinstance(part_data, dict):
                raise ValidationError("Each part entry must be an object.")
                
            # Validate required fields
            required_fields = ['id', 'quantity']
            for field in required_fields:
                if field not in part_data:
                    raise ValidationError(f"Missing required field: {field}")
                    
            part_id = part_data.get('id')
            quantity = part_data.get('quantity')
            
            # Validate part exists
            try:
                part = Part.objects.get(id=part_id)
            except Part.DoesNotExist:
                raise ValidationError(f"Part with ID {part_id} does not exist.")
                
            # Validate quantity
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValidationError(f"Quantity for {part.name} must be greater than 0.")
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid quantity for {part.name}.")
                
            # Validate stock availability
            if part.stock_quantity < quantity:
                raise ValidationError(
                    f"Insufficient stock for {part.name}. "
                    f"Available: {part.stock_quantity}, Requested: {quantity}"
                )
                
            validated_parts.append({
                'part': part,
                'quantity': quantity,
                'unit_cost': part.cost
            })
            
        return validated_parts
    
    def clean_service_image(self):
        """Validate service image upload"""
        image = self.cleaned_data.get('service_image')
        
        if image:
            # Check file size (limit to 10MB)
            if image.size > 10 * 1024 * 1024:
                raise ValidationError("Image file size cannot exceed 10MB.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError("Only JPEG, PNG, GIF, and WebP images are allowed.")
        
        return image
        
    def clean(self):
        """Additional form validation"""
        cleaned_data = super().clean()
        
        # Store validated parts for use in save method
        self.selected_parts = self.clean_parts_data()
        
        # Validate image type is provided if image is uploaded
        service_image = cleaned_data.get('service_image')
        image_type = cleaned_data.get('image_type')
        
        if service_image and not image_type:
            raise ValidationError("Please select an image type when uploading an image.")
        
        return cleaned_data
        
    @transaction.atomic
    def save(self, commit=True):
        """Save maintenance record and associated part usage records"""
        # Save the maintenance record
        maintenance_record = super().save(commit=commit)
        
        if commit and self.selected_parts:
            # Create PartUsage records and update inventory
            for part_data in self.selected_parts:
                part = part_data['part']
                quantity = part_data['quantity']
                unit_cost = part_data['unit_cost']
                
                # Create PartUsage record
                PartUsage.objects.create(
                    maintenance_record=maintenance_record,
                    part=part,
                    quantity=quantity,
                    unit_cost=unit_cost
                )
                
                # Update part inventory
                if not part.reduce_stock(quantity):
                    raise ValidationError(
                        f"Failed to update stock for {part.name}. "
                        f"This may be due to concurrent modifications."
                    )
                    
        return maintenance_record
        
    def get_selected_parts_summary(self):
        """Get summary of selected parts for display"""
        if not self.selected_parts:
            return {
                'parts': [],
                'total_cost': 0
            }
            
        summary = []
        total_cost = 0
        
        for part_data in self.selected_parts:
            part = part_data['part']
            quantity = part_data['quantity']
            unit_cost = part_data['unit_cost'] or 0
            line_total = unit_cost * quantity
            total_cost += line_total
            
            summary.append({
                'name': part.name,
                'part_number': part.part_number,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'line_total': line_total
            })
            
        return {
            'parts': summary,
            'total_cost': total_cost
        }

class InspectionForm(forms.ModelForm):
    """
    Django form for the 50-Point Quarterly Vehicle Health Inspection Checklist
    Based on the Inspections model
    """
    
    class Meta:
        model = Inspections
        fields = [
            'inspection',
            'technician',
            'inspection_date',
            'mileage_at_inspection',
            # Engine & Powertrain
            'engine_oil_level',
            'oil_filter_condition',
            'coolant_level',
            'drive_belts',
            'hoses_condition',
            'air_filter',
            'cabin_air_filter',
            'transmission_fluid',
            'engine_mounts',
            'fluid_leaks',
            'engine_notes',
            # Electrical & Battery
            'battery_voltage',
            'battery_terminals',
            'alternator_output',
            'starter_motor',
            'fuses_relays',
            'electrical_notes',
            # Brakes & Suspension
            'brake_pads',
            'brake_discs',
            'brake_fluid',
            'parking_brake',
            'shocks_struts',
            'suspension_bushings',
            'wheel_bearings',
            'brakes_notes',
            # Steering & Tires
            'steering_response',
            'steering_fluid',
            'tire_tread_depth',
            'tire_pressure',
            'tire_wear_patterns',
            'wheels_rims',
            'steering_notes',
            # Exhaust & Emissions
            'exhaust_system',
            'catalytic_converter',
            'exhaust_warning_lights',
            'exhaust_notes',
            # Safety Equipment
            'seat_belts',
            'airbags',
            'horn_function',
            'first_aid_kit',
            'warning_triangle',
            'safety_notes',
            # Lighting & Visibility
            'headlights',
            'brake_lights',
            'turn_signals',
            'interior_lights',
            'windshield',
            'wiper_blades',
            'rear_defogger',
            'mirrors',
            'lighting_notes',
            # HVAC & Interior
            'air_conditioning',
            'ventilation',
            'seat_adjustments',
            'power_windows',
            'hvac_notes',
            # Technology & Driver Assist
            'infotainment_system',
            'rear_view_camera',
            'technology_notes',
            # Overall
            'overall_notes',
            'recommendations',
            'is_completed'
        ]
        
        widgets = {
            'inspection': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'inspection_date': forms.DateTimeInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'mileage_at_inspection': forms.NumberInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter current mileage',
                'min': '0',
                'step': '1'
            }),
            'is_completed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        # Handle pre-selected inspection from URL parameter
        inspection_id = kwargs.pop('inspection_id', None)
        super().__init__(*args, **kwargs)
        
        # If inspection_id is provided, pre-select it and hide the field
        if inspection_id:
            try:
                inspection = Inspection.objects.get(id=inspection_id)
                self.fields['inspection'].initial = inspection
                self.fields['inspection'].widget = forms.HiddenInput()
                self.fields['technician'].initial = None  # Will be set in view
            except Inspection.DoesNotExist:
                pass
        
        # Add common styling to all status choice fields
        status_widget_attrs = {
            'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
        }
        
        # Apply styling to all status fields
        status_fields = [
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
        
        for field_name in status_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update(status_widget_attrs)
        
        # Add styling to notes fields
        notes_widget_attrs = {
            'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Enter any observations or notes...'
        }
        
        notes_fields = [
            'engine_notes', 'electrical_notes', 'brakes_notes', 'steering_notes', 'exhaust_notes',
            'safety_notes', 'lighting_notes', 'hvac_notes', 'technology_notes', 'overall_notes', 'recommendations'
        ]
        
        for field_name in notes_fields:
            if field_name in self.fields:
                self.fields[field_name].widget = forms.Textarea(attrs=notes_widget_attrs)
    
    def clean_mileage_at_inspection(self):
        """Custom validation for mileage field"""
        mileage = self.cleaned_data.get('mileage_at_inspection')
        
        if mileage is None or mileage == '':
            raise ValidationError("Vehicle mileage is required.")
        
        try:
            mileage = int(mileage)
        except (ValueError, TypeError):
            raise ValidationError("Please enter a valid mileage number.")
        
        if mileage < 0:
            raise ValidationError("Mileage cannot be negative.")
        
        if mileage > 9999999:  # Reasonable upper limit
            raise ValidationError("Mileage seems unreasonably high. Please check the value.")
        
        return mileage
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if form is marked as completed
        is_completed = cleaned_data.get('is_completed', False)
        
        if is_completed:
            # Validate that critical inspection points are filled
            critical_fields = [
                'engine_oil_level', 'brake_pads', 'brake_fluid', 'tire_tread_depth', 
                'tire_pressure', 'headlights', 'brake_lights', 'seat_belts'
            ]
            
            missing_fields = []
            for field in critical_fields:
                if not cleaned_data.get(field):
                    missing_fields.append(self.fields[field].label)
            
            if missing_fields:
                raise ValidationError(
                    f"The following critical inspection points must be completed before marking as finished: {', '.join(missing_fields)}"
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set completion timestamp if form is being marked as completed
        if instance.is_completed and not instance.completed_at:
            from django.utils import timezone
            instance.completed_at = timezone.now()
        
        if commit:
            instance.save()
        
        return instance


class InspectionRecordForm(forms.ModelForm):
    """
    Form for the basic Inspection record (not the detailed checklist)
    """
    class Meta:
        model = Inspection
        fields = [
            'vehicle',
            'inspection_number',
            'year',
            'inspection_result',
            'vehicle_health_index',
            'inspection_date',
            'link_to_results',
            'inspection_pdf'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'inspection_number': forms.TextInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter inspection number'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'min': '1900',
                'max': '2100'
            }),
            'inspection_result': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'carfinity_rating': forms.TextInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter Carfinity rating'
            }),
            'inspection_date': forms.DateInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'link_to_results': forms.URLInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'https://example.com/inspection-results'
            }),
            'inspection_pdf': forms.FileInput(attrs={
                'class': 'w-full mt-1 block text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': '.pdf'
            })
        }
    
    def clean_inspection_pdf(self):
        pdf_file = self.cleaned_data.get('inspection_pdf')
        
        if pdf_file:
            # Check file size (limit to 10MB)
            if pdf_file.size > 10 * 1024 * 1024:
                raise ValidationError("PDF file size cannot exceed 10MB.")
            
            # Check file extension
            if not pdf_file.name.lower().endswith('.pdf'):
                raise ValidationError("Only PDF files are allowed.")
        
        return pdf_file
    
    def clean_inspection_number(self):
        inspection_number = self.cleaned_data.get('inspection_number')
        
        # Check for uniqueness (excluding current instance if editing)
        queryset = Inspection.objects.filter(inspection_number=inspection_number)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError("An inspection with this number already exists.")
        
        return inspection_number


class InitialInspectionForm(forms.ModelForm):
    """
    Django form for the 160-Point Initial Vehicle Inspection for Second-Hand Vehicles
    Based on the InitialInspection model
    """
    
    class Meta:
        model = InitialInspection
        fields = [
            # Basic Information
            'vehicle',
            'inspection_number',
            'technician',
            'inspection_date',
            'mileage_at_inspection',
            
            # Road Test (Points 1-33)
            'cold_engine_operation',
            'throttle_operation',
            'warmup_operation',
            'operating_temp_performance',
            'normal_operating_temp',
            'brake_vibrations',
            'engine_fan_operation',
            'brake_pedal_specs',
            'abs_operation',
            'parking_brake_operation',
            'seat_belt_condition',
            'seat_belt_operation',
            'transmission_operation',
            'auto_trans_cold',
            'auto_trans_operating',
            'steering_feel',
            'steering_centered',
            'vehicle_tracking',
            'tilt_telescopic_steering',
            'washer_fluid_spray',
            'front_wipers',
            'rear_wipers',
            'wiper_rest_position',
            'wiper_blade_replacement',
            'speedometer_function',
            'odometer_function',
            'cruise_control',
            'heater_operation',
            'ac_operation',
            'engine_noise',
            'interior_noise',
            'wind_road_noise',
            'tire_vibration',
            'road_test_notes',
            
            # Frame, Structure & Underbody (Points 34-54)
            'frame_unibody_condition',
            'panel_alignment',
            'underbody_condition',
            'suspension_leaks_wear',
            'struts_shocks_condition',
            'power_steering_leaks',
            'wheel_covers',
            'tire_condition',
            'tread_depth',
            'tire_specifications',
            'brake_calipers_lines',
            'brake_system_equipment',
            'brake_pad_life',
            'brake_rotors_drums',
            'exhaust_system',
            'engine_trans_mounts',
            'drive_axle_shafts',
            'cv_joints_boots',
            'engine_fluid_leaks',
            'transmission_leaks',
            'differential_fluid',
            'frame_structure_notes',
            
            # Under Hood (Points 55-68)
            'drive_belts_hoses',
            'underhood_labels',
            'air_filter_condition',
            'battery_damage',
            'battery_test',
            'battery_posts_cables',
            'battery_secured',
            'charging_system',
            'coolant_level',
            'coolant_protection',
            'oil_filter_change',
            'oil_sludge_check',
            'fluid_levels',
            'fluid_contamination',
            'under_hood_notes',
            
            # Functional & Walkaround (Points 69-82)
            'owners_manual',
            'fuel_gauge',
            'battery_voltage_gauge',
            'temp_gauge',
            'horn_function',
            'airbags_present',
            'headlight_alignment',
            'emissions_test',
            'tail_lights',
            'brake_lights',
            'side_marker_lights',
            'backup_lights',
            'license_plate_lights',
            'exterior_lights_condition',
            'functional_walkaround_notes',
            
            # Interior Functions (Points 83-128)
            'instrument_panel',
            'hvac_panel',
            'instrument_dimmer',
            'turn_signals',
            'hazard_flashers',
            'rearview_mirror',
            'exterior_mirrors',
            'remote_mirror_control',
            'glass_condition',
            'window_tint',
            'dome_courtesy_lights',
            'power_windows',
            'window_locks',
            'audio_system',
            'audio_speakers',
            'antenna',
            'clock_operation',
            'power_outlet',
            'ashtrays',
            'headliner_trim',
            'floor_mats',
            'doors_operation',
            'door_locks',
            'keyless_entry',
            'master_keys',
            'theft_deterrent',
            'seat_adjustments',
            'seat_heaters',
            'memory_seat',
            'headrests',
            'rear_defogger',
            'defogger_indicator',
            'luggage_light',
            'luggage_cleanliness',
            'hood_trunk_latches',
            'emergency_trunk_release',
            'fuel_door_release',
            'spare_tire_cover',
            'spare_tire_present',
            'spare_tire_tread',
            'spare_tire_pressure',
            'spare_tire_damage',
            'spare_tire_secured',
            'jack_tools',
            'acceptable_aftermarket',
            'unacceptable_removal',
            'interior_functions_notes',
            
            # Exterior Appearance (Points 129-152)
            'body_surface',
            'exterior_cleanliness',
            'paint_finish',
            'paint_scratches',
            'wheels_cleanliness',
            'wheel_wells',
            'tires_dressed',
            'engine_compartment_clean',
            'insulation_pad',
            'engine_dressed',
            'door_jambs',
            'glove_console',
            'cabin_air_filter',
            'seats_carpets',
            'vehicle_odors',
            'glass_cleanliness',
            'interior_debris',
            'dash_vents',
            'crevices_clean',
            'upholstery_panels',
            'paint_repairs',
            'glass_repairs',
            'bumpers_condition',
            'interior_surfaces',
            'exterior_appearance_notes',
            
            # Optional/Additional Systems (Points 153-160)
            'sunroof_convertible',
            'seat_heaters_optional',
            'navigation_system',
            'head_unit_software',
            'transfer_case',
            'truck_bed_condition',
            'truck_bed_liner',
            'backup_camera',
            'optional_systems_notes',
            
            # Advanced Safety Systems
            'sos_indicator',
            'lane_keep_assist',
            'adaptive_cruise',
            'parking_assist',
            'safety_systems_notes',
            
            # Hybrid Components
            'hybrid_battery',
            'battery_control_module',
            'hybrid_power_mgmt',
            'electric_motor',
            'ecvt_operation',
            'power_inverter',
            'inverter_coolant',
            'ev_modes',
            'hybrid_park_mechanism',
            'multi_info_display',
            'touch_tracer_display',
            'hill_start_assist',
            'remote_ac',
            'solar_ventilation',
            'hybrid_components_notes',
            
            # Overall Assessment
            'overall_condition_rating',
            'overall_notes',
            'recommendations',
            'estimated_repair_cost',
            'is_completed'
        ]
        
        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'inspection_number': forms.TextInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter unique inspection number'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500'
            }),
            'inspection_date': forms.DateTimeInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'mileage_at_inspection': forms.NumberInput(attrs={
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter current mileage',
                'min': '0',
                'step': '1'
            }),
            'is_completed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add common styling to all status choice fields
        status_widget_attrs = {
            'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-primary focus:border-primary'
        }
        
        # Get all status choice fields from the model
        status_fields = []
        for field in self.Meta.fields:
            if field in self.fields and hasattr(self.fields[field], 'choices') and field not in ['vehicle', 'technician', 'overall_condition_rating']:
                status_fields.append(field)
        
        # Apply styling to all status choice fields
        for field_name in status_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update(status_widget_attrs)
        
        # Add styling to notes fields
        notes_widget_attrs = {
            'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-primary focus:border-primary',
            'rows': 4,
            'placeholder': 'Enter detailed observations, findings, and notes...'
        }
        
        notes_fields = [
            'road_test_notes', 'frame_structure_notes', 'under_hood_notes', 
            'functional_walkaround_notes', 'interior_functions_notes', 
            'exterior_appearance_notes', 'optional_systems_notes', 
            'safety_systems_notes', 'hybrid_components_notes',
            'overall_notes', 'recommendations'
        ]
        
        for field_name in notes_fields:
            if field_name in self.fields:
                self.fields[field_name].widget = forms.Textarea(attrs=notes_widget_attrs)
        
        # Special styling for overall condition rating
        if 'overall_condition_rating' in self.fields:
            self.fields['overall_condition_rating'].widget.attrs.update(status_widget_attrs)
        
        # Special styling for estimated repair cost
        if 'estimated_repair_cost' in self.fields:
            self.fields['estimated_repair_cost'].widget.attrs.update({
                'class': 'w-full mt-1 block rounded-md border-gray-300 shadow-sm focus:ring-primary focus:border-primary',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            })
    
    def clean_inspection_number(self):
        """Custom validation for inspection number uniqueness"""
        inspection_number = self.cleaned_data.get('inspection_number')
        
        # Check for uniqueness (excluding current instance if editing)
        queryset = InitialInspection.objects.filter(inspection_number=inspection_number)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError("An initial inspection with this number already exists.")
        
        return inspection_number
    
    def clean_mileage_at_inspection(self):
        """Custom validation for mileage field"""
        mileage = self.cleaned_data.get('mileage_at_inspection')
        
        if mileage is None or mileage == '':
            raise ValidationError("Vehicle mileage is required.")
        
        try:
            mileage = int(mileage)
        except (ValueError, TypeError):
            raise ValidationError("Please enter a valid mileage number.")
        
        if mileage < 0:
            raise ValidationError("Mileage cannot be negative.")
        
        if mileage > 9999999:  # Reasonable upper limit
            raise ValidationError("Mileage seems unreasonably high. Please check the value.")
        
        return mileage
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if form is marked as completed
        is_completed = cleaned_data.get('is_completed', False)
        
        if is_completed:
            # Validate that critical inspection points are filled for initial inspection
            critical_fields = [
                'cold_engine_operation', 'brake_pedal_specs', 'seat_belt_condition', 
                'transmission_operation', 'steering_feel', 'tire_vibration',
                'frame_unibody_condition'
            ]
            
            missing_fields = []
            for field in critical_fields:
                if not cleaned_data.get(field):
                    missing_fields.append(self.fields[field].label)
            
            if missing_fields:
                raise ValidationError(
                    f"The following critical inspection points must be completed before marking as finished: {', '.join(missing_fields)}"
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set completion timestamp if form is being marked as completed
        if instance.is_completed and not instance.completed_at:
            from django.utils import timezone
            instance.completed_at = timezone.now()
        
        if commit:
            instance.save()
        
        return instance