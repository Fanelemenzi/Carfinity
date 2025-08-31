# Design Document

## Overview

This design enhances the existing maintenance record creation form to include comprehensive part selection and tracking capabilities. The solution builds upon the existing `PartUsage` model and integrates with the current `Part` model to provide technicians with an intuitive interface for selecting parts, tracking quantities, and managing inventory during service operations.

## Architecture

### Frontend Components

**Part Selection Interface**
- Dynamic part search and filter component
- Selected parts management table
- Real-time cost calculation display
- Stock validation and warnings

**Form Integration**
- Enhanced MaintenanceRecordForm with part selection
- JavaScript-based dynamic part management
- AJAX endpoints for part search and validation
- Form validation including part requirements

### Backend Components

**Enhanced Form Processing**
- Extended MaintenanceRecordForm to handle part data
- Custom form validation for part quantities and stock
- Transaction-based record creation to ensure data consistency

**API Endpoints**
- Part search and filtering endpoint
- Stock validation endpoint
- Part details retrieval endpoint

**Inventory Management**
- Automatic stock level updates on record creation
- Low stock threshold monitoring
- Part usage tracking and reporting

## Components and Interfaces

### 1. Enhanced MaintenanceRecordForm

```python
class MaintenanceRecordForm(forms.ModelForm):
    # Existing fields remain unchanged
    # New part-related functionality handled via JavaScript and formsets
    
    def __init__(self, *args, **kwargs):
        # Initialize form with part selection capabilities
        
    def clean(self):
        # Validate part quantities against available stock
        
    def save(self, commit=True):
        # Create maintenance record and associated part usage records
```

### 2. Part Selection JavaScript Component

```javascript
class PartSelector {
    constructor(containerId) {
        // Initialize part selection interface
    }
    
    searchParts(query) {
        // AJAX search for parts with filtering
    }
    
    addPart(partId, quantity) {
        // Add part to selection with validation
    }
    
    removePart(partId) {
        // Remove part from selection
    }
    
    validateStock(partId, quantity) {
        // Validate requested quantity against available stock
    }
    
    calculateTotal() {
        // Calculate total cost of selected parts
    }
}
```

### 3. API Views

```python
class PartSearchAPIView(APIView):
    def get(self, request):
        # Return filtered parts based on search query
        
class PartStockValidationAPIView(APIView):
    def post(self, request):
        # Validate part quantities against current stock
        
class PartDetailsAPIView(APIView):
    def get(self, request, part_id):
        # Return detailed part information including stock and cost
```

### 4. Enhanced Part Model Integration

The existing `Part` model will be extended with inventory tracking:

```python
# Addition to existing Part model
class Part(models.Model):
    # Existing fields...
    stock_quantity = models.PositiveIntegerField(default=0)
    minimum_stock_level = models.PositiveIntegerField(default=5)
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.minimum_stock_level
        
    def reduce_stock(self, quantity):
        # Safely reduce stock with validation
```

## Data Models

### Enhanced PartUsage Model

The existing `PartUsage` model already provides the necessary structure:

```python
class PartUsage(models.Model):
    maintenance_record = models.ForeignKey(MaintenanceRecord, on_delete=models.CASCADE, related_name='parts_used')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='usage_records')
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    
    # Additional methods for cost calculation and validation
```

### Form Data Structure

```javascript
// JavaScript data structure for part selection
const selectedParts = [
    {
        id: 1,
        name: "Oil Filter",
        partNumber: "OF-123",
        quantity: 2,
        unitCost: 15.99,
        totalCost: 31.98,
        availableStock: 50
    }
];
```

## Error Handling

### Frontend Error Handling

1. **Stock Validation Errors**
   - Display warning messages for insufficient stock
   - Prevent form submission with invalid quantities
   - Highlight problematic parts in the selection interface

2. **Network Errors**
   - Graceful handling of API failures
   - Retry mechanisms for critical operations
   - User-friendly error messages

3. **Form Validation Errors**
   - Real-time validation feedback
   - Clear error messages for each field
   - Preservation of user input on validation failure

### Backend Error Handling

1. **Database Transaction Management**
   - Atomic operations for record creation and inventory updates
   - Rollback mechanisms for failed operations
   - Proper error logging and monitoring

2. **Stock Management Errors**
   - Validation of part availability before processing
   - Handling of concurrent stock modifications
   - Error responses for insufficient inventory

3. **Data Integrity**
   - Foreign key constraint handling
   - Validation of part-maintenance record relationships
   - Proper cleanup of orphaned records

## Testing Strategy

### Unit Tests

1. **Form Validation Tests**
   - Test part quantity validation against stock levels
   - Test form submission with valid and invalid data
   - Test error message generation and display

2. **Model Tests**
   - Test PartUsage creation and relationships
   - Test inventory update mechanisms
   - Test cost calculation methods

3. **API Endpoint Tests**
   - Test part search functionality with various filters
   - Test stock validation responses
   - Test error handling for invalid requests

### Integration Tests

1. **End-to-End Form Submission**
   - Test complete maintenance record creation with parts
   - Test inventory updates after successful submission
   - Test rollback behavior on submission failures

2. **JavaScript Component Tests**
   - Test part selection interface interactions
   - Test AJAX communication with backend APIs
   - Test real-time cost calculations and validations

### User Acceptance Tests

1. **Technician Workflow Tests**
   - Test typical maintenance record creation scenarios
   - Test part search and selection workflows
   - Test error recovery and form correction processes

2. **Performance Tests**
   - Test form responsiveness with large part inventories
   - Test search performance with extensive part databases
   - Test concurrent user scenarios

## Implementation Considerations

### Security

- CSRF protection for all form submissions and API calls
- User authentication validation for all operations
- Input sanitization for search queries and form data
- Authorization checks for inventory modifications

### Performance

- Efficient database queries for part searches
- Caching of frequently accessed part information
- Optimized JavaScript for real-time interface updates
- Database indexing for part search operations

### Scalability

- Pagination for large part inventories
- Efficient search algorithms for part filtering
- Modular JavaScript components for maintainability
- Database optimization for concurrent operations

### User Experience

- Intuitive part selection interface design
- Real-time feedback for all user actions
- Clear visual indicators for stock levels and costs
- Responsive design for various screen sizes