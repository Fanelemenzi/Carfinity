# Design Document

## Overview

This design implements a comprehensive scoring system for the 160-point Initial Vehicle Inspection that mirrors the functionality of the existing quarterly inspection scoring system. The system will calculate vehicle health indices, determine inspection results, generate maintenance recommendations, and provide detailed analytics for second-hand vehicle evaluations.

The design leverages the existing patterns established in the `Inspections` model and `utils.py` module, extending them to support the more comprehensive 160-point initial inspection checklist. The system maintains consistency with the current inspection workflow while accommodating the expanded scope and different weighting requirements of initial inspections.
#
# Architecture

### System Components

The initial inspection scoring system follows the same architectural pattern as the existing inspection system:

1. **Model Layer**: Extended `InitialInspection` model with scoring properties and methods
2. **Utility Layer**: New utility functions in `utils.py` for initial inspection calculations
3. **Admin Interface**: Enhanced admin interface with scoring displays and actions
4. **Template Layer**: Updated templates to display scoring information

### Integration Points

- **Existing Inspection System**: Reuses scoring methodology and result categorization
- **Vehicle Model**: Links to existing vehicle records for comprehensive history
- **User Management**: Integrates with existing technician user system
- **Admin Interface**: Extends current admin patterns for consistency

## Components and Interfaces

### Model Extensions

#### InitialInspection Model Properties

The `InitialInspection` model will be extended with the following calculated properties:

```python
@property
def total_points_checked(self) -> int
    """Count completed inspection points (160 total)"""

@property  
def completion_percentage(self) -> float
    """Calculate completion percentage (0-100%)"""

@property
def failed_points(self) -> List[str]
    """Get list of failed inspection point descriptions"""

@property
def has_major_issues(self) -> bool
    """Check if inspection has critical failures"""

@property
def health_index_calculation(self) -> Tuple[str, str]
    """Get calculated health index and inspection result"""
```

#### Model Methods

```python
def save(self, *args, **kwargs):
    """Override save to auto-calculate scoring when completed"""

def _update_related_records(self):
    """Update any related inspection records with calculated results"""
```

### Utility Functions

#### Core Scoring Functions

```python
def calculate_initial_inspection_health_index(inspection: InitialInspection) -> Tuple[str, str]:
    """Calculate health index for 160-point initial inspection"""

def determine_initial_inspection_result(health_percentage: float, failures: Dict) -> str:
    """Determine inspection result based on failures and health score"""

def get_initial_inspection_recommendations(inspection: InitialInspection) -> List[str]:
    """Generate maintenance recommendations based on findings"""

def generate_initial_inspection_summary(inspection: InitialInspection) -> Dict:
    """Generate comprehensive inspection summary"""

def generate_initial_inspection_number() -> str:
    """Generate unique inspection number: INIT-YYYY-NNNN"""
```

#### Supporting Functions

```python
def get_initial_inspection_field_weights() -> Dict[str, Dict[str, int]]:
    """Return categorized field weights for 160-point inspection"""

def categorize_initial_inspection_failures(inspection: InitialInspection) -> Dict:
    """Categorize failures by system and severity"""

def calculate_system_scores(inspection: InitialInspection) -> Dict[str, float]:
    """Calculate individual system scores (Road Test, Frame, etc.)"""
```

## Data Models

### Inspection Point Categories and Weights

The 160-point initial inspection will be categorized into weighted systems:

#### Critical Safety Systems (Weight: 8-12 points each)
- **Braking System**: Brake operation, pedal specs, ABS functionality
- **Steering System**: Steering response, alignment, power steering
- **Tire Safety**: Tread depth, pressure, wear patterns
- **Lighting Systems**: Headlights, brake lights, turn signals
- **Seat Belt Systems**: Operation and condition

#### Important Mechanical Systems (Weight: 4-7 points each)
- **Engine Performance**: Cold start, operating temperature, noise
- **Transmission**: Operation in all modes, fluid condition
- **Suspension**: Shocks, struts, bushings, alignment
- **Electrical Systems**: Battery, alternator, charging system
- **Frame/Structure**: Structural integrity, panel alignment

#### Standard Systems (Weight: 2-4 points each)
- **HVAC Systems**: Heating, air conditioning, ventilation
- **Interior Features**: Power windows, seats, infotainment
- **Exterior Features**: Wipers, mirrors, body condition
- **Fluid Systems**: Oil, coolant, transmission fluid levels

#### Minor Systems (Weight: 1-2 points each)
- **Convenience Features**: Cruise control, interior lighting
- **Technology Systems**: Infotainment, camera systems
- **Safety Equipment**: First aid kit, warning triangle

### Scoring Algorithm

#### Health Index Calculation
```
Total Possible Score = Sum of all applicable field weights
Actual Score = Sum of (field_weight × field_score_multiplier)

Field Score Multipliers:
- Pass: 1.0 (100%)
- Minor Issue: 0.7 (70%)
- Major Issue: 0.3 (30%)
- Fail: 0.0 (0%)
- N/A: Excluded from calculation

Health Percentage = (Actual Score / Total Possible Score) × 100
```

#### Result Determination Logic
```
Critical Failures = Count of failed critical safety systems
Major Failures = Count of major issues across all systems
Minor Failures = Count of minor issues across all systems

Result Logic:
- FAI (Failed): Critical failures ≥ 3 OR Health % < 40%
- FJD (Failed - Major Defects): Critical failures ≥ 1 AND Health % < 60%
- FMD (Failed - Minor Defects): Major failures > 8 OR Health % < 70%
- PJD (Passed - Major Defects): Major failures ≤ 5 AND Health % ≥ 70%
- PMD (Passed - Minor Defects): Minor failures ≤ 10 AND Health % ≥ 80%
- PAS (Passed): Minor failures ≤ 5 AND Health % ≥ 85%
```

## Error Handling

### Validation Rules

1. **Inspection Completion**: Minimum 80% of applicable points must be checked
2. **Critical System Coverage**: All critical safety systems must be inspected
3. **Data Integrity**: Prevent calculation on incomplete inspections
4. **Technician Assignment**: Require valid technician for completed inspections

### Error Scenarios

1. **Incomplete Inspection**: Display warning and prevent final scoring
2. **Missing Critical Data**: Highlight required fields and block completion
3. **Calculation Errors**: Log errors and use fallback scoring methods
4. **Database Errors**: Graceful degradation with user notification

### Fallback Mechanisms

1. **Partial Scoring**: Calculate based on completed sections only
2. **Manual Override**: Allow admin users to manually set results
3. **Recalculation**: Provide admin action to recalculate all scores
4. **Audit Trail**: Log all scoring calculations and changes

## Testing Strategy

### Unit Testing

1. **Scoring Calculations**: Test all scoring algorithms with various input combinations
2. **Model Properties**: Verify all calculated properties return correct values
3. **Utility Functions**: Test edge cases and error conditions
4. **Data Validation**: Test model validation rules and constraints

### Integration Testing

1. **Admin Interface**: Test scoring displays and admin actions
2. **Template Rendering**: Verify scoring information displays correctly
3. **Database Operations**: Test save operations and related record updates
4. **Report Generation**: Test summary and recommendation generation

### Performance Testing

1. **Calculation Speed**: Ensure scoring calculations complete within acceptable time
2. **Database Queries**: Optimize queries for large datasets
3. **Memory Usage**: Monitor memory consumption during bulk operations
4. **Concurrent Access**: Test multiple technicians using system simultaneously

### User Acceptance Testing

1. **Technician Workflow**: Test complete inspection and scoring workflow
2. **Admin Operations**: Test admin interface functionality and reporting
3. **Report Accuracy**: Verify scoring results match manual calculations
4. **User Experience**: Ensure intuitive interface and clear feedback

## Implementation Phases

### Phase 1: Core Scoring System
- Extend `InitialInspection` model with scoring properties
- Implement core utility functions for health index calculation
- Add basic admin interface enhancements

### Phase 2: Advanced Features
- Implement recommendation generation system
- Add comprehensive summary reporting
- Enhance admin interface with bulk operations

### Phase 3: Integration and Polish
- Integrate with existing inspection workflows
- Add template enhancements for scoring display
- Implement audit trail and logging

### Phase 4: Testing and Optimization
- Comprehensive testing across all components
- Performance optimization and query tuning
- User acceptance testing and feedback incorporation