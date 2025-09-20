from django import forms
from django.core.exceptions import ValidationError
from django.apps import apps
from .models import (
    VehicleAssessment,
    ExteriorBodyDamage,
    WheelsAndTires,
    InteriorDamage,
    MechanicalSystems,
    ElectricalSystems,
    SafetySystems,
    FrameAndStructural,
    FluidSystems,
    DocumentationAndIdentification,
    AssessmentPhoto,
    AssessmentReport
)


class VehicleDetailsForm(forms.ModelForm):
    """Step 1: Vehicle and Assessment Basic Details"""
    
    class Meta:
        model = VehicleAssessment
        fields = [
            'assessment_type', 'vehicle', 'assessor_name', 'assessor_certification'
        ]
        widgets = {
            'assessment_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': True
            }),
            'vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': True
            }),
            'assessor_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter assessor full name',
                'required': True
            }),
            'assessor_certification': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Certification number or credentials'
            })
        }


class IncidentLocationForm(forms.ModelForm):
    """Step 2: Incident Location and Context Details"""
    
    class Meta:
        model = VehicleAssessment
        fields = [
            'incident_location', 'incident_date', 'weather_conditions'
        ]
        widgets = {
            'incident_location': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Street address, city, or general location'
            }),
            'incident_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'weather_conditions': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Clear, Rainy, Foggy, Snow'
            })
        }


class ExteriorDamageAssessmentForm(forms.ModelForm):
    """Step 3a: Exterior Body Damage Assessment"""
    
    class Meta:
        model = ExteriorBodyDamage
        fields = [
            # Front End
            'front_bumper', 'front_bumper_notes',
            'hood', 'hood_notes',
            'front_grille', 'front_grille_notes',
            'headlight_housings', 'headlight_housings_notes',
            'headlight_lenses', 'headlight_lenses_notes',
            'front_fenders', 'front_fenders_notes',
            
            # Side Panels
            'driver_side_door', 'driver_side_door_notes',
            'passenger_side_door', 'passenger_side_door_notes',
            'rear_doors', 'rear_doors_notes',
            'side_mirrors', 'side_mirrors_notes',
            'side_windows', 'side_windows_notes',
            
            # Rear End
            'rear_bumper', 'rear_bumper_notes',
            'trunk_hatch', 'trunk_hatch_notes',
            'rear_quarter_panels', 'rear_quarter_panels_notes',
            'taillight_housings', 'taillight_housings_notes',
            'rear_window', 'rear_window_notes',
            
            # Roof and Pillars
            'roof_panel', 'roof_panel_notes',
            'a_pillars', 'a_pillars_notes',
            'b_pillars', 'b_pillars_notes',
            'sunroof_moonroof', 'sunroof_moonroof_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind CSS classes to all fields
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
                    'rows': 2,
                    'placeholder': 'Additional notes or details...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })


class WheelsAndTiresAssessmentForm(forms.ModelForm):
    """Step 3b: Wheels and Tires Assessment"""
    
    class Meta:
        model = WheelsAndTires
        fields = [
            'front_left_tire', 'front_left_tire_notes',
            'front_right_tire', 'front_right_tire_notes',
            'rear_left_tire', 'rear_left_tire_notes',
            'rear_right_tire', 'rear_right_tire_notes',
            'front_left_wheel', 'front_left_wheel_notes',
            'front_right_wheel', 'front_right_wheel_notes',
            'rear_left_wheel', 'rear_left_wheel_notes',
            'rear_right_wheel', 'rear_right_wheel_notes',
            'spare_tire', 'spare_tire_notes',
            'tire_pressure_sensors', 'tire_pressure_sensors_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
                    'rows': 2,
                    'placeholder': 'Condition details...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })


class InteriorDamageAssessmentForm(forms.ModelForm):
    """Step 3c: Interior Damage Assessment"""
    
    class Meta:
        model = InteriorDamage
        fields = [
            'driver_seat', 'driver_seat_notes',
            'passenger_seat', 'passenger_seat_notes',
            'rear_seats', 'rear_seats_notes',
            'seat_belts', 'seat_belts_notes',
            'dashboard', 'dashboard_notes',
            'steering_wheel', 'steering_wheel_notes',
            'instrument_cluster', 'instrument_cluster_notes',
            'center_console', 'center_console_notes',
            'radio_infotainment', 'radio_infotainment_notes',
            'windshield', 'windshield_notes',
            'side_windows_interior', 'side_windows_interior_notes',
            'interior_mirrors', 'interior_mirrors_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
                    'rows': 2,
                    'placeholder': 'Damage details...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })


class MechanicalSystemsAssessmentForm(forms.ModelForm):
    """Step 3d: Mechanical Systems Assessment"""
    
    class Meta:
        model = MechanicalSystems
        fields = [
            'engine_block', 'engine_block_notes',
            'radiator', 'radiator_notes',
            'battery', 'battery_notes',
            'belts_and_hoses', 'belts_and_hoses_notes',
            'shock_absorbers', 'shock_absorbers_notes',
            'struts', 'struts_notes',
            'brake_lines', 'brake_lines_notes',
            'exhaust_manifold', 'exhaust_manifold_notes',
            'catalytic_converter', 'catalytic_converter_notes',
            'muffler', 'muffler_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
                    'rows': 2,
                    'placeholder': 'Condition assessment...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })


class ElectricalSystemsAssessmentForm(forms.ModelForm):
    """Step 3e: Electrical Systems Assessment"""
    
    class Meta:
        model = ElectricalSystems
        fields = [
            'headlight_function', 'headlight_function_notes',
            'taillight_function', 'taillight_function_notes',
            'interior_lighting', 'interior_lighting_notes',
            'warning_lights', 'warning_lights_notes',
            'power_windows', 'power_windows_notes',
            'power_locks', 'power_locks_notes',
            'air_conditioning', 'air_conditioning_notes',
            'heating_system', 'heating_system_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
                    'rows': 2,
                    'placeholder': 'Function test results...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })


class SafetySystemsAssessmentForm(forms.ModelForm):
    """Step 3f: Safety Systems Assessment"""
    
    class Meta:
        model = SafetySystems
        fields = [
            'airbag_systems', 'airbag_systems_notes',
            'abs_system', 'abs_system_notes',
            'stability_control', 'stability_control_notes',
            'parking_sensors', 'parking_sensors_notes',
            'backup_camera_system', 'backup_camera_system_notes',
            'emergency_brake', 'emergency_brake_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
                    'rows': 2,
                    'placeholder': 'Safety system status...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })


class StructuralAssessmentForm(forms.ModelForm):
    """Step 3g: Frame and Structural Assessment"""
    
    class Meta:
        model = FrameAndStructural
        fields = [
            'frame_rails', 'frame_rails_notes',
            'cross_members', 'cross_members_notes',
            'firewall', 'firewall_notes',
            'floor_pans', 'floor_pans_notes',
            'door_jambs', 'door_jambs_notes',
            'trunk_floor', 'trunk_floor_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
                    'rows': 2,
                    'placeholder': 'Structural integrity notes...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })


class FluidSystemsAssessmentForm(forms.ModelForm):
    """Step 3h: Fluid Systems Assessment"""
    
    class Meta:
        model = FluidSystems
        fields = [
            'engine_oil', 'engine_oil_notes',
            'transmission_fluid', 'transmission_fluid_notes',
            'brake_fluid', 'brake_fluid_notes',
            'coolant', 'coolant_notes',
            'power_steering_fluid', 'power_steering_fluid_notes',
            'windshield_washer_fluid', 'windshield_washer_fluid_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Fluid condition details...'
                })
            else:
                field.widget.attrs.update({'class': 'form-control'})


class DocumentationAssessmentForm(forms.ModelForm):
    """Step 3i: Documentation and Identification Assessment"""
    
    class Meta:
        model = DocumentationAndIdentification
        fields = [
            'vin_plate', 'vin_plate_notes',
            'door_jamb_stickers', 'door_jamb_stickers_notes',
            'emissions_stickers', 'emissions_stickers_notes',
            'maintenance_records', 'maintenance_records_notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'notes' in field_name:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Documentation status...'
                })
            else:
                field.widget.attrs.update({'class': 'form-control'})


class AssessmentCategorizationForm(forms.ModelForm):
    """Step 4: Assessment Categorization and Overall Evaluation"""
    
    class Meta:
        model = VehicleAssessment
        fields = [
            'overall_severity',
            'uk_write_off_category',
            'south_africa_70_percent_rule',
            'status'
        ]
        widgets = {
            'overall_severity': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'uk_write_off_category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'south_africa_70_percent_rule': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }


class FinancialInformationForm(forms.ModelForm):
    """Step 5: Financial Information and Valuation"""
    
    class Meta:
        model = VehicleAssessment
        fields = [
            'estimated_repair_cost',
            'vehicle_market_value',
            'salvage_value'
        ]
        widgets = {
            'estimated_repair_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'vehicle_market_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'salvage_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        repair_cost = cleaned_data.get('estimated_repair_cost')
        market_value = cleaned_data.get('vehicle_market_value')
        
        if repair_cost and market_value:
            if repair_cost > market_value:
                # Auto-suggest total loss if repair cost exceeds market value
                self.add_error('estimated_repair_cost', 
                    'Repair cost exceeds market value. Consider total loss assessment.')
        
        return cleaned_data


class AssessmentNotesForm(forms.ModelForm):
    """Step 6: Assessment Notes and Recommendations"""
    
    class Meta:
        model = VehicleAssessment
        fields = [
            'overall_notes',
            'recommendations'
        ]
        widgets = {
            'overall_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Comprehensive assessment summary, key findings, and observations...'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Recommended actions, repair priorities, safety concerns...'
            })
        }


class AssessmentPhotoUploadForm(forms.ModelForm):
    """Photo Upload Form for Assessment Documentation"""
    
    class Meta:
        model = AssessmentPhoto
        fields = ['category', 'image', 'description']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the photo...'
            })
        }


class AssessmentReportForm(forms.ModelForm):
    """Assessment Report Generation Form"""
    
    class Meta:
        model = AssessmentReport
        fields = [
            'report_type',
            'title',
            'executive_summary',
            'detailed_findings',
            'recommendations'
        ]
        widgets = {
            'report_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Report title...'
            }),
            'executive_summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Executive summary of assessment findings...'
            }),
            'detailed_findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Detailed technical findings and analysis...'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Professional recommendations and next steps...'
            })
        }


# Multi-step form helper
class AssessmentWizardFormSet:
    """Helper class to manage the multi-step assessment process"""
    
    FORM_STEPS = [
        ('vehicle_details', VehicleDetailsForm),
        ('location', IncidentLocationForm),
        ('exterior_damage', ExteriorDamageAssessmentForm),
        ('wheels_tires', WheelsAndTiresAssessmentForm),
        ('interior_damage', InteriorDamageAssessmentForm),
        ('mechanical', MechanicalSystemsAssessmentForm),
        ('electrical', ElectricalSystemsAssessmentForm),
        ('safety', SafetySystemsAssessmentForm),
        ('structural', StructuralAssessmentForm),
        ('fluids', FluidSystemsAssessmentForm),
        ('documentation', DocumentationAssessmentForm),
        ('categorization', AssessmentCategorizationForm),
        ('financial', FinancialInformationForm),
        ('notes', AssessmentNotesForm)
    ]
    
    @classmethod
    def get_form_for_step(cls, step_name):
        """Get the form class for a specific step"""
        for step, form_class in cls.FORM_STEPS:
            if step == step_name:
                return form_class
        return None
    
    @classmethod
    def get_step_names(cls):
        """Get list of all step names"""
        return [step for step, _ in cls.FORM_STEPS]