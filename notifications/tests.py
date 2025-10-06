from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import Mock, patch
from vehicles.models import Vehicle
from .permissions import VehicleOwnerPermission


class VehicleOwnerPermissionTest(TestCase):
    """
    Test cases for VehicleOwnerPermission class
    """
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = VehicleOwnerPermission()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users are denied access"""
        request = self.factory.get('/api/vehicle/1/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        mock_view = Mock()
        mock_view.kwargs = {'vehicle_id': 1}
        
        result = self.permission.has_permission(request, mock_view)
        self.assertFalse(result, "Unauthenticated users should be denied access")
    
    def test_authenticated_user_without_vehicle_ownership(self):
        """Test that authenticated users without vehicle ownership are denied"""
        request = self.factory.get('/api/vehicle/999/')
        request.user = self.user
        
        mock_view = Mock()
        mock_view.kwargs = {'vehicle_id': 999}  # Non-existent vehicle
        
        result = self.permission.has_permission(request, mock_view)
        self.assertFalse(result, "Users without vehicle ownership should be denied access")
    
    def test_check_vehicle_ownership_nonexistent_vehicle(self):
        """Test check_vehicle_ownership with non-existent vehicle"""
        vehicle = self.permission.check_vehicle_ownership(self.user, 999)
        self.assertIsNone(vehicle, "Non-existent vehicle should return None")
    
    def test_get_user_vehicles_empty(self):
        """Test get_user_vehicles returns empty queryset for user with no vehicles"""
        vehicles = self.permission.get_user_vehicles(self.user)
        self.assertEqual(vehicles.count(), 0, "User with no vehicles should return empty queryset")
    
    def test_has_object_permission_without_ownership(self):
        """Test has_object_permission denies access without ownership"""
        request = self.factory.get('/api/vehicle/1/')
        request.user = self.user
        
        mock_view = Mock()
        mock_vehicle = Mock(spec=Vehicle)
        mock_vehicle.ownerships.filter.return_value.exists.return_value = False
        
        result = self.permission.has_object_permission(request, mock_view, mock_vehicle)
        self.assertFalse(result, "User without ownership should be denied object access")
    
    def test_has_object_permission_with_ownership(self):
        """Test has_object_permission grants access with ownership"""
        request = self.factory.get('/api/vehicle/1/')
        request.user = self.user
        
        mock_view = Mock()
        mock_vehicle = Mock(spec=Vehicle)
        mock_vehicle.ownerships.filter.return_value.exists.return_value = True
        
        result = self.permission.has_object_permission(request, mock_view, mock_vehicle)
        self.assertTrue(result, "User with ownership should be granted object access")
    
    @patch('notifications.permissions.logger')
    def test_logging_unauthenticated_access(self, mock_logger):
        """Test that unauthenticated access attempts are logged"""
        request = self.factory.get('/api/vehicle/1/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        mock_view = Mock()
        mock_view.kwargs = {'vehicle_id': 1}
        
        self.permission.has_permission(request, mock_view)
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        self.assertIn('Unauthenticated access attempt', mock_logger.warning.call_args[0][0])
    
    @patch('notifications.permissions.logger')
    def test_logging_unauthorized_vehicle_access(self, mock_logger):
        """Test that unauthorized vehicle access attempts are logged"""
        request = self.factory.get('/api/vehicle/999/')
        request.user = self.user
        
        mock_view = Mock()
        mock_view.kwargs = {'vehicle_id': 999}
        
        self.permission.has_permission(request, mock_view)
        
        # Verify warning was logged for unauthorized access
        mock_logger.warning.assert_called()
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if 'attempted to access vehicle' in str(call)]
        self.assertTrue(len(warning_calls) > 0, "Should log unauthorized vehicle access attempt")
    
    def test_validate_vehicle_access_unauthenticated(self):
        """Test validate_vehicle_access raises PermissionDenied for unauthenticated user"""
        from django.core.exceptions import PermissionDenied
        
        unauthenticated_user = Mock()
        unauthenticated_user.is_authenticated = False
        
        with self.assertRaises(PermissionDenied) as context:
            self.permission.validate_vehicle_access(unauthenticated_user, 1)
        
        self.assertEqual(str(context.exception), "Authentication required")
    
    def test_validate_vehicle_access_no_ownership(self):
        """Test validate_vehicle_access raises PermissionDenied for user without ownership"""
        from django.core.exceptions import PermissionDenied
        
        with self.assertRaises(PermissionDenied) as context:
            self.permission.validate_vehicle_access(self.user, 999)  # Non-existent vehicle
        
        self.assertEqual(str(context.exception), "Vehicle not found or access denied")
