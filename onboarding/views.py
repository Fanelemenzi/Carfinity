from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PendingVehicleOnboarding, CustomerOnboarding, VehicleOnboarding
from .forms import ClientForm, VehicleForm, VehicleStatusForm, VehicleEquipmentForm, VehicleImagesForm, CustomerOnboardingForm, VehicleOnboardingForm
import datetime
from decimal import Decimal
import cloudinary.uploader

def serialize_form_data(cleaned_data):
    # Convert date/datetime/decimal fields to string for session storage
    result = {}
    for k, v in cleaned_data.items():
        if isinstance(v, (datetime.date, datetime.datetime)):
            result[k] = v.isoformat()
        elif isinstance(v, Decimal):
            result[k] = str(v)
        elif hasattr(v, 'id'):
            # For model instances, store the id
            result[k] = v.id
        else:
            result[k] = v
    return result

# --- Multi-step onboarding using sessions ---
def onboard_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            request.session['onboarding_client'] = serialize_form_data(form.cleaned_data)
            return redirect('onboard_vehicle')
    else:
        form = ClientForm()
    return render(request, 'onboarding/onboard_vehicle_client.html', {'form': form})

def onboard_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            request.session['onboarding_vehicle'] = serialize_form_data(form.cleaned_data)
            return redirect('onboard_status')
    else:
        form = VehicleForm()
    return render(request, 'onboarding/onboard_vehicle_vehicle.html', {'form': form})

def onboard_status(request):
    if request.method == 'POST':
        form = VehicleStatusForm(request.POST)
        if form.is_valid():
            request.session['onboarding_status'] = serialize_form_data(form.cleaned_data)
            return redirect('onboard_equipment')
    else:
        form = VehicleStatusForm()
    return render(request, 'onboarding/onboard_vehicle_status.html', {'form': form})

def onboard_equipment(request):
    if request.method == 'POST':
        form = VehicleEquipmentForm(request.POST)
        if form.is_valid():
            request.session['onboarding_equipment'] = serialize_form_data(form.cleaned_data)
            return redirect('onboard_images')
    else:
        form = VehicleEquipmentForm()
    return render(request, 'onboarding/onboard_vehicle_equipment.html', {'form': form})

def onboard_images(request):
    if request.method == 'POST':
        form = VehicleImagesForm(request.POST, request.FILES)
        if form.is_valid():
            # Upload images to Cloudinary and store URLs
            image_data = {}
            for field_name, image_file in request.FILES.items():
                if image_file:
                    # Upload to Cloudinary
                    result = cloudinary.uploader.upload(
                        image_file,
                        folder="vehicle_onboarding",
                        public_id=f"{request.user.id}_{field_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        transformation=[
                            {'width': 1200, 'height': 800, 'crop': 'limit'},
                            {'quality': 'auto'}
                        ]
                    )
                    image_data[field_name] = {
                        'url': result['secure_url'],
                        'public_id': result['public_id'],
                        'filename': image_file.name
                    }
            
            request.session['onboarding_images'] = image_data
            return redirect('onboard_complete')
    else:
        form = VehicleImagesForm()
    return render(request, 'onboarding/onboard_vehicle_images.html', {'form': form})

def onboard_complete(request):
    client_data = request.session.get('onboarding_client', {})
    vehicle_data = request.session.get('onboarding_vehicle', {})
    status_data = request.session.get('onboarding_status', {})
    equipment_data = request.session.get('onboarding_equipment', {})
    image_data = request.session.get('onboarding_images', {})
    
    data = {**client_data, **vehicle_data, **status_data, **equipment_data}
    
    # Fetch the User object using the stored ID
    client_user = User.objects.get(id=client_data.get('client')) if client_data.get('client') else None
    
    # Build ownership_data (assign client and start_date)
    ownership_data = {
        'owner_id': client_data.get('client'),
        'start_date': vehicle_data.get('start_date'),
    }
    
    PendingVehicleOnboarding.objects.create(
        submitted_by=request.user,
        client=client_user,
        vehicle_data=vehicle_data,
        ownership_data=ownership_data,
        status_data=status_data,
        equipment_data=equipment_data,
        image_data=image_data,
    )
    
    # Clear session data
    for key in ['onboarding_client', 'onboarding_vehicle', 'onboarding_status', 'onboarding_equipment', 'onboarding_images']:
        if key in request.session:
            del request.session[key]
    
    return render(request, 'onboarding/onboard_vehicle_done.html', {'data': data})


# --- Multi-Step Onboarding Workflow ---
@login_required
def onboarding_step_1(request):
    """Step 1: Welcome and basic information"""
    # Check if user already completed onboarding
    try:
        existing_onboarding = CustomerOnboarding.objects.get(user=request.user)
        messages.info(request, "You've already completed onboarding. You can update your information below.")
        return redirect('onboarding:onboarding_step_2')
    except CustomerOnboarding.DoesNotExist:
        pass
    
    if request.method == 'POST':
        # Store basic info in session and move to step 2
        request.session['onboarding_step_1'] = {
            'customer_type': request.POST.get('customer_type'),
            'preferred_communication': request.POST.get('preferred_communication'),
            'service_radius': request.POST.get('service_radius'),
        }
        return redirect('onboarding:onboarding_step_2')
    
    return render(request, 'onboarding/step_1_welcome.html')

@login_required
def onboarding_step_2(request):
    """Step 2: Service preferences and budget"""
    if 'onboarding_step_1' not in request.session:
        messages.warning(request, "Please start from the beginning.")
        return redirect('onboarding:onboarding_step_1')
    
    if request.method == 'POST':
        request.session['onboarding_step_2'] = {
            'monthly_maintenance_budget': request.POST.get('monthly_maintenance_budget'),
            'maintenance_knowledge': request.POST.get('maintenance_knowledge'),
            'primary_goal': request.POST.get('primary_goal'),
            'service_priority': request.POST.get('service_priority'),
        }
        return redirect('onboarding:onboarding_step_3')
    
    return render(request, 'onboarding/step_2_preferences.html')

@login_required
def onboarding_step_3(request):
    """Step 3: Vehicle information"""
    if 'onboarding_step_2' not in request.session:
        messages.warning(request, "Please complete the previous steps.")
        return redirect('onboarding:onboarding_step_1')
    
    if request.method == 'POST':
        request.session['onboarding_step_3'] = {
            'vin_number': request.POST.get('vin_number'),
            'make': request.POST.get('make'),
            'model': request.POST.get('model'),
            'year': request.POST.get('year'),
            'current_odometer': request.POST.get('current_odometer'),
            'primary_usage': request.POST.get('primary_usage'),
        }
        return redirect('onboarding:onboarding_step_4')
    
    return render(request, 'onboarding/step_3_vehicle.html')

@login_required
def onboarding_step_4(request):
    """Step 4: Final preferences and completion"""
    if 'onboarding_step_3' not in request.session:
        messages.warning(request, "Please complete the previous steps.")
        return redirect('onboarding:onboarding_step_1')
    
    if request.method == 'POST':
        try:
            # Combine all session data
            step_1_data = request.session.get('onboarding_step_1', {})
            step_2_data = request.session.get('onboarding_step_2', {})
            step_3_data = request.session.get('onboarding_step_3', {})
            step_4_data = {
                'preferred_payment_model': request.POST.get('preferred_payment_model'),
                'parts_preference': request.POST.get('parts_preference'),
                'how_heard_about_service': request.POST.get('how_heard_about_service'),
            }
            
            # Create customer onboarding record
            customer_data = {**step_1_data, **step_2_data, **step_4_data}
            customer_onboarding = CustomerOnboarding.objects.create(
                user=request.user,
                **customer_data
            )
            
            # Create vehicle onboarding record
            vehicle_data = {**step_3_data}
            vehicle_data['estimated_annual_mileage'] = request.POST.get('estimated_annual_mileage', '10k_15k')
            vehicle_data['current_condition'] = request.POST.get('current_condition', 'good')
            vehicle_data['maintenance_preference'] = request.POST.get('maintenance_preference', 'cost_effective')
            
            VehicleOnboarding.objects.create(
                customer_onboarding=customer_onboarding,
                **vehicle_data
            )
            
            # Clear session data
            for key in ['onboarding_step_1', 'onboarding_step_2', 'onboarding_step_3']:
                if key in request.session:
                    del request.session[key]
            
            # Mark onboarding as complete
            request.session['onboarding_completed'] = True
            
            messages.success(request, "Onboarding completed successfully! Welcome to Carfinity.")
            return redirect('onboarding:onboarding_complete')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completing onboarding for user {request.user.id}: {str(e)}")
            messages.error(request, "An error occurred while completing your onboarding. Please try again.")
    
    return render(request, 'onboarding/step_4_final.html')

@login_required
def onboarding_complete(request):
    """Onboarding completion and dashboard assignment"""
    # Check if user completed onboarding
    if not request.session.get('onboarding_completed'):
        try:
            CustomerOnboarding.objects.get(user=request.user)
        except CustomerOnboarding.DoesNotExist:
            messages.warning(request, "Please complete the onboarding process first.")
            return redirect('onboarding:onboarding_step_1')
    
    # Clear the completion flag
    if 'onboarding_completed' in request.session:
        del request.session['onboarding_completed']
    
    # Determine dashboard assignment based on user groups or default behavior
    from .services import OnboardingService
    dashboard_url = OnboardingService.assign_user_dashboard(request.user)
    
    context = {
        'dashboard_url': dashboard_url,
        'user': request.user,
    }
    
    return render(request, 'onboarding/onboarding_complete.html', context)

# --- Legacy Customer & Vehicle Onboarding Survey (kept for compatibility) ---
@login_required
def customer_vehicle_survey(request):
    """Combined customer and vehicle onboarding survey - Legacy version"""
    
    # Check if user already completed onboarding
    existing_customer_onboarding = None
    existing_vehicle_onboarding = None
    
    try:
        existing_customer_onboarding = CustomerOnboarding.objects.get(user=request.user)
        existing_vehicle_onboarding = VehicleOnboarding.objects.filter(
            customer_onboarding=existing_customer_onboarding
        ).first()
        
        # If updating, show a message
        if request.method == 'GET':
            messages.info(request, "You can update your onboarding information below.")
    except CustomerOnboarding.DoesNotExist:
        pass
    
    if request.method == 'POST':
        customer_form = CustomerOnboardingForm(request.POST)
        vehicle_form = VehicleOnboardingForm(request.POST)
        
        # Debug: Print form data and errors
        print("=== FORM SUBMISSION DEBUG ===")
        print("Customer form valid:", customer_form.is_valid())
        print("Vehicle form valid:", vehicle_form.is_valid())
        
        if not customer_form.is_valid():
            print("Customer form errors:", customer_form.errors)
        if not vehicle_form.is_valid():
            print("Vehicle form errors:", vehicle_form.errors)
        
        if customer_form.is_valid() and vehicle_form.is_valid():
            try:
                # Save or update customer onboarding
                if existing_customer_onboarding:
                    # Update existing record
                    for field, value in customer_form.cleaned_data.items():
                        setattr(existing_customer_onboarding, field, value)
                    existing_customer_onboarding.save()
                    customer_onboarding = existing_customer_onboarding
                    action_message = "updated"
                else:
                    # Create new record
                    customer_onboarding = customer_form.save(commit=False)
                    customer_onboarding.user = request.user
                    customer_onboarding.save()
                    action_message = "completed"
                
                # Save or update vehicle onboarding
                if existing_vehicle_onboarding:
                    # Update existing record
                    for field, value in vehicle_form.cleaned_data.items():
                        setattr(existing_vehicle_onboarding, field, value)
                    existing_vehicle_onboarding.save()
                else:
                    # Create new record
                    vehicle_onboarding = vehicle_form.save(commit=False)
                    vehicle_onboarding.customer_onboarding = customer_onboarding
                    vehicle_onboarding.save()
                
                messages.success(request, f"Thank you! Your onboarding information has been {action_message} successfully. Welcome to your dashboard!")
                return redirect('dashboard')
            except Exception as e:
                print("Exception during save:", str(e))
                messages.error(request, f"An error occurred while saving your information: {str(e)}")
        else:
            # If forms have errors, they will be displayed in the template
            print("Form validation failed - showing errors to user")
            messages.error(request, "Please correct the errors below and try again.")
    else:
        # Pre-populate forms with existing data if available
        customer_form = CustomerOnboardingForm(instance=existing_customer_onboarding)
        vehicle_form = VehicleOnboardingForm(instance=existing_vehicle_onboarding)
    
    return render(request, 'onboarding/survey.html', {
        'customer_form': customer_form,
        'vehicle_form': vehicle_form,
    })


@login_required
def onboarding_complete_view(request):
    """Simple completion page after survey"""
    return render(request, 'onboarding/onboarding_complete.html')


@login_required
def technician_vehicle_onboarding(request):
    """Vehicle onboarding form for technicians"""
    if request.method == 'POST':
        form = VehicleOnboardingForm(request.POST)
        if form.is_valid():
            # Create a customer onboarding record if it doesn't exist
            customer_onboarding, created = CustomerOnboarding.objects.get_or_create(
                user=request.user,
                defaults={
                    'customer_type': 'individual',
                    'preferred_communication': 'email',
                    'reminder_frequency': 'monthly',
                    'service_radius': '15',
                    'monthly_maintenance_budget': 'pay_as_needed',
                    'maintenance_knowledge': 'intermediate',
                    'primary_goal': 'avoid_breakdowns',
                    'service_priority': 'service_quality',
                    'preferred_payment_model': 'pay_per_service',
                    'parts_preference': 'quality_aftermarket',
                    'extended_warranty_interest': 'not_interested',
                    'how_heard_about_service': 'mechanic_referral',
                }
            )
            
            # Save the vehicle onboarding
            vehicle_onboarding = form.save(commit=False)
            vehicle_onboarding.customer_onboarding = customer_onboarding
            vehicle_onboarding.save()
            
            messages.success(request, f"Vehicle onboarding completed successfully for {vehicle_onboarding.year} {vehicle_onboarding.make} {vehicle_onboarding.model}!")
            return redirect('maintenance_history:technician_dashboard')
    else:
        form = VehicleOnboardingForm()
    
    return render(request, 'onboarding/technician_vehicle_onboarding.html', {
        'form': form,
    })
