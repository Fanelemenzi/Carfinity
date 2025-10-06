"""
Test caching functionality for the dashboard system.
"""
import os
import sys
import django
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

# from notifications.cache_utils import CacheManager  # Temporarily disabled
from notifications.services import DashboardService
from vehicles.models import Vehicle


class TestCacheUtils(TestCase):
    """Test cache utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.vehicle_id = 1
        self.user_id = 1
        self.test_valuation_data = {
            'estimated_value': 25000.0,
            'condition_rating': 'GOOD',
            'last_updated': '2024-01-15',
            'valuation_source': 'KBB'
        }
        self.test_health_data = {
            'health_score': 85,
            'health_status': 'GOOD',
            'last_inspection_date': '2024-01-10'
        }
        
        # Clear cache before each test
        cache.clear()
    
    def test_vehicle_valuation_caching(self):
        """Test vehicle valuation caching and retrieval"""
        # Test setting cache
        result = CacheManager.set_vehicle_valuation(self.vehicle_id, self.test_valuation_data)
        self.assertTrue(result)
        
        # Test getting from cache
        cached_data = CacheManager.get_vehicle_valuation(self.vehicle_id)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['estimated_value'], 25000.0)
        self.assertEqual(cached_data['condition_rating'], 'GOOD')
    
    def test_health_score_caching(self):
        """Test health score caching and retrieval"""
        # Test setting cache
        result = CacheManager.set_health_score(self.vehicle_id, self.test_health_data)
        self.assertTrue(result)
        
        # Test getting from cache
        cached_data = CacheManager.get_health_score(self.vehicle_id)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['health_score'], 85)
        self.assertEqual(cached_data['health_status'], 'GOOD')
    
    def test_dashboard_data_caching(self):
        """Test dashboard data caching and retrieval"""
        dashboard_data = {
            'vehicle_overview': {'id': self.vehicle_id, 'make': 'Toyota'},
            'alerts': [],
            'maintenance': []
        }
        
        # Test setting cache
        result = CacheManager.set_dashboard_data(self.vehicle_id, self.user_id, dashboard_data)
        self.assertTrue(result)
        
        # Test getting from cache
        cached_data = CacheManager.get_dashboard_data(self.vehicle_id, self.user_id)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['vehicle_overview']['make'], 'Toyota')
    
    def test_cache_invalidation(self):
        """Test cache invalidation functionality"""
        # Set some cached data
        CacheManager.set_vehicle_valuation(self.vehicle_id, self.test_valuation_data)
        CacheManager.set_health_score(self.vehicle_id, self.test_health_data)
        
        # Verify data is cached
        self.assertIsNotNone(CacheManager.get_vehicle_valuation(self.vehicle_id))
        self.assertIsNotNone(CacheManager.get_health_score(self.vehicle_id))
        
        # Invalidate cache
        result = CacheManager.invalidate_vehicle_cache(self.vehicle_id)
        self.assertTrue(result)
        
        # Verify data is no longer cached
        self.assertIsNone(CacheManager.get_vehicle_valuation(self.vehicle_id))
        self.assertIsNone(CacheManager.get_health_score(self.vehicle_id))
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key = CacheManager._get_cache_key("valuation", self.vehicle_id)
        expected_key = f"vehicle:{self.vehicle_id}:valuation"
        self.assertEqual(key, expected_key)
        
        key_with_suffix = CacheManager._get_cache_key("inspection", self.vehicle_id, "latest")
        expected_key_with_suffix = f"vehicle:{self.vehicle_id}:inspection:latest"
        self.assertEqual(key_with_suffix, expected_key_with_suffix)
    
    def test_cache_error_handling(self):
        """Test cache error handling"""
        with patch('django.core.cache.cache.get', side_effect=Exception("Cache error")):
            result = CacheManager.get_vehicle_valuation(self.vehicle_id)
            self.assertIsNone(result)
        
        with patch('django.core.cache.cache.set', side_effect=Exception("Cache error")):
            result = CacheManager.set_vehicle_valuation(self.vehicle_id, self.test_valuation_data)
            self.assertFalse(result)


class TestDashboardServiceCaching(TestCase):
    """Test caching integration in DashboardService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.service = DashboardService()
        self.vehicle_id = 1
        
        # Clear cache before each test
        cache.clear()
    
    @patch('notifications.services.Vehicle.objects')
    def test_valuation_service_caching(self, mock_vehicle_objects):
        """Test that valuation service uses caching"""
        # Mock vehicle data
        mock_vehicle = MagicMock()
        mock_vehicle.id = self.vehicle_id
        mock_vehicle.manufacture_year = 2020
        mock_vehicle.current_mileage = 50000
        mock_vehicle.vehiclevaluation.estimated_value = 25000.0
        mock_vehicle.vehiclevaluation.condition_rating = 'GOOD'
        mock_vehicle.vehiclevaluation.last_updated = '2024-01-15'
        mock_vehicle.vehiclevaluation.valuation_source = 'KBB'
        
        mock_vehicle_objects.select_related.return_value.get.return_value = mock_vehicle
        
        # First call should hit the database and cache the result
        result1 = self.service.get_vehicle_valuation(self.vehicle_id, self.user)
        self.assertEqual(result1['estimated_value'], 25000.0)
        
        # Second call should use cached data (mock won't be called again)
        with patch('notifications.services.Vehicle.objects') as mock_second_call:
            result2 = self.service.get_vehicle_valuation(self.vehicle_id, self.user)
            self.assertEqual(result2['estimated_value'], 25000.0)
            # Verify database wasn't queried again
            mock_second_call.select_related.assert_not_called()
    
    def test_cache_invalidation_methods(self):
        """Test cache invalidation methods in service"""
        # Test invalidation
        result = self.service.invalidate_vehicle_cache(self.vehicle_id, self.user.id)
        self.assertTrue(result)
        
        # Test cache warming
        with patch.object(self.service, 'get_vehicle_valuation') as mock_valuation:
            with patch.object(self.service, 'get_complete_dashboard_data') as mock_dashboard:
                mock_valuation.return_value = {'estimated_value': 25000.0}
                mock_dashboard.return_value = {'vehicle_overview': {}}
                
                result = self.service.warm_vehicle_cache(self.vehicle_id, self.user)
                self.assertTrue(result)
                
                # Verify methods were called
                mock_valuation.assert_called_once_with(self.vehicle_id, self.user)
                mock_dashboard.assert_called_once_with(self.vehicle_id, self.user)


def run_cache_tests():
    """Run cache-related tests"""
    print("Running cache functionality tests...")
    
    # Test basic cache operations
    print("\n1. Testing basic cache operations...")
    cache.set('test_key', 'test_value', 300)
    cached_value = cache.get('test_key')
    if cached_value == 'test_value':
        print("✓ Basic cache operations working")
    else:
        print("✗ Basic cache operations failed")
    
    # Test cache manager
    print("\n2. Testing CacheManager...")
    test_data = {'test': 'data', 'value': 123}
    
    # Test valuation caching
    CacheManager.set_vehicle_valuation(1, test_data)
    cached_data = CacheManager.get_vehicle_valuation(1)
    if cached_data == test_data:
        print("✓ Vehicle valuation caching working")
    else:
        print("✗ Vehicle valuation caching failed")
    
    # Test cache invalidation
    CacheManager.invalidate_vehicle_cache(1)
    cached_data = CacheManager.get_vehicle_valuation(1)
    if cached_data is None:
        print("✓ Cache invalidation working")
    else:
        print("✗ Cache invalidation failed")
    
    print("\nCache tests completed!")


if __name__ == '__main__':
    run_cache_tests()