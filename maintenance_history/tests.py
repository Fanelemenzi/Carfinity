from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from maintenance.models import Part, ScheduledMaintenance
from vehicles.models import Vehicle
from .models import MaintenanceRecord, PartUsage
from .forms import MaintenanceRecordForm
import json
from decimal import Decimal


class PartSearchAPIViewTests(TestCase):
    """Test cases for PartSearchAPIView"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test parts
        self.part1 = Part.objects.create(
            name="Oil Filter",
            part_number="OF-123",
            description="High quality oil filter",
            manufacturer="FilterCorp",
            category="Filters",
            cost=15.99,
            stock_quantity=50,
            minimum_stock_level=10
        )
        
        self.part2 = Part.objects.create(
            name="Air Filter",
            part_number="AF-456",
            description="Premium air filter",
            manufacturer="FilterCorp",
            category="Filters",
            cost=25.50,
            stock_quantity=3,  # Low stock
            minimum_stock_level=5
        )
        
        self.part3 = Part.objects.create(
            name="Brake Pad",
            part_number="BP-789",
            description="Ceramic brake pads",
            manufacturer="BrakeCorp",
            category="Brakes",
            cost=89.99,
            stock_quantity=20,
            minimum_stock_level=5
        )
        
        self.part4 = Part.objects.create(
            name="Engine Oil",
            part_number="EO-101",
            description="Synthetic engine oil",
            manufacturer="OilCorp",
            category="Fluids",
            cost=12.99,
            stock_quantity=100,
            minimum_stock_level=20
        )
    
    def test_search_without_query(self):
        """Test searching without any query parameters returns all parts"""
        url = reverse('part_search_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('results', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['results']), 4)
        self.assertEqual(data['pagination']['total_count'], 4)
    
    def test_search_by_name(self):
        """Test searching parts by name"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'q': 'filter'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 2)  # Oil Filter and Air Filter
        part_names = [part['name'] for part in data['results']]
        self.assertIn('Oil Filter', part_names)
        self.assertIn('Air Filter', part_names)
    
    def test_search_by_part_number(self):
        """Test searching parts by part number"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'q': 'OF-123'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Oil Filter')
        self.assertEqual(data['results'][0]['part_number'], 'OF-123')
    
    def test_search_by_description(self):
        """Test searching parts by description"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'q': 'ceramic'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Brake Pad')
    
    def test_filter_by_category(self):
        """Test filtering parts by category"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'category': 'Filters'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 2)
        for part in data['results']:
            self.assertEqual(part['category'], 'Filters')
    
    def test_combined_search_and_filter(self):
        """Test combining search query with category filter"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'q': 'oil', 'category': 'Filters'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Oil Filter')
    
    def test_pagination_default(self):
        """Test default pagination settings"""
        url = reverse('part_search_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        pagination = data['pagination']
        self.assertEqual(pagination['page'], 1)
        self.assertEqual(pagination['total_count'], 4)
        self.assertEqual(pagination['total_pages'], 1)
        self.assertFalse(pagination['has_next'])
        self.assertFalse(pagination['has_previous'])
    
    def test_pagination_custom_page_size(self):
        """Test custom page size"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'page_size': '2'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 2)
        pagination = data['pagination']
        self.assertEqual(pagination['total_pages'], 2)
        self.assertTrue(pagination['has_next'])
        self.assertFalse(pagination['has_previous'])
    
    def test_pagination_second_page(self):
        """Test accessing second page"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'page_size': '2', 'page': '2'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 2)
        pagination = data['pagination']
        self.assertEqual(pagination['page'], 2)
        self.assertFalse(pagination['has_next'])
        self.assertTrue(pagination['has_previous'])
    
    def test_max_page_size_limit(self):
        """Test that page size is limited to maximum value"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'page_size': '200'})  # Request more than max
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Should still return all 4 parts since we have less than 100
        self.assertEqual(len(data['results']), 4)
    
    def test_part_data_structure(self):
        """Test that part data includes all required fields"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'q': 'Oil Filter'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        part = data['results'][0]
        required_fields = [
            'id', 'name', 'part_number', 'description', 'manufacturer',
            'category', 'cost', 'stock_quantity', 'minimum_stock_level', 'is_low_stock'
        ]
        
        for field in required_fields:
            self.assertIn(field, part)
        
        # Test specific values
        self.assertEqual(part['name'], 'Oil Filter')
        self.assertEqual(part['cost'], '15.99')
        self.assertEqual(part['stock_quantity'], 50)
        self.assertFalse(part['is_low_stock'])
    
    def test_low_stock_indication(self):
        """Test that low stock parts are properly indicated"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'q': 'Air Filter'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        part = data['results'][0]
        self.assertTrue(part['is_low_stock'])
        self.assertEqual(part['stock_quantity'], 3)
        self.assertEqual(part['minimum_stock_level'], 5)
    
    def test_no_results_found(self):
        """Test response when no parts match the search"""
        url = reverse('part_search_api')
        response = self.client.get(url, {'q': 'nonexistent'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['results']), 0)
        self.assertEqual(data['pagination']['total_count'], 0)


class PartDetailsAPIViewTests(TestCase):
    """Test cases for PartDetailsAPIView"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test part
        self.part = Part.objects.create(
            name="Test Part",
            part_number="TP-001",
            description="A test part for unit testing",
            manufacturer="TestCorp",
            category="Testing",
            cost=99.99,
            stock_quantity=25,
            minimum_stock_level=10
        )
    
    def test_get_existing_part(self):
        """Test retrieving details for an existing part"""
        url = reverse('part_details_api', kwargs={'part_id': self.part.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('part', data)
        part_data = data['part']
        
        # Check all required fields are present
        required_fields = [
            'id', 'name', 'part_number', 'description', 'manufacturer',
            'category', 'cost', 'stock_quantity', 'minimum_stock_level',
            'is_low_stock', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, part_data)
        
        # Check specific values
        self.assertEqual(part_data['id'], self.part.id)
        self.assertEqual(part_data['name'], 'Test Part')
        self.assertEqual(part_data['part_number'], 'TP-001')
        self.assertEqual(part_data['cost'], '99.99')
        self.assertEqual(part_data['stock_quantity'], 25)
        self.assertFalse(part_data['is_low_stock'])
    
    def test_get_nonexistent_part(self):
        """Test retrieving details for a non-existent part"""
        url = reverse('part_details_api', kwargs={'part_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Part not found')
    
    def test_part_with_null_cost(self):
        """Test retrieving part with null cost"""
        part_no_cost = Part.objects.create(
            name="Free Part",
            part_number="FP-001",
            cost=None,  # No cost set
            stock_quantity=10
        )
        
        url = reverse('part_details_api', kwargs={'part_id': part_no_cost.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        part_data = data['part']
        self.assertIsNone(part_data['cost'])
    
    def test_low_stock_part_details(self):
        """Test retrieving details for a low stock part"""
        low_stock_part = Part.objects.create(
            name="Low Stock Part",
            part_number="LSP-001",
            stock_quantity=2,
            minimum_stock_level=5
        )
        
        url = reverse('part_details_api', kwargs={'part_id': low_stock_part.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        part_data = data['part']
        self.assertTrue(part_data['is_low_stock'])
        self.assertEqual(part_data['stock_quantity'], 2)
        self.assertEqual(part_data['minimum_stock_level'], 5)
    
    def test_datetime_fields_format(self):
        """Test that datetime fields are properly formatted"""
        url = reverse('part_details_api', kwargs={'part_id': self.part.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        part_data = data['part']
        
        # Check that datetime fields are in ISO format
        self.assertIsInstance(part_data['created_at'], str)
        self.assertIsInstance(part_data['updated_at'], str)
        
        # Basic format check (should contain 'T' for ISO format)
        self.assertIn('T', part_data['created_at'])
        self.assertIn('T', part_data['updated_at'])


class MaintenanceRecordFormTests(TestCase):
    """Test cases for enhanced MaintenanceRecordForm with part selection"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testtech',
            email='tech@test.com',
            password='testpass123'
        )
        
        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            vin='1HGBH41JXMN109186',
            license_plate='TEST123',
            make='Toyota',
            model='Camry',
            year=2020,
            color='Blue'
        )
        
        # Create test parts
        self.part1 = Part.objects.create(
            name="Oil Filter",
            part_number="OF-123",
            description="High quality oil filter",
            manufacturer="FilterCorp",
            category="Filters",
            cost=Decimal('15.99'),
            stock_quantity=50,
            minimum_stock_level=10
        )
        
        self.part2 = Part.objects.create(
            name="Air Filter",
            part_number="AF-456",
            description="Premium air filter",
            manufacturer="FilterCorp",
            category="Filters",
            cost=Decimal('25.50'),
            stock_quantity=3,  # Low stock
            minimum_stock_level=5
        )
        
        self.part3 = Part.objects.create(
            name="Brake Pad",
            part_number="BP-789",
            description="Ceramic brake pads",
            manufacturer="BrakeCorp",
            category="Brakes",
            cost=Decimal('89.99'),
            stock_quantity=20,
            minimum_stock_level=5
        )
        
        # Base form data
        self.base_form_data = {
            'vehicle': self.vehicle.id,
            'work_done': 'Oil change and filter replacement',
            'mileage': 50000,
            'notes': 'Regular maintenance'
        }
    
    def test_form_without_parts_data(self):
        """Test form submission without any parts data"""
        form = MaintenanceRecordForm(data=self.base_form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.selected_parts), 0)
        
        # Test save without parts
        record = form.save()
        self.assertIsInstance(record, MaintenanceRecord)
        self.assertEqual(record.parts_used.count(), 0)
    
    def test_form_with_valid_parts_data(self):
        """Test form submission with valid parts data"""
        parts_data = [
            {'id': self.part1.id, 'quantity': 2},
            {'id': self.part3.id, 'quantity': 1}
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.selected_parts), 2)
        
        # Check selected parts structure
        selected_part1 = form.selected_parts[0]
        self.assertEqual(selected_part1['part'], self.part1)
        self.assertEqual(selected_part1['quantity'], 2)
        self.assertEqual(selected_part1['unit_cost'], self.part1.cost)
        
        selected_part2 = form.selected_parts[1]
        self.assertEqual(selected_part2['part'], self.part3)
        self.assertEqual(selected_part2['quantity'], 1)
        self.assertEqual(selected_part2['unit_cost'], self.part3.cost)
    
    def test_form_with_invalid_json_parts_data(self):
        """Test form validation with invalid JSON in parts_data"""
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = 'invalid json'
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('parts_data', form.errors)
        self.assertIn('Invalid parts data format', str(form.errors['parts_data']))
    
    def test_form_with_non_list_parts_data(self):
        """Test form validation when parts_data is not a list"""
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps({'not': 'a list'})
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('parts_data', form.errors)
        self.assertIn('Parts data must be a list', str(form.errors['parts_data']))
    
    def test_form_with_invalid_part_entry_structure(self):
        """Test form validation with invalid part entry structure"""
        parts_data = [
            'not a dict',
            {'id': self.part1.id, 'quantity': 1}
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('parts_data', form.errors)
        self.assertIn('Each part entry must be an object', str(form.errors['parts_data']))
    
    def test_form_with_missing_required_fields(self):
        """Test form validation with missing required fields in part data"""
        parts_data = [
            {'id': self.part1.id},  # Missing quantity
            {'quantity': 2}  # Missing id
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('parts_data', form.errors)
        self.assertIn('Missing required field', str(form.errors['parts_data']))
    
    def test_form_with_nonexistent_part(self):
        """Test form validation with non-existent part ID"""
        parts_data = [
            {'id': 99999, 'quantity': 1}  # Non-existent part ID
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('parts_data', form.errors)
        self.assertIn('Part with ID 99999 does not exist', str(form.errors['parts_data']))
    
    def test_form_with_invalid_quantity(self):
        """Test form validation with invalid quantity values"""
        test_cases = [
            {'id': self.part1.id, 'quantity': 0},      # Zero quantity
            {'id': self.part1.id, 'quantity': -1},     # Negative quantity
            {'id': self.part1.id, 'quantity': 'abc'},  # Non-numeric quantity
            {'id': self.part1.id, 'quantity': None},   # None quantity
        ]
        
        for parts_data in test_cases:
            with self.subTest(quantity=parts_data['quantity']):
                form_data = self.base_form_data.copy()
                form_data['parts_data'] = json.dumps([parts_data])
                
                form = MaintenanceRecordForm(data=form_data)
                
                self.assertFalse(form.is_valid())
                self.assertIn('parts_data', form.errors)
    
    def test_form_with_insufficient_stock(self):
        """Test form validation with insufficient stock"""
        parts_data = [
            {'id': self.part2.id, 'quantity': 5}  # part2 has only 3 in stock
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('parts_data', form.errors)
        self.assertIn('Insufficient stock for Air Filter', str(form.errors['parts_data']))
        self.assertIn('Available: 3, Requested: 5', str(form.errors['parts_data']))
    
    def test_form_save_creates_part_usage_records(self):
        """Test that form save creates PartUsage records and updates inventory"""
        parts_data = [
            {'id': self.part1.id, 'quantity': 2},
            {'id': self.part3.id, 'quantity': 1}
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Store original stock quantities
        original_part1_stock = self.part1.stock_quantity
        original_part3_stock = self.part3.stock_quantity
        
        # Save the form
        record = form.save()
        
        # Check that PartUsage records were created
        self.assertEqual(record.parts_used.count(), 2)
        
        part_usage1 = record.parts_used.get(part=self.part1)
        self.assertEqual(part_usage1.quantity, 2)
        self.assertEqual(part_usage1.unit_cost, self.part1.cost)
        
        part_usage2 = record.parts_used.get(part=self.part3)
        self.assertEqual(part_usage2.quantity, 1)
        self.assertEqual(part_usage2.unit_cost, self.part3.cost)
        
        # Check that inventory was updated
        self.part1.refresh_from_db()
        self.part3.refresh_from_db()
        
        self.assertEqual(self.part1.stock_quantity, original_part1_stock - 2)
        self.assertEqual(self.part3.stock_quantity, original_part3_stock - 1)
    
    def test_form_save_transaction_rollback_on_error(self):
        """Test that form save rolls back on error"""
        # Mock the reduce_stock method to fail
        original_reduce_stock = Part.reduce_stock
        
        def failing_reduce_stock(self, quantity):
            if self.id == self.part1.id:
                return False  # Simulate failure
            return original_reduce_stock(self, quantity)
        
        Part.reduce_stock = failing_reduce_stock
        
        try:
            parts_data = [
                {'id': self.part1.id, 'quantity': 1},
                {'id': self.part3.id, 'quantity': 1}
            ]
            
            form_data = self.base_form_data.copy()
            form_data['parts_data'] = json.dumps(parts_data)
            
            form = MaintenanceRecordForm(data=form_data)
            self.assertTrue(form.is_valid())
            
            # This should raise a ValidationError due to stock reduction failure
            with self.assertRaises(ValidationError) as context:
                form.save()
            
            self.assertIn('Failed to update stock for Oil Filter', str(context.exception))
            
            # Check that no MaintenanceRecord was created
            self.assertEqual(MaintenanceRecord.objects.count(), 0)
            
            # Check that no PartUsage records were created
            self.assertEqual(PartUsage.objects.count(), 0)
            
        finally:
            # Restore original method
            Part.reduce_stock = original_reduce_stock
    
    def test_form_save_without_commit(self):
        """Test form save with commit=False"""
        parts_data = [
            {'id': self.part1.id, 'quantity': 1}
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Save without commit
        record = form.save(commit=False)
        
        # Record should be created but not saved to database
        self.assertIsInstance(record, MaintenanceRecord)
        self.assertIsNone(record.id)
        
        # No PartUsage records should be created
        self.assertEqual(PartUsage.objects.count(), 0)
        
        # Stock should not be updated
        original_stock = self.part1.stock_quantity
        self.part1.refresh_from_db()
        self.assertEqual(self.part1.stock_quantity, original_stock)
    
    def test_get_selected_parts_summary(self):
        """Test get_selected_parts_summary method"""
        parts_data = [
            {'id': self.part1.id, 'quantity': 2},
            {'id': self.part3.id, 'quantity': 1}
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        summary = form.get_selected_parts_summary()
        
        self.assertIn('parts', summary)
        self.assertIn('total_cost', summary)
        
        parts = summary['parts']
        self.assertEqual(len(parts), 2)
        
        # Check first part summary
        part1_summary = parts[0]
        self.assertEqual(part1_summary['name'], 'Oil Filter')
        self.assertEqual(part1_summary['part_number'], 'OF-123')
        self.assertEqual(part1_summary['quantity'], 2)
        self.assertEqual(part1_summary['unit_cost'], Decimal('15.99'))
        self.assertEqual(part1_summary['line_total'], Decimal('31.98'))
        
        # Check second part summary
        part2_summary = parts[1]
        self.assertEqual(part2_summary['name'], 'Brake Pad')
        self.assertEqual(part2_summary['part_number'], 'BP-789')
        self.assertEqual(part2_summary['quantity'], 1)
        self.assertEqual(part2_summary['unit_cost'], Decimal('89.99'))
        self.assertEqual(part2_summary['line_total'], Decimal('89.99'))
        
        # Check total cost
        expected_total = Decimal('31.98') + Decimal('89.99')
        self.assertEqual(summary['total_cost'], expected_total)
    
    def test_get_selected_parts_summary_empty(self):
        """Test get_selected_parts_summary with no parts"""
        form = MaintenanceRecordForm(data=self.base_form_data)
        self.assertTrue(form.is_valid())
        
        summary = form.get_selected_parts_summary()
        
        self.assertEqual(summary, [])
    
    def test_get_selected_parts_summary_with_null_cost(self):
        """Test get_selected_parts_summary with parts having null cost"""
        # Create part with null cost
        part_no_cost = Part.objects.create(
            name="Free Part",
            part_number="FP-001",
            cost=None,
            stock_quantity=10
        )
        
        parts_data = [
            {'id': part_no_cost.id, 'quantity': 2}
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        summary = form.get_selected_parts_summary()
        
        parts = summary['parts']
        self.assertEqual(len(parts), 1)
        
        part_summary = parts[0]
        self.assertIsNone(part_summary['unit_cost'])
        self.assertEqual(part_summary['line_total'], 0)
        self.assertEqual(summary['total_cost'], 0)
    
    def test_form_initialization(self):
        """Test form initialization sets up selected_parts correctly"""
        form = MaintenanceRecordForm()
        
        self.assertEqual(form.selected_parts, [])
        self.assertIn('parts_data', form.fields)
        self.assertTrue(form.fields['parts_data'].widget.is_hidden)
        self.assertFalse(form.fields['parts_data'].required)
    
    def test_form_with_edge_case_quantities(self):
        """Test form with edge case quantities"""
        # Test with maximum reasonable quantity
        parts_data = [
            {'id': self.part1.id, 'quantity': self.part1.stock_quantity}  # Use all available stock
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        # Save and verify stock is completely depleted
        record = form.save()
        self.part1.refresh_from_db()
        self.assertEqual(self.part1.stock_quantity, 0)
    
    def test_concurrent_stock_modification_handling(self):
        """Test handling of concurrent stock modifications"""
        parts_data = [
            {'id': self.part1.id, 'quantity': 5}
        ]
        
        form_data = self.base_form_data.copy()
        form_data['parts_data'] = json.dumps(parts_data)
        
        form = MaintenanceRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Simulate concurrent modification by reducing stock after validation
        self.part1.stock_quantity = 2
        self.part1.save()
        
        # This should fail during save due to insufficient stock
        with self.assertRaises(ValidationError) as context:
            form.save()
        
        self.assertIn('Failed to update stock', str(context.exception))
        self.assertIn('concurrent modifications', str(context.exception))
