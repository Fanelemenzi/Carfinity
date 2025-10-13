<!-- 8cf44739-b5c6-4516-9833-0c4089d64081 59f78954-0536-43a6-b818-4280bdd07b06 -->
# Add Vehicle Dropdown Selector to AutoCare Dashboard

## Implementation Steps

### 1. Update Template (`templates/dashboard/autocare_dashboard.html`)

**Location**: Lines 48-64 (Header section)

Add a vehicle dropdown selector next to the existing header buttons:

- Position dropdown after the user greeting, before notification/settings buttons
- Display format: "2020 Toyota Camry" style
- Include "active" state styling for current vehicle
- Add loading state indicator for AJAX updates

**Template changes**:

```html
<!-- Add vehicle selector dropdown in header (around line 54) -->
<div class="flex items-center gap-3">
  {% if user_vehicles and user_vehicles|length > 1 %}
    <select id="vehicle-selector" class="px-4 py-2 bg-white rounded-lg shadow-md border border-gray-200">
      {% for v in user_vehicles %}
        <option value="{{ v.id }}" {% if vehicle and v.id == vehicle.id %}selected{% endif %}>
          {{ v.manufacture_year }} {{ v.make }} {{ v.model }}
        </option>
      {% endfor %}
    </select>
  {% endif %}
  <!-- existing bell and settings buttons -->
</div>
```

### 2. Add JavaScript for AJAX Vehicle Switching

**Location**: End of template (before `{% endblock %}` at line 338)

Create JavaScript to:

- Listen for vehicle selector change events
- Fetch dashboard data from API endpoint (`/notifications/api/dashboard/<vehicle_id>/`)
- Update all dashboard sections with new data
- Handle loading states and errors gracefully
- Update browser URL without reload using `history.pushState()`

**Key functions**:

- `handleVehicleChange()` - triggered on dropdown change
- `fetchDashboardData(vehicleId)` - AJAX call to API
- `updateDashboardUI(data)` - populate UI with fetched data
- `showLoadingState()` / `hideLoadingState()` - visual feedback
- Helper functions for each dashboard section update

### 3. Verify API Endpoint (`notifications/views.py`)

**Location**: Lines 199-297 (`DashboardAPIView`)

The existing `DashboardAPIView` already provides:

- Complete dashboard data at `/notifications/api/dashboard/<vehicle_id>/`
- Vehicle ownership validation
- All required data sections (overview, maintenance, alerts, history, costs, valuation)

**No changes needed** - API is already functional and returns proper JSON response.

### 4. Update Context Data Handling (`notifications/views.py`)

**Location**: Lines 95-100 (in `get_context_data`)

Verify that `user_vehicles` is properly fetched and passed to template:

```python
user_vehicles = ErrorHandler.handle_data_retrieval(
    lambda: self.get_user_vehicles(),
    fallback_value=[],
    error_message="Failed to load user vehicles list"
)
```

**Already implemented** - just verify it's working correctly.

### 5. Add Dynamic Content Update Functions

**JavaScript implementation details**:

Map API response fields to template sections:

- Vehicle overview (lines 73-123)
- Upcoming maintenance (lines 128-174)
- Alerts (lines 177-209)
- Service history table (lines 220-242)
- Valuation card (lines 261-272)
- Cost analytics (lines 275-293)
- Statistics (lines 296-315)

Update strategy:

- Use `innerHTML` for simple text replacements
- Rebuild table rows for service history
- Update alert lists dynamically
- Preserve existing Tailwind classes and structure

### 6. Error Handling & Edge Cases

Handle scenarios:

- User with only 1 vehicle: Don't show dropdown
- User with 0 vehicles: Show existing "No Vehicle Found" message
- API errors: Show error message, keep current data visible
- Network timeouts: Graceful fallback with retry option
- Loading state: Disable dropdown during fetch, show spinner

## Files to Modify

1. **templates/dashboard/autocare_dashboard.html**

   - Add vehicle selector dropdown in header
   - Add JavaScript for AJAX functionality
   - Add loading overlay/spinner

## Technical Details

- **API Endpoint**: `/notifications/api/dashboard/<vehicle_id>/` (already exists)
- **URL Update**: Use `history.pushState()` to update URL to `/notifications/dashboard/<vehicle_id>/`
- **Data Format**: API returns JSON with all dashboard sections
- **Vehicle Display**: `{{ manufacture_year }} {{ make }} {{ model }}` format
- **Backward Compatibility**: Single-vehicle users see no dropdown, multi-vehicle users get selector

## Benefits

- No page reloads - smooth UX
- Leverages existing API infrastructure
- Graceful degradation for errors
- URL updates allow bookmarking specific vehicle views
- Minimal backend changes needed

### To-dos

- [ ] Add vehicle selector dropdown to dashboard header with proper styling and conditional rendering
- [ ] Implement JavaScript AJAX handler to fetch dashboard data when vehicle selection changes
- [ ] Create JavaScript functions to update each dashboard section with fetched data
- [ ] Add loading indicators and error handling for vehicle switching
- [ ] Test vehicle switching with multiple vehicles and verify all data updates correctly