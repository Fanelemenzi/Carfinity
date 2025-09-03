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
    if request.method =="POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.success(request, ("There was an error try again"))
            return redirect('login')
    else:
        return render(request, 'public/login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out"))
    return redirect('home')

def dashboard(request):
    from django.db.models import Count, Sum, Avg, Q
    from django.utils import timezone
    from datetime import datetime, timedelta
    from maintenance.models import ScheduledMaintenance, Part
    from maintenance_history.models import Inspection, MaintenanceRecord, PartUsage
    from decimal import Decimal
    
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
    
    if request.user.is_authenticated:
        # Check if user has completed onboarding
        from onboarding.models import CustomerOnboarding
        try:
            user_onboarding = CustomerOnboarding.objects.get(user=request.user)
            onboarding_completed = True
        except CustomerOnboarding.DoesNotExist:
            user_onboarding = None
            onboarding_completed = False
        
        # Get user's vehicles
        owned_vehicles = VehicleOwnership.objects.filter(
            user=request.user, 
            is_current_owner=True
        ).select_related('vehicle')
        
        user_vehicles = [ownership.vehicle for ownership in owned_vehicles]
        
        # Calculate Key Metrics
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
            low_stock_parts = Part.objects.filter(
                stock_quantity__lte=models.F('minimum_stock_level')
            ).order_by('stock_quantity')[:5]
        
        # Handle vehicle selection for detailed view
        vehicle_id = request.GET.get('vehicle_id')
        if vehicle_id:
            try:
                selected_vehicle = Vehicle.objects.get(id=vehicle_id)
                # Scheduled Maintenance for selected vehicle
                scheduled_maintenance = ScheduledMaintenance.objects.filter(
                    assigned_plan__vehicle=selected_vehicle
                ).select_related('task').order_by('due_date')
                
                # Inspections for selected vehicle
                inspections = Inspection.objects.filter(
                    vehicle=selected_vehicle
                ).order_by('-inspection_date')
            except Vehicle.DoesNotExist:
                selected_vehicle = None
    else:
        # User is not authenticated - set default values
        onboarding_completed = False
        user_onboarding = None
    
    return render(request, 'dashboard/dashboard.html', {
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
    })


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

def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
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