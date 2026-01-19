from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import Http404, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from vehicles.models import Vehicle
from .services import DashboardService
from .permissions import VehicleOwnerPermission
from .exceptions import (
    VehicleNotFoundError, VehicleAccessDeniedError, DataRetrievalError,
    ExternalServiceError, ErrorHandler
)
from .logging_config import DashboardLogger, log_api_call
import logging

logger = logging.getLogger(__name__)
dashboard_logger = DashboardLogger('views')


class AutoCareDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view for AutoCare functionality providing comprehensive
    vehicle maintenance management interface
    """
    template_name = 'dashboard/autocare_dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        Gather all dashboard context data using DashboardService with comprehensive error handling
        """
        context = super().get_context_data(**kwargs)
        vehicle_id = self.kwargs.get('vehicle_id')
        user_name = self.request.user.first_name or self.request.user.username
        
        try:
            # Get user vehicles first to ensure we have the list
            user_vehicles = ErrorHandler.handle_data_retrieval(
                lambda: self.get_user_vehicles(),
                fallback_value=[],
                error_message="Failed to load user vehicles list"
            )
            
            # Get user's vehicle or default to first vehicle with error handling
            vehicle = ErrorHandler.handle_data_retrieval(
                lambda: self.get_user_vehicle(vehicle_id),
                fallback_value=None,
                error_message=f"Failed to get vehicle for user {self.request.user.id}"
            )
            
            # If no specific vehicle found but user has vehicles, use the first one
            if not vehicle and user_vehicles:
                vehicle = user_vehicles[0]
            
            if vehicle:
                dashboard_service = DashboardService()
                
                # Gather all dashboard data with individual error handling for graceful degradation
                dashboard_data = {}
                
                # Vehicle overview - critical data
                dashboard_data['vehicle_overview'] = ErrorHandler.handle_data_retrieval(
                    lambda: dashboard_service.get_vehicle_overview(vehicle.id, self.request.user),
                    fallback_value={},
                    error_message="Failed to load vehicle overview"
                )
                
                # Upcoming maintenance - important but not critical
                dashboard_data['upcoming_maintenance'] = ErrorHandler.handle_data_retrieval(
                    lambda: dashboard_service.get_upcoming_maintenance(vehicle.id, self.request.user),
                    fallback_value=[],
                    error_message="Failed to load upcoming maintenance"
                )
                
                # Alerts - important for safety
                dashboard_data['alerts'] = ErrorHandler.handle_data_retrieval(
                    lambda: dashboard_service.get_vehicle_alerts(vehicle.id, self.request.user),
                    fallback_value=[],
                    error_message="Failed to load vehicle alerts"
                )
                
                # Service history - nice to have
                dashboard_data['service_history'] = ErrorHandler.handle_data_retrieval(
                    lambda: dashboard_service.get_service_history(vehicle.id, self.request.user, limit=5),
                    fallback_value=[],
                    error_message="Failed to load service history"
                )
                
                # Cost analytics - nice to have
                dashboard_data['cost_analytics'] = ErrorHandler.handle_data_retrieval(
                    lambda: dashboard_service.get_cost_analytics(vehicle.id, self.request.user),
                    fallback_value={},
                    error_message="Failed to load cost analytics"
                )
                
                # Valuation - nice to have, may depend on external service
                dashboard_data['valuation'] = ErrorHandler.handle_data_retrieval(
                    lambda: dashboard_service.get_vehicle_valuation(vehicle.id, self.request.user),
                    fallback_value={},
                    error_message="Failed to load vehicle valuation"
                )
                
                context.update({
                    'vehicle': vehicle,
                    'user_first_name': user_name,
                    'user_vehicles': user_vehicles,
                    **dashboard_data
                })
                
                # Add warnings for any failed data sections
                failed_sections = []
                if not dashboard_data['vehicle_overview']:
                    failed_sections.append('vehicle overview')
                if not dashboard_data['upcoming_maintenance'] and vehicle:
                    failed_sections.append('maintenance schedule')
                if not dashboard_data['service_history'] and vehicle:
                    failed_sections.append('service history')
                
                if failed_sections:
                    context['partial_load_warning'] = f"Some data could not be loaded: {', '.join(failed_sections)}"
                
                logger.info(f"Dashboard context loaded for user {self.request.user.id}, vehicle {vehicle.id}")
                
            else:
                # No vehicles found for user
                context.update({
                    'vehicle': None,
                    'user_first_name': user_name,
                    'user_vehicles': [],
                    'no_vehicles_message': 'No vehicles found. Please add a vehicle to view your dashboard.'
                })
                logger.warning(f"No vehicles found for user {self.request.user.id}")
        
        except (VehicleNotFoundError, VehicleAccessDeniedError) as e:
            logger.warning(f"Vehicle access error for user {self.request.user.id}: {str(e)}")
            context.update({
                'vehicle': None,
                'user_first_name': user_name,
                'user_vehicles': [],
                'error_message': 'Vehicle not found or access denied.'
            })
        
        except Exception as e:
            logger.error(f"Unexpected error loading dashboard context for user {self.request.user.id}: {str(e)}", exc_info=True)
            context.update({
                'vehicle': None,
                'user_first_name': user_name,
                'user_vehicles': [],
                'error_message': 'Unable to load dashboard data. Please try again later.'
            })
        
        return context
    
    def get_user_vehicle(self, vehicle_id=None):
        """
        Get the specified vehicle or user's first vehicle with ownership validation
        """
        try:
            if vehicle_id:
                # Get specific vehicle with ownership validation
                vehicle = Vehicle.objects.select_related('valuation').get(
                    id=vehicle_id,
                    ownerships__user=self.request.user,
                    ownerships__is_current_owner=True
                )
                return vehicle
            else:
                # Get user's first vehicle
                vehicle = Vehicle.objects.select_related('valuation').filter(
                    ownerships__user=self.request.user,
                    ownerships__is_current_owner=True
                ).first()
                return vehicle
                
        except Vehicle.DoesNotExist:
            if vehicle_id:
                # Specific vehicle not found or access denied
                raise Http404("Vehicle not found or access denied")
            return None
    
    def get_user_vehicles(self):
        """
        Get all vehicles owned by the current user for vehicle switching
        """
        return Vehicle.objects.filter(
            ownerships__user=self.request.user,
            ownerships__is_current_owner=True
        ).order_by('make', 'model', 'manufacture_year')


class ServiceHistoryPagination(PageNumberPagination):
    """
    Custom pagination for service history API
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class VehicleSwitchAPIView(APIView):
    """
    API view for switching between user vehicles
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, vehicle_id):
        """
        Switch to a different vehicle for the dashboard
        """
        try:
            # Verify the user owns this vehicle
            vehicle = Vehicle.objects.get(
                id=vehicle_id,
                ownerships__user=request.user,
                ownerships__is_current_owner=True
            )
            
            # Return success response
            return JsonResponse({
                'success': True,
                'vehicle_id': vehicle.id,
                'vehicle_name': f"{vehicle.manufacture_year} {vehicle.make} {vehicle.model}",
                'message': 'Vehicle switched successfully'
            })
            
        except Vehicle.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Vehicle not found or access denied'
            }, status=404)
            
        except Exception as e:
            logger.error(f"Error switching vehicle for user {request.user.id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to switch vehicle'
            }, status=500)


class DashboardAPIView(APIView):
    """
    API view for complete dashboard data
    """
    permission_classes = [IsAuthenticated, VehicleOwnerPermission]
    
    @log_api_call('dashboard_complete_data')
    def get(self, request, vehicle_id):
        """
        Get complete dashboard data for a vehicle with comprehensive error handling
        """
        try:
            # Verify vehicle ownership using error handler
            vehicle = ErrorHandler.validate_vehicle_access(request.user, vehicle_id)
            
            dashboard_service = DashboardService()
            
            # Gather all dashboard data with individual error handling for graceful degradation
            dashboard_data = {}
            
            # Critical data - if this fails, return error
            try:
                dashboard_data['vehicle_overview'] = dashboard_service.get_vehicle_overview(vehicle_id, request.user)
            except Exception as e:
                logger.error(f"Critical error: Failed to get vehicle overview for vehicle {vehicle_id}: {str(e)}")
                raise DataRetrievalError("vehicle overview", e)
            
            # Non-critical data - use graceful degradation
            dashboard_data['upcoming_maintenance'] = ErrorHandler.handle_data_retrieval(
                lambda: dashboard_service.get_upcoming_maintenance(vehicle_id, request.user),
                fallback_value=[],
                error_message="Failed to retrieve upcoming maintenance"
            )
            
            dashboard_data['alerts'] = ErrorHandler.handle_data_retrieval(
                lambda: dashboard_service.get_vehicle_alerts(vehicle_id, request.user),
                fallback_value=[],
                error_message="Failed to retrieve vehicle alerts"
            )
            
            dashboard_data['service_history'] = ErrorHandler.handle_data_retrieval(
                lambda: dashboard_service.get_service_history(vehicle_id, request.user, limit=5),
                fallback_value=[],
                error_message="Failed to retrieve service history"
            )
            
            dashboard_data['cost_analytics'] = ErrorHandler.handle_data_retrieval(
                lambda: dashboard_service.get_cost_analytics(vehicle_id, request.user),
                fallback_value={},
                error_message="Failed to retrieve cost analytics"
            )
            
            # External service dependent data - handle service unavailability
            dashboard_data['valuation'] = ErrorHandler.handle_external_service(
                'vehicle_valuation',
                lambda: dashboard_service.get_vehicle_valuation(vehicle_id, request.user),
                fallback_value={}
            )
            
            # Add metadata about data availability
            dashboard_data['data_status'] = {
                'vehicle_overview': bool(dashboard_data.get('vehicle_overview')),
                'upcoming_maintenance': bool(dashboard_data.get('upcoming_maintenance')),
                'alerts': bool(dashboard_data.get('alerts')),
                'service_history': bool(dashboard_data.get('service_history')),
                'cost_analytics': bool(dashboard_data.get('cost_analytics')),
                'valuation': bool(dashboard_data.get('valuation'))
            }
            
            logger.info(f"Dashboard API data retrieved for user {request.user.id}, vehicle {vehicle_id}")
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except (VehicleNotFoundError, VehicleAccessDeniedError) as e:
            logger.warning(f"Vehicle access error for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': e.code, 'message': e.message, 'details': e.details}},
                status=status.HTTP_404_NOT_FOUND if isinstance(e, VehicleNotFoundError) else status.HTTP_403_FORBIDDEN
            )
        
        except DataRetrievalError as e:
            logger.error(f"Data retrieval error for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': e.code, 'message': e.message, 'details': e.details}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except ExternalServiceError as e:
            logger.error(f"External service error for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': e.code, 'message': e.message, 'details': e.details}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except Exception as e:
            logger.error(f"Unexpected error retrieving dashboard data for user {request.user.id}, vehicle {vehicle_id}: {str(e)}", exc_info=True)
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'Unable to retrieve dashboard data', 'details': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleOverviewAPIView(APIView):
    """
    API view for vehicle overview information
    """
    permission_classes = [IsAuthenticated, VehicleOwnerPermission]
    
    @log_api_call('vehicle_overview')
    def get(self, request, vehicle_id):
        """
        Get vehicle overview data with comprehensive error handling
        """
        try:
            # Verify vehicle ownership using error handler
            vehicle = ErrorHandler.validate_vehicle_access(request.user, vehicle_id)
            
            dashboard_service = DashboardService()
            vehicle_overview = dashboard_service.get_vehicle_overview(vehicle_id, request.user)
            
            if not vehicle_overview:
                raise DataRetrievalError("vehicle overview")
            
            logger.info(f"Vehicle overview retrieved for user {request.user.id}, vehicle {vehicle_id}")
            return Response(vehicle_overview, status=status.HTTP_200_OK)
            
        except (VehicleNotFoundError, VehicleAccessDeniedError) as e:
            return Response(
                {'error': {'code': e.code, 'message': e.message, 'details': e.details}},
                status=status.HTTP_404_NOT_FOUND if isinstance(e, VehicleNotFoundError) else status.HTTP_403_FORBIDDEN
            )
        
        except DataRetrievalError as e:
            return Response(
                {'error': {'code': e.code, 'message': e.message, 'details': e.details}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            logger.error(f"Unexpected error retrieving vehicle overview for user {request.user.id}, vehicle {vehicle_id}: {str(e)}", exc_info=True)
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'Unable to retrieve vehicle overview', 'details': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpcomingMaintenanceAPIView(APIView):
    """
    API view for upcoming maintenance schedules
    """
    permission_classes = [IsAuthenticated, VehicleOwnerPermission]
    
    @log_api_call('upcoming_maintenance')
    def get(self, request, vehicle_id):
        """
        Get upcoming maintenance data
        Vehicle ownership is already verified by VehicleOwnerPermission
        """
        try:
            # Vehicle ownership already verified by permission class
            # Vehicle is available in request.vehicle if needed
            dashboard_service = DashboardService()
            upcoming_maintenance = dashboard_service.get_upcoming_maintenance(vehicle_id, request.user)
            
            logger.info(f"Upcoming maintenance retrieved for user {request.user.id}, vehicle {vehicle_id}")
            return Response(upcoming_maintenance, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving upcoming maintenance for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'Unable to retrieve upcoming maintenance'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleAlertsAPIView(APIView):
    """
    API view for vehicle alerts and notifications
    """
    permission_classes = [IsAuthenticated, VehicleOwnerPermission]
    
    @log_api_call('vehicle_alerts')
    def get(self, request, vehicle_id):
        """
        Get vehicle alerts data
        Vehicle ownership is already verified by VehicleOwnerPermission
        """
        try:
            # Vehicle ownership already verified by permission class
            dashboard_service = DashboardService()
            alerts = dashboard_service.get_vehicle_alerts(vehicle_id, request.user)
            
            logger.info(f"Vehicle alerts retrieved for user {request.user.id}, vehicle {vehicle_id}")
            return Response(alerts, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving vehicle alerts for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'Unable to retrieve vehicle alerts'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ServiceHistoryAPIView(APIView):
    """
    API view for service history with pagination
    """
    permission_classes = [IsAuthenticated, VehicleOwnerPermission]
    pagination_class = ServiceHistoryPagination
    
    @log_api_call('service_history')
    def get(self, request, vehicle_id):
        """
        Get paginated service history data
        Vehicle ownership is already verified by VehicleOwnerPermission
        """
        try:
            # Vehicle ownership already verified by permission class
            dashboard_service = DashboardService()
            
            # Get pagination parameters
            page = request.GET.get('page', 1)
            page_size = min(int(request.GET.get('page_size', 10)), 50)  # Max 50 items per page
            
            # Calculate offset
            try:
                page = int(page)
                offset = (page - 1) * page_size
            except (ValueError, TypeError):
                page = 1
                offset = 0
            
            # Get service history with pagination info
            service_history_data = dashboard_service.get_service_history(
                vehicle_id, 
                request.user, 
                limit=page_size,
                offset=offset
            )
            
            # Add pagination metadata
            total_records = dashboard_service.get_service_history_count(vehicle_id, request.user)
            total_pages = (total_records + page_size - 1) // page_size
            
            paginated_response = {
                'results': service_history_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_records': total_records,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                }
            }
            
            logger.info(f"Service history retrieved for user {request.user.id}, vehicle {vehicle_id}, page {page}")
            return Response(paginated_response, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving service history for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'Unable to retrieve service history'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CostAnalyticsAPIView(APIView):
    """
    API view for cost analytics and spending data
    """
    permission_classes = [IsAuthenticated, VehicleOwnerPermission]
    
    @log_api_call('cost_analytics')
    def get(self, request, vehicle_id):
        """
        Get cost analytics data
        Vehicle ownership is already verified by VehicleOwnerPermission
        """
        try:
            # Vehicle ownership already verified by permission class
            dashboard_service = DashboardService()
            cost_analytics = dashboard_service.get_cost_analytics(vehicle_id, request.user)
            
            logger.info(f"Cost analytics retrieved for user {request.user.id}, vehicle {vehicle_id}")
            return Response(cost_analytics, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving cost analytics for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'Unable to retrieve cost analytics'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleValuationAPIView(APIView):
    """
    API view for vehicle valuation and market value
    """
    permission_classes = [IsAuthenticated, VehicleOwnerPermission]
    
    @log_api_call('vehicle_valuation')
    def get(self, request, vehicle_id):
        """
        Get vehicle valuation data
        Vehicle ownership is already verified by VehicleOwnerPermission
        """
        try:
            # Vehicle ownership already verified by permission class
            dashboard_service = DashboardService()
            valuation = dashboard_service.get_vehicle_valuation(vehicle_id, request.user)
            
            logger.info(f"Vehicle valuation retrieved for user {request.user.id}, vehicle {vehicle_id}")
            return Response(valuation, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving vehicle valuation for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'Unable to retrieve vehicle valuation'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )