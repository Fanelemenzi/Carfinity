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
    assessments = VehicleAssessment.objects.filter(user=request.user).order_by('-assessment_date')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        assessments = assessments.filter(status=status_filter)
    
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
    
    context = {
        'page_obj': page_obj,
        'status_counts': status_counts,
        'current_status': status_filter,
        'status_choices': VehicleAssessment.STATUS_CHOICES,
    }
    return render(request, 'assessments/dashboard.html', context)


@login_required
def start_assessment(request):
    """Start a new assessment - Step 1: Vehicle Details"""
    if request.method == 'POST':
        form = VehicleDetailsForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.user = request.user
            assessment.assessment_id = f"ASS-{uuid.uuid4().hex[:8].upper()}"
            assessment.status = 'in_progress'
            assessment.save()
            
            messages.success(request, f'Assessment {assessment.assessment_id} started successfully!')
            return redirect('assessments:incident_location', assessment_id=assessment.id)
    else:
        form = VehicleDetailsForm()
    
    return render(request, 'assessments/start_assessment.html', {'form': form})


@login_required
def incident_location(request, assessment_id):
    """Step 2: Incident Location and Context"""
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
        'step': 2,
        'total_steps': 14
    }
    return render(request, 'assessments/incident_location.html', context)


@login_required
def exterior_damage_assessment(request, assessment_id):
    """Step 3a: Exterior Damage Assessment"""
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
        'step': 3,
        'total_steps': 14
    }
    return render(request, 'assessments/exterior_damage.html', context)


@login_required
def wheels_tires_assessment(request, assessment_id):
    """Step 3b: Wheels and Tires Assessment"""
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
        'step': 4,
        'total_steps': 14
    }
    return render(request, 'assessments/wheels_tires.html', context)


@login_required
def interior_damage_assessment(request, assessment_id):
    """Step 3c: Interior Damage Assessment"""
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
        'step': 5,
        'total_steps': 14
    }
    return render(request, 'assessments/interior_damage.html', context)


@login_required
def mechanical_systems_assessment(request, assessment_id):
    """Step 3d: Mechanical Systems Assessment"""
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
        'step': 6,
        'total_steps': 14
    }
    return render(request, 'assessments/mechanical_systems.html', context)


@login_required
def electrical_systems_assessment(request, assessment_id):
    """Step 3e: Electrical Systems Assessment"""
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
        'step': 7,
        'total_steps': 14
    }
    return render(request, 'assessments/electrical_systems.html', context)


@login_required
def safety_systems_assessment(request, assessment_id):
    """Step 3f: Safety Systems Assessment"""
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
        'step': 8,
        'total_steps': 14
    }
    return render(request, 'assessments/safety_systems.html', context)


@login_required
def structural_assessment(request, assessment_id):
    """Step 3g: Structural Assessment"""
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
        'step': 9,
        'total_steps': 14
    }
    return render(request, 'assessments/structural_assessment.html', context)


@login_required
def fluid_systems_assessment(request, assessment_id):
    """Step 3h: Fluid Systems Assessment"""
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
        'step': 10,
        'total_steps': 14
    }
    return render(request, 'assessments/fluid_systems.html', context)


@login_required
def documentation_assessment(request, assessment_id):
    """Step 3i: Documentation Assessment"""
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
        'step': 11,
        'total_steps': 14
    }
    return render(request, 'assessments/documentation_assessment.html', context)


@login_required
def assessment_categorization(request, assessment_id):
    """Step 4: Assessment Categorization"""
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
        'step': 12,
        'total_steps': 14
    }
    return render(request, 'assessments/categorization.html', context)


@login_required
def financial_information(request, assessment_id):
    """Step 5: Financial Information"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = FinancialInformationForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Financial information saved!')
            return redirect('assessments:assessment_notes', assessment_id=assessment.id)
    else:
        form = FinancialInformationForm(instance=assessment)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 13,
        'total_steps': 14
    }
    return render(request, 'assessments/financial_information.html', context)


@login_required
def assessment_notes(request, assessment_id):
    """Step 6: Assessment Notes and Completion"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = AssessmentNotesForm(request.POST, instance=assessment)
        if form.is_valid():
            assessment = form.save(commit=False)
            if 'complete_assessment' in request.POST:
                assessment.status = 'completed'
                assessment.completed_date = datetime.now()
                messages.success(request, f'Assessment {assessment.assessment_id} completed successfully!')
            assessment.save()
            return redirect('assessments:assessment_detail', assessment_id=assessment.id)
    else:
        form = AssessmentNotesForm(instance=assessment)
    
    context = {
        'form': form,
        'assessment': assessment,
        'step': 14,
        'total_steps': 14
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
    
    context = {
        'assessment': assessment,
        'exterior_damage': exterior_damage,
        'wheels_tires': wheels_tires,
        'interior_damage': interior_damage,
        'photos': photos,
        'reports': reports,
    }
    return render(request, 'assessments/assessment_detail.html', context)


@login_required
def upload_photos(request, assessment_id):
    """Upload photos for assessment"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    if request.method == 'POST':
        form = AssessmentPhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.assessment = assessment
            photo.save()
            messages.success(request, 'Photo uploaded successfully!')
            return redirect('assessments:upload_photos', assessment_id=assessment.id)
    else:
        form = AssessmentPhotoUploadForm()
    
    photos = assessment.photos.all().order_by('-taken_at')
    
    context = {
        'form': form,
        'assessment': assessment,
        'photos': photos,
    }
    return render(request, 'assessments/upload_photos.html', context)


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
def continue_assessment(request, assessment_id):
    """Continue assessment from current step"""
    assessment = get_object_or_404(VehicleAssessment, id=assessment_id, user=request.user)
    
    # Calculate progress
    completed_steps = 0
    total_steps = 14
    
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
    for step_name, step_data in step_progress.items():
        if step_data['url'] != '#':
            step_data['url'] = f"/assessments/{assessment_id}/{step_data['url'].split(':')[-1]}/"
    
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
