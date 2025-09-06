"""
Utility functions for maintenance history operations
"""
from typing import Dict, List, Tuple
from .models import Inspections


def calculate_vehicle_health_index(inspection_form: Inspections) -> Tuple[str, str]:
    """
    Calculate vehicle health index based on inspection form results.
    
    Args:
        inspection_form: Inspections model instance with completed form data
        
    Returns:
        Tuple of (health_index, inspection_result)
        - health_index: String representation of the calculated health score
        - inspection_result: One of the RESULT_CHOICES from Inspection model
    """
    
    # Define critical safety systems with higher weights
    critical_systems = {
        'brake_pads': 10,
        'brake_discs': 10,
        'brake_fluid': 8,
        'tire_tread_depth': 9,
        'tire_pressure': 7,
        'headlights': 6,
        'brake_lights': 6,
        'seat_belts': 8,
        'steering_response': 9,
        'suspension_bushings': 7,
    }
    
    # Define important systems with medium weights
    important_systems = {
        'engine_oil_level': 6,
        'coolant_level': 5,
        'battery_voltage': 5,
        'alternator_output': 4,
        'transmission_fluid': 5,
        'exhaust_system': 4,
        'air_filter': 3,
        'wiper_blades': 4,
        'mirrors': 3,
    }
    
    # Define minor systems with lower weights
    minor_systems = {
        'cabin_air_filter': 2,
        'interior_lights': 2,
        'infotainment_system': 1,
        'rear_view_camera': 2,
        'air_conditioning': 2,
        'power_windows': 1,
        'first_aid_kit': 1,
        'warning_triangle': 1,
    }
    
    # Combine all systems
    all_systems = {**critical_systems, **important_systems, **minor_systems}
    
    # Calculate scores
    total_possible_score = 0
    actual_score = 0
    major_failures = 0
    minor_failures = 0
    
    for field_name, weight in all_systems.items():
        field_value = getattr(inspection_form, field_name, None)
        
        if field_value:  # Only count if field was actually inspected
            total_possible_score += weight
            
            if field_value == 'pass':
                actual_score += weight
            elif field_value == 'minor':
                actual_score += weight * 0.7  # 70% score for minor issues
                minor_failures += 1
            elif field_value == 'major':
                actual_score += weight * 0.3  # 30% score for major issues
                major_failures += 1
            elif field_value == 'fail':
                # 0% score for complete failures
                if field_name in critical_systems:
                    major_failures += 1
                else:
                    minor_failures += 1
            # 'na' (Not Applicable) doesn't affect the score
    
    # Calculate health index percentage
    if total_possible_score > 0:
        health_percentage = (actual_score / total_possible_score) * 100
    else:
        health_percentage = 0
    
    # Determine health index category
    if health_percentage >= 90:
        health_index = "Excellent (90-100%)"
    elif health_percentage >= 80:
        health_index = "Good (80-89%)"
    elif health_percentage >= 70:
        health_index = "Fair (70-79%)"
    elif health_percentage >= 60:
        health_index = "Poor (60-69%)"
    else:
        health_index = "Critical (<60%)"
    
    # Determine inspection result based on failures and health score
    inspection_result = _determine_inspection_result(
        health_percentage, major_failures, minor_failures, critical_systems, inspection_form
    )
    
    return health_index, inspection_result


def _determine_inspection_result(
    health_percentage: float, 
    major_failures: int, 
    minor_failures: int,
    critical_systems: Dict[str, int],
    inspection_form: Inspections
) -> str:
    """
    Determine the inspection result based on health percentage and failure counts.
    
    Returns one of: "PAS", "PMD", "PJD", "FMD", "FJD", "FAI"
    """
    
    # Check for critical system failures
    critical_failures = []
    for field_name in critical_systems.keys():
        field_value = getattr(inspection_form, field_name, None)
        if field_value in ['fail', 'major']:
            critical_failures.append(field_name)
    
    # Determine result based on failures and health score
    if len(critical_failures) > 0:
        if len(critical_failures) >= 3 or health_percentage < 50:
            return "FAI"  # Failed
        elif any(getattr(inspection_form, field, None) == 'fail' for field in critical_failures):
            return "FJD"  # Failed due to major Defects
        else:
            return "FMD"  # Failed due to minor Defects
    
    # No critical failures - determine pass level
    if major_failures == 0 and minor_failures <= 2:
        return "PAS"  # Passed
    elif major_failures == 0 and minor_failures <= 5:
        return "PMD"  # Passed with minor Defects
    elif major_failures <= 2:
        return "PJD"  # Passed with major Defects
    else:
        return "FMD"  # Failed due to minor Defects


def get_inspection_recommendations(inspection_form: Inspections) -> List[str]:
    """
    Generate maintenance recommendations based on inspection results.
    
    Args:
        inspection_form: Inspections model instance with completed form data
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Define recommendation mappings
    recommendation_map = {
        'brake_pads': "Replace brake pads immediately - critical safety issue",
        'brake_discs': "Inspect and potentially replace brake discs",
        'brake_fluid': "Replace brake fluid and check for leaks",
        'tire_tread_depth': "Replace tires - insufficient tread depth",
        'tire_pressure': "Adjust tire pressure to manufacturer specifications",
        'engine_oil_level': "Change engine oil and filter",
        'coolant_level': "Top up coolant and check for leaks",
        'battery_voltage': "Test and potentially replace battery",
        'air_filter': "Replace air filter",
        'cabin_air_filter': "Replace cabin air filter",
        'headlights': "Replace headlight bulbs or repair wiring",
        'brake_lights': "Replace brake light bulbs or repair wiring",
        'wiper_blades': "Replace windshield wiper blades",
        'transmission_fluid': "Service transmission fluid",
        'steering_response': "Inspect steering system - potential safety issue",
        'suspension_bushings': "Replace worn suspension components",
    }
    
    # Check each field for issues
    for field_name, recommendation in recommendation_map.items():
        field_value = getattr(inspection_form, field_name, None)
        if field_value in ['fail', 'major', 'minor']:
            urgency = "URGENT: " if field_value in ['fail', 'major'] else ""
            recommendations.append(f"{urgency}{recommendation}")
    
    # Add general recommendations based on overall condition
    failed_points = inspection_form.failed_points
    if len(failed_points) > 5:
        recommendations.append("Schedule comprehensive vehicle service due to multiple issues")
    
    if not recommendations:
        recommendations.append("Vehicle is in good condition - continue regular maintenance schedule")
    
    return recommendations


def generate_inspection_number() -> str:
    """
    Generate a unique inspection number in format: INS-YYYY-NNNN
    """
    from datetime import datetime
    from .models import Inspection
    
    current_year = datetime.now().year
    prefix = f"INS-{current_year}-"
    
    # Find the highest number for this year
    existing_inspections = Inspection.objects.filter(
        inspection_number__startswith=prefix
    ).order_by('-inspection_number')
    
    if existing_inspections.exists():
        last_number = existing_inspections.first().inspection_number
        try:
            # Extract the number part and increment
            number_part = int(last_number.split('-')[-1])
            next_number = number_part + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    return f"{prefix}{next_number:04d}"


def generate_inspection_summary(inspection_form: Inspections) -> Dict[str, any]:
    """
    Generate a comprehensive summary of the inspection results.
    
    Args:
        inspection_form: Inspections model instance with completed form data
        
    Returns:
        Dictionary containing inspection summary data
    """
    health_index, inspection_result = calculate_vehicle_health_index(inspection_form)
    recommendations = get_inspection_recommendations(inspection_form)
    failed_points = inspection_form.failed_points
    
    return {
        'health_index': health_index,
        'inspection_result': inspection_result,
        'completion_percentage': inspection_form.completion_percentage,
        'total_points_checked': inspection_form.total_points_checked,
        'failed_points_count': len(failed_points),
        'failed_points': failed_points,
        'has_major_issues': inspection_form.has_major_issues,
        'recommendations': recommendations,
        'inspection_date': inspection_form.inspection_date,
        'technician': inspection_form.technician.get_full_name() if inspection_form.technician else None,
        'vehicle_vin': inspection_form.inspection.vehicle.vin,
        'mileage': inspection_form.mileage_at_inspection,
    }


def get_initial_inspection_field_weights():
    """
    Return categorized field weights for 160-point initial inspection.
    Enhanced weighting system with improved categorization and scoring.
    
    Returns:
        Dict containing field weights organized by criticality level
    """
    
    # Critical Safety Systems (Weight: 15-20 points each) - Highest priority
    critical_systems = {
        'brake_vibrations': 20,
        'brake_pedal_specs': 18,
        'abs_operation': 17,
        'parking_brake_operation': 16,
        'seat_belt_condition': 18,
        'seat_belt_operation': 18,
        'steering_feel': 20,
        'steering_centered': 17,
        'vehicle_tracking': 19,
        'tire_condition': 18,
        'tread_depth': 20,
        'tire_specifications': 15,
        'brake_calipers_lines': 19,
        'brake_pad_life': 20,
        'brake_rotors_drums': 18,
        'headlight_alignment': 16,
        'brake_lights': 17,
        'turn_signals': 17,
        'airbags_present': 19,
        'frame_unibody_condition': 18,  # Added - structural integrity is critical
        'engine_fluid_leaks': 15,  # Moved from important - safety concern
        'transmission_leaks': 14,  # Moved from important - can cause failures
    }
    
    # Important Mechanical Systems (Weight: 10-14 points each) - High priority
    important_systems = {
        'cold_engine_operation': 12,
        'throttle_operation': 11,
        'operating_temp_performance': 13,
        'normal_operating_temp': 12,
        'engine_fan_operation': 10,
        'transmission_operation': 14,
        'auto_trans_cold': 12,
        'auto_trans_operating': 13,
        'panel_alignment': 8,  # Reduced - more cosmetic
        'underbody_condition': 12,
        'suspension_leaks_wear': 13,
        'struts_shocks_condition': 12,
        'power_steering_leaks': 11,
        'exhaust_system': 10,
        'engine_trans_mounts': 11,
        'drive_axle_shafts': 12,
        'cv_joints_boots': 10,
        'differential_fluid': 9,
        'battery_test': 12,
        'charging_system': 13,
        'coolant_level': 11,
        'coolant_protection': 10,
        'oil_filter_change': 11,
        'fluid_levels': 10,
        'fluid_contamination': 12,  # Increased - indicates serious issues
        'oil_sludge_check': 11,  # Moved from standard - engine health critical
        'battery_damage': 10,  # Moved from standard - safety concern
        'battery_posts_cables': 9,  # Moved from standard
        'charging_system': 13,  # Duplicate removed, kept higher weight
    }
    
    # Standard Systems (Weight: 6-9 points each) - Medium priority
    standard_systems = {
        'warmup_operation': 7,
        'speedometer_function': 8,  # Increased - legal requirement
        'odometer_function': 7,
        'cruise_control': 6,
        'heater_operation': 8,  # Increased - safety in cold weather
        'ac_operation': 7,
        'engine_noise': 8,  # Increased - indicates mechanical issues
        'interior_noise': 6,
        'wind_road_noise': 6,
        'tire_vibration': 9,  # Increased - safety concern
        'wheel_covers': 6,
        'brake_system_equipment': 9,  # Increased - brake safety
        'drive_belts_hoses': 8,  # Increased - can cause breakdowns
        'air_filter_condition': 7,
        'battery_secured': 7,  # Increased - safety concern
        'owners_manual': 6,
        'fuel_gauge': 8,  # Increased - prevents running out of fuel
        'battery_voltage_gauge': 6,
        'temp_gauge': 8,  # Increased - prevents overheating
        'horn_function': 7,  # Increased - safety device
        'emissions_test': 8,  # Increased - legal requirement
        'tail_lights': 8,  # Increased - safety critical
        'side_marker_lights': 6,
        'backup_lights': 7,
        'license_plate_lights': 6,
        'exterior_lights_condition': 7,
        'tire_pressure': 9,  # Added - critical for safety and efficiency
        'tire_wear_patterns': 8,  # Added - indicates alignment/suspension issues
        'wheels_rims': 7,  # Added - structural integrity
    }
    
    # Interior and Convenience Systems (Weight: 4-7 points each) - Medium-low priority
    interior_systems = {
        'instrument_panel': 7,  # Increased - safety information display
        'hvac_panel': 5,
        'instrument_dimmer': 4,
        'hazard_flashers': 6,  # Increased - emergency safety device
        'rearview_mirror': 6,  # Increased - visibility safety
        'exterior_mirrors': 6,  # Increased - visibility safety
        'remote_mirror_control': 4,
        'glass_condition': 7,  # Increased - visibility safety
        'window_tint': 5,  # Increased - legal compliance
        'dome_courtesy_lights': 4,
        'power_windows': 5,
        'window_locks': 4,
        'audio_system': 4,
        'audio_speakers': 4,
        'antenna': 4,
        'clock_operation': 4,
        'power_outlet': 4,
        'doors_operation': 6,  # Increased - safety and security
        'door_locks': 6,  # Increased - security
        'keyless_entry': 4,
        'master_keys': 6,  # Increased - security and convenience
        'theft_deterrent': 5,  # Increased - security
        'seat_adjustments': 5,  # Increased - driver safety positioning
        'seat_heaters': 4,
        'memory_seat': 4,
        'headrests': 6,  # Increased - safety in accidents
        'rear_defogger': 6,  # Increased - visibility safety
        'defogger_indicator': 4,
        'luggage_light': 4,
        'hood_trunk_latches': 5,
        'emergency_trunk_release': 6,  # Increased - safety feature
        'fuel_door_release': 4,
        'front_wipers': 7,  # Added - critical for visibility
        'rear_wipers': 5,  # Added - visibility
        'wiper_rest_position': 5,  # Added
        'washer_fluid_spray': 6,  # Added - visibility safety
    }
    
    # Appearance and Minor Systems (Weight: 2-5 points each) - Lower priority
    minor_systems = {
        'tilt_telescopic_steering': 4,  # Increased - driver comfort and safety
        'wiper_blade_replacement': 5,  # Increased - visibility safety
        'underhood_labels': 2,
        'ashtrays': 2,
        'headliner_trim': 3,
        'floor_mats': 3,
        'luggage_cleanliness': 3,
        'spare_tire_cover': 3,
        'spare_tire_present': 5,  # Increased - emergency preparedness
        'spare_tire_tread': 5,  # Increased - emergency safety
        'spare_tire_pressure': 5,  # Increased - emergency readiness
        'spare_tire_damage': 4,  # Increased
        'spare_tire_secured': 4,  # Increased - safety during transport
        'jack_tools': 4,  # Increased - emergency preparedness
        'acceptable_aftermarket': 3,
        'unacceptable_removal': 2,
        'body_surface': 4,
        'exterior_cleanliness': 3,
        'paint_finish': 3,
        'paint_scratches': 3,
        'wheels_cleanliness': 3,
        'wheel_wells': 2,
        'tires_dressed': 2,
        'engine_compartment_clean': 3,
        'insulation_pad': 2,
        'engine_dressed': 2,
        'door_jambs': 2,
        'glove_console': 2,
        'cabin_air_filter': 4,  # Increased - air quality and HVAC efficiency
        'seats_carpets': 3,
        'vehicle_odors': 4,  # Increased - indicates potential issues
        'glass_cleanliness': 3,  # Increased - visibility
        'interior_debris': 2,
        'dash_vents': 2,
        'crevices_clean': 2,
        'upholstery_panels': 3,
        'paint_repairs': 4,  # Increased - indicates accident history
        'glass_repairs': 4,  # Increased - safety and indicates damage
        'bumpers_condition': 4,  # Increased - safety equipment
        'interior_surfaces': 3,
        'sunroof_convertible': 3,
        'seat_heaters_optional': 3,
        'navigation_system': 3,
        'head_unit_software': 2,
        'transfer_case': 5,  # Increased - important for 4WD vehicles
        'truck_bed_condition': 4,  # Increased - structural integrity
        'truck_bed_liner': 3,
        'backup_camera': 4,  # Increased - safety feature
    }
    
    # Advanced and Hybrid Systems (Weight: 4-8 points each) - Variable priority
    advanced_systems = {
        'sos_indicator': 5,  # Increased - emergency safety system
        'lane_keep_assist': 6,  # Increased - active safety system
        'adaptive_cruise': 6,  # Increased - safety and convenience
        'parking_assist': 5,  # Increased - accident prevention
        'hybrid_battery': 8,  # Increased - critical for hybrid operation
        'battery_control_module': 7,  # Increased - critical system
        'hybrid_power_mgmt': 7,  # Increased - critical system
        'electric_motor': 7,  # Increased - critical for hybrid/EV
        'ecvt_operation': 6,  # Increased - transmission critical
        'power_inverter': 6,  # Increased - critical component
        'inverter_coolant': 5,  # Increased - prevents overheating
        'ev_modes': 4,
        'hybrid_park_mechanism': 6,  # Increased - safety system
        'multi_info_display': 4,
        'touch_tracer_display': 4,
        'hill_start_assist': 6,  # Increased - safety feature
        'remote_ac': 4,
        'solar_ventilation': 4,
    }
    
    return {
        'critical': critical_systems,
        'important': important_systems,
        'standard': standard_systems,
        'interior': interior_systems,
        'minor': minor_systems,
        'advanced': advanced_systems,
    }


def calculate_initial_inspection_health_index(inspection) -> Tuple[str, str]:
    """
    Enhanced vehicle health index calculation for 160-point initial inspection.
    
    This redesigned algorithm provides:
    - Dynamic weighting based on vehicle age and mileage
    - Improved severity scoring with more granular penalties
    - System-specific multipliers for critical safety components
    - Comprehensive failure analysis with contextual adjustments
    
    Args:
        inspection: InitialInspection model instance with completed form data
        
    Returns:
        Tuple of (health_index, inspection_result)
        - health_index: String representation of the calculated health score
        - inspection_result: One of the RESULT_CHOICES from Inspection model
    """
    
    # Get enhanced field weights
    field_weights = get_initial_inspection_field_weights()
    
    # Get vehicle context for dynamic adjustments
    vehicle = inspection.vehicle
    vehicle_age = _calculate_vehicle_age(vehicle)
    mileage = inspection.mileage_at_inspection or 0
    
    # Calculate age and mileage factors
    age_factor = _calculate_age_factor(vehicle_age)
    mileage_factor = _calculate_mileage_factor(mileage)
    
    # Initialize scoring variables
    total_possible_score = 0
    actual_score = 0
    weighted_failures = 0
    critical_failures = 0
    major_failures = 0
    minor_failures = 0
    safety_critical_count = 0
    
    # System-specific failure tracking
    system_failures = {
        'critical': [],
        'important': [],
        'standard': [],
        'interior': [],
        'minor': [],
        'advanced': []
    }
    
    # Process each system category
    for category_name, category_fields in field_weights.items():
        category_multiplier = _get_category_multiplier(category_name)
        
        for field_name, base_weight in category_fields.items():
            field_value = getattr(inspection, field_name, None)
            
            if field_value and field_value != 'na':  # Only count inspected fields
                # Apply dynamic weight adjustments
                adjusted_weight = _calculate_adjusted_weight(
                    base_weight, category_name, field_name, age_factor, mileage_factor
                )
                
                total_possible_score += adjusted_weight
                
                # Calculate score based on field value with enhanced penalties
                field_score, failure_severity = _calculate_field_score(
                    field_value, adjusted_weight, category_name, field_name
                )
                
                actual_score += field_score
                
                # Track failures by category and severity
                if failure_severity > 0:
                    system_failures[category_name].append({
                        'field': field_name,
                        'severity': field_value,
                        'weight': adjusted_weight,
                        'score_impact': adjusted_weight - field_score
                    })
                    
                    # Count failures by type
                    if field_value == 'fail':
                        if category_name == 'critical':
                            critical_failures += 1
                            safety_critical_count += 1
                        else:
                            major_failures += 1
                    elif field_value == 'major':
                        major_failures += 1
                        if category_name == 'critical':
                            safety_critical_count += 1
                    elif field_value in ['minor', 'needs_attention']:
                        minor_failures += 1
                    
                    weighted_failures += failure_severity * category_multiplier
    
    # Calculate base health percentage
    if total_possible_score > 0:
        base_health_percentage = (actual_score / total_possible_score) * 100
    else:
        base_health_percentage = 0
    
    # Apply contextual adjustments
    adjusted_health_percentage = _apply_contextual_adjustments(
        base_health_percentage, 
        critical_failures, 
        safety_critical_count,
        weighted_failures,
        system_failures,
        vehicle_age,
        mileage
    )
    
    # Determine health index category with enhanced thresholds
    health_index = _determine_health_index_category(
        adjusted_health_percentage, 
        critical_failures, 
        safety_critical_count
    )
    
    # Determine inspection result with enhanced logic
    inspection_result = _determine_enhanced_inspection_result(
        adjusted_health_percentage, 
        critical_failures, 
        major_failures, 
        minor_failures,
        safety_critical_count,
        system_failures
    )
    
    return health_index, inspection_result


# Enhanced helper functions for the redesigned health index calculation

def _calculate_vehicle_age(vehicle):
    """Calculate vehicle age in years from manufacture year."""
    from datetime import datetime
    try:
        current_year = datetime.now().year
        return max(0, current_year - vehicle.manufacture_year)
    except:
        return 0

def _calculate_age_factor(age_years):
    """Calculate age adjustment factor (1.0 = no adjustment, >1.0 = more lenient)."""
    if age_years <= 3:
        return 1.0  # New vehicles - standard expectations
    elif age_years <= 7:
        return 1.05  # Slightly more lenient for mid-age vehicles
    elif age_years <= 12:
        return 1.1  # More lenient for older vehicles
    elif age_years <= 20:
        return 1.15  # Even more lenient for very old vehicles
    else:
        return 1.2  # Most lenient for classic/vintage vehicles

def _calculate_mileage_factor(mileage):
    """Calculate mileage adjustment factor based on vehicle usage."""
    if mileage <= 30000:
        return 1.0  # Low mileage - standard expectations
    elif mileage <= 75000:
        return 1.02  # Moderate mileage
    elif mileage <= 125000:
        return 1.05  # High mileage
    elif mileage <= 200000:
        return 1.08  # Very high mileage
    else:
        return 1.1  # Extremely high mileage

def _get_category_multiplier(category_name):
    """Get severity multiplier for different system categories."""
    multipliers = {
        'critical': 3.0,    # Critical safety systems have highest impact
        'important': 2.0,   # Important mechanical systems
        'standard': 1.5,    # Standard operational systems
        'interior': 1.2,    # Interior and convenience systems
        'minor': 1.0,       # Appearance and minor systems
        'advanced': 1.8,    # Advanced and hybrid systems
    }
    return multipliers.get(category_name, 1.0)

def _calculate_adjusted_weight(base_weight, category, field_name, age_factor, mileage_factor):
    """Calculate dynamically adjusted weight for a field."""
    # Base adjustment for age and mileage
    adjusted_weight = base_weight * age_factor * mileage_factor
    
    # Special adjustments for specific fields
    high_wear_items = [
        'brake_pad_life', 'tread_depth', 'tire_condition', 'brake_rotors_drums',
        'wiper_blade_replacement', 'cabin_air_filter', 'air_filter_condition'
    ]
    
    if field_name in high_wear_items:
        # These items are expected to wear with age/mileage
        adjusted_weight *= 1.1
    
    return round(adjusted_weight, 2)

def _calculate_field_score(field_value, weight, category, field_name):
    """Calculate score and failure severity for a field."""
    if field_value == 'pass':
        return weight, 0
    elif field_value == 'minor' or field_value == 'needs_attention':
        # Minor issues: 75% score for critical, 80% for others
        multiplier = 0.75 if category == 'critical' else 0.80
        return weight * multiplier, 1
    elif field_value == 'major':
        # Major issues: 40% score for critical, 50% for others
        multiplier = 0.40 if category == 'critical' else 0.50
        return weight * multiplier, 2
    elif field_value == 'fail':
        # Complete failures: 0% score, but critical failures are worse
        return 0, 4 if category == 'critical' else 3
    else:
        return weight, 0  # Default for 'na' or unknown values

def _apply_contextual_adjustments(base_percentage, critical_failures, safety_critical_count, 
                                weighted_failures, system_failures, vehicle_age, mileage):
    """Apply contextual adjustments to the base health percentage."""
    adjusted_percentage = base_percentage
    
    # Severe penalty for multiple critical system failures
    if critical_failures >= 3:
        adjusted_percentage *= 0.7  # 30% penalty
    elif critical_failures >= 2:
        adjusted_percentage *= 0.8  # 20% penalty
    elif critical_failures >= 1:
        adjusted_percentage *= 0.9  # 10% penalty
    
    # Additional penalty for safety-critical issues
    if safety_critical_count >= 5:
        adjusted_percentage *= 0.85
    elif safety_critical_count >= 3:
        adjusted_percentage *= 0.9
    
    # Penalty for widespread system failures
    failed_systems = sum(1 for failures in system_failures.values() if failures)
    if failed_systems >= 5:
        adjusted_percentage *= 0.9
    elif failed_systems >= 4:
        adjusted_percentage *= 0.95
    
    # Bonus for well-maintained older vehicles
    if vehicle_age > 10 and base_percentage > 85:
        adjusted_percentage = min(100, adjusted_percentage * 1.02)
    
    return max(0, min(100, adjusted_percentage))

def _determine_health_index_category(percentage, critical_failures, safety_critical_count):
    """Determine health index category with enhanced logic."""
    # Override for critical safety failures
    if critical_failures >= 3 or safety_critical_count >= 5:
        return "Critical - Unsafe (<40%)"
    elif critical_failures >= 2 or safety_critical_count >= 3:
        return "Poor - Safety Concerns (40-59%)"
    
    # Standard percentage-based categories with safety considerations
    if percentage >= 95:
        return "Excellent - Like New (95-100%)"
    elif percentage >= 90:
        return "Excellent - Very Good Condition (90-94%)"
    elif percentage >= 85:
        return "Good - Well Maintained (85-89%)"
    elif percentage >= 80:
        return "Good - Minor Issues (80-84%)"
    elif percentage >= 75:
        return "Fair - Moderate Issues (75-79%)"
    elif percentage >= 70:
        return "Fair - Multiple Issues (70-74%)"
    elif percentage >= 60:
        return "Poor - Significant Issues (60-69%)"
    elif percentage >= 40:
        return "Poor - Major Repairs Needed (40-59%)"
    else:
        return "Critical - Extensive Repairs Required (<40%)"

def _determine_enhanced_inspection_result(percentage, critical_failures, major_failures, 
                                        minor_failures, safety_critical_count, system_failures):
    """Enhanced inspection result determination with comprehensive failure analysis."""
    
    # Immediate failure conditions
    if critical_failures >= 3 or safety_critical_count >= 5 or percentage < 35:
        return "FAI"  # Failed - Unsafe
    
    # Major failure conditions
    if critical_failures >= 2 or safety_critical_count >= 3 or percentage < 50:
        return "FJD"  # Failed due to major Defects
    
    # Minor failure conditions
    if critical_failures >= 1 or major_failures > 10 or percentage < 65:
        return "FMD"  # Failed due to minor Defects
    
    # Passing conditions with defects
    if major_failures > 5 or minor_failures > 15:
        return "PJD"  # Passed with major Defects
    elif major_failures > 0 or minor_failures > 8:
        return "PMD"  # Passed with minor Defects
    else:
        return "PAS"  # Passed

def _determine_initial_inspection_result(
    health_percentage: float, 
    critical_failures: int, 
    major_failures: int,
    minor_failures: int,
    inspection
) -> str:
    """
    Legacy function - redirects to enhanced result determination.
    Maintained for backward compatibility.
    """
    safety_critical_count = len(inspection.safety_critical_issues) if hasattr(inspection, 'safety_critical_issues') else critical_failures
    system_failures = {}  # Simplified for legacy compatibility
    
    return _determine_enhanced_inspection_result(
        health_percentage, critical_failures, major_failures, 
        minor_failures, safety_critical_count, system_failures
    )


def categorize_initial_inspection_failures(inspection) -> Dict:
    """
    Categorize failures by system and severity for initial inspection.
    
    Args:
        inspection: InitialInspection model instance
        
    Returns:
        Dictionary containing categorized failure information
    """
    field_weights = get_initial_inspection_field_weights()
    
    categorized_failures = {
        'critical': [],
        'important': [],
        'standard': [],
        'interior': [],
        'minor': [],
        'advanced': [],
    }
    
    for category_name, fields in field_weights.items():
        for field_name, weight in fields.items():
            field_value = getattr(inspection, field_name, None)
            if field_value in ['fail', 'major', 'minor', 'needs_attention']:
                # Get the verbose name from the model field
                try:
                    field_obj = inspection._meta.get_field(field_name)
                    description = field_obj.verbose_name or field_name.replace('_', ' ').title()
                except:
                    description = field_name.replace('_', ' ').title()
                
                categorized_failures[category_name].append({
                    'field': field_name,
                    'description': description,
                    'severity': field_value,
                    'weight': weight
                })
    
    return categorized_failures


def calculate_system_scores(inspection) -> Dict[str, float]:
    """
    Calculate individual system scores for initial inspection.
    
    Args:
        inspection: InitialInspection model instance
        
    Returns:
        Dictionary with system names and their percentage scores
    """
    field_weights = get_initial_inspection_field_weights()
    system_scores = {}
    
    for system_name, fields in field_weights.items():
        total_possible = 0
        actual_score = 0
        
        for field_name, weight in fields.items():
            field_value = getattr(inspection, field_name, None)
            
            if field_value:  # Only count inspected fields
                total_possible += weight
                
                if field_value == 'pass':
                    actual_score += weight
                elif field_value in ['minor', 'needs_attention']:
                    actual_score += weight * 0.7
                elif field_value == 'major':
                    actual_score += weight * 0.3
                # 'fail' gets 0 points
        
        if total_possible > 0:
            system_scores[system_name] = round((actual_score / total_possible) * 100, 1)
        else:
            system_scores[system_name] = 0.0
    
    return system_scores


def get_initial_inspection_recommendations(inspection) -> List[str]:
    """
    Generate maintenance recommendations based on initial inspection results.
    
    Args:
        inspection: InitialInspection model instance with completed form data
        
    Returns:
        List of recommendation strings with urgency indicators
    """
    recommendations = []
    
    # Define recommendation mappings for initial inspection fields
    recommendation_map = {
        # Critical Safety Systems - URGENT recommendations
        'brake_vibrations': "URGENT: Inspect and repair brake system - abnormal vibrations detected",
        'brake_pedal_specs': "URGENT: Adjust brake pedal free play and travel to specifications",
        'abs_operation': "URGENT: Diagnose and repair ABS system malfunction",
        'parking_brake_operation': "URGENT: Repair parking brake system - safety critical",
        'seat_belt_condition': "URGENT: Replace damaged seat belts immediately",
        'seat_belt_operation': "URGENT: Repair seat belt mechanism - safety critical",
        'steering_feel': "URGENT: Inspect steering system - abnormal feel detected",
        'steering_centered': "URGENT: Perform wheel alignment - steering wheel not centered",
        'vehicle_tracking': "URGENT: Perform wheel alignment - vehicle not tracking straight",
        'tire_condition': "URGENT: Replace damaged tires immediately",
        'tread_depth': "URGENT: Replace tires - insufficient tread depth (<5/32\")",
        'tire_specifications': "URGENT: Replace tires with correct OEM specifications",
        'brake_calipers_lines': "URGENT: Repair brake calipers and lines - leaks detected",
        'brake_pad_life': "URGENT: Replace brake pads - less than 50% life remaining",
        'brake_rotors_drums': "URGENT: Replace brake rotors/drums - out of specification",
        'headlight_alignment': "URGENT: Align headlights for proper visibility",
        'brake_lights': "URGENT: Repair brake lights - safety critical",
        'turn_signals': "URGENT: Repair turn signals - safety critical",
        'airbags_present': "URGENT: Inspect airbag system - deployment signs detected",
        
        # Important Mechanical Systems
        'cold_engine_operation': "Diagnose cold engine operation issues",
        'throttle_operation': "Service throttle system for proper cold start operation",
        'operating_temp_performance': "Diagnose engine performance issues at operating temperature",
        'normal_operating_temp': "Inspect cooling system - engine not reaching normal temperature",
        'engine_fan_operation': "Repair engine cooling fan system",
        'transmission_operation': "Service transmission/clutch system",
        'auto_trans_cold': "Service automatic transmission - cold operation issues",
        'auto_trans_operating': "Service automatic transmission - operating temperature issues",
        'frame_unibody_condition': "Inspect and repair frame/unibody damage",
        'panel_alignment': "Adjust body panel alignment",
        'underbody_condition': "Repair underbody damage and corrosion",
        'suspension_leaks_wear': "Replace worn suspension components",
        'struts_shocks_condition': "Replace leaking struts/shocks",
        'power_steering_leaks': "Repair power steering system leaks",
        'exhaust_system': "Repair exhaust system leaks and damage",
        'engine_trans_mounts': "Replace worn engine/transmission mounts",
        'drive_axle_shafts': "Repair drive/axle shaft damage",
        'cv_joints_boots': "Replace worn CV joints and boots",
        'engine_fluid_leaks': "Repair engine fluid leaks",
        'transmission_leaks': "Repair transmission case/pan leaks",
        'differential_fluid': "Service differential fluid",
        'battery_test': "Replace battery - failed load test",
        'charging_system': "Repair charging system malfunction",
        'coolant_level': "Top up coolant and check for leaks",
        'coolant_protection': "Service cooling system - insufficient freeze protection",
        'oil_filter_change': "Change engine oil and filter",
        'fluid_levels': "Top up all fluid levels",
        'fluid_contamination': "Replace contaminated fluids",
        
        # Standard Systems
        'warmup_operation': "Diagnose warm-up operation issues",
        'speedometer_function': "Repair speedometer malfunction",
        'odometer_function': "Repair odometer registration issues",
        'cruise_control': "Repair cruise control system",
        'heater_operation': "Repair heating system",
        'ac_operation': "Service air conditioning system",
        'engine_noise': "Diagnose abnormal engine noise",
        'interior_noise': "Address interior squeaks and rattles",
        'wind_road_noise': "Inspect door seals and weatherstripping",
        'tire_vibration': "Balance tires and inspect for damage",
        'wheel_covers': "Secure or replace wheel covers",
        'brake_system_equipment': "Install missing brake system components",
        'drive_belts_hoses': "Replace cracked drive belts and hoses",
        'air_filter_condition': "Replace air filter",
        'battery_damage': "Replace damaged battery",
        'battery_posts_cables': "Clean battery posts and replace damaged cables",
        'battery_secured': "Properly secure battery",
        'oil_sludge_check': "Perform engine flush - oil sludge detected",
        'owners_manual': "Obtain owner's manual and warranty booklet",
        'fuel_gauge': "Repair fuel gauge malfunction",
        'battery_voltage_gauge': "Repair battery voltage gauge",
        'temp_gauge': "Repair engine temperature gauge",
        'horn_function': "Repair horn operation",
        'emissions_test': "Perform required emissions testing",
        'tail_lights': "Replace tail light bulbs",
        'side_marker_lights': "Replace side marker light bulbs",
        'backup_lights': "Replace backup light bulbs",
        'license_plate_lights': "Replace license plate light bulbs",
        'exterior_lights_condition': "Replace damaged exterior light housings",
        
        # Interior and Convenience Systems
        'instrument_panel': "Repair instrument panel/warning lights",
        'hvac_panel': "Repair HVAC panel controls",
        'instrument_dimmer': "Repair instrument light dimmer",
        'hazard_flashers': "Repair hazard flasher system",
        'rearview_mirror': "Replace or adjust rear-view mirror",
        'exterior_mirrors': "Repair exterior mirror adjustment",
        'remote_mirror_control': "Repair remote mirror control",
        'glass_condition': "Repair or replace damaged glass",
        'window_tint': "Ensure window tint compliance with laws",
        'dome_courtesy_lights': "Replace dome/courtesy light bulbs",
        'power_windows': "Repair power window operation",
        'window_locks': "Repair window lock function",
        'audio_system': "Repair audio/CD/Aux system",
        'audio_speakers': "Replace distorted speakers",
        'antenna': "Repair or replace antenna",
        'clock_operation': "Repair clock function",
        'power_outlet': "Repair 12v power outlet",
        'doors_operation': "Adjust door operation",
        'door_locks': "Repair door lock mechanisms",
        'keyless_entry': "Repair remote keyless entry",
        'master_keys': "Obtain second master key",
        'theft_deterrent': "Repair theft deterrent system",
        'seat_adjustments': "Repair seat adjustment mechanisms",
        'seat_heaters': "Repair seat heater function",
        'memory_seat': "Repair memory seat controls",
        'headrests': "Repair headrest adjustment",
        'rear_defogger': "Repair rear defogger",
        'defogger_indicator': "Replace defogger indicator light",
        'luggage_light': "Replace luggage compartment light",
        'hood_trunk_latches': "Repair hood and trunk latches",
        'emergency_trunk_release': "Repair emergency trunk release",
        'fuel_door_release': "Repair fuel door release",
        
        # Appearance and Minor Systems
        'spare_tire_present': "Obtain spare tire or inflator kit",
        'spare_tire_tread': "Replace spare tire - insufficient tread",
        'spare_tire_pressure': "Inflate spare tire to correct pressure",
        'spare_tire_damage': "Replace damaged spare tire",
        'spare_tire_secured': "Properly secure spare tire",
        'jack_tools': "Obtain complete jack and tool set",
        'body_surface': "Repair body surface damage",
        'paint_scratches': "Touch up paint scratches and chips",
        'paint_repairs': "Repair improper paint work",
        'glass_repairs': "Repair improper glass work",
        'bumpers_condition': "Repair bumper cuts and gouges",
        'interior_surfaces': "Repair excessive wear on interior surfaces",
        'cabin_air_filter': "Replace cabin air filter",
        'vehicle_odors': "Address vehicle odors",
        'upholstery_panels': "Repair upholstery and panel damage",
        
        # Advanced Systems
        'navigation_system': "Service navigation system and clear memory",
        'head_unit_software': "Update head unit software",
        'transfer_case': "Service 4WD transfer case",
        'truck_bed_condition': "Repair truck bed damage",
        'truck_bed_liner': "Secure truck bed liner",
        'backup_camera': "Repair backup camera function",
        'lane_keep_assist': "Service Lane Keep Assist system",
        'adaptive_cruise': "Service Adaptive Cruise/Pre-Collision systems",
        'parking_assist': "Repair Intelligent Parking Assist",
        
        # Hybrid Systems
        'hybrid_battery': "Service hybrid battery system",
        'battery_control_module': "Repair battery control module",
        'hybrid_power_mgmt': "Service hybrid power management system",
        'electric_motor': "Service electric motor/generator",
        'ecvt_operation': "Service ECVT transmission",
        'power_inverter': "Repair power inverter",
        'inverter_coolant': "Service inverter coolant system",
        'ev_modes': "Repair EV/Eco/Power mode functions",
        'hybrid_park_mechanism': "Repair hybrid transaxle park mechanism",
    }
    
    # Get field weights to determine criticality
    field_weights = get_initial_inspection_field_weights()
    critical_fields = field_weights['critical']
    
    # Check each field for issues and generate recommendations
    for field_name, recommendation in recommendation_map.items():
        field_value = getattr(inspection, field_name, None)
        if field_value in ['fail', 'major', 'minor', 'needs_attention']:
            
            # Add urgency prefix for critical systems if not already present
            if field_name in critical_fields and not recommendation.startswith("URGENT:"):
                recommendation = f"URGENT: {recommendation}"
            elif field_value == 'fail':
                recommendation = f"CRITICAL: {recommendation}"
            elif field_value == 'major':
                recommendation = f"HIGH PRIORITY: {recommendation}"
            
            recommendations.append(recommendation)
    
    # Add general recommendations based on overall condition
    failed_points = inspection.failed_points
    critical_issues = inspection.safety_critical_issues
    
    if len(critical_issues) > 0:
        recommendations.insert(0, f"URGENT: Address {len(critical_issues)} safety-critical issue(s) before operating vehicle")
    
    if len(failed_points) > 15:
        recommendations.append("RECOMMENDATION: Schedule comprehensive vehicle reconditioning due to multiple issues")
    elif len(failed_points) > 8:
        recommendations.append("RECOMMENDATION: Schedule major service to address multiple system issues")
    
    # Add cost estimation recommendation
    try:
        if inspection.estimated_repair_cost and inspection.estimated_repair_cost > 5000:
            recommendations.append(f"COST CONSIDERATION: Estimated repair cost ${inspection.estimated_repair_cost:,.2f} - evaluate vehicle value vs repair costs")
    except:
        pass
    
    if not recommendations:
        recommendations.append("Vehicle is in good condition - continue regular maintenance schedule")
    
    return recommendations


def generate_initial_inspection_number() -> str:
    """
    Generate a unique initial inspection number in format: INIT-YYYY-NNNN
    """
    from datetime import datetime
    from .models import InitialInspection
    
    current_year = datetime.now().year
    prefix = f"INIT-{current_year}-"
    
    # Find the highest number for this year
    existing_inspections = InitialInspection.objects.filter(
        inspection_number__startswith=prefix
    ).order_by('-inspection_number')
    
    if existing_inspections.exists():
        last_number = existing_inspections.first().inspection_number
        try:
            # Extract the number part and increment
            number_part = int(last_number.split('-')[-1])
            next_number = number_part + 1
        except (ValueError, IndexError):
            next_number = 1000
    else:
        next_number = 1000
    
    return f"{prefix}{next_number:04d}"


def generate_initial_inspection_summary(inspection) -> Dict:
    """
    Generate a comprehensive summary of the initial inspection results.
    
    Args:
        inspection: InitialInspection model instance with completed form data
{{ ... }}
        
    Returns:
        Dictionary containing comprehensive inspection summary data
    """
    health_index, inspection_result = calculate_initial_inspection_health_index(inspection)
    recommendations = get_initial_inspection_recommendations(inspection)
    failed_points = inspection.failed_points
    critical_issues = inspection.safety_critical_issues
    system_scores = calculate_system_scores(inspection)
    categorized_failures = categorize_initial_inspection_failures(inspection)
    
    # Calculate additional metrics
    total_issues = len(failed_points)
    critical_issue_count = len(critical_issues)
    
    # Determine overall assessment
    if "Excellent" in health_index:
        overall_assessment = "Excellent condition - ready for immediate use"
    elif "Good" in health_index:
        overall_assessment = "Good condition - minor maintenance recommended"
    elif "Fair" in health_index:
        overall_assessment = "Fair condition - moderate repairs needed"
    elif "Poor" in health_index:
        overall_assessment = "Poor condition - significant repairs required"
    else:
        overall_assessment = "Critical condition - major repairs required before use"
    
    # Calculate estimated timeframe for repairs
    if critical_issue_count > 0:
        repair_timeframe = "Immediate attention required"
    elif total_issues > 10:
        repair_timeframe = "1-2 weeks for comprehensive repairs"
    elif total_issues > 5:
        repair_timeframe = "3-5 days for moderate repairs"
    elif total_issues > 0:
        repair_timeframe = "1-2 days for minor repairs"
    else:
        repair_timeframe = "No repairs needed"
    
    # Generate priority recommendations (top 5 most critical)
    priority_recommendations = []
    urgent_recommendations = [r for r in recommendations if r.startswith("URGENT:")]
    critical_recommendations = [r for r in recommendations if r.startswith("CRITICAL:")]
    high_priority_recommendations = [r for r in recommendations if r.startswith("HIGH PRIORITY:")]
    
    priority_recommendations.extend(urgent_recommendations[:3])
    priority_recommendations.extend(critical_recommendations[:2])
    if len(priority_recommendations) < 5:
        priority_recommendations.extend(high_priority_recommendations[:5-len(priority_recommendations)])
    
    return {
        # Basic inspection information
        'inspection_number': inspection.inspection_number,
        'vehicle_vin': inspection.vehicle.vin,
        'inspection_date': inspection.inspection_date,
        'technician': inspection.technician.get_full_name() if inspection.technician else None,
        'mileage': inspection.mileage_at_inspection,
        'is_completed': inspection.is_completed,
        'completed_at': inspection.completed_at,
        
        # Scoring and health metrics
        'health_index': health_index,
        'inspection_result': inspection_result,
        'overall_assessment': overall_assessment,
        'completion_percentage': inspection.completion_percentage,
        'total_points_checked': inspection.total_points_checked,
        
        # Issue analysis
        'total_issues': total_issues,
        'critical_issue_count': critical_issue_count,
        'failed_points': failed_points,
        'critical_issues': critical_issues,
        'has_major_issues': inspection.has_major_issues,
        
        # System-specific scores
        'system_scores': system_scores,
        'categorized_failures': categorized_failures,
        
        # Recommendations and actions
        'recommendations': recommendations,
        'priority_recommendations': priority_recommendations,
        'repair_timeframe': repair_timeframe,
        
        # Cost and value assessment
        'estimated_repair_cost': float(inspection.estimated_repair_cost) if inspection.estimated_repair_cost else None,
        'overall_condition_rating': inspection.overall_condition_rating,
        
        # Additional notes
        'overall_notes': inspection.overall_notes,
        'technician_recommendations': inspection.recommendations,
        
        # Section-specific notes
        'section_notes': {
            'road_test': inspection.road_test_notes,
            'frame_structure': inspection.frame_structure_notes,
            'under_hood': inspection.under_hood_notes,
            'functional_walkaround': inspection.functional_walkaround_notes,
            'interior_functions': inspection.interior_functions_notes,
            'exterior_appearance': inspection.exterior_appearance_notes,
            'optional_systems': inspection.optional_systems_notes,
            'safety_systems': inspection.safety_systems_notes,
            'hybrid_components': inspection.hybrid_components_notes,
        },
        
        # Report metadata
        'report_generated_at': timezone.now(),
        'inspection_type': '160-Point Initial Vehicle Inspection',
        'report_version': '1.0',
    }


def generate_initial_inspection_executive_summary(inspection) -> str:
    """
    Generate a concise executive summary of the initial inspection.
    
    Args:
        inspection: InitialInspection model instance
        
    Returns:
        String containing executive summary
    """
    summary_data = generate_initial_inspection_summary(inspection)
    
    health_index = summary_data['health_index']
    total_issues = summary_data['total_issues']
    critical_issues = summary_data['critical_issue_count']
    overall_assessment = summary_data['overall_assessment']
    
    summary = f"""
EXECUTIVE SUMMARY - Initial Vehicle Inspection

Vehicle: {summary_data['vehicle_vin']}
Inspection Date: {summary_data['inspection_date'].strftime('%B %d, %Y')}
Technician: {summary_data['technician'] or 'Not Assigned'}
Mileage: {summary_data['mileage']:,} miles

OVERALL CONDITION: {health_index}
ASSESSMENT: {overall_assessment}

FINDINGS SUMMARY:
- Total Issues Identified: {total_issues}
- Safety-Critical Issues: {critical_issues}
- Completion Rate: {summary_data['completion_percentage']}%

"""
    
    if critical_issues > 0:
        summary += f"⚠️  URGENT: {critical_issues} safety-critical issue(s) require immediate attention before operating this vehicle.\n\n"
    
    if summary_data['priority_recommendations']:
        summary += "TOP PRIORITY ACTIONS:\n"
        for i, rec in enumerate(summary_data['priority_recommendations'][:3], 1):
            summary += f"{i}. {rec}\n"
        summary += "\n"
    
    if summary_data['estimated_repair_cost']:
        summary += f"Estimated Repair Cost: ${summary_data['estimated_repair_cost']:,.2f}\n"
    
    summary += f"Repair Timeframe: {summary_data['repair_timeframe']}\n"
    
    return summary.strip()


def generate_initial_inspection_detailed_report(inspection) -> Dict:
    """
    Generate a detailed technical report for initial inspection.
    
    Args:
        inspection: InitialInspection model instance
        
    Returns:
        Dictionary containing detailed technical report data
    """
    summary_data = generate_initial_inspection_summary(inspection)
    system_scores = summary_data['system_scores']
    categorized_failures = summary_data['categorized_failures']
    
    # Create detailed system analysis
    system_analysis = {}
    system_names = {
        'critical': 'Critical Safety Systems',
        'important': 'Important Mechanical Systems',
        'standard': 'Standard Systems',
        'interior': 'Interior & Convenience Systems',
        'minor': 'Appearance & Minor Systems',
        'advanced': 'Advanced & Hybrid Systems',
    }
    
    for system_key, system_name in system_names.items():
        score = system_scores.get(system_key, 0)
        failures = categorized_failures.get(system_key, [])
        
        if score >= 90:
            status = "Excellent"
        elif score >= 80:
            status = "Good"
        elif score >= 70:
            status = "Fair"
        elif score >= 60:
            status = "Poor"
        else:
            status = "Critical"
        
        system_analysis[system_key] = {
            'name': system_name,
            'score': score,
            'status': status,
            'failure_count': len(failures),
            'failures': failures,
        }
    
    # Generate recommendations by priority
    recommendations_by_priority = {
        'urgent': [r for r in summary_data['recommendations'] if r.startswith("URGENT:")],
        'critical': [r for r in summary_data['recommendations'] if r.startswith("CRITICAL:")],
        'high_priority': [r for r in summary_data['recommendations'] if r.startswith("HIGH PRIORITY:")],
        'standard': [r for r in summary_data['recommendations'] if not any(r.startswith(p) for p in ["URGENT:", "CRITICAL:", "HIGH PRIORITY:", "RECOMMENDATION:", "COST CONSIDERATION:"])],
        'general': [r for r in summary_data['recommendations'] if r.startswith("RECOMMENDATION:")],
        'cost_considerations': [r for r in summary_data['recommendations'] if r.startswith("COST CONSIDERATION:")],
    }
    
    return {
        **summary_data,
        'system_analysis': system_analysis,
        'recommendations_by_priority': recommendations_by_priority,
        'detailed_report_type': 'Technical Analysis Report',
    }


def export_initial_inspection_data(inspection, format_type='json') -> str:
    """
    Export initial inspection data in specified format.
    
    Args:
        inspection: InitialInspection model instance
        format_type: Export format ('json', 'csv', 'summary')
        
    Returns:
        String containing exported data
    """
    if format_type == 'summary':
        return generate_initial_inspection_executive_summary(inspection)
    
    elif format_type == 'json':
        import json
        detailed_report = generate_initial_inspection_detailed_report(inspection)
        
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(detailed_report, indent=2, default=serialize_datetime)
    
    elif format_type == 'csv':
        import csv
        from io import StringIO
        
        summary_data = generate_initial_inspection_summary(inspection)
        output = StringIO()
        
        # Write basic inspection data
        writer = csv.writer(output)
        writer.writerow(['Field', 'Value'])
        writer.writerow(['Inspection Number', summary_data['inspection_number']])
        writer.writerow(['Vehicle VIN', summary_data['vehicle_vin']])
        writer.writerow(['Inspection Date', summary_data['inspection_date']])
        writer.writerow(['Technician', summary_data['technician']])
        writer.writerow(['Mileage', summary_data['mileage']])
        writer.writerow(['Health Index', summary_data['health_index']])
        writer.writerow(['Inspection Result', summary_data['inspection_result']])
        writer.writerow(['Total Issues', summary_data['total_issues']])
        writer.writerow(['Critical Issues', summary_data['critical_issue_count']])
        writer.writerow(['Completion Percentage', f"{summary_data['completion_percentage']}%"])
        
        # Write failed points
        writer.writerow([])
        writer.writerow(['Failed Points'])
        for point in summary_data['failed_points']:
            writer.writerow([point])
        
        # Write recommendations
        writer.writerow([])
        writer.writerow(['Recommendations'])
        for rec in summary_data['recommendations']:
            writer.writerow([rec])
        
        return output.getvalue()
    
    else:
        raise ValueError(f"Unsupported format type: {format_type}")
def validate_initial_inspection_completion(inspection) -> Tuple[bool, List[str]]:
    """
    Validate that an initial inspection is ready for completion and scoring.
    
    Args:
        inspection: InitialInspection model instance
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check minimum completion percentage
    if inspection.completion_percentage < 80:
        issues.append(f"Inspection only {inspection.completion_percentage}% complete (minimum 80% required)")
    
    # Check critical safety systems
    critical_fields = [
        'brake_vibrations', 'brake_pedal_specs', 'abs_operation', 'parking_brake_operation',
        'seat_belt_condition', 'seat_belt_operation', 'steering_feel', 'vehicle_tracking',
        'tire_condition', 'tread_depth', 'brake_pad_life', 'headlight_alignment'
    ]
    
    missing_critical = []
    for field in critical_fields:
        if not getattr(inspection, field):
            try:
                field_obj = inspection._meta.get_field(field)
                missing_critical.append(field_obj.verbose_name)
            except:
                missing_critical.append(field.replace('_', ' ').title())
    
    if missing_critical:
        issues.append(f"Critical safety systems not inspected: {', '.join(missing_critical[:5])}")
    
    # Check for required technician
    if not inspection.technician:
        issues.append("Technician must be assigned before completion")
    
    # Check for basic vehicle information
    if not inspection.mileage_at_inspection:
        issues.append("Vehicle mileage must be recorded")
    
    return len(issues) == 0, issues


def sync_initial_inspection_with_regular_inspection(initial_inspection):
    """
    Create or update a regular Inspection record based on initial inspection results.
    This helps maintain consistency between the two inspection systems.
    
    Args:
        initial_inspection: InitialInspection model instance
    """
    if not initial_inspection.is_completed:
        return None
    
    try:
        from .models import Inspection
        
        # Generate inspection number for regular inspection if needed
        regular_inspection_number = f"REG-{initial_inspection.inspection_number}"
        
        # Get or create regular inspection record
        regular_inspection, created = Inspection.objects.get_or_create(
            vehicle=initial_inspection.vehicle,
            inspection_number=regular_inspection_number,
            defaults={
                'year': initial_inspection.inspection_date.year,
                'inspection_date': initial_inspection.inspection_date.date(),
                'inspection_result': initial_inspection.inspection_result,
                'vehicle_health_index': initial_inspection.vehicle_health_index,
            }
        )
        
        if not created:
            # Update existing record
            regular_inspection.inspection_result = initial_inspection.inspection_result
            regular_inspection.vehicle_health_index = initial_inspection.vehicle_health_index
            regular_inspection.save()
        
        return regular_inspection
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error syncing initial inspection {initial_inspection.pk} with regular inspection: {str(e)}")
        return None


def get_inspection_workflow_status(vehicle):
    """
    Get the current inspection workflow status for a vehicle.
    
    Args:
        vehicle: Vehicle model instance
        
    Returns:
        Dictionary with workflow status information
    """
    from .models import InitialInspection, Inspection
    
    # Get latest initial inspection
    latest_initial = InitialInspection.objects.filter(vehicle=vehicle).order_by('-inspection_date').first()
    
    # Get latest regular inspection
    latest_regular = Inspection.objects.filter(vehicle=vehicle).order_by('-inspection_date').first()
    
    status = {
        'vehicle_vin': vehicle.vin,
        'has_initial_inspection': latest_initial is not None,
        'has_regular_inspection': latest_regular is not None,
        'initial_inspection_completed': latest_initial.is_completed if latest_initial else False,
        'workflow_stage': 'none',
        'recommendations': []
    }
    
    if not latest_initial:
        status['workflow_stage'] = 'needs_initial_inspection'
        status['recommendations'].append('Schedule initial 160-point inspection')
    elif not latest_initial.is_completed:
        status['workflow_stage'] = 'initial_inspection_in_progress'
        status['recommendations'].append(f'Complete initial inspection ({latest_initial.completion_percentage}% done)')
    elif latest_initial.is_completed:
        # Check if initial inspection found major issues
        critical_issues = len(latest_initial.safety_critical_issues)
        total_issues = len(latest_initial.failed_points)
        
        if critical_issues > 0:
            status['workflow_stage'] = 'requires_repairs'
            status['recommendations'].append(f'Address {critical_issues} critical safety issue(s) before regular use')
        elif total_issues > 10:
            status['workflow_stage'] = 'requires_maintenance'
            status['recommendations'].append(f'Address {total_issues} maintenance issues')
        else:
            status['workflow_stage'] = 'ready_for_service'
            status['recommendations'].append('Vehicle ready for regular maintenance schedule')
    
    # Add scoring information if available
    if latest_initial and latest_initial.is_completed:
        try:
            status['health_index'] = latest_initial.vehicle_health_index
            status['inspection_result'] = latest_initial.inspection_result
            status['last_inspection_date'] = latest_initial.inspection_date
        except:
            pass
    
    return status


def generate_inspection_workflow_report(vehicles=None):
    """
    Generate a workflow status report for vehicles.
    
    Args:
        vehicles: QuerySet of vehicles (if None, includes all vehicles)
        
    Returns:
        Dictionary with workflow report data
    """
    from vehicles.models import Vehicle
    
    if vehicles is None:
        vehicles = Vehicle.objects.all()
    
    report_data = {
        'total_vehicles': vehicles.count(),
        'workflow_summary': {
            'needs_initial_inspection': 0,
            'initial_inspection_in_progress': 0,
            'requires_repairs': 0,
            'requires_maintenance': 0,
            'ready_for_service': 0,
        },
        'vehicle_details': []
    }
    
    for vehicle in vehicles:
        status = get_inspection_workflow_status(vehicle)
        report_data['vehicle_details'].append(status)
        
        # Update summary counts
        workflow_stage = status['workflow_stage']
        if workflow_stage in report_data['workflow_summary']:
            report_data['workflow_summary'][workflow_stage] += 1
    
    return report_data