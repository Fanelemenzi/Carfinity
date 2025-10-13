"""
Tests for cost analytics functionality.
"""

from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from vehicles.models import Vehicle
from maintenance_history.models import MaintenanceRecord, PartUsage
from maintenance.models import Part
from notifications.models import VehicleCostAnalytics
from notifications.cost_utils import CostCalculationUtils


class CostCalculationUtilsTestCase(TestCase):
    """Test cases for cost calculation utilities."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            vin='1HGCM82633A123456',
            make='Toyota',
            model='Corolla',
            manufacture_year=2020,
            license_plate='TEST123'
        )
        
        # Create test parts
        self.oil_filter = Part.objects.create(
            name='Oil Filter',
            cost=Decimal('25.99'),
            part_number='OF-123'
        )
        
        self.brake_pads = Part.objects.create(
            name='Brake Pads',
            cost=Decimal('89.99'),
            part_number='BP-456'
        )
        
        # Create test maintenance records
        self.maintenance_record_1 = MaintenanceRecord.objects.create(
            vehicle=self.vehicle,
            technician=self.user,
            work_done='Oil change and filter replacement',
            date_performed=timezone.now() - relativedelta(days=30),
            mileage=50000,
            notes='Regular maintenance'
        )
        
        self.maintenance_record_2 = MaintenanceRecord.objects.create(
            vehicle=self.vehicle,
            technician=self.user,
            work_done='Brake pad replacement',
            date_performed=timezone.now() - relativedelta(days=60),
            mileage=49500,
            notes='Brake maintenance'
        )
        
        # Create part usage records
        PartUsage.objects.create(
            maintenance_record=self.maintenance_record_1,
            part=self.oil_filter,
            quantity=1,
            unit_cost=Decimal('25.99')
        )
        
        PartUsage.objects.create(
            maintenance_record=self.maintenance_record_2,
            part=self.brake_pads,
            quantity=2,
            unit_cost=Decimal('89.99')
        )
    
    def test_calculate_parts_cost(self):
        """Test parts cost calculation for a maintenance record."""
        # Test maintenance record 1 (oil filter)
        parts_cost_1 = CostCalculationUtils.calculate_parts_cost(self.maintenance_record_1)
        self.assertEqual(parts_cost_1, Decimal('25.99'))
        
        # Test maintenance record 2 (brake pads x2)
        parts_cost_2 = CostCalculationUtils.calculate_parts_cost(self.maintenance_record_2)
        self.assertEqual(parts_cost_2, Decimal('179.98'))  # 89.99 * 2
    
    def test_calculate_labor_cost(self):
        """Test labor cost calculation (currently returns 0)."""
        labor_cost = CostCalculationUtils.calculate_labor_cost(self.maintenance_record_1)
        self.assertEqual(labor_cost, Decimal('0.00'))
    
    def test_calculate_total_maintenance_cost(self):
        """Test total maintenance cost calculation."""
        total_cost_1 = CostCalculationUtils.calculate_total_maintenance_cost(self.maintenance_record_1)
        self.assertEqual(total_cost_1, Decimal('25.99'))
        
        total_cost_2 = CostCalculationUtils.calculate_total_maintenance_cost(self.maintenance_record_2)
        self.assertEqual(total_cost_2, Decimal('179.98'))
    
    def test_calculate_monthly_costs(self):
        """Test monthly cost calculation."""
        # Get the month of the first maintenance record
        maintenance_date = self.maintenance_record_1.date_performed.date()
        year = maintenance_date.year
        month = maintenance_date.month
        
        monthly_costs = CostCalculationUtils.calculate_monthly_costs(self.vehicle, year, month)
        
        self.assertEqual(monthly_costs['total_cost'], Decimal('25.99'))
        self.assertEqual(monthly_costs['parts_cost'], Decimal('25.99'))
        self.assertEqual(monthly_costs['labor_cost'], Decimal('0.00'))
        self.assertEqual(monthly_costs['maintenance_cost'], Decimal('25.99'))
    
    def test_calculate_lifetime_costs(self):
        """Test lifetime cost calculation."""
        lifetime_costs = CostCalculationUtils.calculate_lifetime_costs(self.vehicle)
        
        # Should include both maintenance records
        expected_total = Decimal('25.99') + Decimal('179.98')  # 205.97
        
        self.assertEqual(lifetime_costs['lifetime_total_cost'], expected_total)
        self.assertEqual(lifetime_costs['lifetime_parts_cost'], expected_total)
        self.assertEqual(lifetime_costs['lifetime_labor_cost'], Decimal('0.00'))
        self.assertEqual(lifetime_costs['total_maintenance_records'], 2)
    
    def test_calculate_average_monthly_cost(self):
        """Test average monthly cost calculation."""
        # This will calculate average over 12 months, so should be relatively low
        avg_cost = CostCalculationUtils.calculate_average_monthly_cost(self.vehicle, 12)
        
        # Should be total cost divided by 12 months
        expected_avg = (Decimal('25.99') + Decimal('179.98')) / Decimal('12')
        expected_avg = expected_avg.quantize(Decimal('0.01'))
        
        self.assertEqual(avg_cost, expected_avg)
    
    def test_store_monthly_analytics(self):
        """Test storing monthly analytics in database."""
        maintenance_date = self.maintenance_record_1.date_performed.date()
        year = maintenance_date.year
        month = maintenance_date.month
        
        analytics = CostCalculationUtils.store_monthly_analytics(self.vehicle, year, month)
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.vehicle, self.vehicle)
        self.assertEqual(analytics.month, date(year, month, 1))
        self.assertEqual(analytics.total_cost, Decimal('25.99'))
        self.assertEqual(analytics.parts_cost, Decimal('25.99'))
        self.assertEqual(analytics.labor_cost, Decimal('0.00'))
        
        # Verify it was saved to database
        saved_analytics = VehicleCostAnalytics.objects.get(
            vehicle=self.vehicle,
            month=date(year, month, 1)
        )
        self.assertEqual(saved_analytics.total_cost, Decimal('25.99'))
    
    def test_bulk_calculate_analytics(self):
        """Test bulk analytics calculation."""
        count = CostCalculationUtils.bulk_calculate_analytics(self.vehicle, 3)
        
        # Should create analytics for 3 months
        self.assertEqual(count, 3)
        
        # Verify records were created
        analytics_count = VehicleCostAnalytics.objects.filter(vehicle=self.vehicle).count()
        self.assertEqual(analytics_count, 3)
    
    def test_get_cost_trends(self):
        """Test cost trends calculation."""
        trends = CostCalculationUtils.get_cost_trends(self.vehicle, 3)
        
        self.assertEqual(len(trends), 3)
        
        # Each trend should have required fields
        for trend in trends:
            self.assertIn('month', trend)
            self.assertIn('month_name', trend)
            self.assertIn('total_cost', trend)
            self.assertIn('parts_cost', trend)
            self.assertIn('labor_cost', trend)
    
    def test_calculate_cost_by_service_type(self):
        """Test cost calculation by service type."""
        service_costs = CostCalculationUtils.calculate_cost_by_service_type(self.vehicle, 12)
        
        # Should have costs grouped by work_done (since no scheduled maintenance)
        self.assertIn('Oil change and filter replacement', service_costs)
        self.assertIn('Brake pad replacement', service_costs)
        
        self.assertEqual(service_costs['Oil change and filter replacement'], Decimal('25.99'))
        self.assertEqual(service_costs['Brake pad replacement'], Decimal('179.98'))


class VehicleCostAnalyticsModelTestCase(TestCase):
    """Test cases for VehicleCostAnalytics model."""
    
    def setUp(self):
        """Set up test data."""
        self.vehicle = Vehicle.objects.create(
            vin='1HGCM82633A654321',
            make='Honda',
            model='Civic',
            manufacture_year=2019,
            license_plate='TEST456'
        )
    
    def test_create_cost_analytics(self):
        """Test creating cost analytics record."""
        analytics = VehicleCostAnalytics.objects.create(
            vehicle=self.vehicle,
            month=date(2025, 1, 1),
            total_cost=Decimal('150.00'),
            maintenance_cost=Decimal('150.00'),
            parts_cost=Decimal('100.00'),
            labor_cost=Decimal('50.00')
        )
        
        self.assertEqual(analytics.vehicle, self.vehicle)
        self.assertEqual(analytics.total_cost, Decimal('150.00'))
        self.assertEqual(analytics.parts_cost, Decimal('100.00'))
        self.assertEqual(analytics.labor_cost, Decimal('50.00'))
    
    def test_cost_analytics_str_representation(self):
        """Test string representation of cost analytics."""
        analytics = VehicleCostAnalytics.objects.create(
            vehicle=self.vehicle,
            month=date(2025, 1, 1),
            total_cost=Decimal('150.00'),
            maintenance_cost=Decimal('150.00'),
            parts_cost=Decimal('100.00'),
            labor_cost=Decimal('50.00')
        )
        
        expected_str = f"{self.vehicle.vin} - 2025-01 - $150.00"
        self.assertEqual(str(analytics), expected_str)