# parts_identification.py
"""
Parts Identification Engine for extracting damaged parts from vehicle assessments.

This module provides the PartsIdentificationEngine class that scans completed
vehicle assessments to identify damaged parts requiring quotes.
"""

import re
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from django.db import transaction
from django.utils import timezone

from .models import DamagedPart
from assessments.models import VehicleAssessment, AssessmentPhoto


class PartsIdentificationEngine:
    """
    Engine for identifying damaged parts from completed vehicle assessments.
    
    Scans all assessment sections to extract damaged components, consolidates
    duplicates, estimates labor hours, and creates DamagedPart records.
    """
    
    # Mapping of assessment fields to part information
    PART_MAPPINGS = {
        # Exterior damage mappings
        'exterior': {
            'front_bumper': {'category': 'body', 'name': 'Front Bumper'},
            'hood': {'category': 'body', 'name': 'Hood'},
            'front_grille': {'category': 'trim', 'name': 'Front Grille'},
            'headlight_housings': {'category': 'electrical', 'name': 'Headlight Housing'},
            'headlight_lenses': {'category': 'glass', 'name': 'Headlight Lens'},
            'front_fenders': {'category': 'body', 'name': 'Front Fender'},
            'front_quarter_panels': {'category': 'body', 'name': 'Front Quarter Panel'},
            'fog_light_housings': {'category': 'electrical', 'name': 'Fog Light Housing'},
            'license_plate_bracket': {'category': 'trim', 'name': 'License Plate Bracket'},
            'front_spoiler_air_dam': {'category': 'trim', 'name': 'Front Spoiler/Air Dam'},
            'driver_side_door': {'category': 'body', 'name': 'Driver Side Door'},
            'passenger_side_door': {'category': 'body', 'name': 'Passenger Side Door'},
            'rear_doors': {'category': 'body', 'name': 'Rear Door'},
            'door_frames': {'category': 'structural', 'name': 'Door Frame'},
            'side_mirrors': {'category': 'electrical', 'name': 'Side Mirror'},
            'side_moldings_trim': {'category': 'trim', 'name': 'Side Molding/Trim'},
            'rocker_panels': {'category': 'body', 'name': 'Rocker Panel'},
            'wheel_well_liners': {'category': 'trim', 'name': 'Wheel Well Liner'},
            'side_windows': {'category': 'glass', 'name': 'Side Window'},
            'door_handles': {'category': 'trim', 'name': 'Door Handle'},
            'rear_bumper': {'category': 'body', 'name': 'Rear Bumper'},
            'trunk_hatch': {'category': 'body', 'name': 'Trunk/Hatch'},
            'rear_quarter_panels': {'category': 'body', 'name': 'Rear Quarter Panel'},
            'taillight_housings': {'category': 'electrical', 'name': 'Taillight Housing'},
            'taillight_lenses': {'category': 'glass', 'name': 'Taillight Lens'},
            'rear_window': {'category': 'glass', 'name': 'Rear Window'},
            'rear_spoiler': {'category': 'trim', 'name': 'Rear Spoiler'},
            'exhaust_tips': {'category': 'trim', 'name': 'Exhaust Tips'},
            'rear_license_plate_area': {'category': 'trim', 'name': 'Rear License Plate Area'},
            'backup_camera': {'category': 'electrical', 'name': 'Backup Camera'},
            'roof_panel': {'category': 'body', 'name': 'Roof Panel'},
            'a_pillars': {'category': 'structural', 'name': 'A-Pillar'},
            'b_pillars': {'category': 'structural', 'name': 'B-Pillar'},
            'c_pillars': {'category': 'structural', 'name': 'C-Pillar'},
            'd_pillars': {'category': 'structural', 'name': 'D-Pillar'},
            'roof_rails': {'category': 'trim', 'name': 'Roof Rail'},
            'sunroof_moonroof': {'category': 'glass', 'name': 'Sunroof/Moonroof'},
            'antenna': {'category': 'electrical', 'name': 'Antenna'},
        },
        
        # Wheels and tires mappings
        'wheels': {
            'front_left_tire': {'category': 'wheels', 'name': 'Front Left Tire'},
            'front_right_tire': {'category': 'wheels', 'name': 'Front Right Tire'},
            'rear_left_tire': {'category': 'wheels', 'name': 'Rear Left Tire'},
            'rear_right_tire': {'category': 'wheels', 'name': 'Rear Right Tire'},
            'front_left_wheel': {'category': 'wheels', 'name': 'Front Left Wheel'},
            'front_right_wheel': {'category': 'wheels', 'name': 'Front Right Wheel'},
            'rear_left_wheel': {'category': 'wheels', 'name': 'Rear Left Wheel'},
            'rear_right_wheel': {'category': 'wheels', 'name': 'Rear Right Wheel'},
            'spare_tire': {'category': 'wheels', 'name': 'Spare Tire'},
            'wheel_lug_nuts': {'category': 'wheels', 'name': 'Wheel Lug Nuts'},
            'tire_pressure_sensors': {'category': 'electrical', 'name': 'Tire Pressure Sensor'},
            'center_caps': {'category': 'trim', 'name': 'Center Caps'},
        },
        
        # Interior damage mappings
        'interior': {
            'driver_seat': {'category': 'interior', 'name': 'Driver Seat'},
            'passenger_seat': {'category': 'interior', 'name': 'Passenger Seat'},
            'rear_seats': {'category': 'interior', 'name': 'Rear Seats'},
            'seat_belts': {'category': 'safety', 'name': 'Seat Belt'},
            'headrests': {'category': 'interior', 'name': 'Headrest'},
            'armrests': {'category': 'interior', 'name': 'Armrest'},
            'floor_mats': {'category': 'interior', 'name': 'Floor Mat'},
            'dashboard': {'category': 'interior', 'name': 'Dashboard'},
            'steering_wheel': {'category': 'interior', 'name': 'Steering Wheel'},
            'instrument_cluster': {'category': 'electrical', 'name': 'Instrument Cluster'},
            'center_console': {'category': 'interior', 'name': 'Center Console'},
            'climate_controls': {'category': 'electrical', 'name': 'Climate Controls'},
            'radio_infotainment': {'category': 'electrical', 'name': 'Radio/Infotainment'},
            'glove_compartment': {'category': 'interior', 'name': 'Glove Compartment'},
            'door_panels': {'category': 'interior', 'name': 'Door Panel'},
            'windshield': {'category': 'glass', 'name': 'Windshield'},
            'side_windows_interior': {'category': 'glass', 'name': 'Side Window'},
            'interior_mirrors': {'category': 'glass', 'name': 'Interior Mirror'},
            'visors': {'category': 'interior', 'name': 'Sun Visor'},
        },
        
        # Mechanical systems mappings
        'mechanical': {
            'engine_block': {'category': 'mechanical', 'name': 'Engine Block'},
            'radiator': {'category': 'mechanical', 'name': 'Radiator'},
            'battery': {'category': 'electrical', 'name': 'Battery'},
            'air_filter_housing': {'category': 'mechanical', 'name': 'Air Filter Housing'},
            'belts_and_hoses': {'category': 'mechanical', 'name': 'Belts and Hoses'},
            'fluid_reservoirs': {'category': 'fluid', 'name': 'Fluid Reservoir'},
            'wiring_harnesses': {'category': 'electrical', 'name': 'Wiring Harness'},
            'engine_mounts': {'category': 'mechanical', 'name': 'Engine Mount'},
            'shock_absorbers': {'category': 'mechanical', 'name': 'Shock Absorber'},
            'struts': {'category': 'mechanical', 'name': 'Strut'},
            'springs': {'category': 'mechanical', 'name': 'Spring'},
            'control_arms': {'category': 'mechanical', 'name': 'Control Arm'},
            'tie_rods': {'category': 'mechanical', 'name': 'Tie Rod'},
            'steering_rack': {'category': 'mechanical', 'name': 'Steering Rack'},
            'brake_lines': {'category': 'mechanical', 'name': 'Brake Line'},
            'exhaust_manifold': {'category': 'mechanical', 'name': 'Exhaust Manifold'},
            'catalytic_converter': {'category': 'mechanical', 'name': 'Catalytic Converter'},
            'muffler': {'category': 'mechanical', 'name': 'Muffler'},
            'exhaust_pipes': {'category': 'mechanical', 'name': 'Exhaust Pipe'},
            'heat_shields': {'category': 'mechanical', 'name': 'Heat Shield'},
        },
        
        # Electrical systems mappings
        'electrical': {
            'headlight_function': {'category': 'electrical', 'name': 'Headlight System'},
            'taillight_function': {'category': 'electrical', 'name': 'Taillight System'},
            'interior_lighting': {'category': 'electrical', 'name': 'Interior Lighting'},
            'warning_lights': {'category': 'electrical', 'name': 'Warning Light System'},
            'horn': {'category': 'electrical', 'name': 'Horn'},
            'power_windows': {'category': 'electrical', 'name': 'Power Window System'},
            'power_locks': {'category': 'electrical', 'name': 'Power Lock System'},
            'air_conditioning': {'category': 'electrical', 'name': 'Air Conditioning System'},
            'heating_system': {'category': 'electrical', 'name': 'Heating System'},
        },
        
        # Safety systems mappings
        'safety': {
            'airbag_system': {'category': 'safety', 'name': 'Airbag System'},
            'abs_system': {'category': 'safety', 'name': 'ABS System'},
            'traction_control': {'category': 'safety', 'name': 'Traction Control System'},
            'stability_control': {'category': 'safety', 'name': 'Stability Control System'},
            'parking_sensors': {'category': 'safety', 'name': 'Parking Sensor'},
            'backup_camera_safety': {'category': 'safety', 'name': 'Backup Camera System'},
        },
        
        # Structural mappings
        'structural': {
            'frame_rails': {'category': 'structural', 'name': 'Frame Rail'},
            'cross_members': {'category': 'structural', 'name': 'Cross Member'},
            'unibody_structure': {'category': 'structural', 'name': 'Unibody Structure'},
            'crumple_zones': {'category': 'structural', 'name': 'Crumple Zone'},
            'reinforcement_bars': {'category': 'structural', 'name': 'Reinforcement Bar'},
        },
        
        # Fluid systems mappings
        'fluids': {
            'engine_oil': {'category': 'fluid', 'name': 'Engine Oil System'},
            'coolant_system': {'category': 'fluid', 'name': 'Coolant System'},
            'brake_fluid': {'category': 'fluid', 'name': 'Brake Fluid System'},
            'transmission_fluid': {'category': 'fluid', 'name': 'Transmission Fluid System'},
            'power_steering_fluid': {'category': 'fluid', 'name': 'Power Steering Fluid System'},
            'windshield_washer': {'category': 'fluid', 'name': 'Windshield Washer System'},
        }
    }
    
    # Labor hour estimates by damage severity and part category
    LABOR_ESTIMATES = {
        'body': {
            'minor': 2.0,
            'moderate': 4.0,
            'severe': 8.0,
            'replace': 6.0,
        },
        'mechanical': {
            'minor': 1.5,
            'moderate': 3.0,
            'severe': 6.0,
            'replace': 4.0,
        },
        'electrical': {
            'minor': 1.0,
            'moderate': 2.0,
            'severe': 4.0,
            'replace': 3.0,
        },
        'glass': {
            'minor': 0.5,
            'moderate': 1.0,
            'severe': 2.0,
            'replace': 1.5,
        },
        'interior': {
            'minor': 1.0,
            'moderate': 2.0,
            'severe': 4.0,
            'replace': 3.0,
        },
        'trim': {
            'minor': 0.5,
            'moderate': 1.0,
            'severe': 2.0,
            'replace': 1.0,
        },
        'wheels': {
            'minor': 0.5,
            'moderate': 1.0,
            'severe': 1.5,
            'replace': 1.0,
        },
        'safety': {
            'minor': 2.0,
            'moderate': 4.0,
            'severe': 8.0,
            'replace': 6.0,
        },
        'structural': {
            'minor': 4.0,
            'moderate': 8.0,
            'severe': 16.0,
            'replace': 12.0,
        },
        'fluid': {
            'minor': 1.0,
            'moderate': 2.0,
            'severe': 3.0,
            'replace': 2.0,
        },
    }
    
    def __init__(self):
        """Initialize the parts identification engine."""
        pass
    
    def identify_damaged_parts(self, assessment: VehicleAssessment) -> List[DamagedPart]:
        """
        Scan assessment sections and create DamagedPart records.
        
        Args:
            assessment: VehicleAssessment instance to scan
            
        Returns:
            List of created DamagedPart instances
            
        Raises:
            ValueError: If assessment is not completed or invalid
        """
        if not assessment:
            raise ValueError("Assessment cannot be None")
        
        if assessment.status not in ['completed', 'under_review']:
            raise ValueError(f"Assessment must be completed or under review, got: {assessment.status}")
        
        # Get all assessment sections
        sections = self.get_assessment_sections(assessment)
        
        # Extract parts from each section
        all_parts = []
        for section_name, section_obj in sections.items():
            if section_obj:
                parts = self.extract_parts_from_section(section_obj, section_name)
                all_parts.extend(parts)
        
        # Consolidate duplicate parts
        consolidated_parts = self.consolidate_duplicate_parts(all_parts)
        
        # Create DamagedPart records
        created_parts = []
        with transaction.atomic():
            for part_data in consolidated_parts:
                damaged_part = self.create_damaged_part_record(assessment, part_data)
                if damaged_part:
                    created_parts.append(damaged_part)
            
            # Mark parts identification as complete
            assessment.parts_identification_complete = True
            assessment.save(update_fields=['parts_identification_complete'])
        
        return created_parts
    
    def get_assessment_sections(self, assessment: VehicleAssessment) -> Dict[str, object]:
        """
        Get all assessment section objects.
        
        Args:
            assessment: VehicleAssessment instance
            
        Returns:
            Dictionary mapping section names to section objects
        """
        sections = {}
        
        # Get related section objects
        try:
            sections['exterior'] = getattr(assessment, 'exterior_damage', None)
        except:
            sections['exterior'] = None
            
        try:
            sections['wheels'] = getattr(assessment, 'wheels_tires', None)
        except:
            sections['wheels'] = None
            
        try:
            sections['interior'] = getattr(assessment, 'interior_damage', None)
        except:
            sections['interior'] = None
            
        try:
            sections['mechanical'] = getattr(assessment, 'mechanical_systems', None)
        except:
            sections['mechanical'] = None
            
        try:
            sections['electrical'] = getattr(assessment, 'electrical_systems', None)
        except:
            sections['electrical'] = None
            
        try:
            sections['safety'] = getattr(assessment, 'safety_systems', None)
        except:
            sections['safety'] = None
            
        try:
            sections['structural'] = getattr(assessment, 'frame_structural', None)
        except:
            sections['structural'] = None
            
        try:
            sections['fluids'] = getattr(assessment, 'fluid_systems', None)
        except:
            sections['fluids'] = None
        
        return sections
    
    def extract_parts_from_section(self, section_obj: object, section_name: str) -> List[Dict]:
        """
        Extract damaged parts from a specific assessment section.
        
        Args:
            section_obj: Assessment section object (e.g., ExteriorBodyDamage)
            section_name: Name of the section ('exterior', 'mechanical', etc.)
            
        Returns:
            List of part data dictionaries
        """
        parts = []
        
        if not section_obj or section_name not in self.PART_MAPPINGS:
            return parts
        
        section_mappings = self.PART_MAPPINGS[section_name]
        
        # Iterate through all fields in the section
        for field_name, part_info in section_mappings.items():
            # Get damage severity value
            damage_value = getattr(section_obj, field_name, None)
            
            # Skip if no damage or field doesn't exist
            if not damage_value or damage_value in ['none', 'working', 'excellent', 'good']:
                continue
            
            # Get notes field
            notes_field = f"{field_name}_notes"
            notes = getattr(section_obj, notes_field, '')
            
            # Map damage values to our severity scale
            severity = self.map_damage_severity(damage_value, section_name)
            
            if severity:
                part_data = {
                    'section_type': section_name,
                    'field_name': field_name,
                    'part_name': part_info['name'],
                    'part_category': part_info['category'],
                    'damage_severity': severity,
                    'damage_description': self.generate_damage_description(
                        part_info['name'], severity, damage_value, notes
                    ),
                    'requires_replacement': severity == 'replace' or damage_value in ['destroyed', 'failed'],
                    'estimated_labor_hours': self.estimate_labor_hours(
                        part_info['category'], severity
                    ),
                    'notes': notes,
                    'original_damage_value': damage_value,
                }
                parts.append(part_data)
        
        return parts
    
    def map_damage_severity(self, damage_value: str, section_name: str) -> Optional[str]:
        """
        Map assessment damage values to standardized severity levels.
        
        Args:
            damage_value: Original damage value from assessment
            section_name: Section name for context
            
        Returns:
            Mapped severity level or None if no damage
        """
        # Mapping for exterior/interior damage values
        damage_mappings = {
            'light': 'minor',
            'minor': 'minor',
            'moderate': 'moderate',
            'severe': 'severe',
            'destroyed': 'replace',
            'fair': 'minor',
            'poor': 'moderate',
            'failed': 'replace',
            'intermittent': 'minor',
            'not_working': 'severe',
        }
        
        return damage_mappings.get(damage_value.lower())
    
    def generate_damage_description(self, part_name: str, severity: str, 
                                  original_value: str, notes: str) -> str:
        """
        Generate a descriptive damage description.
        
        Args:
            part_name: Name of the damaged part
            severity: Mapped severity level
            original_value: Original assessment value
            notes: Additional notes from assessment
            
        Returns:
            Generated damage description
        """
        severity_descriptions = {
            'minor': 'shows minor damage',
            'moderate': 'has moderate damage requiring repair',
            'severe': 'has severe damage requiring significant repair',
            'replace': 'requires complete replacement',
        }
        
        base_description = f"{part_name} {severity_descriptions.get(severity, 'is damaged')}"
        
        if original_value and original_value != severity:
            base_description += f" (assessed as {original_value})"
        
        if notes and notes.strip():
            base_description += f". Notes: {notes.strip()}"
        
        return base_description
    
    def consolidate_duplicate_parts(self, parts: List[Dict]) -> List[Dict]:
        """
        Merge identical parts found across different sections.
        
        Args:
            parts: List of part data dictionaries
            
        Returns:
            List of consolidated part data dictionaries
        """
        consolidated = {}
        
        for part in parts:
            # Create a key for grouping similar parts
            key = (
                part['part_name'].lower().strip(),
                part['part_category']
            )
            
            if key in consolidated:
                # Merge with existing part
                existing = consolidated[key]
                
                # Use the more severe damage level
                if self.get_severity_weight(part['damage_severity']) > \
                   self.get_severity_weight(existing['damage_severity']):
                    existing['damage_severity'] = part['damage_severity']
                    existing['requires_replacement'] = part['requires_replacement']
                
                # Combine descriptions and notes
                if part['damage_description'] not in existing['damage_description']:
                    existing['damage_description'] += f" Also: {part['damage_description']}"
                
                if part['notes'] and part['notes'] not in existing['notes']:
                    existing['notes'] += f" {part['notes']}"
                
                # Use higher labor estimate
                existing['estimated_labor_hours'] = max(
                    existing['estimated_labor_hours'],
                    part['estimated_labor_hours']
                )
                
                # Track multiple sections
                if 'sections' not in existing:
                    existing['sections'] = [existing['section_type']]
                if part['section_type'] not in existing['sections']:
                    existing['sections'].append(part['section_type'])
                
            else:
                # Add new part
                consolidated[key] = part.copy()
        
        return list(consolidated.values())
    
    def get_severity_weight(self, severity: str) -> int:
        """Get numeric weight for severity comparison."""
        weights = {
            'minor': 1,
            'moderate': 2,
            'severe': 3,
            'replace': 4,
        }
        return weights.get(severity, 0)
    
    def estimate_labor_hours(self, part_category: str, damage_severity: str) -> Decimal:
        """
        Estimate labor hours based on damage type and severity.
        
        Args:
            part_category: Category of the part
            damage_severity: Severity of the damage
            
        Returns:
            Estimated labor hours as Decimal
        """
        if part_category not in self.LABOR_ESTIMATES:
            # Default estimates for unknown categories
            default_estimates = {
                'minor': 1.0,
                'moderate': 2.0,
                'severe': 4.0,
                'replace': 3.0,
            }
            return Decimal(str(default_estimates.get(damage_severity, 2.0)))
        
        category_estimates = self.LABOR_ESTIMATES[part_category]
        hours = category_estimates.get(damage_severity, 2.0)
        
        return Decimal(str(hours))
    
    def create_damaged_part_record(self, assessment: VehicleAssessment, 
                                 part_data: Dict) -> Optional[DamagedPart]:
        """
        Create a DamagedPart record from part data.
        
        Args:
            assessment: VehicleAssessment instance
            part_data: Dictionary containing part information
            
        Returns:
            Created DamagedPart instance or None if creation failed
        """
        try:
            damaged_part = DamagedPart.objects.create(
                assessment=assessment,
                section_type=part_data['section_type'],
                part_name=part_data['part_name'],
                part_category=part_data['part_category'],
                damage_severity=part_data['damage_severity'],
                damage_description=part_data['damage_description'],
                requires_replacement=part_data['requires_replacement'],
                estimated_labor_hours=part_data['estimated_labor_hours'],
                notes=part_data['notes'],
            )
            
            # Link damage images if available
            self.link_damage_images(damaged_part, part_data)
            
            return damaged_part
            
        except Exception as e:
            # Log error but don't fail the entire process
            print(f"Error creating DamagedPart record: {e}")
            return None
    
    def link_damage_images(self, damaged_part: DamagedPart, part_data: Dict) -> None:
        """
        Associate photos with specific parts based on section and keywords.
        
        Args:
            damaged_part: DamagedPart instance
            part_data: Dictionary containing part information
        """
        try:
            # Get all photos for the assessment
            assessment_photos = AssessmentPhoto.objects.filter(
                assessment=damaged_part.assessment
            )
            
            # Find photos that might be related to this part
            related_photos = []
            
            part_keywords = self.get_part_keywords(damaged_part.part_name)
            section_keywords = [damaged_part.section_type]
            
            for photo in assessment_photos:
                # Check photo description/filename for keywords
                photo_text = ''
                if hasattr(photo, 'description') and photo.description:
                    photo_text += photo.description.lower()
                if hasattr(photo, 'image') and photo.image:
                    photo_text += str(photo.image).lower()
                
                # Check if any keywords match
                for keyword in part_keywords + section_keywords:
                    if keyword.lower() in photo_text:
                        related_photos.append(photo)
                        break
            
            # Link the photos
            if related_photos:
                damaged_part.damage_images.set(related_photos)
                
        except Exception as e:
            # Log error but don't fail
            print(f"Error linking damage images: {e}")
    
    def get_part_keywords(self, part_name: str) -> List[str]:
        """
        Generate keywords for photo matching based on part name.
        
        Args:
            part_name: Name of the part
            
        Returns:
            List of keywords for matching
        """
        keywords = []
        
        # Split part name into words
        words = re.split(r'[/\-\s]+', part_name.lower())
        keywords.extend(words)
        
        # Add common variations
        keyword_variations = {
            'bumper': ['bumper', 'front', 'rear'],
            'door': ['door', 'side'],
            'fender': ['fender', 'quarter'],
            'light': ['light', 'lamp', 'headlight', 'taillight'],
            'mirror': ['mirror', 'side'],
            'window': ['window', 'glass'],
            'wheel': ['wheel', 'rim', 'tire'],
            'hood': ['hood', 'bonnet'],
            'trunk': ['trunk', 'boot', 'hatch'],
        }
        
        for word in words:
            if word in keyword_variations:
                keywords.extend(keyword_variations[word])
        
        return list(set(keywords))  # Remove duplicates