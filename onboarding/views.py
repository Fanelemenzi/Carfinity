from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import PendingVehicleOnboarding
from .forms import ClientForm, VehicleForm, VehicleStatusForm, VehicleEquipmentForm, VehicleImagesForm
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
