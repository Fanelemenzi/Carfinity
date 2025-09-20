from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db import models
from vehicles.models import Vehicle, VehicleStatus, VehicleOwnership, VehicleImage  # Add VehicleImage
from maintenance_history.models import MaintenanceRecord, Inspection, InitialInspection
from vehicle_equip.models import PowertrainAndDrivetrain, ChassisSuspensionAndBraking, ElectricalSystem, ExteriorFeaturesAndBody, ActiveSafetyAndADAS
from django.http import JsonResponse
from .forms import SignUpForm
from .models import Profile, DataConsent
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden
from .permissions import require_group, require_organization_type, require_any_group, require_dashboard_access, check_permission_conflicts

# Create your views here.

def home(request):
    return render(request, 'public/index.html', {})

def about(request):
    return render(request, 'public/about.html', {})

def blog(request):
    return render(request, 'public/blog.html', {})

def contact(request):
    return render(request, 'public/contact.html', {})

def login_user(request):
    from .error_handlers import SecurityEventLogger
    
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        # Get client IP for logging
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if client_ip:
            client_ip = client_ip.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Log successful authentication
            SecurityEventLogger.log_authentication_attempt(username, True, client_ip)
            
            # Check if "remember me" is selected
            remember_me = request.POST.get('remember_me')
            
            # Set session expiry based on remember me
            if remember_me:
                # Remember for 30 days
                request.session.set_expiry(30 * 24 * 60 * 60)
            else:
                # Default session expiry (browser close)
                request.session.set_expiry(0)
            
            login(request, user)
            
            # Get next URL from POST data or GET parameter
            next_url = request.POST.get('next') or request.GET.get('next')
            
            # Use DashboardRouter for intelligent post-login routing
            from .services import DashboardRouter
            try:
                redirect_url = DashboardRouter.get_post_login_redirect(user, next_url)
                
                # Convert URL to view name if needed for Django redirect
                if redirect_url.startswith('/'):
                    # Use the helper function to convert URL to view name
                    redirect_target = get_post_login_redirect(user)
                else:
                    redirect_target = redirect_url
                
                return redirect(redirect_target)
            except Exception as e:
                # Log the error and fall back to basic redirect
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in post-login redirect for user {user.id}: {str(e)}")
                
                # Fall back to basic dashboard redirect
                return redirect('dashboard')
        else:
            # Log failed authentication
            SecurityEventLogger.log_authentication_attempt(username, False, client_ip)
            
            messages.error(request, "Invalid username or password. Please try again.")
            return redirect('login')
    else:
        # Handle GET request - show login form with next parameter
        next_url = request.GET.get('next', '')
        context = {'next': next_url} if next_url else {}
        return render(request, 'public/login.html', context)

def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out"))
    return redirect('home')

def dashboard(request):
    """
    Smart dashboard view that handles authentication and routing at the template level.
    This approach is more flexible and handles edge cases better.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Always render the smart dashboard template - it will handle authentication logic
    context = {}
    
    # If user is authenticated, get their data for the customer dashboard
    if request.user.is_authenticated:
        try:
            context = render_customer_dashboard_context(request)
        except Exception as e:
            logger.error(f"Error getting dashboard context for user {request.user.id}: {str(e)}")
            # Continue with empty context - template will handle the error
    
    return render(request, 'dashboard/smart_dashboard.html', context)


def render_customer_dashboard_context(request):
    """
    Get the context data for the customer dashboard.
    """
    from django.db.models import Count, Sum, Avg, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    from maintenance.models import ScheduledMaintenance, Part
    from maintenance_history.models import Inspection, MaintenanceRecord, PartUsage
    from decimal import Decimal
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Initialize default values
    owned_vehicles = []
    scheduled_maintenance = []
    inspections = []
    selected_vehicle = None
    
    # Initialize onboarding variables
    onboarding_completed = False
    user_onboarding = None
    
    # Initialize dashboard metrics
    dashboard_metrics = {
        'total_vehicles': 0,
        'upcoming_maintenance': 0,
        'overdue_maintenance': 0,
        'average_health': 0,
        'monthly_cost': 0,
    }
    
    vehicle_health_data = []
    upcoming_maintenance_data = []
    recent_inspections = []
    recent_maintenance = []
    low_stock_parts = []
    
    # Error handling context
    error_context = {
        'has_errors': False,
        'error_messages': [],
        'warning_messages': []
    }
    
    if request.user.is_authenticated:
        # Check if user has completed onboarding
        from onboarding.models import CustomerOnboarding
        try:
            user_onboarding = CustomerOnboarding.objects.get(user=request.user)
            onboarding_completed = True
        except CustomerOnboarding.DoesNotExist:
            user_onboarding = None
            onboarding_completed = False
            error_context['warning_messages'].append("Complete your onboarding to access all dashboard features.")
        except Exception as e:
            logger.error(f"Error checking onboarding status for user {request.user.id}: {str(e)}")
            error_context['warning_messages'].append("Unable to verify onboarding status. Some features may be limited.")
        
        # Get user's vehicles with error handling
        try:
            owned_vehicles = VehicleOwnership.objects.filter(
                user=request.user, 
                is_current_owner=True
            ).select_related('vehicle')
            
            user_vehicles = [ownership.vehicle for ownership in owned_vehicles]
            
            if not user_vehicles:
                error_context['warning_messages'].append("No vehicles found. Add a vehicle to see dashboard data.")
                
        except Exception as e:
            logger.error(f"Error retrieving vehicles for user {request.user.id}: {str(e)}")
            error_context['has_errors'] = True
            error_context['error_messages'].append("Unable to load vehicle data. Please try again later.")
            user_vehicles = []
        
        # Calculate Key Metrics with error handling
        try:
            dashboard_metrics['total_vehicles'] = len(user_vehicles)
            
            if user_vehicles:
                # Get current date for calculations
                today = timezone.now().date()
                thirty_days_from_now = today + timedelta(days=30)
                current_month_start = today.replace(day=1)
                
                # Upcoming and Overdue Maintenance
                all_scheduled = ScheduledMaintenance.objects.filter(
                    assigned_plan__vehicle__in=user_vehicles,
                    status__in=['PENDING', 'OVERDUE']
                )
                
                upcoming_count = all_scheduled.filter(
                    due_date__lte=thirty_days_from_now,
                    due_date__gte=today
                ).count()
                
                overdue_count = all_scheduled.filter(
                    due_date__lt=today
                ).count()
                
                dashboard_metrics['upcoming_maintenance'] = upcoming_count
                dashboard_metrics['overdue_maintenance'] = overdue_count
                
                # Update overdue status
                all_scheduled.filter(due_date__lt=today).update(status='OVERDUE')
                
                # Average Vehicle Health (from latest inspections)
                health_scores = []
                for vehicle in user_vehicles:
                    latest_inspection = Inspection.objects.filter(
                        vehicle=vehicle
                    ).order_by('-inspection_date').first()
                    
                    if latest_inspection and latest_inspection.vehicle_health_index:
                        try:
                            # Extract numeric value from health index string
                            health_str = latest_inspection.vehicle_health_index
                            if '%' in health_str:
                                health_value = float(health_str.replace('%', ''))
                            elif 'Excellent' in health_str:
                                health_value = 95.0
                            elif 'Good' in health_str:
                                health_value = 80.0
                            elif 'Fair' in health_str:
                                health_value = 65.0
                            elif 'Poor' in health_str:
                                health_value = 40.0
                            else:
                                # Try to extract number from string
                                import re
                                numbers = re.findall(r'\d+\.?\d*', health_str)
                                health_value = float(numbers[0]) if numbers else 75.0
                            
                            health_scores.append(health_value)
                            
                            # Add to vehicle health data
                            vehicle_health_data.append({
                                'vehicle': vehicle,
                                'health_score': health_value,
                                'health_category': get_health_category(health_value),
                                'last_inspection': latest_inspection.inspection_date,
                            })
                        except (ValueError, AttributeError):
                            # Default health score if parsing fails
                            health_scores.append(75.0)
                            vehicle_health_data.append({
                                'vehicle': vehicle,
                                'health_score': 75.0,
                                'health_category': 'Good',
                                'last_inspection': latest_inspection.inspection_date if latest_inspection else None,
                            })
                    else:
                        # No inspection data available
                        vehicle_health_data.append({
                            'vehicle': vehicle,
                            'health_score': None,
                            'health_category': 'No Data',
                            'last_inspection': None,
                        })
                
                if health_scores:
                    dashboard_metrics['average_health'] = round(sum(health_scores) / len(health_scores), 1)
                
                # Monthly Maintenance Cost
                current_month_maintenance = MaintenanceRecord.objects.filter(
                    vehicle__in=user_vehicles,
                    date_performed__gte=current_month_start
                )
                
                # Calculate total cost from parts used
                monthly_cost = 0
                for record in current_month_maintenance:
                    parts_cost = PartUsage.objects.filter(
                        maintenance_record=record,
                        unit_cost__isnull=False
                    ).aggregate(
                        total=Sum('unit_cost')
                    )['total'] or 0
                    monthly_cost += float(parts_cost)
                
                dashboard_metrics['monthly_cost'] = round(monthly_cost, 2)
                
                # Get Upcoming Maintenance Data (next 30 days)
                upcoming_maintenance_data = ScheduledMaintenance.objects.filter(
                    assigned_plan__vehicle__in=user_vehicles,
                    due_date__lte=thirty_days_from_now,
                    status__in=['PENDING', 'OVERDUE']
                ).select_related(
                    'assigned_plan__vehicle',
                    'task'
                ).order_by('due_date')[:10]  # Limit to 10 most urgent
                
                # Get Recent Inspections
                recent_inspections = Inspection.objects.filter(
                    vehicle__in=user_vehicles
                ).select_related('vehicle').order_by('-inspection_date')[:5]
                
                # Get Recent Maintenance Records
                recent_maintenance = MaintenanceRecord.objects.filter(
                    vehicle__in=user_vehicles
                ).select_related(
                    'vehicle', 'technician'
                ).prefetch_related(
                    'parts_used__part'
                ).order_by('-date_performed')[:5]
                
                # Get Low Stock Parts (if user has access to parts inventory)
                try:
                    low_stock_parts = Part.objects.filter(
                        stock_quantity__lte=models.F('minimum_stock_level')
                    ).order_by('stock_quantity')[:5]
                except Exception as e:
                    logger.warning(f"Error retrieving low stock parts for user {request.user.id}: {str(e)}")
                    low_stock_parts = []
                
        except Exception as e:
            logger.error(f"Error calculating dashboard metrics for user {request.user.id}: {str(e)}")
            error_context['has_errors'] = True
            error_context['error_messages'].append("Unable to calculate dashboard metrics. Please try again later.")
        
        # Handle vehicle selection for detailed view with error handling
        vehicle_id = request.GET.get('vehicle_id')
        if vehicle_id:
            try:
                selected_vehicle = Vehicle.objects.get(id=vehicle_id)
                # Verify user owns this vehicle
                if not VehicleOwnership.objects.filter(user=request.user, vehicle=selected_vehicle, is_current_owner=True).exists():
                    messages.error(request, "You don't have access to view details for this vehicle.")
                    selected_vehicle = None
                else:
                    # Scheduled Maintenance for selected vehicle
                    scheduled_maintenance = ScheduledMaintenance.objects.filter(
                        assigned_plan__vehicle=selected_vehicle
                    ).select_related('task').order_by('due_date')
                    
                    # Inspections for selected vehicle
                    inspections = Inspection.objects.filter(
                        vehicle=selected_vehicle
                    ).order_by('-inspection_date')
            except Vehicle.DoesNotExist:
                messages.error(request, "The selected vehicle was not found.")
                selected_vehicle = None
            except Exception as e:
                logger.error(f"Error loading vehicle details for user {request.user.id}, vehicle {vehicle_id}: {str(e)}")
                messages.error(request, "Unable to load vehicle details. Please try again.")
                selected_vehicle = None
    else:
        # User is not authenticated - set default values
        onboarding_completed = False
        user_onboarding = None
    
    # Add error context to messages if there are any
    if error_context['has_errors']:
        for error_msg in error_context['error_messages']:
            messages.error(request, error_msg)
    
    if error_context['warning_messages']:
        for warning_msg in error_context['warning_messages']:
            messages.warning(request, warning_msg)
    
    return {
        'owned_vehicles': owned_vehicles,
        'scheduled_maintenance': scheduled_maintenance,
        'inspections': inspections,
        'selected_vehicle': selected_vehicle,
        'dashboard_metrics': dashboard_metrics,
        'vehicle_health_data': vehicle_health_data,
        'upcoming_maintenance_data': upcoming_maintenance_data,
        'recent_inspections': recent_inspections,
        'recent_maintenance': recent_maintenance,
        'low_stock_parts': low_stock_parts,
        'onboarding_completed': onboarding_completed,
        'user_onboarding': user_onboarding,
        'error_context': error_context,
    }


def get_health_category(health_score):
    """Convert health score to category"""
    if health_score >= 90:
        return 'Excellent'
    elif health_score >= 75:
        return 'Good'
    elif health_score >= 60:
        return 'Fair'
    else:
        return 'Needs Attention'

def login_dashboard(request):
    return render(request, 'dashboard/login_dashboard.html', {})

def test_auth(request):
    """Test view to check authentication and group assignments"""
    return render(request, 'dashboard/test_auth.html', {})

def test_simple(request):
    """Simple test view to check template tag functionality"""
    return render(request, 'dashboard/test_simple.html', {})

def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        
        # Check if terms and conditions are accepted
        terms_accepted = request.POST.get('terms')
        
        if form.is_valid() and terms_accepted:
            try:
                # Create the user
                user = form.save()
                
                # Create associated profile
                Profile.objects.create(user=user)
                
                # Create data consents
                DataConsent.objects.create(
                    user=user,
                    consent_type='PRIVACY'
                )
                DataConsent.objects.create(
                    user=user,
                    consent_type='EMAIL'
                )
                DataConsent.objects.create(
                    user=user,
                    consent_type='DATA'
                )
                DataConsent.objects.create(
                    user=user,
                    consent_type='DATA_ANALYTICS'
                )
                
                # Log the user in
                login(request, user)
                
                # Show success message
                messages.success(request, "Registration successful! Welcome to Carfinity.")
                
                # Redirect to onboarding survey
                return redirect('customer_vehicle_survey')
                
            except Exception as e:
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error during user registration: {str(e)}")
                
                # Show error message
                messages.error(request, "An error occurred during registration. Please try again.")
                
        elif not terms_accepted:
            messages.error(request, "You must accept the Terms of Service and Privacy Policy to continue.")
        else:
            # Form validation errors will be displayed by the template
            pass
            
    else:
        form = SignUpForm()
    
    return render(request, 'public/register.html', {
        'form': form
    })

def search(request):
    return render(request, 'search/search.html', {})

def search_results(request):
    vin = request.GET.get('vin')
    
    # Initialize context with error handling
    context = {
        'searched_vin': vin,
        'error_type': None,
        'error_message': None,
        'vehicle': None,
        'status': None,
        'maintenance_records': [],
        'inspections': [],
        'vehicle_images': [],
        'powertrain': None,
        'chassis': None,
        'electrical': None,
        'exterior': None,
        'safety': None,
    }
    
    # Check if VIN was provided
    if not vin:
        context.update({
            'error_type': 'missing_vin',
            'error_message': 'Please enter a VIN number to search for vehicle information.'
        })
        return render(request, 'search/search-results.html', context)
    
    # Clean and validate VIN format
    vin = vin.strip().upper()
    if len(vin) != 17:
        context.update({
            'error_type': 'invalid_vin_format',
            'error_message': f'Invalid VIN format. VIN must be exactly 17 characters long. You entered: {len(vin)} characters.'
        })
        return render(request, 'search/search-results.html', context)
    
    try:
        # Get the vehicle
        vehicle = Vehicle.objects.get(vin=vin)
        
        # Get vehicle status
        try:
            vehicle_status = VehicleStatus.objects.get(vehicle=vehicle)
        except VehicleStatus.DoesNotExist:
            vehicle_status = None
        
        # Get maintenance records with related data
        maintenance_records = MaintenanceRecord.objects.filter(vehicle=vehicle).select_related(
            'technician', 'scheduled_maintenance'
        ).prefetch_related(
            'parts_used__part'
        ).order_by('-date_performed')
        
        # Get inspections with related inspection forms
        inspections = Inspection.objects.filter(vehicle=vehicle).select_related(
            'inspections_form__technician'
        ).order_by('-inspection_date')
        
        # Get initial inspections
        initial_inspections = InitialInspection.objects.filter(vehicle=vehicle).select_related(
            'technician'
        ).order_by('-inspection_date')
        
        # Get vehicle images
        vehicle_images = VehicleImage.objects.filter(vehicle=vehicle).order_by('-is_primary', '-uploaded_at')
        
        # Get vehicle equipment information
        powertrain = PowertrainAndDrivetrain.objects.filter(vehicle=vehicle).first()
        chassis = ChassisSuspensionAndBraking.objects.filter(vehicle=vehicle).first()
        electrical = ElectricalSystem.objects.filter(vehicle=vehicle).first()
        exterior = ExteriorFeaturesAndBody.objects.filter(vehicle=vehicle).first()
        safety = ActiveSafetyAndADAS.objects.filter(vehicle=vehicle).first()
        
        context.update({
            'vehicle': vehicle,
            'status': vehicle_status,
            'maintenance_records': maintenance_records,
            'inspections': inspections,
            'initial_inspections': initial_inspections,
            'vehicle_images': vehicle_images,
            'powertrain': powertrain,
            'chassis': chassis,
            'electrical': electrical,
            'exterior': exterior,
            'safety': safety,
        })
        
        return render(request, 'search/search-results.html', context)
        
    except Vehicle.DoesNotExist:
        context.update({
            'error_type': 'vehicle_not_found',
            'error_message': f'No vehicle found with VIN: {vin}. Please check the VIN number and try again.'
        })
        return render(request, 'search/search-results.html', context)
        
    except Exception as e:
        context.update({
            'error_type': 'system_error',
            'error_message': f'An unexpected error occurred while searching for the vehicle. Please try again later.'
        })
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Search error for VIN {vin}: {str(e)}")
        return render(request, 'search/search-results.html', context)



#def create_record(request):
#    return render(request, 'maintenance/create_record.html', {})

@login_required
def typeform_redirect(request):
    return render(request, 'public/typeform_embed.html')

@login_required
def check_onboarding_status(request):
    """Check if user has completed onboarding and redirect accordingly"""
    from onboarding.models import CustomerOnboarding
    
    try:
        CustomerOnboarding.objects.get(user=request.user)
        # User has completed onboarding, redirect to dashboard
        return redirect('dashboard')
    except CustomerOnboarding.DoesNotExist:
        # User hasn't completed onboarding, redirect to survey
        return redirect('customer_vehicle_survey')


def get_post_login_redirect(user):
    """
    Determine the appropriate redirect URL after login based on user groups and organization.
    Uses the DashboardRouter for intelligent routing logic.
    
    This function is kept for backward compatibility but delegates to DashboardRouter.
    """
    from .services import DashboardRouter
    
    # Use the new DashboardRouter for intelligent routing
    redirect_url = DashboardRouter.get_post_login_redirect(user)
    
    # Convert absolute URLs to view names for Django redirect compatibility
    url_to_view_mapping = {
        '/dashboard/': 'dashboard',
        '/insurance-dashboard/': 'insurance:insurance_dashboard',
        '/dashboard-selector/': 'dashboard_selector',
        '/access-denied/': 'access_denied',
        '/': 'home'
    }
    
    # Check for exact matches first
    if redirect_url in url_to_view_mapping:
        return url_to_view_mapping[redirect_url]
    
    # Check for URL patterns with query parameters
    for url_pattern, view_name in url_to_view_mapping.items():
        if redirect_url.startswith(url_pattern):
            return view_name
    
    # If no mapping found, return the URL as-is
    return redirect_url


def access_denied(request):
    """
    View for handling access denied scenarios.
    Uses the new error handling system for consistent user feedback.
    """
    from .error_handlers import AuthenticationErrorHandler, ErrorType
    
    # Determine the specific error type
    if not request.user.is_authenticated:
        return AuthenticationErrorHandler.handle_access_denied(
            request, ErrorType.NO_AUTHENTICATION
        )
    
    # User is authenticated, check for specific issues
    user_groups = list(request.user.groups.values_list('name', flat=True))
    
    if not user_groups:
        return AuthenticationErrorHandler.handle_access_denied(
            request, ErrorType.NO_GROUPS
        )
    
    # Check organization status
    try:
        from organizations.models import OrganizationUser
        org_user = OrganizationUser.objects.filter(user=request.user, is_active=True).first()
        if not org_user:
            return AuthenticationErrorHandler.handle_access_denied(
                request, ErrorType.NO_ORGANIZATION
            )
    except ImportError:
        # Organization app not available, continue with generic access denied
        pass
    
    # Generic access denied
    return AuthenticationErrorHandler.handle_access_denied(
        request, ErrorType.ACCESS_DENIED
    )


def no_groups_error(request):
    """Specific view for users with no group assignments"""
    from .error_handlers import AuthenticationErrorHandler, ErrorType
    return AuthenticationErrorHandler.handle_access_denied(
        request, ErrorType.NO_GROUPS
    )


def no_organization_error(request):
    """Specific view for users with no organization assignments"""
    from .error_handlers import AuthenticationErrorHandler, ErrorType
    return AuthenticationErrorHandler.handle_access_denied(
        request, ErrorType.NO_ORGANIZATION
    )


def system_error(request):
    """View for handling system errors"""
    from .error_handlers import AuthenticationErrorHandler
    return AuthenticationErrorHandler.handle_system_error(request)


@require_any_group(['customers', 'insurance_company'])
@check_permission_conflicts
def dashboard_selector(request):
    """
    View for users who have access to multiple dashboards.
    Allows them to choose which dashboard to access.
    Uses DashboardRouter for intelligent routing decisions.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to access the dashboard selector.")
        return redirect('login')
    
    try:
        from .services import DashboardRouter, AuthenticationService
        
        # Get user permissions with error handling
        try:
            permissions = AuthenticationService.get_user_permissions(request.user)
        except Exception as e:
            logger.error(f"Error getting user permissions for user {request.user.id}: {str(e)}")
            messages.error(request, "Unable to determine your access permissions. Please contact support.")
            return redirect('access_denied')
        
        if not permissions.available_dashboards:
            messages.warning(request, "You don't have access to any dashboards. Please contact your administrator.")
            return redirect('access_denied')
        
        # If user only has access to one dashboard, redirect directly
        if len(permissions.available_dashboards) == 1:
            dashboard_name = permissions.available_dashboards[0]
            dashboard_info = AuthenticationService.DASHBOARDS.get(dashboard_name)
            if dashboard_info:
                messages.info(request, f"Redirecting to your {dashboard_info.display_name}.")
                return redirect(dashboard_info.url)
            else:
                logger.error(f"Dashboard info not found for dashboard: {dashboard_name}")
                messages.error(request, "Dashboard configuration error. Please contact support.")
                return redirect('access_denied')
        
        # Get available dashboards using DashboardRouter
        try:
            available_dashboards = DashboardRouter.get_available_dashboards(request.user)
        except Exception as e:
            logger.error(f"Error getting available dashboards for user {request.user.id}: {str(e)}")
            messages.error(request, "Unable to load dashboard options. Please try again later.")
            return redirect('access_denied')
        
        # Prepare dashboard options for template
        dashboard_options = []
        for dashboard_info in available_dashboards:
            dashboard_options.append({
                'name': dashboard_info.name,
                'display_name': dashboard_info.display_name,
                'url': dashboard_info.url,
                'description': f'Access your {dashboard_info.display_name.lower()} features',
                'required_groups': dashboard_info.required_groups,
                'required_org_types': dashboard_info.required_org_types
            })
        
        # Get conflict resolution information
        try:
            conflict_resolution = DashboardRouter.resolve_dashboard_conflicts(request.user)
            default_dashboard = DashboardRouter.get_default_dashboard(request.user)
        except Exception as e:
            logger.warning(f"Error getting conflict resolution for user {request.user.id}: {str(e)}")
            conflict_resolution = None
            default_dashboard = None
        
        context = {
            'dashboard_options': dashboard_options,
            'user_permissions': permissions,
            'conflict_resolution': conflict_resolution,
            'default_dashboard': default_dashboard
        }
        
        return render(request, 'dashboard/dashboard_selector.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in dashboard_selector for user {request.user.id}: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('access_denied')


@require_any_group(['customers', 'insurance_company'])
@check_permission_conflicts
def switch_dashboard(request, dashboard_name):
    """
    View for switching between dashboards for multi-access users.
    Validates access and redirects to the requested dashboard.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from .services import DashboardRouter, AuthenticationService
        
        # Validate dashboard name format
        if not dashboard_name or not isinstance(dashboard_name, str):
            messages.error(request, "Invalid dashboard name provided.")
            return redirect('dashboard_selector')
        
        # Validate that user has access to the requested dashboard
        try:
            has_access = DashboardRouter.validate_dashboard_access(request.user, dashboard_name)
        except Exception as e:
            logger.error(f"Error validating dashboard access for user {request.user.id}, dashboard {dashboard_name}: {str(e)}")
            messages.error(request, "Unable to validate dashboard access. Please try again.")
            return redirect('dashboard_selector')
        
        if not has_access:
            logger.warning(f"User {request.user.id} attempted to access unauthorized dashboard: {dashboard_name}")
            messages.error(request, f"You don't have access to the {dashboard_name} dashboard.")
            return redirect('access_denied')
        
        # Get dashboard info and redirect
        dashboard_info = AuthenticationService.DASHBOARDS.get(dashboard_name)
        if dashboard_info:
            messages.success(request, f"Switched to {dashboard_info.display_name}")
            logger.info(f"User {request.user.id} successfully switched to dashboard: {dashboard_name}")
            return redirect(dashboard_info.url)
        else:
            logger.error(f"Dashboard configuration not found for: {dashboard_name}")
            messages.error(request, f"Dashboard '{dashboard_name}' configuration not found.")
            return redirect('dashboard_selector')
            
    except Exception as e:
        logger.error(f"Unexpected error in switch_dashboard for user {request.user.id}, dashboard {dashboard_name}: {str(e)}")
        messages.error(request, "An unexpected error occurred while switching dashboards. Please try again.")
        return redirect('dashboard_selector')


@require_any_group(['customers', 'insurance_company'])
def dashboard_switch_api(request):
    """
    API endpoint for getting dashboard switching options.
    Returns JSON data for dynamic dashboard switching interfaces.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'GET':
        try:
            from .services import DashboardRouter
            
            current_dashboard = request.GET.get('current', '')
            
            # Validate current dashboard parameter
            if current_dashboard and not isinstance(current_dashboard, str):
                return JsonResponse({
                    'success': False, 
                    'error': 'Invalid current dashboard parameter'
                }, status=400)
            
            # Get switch options with error handling
            try:
                switch_options = DashboardRouter.get_dashboard_switch_options(request.user, current_dashboard)
            except Exception as e:
                logger.error(f"Error getting dashboard switch options for user {request.user.id}: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to load dashboard options'
                }, status=500)
            
            return JsonResponse({
                'success': True,
                'switch_options': switch_options,
                'current_dashboard': current_dashboard,
                'user_id': request.user.id
            })
            
        except Exception as e:
            logger.error(f"Unexpected error in dashboard_switch_api for user {request.user.id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=500)
    
    return JsonResponse({
        'success': False, 
        'error': 'Method not allowed'
    }, status=405)