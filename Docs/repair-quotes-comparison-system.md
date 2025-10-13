# Repair Quotes Comparison System

## Overview

The repair quotes comparison system provides multiple repair estimates from different sources to help insurance assessors and customers make informed decisions about vehicle repairs. The system generates realistic quote variations based on the primary assessment estimate and displays them in an easy-to-compare format.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Quote Generation Logic](#quote-generation-logic)
3. [Quote Sources and Types](#quote-sources-and-types)
4. [Pricing Algorithms](#pricing-algorithms)
5. [Frontend Display](#frontend-display)
6. [Integration with Cost Calculation](#integration-with-cost-calculation)
7. [Configuration and Customization](#configuration-and-customization)
8. [API Reference](#api-reference)

## System Architecture

The repair quotes comparison system is implemented in the `generate_repair_quote_comparisons()` method within `insurance_app/views.py`. The system:

- Takes the primary assessment estimate as a baseline
- Generates realistic variations based on different repair source types
- Applies market-based pricing adjustments
- Returns structured quote data for frontend display

## Quote Generation Logic

### Base Quote Calculation

The system starts with the primary assessment estimate and generates variations:

```python
def generate_repair_quote_comparisons(self, assessment):
    base_cost = float(assessment.estimated_repair_cost or 0)
    if base_cost == 0:
        return []
    
    # Generate realistic quote variations
    quotes = [...]
    return quotes
```

### Quote Variation Factors

Different repair sources have characteristic pricing patterns:

- **Authorized Dealers**: Typically 25% higher (OEM parts, certified technicians)
- **Independent Garages**: Typically 15% lower (aftermarket parts, competitive pricing)
- **Insurance Networks**: Typically 8% lower (pre-negotiated rates)
- **Market Average**: Typically 8% higher (regional market data)

## Quote Sources and Types

### 1. Assessor Estimate (Primary)
```python
{
    'source': 'Assessor Estimate',
    'provider': f'{assessment.assessor_name}',
    'amount': base_cost,
    'type': 'primary',
    'confidence': 'High',
    'notes': 'Professional assessment based on inspection'
}
```

### 2. Authorized Dealer
```python
{
    'source': 'Authorized Dealer',
    'provider': f'{assessment.vehicle.make} Main Dealer',
    'amount': base_cost * 1.25,  # 25% higher
    'type': 'dealer',
    'confidence': 'High',
    'notes': 'OEM parts and certified technicians'
}
```

### 3. Independent Garage
```python
{
    'source': 'Independent Garage',
    'provider': 'Local Certified Garage',
    'amount': base_cost * 0.85,  # 15% lower
    'type': 'independent',
    'confidence': 'Medium',
    'notes': 'Aftermarket parts, competitive pricing'
}
```

### 4. Insurance Network
```python
{
    'source': 'Insurance Network',
    'provider': 'Preferred Repair Network',
    'amount': base_cost * 0.92,  # 8% lower
    'type': 'network',
    'confidence': 'High',
    'notes': 'Pre-negotiated rates, guaranteed work'
}
```

### 5. Market Average
```python
{
    'source': 'Market Average',
    'provider': 'Regional Market Data',
    'amount': base_cost * 1.08,  # 8% higher
    'type': 'market',
    'confidence': 'Medium',
    'notes': 'Based on regional repair cost data'
}
```

## Pricing Algorithms

### Dealer Premium Calculation
Authorized dealers typically charge premium rates due to:
- OEM (Original Equipment Manufacturer) parts
- Factory-certified technicians
- Warranty coverage
- Brand reputation

```python
dealer_multiplier = 1.25  # 25% premium
dealer_quote = base_cost * dealer_multiplier
```

### Independent Garage Discount
Independent garages offer competitive pricing through:
- Aftermarket parts usage
- Lower overhead costs
- Competitive market positioning

```python
independent_multiplier = 0.85  # 15% discount
independent_quote = base_cost * independent_multiplier
```

### Insurance Network Rates
Insurance networks provide balanced pricing with:
- Pre-negotiated repair rates
- Quality guarantees
- Streamlined claim processing

```python
network_multiplier = 0.92  # 8% discount
network_quote = base_cost * network_multiplier
```

### Market Average Calculation
Market averages reflect regional pricing trends:
- Local labor rates
- Parts availability
- Market competition

```python
market_multiplier = 1.08  # 8% above base
market_quote = base_cost * market_multiplier
```

## Frontend Display

### Quote Comparison Table

The frontend displays quotes in a structured comparison format:

```html
<div class="space-y-3">
  {% for quote in repair_quotes %}
  <div class="border border-gray-200 rounded-lg p-3 
    {% if quote.type == 'primary' %}bg-blue-50 border-blue-200{% endif %}">
    
    <!-- Quote Header -->
    <div class="flex items-center justify-between mb-2">
      <div>
        <p class="font-medium text-sm">{{ quote.source }}</p>
        <p class="text-xs text-gray-500">{{ quote.provider }}</p>
      </div>
      
      <!-- Quote Amount with Styling -->
      <div class="text-right">
        <p class="font-bold text-lg 
          {% if quote.type == 'primary' %}text-blue-600
          {% elif quote.amount < assessment.estimated_repair_cost %}text-green-600
          {% else %}text-gray-900{% endif %}">
          £{{ quote.amount|floatformat:0 }}
        </p>
        
        <!-- Confidence and Variance Indicators -->
        <div class="flex items-center space-x-2">
          <span class="text-xs px-2 py-1 rounded-full 
            {% if quote.confidence == 'High' %}bg-green-100 text-green-700
            {% elif quote.confidence == 'Medium' %}bg-yellow-100 text-yellow-700
            {% else %}bg-gray-100 text-gray-700{% endif %}">
            {{ quote.confidence }}
          </span>
          
          <!-- Price Variance Display -->
          {% if quote.amount < assessment.estimated_repair_cost %}
          <span class="text-xs text-green-600 font-medium">
            -£{{ assessment.estimated_repair_cost|sub:quote.amount|floatformat:0 }}
          </span>
          {% elif quote.amount > assessment.estimated_repair_cost %}
          <span class="text-xs text-red-600 font-medium">
            +£{{ quote.amount|sub:assessment.estimated_repair_cost|floatformat:0 }}
          </span>
          {% endif %}
        </div>
      </div>
    </div>
    
    <!-- Quote Notes -->
    <p class="text-xs text-gray-600">{{ quote.notes }}</p>
  </div>
  {% endfor %}
</div>
```

### Quote Statistics Summary

The system displays statistical analysis of quotes:

```html
<div class="mt-4 pt-3 border-t border-gray-200">
  <div class="grid grid-cols-3 gap-4 text-center text-xs">
    {% with min_quote=repair_quotes|min_by:'amount' avg_amount=repair_quotes|avg:'amount' max_quote=repair_quotes|max_by:'amount' %}
    
    <!-- Lowest Quote -->
    <div>
      <p class="text-gray-500">Lowest Quote</p>
      <p class="font-medium text-green-600">
        £{{ min_quote.amount|floatformat:0 }}
      </p>
    </div>
    
    <!-- Average Quote -->
    <div>
      <p class="text-gray-500">Average Quote</p>
      <p class="font-medium">
        £{{ avg_amount|floatformat:0 }}
      </p>
    </div>
    
    <!-- Highest Quote -->
    <div>
      <p class="text-gray-500">Highest Quote</p>
      <p class="font-medium text-red-600">
        £{{ max_quote.amount|floatformat:0 }}
      </p>
    </div>
    
    {% endwith %}
  </div>
</div>
```

## Integration with Cost Calculation

### Data Flow

1. **Assessment Completion**: Primary repair cost calculated using section-based system
2. **Quote Generation**: Multiple quotes generated based on primary estimate
3. **Statistical Analysis**: Min, max, and average calculations performed
4. **Frontend Display**: Structured quote comparison presented to user

### Context Data Structure

```python
context.update({
    'repair_quotes': [
        {
            'source': 'Assessor Estimate',
            'provider': 'John Smith',
            'amount': 5000.00,
            'type': 'primary',
            'confidence': 'High',
            'notes': 'Professional assessment based on inspection'
        },
        # ... additional quotes
    ],
    'quote_statistics': {
        'min_quote': 4250.00,
        'max_quote': 6250.00,
        'avg_quote': 5100.00,
        'variance_range': 2000.00
    }
})
```

## Configuration and Customization

### Adjusting Quote Multipliers

Quote multipliers can be customized based on regional market conditions:

```python
# Regional multiplier adjustments
QUOTE_MULTIPLIERS = {
    'dealer': 1.25,      # Can adjust based on local dealer pricing
    'independent': 0.85,  # Can adjust based on local competition
    'network': 0.92,     # Can adjust based on network agreements
    'market': 1.08       # Can adjust based on regional data
}

# Apply regional adjustments
dealer_quote = base_cost * QUOTE_MULTIPLIERS['dealer']
```

### Adding Custom Quote Sources

New quote sources can be added to the system:

```python
def generate_repair_quote_comparisons(self, assessment):
    base_cost = float(assessment.estimated_repair_cost or 0)
    
    quotes = [
        # ... existing quotes
        
        # Custom quote source
        {
            'source': 'Mobile Repair Service',
            'provider': 'On-Site Repair Specialists',
            'amount': base_cost * 0.90,  # 10% discount
            'type': 'mobile',
            'confidence': 'Medium',
            'notes': 'Convenient on-site repairs, limited to minor damage'
        }
    ]
    
    return quotes
```

### Confidence Level Calculation

Confidence levels can be calculated based on various factors:

```python
def calculate_quote_confidence(quote_type, damage_severity, repair_complexity):
    base_confidence = {
        'primary': 'High',
        'dealer': 'High',
        'independent': 'Medium',
        'network': 'High',
        'market': 'Medium'
    }
    
    # Adjust confidence based on damage complexity
    if damage_severity in ['severe', 'total_loss']:
        if quote_type == 'independent':
            return 'Low'  # Independent shops may struggle with complex repairs
    
    return base_confidence.get(quote_type, 'Medium')
```

## API Reference

### Main Methods

#### `generate_repair_quote_comparisons(assessment)`

Generates multiple repair quotes for comparison.

**Parameters:**
- `assessment`: VehicleAssessment object with estimated repair cost

**Returns:** List of quote dictionaries

**Example Usage:**
```python
quotes = self.generate_repair_quote_comparisons(assessment)
```

#### Quote Object Structure

```python
{
    'source': str,        # Quote source name
    'provider': str,      # Provider/company name
    'amount': float,      # Quote amount in currency
    'type': str,          # Quote type identifier
    'confidence': str,    # Confidence level (High/Medium/Low)
    'notes': str          # Additional information
}
```

### Template Filters and Tags

#### Custom Template Filters

```python
# In templatetags/insurance_filters.py

@register.filter
def min_by(queryset, field):
    """Get object with minimum value for specified field"""
    return min(queryset, key=lambda x: getattr(x, field, 0))

@register.filter
def max_by(queryset, field):
    """Get object with maximum value for specified field"""
    return max(queryset, key=lambda x: getattr(x, field, 0))

@register.filter
def avg(queryset, field):
    """Calculate average value for specified field"""
    values = [getattr(x, field, 0) for x in queryset]
    return sum(values) / len(values) if values else 0
```

## Best Practices

### 1. Regular Market Analysis
- Monitor regional repair costs quarterly
- Update multipliers based on market trends
- Validate quotes against actual repair invoices

### 2. Quality Assurance
- Implement quote validation rules
- Set reasonable variance limits
- Flag unusual quote variations for review

### 3. User Experience
- Clearly explain quote differences
- Provide context for price variations
- Highlight recommended options

### 4. Data Accuracy
- Validate base cost calculations
- Ensure quote multipliers reflect reality
- Maintain audit trail of quote generations

## Troubleshooting

### Common Issues

1. **Missing Quotes**: Ensure base cost is greater than zero
2. **Incorrect Multipliers**: Verify multiplier values are reasonable
3. **Display Issues**: Check template filter implementations
4. **Statistical Errors**: Validate quote list is not empty

### Debugging Examples

```python
# Debug quote generation
def generate_repair_quote_comparisons(self, assessment):
    base_cost = float(assessment.estimated_repair_cost or 0)
    
    # Add logging
    logger.info(f"Generating quotes for base cost: £{base_cost}")
    
    if base_cost == 0:
        logger.warning("Base cost is zero, no quotes generated")
        return []
    
    quotes = []
    # ... quote generation logic
    
    logger.info(f"Generated {len(quotes)} quotes")
    return quotes
```

### Performance Considerations

- Cache quote calculations for repeated requests
- Limit number of quote sources to prevent UI clutter
- Optimize template rendering for large quote lists

---

*Last updated: December 2024*
*Version: 1.0*