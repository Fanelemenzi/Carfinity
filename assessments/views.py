from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from django.core.paginator import Paginator
from .models import (
    VehicleAssessment, ExteriorBodyDamage, WheelsAndTires, InteriorDamage,
    MechanicalSystems, ElectricalSystems, SafetySystems, FrameAndStructural,
    FluidSystems, DocumentationAndIdentification, AssessmentPhoto, AssessmentReport
)
from .forms import (
    VehicleDetailsForm, IncidentLocationForm, ExteriorDamageAssessmentForm,
    WheelsAndTiresAssessmentForm, InteriorDamageAssessmentForm, MechanicalSystemsAssessmentForm,
    ElectricalSystemsAssessmentForm, SafetySystemsAssessmentForm, StructuralAssessmentForm,
    FluidSystemsAssessmentForm, DocumentationAssessmentForm, AssessmentCategorizationForm,
    FinancialInformationForm, AssessmentNotesForm, AssessmentPhotoUploadForm,
    AssessmentReportForm, AssessmentWizardFormSet
)
import uuid
from datetime import datetime


@login_required
def assessment_dashboard(request):
    """Dashboard showing all assessments for the current user"""
    assessments = VehicleAssessment.objects.filter(user=request.user).select_related(
        'organization', 'vehicle', 'assigned_agent'
    ).order_by('-assessment_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        assessments = assessments.filter(status=status_filter)
    
    # Filter by organization if provided
    org_filter = request.GET.get('organization')
    if org_filter:
        assessments = assessments.filter(organization_id=org_filter)
    
    # Pagination
    paginator = Paginator(assessments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Status counts for dashboard stats
    status_counts = {
        'pending': VehicleAssessment.objects.filter(user=request.user, status='pending').count(),
        'in_progress': VehicleAssessment.objects.filter(user=request.user, status='in_progress').count(),
        'completed': VehicleAssessment.objects.filter(user=request.user, status='completed').count(),
        'total': VehicleAssessment.objects.filter(user=request.user).count(),
    }
    
    # Get user's organizations for filtering
    from organizations.models import Organization
    user_organizations = Organization.objects.filter(
        organization_members__user=request.user,
        organization_members__is_active=True
    ).distinct()
    
    context = {
        'page_obj': page_obj,
        'status_counts': status_counts,
        'current_status': status_filter,
        'current_organization': org_filter,
        'user_organizations': user_organizations,
        'status_choices': VehicleAssessment.STATUS_CHOICES,
    }
    return render(request, 'assessments/dashboard.html', context)


@login_required
def start_assessment(request):
    """Start a new assessment - Step 1: Vehicle Details"""
    if request.method == 'POST':
        form = VehicleDetailsForm(request.POST, user=request.user)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.user = request.user
            assessment.assessment_id = f"ASS-{uuid.uuid4().hex[:8].upper()}"
            assessment.status = 'in_progress'
            
            # Auto-assign organization if not set
            if not assessment.organization:
                from organizations.models import Organization
                user_org = Organization.objects.filter(
                    organization_members__user=request.user,
                    organization_members__is_active=True
                ).first()
                if user_org:
                    assessment.organization = user_org
            
            # Auto-assign user as agent if not set
            if not assessment.assigned_agent:
                assessment.assigned_agent = request.user
            
            assessment.save()
            
            messages.success(request, f'Assessment {assessment.assessment_id} started successfully!')
            return redirect('assessments:incident_location', assessment_id=assessment.id)
    else:
        form = VehicleDetailsForm(user=request.user)
    
    context = {
        'form': form,
        'step': 1,
        'total_steps': 16
    }
    return render(request, 'assessments/start_assessment.html', context)


@login_required
def incident_location(request, assessment_id):
    """Step 3: Incident Location and Context"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = IncidentLocationForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Location details saved!')
            return redirect('assessments:exterior_damage', assessment_id=assessment.id)
    else:
        form = IncidentLocationForm(instance=assessment)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 3,
        'total_steps': 16
    }
    return render(request, 'assessments/incident_location.html', context)


@login_required
def exterior_damage_assessment(request, assessment_id):
    """Step 4: Exterior Damage Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        exterior_damage = assessment.exterior_damage
    except ExteriorBodyDamage.DoesNotExist:
        exterior_damage = None
    
    if request.method == 'POST':
        form = ExteriorDamageAssessmentForm(request.POST, instance=exterior_damage)
        if form.is_valid():
            exterior_damage = form.save(commit=False)
            exterior_damage.assessment = assessment
            exterior_damage.save()
            messages.success(request, 'Exterior damage assessment saved!')
            return redirect('assessments:wheels_tires', assessment_id=assessment.id)
    else:
        form = ExteriorDamageAssessmentForm(instance=exterior_damage)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 4,
        'total_steps': 16
    }
    return render(request, 'assessments/exterior_damage.html', context)


@login_required
def wheels_tires_assessment(request, assessment_id):
    """Step 5: Wheels and Tires Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        wheels_tires = assessment.wheels_tires
    except WheelsAndTires.DoesNotExist:
        wheels_tires = None
    
    if request.method == 'POST':
        form = WheelsAndTiresAssessmentForm(request.POST, instance=wheels_tires)
        if form.is_valid():
            wheels_tires = form.save(commit=False)
            wheels_tires.assessment = assessment
            wheels_tires.save()
            messages.success(request, 'Wheels and tires assessment saved!')
            return redirect('assessments:interior_damage', assessment_id=assessment.id)
    else:
        form = WheelsAndTiresAssessmentForm(instance=wheels_tires)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 5,
        'total_steps': 16
    }
    return render(request, 'assessments/wheels_tires.html', context)


@login_required
def interior_damage_assessment(request, assessment_id):
    """Step 6: Interior Damage Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        interior_damage = assessment.interior_damage
    except InteriorDamage.DoesNotExist:
        interior_damage = None
    
    if request.method == 'POST':
        form = InteriorDamageAssessmentForm(request.POST, instance=interior_damage)
        if form.is_valid():
            interior_damage = form.save(commit=False)
            interior_damage.assessment = assessment
            interior_damage.save()
            messages.success(request, 'Interior damage assessment saved!')
            return redirect('assessments:mechanical_systems', assessment_id=assessment.id)
    else:
        form = InteriorDamageAssessmentForm(instance=interior_damage)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 6,
        'total_steps': 16
    }
    return render(request, 'assessments/interior_damage.html', context)


@login_required
def mechanical_systems_assessment(request, assessment_id):
    """Step 7: Mechanical Systems Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        mechanical = assessment.mechanical_systems
    except MechanicalSystems.DoesNotExist:
        mechanical = None
    
    if request.method == 'POST':
        form = MechanicalSystemsAssessmentForm(request.POST, instance=mechanical)
        if form.is_valid():
            mechanical = form.save(commit=False)
            mechanical.assessment = assessment
            mechanical.save()
            messages.success(request, 'Mechanical systems assessment saved!')
            return redirect('assessments:electrical_systems', assessment_id=assessment.id)
    else:
        form = MechanicalSystemsAssessmentForm(instance=mechanical)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 7,
        'total_steps': 16
    }
    return render(request, 'assessments/mechanical_systems.html', context)


@login_required
def electrical_systems_assessment(request, assessment_id):
    """Step 8: Electrical Systems Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        electrical = assessment.electrical_systems
    except ElectricalSystems.DoesNotExist:
        electrical = None
    
    if request.method == 'POST':
        form = ElectricalSystemsAssessmentForm(request.POST, instance=electrical)
        if form.is_valid():
            electrical = form.save(commit=False)
            electrical.assessment = assessment
            electrical.save()
            messages.success(request, 'Electrical systems assessment saved!')
            return redirect('assessments:safety_systems', assessment_id=assessment.id)
    else:
        form = ElectricalSystemsAssessmentForm(instance=electrical)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 8,
        'total_steps': 16
    }
    return render(request, 'assessments/electrical_systems.html', context)


@login_required
def safety_systems_assessment(request, assessment_id):
    """Step 9: Safety Systems Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        safety = assessment.safety_systems
    except SafetySystems.DoesNotExist:
        safety = None
    
    if request.method == 'POST':
        form = SafetySystemsAssessmentForm(request.POST, instance=safety)
        if form.is_valid():
            safety = form.save(commit=False)
            safety.assessment = assessment
            safety.save()
            messages.success(request, 'Safety systems assessment saved!')
            return redirect('assessments:structural_assessment', assessment_id=assessment.id)
    else:
        form = SafetySystemsAssessmentForm(instance=safety)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 9,
        'total_steps': 16
    }
    return render(request, 'assessments/safety_systems.html', context)


@login_required
def structural_assessment(request, assessment_id):
    """Step 10: Structural Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        structural = assessment.frame_structural
    except FrameAndStructural.DoesNotExist:
        structural = None
    
    if request.method == 'POST':
        form = StructuralAssessmentForm(request.POST, instance=structural)
        if form.is_valid():
            structural = form.save(commit=False)
            structural.assessment = assessment
            structural.save()
            messages.success(request, 'Structural assessment saved!')
            return redirect('assessments:fluid_systems', assessment_id=assessment.id)
    else:
        form = StructuralAssessmentForm(instance=structural)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 10,
        'total_steps': 16
    }
    return render(request, 'assessments/structural_assessment.html', context)


@login_required
def fluid_systems_assessment(request, assessment_id):
    """Step 11: Fluid Systems Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        fluids = assessment.fluid_systems
    except FluidSystems.DoesNotExist:
        fluids = None
    
    if request.method == 'POST':
        form = FluidSystemsAssessmentForm(request.POST, instance=fluids)
        if form.is_valid():
            fluids = form.save(commit=False)
            fluids.assessment = assessment
            fluids.save()
            messages.success(request, 'Fluid systems assessment saved!')
            return redirect('assessments:documentation_assessment', assessment_id=assessment.id)
    else:
        form = FluidSystemsAssessmentForm(instance=fluids)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 11,
        'total_steps': 16
    }
    return render(request, 'assessments/fluid_systems.html', context)


@login_required
def documentation_assessment(request, assessment_id):
    """Step 12: Documentation Assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    try:
        documentation = assessment.documentation
    except DocumentationAndIdentification.DoesNotExist:
        documentation = None
    
    if request.method == 'POST':
        form = DocumentationAssessmentForm(request.POST, instance=documentation)
        if form.is_valid():
            documentation = form.save(commit=False)
            documentation.assessment = assessment
            documentation.save()
            messages.success(request, 'Documentation assessment saved!')
            return redirect('assessments:categorization', assessment_id=assessment.id)
    else:
        form = DocumentationAssessmentForm(instance=documentation)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 12,
        'total_steps': 16
    }
    return render(request, 'assessments/documentation_assessment.html', context)


@login_required
def assessment_categorization(request, assessment_id):
    """Step 13: Assessment Categorization"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = AssessmentCategorizationForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assessment categorization saved!')
            return redirect('assessments:financial_information', assessment_id=assessment.id)
    else:
        form = AssessmentCategorizationForm(instance=assessment)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 13,
        'total_steps': 16
    }
    return render(request, 'assessments/categorization.html', context)


@login_required
def financial_information(request, assessment_id):
    """Step 14: Financial Information"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = FinancialInformationForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Financial information saved!')
            return redirect('assessments:upload_photos', assessment_id=assessment.id)
    else:
        form = FinancialInformationForm(instance=assessment)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 14,
        'total_steps': 16
    }
    return render(request, 'assessments/financial_information.html', context)


@login_required
def assessment_photo_upload(request, assessment_id):
    """Step 15: Photo Upload Documentation"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = AssessmentPhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.assessment = assessment
            
            # Upload to Cloudinary
            if photo.image:
                import cloudinary.uploader
                try:
                    result = cloudinary.uploader.upload(
                        photo.image,
                        folder="assessment_photos",
                        public_id=f"{assessment.assessment_id}_{photo.category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        transformation=[
                            {'width': 1200, 'height': 800, 'crop': 'limit'},
                            {'quality': 'auto'}
                        ]
                    )
                    # Store the Cloudinary URL
                    photo.image = result['secure_url']
                    photo.save()
                    messages.success(request, 'Photo uploaded successfully!')
                except Exception as e:
                    messages.error(request, f'Error uploading photo: {str(e)}')
                    return redirect('assessments:upload_photos', assessment_id=assessment.id)
            
            # Check if user wants to continue to next step
            if 'continue_to_notes' in request.POST:
                return redirect('assessments:assessment_notes', assessment_id=assessment.id)
            else:
                return redirect('assessments:upload_photos', assessment_id=assessment.id)
    else:
        form = AssessmentPhotoUploadForm()
    
    # Get existing photos
    photos = assessment.photos.all().order_by('-taken_at')
    
    context = {
        'form': form,
        'assessment': assessment,
        'photos': photos,
        'step': 15,
        'total_steps': 16
    }
    return render(request, 'assessments/upload_photos.html', context)


@login_required
def assessment_notes(request, assessment_id):
    """Step 16: Assessment Notes and Completion"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = AssessmentNotesForm(request.POST, instance=assessment)
        if form.is_valid():
            assessment = form.save(commit=False)
            if 'complete_assessment' in request.POST:
                assessment.status = 'completed'
                assessment.completed_date = datetime.now()
                
                # Trigger parts identification for parts-based quote system
                if assessment.uses_parts_based_quotes and not assessment.parts_identification_complete:
                    try:
                        from insurance_app.parts_identification import PartsIdentificationEngine
                        engine = PartsIdentificationEngine()
                        damaged_parts = engine.identify_damaged_parts(assessment)
                        
                        if damaged_parts:
                            assessment.parts_identification_complete = True
                            assessment.quote_collection_status = 'not_started'
                            messages.success(request, f'Assessment {assessment.assessment_id} completed successfully! {len(damaged_parts)} damaged parts identified for quote collection.')
                        else:
                            messages.success(request, f'Assessment {assessment.assessment_id} completed successfully! No damaged parts requiring quotes were identified.')
                    except Exception as e:
                        messages.warning(request, f'Assessment {assessment.assessment_id} completed successfully! Parts identification will be processed separately. Error: {str(e)}')
                else:
                    messages.success(request, f'Assessment {assessment.assessment_id} completed successfully!')
                    
            assessment.save()
            return redirect('assessments:assessment_detail', assessment_id=assessment.id)
    else:
        form = AssessmentNotesForm(instance=assessment)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 16,
        'total_steps': 16
    }
    return render(request, 'assessments/assessment_notes.html', context)


@login_required
def assessment_detail(request, assessment_id):
    """View detailed assessment results"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    # Get all related assessment data
    try:
        exterior_damage = assessment.exterior_damage
    except ExteriorBodyDamage.DoesNotExist:
        exterior_damage = None
    
    try:
        wheels_tires = assessment.wheels_tires
    except WheelsAndTires.DoesNotExist:
        wheels_tires = None
    
    try:
        interior_damage = assessment.interior_damage
    except InteriorDamage.DoesNotExist:
        interior_damage = None
    
    # Get photos
    photos = assessment.photos.all().order_by('category', 'taken_at')
    
    # Get reports
    reports = assessment.reports.all().order_by('-id')
    
    # Parts-based quote system integration
    quote_progress = assessment.get_quote_collection_progress()
    damaged_parts = None
    quote_summary = None
    
    if assessment.uses_parts_based_quotes:
        # Get damaged parts if they exist
        try:
            from insurance_app.models import DamagedPart, AssessmentQuoteSummary
            damaged_parts = DamagedPart.objects.filter(assessment=assessment).order_by('part_category', 'part_name')
            
            # Get quote summary if it exists
            try:
                quote_summary = AssessmentQuoteSummary.objects.get(assessment=assessment)
            except AssessmentQuoteSummary.DoesNotExist:
                quote_summary = None
                
        except ImportError:
            pass
    
    # Get comprehensive cost information
    cost_info = assessment.get_cost_summary()
    
    # Add additional fields for template compatibility
    cost_info.update({
        'estimated_cost': assessment.estimated_repair_cost,
        'parts_based_total': cost_info.get('repair_cost') if assessment.uses_parts_based_quotes else None,
    })
    
    context = {
        'assessment': assessment,
        'exterior_damage': exterior_damage,
        'wheels_tires': wheels_tires,
        'interior_damage': interior_damage,
        'photos': photos,
        'reports': reports,
        'quote_progress': quote_progress,
        'damaged_parts': damaged_parts,
        'quote_summary': quote_summary,
        'cost_info': cost_info,
    }
    return render(request, 'assessments/assessment_detail.html', context)


@login_required
def upload_photos(request, assessment_id):
    """Upload photos for assessment"""
    import logging
    logger = logging.getLogger(__name__)
    
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    logger.info(f"Photo upload page accessed for assessment {assessment.assessment_id} by user {request.user.username}")
    
    if request.method == 'POST':
        logger.info(f"POST request received for photo upload. Files: {list(request.FILES.keys())}")
        logger.info(f"POST data: {dict(request.POST)}")
        
        form = AssessmentPhotoUploadForm(request.POST, request.FILES)
        logger.info(f"Form created with data. Form is valid: {form.is_valid()}")
        
        if form.is_valid():
            logger.info("Form validation passed")
            
            # Check if image was provided
            if 'image' in request.FILES and request.FILES['image']:
                logger.info(f"Image file found: {request.FILES['image'].name}, size: {request.FILES['image'].size} bytes")
                
                photo = form.save(commit=False)
                photo.assessment = assessment
                photo.save()
                
                logger.info(f"Photo saved successfully with ID: {photo.id}")
                messages.success(request, 'Photo uploaded successfully!')
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    logger.info("Returning AJAX success response")
                    return JsonResponse({
                        'success': True,
                        'message': 'Photo uploaded successfully!',
                        'photo_id': photo.id,
                        'photo_count': assessment.photos.count()
                    })
                
                return redirect('assessments:upload_photos', assessment_id=assessment.id)
            else:
                logger.warning("No image file provided in the upload")
                messages.warning(request, 'Please select an image file to upload.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'message': 'Please select an image file to upload.'
                    })
        else:
            logger.error(f"Form validation failed. Errors: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': 'Form validation failed.',
                    'errors': form.errors
                })
    else:
        logger.info("GET request - displaying upload form")
        form = AssessmentPhotoUploadForm()
    
    photos = assessment.photos.all().order_by('-taken_at')
    logger.info(f"Found {photos.count()} existing photos for assessment")
    
    context = {
        'form': form,
        'assessment': assessment,
        'photos': photos,
    }
    
    # Handle AJAX requests for refreshing photos section
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logger.info("Returning AJAX template response")
        return render(request, 'assessments/upload_photos.html', context)
    
    return render(request, 'assessments/upload_photos.html', context)


@login_required
def delete_photo(request, assessment_id):
    """Delete a photo from assessment"""
    import logging
    logger = logging.getLogger(__name__)
    
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    logger.info(f"Photo delete request for assessment {assessment.assessment_id} by user {request.user.username}")
    
    if request.method == 'POST':
        photo_id = request.POST.get('photo_id')
        logger.info(f"Attempting to delete photo ID: {photo_id}")
        
        if photo_id:
            try:
                photo = assessment.photos.get(id=photo_id)
                photo_name = photo.image.name if photo.image else 'No image'
                photo.delete()
                logger.info(f"Photo deleted successfully: {photo_name}")
                messages.success(request, 'Photo deleted successfully!')
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': True,
                        'message': 'Photo deleted successfully!',
                        'photo_count': assessment.photos.count()
                    })
                    
            except AssessmentPhoto.DoesNotExist:
                logger.error(f"Photo with ID {photo_id} not found for assessment {assessment.assessment_id}")
                messages.error(request, 'Photo not found.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'message': 'Photo not found.'
                    })
        else:
            logger.error("No photo ID provided in delete request")
            messages.error(request, 'Invalid photo ID.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid photo ID.'
                })
    
    return redirect('assessments:upload_photos', assessment_id=assessment.id)


@login_required
def generate_report(request, assessment_id):
    """Generate assessment report"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = AssessmentReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.assessment = assessment
            report.save()
            messages.success(request, 'Report generated successfully!')
            return redirect('assessments:assessment_detail', assessment_id=assessment.id)
    else:
        # Pre-populate form with assessment data
        initial_data = {
            'title': f'Assessment Report - {assessment.assessment_id}',
            'executive_summary': f'Assessment of {assessment.vehicle} conducted on {assessment.assessment_date.strftime("%B %d, %Y")}.',
        }
        form = AssessmentReportForm(initial=initial_data)
    
    context = {
        'form': form,
        'assessment': assessment,
    }
    return render(request, 'assessments/generate_report.html', context)


@login_required
def update_assessment_status(request, assessment_id):
    """Update assessment status"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(VehicleAssessment.STATUS_CHOICES):
            old_status = assessment.get_status_display()
            assessment.status = new_status
            assessment.save()
            
            # Create workflow step
            from .models import AssessmentWorkflow
            AssessmentWorkflow.objects.create(
                assessment=assessment,
                step='status_updated',
                notes=f'Status changed from {old_status} to {assessment.get_status_display()}',
                completed_by=request.user
            )
            
            messages.success(request, f'Assessment status updated to {assessment.get_status_display()}')
        else:
            messages.error(request, 'Invalid status selected')
    
    return redirect('assessments:continue_assessment', assessment_id=assessment.id)


@login_required
def quote_request_dispatch(request, assessment_id):
    """Quote request dispatch interface for parts-based quote system"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    # Import quote system models
    from insurance_app.models import DamagedPart, PartQuoteRequest
    from insurance_app.quote_managers import PartQuoteRequestManager
    
    # Get damaged parts for this assessment
    damaged_parts = DamagedPart.objects.filter(assessment=assessment).select_related('assessment').prefetch_related('damage_images', 'quote_requests')
    
    # Get existing quote requests
    quote_requests = PartQuoteRequest.objects.filter(assessment=assessment).select_related('damaged_part', 'dispatched_by').order_by('-request_date')
    
    # Provider performance data (mock data for now - would come from actual provider tracking)
    provider_performance = {
        'assessor': {'response_rate': 100, 'avg_response_time': 0, 'reliability_score': 95},
        'dealer': {'response_rate': 85, 'avg_response_time': 24, 'reliability_score': 90},
        'independent': {'response_rate': 78, 'avg_response_time': 48, 'reliability_score': 82},
        'network': {'response_rate': 92, 'avg_response_time': 12, 'reliability_score': 88},
    }
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'dispatch_quotes':
            # Handle batch quote request dispatch
            selected_parts = request.POST.getlist('selected_parts')
            provider_types = {
                'include_assessor': request.POST.get('include_assessor') == 'on',
                'include_dealer': request.POST.get('include_dealer') == 'on',
                'include_independent': request.POST.get('include_independent') == 'on',
                'include_network': request.POST.get('include_network') == 'on',
            }
            
            if not any(provider_types.values()):
                messages.error(request, 'Please select at least one provider type.')
                return redirect('assessments:quote_request_dispatch', assessment_id=assessment.id)
            
            if not selected_parts:
                messages.error(request, 'Please select at least one part for quote requests.')
                return redirect('assessments:quote_request_dispatch', assessment_id=assessment.id)
            
            try:
                # Create quote requests for selected parts
                quote_manager = PartQuoteRequestManager()
                created_requests = []
                
                for part_id in selected_parts:
                    try:
                        damaged_part = DamagedPart.objects.get(id=part_id, assessment=assessment)
                        
                        # Check if active request already exists
                        existing_request = PartQuoteRequest.objects.filter(
                            damaged_part=damaged_part,
                            status__in=['draft', 'pending', 'sent']
                        ).first()
                        
                        if existing_request:
                            messages.warning(request, f'Active quote request already exists for {damaged_part.part_name}')
                            continue
                        
                        # Create new quote request
                        quote_request = quote_manager.create_quote_request(
                            damaged_part=damaged_part,
                            dispatched_by=request.user,
                            **provider_types
                        )
                        created_requests.append(quote_request)
                        
                    except DamagedPart.DoesNotExist:
                        messages.error(request, f'Invalid part ID: {part_id}')
                        continue
                
                if created_requests:
                    messages.success(request, f'Successfully created {len(created_requests)} quote requests.')
                    
                    # Handle AJAX requests
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Successfully created {len(created_requests)} quote requests.',
                            'created_count': len(created_requests)
                        })
                else:
                    messages.warning(request, 'No new quote requests were created.')
                    
            except Exception as e:
                messages.error(request, f'Error creating quote requests: {str(e)}')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'Error creating quote requests: {str(e)}'
                    })
        
        elif action == 'cancel_request':
            # Handle individual request cancellation
            request_id = request.POST.get('request_id')
            try:
                quote_request = PartQuoteRequest.objects.get(
                    request_id=request_id,
                    assessment=assessment
                )
                quote_request.status = 'cancelled'
                quote_request.save()
                messages.success(request, f'Quote request {request_id} cancelled successfully.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Quote request {request_id} cancelled successfully.'
                    })
                    
            except PartQuoteRequest.DoesNotExist:
                messages.error(request, 'Quote request not found.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Quote request not found.'
                    })
        
        return redirect('assessments:quote_request_dispatch', assessment_id=assessment.id)
    
    # Get quote request statistics
    request_stats = {
        'total_requests': quote_requests.count(),
        'pending_requests': quote_requests.filter(status__in=['draft', 'pending', 'sent']).count(),
        'completed_requests': quote_requests.filter(status='received').count(),
        'expired_requests': quote_requests.filter(status='expired').count(),
    }
    
    context = {
        'assessment': assessment,
        'damaged_parts': damaged_parts,
        'quote_requests': quote_requests,
        'provider_performance': provider_performance,
        'request_stats': request_stats,
    }
    
    # Handle AJAX requests for status updates
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'assessments/quote_request_ajax.html', context)
    
    return render(request, 'assessments/quote_request.html', context)


@login_required
def quote_request_status_api(request, assessment_id):
    """API endpoint for real-time quote request status updates"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    # Import quote system models
    from insurance_app.models import PartQuoteRequest
    
    # Get quote requests with status updates
    quote_requests = PartQuoteRequest.objects.filter(
        assessment=assessment
    ).select_related('damaged_part', 'dispatched_by').order_by('-request_date')
    
    # Build response data
    requests_data = []
    for request in quote_requests:
        requests_data.append({
            'request_id': request.request_id,
            'part_name': request.damaged_part.part_name,
            'status': request.status,
            'status_display': request.get_status_display(),
            'request_date': request.request_date.isoformat(),
            'expiry_date': request.expiry_date.isoformat(),
            'is_expired': request.is_expired(),
            'providers': {
                'assessor': request.include_assessor,
                'dealer': request.include_dealer,
                'independent': request.include_independent,
                'network': request.include_network,
            }
        })
    
    # Get updated statistics
    request_stats = {
        'total_requests': quote_requests.count(),
        'pending_requests': quote_requests.filter(status__in=['draft', 'pending', 'sent']).count(),
        'completed_requests': quote_requests.filter(status='received').count(),
        'expired_requests': quote_requests.filter(status='expired').count(),
    }
    
    return JsonResponse({
        'success': True,
        'requests': requests_data,
        'stats': request_stats,
        'timestamp': timezone.now().isoformat()
    })


@login_required
def parts_review(request, assessment_id):
    """Parts review and editing interface for quote system"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    # Import DamagedPart model
    from insurance_app.models import DamagedPart
    
    # Get damaged parts for this assessment
    damaged_parts = DamagedPart.objects.filter(assessment=assessment).order_by(
        'section_type', 'part_category', 'part_name'
    )
    
    context = {
        'assessment': assessment,
        'damaged_parts': damaged_parts,
    }
    
    return render(request, 'assessments/parts_review.html', context)


@login_required
def parts_review_api(request, assessment_id):
    """API endpoints for parts review operations"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    from insurance_app.models import DamagedPart
    from insurance_app.parts_identification import PartsIdentificationEngine
    import json
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'identify_parts':
            # Re-identify parts from assessment
            try:
                engine = PartsIdentificationEngine()
                identified_parts = engine.identify_damaged_parts(assessment)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Identified {len(identified_parts)} damaged parts',
                    'parts_count': len(identified_parts)
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error identifying parts: {str(e)}'
                })
        
        elif action == 'update_part':
            # Update part details
            part_id = request.POST.get('part_id')
            field = request.POST.get('field')
            value = request.POST.get('value')
            
            try:
                part = DamagedPart.objects.get(id=part_id, assessment=assessment)
                
                # Validate and update field
                if field == 'part_name':
                    part.part_name = value
                elif field == 'part_category':
                    if value in dict(DamagedPart.PART_CATEGORIES):
                        part.part_category = value
                elif field == 'damage_severity':
                    if value in dict(DamagedPart.DAMAGE_SEVERITY):
                        part.damage_severity = value
                elif field == 'estimated_labor_hours':
                    part.estimated_labor_hours = float(value)
                elif field == 'damage_description':
                    part.damage_description = value
                
                part.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Part updated successfully'
                })
            except DamagedPart.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Part not found'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error updating part: {str(e)}'
                })
        
        elif action == 'add_part':
            # Add new part
            try:
                part = DamagedPart.objects.create(
                    assessment=assessment,
                    section_type=request.POST.get('section_type', 'exterior'),
                    part_name=request.POST.get('part_name'),
                    part_number=request.POST.get('part_number', ''),
                    part_category=request.POST.get('part_category'),
                    damage_severity=request.POST.get('damage_severity'),
                    damage_description=request.POST.get('damage_description', ''),
                    estimated_labor_hours=float(request.POST.get('estimated_labor_hours', 1.0)),
                    notes=request.POST.get('notes', '')
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Part added successfully',
                    'part_id': part.id
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error adding part: {str(e)}'
                })
        
        elif action == 'remove_part':
            # Remove part
            part_id = request.POST.get('part_id')
            try:
                part = DamagedPart.objects.get(id=part_id, assessment=assessment)
                part.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Part removed successfully'
                })
            except DamagedPart.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Part not found'
                })
        
        elif action == 'create_quote_requests':
            # Create quote requests for selected parts
            selected_parts = request.POST.getlist('selected_parts[]')
            providers = request.POST.getlist('providers[]')
            
            try:
                from insurance_app.quote_managers import PartQuoteRequestManager
                
                manager = PartQuoteRequestManager()
                requests_created = 0
                
                for part_id in selected_parts:
                    part = DamagedPart.objects.get(id=part_id, assessment=assessment)
                    quote_requests = manager.create_quote_requests(part, providers)
                    requests_created += len(quote_requests)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Created {requests_created} quote requests',
                    'requests_created': requests_created
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error creating quote requests: {str(e)}'
                })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def part_details_api(request, assessment_id, part_id):
    """API endpoint for part details modal"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    from insurance_app.models import DamagedPart
    
    try:
        part = DamagedPart.objects.get(id=part_id, assessment=assessment)
        
        # Get quotes for this part
        quotes_data = []
        for quote in part.quotes.filter(status='validated'):
            quotes_data.append({
                'provider_name': quote.provider_name,
                'provider_type': quote.get_provider_type_display(),
                'total_cost': str(quote.total_cost),
                'part_cost': str(quote.part_cost),
                'labor_cost': str(quote.labor_cost),
                'paint_cost': str(quote.paint_cost),
                'part_type': quote.get_part_type_display(),
                'estimated_completion_days': quote.estimated_completion_days,
                'part_warranty_months': quote.part_warranty_months,
                'labor_warranty_months': quote.labor_warranty_months,
            })
        
        part_data = {
            'part_name': part.part_name,
            'part_number': part.part_number,
            'part_category': part.get_part_category_display(),
            'damage_severity': part.get_damage_severity_display(),
            'damage_description': part.damage_description,
            'section_type': part.get_section_type_display(),
            'estimated_labor_hours': str(part.estimated_labor_hours),
            'requires_replacement': part.requires_replacement,
            'quotes': quotes_data
        }
        
        return JsonResponse(part_data)
        
    except DamagedPart.DoesNotExist:
        return JsonResponse({'error': 'Part not found'}, status=404)


@login_required
def quote_status_refresh_api(request, assessment_id):
    """API endpoint for refreshing quote status"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    from insurance_app.models import AssessmentQuoteSummary
    
    try:
        quote_summary = AssessmentQuoteSummary.objects.get(assessment=assessment)
        
        # Check if there have been updates since last request
        last_check = request.GET.get('last_check')
        updated = False
        
        if last_check:
            from datetime import datetime
            from django.utils import timezone
            import dateutil.parser
            
            try:
                last_check_time = dateutil.parser.parse(last_check)
                if quote_summary.last_updated > last_check_time:
                    updated = True
            except:
                updated = True
        else:
            updated = True
        
        return JsonResponse({
            'updated': updated,
            'last_updated': quote_summary.last_updated.isoformat(),
            'status': quote_summary.status,
            'completion_percentage': quote_summary.calculate_completion_percentage()
        })
        
    except AssessmentQuoteSummary.DoesNotExist:
        return JsonResponse({
            'updated': False,
            'error': 'Quote summary not found'
        })


@login_required
def continue_assessment(request, assessment_id):
    """Continue assessment from current step"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    # Calculate progress
    completed_steps = 0
    total_steps = 16
    
    # Check which steps are completed
    step_progress = {
        'vehicle_details': {
            'title': 'Vehicle Details',
            'description': 'Basic vehicle and assessment information',
            'completed': bool(assessment.vehicle and assessment.assessor_name),
            'current': False,
            'available': True,
            'url': '#'  # Already completed
        },
        'location': {
            'title': 'Location & Context',
            'description': 'Incident location and context details',
            'completed': bool(assessment.incident_location),
            'current': False,
            'available': True,
            'url': 'assessments:incident_location'
        },
        'exterior_damage': {
            'title': 'Exterior Damage',
            'description': 'Exterior body damage assessment',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:exterior_damage'
        },
        'wheels_tires': {
            'title': 'Wheels & Tires',
            'description': 'Wheels and tires condition',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:wheels_tires'
        },
        'interior_damage': {
            'title': 'Interior Damage',
            'description': 'Interior components assessment',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:interior_damage'
        },
        'mechanical': {
            'title': 'Mechanical Systems',
            'description': 'Engine and mechanical components',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:mechanical_systems'
        },
        'electrical': {
            'title': 'Electrical Systems',
            'description': 'Electrical and electronic systems',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:electrical_systems'
        },
        'safety': {
            'title': 'Safety Systems',
            'description': 'Safety and security systems',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:safety_systems'
        },
        'structural': {
            'title': 'Structural Assessment',
            'description': 'Frame and structural integrity',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:structural_assessment'
        },
        'fluids': {
            'title': 'Fluid Systems',
            'description': 'Fluid levels and conditions',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:fluid_systems'
        },
        'documentation': {
            'title': 'Documentation',
            'description': 'Vehicle documentation and records',
            'completed': False,
            'current': False,
            'available': True,
            'url': 'assessments:documentation_assessment'
        },
        'categorization': {
            'title': 'Categorization',
            'description': 'Overall assessment categorization',
            'completed': bool(assessment.overall_severity),
            'current': False,
            'available': True,
            'url': 'assessments:categorization'
        },
        'financial': {
            'title': 'Financial Information',
            'description': 'Cost estimates and valuations',
            'completed': bool(assessment.estimated_repair_cost or assessment.vehicle_market_value),
            'current': False,
            'available': True,
            'url': 'assessments:financial_information'
        },
        'photo_upload': {
            'title': 'Photo Documentation',
            'description': 'Upload assessment photos',
            'completed': bool(assessment.photos.exists()),
            'current': False,
            'available': True,
            'url': 'assessments:upload_photos'
        },
        'notes': {
            'title': 'Notes & Completion',
            'description': 'Final notes and assessment completion',
            'completed': bool(assessment.overall_notes and assessment.status == 'completed'),
            'current': False,
            'available': True,
            'url': 'assessments:assessment_notes'
        }
    }
    
    # Determine current step and update progress
    current_step = None
    for step_name, step_data in step_progress.items():
        if step_data['completed']:
            completed_steps += 1
        elif not current_step and not step_data['completed']:
            current_step = step_name
            step_data['current'] = True
            break
    
    # Update URLs with assessment ID
    url_mapping = {
        'incident_location': f"/assessments/{assessment_id}/location/",
        'exterior_damage': f"/assessments/{assessment_id}/exterior-damage/",
        'wheels_tires': f"/assessments/{assessment_id}/wheels-tires/",
        'interior_damage': f"/assessments/{assessment_id}/interior-damage/",
        'mechanical_systems': f"/assessments/{assessment_id}/mechanical/",
        'electrical_systems': f"/assessments/{assessment_id}/electrical/",
        'safety_systems': f"/assessments/{assessment_id}/safety/",
        'structural_assessment': f"/assessments/{assessment_id}/structural/",
        'fluid_systems': f"/assessments/{assessment_id}/fluids/",
        'documentation_assessment': f"/assessments/{assessment_id}/documentation/",
        'categorization': f"/assessments/{assessment_id}/categorization/",
        'financial_information': f"/assessments/{assessment_id}/financial/",
        'photo_upload': f"/assessments/{assessment_id}/upload-photos/",
        'assessment_notes': f"/assessments/{assessment_id}/notes/"
    }
    
    for step_name, step_data in step_progress.items():
        if step_data['url'] != '#':
            url_name = step_data['url'].split(':')[-1]
            step_data['url'] = url_mapping.get(url_name, '#')
    
    progress_percentage = int((completed_steps / total_steps) * 100)
    
    context = {
        'assessment': assessment,
        'step_progress': step_progress,
        'progress_percentage': progress_percentage,
        'completed_steps': completed_steps,
        'total_steps': total_steps,
        'current_step': current_step
    }
    
    return render(request, 'assessments/continue_assessment.html', context)


@login_required
def quote_summary(request, assessment_id):
    """Quote comparison and summary interface"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    # Import quote system models
    from insurance_app.models import (
        DamagedPart, PartQuote, PartMarketAverage, AssessmentQuoteSummary
    )
    from insurance_app.recommendation_engine import QuoteRecommendationEngine
    from insurance_app.market_analysis import MarketAverageCalculator
    
    # Get or create quote summary
    quote_summary, created = AssessmentQuoteSummary.objects.get_or_create(
        assessment=assessment,
        defaults={'status': 'collecting'}
    )
    
    # Update summary metrics
    quote_summary.update_summary_metrics()
    
    # Handle POST requests for quote selection
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'finalize_quotes':
            try:
                selection_strategy = request.POST.get('selection_strategy', 'recommended')
                priority_factor = request.POST.get('priority_factor', 'balanced')
                
                # Process quote selections based on strategy
                if selection_strategy == 'custom':
                    # Handle custom selections
                    selected_quotes = []
                    for key, value in request.POST.items():
                        if key.startswith('selected_quotes[') and key.endswith('][part_id]'):
                            index = key.split('[')[1].split(']')[0]
                            part_id = value
                            provider_type = request.POST.get(f'selected_quotes[{index}][provider_type]')
                            cost = request.POST.get(f'selected_quotes[{index}][cost]')
                            
                            if part_id and provider_type:
                                selected_quotes.append({
                                    'part_id': part_id,
                                    'provider_type': provider_type,
                                    'cost': float(cost) if cost else 0
                                })
                    
                    # Store custom selections
                    quote_summary.recommended_provider_mix = {
                        'strategy': 'custom',
                        'selections': selected_quotes
                    }
                else:
                    # Apply automatic selection strategy
                    engine = QuoteRecommendationEngine()
                    recommendation = engine.generate_recommendation(
                        assessment, 
                        strategy=selection_strategy,
                        priority_factor=priority_factor
                    )
                    
                    quote_summary.recommended_provider_mix = recommendation
                    quote_summary.recommended_total = recommendation.get('total_cost')
                    quote_summary.recommendation_reasoning = recommendation.get('reasoning', '')
                
                quote_summary.status = 'approved'
                quote_summary.completed_by = request.user
                quote_summary.save()
                
                # Update assessment status
                assessment.quote_collection_status = 'completed'
                assessment.save()
                
                messages.success(request, 'Quote selection finalized successfully!')
                
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('assessments:assessment_detail', args=[assessment.id])
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
    
    # Get damaged parts with quotes and market data
    damaged_parts = DamagedPart.objects.filter(assessment=assessment).prefetch_related(
        'quotes', 'market_average'
    ).order_by('section_type', 'part_category', 'part_name')
    
    # Build parts comparison data
    parts_comparison = []
    for part in damaged_parts:
        # Get quotes by provider type
        quotes_by_provider = {
            'assessor': part.quotes.filter(provider_type='assessor', status='validated').first(),
            'dealer': part.quotes.filter(provider_type='dealer', status='validated').first(),
            'independent': part.quotes.filter(provider_type='independent', status='validated').first(),
            'network': part.quotes.filter(provider_type='network', status='validated').first(),
        }
        
        # Get market average
        market_average = getattr(part, 'market_average', None)
        
        # Find best quote (lowest cost)
        valid_quotes = [q for q in quotes_by_provider.values() if q]
        best_quote = min(valid_quotes, key=lambda q: q.total_cost) if valid_quotes else None
        
        # Determine damage severity class for styling
        severity_classes = {
            'minor': 'info',
            'moderate': 'warning', 
            'severe': 'danger',
            'replace': 'primary'
        }
        
        # Build provider quote data
        provider_quotes = []
        for provider_type in ['assessor', 'dealer', 'independent', 'network']:
            quote = quotes_by_provider[provider_type]
            is_outlier = False
            
            if quote and market_average:
                # Check if quote is an outlier
                avg_cost = float(market_average.average_total_cost)
                std_dev = float(market_average.standard_deviation)
                quote_cost = float(quote.total_cost)
                
                if abs(quote_cost - avg_cost) > (2 * std_dev):
                    is_outlier = True
            
            provider_quotes.append({
                'provider_type': provider_type,
                'quote': quote,
                'is_outlier': is_outlier
            })
        
        parts_comparison.append({
            'part': part,
            'provider_quotes': provider_quotes,
            'market_average': market_average,
            'best_quote': best_quote,
            'damage_severity_class': severity_classes.get(part.damage_severity, 'secondary')
        })
    
    # Calculate provider variance from market average
    provider_variances = {}
    if quote_summary.market_average_total:
        market_avg = float(quote_summary.market_average_total)
        
        for provider in ['assessor', 'dealer', 'independent', 'network']:
            provider_total = getattr(quote_summary, f'{provider}_total')
            if provider_total:
                provider_cost = float(provider_total)
                variance = ((provider_cost - market_avg) / market_avg) * 100
                
                if variance > 0:
                    direction = 'above'
                    css_class = 'danger' if variance > 20 else 'warning'
                else:
                    direction = 'below'
                    css_class = 'success'
                
                provider_variances[f'{provider}_variance'] = {
                    'percentage': abs(variance),
                    'direction': direction,
                    'class': css_class
                }
    
    # Generate recommendation (simplified for assessment level)
    recommendation = None
    try:
        if damaged_parts.exists():
            # Get the first part with quotes as an example
            part_with_quotes = damaged_parts.filter(quotes__isnull=False).first()
            if part_with_quotes:
                engine = QuoteRecommendationEngine()
                part_recommendation = engine.generate_recommendation(part_with_quotes)
                
                # Create a simplified assessment-level recommendation
                recommendation = {
                    'strategy_display': 'Balanced Approach',
                    'reasoning': 'Recommended strategy balances cost, quality, and timeline factors.',
                    'total_cost': quote_summary.get_best_provider_total() or 0,
                    'savings_amount': quote_summary.potential_savings or 0,
                    'overall_score': 85,  # Simplified score
                    'alternatives': []
                }
    except Exception as e:
        print(f"Error generating recommendation: {e}")
    
    # Calculate completion percentage
    completion_percentage = quote_summary.calculate_completion_percentage()
    
    context = {
        'assessment': assessment,
        'quote_summary': quote_summary,
        'parts_comparison': parts_comparison,
        'completion_percentage': completion_percentage,
        'recommendation': recommendation,
        **provider_variances
    }
    
    return render(request, 'assessments/quote_summary.html', context)


@login_required
def trigger_parts_identification(request, assessment_id):
    """Manually trigger parts identification for an assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if not assessment.uses_parts_based_quotes:
        messages.error(request, 'This assessment uses hardcoded costs and does not support parts identification.')
        return redirect('assessments:assessment_detail', assessment_id=assessment.id)
    
    if assessment.parts_identification_complete:
        messages.info(request, 'Parts identification has already been completed for this assessment.')
        return redirect('assessments:assessment_detail', assessment_id=assessment.id)
    
    if request.method == 'POST':
        try:
            from insurance_app.parts_identification import PartsIdentificationEngine
            engine = PartsIdentificationEngine()
            damaged_parts = engine.identify_damaged_parts(assessment)
            
            if damaged_parts:
                assessment.parts_identification_complete = True
                assessment.quote_collection_status = 'not_started'
                assessment.save()
                
                messages.success(request, f'Parts identification completed! {len(damaged_parts)} damaged parts identified and ready for quote collection.')
            else:
                assessment.parts_identification_complete = True
                assessment.save()
                messages.info(request, 'Parts identification completed. No damaged parts requiring quotes were identified.')
                
        except Exception as e:
            messages.error(request, f'Error during parts identification: {str(e)}')
        
        return redirect('assessments:assessment_detail', assessment_id=assessment.id)
    
    context = {'assessment': assessment}
    return render(request, 'assessments/trigger_parts_identification.html', context)


@login_required
def delete_assessment(request, assessment_id):
    """Delete an assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        assessment_id_display = assessment.assessment_id
        assessment.delete()
        messages.success(request, f'Assessment {assessment_id_display} deleted successfully!')
        return redirect('assessments:dashboard')
    
    context = {'assessment': assessment}
    return render(request, 'assessments/delete_assessment.html', context)