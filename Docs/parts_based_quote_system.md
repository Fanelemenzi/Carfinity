# Parts-Based Repair Quotation System

## Overview

The Parts-Based Repair Quotation System is an intelligent backend system that collects damaged parts from vehicle assessments across different sections, requests itemized repair quotations from four different provider types, calculates market averages for each part and overall repair, and recommends the best quote based on multiple factors including price, quality, and reliability.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Models](#data-models)
3. [Quote Collection Workflow](#quote-collection-workflow)
4. [Provider Types and Integration](#provider-types-and-integration)
5. [Market Average Calculation](#market-average-calculation)
6. [Quote Recommendation Engine](#quote-recommendation-engine)
7. [API Endpoints](#api-endpoints)
8. [Business Logic](#business-logic)
9. [Implementation Examples](#implementation-examples)
10. [Usage Scenarios](#usage-scenarios)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vehicle Assessment Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Front   │  │   Side   │  │   Rear   │  │  Roof    │       │
│  │ Section  │  │ Section  │  │ Section  │  │ Section  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
        ┌─────────────▼──────────────┐
        │  Damaged Parts Aggregator  │
        │  - Collect all damaged     │
        │  - Deduplicate parts       │
        │  - Create quote request    │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │   Quote Request Dispatcher │
        │  - Send to 4 providers     │
        │  - Track responses         │
        │  - Validate quotes         │
        └─────────────┬──────────────┘
                      │
    ┌─────────────────┼─────────────────┬─────────────────┐
    │                 │                 │                 │
┌───▼────┐    ┌──────▼─────┐    ┌──────▼────┐    ┌──────▼────┐
│Assessor│    │  Authorized│    │Independent│    │ Insurance │
│Estimate│    │   Dealer   │    │  Garage   │    │  Network  │
└───┬────┘    └──────┬─────┘    └──────┬────┘    └──────┬────┘
    │                │                 │                 │
    └────────────────┴─────────────────┴─────────────────┘
                     │
        ┌────────────▼───────────────┐
        │  Quote Analysis Engine     │
        │  - Calculate market avg    │
        │  - Compare part-by-part    │
        │  - Score providers         │
        └────────────┬───────────────┘
                     │
        ┌────────────▼───────────────┐
        │ Recommendation Engine      │
        │  - Best value analysis     │
        │  - Quality scoring         │
        │  - Generate recommendation │
        └────────────────────────────┘
```

### System Components

1. **Damaged Parts Aggregator**: Collects damaged parts from all vehicle sections
2. **Quote Request Dispatcher**: Manages quote requests to multiple providers
3. **Provider Interface Layer**: Handles communication with different provider types
4. **Quote Analysis Engine**: Calculates market averages and comparisons
5. **Recommendation Engine**: Determines best quote based on multiple criteria
6. **Data Persistence Layer**: Stores all quotes, calculations, and recommendations

---

## Data Models

### 1. DamagedPart Model

Represents individual damaged parts identified during assessment.

```python
class DamagedPart(models.Model):
    """Individual damaged part from vehicle assessment"""
    
    PART_CATEGORIES = [
        ('body', 'Body Panel'),
        ('mechanical', 'Mechanical Component'),
        ('electrical', 'Electrical Component'),
        ('glass', 'Glass/Windows'),
        ('interior', 'Interior Component'),
        ('trim', 'Trim/Cosmetic'),
    ]
    
    DAMAGE_SEVERITY = [
        ('minor', 'Minor Damage'),
        ('moderate', 'Moderate Damage'),
        ('severe', 'Severe Damage'),
        ('replace', 'Requires Replacement'),
    ]
    
    # Link to assessment and section
    assessment = models.ForeignKey(
        'VehicleAssessment',
        on_delete=models.CASCADE,
        related_name='damaged_parts'
    )
    section = models.ForeignKey(
        'VehicleSection',
        on_delete=models.CASCADE,
        related_name='damaged_parts'
    )
    
    # Part details
    part_name = models.CharField(max_length=200)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    part_category = models.CharField(max_length=20, choices=PART_CATEGORIES)
    
    # Damage details
    damage_severity = models.CharField(max_length=20, choices=DAMAGE_SEVERITY)
    damage_description = models.TextField()
    requires_replacement = models.BooleanField(default=False)
    
    # Labor estimate
    estimated_labor_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Images
    damage_image = models.ImageField(
        upload_to='damage_images/',
        blank=True,
        null=True
    )
    
    # Metadata
    identified_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['section', 'part_name']
        indexes = [
            models.Index(fields=['assessment', 'part_category']),
            models.Index(fields=['damage_severity']),
        ]
    
    def __str__(self):
        return f"{self.part_name} - {self.get_damage_severity_display()}"
    
    def get_quote_requests(self):
        """Get all quote requests for this part"""
        return PartQuoteRequest.objects.filter(damaged_part=self)
```

### 2. PartQuoteRequest Model

Manages quote requests sent to providers for specific parts.

```python
class PartQuoteRequest(models.Model):
    """Quote request for a specific damaged part"""
    
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent to Provider'),
        ('received', 'Quote Received'),
        ('expired', 'Request Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Links
    damaged_part = models.ForeignKey(
        'DamagedPart',
        on_delete=models.CASCADE,
        related_name='quote_requests'
    )
    assessment = models.ForeignKey(
        'VehicleAssessment',
        on_delete=models.CASCADE,
        related_name='part_quote_requests'
    )
    
    # Request details
    request_id = models.CharField(max_length=50, unique=True)
    request_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    
    # Provider targeting
    include_assessor = models.BooleanField(default=True)
    include_dealer = models.BooleanField(default=True)
    include_independent = models.BooleanField(default=True)
    include_network = models.BooleanField(default=True)
    
    # Additional context
    vehicle_make = models.CharField(max_length=100)
    vehicle_model = models.CharField(max_length=100)
    vehicle_year = models.IntegerField()
    
    class Meta:
        ordering = ['-request_date']
    
    def __str__(self):
        return f"Quote Request {self.request_id} - {self.damaged_part.part_name}"
    
    def generate_request_id(self):
        """Generate unique request ID"""
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"QR-{timestamp}-{unique_id}"
```

### 3. PartQuote Model

Individual quotes received from providers for specific parts.

```python
class PartQuote(models.Model):
    """Individual quote from a provider for a specific part"""
    
    PROVIDER_TYPES = [
        ('assessor', 'Assessor Estimate'),
        ('dealer', 'Authorized Dealer'),
        ('independent', 'Independent Garage'),
        ('network', 'Insurance Network'),
    ]
    
    QUOTE_STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    # Links
    quote_request = models.ForeignKey(
        'PartQuoteRequest',
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    damaged_part = models.ForeignKey(
        'DamagedPart',
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    
    # Provider information
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    provider_name = models.CharField(max_length=200)
    provider_contact = models.CharField(max_length=200, blank=True)
    
    # Part pricing
    part_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost of the part itself"
    )
    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Labor cost for repair/replacement"
    )
    paint_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Paint and finishing costs"
    )
    additional_costs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Miscellaneous costs"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total cost for this part"
    )
    
    # Part details
    part_type = models.CharField(
        max_length=50,
        choices=[
            ('oem', 'OEM (Original Equipment)'),
            ('oem_equivalent', 'OEM Equivalent'),
            ('aftermarket', 'Aftermarket'),
            ('used', 'Used/Reconditioned'),
        ],
        default='oem'
    )
    part_warranty_months = models.IntegerField(default=12)
    labor_warranty_months = models.IntegerField(default=12)
    
    # Timeline
    estimated_delivery_days = models.IntegerField(
        help_text="Days until part delivery"
    )
    estimated_completion_days = models.IntegerField(
        help_text="Days until repair completion"
    )
    
    # Quote metadata
    quote_date = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()
    status = models.CharField(max_length=20, choices=QUOTE_STATUS, default='submitted')
    
    # Quality indicators
    confidence_score = models.IntegerField(
        default=50,
        help_text="Provider confidence score (0-100)"
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['total_cost']
        unique_together = ['quote_request', 'provider_type']
        indexes = [
            models.Index(fields=['provider_type', 'total_cost']),
            models.Index(fields=['damaged_part', 'provider_type']),
        ]
    
    def __str__(self):
        return f"{self.get_provider_type_display()} - {self.damaged_part.part_name} - £{self.total_cost}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate total cost"""
        self.total_cost = (
            self.part_cost + 
            self.labor_cost + 
            self.paint_cost + 
            self.additional_costs
        )
        super().save(*args, **kwargs)
    
    def get_cost_breakdown(self):
        """Return detailed cost breakdown"""
        return {
            'part_cost': float(self.part_cost),
            'labor_cost': float(self.labor_cost),
            'paint_cost': float(self.paint_cost),
            'additional_costs': float(self.additional_costs),
            'total_cost': float(self.total_cost),
            'breakdown_percentage': {
                'part': (float(self.part_cost) / float(self.total_cost) * 100) if self.total_cost > 0 else 0,
                'labor': (float(self.labor_cost) / float(self.total_cost) * 100) if self.total_cost > 0 else 0,
                'paint': (float(self.paint_cost) / float(self.total_cost) * 100) if self.total_cost > 0 else 0,
                'additional': (float(self.additional_costs) / float(self.total_cost) * 100) if self.total_cost > 0 else 0,
            }
        }
```

### 4. PartMarketAverage Model

Stores calculated market averages for each damaged part.

```python
class PartMarketAverage(models.Model):
    """Market average calculations for individual parts"""
    
    damaged_part = models.OneToOneField(
        'DamagedPart',
        on_delete=models.CASCADE,
        related_name='market_average'
    )
    
    # Average calculations
    average_part_cost = models.DecimalField(max_digits=10, decimal_places=2)
    average_labor_cost = models.DecimalField(max_digits=10, decimal_places=2)
    average_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Range calculations
    min_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    max_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    price_variance = models.DecimalField(max_digits=10, decimal_places=2)
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Provider breakdown
    lowest_quote_provider = models.CharField(max_length=20)
    highest_quote_provider = models.CharField(max_length=20)
    
    # Statistical data
    quote_count = models.IntegerField()
    standard_deviation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Confidence metrics
    confidence_level = models.CharField(
        max_length=10,
        choices=[
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ]
    )
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Part Market Average'
        verbose_name_plural = 'Part Market Averages'
    
    def __str__(self):
        return f"Market Avg: {self.damaged_part.part_name} - £{self.average_total_cost}"
    
    def get_variance_analysis(self):
        """Return variance analysis"""
        return {
            'average': float(self.average_total_cost),
            'min': float(self.min_total_cost),
            'max': float(self.max_total_cost),
            'variance': float(self.price_variance),
            'variance_percentage': float(self.variance_percentage),
            'spread': float(self.max_total_cost - self.min_total_cost),
            'confidence': self.confidence_level,
        }
```

### 5. AssessmentQuoteSummary Model

Overall summary of all quotes for an assessment.

```python
class AssessmentQuoteSummary(models.Model):
    """Summary of all quotes for entire assessment"""
    
    assessment = models.OneToOneField(
        'VehicleAssessment',
        on_delete=models.CASCADE,
        related_name='quote_summary'
    )
    
    # Total costs by provider
    assessor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dealer_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    independent_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    network_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Market average
    market_average_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Parts statistics
    total_parts_quoted = models.IntegerField()
    total_parts_assessed = models.IntegerField()
    quote_completion_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Best quote analysis
    recommended_provider = models.CharField(max_length=20)
    recommended_total = models.DecimalField(max_digits=10, decimal_places=2)
    recommendation_reason = models.TextField()
    potential_savings = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Quality scores
    assessor_score = models.IntegerField(default=0)
    dealer_score = models.IntegerField(default=0)
    independent_score = models.IntegerField(default=0)
    network_score = models.IntegerField(default=0)
    
    # Timeline
    fastest_completion_days = models.IntegerField(null=True, blank=True)
    average_completion_days = models.IntegerField(null=True, blank=True)
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Assessment Quote Summary'
        verbose_name_plural = 'Assessment Quote Summaries'
    
    def __str__(self):
        return f"Quote Summary: {self.assessment} - Recommended: {self.recommended_provider}"
    
    def get_provider_comparison(self):
        """Return comparison of all providers"""
        providers = []
        
        if self.assessor_total > 0:
            providers.append({
                'type': 'assessor',
                'name': 'Assessor Estimate',
                'total': float(self.assessor_total),
                'score': self.assessor_score,
                'vs_market': float(self.assessor_total - self.market_average_total),
            })
        
        if self.dealer_total > 0:
            providers.append({
                'type': 'dealer',
                'name': 'Authorized Dealer',
                'total': float(self.dealer_total),
                'score': self.dealer_score,
                'vs_market': float(self.dealer_total - self.market_average_total),
            })
        
        if self.independent_total > 0:
            providers.append({
                'type': 'independent',
                'name': 'Independent Garage',
                'total': float(self.independent_total),
                'score': self.independent_score,
                'vs_market': float(self.independent_total - self.market_average_total),
            })
        
        if self.network_total > 0:
            providers.append({
                'type': 'network',
                'name': 'Insurance Network',
                'total': float(self.network_total),
                'score': self.network_score,
                'vs_market': float(self.network_total - self.market_average_total),
            })
        
        return sorted(providers, key=lambda x: x['total'])
```

---

## Quote Collection Workflow

### Step-by-Step Process

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Assessment Completion                                   │
│ - Vehicle sections assessed                                     │
│ - Damaged parts identified in each section                      │
│ - Damage severity and repair requirements determined            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Parts Aggregation                                       │
│ - Collect all damaged parts from all sections                   │
│ - Remove duplicates                                             │
│ - Categorize by part type and severity                          │
│ - Calculate estimated labor hours                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Quote Request Creation                                  │
│ - Generate unique request ID for each part                      │
│ - Package part details and vehicle information                  │
│ - Set expiry date (typically 7-14 days)                         │
│ - Determine which providers to contact                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Quote Request Dispatch                                  │
│ - Send to Assessor (internal estimate)                          │
│ - Send to Authorized Dealer (via API/Email)                     │
│ - Send to Independent Garages (via API/Email)                   │
│ - Send to Insurance Network (via API)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Quote Collection                                        │
│ - Receive quotes from providers                                 │
│ - Validate quote completeness and accuracy                      │
│ - Store itemized part costs                                     │
│ - Track response times and completion rates                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Market Average Calculation                              │
│ - Calculate average for each part                               │
│ - Calculate overall assessment average                          │
│ - Determine price variance and confidence                       │
│ - Identify outliers                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Quote Analysis & Recommendation                         │
│ - Score each provider on multiple criteria                      │
│ - Calculate value-for-money metrics                             │
│ - Consider part quality, warranties, and timeline               │
│ - Generate recommendation with reasoning                        │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow State Machine

```python
class QuoteWorkflowState:
    """State machine for quote collection workflow"""
    
    STATES = [
        'assessment_complete',    # Initial state
        'parts_aggregated',       # Parts collected
        'requests_created',       # Quote requests generated
        'requests_dispatched',    # Sent to providers
        'quotes_collecting',      # Receiving quotes
        'quotes_complete',        # All quotes received
        'analysis_complete',      # Market average calculated
        'recommendation_ready',   # Final recommendation generated
    ]
    
    TRANSITIONS = {
        'assessment_complete': ['parts_aggregated'],
        'parts_aggregated': ['requests_created'],
        'requests_created': ['requests_dispatched'],
        'requests_dispatched': ['quotes_collecting'],
        'quotes_collecting': ['quotes_complete', 'quotes_collecting'],
        'quotes_complete': ['analysis_complete'],
        'analysis_complete': ['recommendation_ready'],
    }
```

---

## Provider Types and Integration

### 1. Assessor Estimate (Internal)

**Description**: Internal estimate generated by the insurance assessor based on industry databases and experience.

**Integration Method**: Direct calculation using internal pricing database

**Characteristics**:
- Fastest turnaround (immediate)
- Based on standardized pricing
- Conservative estimates
- High reliability

**Quote Generation**:
```python
def generate_assessor_estimate(damaged_part):
    """Generate assessor's estimate for a part"""
    
    # Get base part cost from pricing database
    base_part_cost = PricingDatabase.get_part_cost(
        make=damaged_part.assessment.vehicle.make,
        model=damaged_part.assessment.vehicle.model,
        part_name=damaged_part.part_name
    )
    
    # Calculate labor cost
    labor_rate = 45.00  # £45/hour standard rate
    labor_cost = damaged_part.estimated_labor_hours * labor_rate
    
    # Calculate paint cost if applicable
    paint_cost = 0
    if damaged_part.part_category == 'body':
        paint_cost = base_part_cost * 0.15  # 15% of part cost
    
    return PartQuote(
        provider_type='assessor',
        provider_name='Internal Assessment',
        part_cost=base_part_cost,
        labor_cost=labor_cost,
        paint_cost=paint_cost,
        part_type='oem_equivalent',
        estimated_delivery_days=3,
        estimated_completion_days=5,
        confidence_score=85
    )
```

### 2. Authorized Dealer

**Description**: Official manufacturer dealer with access to OEM parts and certified technicians.

**Integration Method**: API integration or automated email system

**Characteristics**:
- Premium pricing (typically 20-30% higher)
- OEM parts only
- Manufacturer warranty
- Longer lead times for rare parts
- High quality assurance

**API Request Format**:
```json
{
    "request_id": "QR-20241227-ABC123",
    "vehicle": {
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "vin": "1HGBH41JXMN109186"
    },
    "parts": [
        {
            "part_name": "Front Bumper",
            "part_number": "52119-06903",
            "damage_severity": "replace",
            "estimated_labor_hours": 2.5,
            "requires_paint": true,
            "damage_description": "Cracked and deformed from impact",
            "image_url": "https://..."
        }
    ],
    "quote_deadline": "2025-01-03T23:59:59Z"
}
```

**Expected Response**:
```json
{
    "request_id": "QR-20241227-ABC123",
    "dealer_name": "Toyota Main Dealer",
    "dealer_contact": "service@toyotadealer.com",
    "quotes": [
        {
            "part_name": "Front Bumper",
            "part_number": "52119-06903",
            "part_cost": 450.00,
            "part_type": "oem",
            "labor_cost": 125.00,
            "labor_hours": 2.5,
            "paint_cost": 180.00,
            "additional_costs": 25.00,
            "total_cost": 780.00,
            "availability": "in_stock",
            "delivery_days": 1,
            "completion_days": 3,
            "warranty_months": 24,
            "notes": "OEM part with manufacturer warranty"
        }
    ],
    "valid_until": "2025-01-03T23:59:59Z"
}
```

### 3. Independent Garage

**Description**: Local independent repair shops offering competitive pricing with aftermarket parts.

**Integration Method**: Multi-garage quote aggregation platform or individual requests

**Characteristics**:
- Competitive pricing (typically 15-25% lower)
- Aftermarket or OEM equivalent parts
- Flexible scheduling
- Faster turnaround
- Variable quality depending on garage

**Request Distribution**:
```python
def dispatch_to_independent_garages(part_quote_request):
    """Send quote request to multiple independent garages"""
    
    # Get qualified garages in the area
    garages = IndependentGarage.objects.filter(
        location__distance_lte=(
            part_quote_request.assessment.location,
            25  # 25 mile radius
        ),
        certified=True,
        rating__gte=4.0
    )[:5]  # Top 5 garages
    
    for garage in garages:
        # Send quote request via API or email
        send_quote_request(
            garage=garage,
            request=part_quote_request,
            method=garage.preferred_contact_method
        )
```

### 4. Insurance Network

**Description**: Pre-approved repair network with negotiated rates and guaranteed work.

**Integration Method**: Direct API integration with insurance network platform

**Characteristics**:
- Negotiated pricing (typically 10-15% lower)
- Mix of OEM and quality aftermarket parts
- Guaranteed work quality
- Streamlined claims process
- Priority service for insurance customers

**API Integration**:
```python
class InsuranceNetworkAPI:
    """Integration with insurance network providers"""
    
    def __init__(self, api_key, network_id):
        self.api_key = api_key
        self.network_id = network_id
        self.base_url = "https://api.insurancenetwork.com/v1"
    
    def request_quote(self, assessment, damaged_parts):
        """Request quotes from network providers"""
        
        payload = {
            "network_id": self.network_id,
            "claim_number": assessment.claim_number,
            "vehicle": self._format_vehicle_data(assessment.vehicle),
            "parts": self._format_parts_data(damaged_parts),
            "location": {
                "postcode": assessment.location_postcode,
                "radius_miles": 20
            },
            "urgency": "standard",
            "preferred_parts": "oem_or_equivalent"
        }
        
        response = requests.post(
            f"{self.base_url}/quote-requests",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )
        
        return response.json()
    
    def _format_vehicle_data(self, vehicle):
        return {
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "registration": vehicle.registration_number,
            "vin": vehicle.vin_number
        }
    
    def _format_parts_data(self, damaged_parts):
        return [
            {
                "part_id": part.id,
                "part_name": part.part_name,
                "part_number": part.part_number,
                "damage_type": part.damage_severity,
                "labor_hours": float(part.estimated_labor_hours)
            }
            for part in damaged_parts
        ]
```

---

## Market Average Calculation

### Algorithm Overview

The market average calculation system analyzes all received quotes for each damaged part and calculates comprehensive statistics.

### Core Calculation Engine

```python
class MarketAverageCalculator:
    """Calculate market averages for damaged parts"""
    
    def __init__(self, damaged_part):
        self.damaged_part = damaged_part
        self.quotes = damaged_part.quotes.filter(
            status='submitted'
        ).exclude(total_cost=0)
    
    def calculate(self):
        """Calculate comprehensive market average"""
        
        if self.quotes.count() < 2:
            raise ValueError("Need at least 2 quotes to calculate market average")
        
        # Extract cost data
        total_costs = [float(q.total_cost) for q in self.quotes]
        part_costs = [float(q.part_cost) for q in self.quotes]
        labor_costs = [float(q.labor_cost) for q in self.quotes]
        
        # Calculate averages
        avg_total = statistics.mean(total_costs)
        avg_part = statistics.mean(part_costs)
        avg_labor = statistics.mean(labor_costs)
        
        # Calculate range
        min_cost = min(total_costs)
        max_cost = max(total_costs)
        variance = max_cost - min_cost
        variance_pct = (variance / avg_total) * 100
        
        # Calculate standard deviation
        std_dev = statistics.stdev(total_costs) if len(total_costs) > 1 else 0
        
        # Determine confidence level
        confidence = self._calculate_confidence(variance_pct, std_dev, len(total_costs))
        
        # Identify outliers
        outliers = self._identify_outliers(total_costs, avg_total, std_dev)
        
        # Find min/max providers
        min_quote = min(self.quotes, key=lambda q: q.total_cost)
        max_quote = max(self.quotes, key=lambda q: q.total_cost)
        
        # Create or update market average record
        market_avg, created = PartMarketAverage.objects.update_or_create(
            damaged_part=self.damaged_part,
            defaults={
                'average_part_cost': Decimal(str(round(avg_part, 2))),
                'average_labor_cost': Decimal(str(round(avg_labor, 2))),
                'average_total_cost': Decimal(str(round(avg_total, 2))),
                'min_total_cost': Decimal(str(round(min_cost, 2))),
                'max_total_cost': Decimal(str(round(max_cost, 2))),
                'price_variance': Decimal(str(round(variance, 2))),
                'variance_percentage': Decimal(str(round(variance_pct, 2))),
                'lowest_quote_provider': min_quote.provider_type,
                'highest_quote_provider': max_quote.provider_type,
                'quote_count': len(total_costs),
                'standard_deviation': Decimal(str(round(std_dev, 2))),
                'confidence_level': confidence,
            }
        )
        
        return market_avg
    
    def _calculate_confidence(self, variance_pct, std_dev, quote_count):
        """Calculate confidence level based on variance and data quality"""
        
        # Base confidence on variance percentage
        if variance_pct < 10:
            base_confidence = 'high'
        elif variance_pct < 25:
            base_confidence = 'medium'
        else:
            base_confidence = 'low'
        
        # Adjust for quote count
        if quote_count < 3:
            if base_confidence == 'high':
                base_confidence = 'medium'
            elif base_confidence == 'medium':
                base_confidence = 'low'
        
        return base_confidence
    
    def _identify_outliers(self, values, mean, std_dev):
        """Identify statistical outliers (> 2 standard deviations)"""
        
        if std_dev == 0:
            return []
        
        outliers = []
        for value in values:
            z_score = abs((value - mean) / std_dev)
            if z_score > 2:
                outliers.append(value)
        
        return outliers
```

### Part-by-Part Analysis

```python
def calculate_all_part_averages(assessment):
    """Calculate market average for all damaged parts in assessment"""
    
    damaged_parts = assessment.damaged_parts.all()
    results = []
    
    for part in damaged_parts:
        try:
            calculator = MarketAverageCalculator(part)
            market_avg = calculator.calculate()
            results.append({
                'part': part,
                'market_average': market_avg,
                'status': 'success'
            })
        except ValueError as e:
            results.append({
                'part': part,
                'market_average': None,
                'status': 'insufficient_quotes',
                'error': str(e)
            })
    
    return results
```

### Overall Assessment Average

```python
def calculate_assessment_market_average(assessment):
    """Calculate overall market average for entire assessment"""
    
    # Get all part market averages
    part_averages = PartMarketAverage.objects.filter(
        damaged_part__assessment=assessment
    )
    
    if not part_averages.exists():
        return None
    
    # Sum up all averages
    total_market_average = sum(
        float(pa.average_total_cost) for pa in part_averages
    )
    
    # Calculate provider totals
    provider_totals = {
        'assessor': 0,
        'dealer': 0,
        'independent': 0,
        'network': 0,
    }
    
    for part in assessment.damaged_parts.all():
        for quote in part.quotes.filter(status='submitted'):
            provider_totals[quote.provider_type] += float(quote.total_cost)
    
    return {
        'market_average': total_market_average,
        'provider_totals': provider_totals,
        'part_count': part_averages.count(),
    }
```

---

## Quote Recommendation Engine

### Scoring Algorithm

The recommendation engine uses a multi-factor scoring system to determine the best quote.

```python
class QuoteRecommendationEngine:
    """Intelligent quote recommendation system"""
    
    WEIGHTS = {
        'price': 0.40,           # 40% weight on price
        'quality': 0.25,         # 25% weight on quality
        'timeline': 0.15,        # 15% weight on completion time
        'warranty': 0.10,        # 10% weight on warranty
        'reliability': 0.10,     # 10% weight on provider reliability
    }
    
    def __init__(self, assessment):
        self.assessment = assessment
        self.damaged_parts = assessment.damaged_parts.all()
    
    def generate_recommendation(self):
        """Generate comprehensive quote recommendation"""
        
        # Calculate scores for each provider
        provider_scores = self._calculate_provider_scores()
        
        # Determine best overall value
        recommended_provider = max(
            provider_scores.items(),
            key=lambda x: x[1]['total_score']
        )
        
        # Calculate potential savings
        market_avg = calculate_assessment_market_average(self.assessment)
        recommended_total = provider_scores[recommended_provider[0]]['total_cost']
        
        highest_total = max(
            score['total_cost'] 
            for score in provider_scores.values()
        )
        
        potential_savings = highest_total - recommended_total
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            recommended_provider[0],
            provider_scores[recommended_provider[0]],
            market_avg
        )
        
        # Create or update summary
        summary, created = AssessmentQuoteSummary.objects.update_or_create(
            assessment=self.assessment,
            defaults={
                'assessor_total': provider_scores.get('assessor', {}).get('total_cost', 0),
                'dealer_total': provider_scores.get('dealer', {}).get('total_cost', 0),
                'independent_total': provider_scores.get('independent', {}).get('total_cost', 0),
                'network_total': provider_scores.get('network', {}).get('total_cost', 0),
                'market_average_total': market_avg['market_average'],
                'total_parts_quoted': len(self.damaged_parts),
                'total_parts_assessed': len(self.damaged_parts),
                'quote_completion_percentage': 100,
                'recommended_provider': recommended_provider[0],
                'recommended_total': recommended_total,
                'recommendation_reason': reasoning,
                'potential_savings': potential_savings,
                'assessor_score': provider_scores.get('assessor', {}).get('total_score', 0),
                'dealer_score': provider_scores.get('dealer', {}).get('total_score', 0),
                'independent_score': provider_scores.get('independent', {}).get('total_score', 0),
                'network_score': provider_scores.get('network', {}).get('total_score', 0),
            }
        )
        
        return summary
    
    def _calculate_provider_scores(self):
        """Calculate comprehensive scores for all providers"""
        
        providers = ['assessor', 'dealer', 'independent', 'network']
        scores = {}
        
        for provider in providers:
            quotes = PartQuote.objects.filter(
                damaged_part__assessment=self.assessment,
                provider_type=provider,
                status='submitted'
            )
            
            if not quotes.exists():
                continue
            
            # Calculate total cost
            total_cost = sum(float(q.total_cost) for q in quotes)
            
            # Calculate individual factor scores
            price_score = self._calculate_price_score(total_cost)
            quality_score = self._calculate_quality_score(quotes)
            timeline_score = self._calculate_timeline_score(quotes)
            warranty_score = self._calculate_warranty_score(quotes)
            reliability_score = self._calculate_reliability_score(provider)
            
            # Calculate weighted total score
            total_score = (
                price_score * self.WEIGHTS['price'] +
                quality_score * self.WEIGHTS['quality'] +
                timeline_score * self.WEIGHTS['timeline'] +
                warranty_score * self.WEIGHTS['warranty'] +
                reliability_score * self.WEIGHTS['reliability']
            )
            
            scores[provider] = {
                'total_cost': total_cost,
                'price_score': price_score,
                'quality_score': quality_score,
                'timeline_score': timeline_score,
                'warranty_score': warranty_score,
                'reliability_score': reliability_score,
                'total_score': round(total_score, 2),
            }
        
        return scores
    
    def _calculate_price_score(self, total_cost):
        """Score based on price competitiveness (0-100)"""
        
        all_totals = []
        for provider in ['assessor', 'dealer', 'independent', 'network']:
            quotes = PartQuote.objects.filter(
                damaged_part__assessment=self.assessment,
                provider_type=provider,
                status='submitted'
            )
            if quotes.exists():
                all_totals.append(sum(float(q.total_cost) for q in quotes))
        
        if not all_totals:
            return 50
        
        min_total = min(all_totals)
        max_total = max(all_totals)
        
        if max_total == min_total:
            return 100
        
        # Inverse scoring: lower price = higher score
        score = 100 - ((total_cost - min_total) / (max_total - min_total) * 100)
        return round(score, 2)
    
    def _calculate_quality_score(self, quotes):
        """Score based on part quality and type (0-100)"""
        
        quality_points = {
            'oem': 100,
            'oem_equivalent': 85,
            'aftermarket': 70,
            'used': 50,
        }
        
        total_quality = 0
        for quote in quotes:
            total_quality += quality_points.get(quote.part_type, 70)
        
        return round(total_quality / quotes.count(), 2) if quotes.count() > 0 else 70
    
    def _calculate_timeline_score(self, quotes):
        """Score based on completion timeline (0-100)"""
        
        avg_completion_days = sum(
            q.estimated_completion_days for q in quotes
        ) / quotes.count()
        
        # Score inversely proportional to days
        # 1-3 days = 100, 4-7 days = 80, 8-14 days = 60, 15+ days = 40
        if avg_completion_days <= 3:
            return 100
        elif avg_completion_days <= 7:
            return 80
        elif avg_completion_days <= 14:
            return 60
        else:
            return 40
    
    def _calculate_warranty_score(self, quotes):
        """Score based on warranty terms (0-100)"""
        
        avg_warranty_months = sum(
            q.part_warranty_months for q in quotes
        ) / quotes.count()
        
        # 24+ months = 100, 12 months = 70, 6 months = 50, <6 months = 30
        if avg_warranty_months >= 24:
            return 100
        elif avg_warranty_months >= 12:
            return 70
        elif avg_warranty_months >= 6:
            return 50
        else:
            return 30
    
    def _calculate_reliability_score(self, provider_type):
        """Score based on provider reliability (0-100)"""
        
        # Base reliability scores by provider type
        reliability_scores = {
            'dealer': 95,        # Highest reliability
            'network': 90,       # High reliability with guarantees
            'assessor': 85,      # Reliable estimates
            'independent': 75,   # Variable reliability
        }
        
        return reliability_scores.get(provider_type, 70)
    
    def _generate_reasoning(self, provider, scores, market_avg):
        """Generate human-readable reasoning for recommendation"""
        
        reasons = []
        
        # Price comparison
        if scores['total_cost'] < market_avg['market_average']:
            savings = market_avg['market_average'] - scores['total_cost']
            reasons.append(
                f"£{savings:.2f} below market average "
                f"({((savings/market_avg['market_average'])*100):.1f}% savings)"
            )
        
        # Quality assessment
        if scores['quality_score'] >= 85:
            reasons.append("High quality parts (OEM or equivalent)")
        
        # Timeline
        if scores['timeline_score'] >= 80:
            reasons.append("Fast completion timeline")
        
        # Warranty
        if scores['warranty_score'] >= 70:
            reasons.append("Comprehensive warranty coverage")
        
        # Overall value
        if scores['total_score'] >= 80:
            reasons.append("Excellent overall value for money")
        
        provider_names = {
            'assessor': 'Assessor Estimate',
            'dealer': 'Authorized Dealer',
            'independent': 'Independent Garage',
            'network': 'Insurance Network',
        }
        
        reasoning = (
            f"**{provider_names[provider]}** is recommended based on:\n\n"
            + "\n".join(f"• {reason}" for reason in reasons)
            + f"\n\n**Overall Score**: {scores['total_score']}/100"
        )
        
        return reasoning
```

### Alternative Recommendation Strategies

```python
class RecommendationStrategy:
    """Different recommendation strategies for different scenarios"""
    
    @staticmethod
    def best_value(assessment):
        """Best overall value (default strategy)"""
        engine = QuoteRecommendationEngine(assessment)
        return engine.generate_recommendation()
    
    @staticmethod
    def lowest_price(assessment):
        """Recommend lowest total price"""
        provider_totals = {}
        
        for provider in ['assessor', 'dealer', 'independent', 'network']:
            quotes = PartQuote.objects.filter(
                damaged_part__assessment=assessment,
                provider_type=provider,
                status='submitted'
            )
            if quotes.exists():
                provider_totals[provider] = sum(
                    float(q.total_cost) for q in quotes
                )
        
        if not provider_totals:
            return None
        
        return min(provider_totals.items(), key=lambda x: x[1])
    
    @staticmethod
    def fastest_completion(assessment):
        """Recommend fastest completion time"""
        provider_timelines = {}
        
        for provider in ['assessor', 'dealer', 'independent', 'network']:
            quotes = PartQuote.objects.filter(
                damaged_part__assessment=assessment,
                provider_type=provider,
                status='submitted'
            )
            if quotes.exists():
                avg_days = sum(
                    q.estimated_completion_days for q in quotes
                ) / quotes.count()
                provider_timelines[provider] = avg_days
        
        if not provider_timelines:
            return None
        
        return min(provider_timelines.items(), key=lambda x: x[1])
    
    @staticmethod
    def highest_quality(assessment):
        """Recommend highest quality parts"""
        quality_ranks = {'oem': 4, 'oem_equivalent': 3, 'aftermarket': 2, 'used': 1}
        provider_quality = {}
        
        for provider in ['assessor', 'dealer', 'independent', 'network']:
            quotes = PartQuote.objects.filter(
                damaged_part__assessment=assessment,
                provider_type=provider,
                status='submitted'
            )
            if quotes.exists():
                avg_quality = sum(
                    quality_ranks.get(q.part_type, 2) for q in quotes
                ) / quotes.count()
                provider_quality[provider] = avg_quality
        
        if not provider_quality:
            return None
        
        return max(provider_quality.items(), key=lambda x: x[1])
```

---

## API Endpoints

### RESTful API Design

```python
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'damaged-parts', api_views.DamagedPartViewSet)
router.register(r'part-quotes', api_views.PartQuoteViewSet)
router.register(r'quote-requests', api_views.PartQuoteRequestViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/assessment/<int:assessment_id>/aggregate-parts/', 
         api_views.aggregate_damaged_parts),
    path('api/assessment/<int:assessment_id>/request-quotes/',
         api_views.request_quotes_for_assessment),
    path('api/assessment/<int:assessment_id>/calculate-market-average/',
         api_views.calculate_market_averages),
    path('api/assessment/<int:assessment_id>/generate-recommendation/',
         api_views.generate_recommendation),
    path('api/assessment/<int:assessment_id>/quote-summary/',
         api_views.get_quote_summary),
]
```

### API View Implementations

```python
# api_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

@api_view(['POST'])
def aggregate_damaged_parts(request, assessment_id):
    """
    Aggregate all damaged parts from assessment sections
    
    POST /api/assessment/{id}/aggregate-parts/
    """
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id)
    
    # Get all damaged parts from all sections
    damaged_parts = DamagedPart.objects.filter(assessment=assessment)
    
    # Group by category
    parts_by_category = {}
    for part in damaged_parts:
        category = part.part_category
        if category not in parts_by_category:
            parts_by_category[category] = []
        parts_by_category[category].append({
            'id': part.id,
            'name': part.part_name,
            'severity': part.damage_severity,
            'section': part.section.name,
        })
    
    return Response({
        'assessment_id': assessment_id,
        'total_parts': damaged_parts.count(),
        'parts_by_category': parts_by_category,
    })

@api_view(['POST'])
def request_quotes_for_assessment(request, assessment_id):
    """
    Create and dispatch quote requests for all damaged parts
    
    POST /api/assessment/{id}/request-quotes/
    Body: {
        "providers": ["assessor", "dealer", "independent", "network"],
        "expiry_days": 7
    }
    """
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id)
    providers = request.data.get('providers', ['assessor', 'dealer', 'independent', 'network'])
    expiry_days = request.data.get('expiry_days', 7)
    
    damaged_parts = assessment.damaged_parts.all()
    quote_requests_created = []
    
    for part in damaged_parts:
        # Create quote request
        quote_request = PartQuoteRequest.objects.create(
            damaged_part=part,
            assessment=assessment,
            request_id=generate_unique_request_id(),
            expiry_date=timezone.now() + timedelta(days=expiry_days),
            include_assessor='assessor' in providers,
            include_dealer='dealer' in providers,
            include_independent='independent' in providers,
            include_network='network' in providers,
            vehicle_make=assessment.vehicle.make,
            vehicle_model=assessment.vehicle.model,
            vehicle_year=assessment.vehicle.year,
        )
        
        # Dispatch to providers
        dispatch_quote_request(quote_request, providers)
        
        quote_requests_created.append({
            'request_id': quote_request.request_id,
            'part_name': part.part_name,
            'providers_contacted': providers,
        })
    
    return Response({
        'assessment_id': assessment_id,
        'quote_requests_created': len(quote_requests_created),
        'details': quote_requests_created,
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def calculate_market_averages(request, assessment_id):
    """
    Calculate market averages for all parts in assessment
    
    POST /api/assessment/{id}/calculate-market-average/
    """
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id)
    
    results = calculate_all_part_averages(assessment)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']
    
    return Response({
        'assessment_id': assessment_id,
        'total_parts': len(results),
        'successful_calculations': len(successful),
        'failed_calculations': len(failed),
        'market_averages': [
            {
                'part_name': r['part'].part_name,
                'average_cost': float(r['market_average'].average_total_cost),
                'min_cost': float(r['market_average'].min_total_cost),
                'max_cost': float(r['market_average'].max_total_cost),
                'confidence': r['market_average'].confidence_level,
            }
            for r in successful
        ],
        'failures': [
            {
                'part_name': r['part'].part_name,
                'reason': r.get('error', 'Unknown error'),
            }
            for r in failed
        ]
    })

@api_view(['POST'])
def generate_recommendation(request, assessment_id):
    """
    Generate quote recommendation for assessment
    
    POST /api/assessment/{id}/generate-recommendation/
    Body: {
        "strategy": "best_value"  // or "lowest_price", "fastest_completion", "highest_quality"
    }
    """
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id)
    strategy = request.data.get('strategy', 'best_value')
    
    # Generate recommendation based on strategy
    if strategy == 'best_value':
        summary = RecommendationStrategy.best_value(assessment)
    elif strategy == 'lowest_price':
        result = RecommendationStrategy.lowest_price(assessment)
        # Convert to summary format
    elif strategy == 'fastest_completion':
        result = RecommendationStrategy.fastest_completion(assessment)
    elif strategy == 'highest_quality':
        result = RecommendationStrategy.highest_quality(assessment)
    else:
        return Response({
            'error': 'Invalid strategy'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'assessment_id': assessment_id,
        'recommended_provider': summary.recommended_provider,
        'recommended_total': float(summary.recommended_total),
        'market_average': float(summary.market_average_total),
        'potential_savings': float(summary.potential_savings),
        'recommendation_reason': summary.recommendation_reason,
        'provider_scores': {
            'assessor': summary.assessor_score,
            'dealer': summary.dealer_score,
            'independent': summary.independent_score,
            'network': summary.network_score,
        }
    })

@api_view(['GET'])
def get_quote_summary(request, assessment_id):
    """
    Get comprehensive quote summary for assessment
    
    GET /api/assessment/{id}/quote-summary/
    """
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id)
    
    try:
        summary = assessment.quote_summary
    except AssessmentQuoteSummary.DoesNotExist:
        return Response({
            'error': 'Quote summary not yet generated. Please generate recommendation first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get detailed part breakdowns
    part_details = []
    for part in assessment.damaged_parts.all():
        quotes = part.quotes.filter(status='submitted')
        part_details.append({
            'part_name': part.part_name,
            'quotes': [
                {
                    'provider': q.get_provider_type_display(),
                    'total_cost': float(q.total_cost),
                    'part_cost': float(q.part_cost),
                    'labor_cost': float(q.labor_cost),
                    'part_type': q.get_part_type_display(),
                }
                for q in quotes
            ]
        })
    
    return Response({
        'assessment_id': assessment_id,
        'summary': {
            'market_average_total': float(summary.market_average_total),
            'recommended_provider': summary.recommended_provider,
            'recommended_total': float(summary.recommended_total),
            'potential_savings': float(summary.potential_savings),
            'recommendation_reason': summary.recommendation_reason,
        },
        'provider_totals': {
            'assessor': float(summary.assessor_total) if summary.assessor_total > 0 else None,
            'dealer': float(summary.dealer_total) if summary.dealer_total > 0 else None,
            'independent': float(summary.independent_total) if summary.independent_total > 0 else None,
            'network': float(summary.network_total) if summary.network_total > 0 else None,
        },
        'provider_scores': {
            'assessor': summary.assessor_score,
            'dealer': summary.dealer_score,
            'independent': summary.independent_score,
            'network': summary.network_score,
        },
        'part_details': part_details,
        'statistics': {
            'total_parts': summary.total_parts_quoted,
            'fastest_completion_days': summary.fastest_completion_days,
            'average_completion_days': summary.average_completion_days,
        }
    })
```

---

## Business Logic

### Complete Workflow Implementation

```python
class QuoteWorkflowManager:
    """Manages the complete quote workflow from assessment to recommendation"""
    
    def __init__(self, assessment):
        self.assessment = assessment
    
    def execute_complete_workflow(self):
        """Execute the complete quote workflow"""
        
        workflow_log = []
        
        try:
            # Step 1: Aggregate damaged parts
            workflow_log.append(self._log_step(
                "Aggregating damaged parts",
                self._aggregate_parts()
            ))
            
            # Step 2: Create quote requests
            workflow_log.append(self._log_step(
                "Creating quote requests",
                self._create_quote_requests()
            ))
            
            # Step 3: Dispatch to providers
            workflow_log.append(self._log_step(
                "Dispatching to providers",
                self._dispatch_requests()
            ))
            
            # Step 4: Wait for quotes (this would be async in production)
            workflow_log.append(self._log_step(
                "Collecting quotes",
                {"status": "pending", "message": "Waiting for provider responses"}
            ))
            
            # Step 5: Calculate market averages (done after quotes received)
            # Step 6: Generate recommendation (done after market averages)
            
            return {
                'status': 'success',
                'workflow_log': workflow_log,
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'workflow_log': workflow_log,
            }
    
    def _aggregate_parts(self):
        """Aggregate all damaged parts"""
        parts = self.assessment.damaged_parts.all()
        return {
            'parts_count': parts.count(),
            'categories': list(parts.values_list('part_category', flat=True).distinct())
        }
    
    def _create_quote_requests(self):
        """Create quote requests for all parts"""
        requests_created = []
        
        for part in self.assessment.damaged_parts.all():
            quote_request = PartQuoteRequest.objects.create(
                damaged_part=part,
                assessment=self.assessment,
                request_id=self._generate_request_id(),
                expiry_date=timezone.now() + timedelta(days=7),
                vehicle_make=self.assessment.vehicle.make,
                vehicle_model=self.assessment.vehicle.model,
                vehicle_year=self.assessment.vehicle.year,
            )
            requests_created.append(quote_request)
        
        return {
            'requests_created': len(requests_created),
            'request_ids': [r.request_id for r in requests_created]
        }
    
    def _dispatch_requests(self):
        """Dispatch quote requests to all providers"""
        dispatched = {
            'assessor': 0,
            'dealer': 0,
            'independent': 0,
            'network': 0,
        }
        
        quote_requests = PartQuoteRequest.objects.filter(
            assessment=self.assessment,
            status='pending'
        )
        
        for request in quote_requests:
            # Generate assessor estimate immediately
            if request.include_assessor:
                self._generate_assessor_quote(request)
                dispatched['assessor'] += 1
            
            # Send to dealer
            if request.include_dealer:
                self._send_to_dealer(request)
                dispatched['dealer'] += 1
            
            # Send to independent garages
            if request.include_independent:
                self._send_to_independent(request)
                dispatched['independent'] += 1
            
            # Send to insurance network
            if request.include_network:
                self._send_to_network(request)
                dispatched['network'] += 1
            
            # Update request status
            request.status = 'sent'
            request.save()
        
        return dispatched
    
    def _generate_assessor_quote(self, quote_request):
        """Generate immediate assessor estimate"""
        part = quote_request.damaged_part
        
        # Use internal pricing database
        base_cost = self._get_base_part_cost(part)
        labor_cost = float(part.estimated_labor_hours) * 45.00  # £45/hour
        paint_cost = base_cost * 0.15 if part.part_category == 'body' else 0
        
        PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=part,
            provider_type='assessor',
            provider_name=f'{self.assessment.assessor_name}',
            part_cost=Decimal(str(base_cost)),
            labor_cost=Decimal(str(labor_cost)),
            paint_cost=Decimal(str(paint_cost)),
            part_type='oem_equivalent',
            estimated_delivery_days=3,
            estimated_completion_days=5,
            valid_until=timezone.now() + timedelta(days=30),
            confidence_score=85
        )
    
    def _get_base_part_cost(self, part):
        """Get base part cost from pricing database"""
        # This would query an actual pricing database in production
        # For now, return estimated costs based on category
        base_costs = {
            'body': 300,
            'mechanical': 450,
            'electrical': 250,
            'glass': 200,
            'interior': 150,
            'trim': 100,
        }
        return base_costs.get(part.part_category, 200)
    
    def _send_to_dealer(self, quote_request):
        """Send quote request to authorized dealer"""
        # Implementation would integrate with dealer API
        pass
    
    def _send_to_independent(self, quote_request):
        """Send quote request to independent garages"""
        # Implementation would integrate with garage network
        pass
    
    def _send_to_network(self, quote_request):
        """Send quote request to insurance network"""
        # Implementation would integrate with insurance network API
        pass
    
    def _generate_request_id(self):
        """Generate unique request ID"""
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"QR-{timestamp}-{unique_id}"
    
    def _log_step(self, step_name, result):
        """Log workflow step"""
        return {
            'step': step_name,
            'timestamp': timezone.now().isoformat(),
            'result': result
        }
```

### Quote Response Handler

```python
class QuoteResponseHandler:
    """Handles incoming quotes from providers"""
    
    @staticmethod
    def process_provider_response(quote_request_id, provider_type, quote_data):
        """Process incoming quote from provider"""
        
        try:
            quote_request = PartQuoteRequest.objects.get(
                request_id=quote_request_id
            )
            
            # Validate quote data
            if not QuoteResponseHandler._validate_quote_data(quote_data):
                raise ValueError("Invalid quote data format")
            
            # Check if quote already exists
            existing_quote = PartQuote.objects.filter(
                quote_request=quote_request,
                provider_type=provider_type
            ).first()
            
            if existing_quote:
                # Update existing quote
                QuoteResponseHandler._update_quote(existing_quote, quote_data)
            else:
                # Create new quote
                QuoteResponseHandler._create_quote(
                    quote_request,
                    provider_type,
                    quote_data
                )
            
            # Check if all quotes received
            QuoteResponseHandler._check_completion(quote_request)
            
            return {'status': 'success', 'message': 'Quote processed successfully'}
            
        except PartQuoteRequest.DoesNotExist:
            return {'status': 'error', 'message': 'Quote request not found'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def _validate_quote_data(quote_data):
        """Validate incoming quote data"""
        required_fields = [
            'provider_name',
            'part_cost',
            'labor_cost',
            'estimated_delivery_days',
            'estimated_completion_days'
        ]
        return all(field in quote_data for field in required_fields)
    
    @staticmethod
    def _create_quote(quote_request, provider_type, quote_data):
        """Create new quote from provider data"""
        return PartQuote.objects.create(
            quote_request=quote_request,
            damaged_part=quote_request.damaged_part,
            provider_type=provider_type,
            provider_name=quote_data['provider_name'],
            provider_contact=quote_data.get('provider_contact', ''),
            part_cost=Decimal(str(quote_data['part_cost'])),
            labor_cost=Decimal(str(quote_data['labor_cost'])),
            paint_cost=Decimal(str(quote_data.get('paint_cost', 0))),
            additional_costs=Decimal(str(quote_data.get('additional_costs', 0))),
            part_type=quote_data.get('part_type', 'oem_equivalent'),
            part_warranty_months=quote_data.get('part_warranty_months', 12),
            labor_warranty_months=quote_data.get('labor_warranty_months', 12),
            estimated_delivery_days=quote_data['estimated_delivery_days'],
            estimated_completion_days=quote_data['estimated_completion_days'],
            valid_until=timezone.now() + timedelta(days=14),
            confidence_score=quote_data.get('confidence_score', 70),
            notes=quote_data.get('notes', ''),
            status='submitted'
        )
    
    @staticmethod
    def _update_quote(quote, quote_data):
        """Update existing quote with new data"""
        quote.provider_name = quote_data['provider_name']
        quote.provider_contact = quote_data.get('provider_contact', '')
        quote.part_cost = Decimal(str(quote_data['part_cost']))
        quote.labor_cost = Decimal(str(quote_data['labor_cost']))
        quote.paint_cost = Decimal(str(quote_data.get('paint_cost', 0)))
        quote.additional_costs = Decimal(str(quote_data.get('additional_costs', 0)))
        quote.part_type = quote_data.get('part_type', quote.part_type)
        quote.estimated_delivery_days = quote_data['estimated_delivery_days']
        quote.estimated_completion_days = quote_data['estimated_completion_days']
        quote.notes = quote_data.get('notes', '')
        quote.save()
        return quote
    
    @staticmethod
    def _check_completion(quote_request):
        """Check if all expected quotes have been received"""
        expected_providers = []
        
        if quote_request.include_assessor:
            expected_providers.append('assessor')
        if quote_request.include_dealer:
            expected_providers.append('dealer')
        if quote_request.include_independent:
            expected_providers.append('independent')
        if quote_request.include_network:
            expected_providers.append('network')
        
        received_providers = list(
            quote_request.quotes.values_list('provider_type', flat=True)
        )
        
        if set(expected_providers) == set(received_providers):
            quote_request.status = 'received'
            quote_request.save()
            
            # Trigger market average calculation if all parts have quotes
            assessment = quote_request.assessment
            all_requests = assessment.part_quote_requests.all()
            
            if all(req.status == 'received' for req in all_requests):
                # All quotes received, calculate market averages
                calculate_all_part_averages(assessment)
                
                # Generate recommendation
                engine = QuoteRecommendationEngine(assessment)
                engine.generate_recommendation()
```

---

## Implementation Examples

### Example 1: Complete Workflow Execution

```python
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import VehicleAssessment

def initiate_quote_workflow(request, assessment_id):
    """Initiate complete quote workflow for an assessment"""
    
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id)
    
    # Check if assessment is complete
    if not assessment.is_complete:
        messages.error(request, 'Assessment must be completed before requesting quotes')
        return redirect('assessment_detail', assessment_id=assessment_id)
    
    # Initialize workflow manager
    workflow = QuoteWorkflowManager(assessment)
    
    # Execute workflow
    result = workflow.execute_complete_workflow()
    
    if result['status'] == 'success':
        messages.success(
            request,
            f"Quote requests sent successfully. "
            f"Quotes dispatched to {len(result['workflow_log'])} providers."
        )
    else:
        messages.error(request, f"Workflow error: {result.get('error')}")
    
    return redirect('quote_status', assessment_id=assessment_id)
```

### Example 2: Provider Quote Submission

```python
# api_views.py
@api_view(['POST'])
def submit_provider_quote(request):
    """
    API endpoint for providers to submit quotes
    
    POST /api/quotes/submit/
    Body: {
        "request_id": "QR-20241227-ABC123",
        "provider_type": "dealer",
        "quote_data": {
            "provider_name": "Toyota Main Dealer",
            "provider_contact": "service@toyota.com",
            "part_cost": 450.00,
            "labor_cost": 125.00,
            "paint_cost": 180.00,
            "part_type": "oem",
            "estimated_delivery_days": 2,
            "estimated_completion_days": 4,
            "part_warranty_months": 24,
            "notes": "OEM part with manufacturer warranty"
        }
    }
    """
    request_id = request.data.get('request_id')
    provider_type = request.data.get('provider_type')
    quote_data = request.data.get('quote_data')
    
    if not all([request_id, provider_type, quote_data]):
        return Response({
            'error': 'Missing required fields'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    result = QuoteResponseHandler.process_provider_response(
        request_id,
        provider_type,
        quote_data
    )
    
    if result['status'] == 'success':
        return Response(result, status=status.HTTP_201_CREATED)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
```

### Example 3: View Quote Summary and Recommendation

```python
# views.py
def quote_summary_view(request, assessment_id):
    """Display comprehensive quote summary with recommendation"""
    
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id)
    
    try:
        summary = assessment.quote_summary
    except AssessmentQuoteSummary.DoesNotExist:
        messages.warning(
            request,
            'Quote summary not available yet. Please wait for all quotes to be received.'
        )
        return redirect('quote_status', assessment_id=assessment_id)
    
    # Get part-by-part breakdown
    part_details = []
    for part in assessment.damaged_parts.all():
        try:
            market_avg = part.market_average
            quotes = part.quotes.filter(status='submitted')
            
            part_details.append({
                'part': part,
                'market_average': market_avg,
                'quotes': quotes,
                'lowest_quote': quotes.order_by('total_cost').first(),
            })
        except PartMarketAverage.DoesNotExist:
            continue
    
    context = {
        'assessment': assessment,
        'summary': summary,
        'part_details': part_details,
        'provider_comparison': summary.get_provider_comparison(),
    }
    
    return render(request, 'insurance_app/quote_summary.html', context)
```

---

## Usage Scenarios

### Scenario 1: New Assessment with Multiple Damaged Parts

**Situation**: A Toyota Camry has been in a front-end collision affecting multiple parts.

**Parts Identified**:
- Front bumper (body panel - replace)
- Headlight assembly left (electrical - replace)
- Hood (body panel - repair & paint)
- Radiator (mechanical - replace)
- Front grille (trim - replace)

**Workflow**:

1. **Assessment Completion**
   ```python
   assessment = VehicleAssessment.objects.get(id=123)
   
   # Parts already added during assessment
   damaged_parts = assessment.damaged_parts.all()
   # Returns: 5 parts
   ```

2. **Initiate Quote Request**
   ```python
   workflow = QuoteWorkflowManager(assessment)
   result = workflow.execute_complete_workflow()
   
   # Result: 5 quote requests created, sent to 4 providers each
   # Total: 20 quote requests dispatched
   ```

3. **Quotes Received** (over 24-48 hours)
   ```
   Front Bumper:
   - Assessor: £420 (OEM equivalent, 5 days)
   - Dealer: £580 (OEM, 3 days)
   - Independent: £350 (Aftermarket, 4 days)
   - Network: £390 (OEM equivalent, 4 days)
   
   Headlight Assembly:
   - Assessor: £280 (OEM equivalent, 3 days)
   - Dealer: £350 (OEM, 2 days)
   - Independent: £220 (Aftermarket, 3 days)
   - Network: £260 (OEM equivalent, 3 days)
   
   [Similar for other parts...]
   ```

4. **Market Average Calculated**
   ```python
   calculate_all_part_averages(assessment)
   
   # Results:
   # Front Bumper: £435 average (variance 39.5%)
   # Headlight: £277.50 average (variance 37.1%)
   # Hood: £680 average (variance 23.5%)
   # Radiator: £425 average (variance 18.8%)
   # Grille: £145 average (variance 31.0%)
   
   # Total Market Average: £1,962.50
   ```

5. **Recommendation Generated**
   ```python
   engine = QuoteRecommendationEngine(assessment)
   summary = engine.generate_recommendation()
   
   # Recommendation: Insurance Network
   # Total: £1,795
   # Savings vs highest: £415 (18.8%)
   # Scores:
   #   - Price: 92/100
   #   - Quality: 85/100
   #   - Timeline: 80/100
   #   - Warranty: 70/100
   #   - Reliability: 90/100
   # Overall: 87.5/100
   ```

### Scenario 2: High-End Vehicle with Premium Parts

**Situation**: A Mercedes-Benz S-Class requires specialized parts.

**Characteristics**:
- OEM parts strongly preferred
- Dealer network required for warranty
- Quality over price priority

**Custom Recommendation Strategy**:
```python
# Use highest quality strategy instead of best value
result = RecommendationStrategy.highest_quality(assessment)

# Result: Authorized Dealer recommended
# Reasoning: 
# - 100% OEM parts
# - Manufacturer certification maintained
# - Extended warranty coverage
# - Even though 25% more expensive than market average
```

### Scenario 3: Insurance Claim with Budget Constraints

**Situation**: Customer has limited coverage, needs most economical option.

**Strategy**:
```python
# Use lowest price strategy
result = RecommendationStrategy.lowest_price(assessment)

# Result: Independent Garage recommended
# Total: £1,450
# Savings: £512.50 below market average (26.1%)
# Notes: Aftermarket parts, 12-month warranty
```

### Scenario 4: Urgent Repair Required

**Situation**: Customer needs vehicle back as soon as possible.

**Strategy**:
```python
# Use fastest completion strategy
result = RecommendationStrategy.fastest_completion(assessment)

# Result: Dealer recommended
# Completion: 3 days average
# Parts in stock, priority service available
# Even though 18% above market average
```

### Scenario 5: Part-by-Part Selection (Hybrid Approach)

**Situation**: Customer wants to mix and match providers for different parts.

**Implementation**:
```python
def create_hybrid_quote(assessment):
    """Allow selection of different providers for different parts"""
    
    selections = {
        'Front Bumper': 'independent',  # Lowest cost
        'Headlight': 'network',         # Good balance
        'Hood': 'dealer',               # Complex repair, want OEM
        'Radiator': 'network',          # Mechanical, want warranty
        'Grille': 'independent',        # Simple part, save money
    }
    
    total_cost = 0
    for part in assessment.damaged_parts.all():
        provider = selections.get(part.part_name)
        quote = part.quotes.filter(provider_type=provider).first()
        if quote:
            total_cost += float(quote.total_cost)
    
    return {
        'hybrid_total': total_cost,
        'selections': selections,
        'potential_savings': 'Optimized per part'
    }

# Result: £1,680 total
# 14.4% below market average
# Mix of quality and value
```

---

## Advanced Features

### 1. Historical Price Trending

```python
class PartPriceTrend(models.Model):
    """Track historical pricing for parts over time"""
    
    part_name = models.CharField(max_length=200)
    vehicle_make = models.CharField(max_length=100)
    vehicle_model = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20)
    
    average_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quote_count = models.IntegerField()
    period_start = models.DateField()
    period_end = models.DateField()
    
    class Meta:
        indexes = [
            models.Index(fields=['part_name', 'vehicle_make', 'period_end']),
        ]
    
    @staticmethod
    def analyze_trend(part_name, vehicle_make, months=6):
        """Analyze price trend for a specific part"""
        trends = PartPriceTrend.objects.filter(
            part_name=part_name,
            vehicle_make=vehicle_make,
            period_end__gte=timezone.now() - timedelta(days=months*30)
        ).order_by('period_end')
        
        if trends.count() < 2:
            return None
        
        prices = [float(t.average_cost) for t in trends]
        
        # Calculate trend
        first_price = prices[0]
        last_price = prices[-1]
        change = last_price - first_price
        change_pct = (change / first_price) * 100
        
        return {
            'trend_direction': 'increasing' if change > 0 else 'decreasing',
            'change_amount': change,
            'change_percentage': change_pct,
            'current_price': last_price,
            'historical_low': min(prices),
            'historical_high': max(prices),
        }
```

### 2. Provider Performance Tracking

```python
class ProviderPerformance(models.Model):
    """Track provider performance metrics"""
    
    provider_type = models.CharField(max_length=20)
    provider_name = models.CharField(max_length=200)
    
    # Performance metrics
    total_quotes_submitted = models.IntegerField(default=0)
    average_response_time_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )
    quotes_accepted = models.IntegerField(default=0)
    quotes_rejected = models.IntegerField(default=0)
    
    # Quality metrics
    average_customer_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True
    )
    completion_on_time_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    warranty_claim_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    
    # Pricing metrics
    average_competitiveness_score = models.IntegerField()
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def calculate_reliability_score(self):
        """Calculate overall reliability score (0-100)"""
        scores = []
        
        # Response time score
        if self.average_response_time_hours <= 24:
            scores.append(100)
        elif self.average_response_time_hours <= 48:
            scores.append(80)
        else:
            scores.append(60)
        
        # Acceptance rate score
        if self.total_quotes_submitted > 0:
            acceptance_rate = (self.quotes_accepted / self.total_quotes_submitted) * 100
            scores.append(acceptance_rate)
        
        # On-time completion score
        scores.append(float(self.completion_on_time_rate))
        
        # Customer rating score
        if self.average_customer_rating:
            scores.append(float(self.average_customer_rating) * 20)  # Convert 5-star to 100
        
        return round(sum(scores) / len(scores), 2) if scores else 0
```

### 3. Smart Quote Request Optimization

```python
class SmartQuoteOptimizer:
    """Optimize which providers to contact based on historical data"""
    
    @staticmethod
    def select_optimal_providers(damaged_part):
        """Select best providers to contact for a specific part"""
        
        # Get historical performance for this part type
        part_category = damaged_part.part_category
        vehicle_make = damaged_part.assessment.vehicle.make
        
        provider_scores = {}
        
        for provider_type in ['dealer', 'independent', 'network']:
            # Calculate score based on:
            # - Response rate for similar parts
            # - Price competitiveness
            # - Quality ratings
            # - Availability of parts
            
            score = SmartQuoteOptimizer._calculate_provider_score(
                provider_type,
                part_category,
                vehicle_make
            )
            
            provider_scores[provider_type] = score
        
        # Return top 3 providers
        sorted_providers = sorted(
            provider_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return [p[0] for p in sorted_providers]
    
    @staticmethod
    def _calculate_provider_score(provider_type, part_category, vehicle_make):
        """Calculate provider score for specific part"""
        
        # This would use historical data
        # Simplified example:
        base_scores = {
            'dealer': 85,
            'independent': 75,
            'network': 80,
        }
        
        return base_scores.get(provider_type, 70)
```

---

## System Benefits

### For Insurance Companies

1. **Cost Savings**: Average 15-25% savings through competitive quotes
2. **Transparency**: Clear breakdown of all repair costs
3. **Quality Assurance**: Multiple providers ensure competitive quality
4. **Data-Driven**: Market averages based on real data, not estimates
5. **Efficiency**: Automated quote collection reduces manual work
6. **Compliance**: Documented quote process for regulatory requirements

### For Customers

1. **Choice**: Multiple repair options at different price points
2. **Confidence**: Market average provides price validation
3. **Speed**: Faster quote collection and comparison
4. **Quality Options**: Can choose between OEM, equivalent, or aftermarket
5. **Transparency**: See exactly what they're paying for

### For Repair Providers

1. **More Business**: Access to insurance claim work
2. **Fair Competition**: Compete on price and quality
3. **Streamlined Process**: Automated quote requests
4. **Performance Tracking**: Build reputation through quality work

---

## Technical Requirements

### Infrastructure

- **Database**: PostgreSQL 12+ (for JSON fields and advanced queries)
- **Cache**: Redis (for quote request tracking)
- **Queue**: Celery (for async quote dispatch)
- **Storage**: S3-compatible (for damage images)
- **API Gateway**: For provider integrations

### Scalability Considerations

- Async processing for quote requests (handle 1000s simultaneously)
- Database indexing on frequently queried fields
- Caching of market averages and provider scores
- Rate limiting on API endpoints
- Load balancing for high traffic

### Security

- API authentication for provider endpoints
- Encryption of sensitive quote data
- Audit logging of all quote transactions
- Role-based access control
- GDPR compliance for customer data

---

## Future Enhancements

1. **AI-Powered Estimation**: Machine learning for more accurate assessor estimates
2. **Real-time Pricing**: Live pricing updates from suppliers
3. **Parts Marketplace**: Direct parts ordering integration
4. **Mobile App**: Provider mobile app for on-site quoting
5. **Blockchain**: Immutable quote history and tracking
6. **Predictive Analytics**: Forecast part price trends
7. **Customer Portal**: Self-service quote comparison
8. **Integration Hub**: Connect with more provider networks

---

*Document Version: 1.0*  
*Last Updated: December 2024*  
*System Status: Design Phase*