from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from .models import PendingVehicleOnboarding, CustomerOnboarding, VehicleOnboarding
from .forms import ClientForm, VehicleForm, VehicleStatusForm, VehicleEquipmentForm, VehicleImagesForm, CustomerOnboardingForm, VehicleOnboardingForm
import datetime
from decimal import Decimal
import cloudinary.uploader
import uuid

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
def start_onboarding(request):
    """Start a new onboarding process - Step 1: Welcome and Customer Type"""
    # Check if user already completed onboarding
    try:
        existing_onboarding = CustomerOnboarding.objects.get(user=request.user)
        messages.info(request, "You've already completed onboarding. You can continue or update your information.")
        return redirect('onboarding:continue_onboarding', onboarding_id=existing_onboarding.id)
    except CustomerOnboarding.DoesNotExist:
        pass
    
    if request.method == 'POST':
        # Create initial onboarding record
        customer_onboarding = CustomerOnboarding.objects.create(
            user=request.user,
            customer_type=request.POST.get('customer_type', 'individual'),
            preferred_communication=request.POST.get('preferred_communication', 'email'),
            service_radius=request.POST.get('service_radius', '15'),
            status='in_progress'
        )
        
        messages.success(request, f'Onboarding started successfully! ID: {customer_onboarding.id}')
        return redirect('onboarding:service_preferences', onboarding_id=customer_onboarding.id)
    
    context = {
        'step': 1,
        'total_steps': 6
    }
    return render(request, 'onboarding/start_onboarding.html', context)

@login_required
def service_preferences(request, onboarding_id):
    """Step 2: Service Preferences and Budget"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    if request.method == 'POST':
        # Update onboarding record with service preferences
        onboarding.monthly_maintenance_budget = request.POST.get('monthly_maintenance_budget', 'pay_as_needed')
        onboarding.maintenance_knowledge = request.POST.get('maintenance_knowledge', 'basic')
        onboarding.primary_goal = request.POST.get('primary_goal', 'avoid_breakdowns')
        onboarding.service_priority = request.POST.get('service_priority', 'service_quality')
        onboarding.save()
        
        messages.success(request, 'Service preferences saved!')
        return redirect('onboarding:vehicle_information', onboarding_id=onboarding.id)
    
    context = {
        'onboarding': onboarding,
        'step': 2,
        'total_steps': 6
    }
    return render(request, 'onboarding/service_preferences.html', context)

@login_required
def vehicle_information(request, onboarding_id):
    """Step 3: Vehicle Information"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    # Get or create vehicle onboarding record
    try:
        vehicle_onboarding = onboarding.vehicle_onboarding
    except VehicleOnboarding.DoesNotExist:
        vehicle_onboarding = None
    
    if request.method == 'POST':
        # Create or update vehicle onboarding
        if vehicle_onboarding:
            # Update existing
            vehicle_onboarding.vin_number = request.POST.get('vin_number', '')
            vehicle_onboarding.make = request.POST.get('make', '')
            vehicle_onboarding.model = request.POST.get('model', '')
            vehicle_onboarding.year = request.POST.get('year')
            vehicle_onboarding.current_odometer = request.POST.get('current_odometer')
            vehicle_onboarding.primary_usage = request.POST.get('primary_usage', 'daily_commute')
            vehicle_onboarding.save()
        else:
            # Create new
            vehicle_onboarding = VehicleOnboarding.objects.create(
                customer_onboarding=onboarding,
                vin_number=request.POST.get('vin_number', ''),
                make=request.POST.get('make', ''),
                model=request.POST.get('model', ''),
                year=request.POST.get('year'),
                current_odometer=request.POST.get('current_odometer'),
                primary_usage=request.POST.get('primary_usage', 'daily_commute')
            )
        
        messages.success(request, 'Vehicle information saved!')
        return redirect('onboarding:maintenance_preferences', onboarding_id=onboarding.id)
    
    context = {
        'onboarding': onboarding,
        'vehicle_onboarding': vehicle_onboarding,
        'step': 3,
        'total_steps': 6
    }
    return render(request, 'onboarding/vehicle_information.html', context)

@login_required
def maintenance_preferences(request, onboarding_id):
    """Step 4: Maintenance Preferences"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    try:
        vehicle_onboarding = onboarding.vehicle_onboarding
    except VehicleOnboarding.DoesNotExist:
        messages.error(request, "Please complete vehicle information first.")
        return redirect('onboarding:vehicle_information', onboarding_id=onboarding.id)
    
    if request.method == 'POST':
        # Update vehicle maintenance preferences
        vehicle_onboarding.estimated_annual_mileage = request.POST.get('estimated_annual_mileage', '10k_15k')
        vehicle_onboarding.current_condition = request.POST.get('current_condition', 'good')
        vehicle_onboarding.maintenance_preference = request.POST.get('maintenance_preference', 'cost_effective')
        vehicle_onboarding.save()
        
        messages.success(request, 'Maintenance preferences saved!')
        return redirect('onboarding:payment_preferences', onboarding_id=onboarding.id)
    
    context = {
        'onboarding': onboarding,
        'vehicle_onboarding': vehicle_onboarding,
        'step': 4,
        'total_steps': 6
    }
    return render(request, 'onboarding/maintenance_preferences.html', context)

@login_required
def payment_preferences(request, onboarding_id):
    """Step 5: Payment and Final Preferences"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    if request.method == 'POST':
        # Update final preferences
        onboarding.preferred_payment_model = request.POST.get('preferred_payment_model', 'pay_per_service')
        onboarding.parts_preference = request.POST.get('parts_preference', 'quality_aftermarket')
        onboarding.extended_warranty_interest = request.POST.get('extended_warranty_interest', 'not_interested')
        onboarding.how_heard_about_service = request.POST.get('how_heard_about_service', 'online_search')
        onboarding.save()
        
        messages.success(request, 'Payment preferences saved!')
        return redirect('onboarding:onboarding_review', onboarding_id=onboarding.id)
    
    context = {
        'onboarding': onboarding,
        'step': 5,
        'total_steps': 6
    }
    return render(request, 'onboarding/payment_preferences.html', context)

@login_required
def onboarding_review(request, onboarding_id):
    """Step 6: Review and Complete Onboarding"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    try:
        vehicle_onboarding = onboarding.vehicle_onboarding
    except VehicleOnboarding.DoesNotExist:
        vehicle_onboarding = None
    
    if request.method == 'POST':
        try:
            # Mark onboarding as completed
            onboarding.status = 'completed'
            onboarding.completed_date = datetime.datetime.now()
            onboarding.save()
            
            # Clear any session data
            for key in ['onboarding_step_1', 'onboarding_step_2', 'onboarding_step_3', 'onboarding_step_4']:
                if key in request.session:
                    del request.session[key]
            
            # Mark onboarding as complete in session
            request.session['onboarding_completed'] = True
            
            messages.success(request, "Onboarding completed successfully! Welcome to Carfinity.")
            return redirect('onboarding:onboarding_complete')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completing onboarding for user {request.user.id}: {str(e)}")
            messages.error(request, "An error occurred while completing your onboarding. Please try again.")
    
    context = {
        'onboarding': onboarding,
        'vehicle_onboarding': vehicle_onboarding,
        'step': 6,
        'total_steps': 6
    }
    return render(request, 'onboarding/onboarding_review.html', context)

@login_required
def continue_onboarding(request, onboarding_id):
    """Continue onboarding from current step"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    # Calculate progress
    completed_steps = 0
    total_steps = 6
    
    # Check which steps are completed
    step_progress = {
        'customer_info': {
            'title': 'Customer Information',
            'description': 'Basic customer type and communication preferences',
            'completed': bool(onboarding.customer_type and onboarding.preferred_communication),
            'current': False,
            'available': True,
            'url': '#'  # Already completed in start_onboarding
        },
        'service_preferences': {
            'title': 'Service Preferences',
            'description': 'Budget and maintenance preferences',
            'completed': bool(onboarding.monthly_maintenance_budget and onboarding.maintenance_knowledge),
            'current': False,
            'available': True,
            'url': 'onboarding:service_preferences'
        },
        'vehicle_information': {
            'title': 'Vehicle Information',
            'description': 'Vehicle details and specifications',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'onboarding:vehicle_information'
        },
        'maintenance_preferences': {
            'title': 'Maintenance Preferences',
            'description': 'Vehicle condition and maintenance approach',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'onboarding:maintenance_preferences'
        },
        'payment_preferences': {
            'title': 'Payment Preferences',
            'description': 'Payment model and parts preferences',
            'completed': bool(onboarding.preferred_payment_model and onboarding.parts_preference),
            'current': False,
            'available': True,
            'url': 'onboarding:payment_preferences'
        },
        'review_complete': {
            'title': 'Review & Complete',
            'description': 'Review information and complete onboarding',
            'completed': bool(onboarding.status == 'completed'),
            'current': False,
            'available': True,
            'url': 'onboarding:onboarding_review'
        }
    }
    
    # Check vehicle onboarding completion
    try:
        vehicle_onboarding = onboarding.vehicle_onboarding
        step_progress['vehicle_information']['completed'] = bool(
            vehicle_onboarding.make and vehicle_onboarding.model and vehicle_onboarding.year
        )
        step_progress['maintenance_preferences']['completed'] = bool(
            vehicle_onboarding.estimated_annual_mileage and vehicle_onboarding.current_condition
        )
    except VehicleOnboarding.DoesNotExist:
        pass
    
    # Determine current step and update progress
    current_step = None
    for step_name, step_data in step_progress.items():
        if step_data['completed']:
            completed_steps += 1
        elif not current_step and not step_data['completed']:
            current_step = step_name
            step_data['current'] = True
            break
    
    # Update URLs with onboarding ID
    url_mapping = {
        'service_preferences': f"/onboarding/{onboarding_id}/service-preferences/",
        'vehicle_information': f"/onboarding/{onboarding_id}/vehicle-information/",
        'maintenance_preferences': f"/onboarding/{onboarding_id}/maintenance-preferences/",
        'payment_preferences': f"/onboarding/{onboarding_id}/payment-preferences/",
        'onboarding_review': f"/onboarding/{onboarding_id}/review/"
    }
    
    for step_name, step_data in step_progress.items():
        if step_data['url'] != '#':
            url_name = step_data['url'].split(':')[-1]
            step_data['url'] = url_mapping.get(url_name, '#')
    
    progress_percentage = int((completed_steps / total_steps) * 100)
    
    context = {
        'onboarding': onboarding,
        'step_progress': step_progress,
        'progress_percentage': progress_percentage,
        'completed_steps': completed_steps,
        'total_steps': total_steps,
        'current_step': current_step
    }
    
    return render(request, 'onboarding/continue_onboarding.html', context)

@login_required
def onboarding_complete(request):
    """Onboarding completion and dashboard assignment"""
    # Check if user completed onboarding
    if not request.session.get('onboarding_completed'):
        try:
            onboarding = CustomerOnboarding.objects.get(user=request.user, status='completed')
        except CustomerOnboarding.DoesNotExist:
            messages.warning(request, "Please complete the onboarding process first.")
            return redirect('onboarding:start_onboarding')
    
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

@login_required
def update_onboarding_status(request, onboarding_id):
    """Update onboarding status"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['in_progress', 'completed', 'cancelled']:
            old_status = onboarding.status
            onboarding.status = new_status
            if new_status == 'completed':
                onboarding.completed_date = datetime.datetime.now()
            onboarding.save()
            
            messages.success(request, f'Onboarding status updated from {old_status} to {new_status}')
        else:
            messages.error(request, 'Invalid status selected')
    
    return redirect('onboarding:continue_onboarding', onboarding_id=onboarding.id)

@login_required
def delete_onboarding(request, onboarding_id):
    """Delete an onboarding record"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    if request.method == 'POST':
        onboarding_id_display = onboarding.id
        onboarding.delete()
        messages.success(request, f'Onboarding record {onboarding_id_display} deleted successfully!')
        return redirect('onboarding:start_onboarding')
    
    context = {'onboarding': onboarding}
    return render(request, 'onboarding/delete_onboarding.html', context)

# --- Onboarding Dashboard ---
@login_required
def onboarding_dashboard(request):
    """Dashboard showing all onboarding records for the current user"""
    onboardings = CustomerOnboarding.objects.filter(user=request.user).select_related(
        'user'
    ).prefetch_related('vehicle_onboarding').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        onboardings = onboardings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(onboardings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Status counts for dashboard stats
    status_counts = {
        'in_progress': CustomerOnboarding.objects.filter(user=request.user, status='in_progress').count(),
        'completed': CustomerOnboarding.objects.filter(user=request.user, status='completed').count(),
        'cancelled': CustomerOnboarding.objects.filter(user=request.user, status='cancelled').count(),
        'total': CustomerOnboarding.objects.filter(user=request.user).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'status_counts': status_counts,
        'current_status': status_filter,
        'status_choices': [
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
    }
    return render(request, 'onboarding/dashboard.html', context)

# --- Legacy Customer & Vehicle Onboarding Survey (updated for compatibility) ---
@login_required
def customer_vehicle_survey(request):
    """Combined customer and vehicle onboarding survey - Legacy version with new workflow integration"""
    
    # Check if user already completed onboarding
    existing_customer_onboarding = None
    existing_vehicle_onboarding = None
    
    try:
        existing_customer_onboarding = CustomerOnboarding.objects.get(user=request.user)
        existing_vehicle_onboarding = VehicleOnboarding.objects.filter(
            customer_onboarding=existing_customer_onboarding
        ).first()
        
        # If updating, show a message and redirect to new workflow
        if request.method == 'GET':
            messages.info(request, "You can update your onboarding information using our improved workflow.")
            return redirect('onboarding:continue_onboarding', onboarding_id=existing_customer_onboarding.id)
    except CustomerOnboarding.DoesNotExist:
        # Redirect new users to the new workflow
        messages.info(request, "Welcome! Let's get you started with our improved onboarding process.")
        return redirect('onboarding:start_onboarding')
    
    if request.method == 'POST':
        customer_form = CustomerOnboardingForm(request.POST)
        vehicle_form = VehicleOnboardingForm(request.POST)
        
        if customer_form.is_valid() and vehicle_form.is_valid():
            try:
                with transaction.atomic():
                    # Save or update customer onboarding
                    if existing_customer_onboarding:
                        # Update existing record
                        for field, value in customer_form.cleaned_data.items():
                            setattr(existing_customer_onboarding, field, value)
                        existing_customer_onboarding.status = 'completed'
                        existing_customer_onboarding.completed_date = datetime.datetime.now()
                        existing_customer_onboarding.save()
                        customer_onboarding = existing_customer_onboarding
                        action_message = "updated"
                    else:
                        # Create new record
                        customer_onboarding = customer_form.save(commit=False)
                        customer_onboarding.user = request.user
                        customer_onboarding.status = 'completed'
                        customer_onboarding.completed_date = datetime.datetime.now()
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
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in legacy onboarding for user {request.user.id}: {str(e)}")
                messages.error(request, f"An error occurred while saving your information: {str(e)}")
        else:
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
def onboarding_detail(request, onboarding_id):
    """View detailed onboarding information"""
    onboarding = get_object_or_404(CustomerOnboarding, id=onboarding_id, user=request.user)
    
    # Get vehicle onboarding if exists
    try:
        vehicle_onboarding = onboarding.vehicle_onboarding
    except VehicleOnboarding.DoesNotExist:
        vehicle_onboarding = None
    
    # Calculate completion percentage
    total_fields = 15  # Total number of important fields
    completed_fields = 0
    
    # Check customer onboarding completion
    customer_fields = [
        onboarding.customer_type, onboarding.preferred_communication,
        onboarding.monthly_maintenance_budget, onboarding.maintenance_knowledge,
        onboarding.primary_goal, onboarding.service_priority,
        onboarding.preferred_payment_model, onboarding.parts_preference
    ]
    completed_fields += sum(1 for field in customer_fields if field)
    
    # Check vehicle onboarding completion
    if vehicle_onboarding:
        vehicle_fields = [
            vehicle_onboarding.make, vehicle_onboarding.model,
            vehicle_onboarding.year, vehicle_onboarding.current_odometer,
            vehicle_onboarding.primary_usage, vehicle_onboarding.estimated_annual_mileage,
            vehicle_onboarding.current_condition
        ]
        completed_fields += sum(1 for field in vehicle_fields if field)
    
    completion_percentage = int((completed_fields / total_fields) * 100)
    
    context = {
        'onboarding': onboarding,
        'vehicle_onboarding': vehicle_onboarding,
        'completion_percentage': completion_percentage,
        'completed_fields': completed_fields,
        'total_fields': total_fields,
    }
    return render(request, 'onboarding/onboarding_detail.html', context)

@login_required
def onboarding_complete_view(request):
    """Simple completion page after survey - Legacy compatibility"""
    # Redirect to new completion flow
    try:
        onboarding = CustomerOnboarding.objects.get(user=request.user, status='completed')
        return redirect('onboarding:onboarding_complete')
    except CustomerOnboarding.DoesNotExist:
        messages.warning(request, "Please complete the onboarding process first.")
        return redirect('onboarding:start_onboarding')

@login_required
def technician_vehicle_onboarding(request):
    """Vehicle onboarding form for technicians - Updated to use new workflow"""
    if request.method == 'POST':
        form = VehicleOnboardingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create a customer onboarding record if it doesn't exist
                    customer_onboarding, created = CustomerOnboarding.objects.get_or_create(
                        user=request.user,
                        defaults={
                            'customer_type': 'technician',
                            'preferred_communication': 'email',
                            'service_radius': '25',
                            'monthly_maintenance_budget': 'pay_as_needed',
                            'maintenance_knowledge': 'expert',
                            'primary_goal': 'avoid_breakdowns',
                            'service_priority': 'service_quality',
                            'preferred_payment_model': 'pay_per_service',
                            'parts_preference': 'quality_aftermarket',
                            'extended_warranty_interest': 'not_interested',
                            'how_heard_about_service': 'mechanic_referral',
                            'status': 'completed',
                            'completed_date': datetime.datetime.now()
                        }
                    )
                    
                    # If updating existing onboarding, mark as completed
                    if not created and customer_onboarding.status != 'completed':
                        customer_onboarding.status = 'completed'
                        customer_onboarding.completed_date = datetime.datetime.now()
                        customer_onboarding.save()
                    
                    # Save the vehicle onboarding
                    vehicle_onboarding = form.save(commit=False)
                    vehicle_onboarding.customer_onboarding = customer_onboarding
                    vehicle_onboarding.save()
                    
                    messages.success(request, f"Vehicle onboarding completed successfully for {vehicle_onboarding.year} {vehicle_onboarding.make} {vehicle_onboarding.model}!")
                    return redirect('maintenance_history:technician_dashboard')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in technician onboarding for user {request.user.id}: {str(e)}")
                messages.error(request, f"An error occurred while saving vehicle information: {str(e)}")
    else:
        form = VehicleOnboardingForm()
    
    context = {
        'form': form,
        'is_technician': True,
    }
    return render(request, 'onboarding/technician_vehicle_onboarding.html', context)
