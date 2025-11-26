# Insurance Assessment Repair Cost Calculation System

## Overview

This document explains how the backend calculates repair estimates for each vehicle section and determines labor costs and material costs in the insurance assessment system.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Section-Based Cost Calculation](#section-based-cost-calculation)
3. [Labor and Material Cost Breakdown](#labor-and-material-cost-breakdown)
4. [Settlement Calculation Logic](#settlement-calculation-logic)
5. [Frontend Integration](#frontend-integration)
6. [Cost Structure Examples](#cost-structure-examples)
7. [API Reference](#api-reference)

## System Architecture

The repair cost calculation uses a multi-layered approach:

- **Section Assessment**: Each vehicle section is assessed independently
- **Damage Severity Mapping**: Damage levels are mapped to base repair costs
- **Component Multipliers**: High-value components receive cost multipliers
- **Labor Calculation**: Labor costs are calculated as a percentage of parts costs
- **Additional Costs**: Paint, materials, shop supplies, and VAT are added

## Section-Based Cost Calculation

### Base Cost Structure

The system defines base costs for different damage severities across eight vehicle sections:

```python
base_costs = {
    'exterior': {
        'none': £0, 'light': £250, 'moderate': £650, 
        'severe': £1500, 'destroyed': £3200
    },
    'wheels': {
        'none': £0, 'light': £75, 'moderate': £200, 
        'severe': £500, 'destroyed': £950
    },
    'interior': {
        'none': £0, 'light': £150, 'moderate': £400, 
        'severe': £950, 'destroyed': £1800
    },
    'mechanical': {
        'excellent': £0, 'good': £0, 'fair': £300, 
        'poor': £800, 'failed': £2200
    },
    'electrical': {
        'working': £0, 'intermittent': £150, 'not_working': £550, 
        'not_tested': £250
    },
    'safety': {
        'working': £0, 'fault': £450, 'deployed': £1200, 
        'not_working': £800, 'not_tested': £300
    },
    'structural': {
        'intact': £0, 'minor_damage': £750, 'moderate_damage': £2200, 
        'severe_damage': £5500, 'compromised': £12000
    },
    'fluids': {
        'good': £0, 'low': £80, 'contaminated': £300, 
        'leaking': £550, 'empty': £400
    }
}
```

### Component-Specific Multipliers

High-value or complex components receive additional cost multipliers:

```python
component_multipliers = {
    'exterior': {
        'hood': 1.5,
        'front_bumper': 1.2,
        'rear_bumper': 1.2,
        'headlight_housings': 2.0,
        'taillight_housings': 1.8,
        'front_fenders': 1.3,
        'rear_quarter_panels': 1.4
    },
    'mechanical': {
        'engine_block': 3.0,
        'radiator': 1.5,
        'transmission': 2.5,
        'steering_rack': 2.0
    },
    'safety': {
        'airbag_systems': 2.5,
        'abs_system': 2.0,
        'stability_control': 1.8
    },
    'structural': {
        'frame_rails': 2.0,
        'firewall': 1.8,
        'cross_members': 1.5
    }
}
```

### Calculation Method

The `calculate_section_cost()` method processes each section:

1. **Iterate through all fields** in the section object
2. **Map field values** to damage severity levels
3. **Apply base costs** for each damaged component
4. **Apply multipliers** for high-value components
5. **Sum total section cost**

```python
def calculate_section_cost(self, section_obj, section_type):
    total_cost = 0
    costs = base_costs.get(section_type, {})
    multipliers = component_multipliers.get(section_type, {})
    
    for field in section_obj._meta.fields:
        field_value = getattr(section_obj, field.name, None)
        if field_value and field_value in costs:
            base_cost = costs[field_value]
            multiplier = multipliers.get(field.name, 1.0)
            total_cost += base_cost * multiplier
    
    return total_cost
```

## Labor and Material Cost Breakdown

### Labor Cost Calculation

Labor costs are calculated as **70% of parts costs**, following automotive industry standards:

```python
labor_cost = parts_cost * 0.7
```

This ratio reflects the typical relationship where labor represents 60-80% of parts costs in automotive repairs.

### Additional Cost Components

The system adds several additional cost components to create a comprehensive estimate:

```python
def calculate_detailed_cost_breakdown(self, assessment):
    # Calculate parts and labor for each section
    for section_type, section_obj in sections:
        if section_obj:
            parts_cost = self.calculate_section_cost(section_obj, section_type)
            labor_cost = parts_cost * 0.7  # 70% of parts cost
            section_total = parts_cost + labor_cost
    
    # Additional costs
    paint_materials = total_parts_cost * 0.15  # 15% for paint and materials
    shop_supplies = total_parts_cost * 0.08    # 8% for shop supplies
    vat = (subtotal + paint_materials + shop_supplies) * 0.20  # 20% VAT
    
    return detailed_breakdown
```

### Cost Breakdown Structure

```python
detailed_costs = {
    'section_costs': {
        'exterior': {
            'parts_cost': 1200.00,
            'labor_cost': 840.00,      # 70% of parts
            'total_cost': 2040.00,
            'severity': 'moderate'
        },
        # ... other sections
    },
    'subtotal': 5000.00,              # Sum of all section totals
    'paint_materials': 750.00,        # 15% of subtotal
    'shop_supplies': 400.00,          # 8% of subtotal
    'total_before_tax': 6150.00,
    'vat': 1230.00,                   # 20% VAT
    'grand_total': 7380.00            # Final repair estimate
}
```

## Settlement Calculation Logic

### Total Loss Determination

The system determines if a vehicle is a total loss using a **70% threshold**:

```python
total_loss_threshold = market_value * 0.70
is_total_loss = repair_cost > total_loss_threshold
```

### Depreciation Calculation

Two types of depreciation are calculated:

#### Age-Based Depreciation
```python
vehicle_age = current_year - manufacture_year
age_depreciation_rate = min(0.15, 0.02 * vehicle_age)  # 2% per year, max 15%
```

#### Damage-Based Depreciation
```python
severity_depreciation = {
    'cosmetic': 0.02,    # 2%
    'minor': 0.03,       # 3%
    'moderate': 0.05,    # 5%
    'major': 0.08,       # 8%
    'total_loss': 0.15   # 15%
}
```

### Settlement Amount Calculation

```python
def calculate_settlement_details(self, assessment):
    # Calculate total depreciation
    total_depreciation_rate = age_depreciation_rate + damage_depreciation
    depreciation_amount = market_value * total_depreciation_rate
    
    # Get policy deductible
    deductible = getattr(assessment.vehicle.policy, 'deductible', 500)
    
    if is_total_loss:
        # Total loss settlement
        settlement_amount = market_value - depreciation_amount - deductible
        if salvage_value > 0:
            settlement_amount += salvage_value
    else:
        # Repair settlement
        settlement_amount = repair_cost - deductible
    
    return settlement_details
```

## Frontend Integration

### Template Data Structure

The backend passes structured data to the frontend template:

```python
assessment_data = {
    'sections': [
        {
            'id': 'exterior',
            'name': 'EXTERIOR DAMAGE',
            'icon': '🚗',
            'cost': '£1,200',
            'severity': 'moderate',
            'componentCount': 38,
            'rawCost': 1200,
            'damageDetails': {
                'damage_percentage': 25,
                'repair_priority': 'Medium'
            }
        },
        # ... other sections
    ],
    'estimated_repair_cost': '£7,380',
    'assessment_progress': 85
}
```

### Template Display Logic

The template uses Django template tags to display costs:

```html
<!-- Section Cost Display -->
<p class="text-lg font-bold">{{ section.cost }}</p>

<!-- Cost Indicator with Conditional Styling -->
{% if section.rawCost < 500 %}
<span class="text-green-600 bg-green-50">Low Cost</span>
{% elif section.rawCost < 2000 %}
<span class="text-yellow-600 bg-yellow-50">Moderate Cost</span>
{% else %}
<span class="text-red-600 bg-red-50">High Cost</span>
{% endif %}

<!-- Detailed Cost Breakdown -->
<div class="flex justify-between">
    <span>Parts & Materials:</span>
    <span>£{{ section_data.parts_cost|floatformat:0 }}</span>
</div>
<div class="flex justify-between">
    <span>Labor (70%):</span>
    <span>£{{ section_data.labor_cost|floatformat:0 }}</span>
</div>
```

## Cost Structure Examples

### Example 1: Minor Exterior Damage

```
Vehicle: 2020 BMW 3 Series
Damage: Light scratches on hood and front bumper

Calculation:
- Hood (light damage): £250 × 1.5 multiplier = £375
- Front bumper (light damage): £250 × 1.2 multiplier = £300
- Parts subtotal: £675
- Labor (70%): £472.50
- Section total: £1,147.50
```

### Example 2: Major Mechanical Failure

```
Vehicle: 2018 Ford Focus
Damage: Engine block failure

Calculation:
- Engine block (failed): £2,200 × 3.0 multiplier = £6,600
- Parts subtotal: £6,600
- Labor (70%): £4,620
- Section total: £11,220
```

### Example 3: Complete Assessment

```
Vehicle: 2019 Toyota Camry
Multiple sections damaged

Section Breakdown:
- Exterior: £2,040
- Mechanical: £1,500
- Safety: £800
- Interior: £600

Subtotal: £4,940
Paint & Materials (15%): £741
Shop Supplies (8%): £395
Total before VAT: £6,076
VAT (20%): £1,215
Grand Total: £7,291
```

## API Reference

### Key Methods

#### `calculate_section_cost(section_obj, section_type)`
Calculates repair cost for a specific vehicle section.

**Parameters:**
- `section_obj`: Assessment section object
- `section_type`: String identifier for section type

**Returns:** Float representing section repair cost

#### `calculate_detailed_cost_breakdown(assessment)`
Generates comprehensive cost breakdown including labor, materials, and taxes.

**Parameters:**
- `assessment`: VehicleAssessment object

**Returns:** Dictionary with detailed cost structure

#### `calculate_settlement_details(assessment)`
Calculates settlement information including total loss determination.

**Parameters:**
- `assessment`: VehicleAssessment object

**Returns:** Dictionary with settlement details and recommendations

### Data Models

#### Section Cost Structure
```python
{
    'parts_cost': float,
    'labor_cost': float,
    'total_cost': float,
    'severity': string
}
```

#### Settlement Details Structure
```python
{
    'repair_cost': float,
    'market_value': float,
    'depreciation_amount': float,
    'deductible': float,
    'is_total_loss': boolean,
    'settlement_amount': float,
    'recommendation': string
}
```

## Configuration

### Customizing Base Costs

Base costs can be adjusted in the `calculate_section_cost` method:

```python
# Update base costs for inflation or market changes
base_costs['exterior']['moderate'] = 700  # Increase from £650
```

### Adjusting Labor Rates

Labor percentage can be modified per section or globally:

```python
# Global labor rate adjustment
labor_rate = 0.75  # Increase from 70% to 75%
labor_cost = parts_cost * labor_rate
```

### Modifying Additional Cost Percentages

```python
# Adjust additional cost percentages
paint_materials = total_parts_cost * 0.18  # Increase from 15% to 18%
shop_supplies = total_parts_cost * 0.10    # Increase from 8% to 10%
```

## Best Practices

1. **Regular Cost Updates**: Review and update base costs quarterly to reflect market changes
2. **Component Validation**: Ensure all vehicle components are properly mapped to cost categories
3. **Labor Rate Monitoring**: Monitor regional labor rates and adjust percentages accordingly
4. **Settlement Threshold Review**: Periodically review total loss thresholds based on market conditions
5. **Audit Trail**: Maintain detailed logs of cost calculations for audit purposes

## Troubleshooting

### Common Issues

1. **Zero Cost Calculations**: Check that section objects exist and have valid damage assessments
2. **Incorrect Multipliers**: Verify component names match multiplier dictionary keys
3. **Settlement Calculation Errors**: Ensure vehicle market value and repair costs are properly set
4. **Template Display Issues**: Confirm cost data is properly formatted in the view context

### Debugging Tips

```python
# Add logging to track cost calculations
import logging
logger = logging.getLogger(__name__)

def calculate_section_cost(self, section_obj, section_type):
    logger.info(f"Calculating costs for {section_type} section")
    # ... calculation logic
    logger.info(f"Total cost for {section_type}: £{total_cost}")
    return total_cost
```

---

*Last updated: December 2024*
*Version: 1.0*