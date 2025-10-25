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
from django.contrib.auth.decorators import user_passes_test
from .services import AuthenticationService

# Helper decorators for 3-group authentication system
def require_staff(view_func):
    """Decorator to require Staff group membership"""
    def check_staff(user):
        return AuthenticationService.check_group_access(user, 'Staff')
    return user_passes_test(check_staff)(view_func)

def require_autocare(view_func):
    """Decorator to require AutoCare group membership"""
    def check_autocare(user):
        return AuthenticationService.check_group_access(user, 'AutoCare')
    return user_passes_test(check_autocare)(view_func)

def require_autoassess(view_func):
    """Decorator to require AutoAssess group membership"""
    def check_autoassess(user):
        return AuthenticationService.check_group_access(user, 'AutoAssess')
    return user_passes_test(check_autoassess)(view_func)

def require_any_group_simple(groups):
    """Decorator to require membership in any of the specified groups"""
    def decorator(view_func):
        def check_groups(user):
            for group in groups:
                if AuthenticationService.check_group_access(user, group):
                    return True
            return False
        return user_passes_test(check_groups)(view_func)
    return decorator

# Create your views here.

def home(request):
    """
    Home/Landing page view.
    Redirects authenticated users to dashboard, shows landing page to unauthenticated users.
    """
    if request.user.is_authenticated:
        # Redirect authenticated users to dashboard
        return redirect('dashboard')
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
            
            # Set session expiry to 90 days for persistent login
            request.session.set_expiry(90 * 24 * 60 * 60)
            
            login(request, user)
            
            # Get next URL from POST data or GET parameter
            next_url = request.POST.get('next') or request.GET.get('next')
            
            # Use DashboardRouter for intelligent post-login routing
            from .services import DashboardRouter
            try:
                redirect_url = DashboardRouter.get_post_login_redirect(user, next_url)
                
                # Convert URL to view name if needed for Django redirect
                if redirect_url.startswith('/'):
                    # Convert URL to view name for Django redirect using the calculated URL
                    redirect_target = get_post_login_redirect(user, redirect_url)
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
    Dashboard view that redirects users to their appropriate dashboard based on group membership.
    Matches the AutoAssess implementation pattern.
    """
    import logging
    from django.shortcuts import redirect
    logger = logging.getLogger(__name__)

    logger.info(f"Dashboard access - User: {request.user.id if request.user.is_authenticated else 'Anonymous'}")

    # Use AuthenticationService to determine dashboard access
    if request.user.is_authenticated:
        try:
            permissions = AuthenticationService.get_user_permissions(request.user)
            logger.info(f"User permissions: {permissions}")

            # Check if user has AutoCare dashboard access
            if 'autocare' in permissions.available_dashboards:
                logger.info(f"AutoCare user {request.user.id} ({request.user.username}) redirecting to AutoCare dashboard")
                return redirect('notifications:autocare_dashboard')
            
            # Check if user has AutoAssess dashboard access
            elif 'autoassess' in permissions.available_dashboards:
                logger.info(f"AutoAssess user {request.user.id} ({request.user.username}) redirecting to AutoAssess dashboard")
                return redirect('insurance_app:assessment_dashboard')
            
            # Staff users get redirected to admin or smart dashboard
            elif 'staff' in permissions.available_dashboards:
                logger.info(f"Staff user {request.user.id} ({request.user.username}) using smart dashboard")
                return render(request, 'dashboard/smart_dashboard.html', {})

        except Exception as e:
            logger.error(f"Error getting user permissions for dashboard: {str(e)}")

    # For unauthenticated users or users without specific group access, use smart dashboard
    logger.info(f"User accessing smart dashboard")
    return render(request, 'dashboard/smart_dashboard.html', {})


# Removed render_customer_dashboard_context function - no longer needed with simplified dashboard routing

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
                
                # Start onboarding workflow - redirect to onboarding step 1
                return redirect('onboarding:onboarding_step_1')
                
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


def get_post_login_redirect(user, redirect_url=None):
    """
    Determine the appropriate redirect URL after login based on user groups and organization.
    Uses the DashboardRouter for intelligent routing logic.
    
    This function is kept for backward compatibility but delegates to DashboardRouter.
    """
    from .services import DashboardRouter
    
    # If redirect_url is provided, use it directly for URL-to-view conversion
    if redirect_url:
        return _convert_url_to_view_name(redirect_url)
    
    # Use the new DashboardRouter for intelligent routing
    redirect_url = DashboardRouter.get_post_login_redirect(user)
    
    # Convert absolute URLs to view names for Django redirect compatibility
    return _convert_url_to_view_name(redirect_url)


def _convert_url_to_view_name(redirect_url):
    """
    Convert absolute URL to Django view name for redirect compatibility.
    """
    url_to_view_mapping = {
        '/dashboard/': 'dashboard',
        '/notifications/dashboard/': 'notifications:autocare_dashboard',
        '/insurance/': 'insurance:insurance_dashboard',
        '/dashboard-selector/': 'dashboard_selector',
        '/access-denied/': 'access_denied',
        '/': 'home'
    }
    
    # Check for exact matches first
    if redirect_url in url_to_view_mapping:
        return url_to_view_mapping[redirect_url]
    
    # Check for URL patterns with query parameters
    for url_pattern, view_name in url_to_view_mapping.items():
        if redirect_url.startswith(url_pattern) and redirect_url != '/':
            return view_name
    
    # If no mapping found, return the URL as-is
    return redirect_url


def access_denied(request):
    """
    Simplified access denied view for 3-group authentication system.
    """
    context = {
        'error_type': 'access_denied',
        'error_message': 'You do not have permission to access this resource.',
        'user_authenticated': request.user.is_authenticated,
        'user_groups': [],
        'available_dashboards': []
    }
    
    if request.user.is_authenticated:
        # Get user's groups and available dashboards
        permissions = AuthenticationService.get_user_permissions(request.user)
        context.update({
            'user_groups': permissions.groups,
            'available_dashboards': permissions.available_dashboards,
            'has_access': permissions.has_access
        })
        
        # Determine specific error message
        if not permissions.groups:
            context['error_message'] = 'You are not assigned to any groups. Please contact an administrator.'
        elif not permissions.has_access:
            context['error_message'] = 'You do not have access to any dashboards. Please contact an administrator.'
    else:
        context['error_message'] = 'You must be logged in to access this resource.'
    
    return render(request, 'errors/access_denied.html', context)


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


@require_any_group_simple(['Staff', 'AutoCare', 'AutoAssess'])
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
        
        # Prepare dashboard options for template using simplified system
        from .services import get_available_dashboards
        dashboard_options = get_available_dashboards(request.user)
        
        # Get default dashboard
        default_dashboard = permissions.default_dashboard
        
        context = {
            'dashboard_options': dashboard_options,
            'user_permissions': permissions,
            'default_dashboard': default_dashboard
        }
        
        return render(request, 'dashboard/dashboard_selector.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in dashboard_selector for user {request.user.id}: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return redirect('access_denied')


@require_any_group_simple(['Staff', 'AutoCare', 'AutoAssess'])
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
        
        # Validate that user has access to the requested dashboard using simplified system
        permissions = AuthenticationService.get_user_permissions(request.user)
        if dashboard_name not in permissions.available_dashboards:
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


@require_any_group_simple(['Staff', 'AutoCare', 'AutoAssess'])
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


@login_required
@require_autocare
def switch_vehicle(request):
    """
    API endpoint for switching vehicles in the dashboard.
    Handles AJAX requests to update dashboard data for selected vehicle.
    """
    if request.method == 'POST':
        try:
            import json
            
            # Parse JSON data
            data = json.loads(request.body)
            vehicle_id = data.get('vehicle_id')
            
            if not vehicle_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Vehicle ID is required'
                }, status=400)
            
            # Get the vehicle and verify ownership
            try:
                vehicle_ownership = VehicleOwnership.objects.get(
                    vehicle_id=vehicle_id,
                    user=request.user
                )
                vehicle = vehicle_ownership.vehicle
            except VehicleOwnership.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Vehicle not found or access denied'
                }, status=404)
            
            # Get vehicle data for dashboard update
            vehicle_data = {
                'id': vehicle.id,
                'make': vehicle.make,
                'model': vehicle.model,
                'manufacture_year': vehicle.manufacture_year,
                'vin': vehicle.vin,
                'current_mileage': vehicle.current_mileage,
                'color': vehicle.color,
                'transmission': vehicle.transmission,
                'fuel_type': vehicle.fuel_type,
                'engine_size': vehicle.engine_size,
            }
            
            # Add image URL if available
            vehicle_image = VehicleImage.objects.filter(vehicle=vehicle).first()
            if vehicle_image and vehicle_image.image:
                vehicle_data['image_url'] = vehicle_image.image.url
            
            # Get health status (mock data for now)
            vehicle_data['health_status'] = {
                'score': 85,
                'status': 'Excellent'
            }
            
            # Get next service information (mock data for now)
            vehicle_data['next_service'] = {
                'type': 'Oil Change & Inspection',
                'due_date': 'March 15, 2025',
                'due_mileage': 45000
            }
            
            # Get estimated value (mock data for now)
            vehicle_data['estimated_value'] = {
                'amount': 24500,
                'change_percent': 2.3
            }
            
            # Try to get real maintenance data
            try:
                latest_maintenance = MaintenanceRecord.objects.filter(
                    vehicle=vehicle
                ).order_by('-date_performed').first()
                
                if latest_maintenance:
                    vehicle_data['last_service'] = {
                        'type': latest_maintenance.service_type,
                        'date': latest_maintenance.date_performed.strftime('%B %d, %Y'),
                        'provider': latest_maintenance.service_provider,
                        'cost': float(latest_maintenance.cost) if latest_maintenance.cost else 0
                    }
            except Exception as e:
                # If maintenance data fails, continue without it
                pass
            
            # Store selected vehicle in session for future requests
            request.session['selected_vehicle_id'] = vehicle_id
            
            return JsonResponse({
                'success': True,
                'vehicle_data': vehicle_data,
                'message': 'Vehicle switched successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)