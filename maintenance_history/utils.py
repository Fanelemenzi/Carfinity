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