from django.shortcuts import render, redirect, get_object_or_404
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from vehicles.models import Vehicle, VehicleStatus
from maintenance_history.models import MaintenanceRecord, Inspection
from vehicle_equip.models import PowertrainAndDrivetrain, ChassisSuspensionAndBraking, ElectricalSystem, ExteriorFeaturesAndBody, ActiveSafetyAndADAS
from django.http import JsonResponse
from .forms import SignUpForm
from .models import Profile, DataConsent

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
    return render(request, 'dashboard/dashboard.html', {})

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
            return redirect('dashboard')
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