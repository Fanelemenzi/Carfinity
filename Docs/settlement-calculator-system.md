# Settlement Calculator System

## Overview

The settlement calculator system determines whether a vehicle should be repaired or declared a total loss, and calculates the appropriate settlement amount. The system considers multiple factors including market value, vehicle age, repair costs, depreciation, policy deductibles, and salvage value to provide accurate settlement recommendations.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Total Loss Determination](#total-loss-determination)
3. [Market Value Assessment](#market-value-assessment)
4. [Vehicle Age and Depreciation](#vehicle-age-and-depreciation)
5. [Repair Cost Analysis](#repair-cost-analysis)
6. [Policy Deductible Calculation](#policy-deductible-calculation)
7. [Salvage Value Assessment](#salvage-value-assessment)
8. [Settlement Amount Calculation](#settlement-amount-calculation)
9. [Frontend Integration](#frontend-integration)
10. [Configuration and Customization](#configuration-and-customization)
11. [API Reference](#api-reference)

## System Architecture

The settlement calculator is implemented in the `calculate_settlement_details()` method within `insurance_app/views.py`. The system follows this workflow:

1. **Input Validation**: Verify required data (repair cost, market value)
2. **Total Loss Check**: Compare repair cost to total loss threshold
3. **Depreciation Calculation**: Calculate age and damage-based depreciation
4. **Settlement Determination**: Calculate final settlement amount
5. **Recommendation Generation**: Provide repair vs. total loss recommendation

```python
def calculate_settlement_details(self, assessment):
    """Calculate detailed settlement information with depreciation and deductibles"""
    if not assessment.estimated_repair_cost or not assessment.vehicle_market_value:
        return None
    
    # Extract base values
    repair_cost = float(assessment.estimated_repair_cost)
    market_value = float(assessment.vehicle_market_value)
    salvage_value = float(assessment.salvage_value or 0)
    
    # Perform calculations...
    return settlement_details
```

## Total Loss Determination

### Threshold Calculation

The system uses a **70% threshold** to determine total loss status:

```python
total_loss_threshold = market_value * 0.70
is_total_loss = repair_cost > total_loss_threshold
```

### Industry Standards

- **70% Rule**: Most insurers declare total loss when repair costs exceed 70% of vehicle's actual cash value
- **Regulatory Compliance**: Threshold may vary by jurisdiction (65-80% range)
- **Economic Viability**: Considers cost-effectiveness of repairs vs. replacement

### Total Loss Logic Flow

```python
if repair_cost > (market_value * 0.70):
    # Vehicle is total loss
    settlement_type = "Total Loss Settlement"
    calculation_method = "market_value_based"
else:
    # Vehicle is repairable
    settlement_type = "Repair Settlement"
    calculation_method = "repair_cost_based"
```

## Market Value Assessment

### Market Value Sources

The system uses multiple data sources to determine vehicle market value:

1. **Industry Valuation Tools**
   - Kelley Blue Book (KBB)
   - Edmunds
   - AutoTrader market data
   - NADA Guides

2. **Regional Market Factors**
   - Local supply and demand
   - Regional price variations
   - Seasonal adjustments
   - Economic conditions

3. **Vehicle-Specific Factors**
   - Mileage adjustments
   - Condition assessments
   - Optional equipment value
   - Maintenance history impact

### Market Value Calculation

```python
def calculate_market_value(vehicle):
    """Calculate current market value based on multiple factors"""
    
    # Base value from industry sources
    base_value = get_industry_valuation(vehicle)
    
    # Mileage adjustment
    mileage_factor = calculate_mileage_adjustment(vehicle.mileage, vehicle.year)
    
    # Condition adjustment
    condition_factor = get_condition_multiplier(vehicle.condition)
    
    # Regional adjustment
    regional_factor = get_regional_multiplier(vehicle.location)
    
    # Calculate final market value
    market_value = base_value * mileage_factor * condition_factor * regional_factor
    
    return market_value
```

### Market Value Validation

```python
# Validate market value against reasonable ranges
def validate_market_value(vehicle, calculated_value):
    # Check against MSRP depreciation curves
    expected_range = calculate_expected_value_range(vehicle)
    
    if calculated_value < expected_range['min']:
        return expected_range['min']
    elif calculated_value > expected_range['max']:
        return expected_range['max']
    
    return calculated_value
```

## Vehicle Age and Depreciation

### Age-Based Depreciation Calculation

The system calculates depreciation based on vehicle age with diminishing returns:

```python
# Calculate vehicle age
vehicle_age = timezone.now().year - assessment.vehicle.manufacture_year

# Age-based depreciation: 2% per year, maximum 15%
age_depreciation_rate = min(0.15, 0.02 * vehicle_age)
```

### Depreciation Schedule

| Vehicle Age | Annual Depreciation | Cumulative Max |
|-------------|-------------------|----------------|
| 1-2 years   | 2% per year       | 4%            |
| 3-5 years   | 2% per year       | 10%           |
| 6-7 years   | 2% per year       | 14%           |
| 8+ years    | Capped at 15%     | 15%           |

### Damage-Based Depreciation

Additional depreciation based on damage severity:

```python
severity_depreciation = {
    'cosmetic': 0.02,      # 2% - Minor cosmetic damage
    'minor': 0.03,         # 3% - Minor functional damage
    'moderate': 0.05,      # 5% - Moderate damage requiring repair
    'major': 0.08,         # 8% - Major structural/mechanical damage
    'total_loss': 0.15     # 15% - Severe damage beyond economic repair
}

damage_depreciation = severity_depreciation.get(assessment.overall_severity, 0.05)
```

### Combined Depreciation Calculation

```python
# Total depreciation combines age and damage factors
total_depreciation_rate = age_depreciation_rate + damage_depreciation
depreciation_amount = market_value * total_depreciation_rate

# Apply maximum depreciation cap (typically 25-30%)
max_depreciation_rate = 0.25
if total_depreciation_rate > max_depreciation_rate:
    total_depreciation_rate = max_depreciation_rate
    depreciation_amount = market_value * max_depreciation_rate
```

### Depreciation Examples

#### Example 1: 3-Year-Old Vehicle with Minor Damage
```
Vehicle: 2021 Honda Civic
Market Value: £18,000
Age: 3 years
Damage: Minor

Calculations:
- Age Depreciation: 3 × 2% = 6%
- Damage Depreciation: 3% (minor)
- Total Depreciation: 9%
- Depreciation Amount: £18,000 × 9% = £1,620
```

#### Example 2: 8-Year-Old Vehicle with Major Damage
```
Vehicle: 2016 Ford Focus
Market Value: £8,000
Age: 8 years
Damage: Major

Calculations:
- Age Depreciation: 15% (capped)
- Damage Depreciation: 8% (major)
- Total Depreciation: 23%
- Depreciation Amount: £8,000 × 23% = £1,840
```

## Repair Cost Analysis

### Repair Cost Components

The system analyzes repair costs from the detailed cost breakdown:

```python
def analyze_repair_costs(assessment):
    """Analyze repair cost components for settlement calculation"""
    
    repair_breakdown = {
        'parts_cost': 0,
        'labor_cost': 0,
        'paint_materials': 0,
        'shop_supplies': 0,
        'tax': 0,
        'total_cost': 0
    }
    
    # Get detailed cost breakdown
    detailed_costs = calculate_detailed_cost_breakdown(assessment)
    
    # Extract components
    repair_breakdown['parts_cost'] = sum(
        section['parts_cost'] for section in detailed_costs['section_costs'].values()
    )
    repair_breakdown['labor_cost'] = sum(
        section['labor_cost'] for section in detailed_costs['section_costs'].values()
    )
    repair_breakdown['paint_materials'] = detailed_costs['paint_materials']
    repair_breakdown['shop_supplies'] = detailed_costs['shop_supplies']
    repair_breakdown['tax'] = detailed_costs['vat']
    repair_breakdown['total_cost'] = detailed_costs['grand_total']
    
    return repair_breakdown
```

### Repair Cost Validation

```python
def validate_repair_costs(repair_cost, market_value):
    """Validate repair costs against market value"""
    
    # Check for unreasonable repair costs
    if repair_cost > market_value * 1.5:
        # Repair cost exceeds 150% of market value - likely total loss
        return {
            'valid': False,
            'reason': 'Repair cost exceeds reasonable threshold',
            'recommendation': 'total_loss'
        }
    
    if repair_cost < market_value * 0.05:
        # Very low repair cost - verify assessment completeness
        return {
            'valid': True,
            'reason': 'Low repair cost - verify assessment',
            'recommendation': 'repair'
        }
    
    return {'valid': True, 'reason': 'Repair cost within normal range'}
```

## Policy Deductible Calculation

### Deductible Sources

The system retrieves deductible information from multiple sources:

1. **Policy Database**: Primary source from insurance policy
2. **Default Values**: Fallback deductible amounts
3. **Coverage Type**: Different deductibles for different coverage types

```python
def get_policy_deductible(assessment):
    """Get policy deductible from various sources"""
    
    # Try to get from policy relationship
    try:
        if hasattr(assessment.vehicle, 'policy') and assessment.vehicle.policy:
            policy = assessment.vehicle.policy
            
            # Check for collision deductible
            if hasattr(policy, 'collision_deductible'):
                return float(policy.collision_deductible)
            
            # Check for comprehensive deductible
            if hasattr(policy, 'comprehensive_deductible'):
                return float(policy.comprehensive_deductible)
            
            # Check for general deductible
            if hasattr(policy, 'deductible'):
                return float(policy.deductible)
                
    except (AttributeError, ValueError, TypeError):
        pass
    
    # Fallback to default deductible
    return 500.0  # Default £500 deductible
```

### Deductible Types and Amounts

| Coverage Type | Typical Deductible Range | Default Amount |
|---------------|-------------------------|----------------|
| Collision     | £250 - £1,000          | £500          |
| Comprehensive | £100 - £500            | £250          |
| Uninsured Motorist | £250 - £500       | £300          |
| Glass Coverage | £0 - £100             | £50           |

### Deductible Application Logic

```python
def apply_deductible(settlement_amount, deductible, settlement_type):
    """Apply deductible to settlement amount"""
    
    if settlement_type == 'total_loss':
        # For total loss, deductible reduces settlement
        final_settlement = max(0, settlement_amount - deductible)
    else:
        # For repairs, deductible reduces repair payment
        final_settlement = max(0, settlement_amount - deductible)
    
    return {
        'gross_settlement': settlement_amount,
        'deductible_applied': min(deductible, settlement_amount),
        'net_settlement': final_settlement
    }
```

## Salvage Value Assessment

### Salvage Value Calculation

Salvage value represents the worth of a total loss vehicle sold for parts or scrap:

```python
def calculate_salvage_value(vehicle, market_value, damage_severity):
    """Calculate salvage value based on vehicle condition and market factors"""
    
    # Base salvage percentages by damage severity
    salvage_percentages = {
        'minor': 0.75,      # 75% of market value
        'moderate': 0.60,   # 60% of market value
        'major': 0.40,      # 40% of market value
        'severe': 0.25,     # 25% of market value
        'total_loss': 0.15  # 15% of market value
    }
    
    # Get base salvage percentage
    base_percentage = salvage_percentages.get(damage_severity, 0.40)
    
    # Adjust for vehicle factors
    age_factor = calculate_age_factor(vehicle.year)
    mileage_factor = calculate_mileage_factor(vehicle.mileage)
    condition_factor = calculate_condition_factor(vehicle.condition)
    
    # Calculate salvage value
    salvage_value = market_value * base_percentage * age_factor * mileage_factor * condition_factor
    
    # Apply minimum salvage value (scrap metal value)
    min_salvage = calculate_minimum_scrap_value(vehicle)
    
    return max(salvage_value, min_salvage)
```

### Salvage Value Factors

#### Age Factor
```python
def calculate_age_factor(vehicle_year):
    """Calculate age factor for salvage value"""
    current_year = timezone.now().year
    age = current_year - vehicle_year
    
    if age <= 3:
        return 1.0      # No age penalty for newer vehicles
    elif age <= 7:
        return 0.9      # 10% reduction for mid-age vehicles
    elif age <= 12:
        return 0.7      # 30% reduction for older vehicles
    else:
        return 0.5      # 50% reduction for very old vehicles
```

#### Mileage Factor
```python
def calculate_mileage_factor(mileage):
    """Calculate mileage factor for salvage value"""
    if mileage <= 50000:
        return 1.0      # No mileage penalty
    elif mileage <= 100000:
        return 0.9      # 10% reduction
    elif mileage <= 150000:
        return 0.8      # 20% reduction
    else:
        return 0.7      # 30% reduction for high mileage
```

### Salvage Value Examples

#### Example 1: Moderate Damage, Newer Vehicle
```
Vehicle: 2020 BMW 3 Series
Market Value: £25,000
Damage: Moderate
Age: 4 years
Mileage: 45,000

Calculations:
- Base Salvage: £25,000 × 60% = £15,000
- Age Factor: 0.9 (4 years old)
- Mileage Factor: 1.0 (low mileage)
- Final Salvage: £15,000 × 0.9 × 1.0 = £13,500
```

#### Example 2: Severe Damage, Older Vehicle
```
Vehicle: 2015 Ford Fiesta
Market Value: £6,000
Damage: Severe
Age: 9 years
Mileage: 120,000

Calculations:
- Base Salvage: £6,000 × 25% = £1,500
- Age Factor: 0.7 (9 years old)
- Mileage Factor: 0.8 (high mileage)
- Final Salvage: £1,500 × 0.7 × 0.8 = £840
```

## Settlement Amount Calculation

### Total Loss Settlement

For vehicles declared total loss:

```python
def calculate_total_loss_settlement(market_value, depreciation_amount, deductible, salvage_value):
    """Calculate total loss settlement amount"""
    
    # Start with market value
    settlement_base = market_value
    
    # Subtract depreciation
    settlement_after_depreciation = settlement_base - depreciation_amount
    
    # Subtract deductible
    settlement_after_deductible = settlement_after_depreciation - deductible
    
    # Add salvage value (if customer keeps vehicle)
    # Note: Salvage value is typically retained by insurer
    final_settlement = settlement_after_deductible
    
    return {
        'settlement_type': 'Total Loss',
        'market_value': market_value,
        'depreciation': depreciation_amount,
        'deductible': deductible,
        'salvage_value': salvage_value,
        'gross_settlement': settlement_after_depreciation,
        'net_settlement': max(0, final_settlement),
        'calculation_method': 'ACV - Depreciation - Deductible'
    }
```

### Repair Settlement

For repairable vehicles:

```python
def calculate_repair_settlement(repair_cost, deductible):
    """Calculate repair settlement amount"""
    
    # Repair settlement is repair cost minus deductible
    net_settlement = max(0, repair_cost - deductible)
    
    return {
        'settlement_type': 'Repair',
        'repair_cost': repair_cost,
        'deductible': deductible,
        'gross_settlement': repair_cost,
        'net_settlement': net_settlement,
        'calculation_method': 'Repair Cost - Deductible'
    }
```

### Complete Settlement Calculation

```python
def calculate_settlement_details(self, assessment):
    """Calculate complete settlement details"""
    
    # Extract base values
    repair_cost = float(assessment.estimated_repair_cost)
    market_value = float(assessment.vehicle_market_value)
    salvage_value = float(assessment.salvage_value or 0)
    
    # Calculate depreciation
    vehicle_age = timezone.now().year - assessment.vehicle.manufacture_year
    age_depreciation_rate = min(0.15, 0.02 * vehicle_age)
    
    severity_depreciation = {
        'cosmetic': 0.02, 'minor': 0.03, 'moderate': 0.05,
        'major': 0.08, 'total_loss': 0.15
    }
    damage_depreciation = severity_depreciation.get(assessment.overall_severity, 0.05)
    
    total_depreciation_rate = age_depreciation_rate + damage_depreciation
    depreciation_amount = market_value * total_depreciation_rate
    
    # Get deductible
    deductible = get_policy_deductible(assessment)
    
    # Determine total loss status
    total_loss_threshold = market_value * 0.70
    is_total_loss = repair_cost > total_loss_threshold
    
    # Calculate settlement
    if is_total_loss:
        settlement_amount = market_value - depreciation_amount - deductible
        if salvage_value > 0:
            settlement_amount += salvage_value
        recommendation = 'Total Loss Settlement'
    else:
        settlement_amount = repair_cost - deductible
        recommendation = 'Repair Settlement'
    
    return {
        'repair_cost': repair_cost,
        'market_value': market_value,
        'salvage_value': salvage_value,
        'vehicle_age': vehicle_age,
        'age_depreciation_rate': age_depreciation_rate,
        'damage_depreciation_rate': damage_depreciation,
        'total_depreciation_rate': total_depreciation_rate,
        'depreciation_amount': depreciation_amount,
        'deductible': deductible,
        'total_loss_threshold': total_loss_threshold,
        'is_total_loss': is_total_loss,
        'settlement_amount': max(0, settlement_amount),
        'recommendation': recommendation
    }
```

## Frontend Integration

### Settlement Display Template

The frontend displays settlement calculations in a structured format:

```html
<!-- Settlement Calculator Panel -->
<div class="bg-white rounded-2xl p-4 shadow-sm sticky top-6">
  <h3 class="text-lg font-semibold mb-3">Settlement Calculator</h3>
  
  {% if settlement_details %}
  <div class="space-y-3 text-sm">
    
    <!-- Vehicle Information -->
    <div class="bg-gray-50 rounded-lg p-3">
      <div class="flex items-center justify-between mb-1">
        <span class="text-xs text-gray-500">Vehicle Market Value</span>
        <span class="font-medium">£{{ settlement_details.market_value|floatformat:0 }}</span>
      </div>
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-500">Vehicle Age</span>
        <span class="text-xs">{{ settlement_details.vehicle_age }} years</span>
      </div>
    </div>
    
    <!-- Repair Cost -->
    <div class="flex items-center justify-between">
      <span>Repair Cost</span>
      <span class="font-medium">£{{ settlement_details.repair_cost|floatformat:0 }}</span>
    </div>
    
    <!-- Depreciation Breakdown -->
    <div class="bg-yellow-50 rounded-lg p-3">
      <p class="text-xs font-medium text-yellow-800 mb-2">Depreciation Factors</p>
      <div class="space-y-1 text-xs">
        <div class="flex justify-between">
          <span>Age Depreciation ({{ settlement_details.age_depreciation_rate|mul:100|floatformat:1 }}%):</span>
          <span class="text-red-600">-£{{ settlement_details.market_value|mul:settlement_details.age_depreciation_rate|floatformat:0 }}</span>
        </div>
        <div class="flex justify-between">
          <span>Damage Depreciation ({{ settlement_details.damage_depreciation_rate|mul:100|floatformat:1 }}%):</span>
          <span class="text-red-600">-£{{ settlement_details.market_value|mul:settlement_details.damage_depreciation_rate|floatformat:0 }}</span>
        </div>
        <div class="flex justify-between border-t pt-1 font-medium">
          <span>Total Depreciation:</span>
          <span class="text-red-600">-£{{ settlement_details.depreciation_amount|floatformat:0 }}</span>
        </div>
      </div>
    </div>
    
    <!-- Policy Deductible -->
    <div class="flex items-center justify-between">
      <span>Policy Deductible</span>
      <span class="text-red-600">-£{{ settlement_details.deductible|floatformat:0 }}</span>
    </div>
    
    <!-- Salvage Value (if applicable) -->
    {% if settlement_details.salvage_value > 0 %}
    <div class="flex items-center justify-between">
      <span>Salvage Value</span>
      <span class="text-green-600">+£{{ settlement_details.salvage_value|floatformat:0 }}</span>
    </div>
    {% endif %}
    
    <!-- Total Loss Check -->
    <div class="{% if settlement_details.is_total_loss %}bg-red-50 border border-red-200{% else %}bg-green-50 border border-green-200{% endif %} rounded-lg p-3">
      <p class="text-xs font-medium mb-1 {% if settlement_details.is_total_loss %}text-red-600{% else %}text-green-600{% endif %}">
        {% if settlement_details.is_total_loss %}TOTAL LOSS THRESHOLD EXCEEDED{% else %}REPAIR ECONOMICALLY VIABLE{% endif %}
      </p>
      <p class="text-xs {% if settlement_details.is_total_loss %}text-red-700{% else %}text-green-700{% endif %}">
        Repair cost (£{{ settlement_details.repair_cost|floatformat:0 }}) 
        {% if settlement_details.is_total_loss %}exceeds{% else %}is below{% endif %} 
        70% threshold (£{{ settlement_details.total_loss_threshold|floatformat:0 }})
      </p>
    </div>
    
    <!-- Settlement Amount -->
    <div class="border-t pt-3 mt-3">
      <div class="flex items-center justify-between">
        <span class="font-semibold">{{ settlement_details.recommendation }}</span>
        <span class="text-xl font-extrabold {% if settlement_details.is_total_loss %}text-red-600{% else %}text-green-600{% endif %}">
          £{{ settlement_details.settlement_amount|floatformat:0 }}
        </span>
      </div>
    </div>
    
    <!-- Settlement Recommendation -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
      <p class="text-xs text-blue-600 font-medium mb-1">RECOMMENDATION</p>
      <p class="text-xs text-blue-700">
        {% if settlement_details.is_total_loss %}
          Recommend total loss settlement. Vehicle repair cost exceeds economic threshold.
          {% if settlement_details.salvage_value > 0 %}
          Salvage value of £{{ settlement_details.salvage_value|floatformat:0 }} included in settlement.
          {% endif %}
        {% else %}
          Recommend repair settlement. Repair is economically viable and cost-effective.
        {% endif %}
      </p>
    </div>
    
  </div>
  {% endif %}
</div>
```

### Interactive Calculation Details

```html
<!-- Settlement Calculation Details -->
<div class="mt-3 pt-3 border-t border-gray-200">
  <button type="button" onclick="toggleCalculationDetails()" class="text-xs text-blue-600 hover:text-blue-800 font-medium">
    <i class="fas fa-calculator mr-1"></i>Show Calculation Details
  </button>
  <div id="calculationDetails" class="hidden mt-2 text-xs text-gray-600 bg-gray-50 rounded p-2">
    <p class="font-medium mb-1">Settlement Calculation:</p>
    {% if settlement_details.is_total_loss %}
    <p>Market Value: £{{ settlement_details.market_value|floatformat:0 }}</p>
    <p>- Total Depreciation: £{{ settlement_details.depreciation_amount|floatformat:0 }}</p>
    <p>- Policy Deductible: £{{ settlement_details.deductible|floatformat:0 }}</p>
    {% if settlement_details.salvage_value > 0 %}
    <p>+ Salvage Value: £{{ settlement_details.salvage_value|floatformat:0 }}</p>
    {% endif %}
    {% else %}
    <p>Repair Cost: £{{ settlement_details.repair_cost|floatformat:0 }}</p>
    <p>- Policy Deductible: £{{ settlement_details.deductible|floatformat:0 }}</p>
    {% endif %}
    <p class="font-medium border-t pt-1 mt-1">= Settlement: £{{ settlement_details.settlement_amount|floatformat:0 }}</p>
  </div>
</div>
```

## Configuration and Customization

### Adjusting Total Loss Threshold

```python
# Configuration settings
SETTLEMENT_CONFIG = {
    'total_loss_threshold': 0.70,  # 70% threshold
    'max_age_depreciation': 0.15,  # 15% maximum
    'age_depreciation_rate': 0.02, # 2% per year
    'default_deductible': 500.0,   # £500 default
    'min_salvage_percentage': 0.10 # 10% minimum salvage
}

# Apply configuration
total_loss_threshold = market_value * SETTLEMENT_CONFIG['total_loss_threshold']
```

### Regional Adjustments

```python
# Regional configuration
REGIONAL_ADJUSTMENTS = {
    'london': {
        'market_value_multiplier': 1.15,  # 15% higher in London
        'repair_cost_multiplier': 1.20,   # 20% higher repair costs
        'salvage_value_multiplier': 1.10   # 10% higher salvage value
    },
    'scotland': {
        'market_value_multiplier': 0.95,   # 5% lower in Scotland
        'repair_cost_multiplier': 0.90,    # 10% lower repair costs
        'salvage_value_multiplier': 0.85    # 15% lower salvage value
    }
}
```

### Custom Depreciation Schedules

```python
# Luxury vehicle depreciation schedule
LUXURY_DEPRECIATION = {
    'age_rates': {
        1: 0.20,  # 20% first year
        2: 0.15,  # 15% second year
        3: 0.10,  # 10% third year
        4: 0.08,  # 8% fourth year
        5: 0.05   # 5% thereafter
    },
    'damage_multipliers': {
        'cosmetic': 1.5,   # Higher impact on luxury vehicles
        'minor': 2.0,
        'moderate': 2.5,
        'major': 3.0,
        'total_loss': 3.5
    }
}
```

## API Reference

### Main Methods

#### `calculate_settlement_details(assessment)`

Calculates complete settlement information including total loss determination.

**Parameters:**
- `assessment`: VehicleAssessment object with required financial data

**Returns:** Dictionary with settlement details

**Example Usage:**
```python
settlement_info = self.calculate_settlement_details(assessment)
```

#### `get_policy_deductible(assessment)`

Retrieves policy deductible from various sources.

**Parameters:**
- `assessment`: VehicleAssessment object

**Returns:** Float representing deductible amount

#### `calculate_salvage_value(vehicle, market_value, damage_severity)`

Calculates salvage value based on vehicle and damage factors.

**Parameters:**
- `vehicle`: Vehicle object
- `market_value`: Float representing current market value
- `damage_severity`: String representing damage level

**Returns:** Float representing salvage value

### Data Structures

#### Settlement Details Object

```python
{
    'repair_cost': float,              # Total repair cost
    'market_value': float,             # Current market value
    'salvage_value': float,            # Salvage value if total loss
    'vehicle_age': int,                # Vehicle age in years
    'age_depreciation_rate': float,    # Age-based depreciation rate
    'damage_depreciation_rate': float, # Damage-based depreciation rate
    'total_depreciation_rate': float,  # Combined depreciation rate
    'depreciation_amount': float,      # Total depreciation amount
    'deductible': float,               # Policy deductible
    'total_loss_threshold': float,     # Total loss threshold amount
    'is_total_loss': bool,             # Total loss determination
    'settlement_amount': float,        # Final settlement amount
    'recommendation': str              # Settlement recommendation
}
```

#### Depreciation Breakdown Object

```python
{
    'age_component': {
        'rate': float,                 # Age depreciation rate
        'amount': float,               # Age depreciation amount
        'years': int                   # Vehicle age
    },
    'damage_component': {
        'rate': float,                 # Damage depreciation rate
        'amount': float,               # Damage depreciation amount
        'severity': str                # Damage severity level
    },
    'total': {
        'rate': float,                 # Total depreciation rate
        'amount': float,               # Total depreciation amount
        'capped': bool                 # Whether depreciation was capped
    }
}
```

## Best Practices

### 1. Data Validation
- Validate all input values before calculations
- Implement reasonable bounds checking
- Handle missing or invalid data gracefully

### 2. Audit Trail
- Log all settlement calculations
- Maintain detailed calculation breakdowns
- Track changes to settlement parameters

### 3. Regular Updates
- Review market value sources quarterly
- Update depreciation schedules annually
- Monitor total loss threshold effectiveness

### 4. Quality Assurance
- Implement calculation validation rules
- Cross-reference with industry standards
- Regular accuracy testing against actual settlements

## Troubleshooting

### Common Issues

1. **Missing Market Value**: Ensure vehicle market value is properly set
2. **Zero Settlement Amount**: Check deductible doesn't exceed settlement
3. **Incorrect Total Loss Determination**: Verify threshold calculations
4. **Depreciation Calculation Errors**: Validate age and severity inputs

### Debugging Examples

```python
# Debug settlement calculation
def calculate_settlement_details(self, assessment):
    logger.info(f"Starting settlement calculation for assessment {assessment.id}")
    
    # Validate inputs
    if not assessment.estimated_repair_cost:
        logger.error("Missing repair cost for settlement calculation")
        return None
    
    if not assessment.vehicle_market_value:
        logger.error("Missing market value for settlement calculation")
        return None
    
    # Log calculation steps
    repair_cost = float(assessment.estimated_repair_cost)
    market_value = float(assessment.vehicle_market_value)
    
    logger.info(f"Repair cost: £{repair_cost}, Market value: £{market_value}")
    
    # Continue with calculations...
    return settlement_details
```

### Performance Optimization

- Cache market value lookups
- Optimize depreciation calculations
- Minimize database queries in settlement logic

---

*Last updated: December 2024*
*Version: 1.0*