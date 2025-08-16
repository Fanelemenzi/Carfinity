# Vehicle Equipment Onboarding System

## Overview

The vehicle equipment onboarding system is a comprehensive Django-based solution for capturing detailed vehicle specifications and features during the onboarding process. This system is designed to collect extensive technical information about vehicles across multiple categories.

## System Architecture

### Models Structure

The system is built around five main model classes in the `vehicle_equip` app, each representing a different aspect of vehicle equipment:

#### 1. PowertrainAndDrivetrain
**Purpose**: Captures engine, transmission, and drivetrain specifications

**Key Fields**:
- `base_engine` - Engine type and specifications
- `engine_displacement` - Engine displacement in liters
- `engine_power` - Engine power in horsepower
- `transmission_type` - Type of transmission (Manual, Automatic, CVT, etc.)
- `gear_count` - Number of gears
- `drive_layout` - Drive configuration (FWD, RWD, AWD, 4WD)
- `fuel_system` - Fuel type (Gasoline, Diesel, Electric, Hybrid, etc.)
- `emissions_standard` - Emissions compliance standard
- `has_start_stop` - Automatic start-stop system
- `has_regenerative_braking` - Regenerative braking capability
- `gearshift_position` - Location of gearshift mechanism
- `gearshift_material` - Material of gearshift knob/handle
- `notes` - Additional powertrain notes

#### 2. ChassisSuspensionAndBraking
**Purpose**: Documents suspension, braking, and steering systems

**Key Fields**:
- `front_suspension` / `rear_suspension` - Suspension types (MacPherson, Double Wishbone, etc.)
- `front_brake_type` / `rear_brake_type` - Brake types (Disc, Drum, Ceramic, etc.)
- `brake_systems` - Primary brake system (ABS, EBD, BAS, etc.)
- `parking_brake_type` - Parking brake mechanism
- `steering_system` - Steering system type
- `steering_wheel_features` - Steering wheel capabilities
- `has_park_distance_control` - Park distance control availability

#### 3. ElectricalSystem
**Purpose**: Covers battery, charging, lighting, and electrical components

**Key Fields**:
- `primary_battery_type` / `primary_battery_capacity` - Main battery specifications
- `has_second_battery` / `second_battery_type` / `second_battery_capacity` - Secondary battery system
- `alternator_output` - Alternator capacity in amps
- `operating_voltage` - System voltage (12V, 24V, 48V, 400V, 800V)
- `headlight_type` - Headlight technology (Halogen, HID, LED, Laser, Matrix)
- `headlight_control` / `headlight_range_control` - Automatic headlight features
- `instrument_cluster_type` - Dashboard display type
- `socket_type` - Power socket types available
- `horn_type` - Horn configuration

#### 4. ExteriorFeaturesAndBody
**Purpose**: Documents body style, exterior features, and protective elements

**Key Fields**:
- `body_style` - Vehicle body type (Sedan, SUV, Truck, etc.)
- `windshield_type` / `side_windows_type` - Glass specifications
- `has_chrome_package` - Chrome trim package
- `has_roof_rails` - Roof rail/load rack presence
- `roof_type` - Roof configuration (Fixed, Sunroof, Panoramic, etc.)
- Lighting features (fog lamps, range control)
- Protection features (scuff plates, underbody guards)
- `wheel_type` - Wheel material and specifications
- `tailgate_lock_type` - Tailgate locking mechanism
- `left_mirror_type` / `right_mirror_type` - Mirror specifications
- `antenna_type` - Antenna configuration

#### 5. ActiveSafetyAndADAS
**Purpose**: Captures advanced driver assistance and safety systems

**Key Fields**:
- `cruise_control_system` - Cruise control type (Standard, Adaptive, Intelligent)
- `has_speed_limiter` - Speed limiting functionality
- `park_distance_control` - Parking assistance level
- `driver_alert_system` - Driver monitoring capabilities
- `tire_pressure_monitoring` - TPMS type and features
- `lane_assist_system` - Lane assistance level
- `blind_spot_monitoring` - Blind spot detection
- `collision_warning_system` - Collision avoidance systems
- `has_cross_traffic_alert` - Cross traffic monitoring
- `has_traffic_sign_recognition` - Traffic sign detection

## Database Relationships

All equipment models use a **OneToOneField** relationship with the main `Vehicle` model:
- Each vehicle can have exactly one instance of each equipment category
- Equipment records are automatically deleted when the associated vehicle is deleted
- Related names provide easy access: `vehicle.powertrain`, `vehicle.chassis`, etc.

## User Interface Implementation

### HTML Template Structure

The onboarding template (`templates/onboarding/onboard_vehicle_equipment.html`) is organized as follows:

1. **Stepper Navigation**: Visual progress indicator showing current step (Equipment - Step 4)
2. **Form Sections**: Five distinct sections matching the model categories
3. **Field Rendering**: Consistent field rendering using `{% include 'onboarding/field.html' %}`
4. **Navigation Controls**: Back/Next buttons for wizard navigation

### Form Organization

Fields are grouped logically under section headings:
- **Powertrain & Drivetrain** (14 fields)
- **Chassis, Suspension & Braking** (9 fields)  
- **Electrical System** (13 fields)
- **Exterior Features & Body** (19 fields)
- **Active Safety & ADAS** (10 fields)

**Total**: 65 comprehensive vehicle equipment fields

## Data Validation

### Field Constraints
- **Numeric Validators**: Engine displacement, power, gear count with min/max limits
- **Choice Fields**: Extensive use of predefined choices for consistency
- **Optional Fields**: Most fields are nullable/blank to accommodate varying vehicle specifications
- **Help Text**: Comprehensive help text for user guidance

### Business Logic
- Conditional fields (e.g., second battery fields only relevant when `has_second_battery` is True)
- Logical groupings ensure related fields are captured together
- Standardized choice values enable consistent data analysis

## Integration Points

### Wizard Integration
- Part of Django FormWizard multi-step onboarding process
- Maintains state between steps
- Validates data before proceeding to next step

### Vehicle Association
- Automatically links equipment data to the vehicle being onboarded
- Ensures data integrity through foreign key relationships
- Supports equipment updates post-onboarding

## Benefits

1. **Comprehensive Coverage**: Captures detailed technical specifications across all major vehicle systems
2. **Standardized Data**: Consistent choice fields enable reliable filtering and comparison
3. **User-Friendly**: Logical grouping and clear labeling improve user experience
4. **Scalable**: Model structure supports easy addition of new equipment categories
5. **Data Integrity**: Strong relationships and validation ensure clean data

## Future Enhancements

Potential areas for expansion:
- Interior features and comfort systems
- Entertainment and connectivity systems
- Advanced driver assistance system details
- Performance and handling characteristics
- Maintenance and service requirements

## Technical Notes

- All models inherit from Django's `Model` class
- Uses Django's built-in field types and validators
- Implements proper `__str__` methods for admin interface
- Includes comprehensive `Meta` classes for proper naming and ordering
- Follows Django best practices for model design and relationships