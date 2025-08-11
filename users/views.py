from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from vehicles.models import Vehicle, VehicleStatus, VehicleOwnership, VehicleImage  # Add VehicleImage
from maintenance_history.models import MaintenanceRecord, Inspection
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
    owned_vehicles = []
    scheduled_maintenance = []
    inspections = []
    selected_vehicle = None
    if request.user.is_authenticated:
        owned_vehicles = VehicleOwnership.objects.filter(user=request.user, is_current_owner=True).select_related('vehicle')
        vehicle_id = request.GET.get('vehicle_id')
        if vehicle_id:
            from maintenance.models import ScheduledMaintenance
            from maintenance_history.models import Inspection
            selected_vehicle = Vehicle.objects.get(id=vehicle_id)
            # Scheduled Maintenance
            scheduled_maintenance = ScheduledMaintenance.objects.filter(
                assigned_plan__vehicle=selected_vehicle
            )
            # Inspections
            inspections = Inspection.objects.filter(vehicle=selected_vehicle)
    return render(request, 'dashboard/dashboard.html', {
        'owned_vehicles': owned_vehicles,
        'scheduled_maintenance': scheduled_maintenance,
        'inspections': inspections,
        'selected_vehicle': selected_vehicle,
    })

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
            
            # Redirect to dashboard
            return redirect('typeform_onboarding')
    else:
        form = SignUpForm()
    
    return render(request, 'public/register.html', {
        'form': form
    })

def search(request):
    return render(request, 'search/search.html', {})

def search_results(request):
    vin = request.GET.get('vin')
    if not vin:
        messages.error(request, "Please enter a VIN number")
        return redirect('search')
    
    try:
        # Get the vehicle
        vehicle = get_object_or_404(Vehicle, vin=vin)
        
        # Get vehicle status
        vehicle_status = get_object_or_404(VehicleStatus, vehicle=vehicle)
        
        # Get maintenance records
        maintenance_records = MaintenanceRecord.objects.filter(vehicle=vehicle).order_by('-date_performed')
        
        # Get inspections
        inspections = Inspection.objects.filter(vehicle=vehicle).order_by('-inspection_date')
        
        # Get vehicle images - Add this section
        vehicle_images = VehicleImage.objects.filter(vehicle=vehicle).order_by('-is_primary', '-uploaded_at')
        
        # Get vehicle equipment information
        powertrain = PowertrainAndDrivetrain.objects.filter(vehicle=vehicle).first()
        chassis = ChassisSuspensionAndBraking.objects.filter(vehicle=vehicle).first()
        electrical = ElectricalSystem.objects.filter(vehicle=vehicle).first()
        exterior = ExteriorFeaturesAndBody.objects.filter(vehicle=vehicle).first()
        safety = ActiveSafetyAndADAS.objects.filter(vehicle=vehicle).first()
        
        context = {
            'vehicle': vehicle,
            'status': vehicle_status,
            'maintenance_records': maintenance_records,
            'inspections': inspections,
            'vehicle_images': vehicle_images,  # Add this to context
            'powertrain': powertrain,
            'chassis': chassis,
            'electrical': electrical,
            'exterior': exterior,
            'safety': safety,
        }
        
        return render(request, 'search/search-results.html', context)
        
    except Vehicle.DoesNotExist:
        messages.error(request, f"No vehicle found with VIN: {vin}")
        return redirect('search')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('search')



#def create_record(request):
#    return render(request, 'maintenance/create_record.html', {})

@login_required
def typeform_redirect(request):
    return render(request, 'public/typeform_embed.html')