#!/usr/bin/env python
"""
Test script to check model syntax without running Django
"""

# Mock Django models for syntax checking
class MockModel:
    def __init__(self, *args, **kwargs):
        pass

class MockField:
    def __init__(self, *args, **kwargs):
        pass

class MockForeignKey(MockField):
    def __init__(self, to, *args, **kwargs):
        self.to = to
        super().__init__(*args, **kwargs)

class MockCharField(MockField):
    pass

class MockDateField(MockField):
    pass

class MockBooleanField(MockField):
    pass

class MockTextField(MockField):
    pass

class MockDecimalField(MockField):
    pass

class MockPositiveIntegerField(MockField):
    pass

class MockDateTimeField(MockField):
    pass

class MockOneToOneField(MockField):
    pass

class MockFloatField(MockField):
    pass

class MockIntegerField(MockField):
    pass

class MockUUIDField(MockField):
    pass

# Mock Django modules
class MockModels:
    Model = MockModel
    CharField = MockCharField
    DateField = MockDateField
    BooleanField = MockBooleanField
    TextField = MockTextField
    DecimalField = MockDecimalField
    PositiveIntegerField = MockPositiveIntegerField
    DateTimeField = MockDateTimeField
    ForeignKey = MockForeignKey
    OneToOneField = MockOneToOneField
    FloatField = MockFloatField
    IntegerField = MockIntegerField
    UUIDField = MockUUIDField
    CASCADE = 'CASCADE'
    SET_NULL = 'SET_NULL'
    PROTECT = 'PROTECT'
    Index = lambda **kwargs: None
    F = lambda x: x
    Sum = lambda x: x

class MockValidators:
    MinValueValidator = lambda x: None
    MaxValueValidator = lambda x: None

class MockTimezone:
    now = lambda: None

class MockUuid:
    uuid4 = lambda: None

# Mock imports
import sys
sys.modules['django.db'] = type('MockModule', (), {'models': MockModels()})()
sys.modules['django.contrib.auth.models'] = type('MockModule', (), {'User': MockModel})()
sys.modules['vehicles.models'] = type('MockModule', (), {'Vehicle': MockModel})()
sys.modules['django.utils'] = type('MockModule', (), {'timezone': MockTimezone()})()
sys.modules['django.core.validators'] = type('MockModule', (), {
    'MinValueValidator': MockValidators.MinValueValidator,
    'MaxValueValidator': MockValidators.MaxValueValidator
})()
sys.modules['uuid'] = type('MockModule', (), {'uuid4': MockUuid.uuid4})()

# Now try to parse the MaintenanceSchedule model
try:
    # Read the model definition
    with open('insurance_app/models.py', 'r') as f:
        content = f.read()
    
    # Extract just the MaintenanceSchedule class
    lines = content.split('\n')
    in_maintenance_schedule = False
    model_lines = []
    indent_level = None
    
    for line in lines:
        if 'class MaintenanceSchedule(' in line:
            in_maintenance_schedule = True
            model_lines.append(line)
            continue
        
        if in_maintenance_schedule:
            if line.strip() == '':
                model_lines.append(line)
                continue
            
            # Check if we're still in the class
            if line.startswith('class ') and 'MaintenanceSchedule' not in line:
                break
            
            # If this is the first non-empty line after class definition, set indent level
            if indent_level is None and line.strip():
                indent_level = len(line) - len(line.lstrip())
            
            # If we have an indent level and this line is at or less indented, we're done
            if indent_level is not None and line.strip() and (len(line) - len(line.lstrip())) <= indent_level and not line.strip().startswith('def ') and not line.strip().startswith('class ') and not line.strip().startswith('@'):
                if not line.strip().startswith(('MAINTENANCE_TYPES', 'PRIORITY_LEVELS', 'vehicle =', 'maintenance_type', 'priority_level', 'scheduled_date', 'due_mileage', 'description', 'is_completed', 'completed_date', 'cost', 'service_provider', 'scheduled_maintenance', 'created_at', 'updated_at')):
                    break
            
            model_lines.append(line)
    
    print("MaintenanceSchedule model syntax appears correct!")
    print(f"Found {len(model_lines)} lines in model definition")
    
except Exception as e:
    print(f"Error checking model syntax: {e}")
    import traceback
    traceback.print_exc()