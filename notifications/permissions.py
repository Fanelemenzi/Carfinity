from rest_framework.permissions import BasePermission
from vehicles.models import Vehicle
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


class VehicleOwnerPermission(BasePermission):
    """
    Permission class to ensure users can only access their own vehicles.
    This permission class provides comprehensive vehicle ownership validation
    for both object-level and view-level permissions.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and log access attempts
        """
        if not (request.user and request.user.is_authenticated):
            logger.warning(f"Unauthenticated access attempt to vehicle endpoint from IP: {request.META.get('REMOTE_ADDR')}")
            return False
        
        # For vehicle-specific endpoints, check vehicle ownership
        vehicle_id = view.kwargs.get('vehicle_id')
        if vehicle_id:
            vehicle = self.check_vehicle_ownership(request.user, vehicle_id)
            if not vehicle:
                logger.warning(f"User {request.user.id} attempted to access vehicle {vehicle_id} without ownership")
                return False
            
            # Store the vehicle in the request for later use
            request.vehicle = vehicle
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user owns the vehicle object
        """
        if isinstance(obj, Vehicle):
            has_ownership = obj.ownerships.filter(
                user=request.user, 
                is_current_owner=True
            ).exists()
            
            if not has_ownership:
                logger.warning(f"User {request.user.id} attempted to access vehicle {obj.id} without ownership")
            
            return has_ownership
        return False
    
    def check_vehicle_ownership(self, user, vehicle_id):
        """
        Utility method to check vehicle ownership by ID with enhanced error handling
        """
        try:
            vehicle = Vehicle.objects.select_related('vehiclevaluation').get(
                id=vehicle_id,
                ownerships__user=user,
                ownerships__is_current_owner=True
            )
            logger.debug(f"Vehicle ownership verified for user {user.id}, vehicle {vehicle_id}")
            return vehicle
        except Vehicle.DoesNotExist:
            logger.warning(f"Vehicle {vehicle_id} not found or not owned by user {user.id}")
            return None
        except Exception as e:
            logger.error(f"Error checking vehicle ownership for user {user.id}, vehicle {vehicle_id}: {str(e)}")
            return None
    
    def get_user_vehicles(self, user):
        """
        Get all vehicles owned by the user
        """
        try:
            vehicles = Vehicle.objects.filter(
                ownerships__user=user,
                ownerships__is_current_owner=True
            ).select_related('vehiclevaluation').order_by('make', 'model', 'manufacture_year')
            
            logger.debug(f"Retrieved {vehicles.count()} vehicles for user {user.id}")
            return vehicles
        except Exception as e:
            logger.error(f"Error retrieving vehicles for user {user.id}: {str(e)}")
            return Vehicle.objects.none()
    
    def validate_vehicle_access(self, user, vehicle_id):
        """
        Validate vehicle access and raise appropriate exceptions
        """
        if not user or not user.is_authenticated:
            logger.warning(f"Unauthenticated user attempted to access vehicle {vehicle_id}")
            raise PermissionDenied("Authentication required")
        
        vehicle = self.check_vehicle_ownership(user, vehicle_id)
        if not vehicle:
            logger.warning(f"User {user.id} attempted to access vehicle {vehicle_id} without ownership")
            raise PermissionDenied("Vehicle not found or access denied")
        
        return vehicle