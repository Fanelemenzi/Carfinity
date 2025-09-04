from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import logging
import json
from django.utils import timezone
from .models import MaintenanceRecord, PartUsage, Inspection, Inspections, InitialInspection
from .forms import MaintenanceRecordForm, InspectionForm, InspectionRecordForm, InitialInspectionForm
from maintenance.models import Part

# Set up logging
logger = logging.getLogger(__name__)

class TechnicianDashboardView(LoginRequiredMixin, ListView):
    model = MaintenanceRecord
    template_name = 'maintenance/technician_dashboard.html'
    context_object_name = 'records'
    
    def get_queryset(self):
        return MaintenanceRecord.objects.filter(
            technician=self.request.user
        ).order_by('-date_performed')[:10]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get inspection statistics
        user_inspections = Inspections.objects.filter(technician=self.request.user)
        context['total_inspections'] = user_inspections.count()
        context['pending_inspections'] = user_inspections.filter(is_completed=False).count()
        context['completed_today'] = user_inspections.filter(
            inspection_date__date=timezone.now().date(),
            is_completed=True
        ).count()
        context['maintenance_records'] = MaintenanceRecord.objects.filter(
            technician=self.request.user
        ).count()
        
        # Get initial inspection statistics
        user_initial_inspections = InitialInspection.objects.filter(technician=self.request.user)
        context['total_initial_inspections'] = user_initial_inspections.count()
        context['pending_initial_inspections'] = user_initial_inspections.filter(is_completed=False).count()
        context['completed_initial_today'] = user_initial_inspections.filter(
            inspection_date__date=timezone.now().date(),
            is_completed=True
        ).count()
        
        return context

class CreateMaintenanceRecordView(LoginRequiredMixin, CreateView):
    model = MaintenanceRecord
    form_class = MaintenanceRecordForm
    template_name = 'maintenance/create_record.html'
    success_url = '/technician-dashboard/'
    
    def form_valid(self, form):
        """Handle successful form submission with part data processing"""
        try:
            with transaction.atomic():
                # Set the technician
                form.instance.technician = self.request.user
                
                # Save the maintenance record and parts
                maintenance_record = form.save()
                
                # Get parts summary for success message
                parts_summary = form.get_selected_parts_summary()
                
                # Log successful creation
                logger.info(
                    f"Maintenance record created successfully. "
                    f"Record ID: {maintenance_record.id}, "
                    f"Technician: {self.request.user.username}, "
                    f"Vehicle: {maintenance_record.vehicle.vin}, "
                    f"Parts used: {len(parts_summary.get('parts', []))}, "
                    f"Total parts cost: ${parts_summary.get('total_cost', 0):.2f}, "
                    f"Image uploaded: {bool(maintenance_record.service_image)}"
                )
                
                # Create success message with part usage summary
                self._create_success_message(maintenance_record, parts_summary)
                
                return super().form_valid(form)
                
        except ValidationError as e:
            # Handle part selection conflicts and validation errors
            logger.warning(
                f"Validation error during maintenance record creation. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}"
            )
            
            # Add error messages to form
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
            else:
                form.add_error(None, str(e))
                
            return self.form_invalid(form)
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f"Unexpected error during maintenance record creation. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}", 
                exc_info=True
            )
            
            messages.error(
                self.request,
                "An unexpected error occurred while creating the maintenance record. "
                "Please try again or contact support if the problem persists."
            )
            
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        # Log form validation errors
        logger.warning(
            f"Form validation failed for maintenance record creation. "
            f"User: {self.request.user.username}, "
            f"Errors: {form.errors}"
        )
        
        # Add general error message
        messages.error(
            self.request,
            "Please correct the errors below and try again."
        )
        
        return super().form_invalid(form)
    
    def _create_success_message(self, maintenance_record, parts_summary):
        """Create detailed success message with part usage summary"""
        base_message = f"Maintenance record created successfully for {maintenance_record.vehicle.vin}."
        
        # Add image information if uploaded
        image_message = ""
        if maintenance_record.service_image:
            image_message = f" Service image uploaded ({maintenance_record.image_type_display})."
        
        parts_used = parts_summary.get('parts', [])
        if parts_used:
            parts_details = []
            for part in parts_used:
                parts_details.append(
                    f"{part['name']} (x{part['quantity']}) - ${part['line_total']:.2f}"
                )
            
            parts_message = (
                f" Parts used: {', '.join(parts_details)}. "
                f"Total parts cost: ${parts_summary.get('total_cost', 0):.2f}."
            )
            
            messages.success(self.request, base_message + image_message + parts_message)
        else:
            messages.success(self.request, base_message + image_message)
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template"""
        context = super().get_context_data(**kwargs)
        
        # Add any additional context needed for part selection
        context['available_parts'] = Part.objects.filter(stock_quantity__gt=0).order_by('name')
        
        return context
# Inspection Views
class InspectionListView(LoginRequiredMixin, ListView):
    model = Inspection
    template_name = 'maintenance/inspection_list.html'
    context_object_name = 'inspections'
    paginate_by = 20
    
    def get_queryset(self):
        return Inspection.objects.select_related('vehicle').order_by('-inspection_date')

class InspectionDetailView(LoginRequiredMixin, DetailView):
    model = Inspection
    template_name = 'maintenance/inspection_detail.html'
    context_object_name = 'inspection'

@method_decorator(login_required, name='dispatch')
class InspectionPDFViewerView(View):
    """View for displaying PDF in browser"""
    
    def get(self, request, pk):
        inspection = get_object_or_404(Inspection, pk=pk)
        
        if not inspection.inspection_pdf:
            raise Http404("No PDF file found for this inspection")
        
        try:
            # For Cloudinary, we can redirect to the PDF URL
            return HttpResponse(
                f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Inspection Report - {inspection.inspection_number}</title>
                    <style>
                        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
                        .header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #dee2e6; }}
                        .header h1 {{ margin: 0; color: #495057; }}
                        .pdf-container {{ width: 100%; height: calc(100vh - 80px); }}
                        .pdf-embed {{ width: 100%; height: 100%; border: none; }}
                        .error {{ padding: 20px; text-align: center; color: #dc3545; }}
                        .download-btn {{ 
                            display: inline-block; 
                            padding: 8px 16px; 
                            background: #007bff; 
                            color: white; 
                            text-decoration: none; 
                            border-radius: 4px; 
                            margin-left: 15px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Inspection Report: {inspection.inspection_number}</h1>
                        <span>Vehicle: {inspection.vehicle.vin} | Date: {inspection.inspection_date}</span>
                        <a href="{inspection.inspection_pdf.url}" class="download-btn" download>Download PDF</a>
                    </div>
                    <div class="pdf-container">
                        <embed src="{inspection.inspection_pdf.url}" type="application/pdf" class="pdf-embed">
                        <div class="error">
                            <p>Your browser doesn't support PDF viewing.</p>
                            <p><a href="{inspection.inspection_pdf.url}" download>Click here to download the PDF</a></p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                content_type='text/html'
            )
        except Exception as e:
            logger.error(f"Error displaying PDF for inspection {pk}: {str(e)}")
            raise Http404("Error loading PDF file")

@method_decorator(login_required, name='dispatch')
class InspectionPDFDownloadView(View):
    """View for downloading PDF files"""
    
    def get(self, request, pk):
        inspection = get_object_or_404(Inspection, pk=pk)
        
        if not inspection.inspection_pdf:
            raise Http404("No PDF file found for this inspection")
        
        try:
            # For Cloudinary, redirect to the file URL with download headers
            response = HttpResponse()
            response['X-Accel-Redirect'] = inspection.inspection_pdf.url
            response['Content-Type'] = 'application/pdf'
            response['Content-Disposition'] = f'attachment; filename="inspection_{inspection.inspection_number}.pdf"'
            return response
            
        except Exception as e:
            logger.error(f"Error downloading PDF for inspection {pk}: {str(e)}")
            raise Http404("Error downloading PDF file")


# Inspection Form Views
class InspectionFormListView(LoginRequiredMixin, ListView):
    model = Inspections
    template_name = 'maintenance/inspection_form_list.html'
    context_object_name = 'inspection_forms'
    paginate_by = 20
    
    def get_queryset(self):
        return Inspections.objects.select_related('inspection__vehicle', 'technician').order_by('-inspection_date')

class InspectionFormDetailView(LoginRequiredMixin, DetailView):
    model = Inspections
    template_name = 'maintenance/inspection_form_detail.html'
    context_object_name = 'inspection_form'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add inspection points organized by category
        inspection_form = self.object
        
        context['inspection_categories'] = {
            'Engine & Powertrain': [
                ('engine_oil_level', 'Engine oil level & quality'),
                ('oil_filter_condition', 'Oil filter condition'),
                ('coolant_level', 'Coolant level & leaks'),
                ('drive_belts', 'Drive belts for cracks/wear'),
                ('hoses_condition', 'Hoses for leaks or soft spots'),
                ('air_filter', 'Air filter condition'),
                ('cabin_air_filter', 'Cabin air filter condition'),
                ('transmission_fluid', 'Transmission fluid level & leaks'),
                ('engine_mounts', 'Engine/transmission mounts'),
                ('fluid_leaks', 'Fluid leaks under engine & gearbox'),
            ],
            'Electrical & Battery': [
                ('battery_voltage', 'Battery voltage & charging system'),
                ('battery_terminals', 'Battery terminals for corrosion'),
                ('alternator_output', 'Alternator output'),
                ('starter_motor', 'Starter motor performance'),
                ('fuses_relays', 'All fuses and relays'),
            ],
            'Brakes & Suspension': [
                ('brake_pads', 'Brake pads/shoes thickness'),
                ('brake_discs', 'Brake discs/drums damage/warping'),
                ('brake_fluid', 'Brake fluid level & condition'),
                ('parking_brake', 'Parking brake function'),
                ('shocks_struts', 'Shocks/struts for leaks'),
                ('suspension_bushings', 'Suspension bushings & joints'),
                ('wheel_bearings', 'Wheel bearings for noise/play'),
            ],
            'Steering & Tires': [
                ('steering_response', 'Steering response & play'),
                ('steering_fluid', 'Steering fluid level & leaks'),
                ('tire_tread_depth', 'Tire tread depth (>5/32")'),
                ('tire_pressure', 'Tire pressure (all tires + spare)'),
                ('tire_wear_patterns', 'Tire wear patterns'),
                ('wheels_rims', 'Wheels & rims for damage'),
            ],
            'Exhaust & Emissions': [
                ('exhaust_system', 'Exhaust for leaks/damage'),
                ('catalytic_converter', 'Catalytic converter/muffler condition'),
                ('exhaust_warning_lights', 'No exhaust warning lights'),
            ],
            'Safety Equipment': [
                ('seat_belts', 'Seat belts operation & condition'),
                ('airbags', 'Airbags (warning light off)'),
                ('horn_function', 'Horn function'),
                ('first_aid_kit', 'First-aid kit contents'),
                ('warning_triangle', 'Warning triangle/reflective vest present'),
            ],
            'Lighting & Visibility': [
                ('headlights', 'Headlights (low/high beam)'),
                ('brake_lights', 'Brake/reverse/fog lights'),
                ('turn_signals', 'Turn signals & hazard lights'),
                ('interior_lights', 'Interior dome/courtesy lights'),
                ('windshield', 'Windshield for cracks/chips'),
                ('wiper_blades', 'Wiper blades & washer spray'),
                ('rear_defogger', 'Rear defogger/heater operation'),
                ('mirrors', 'Mirrors adjustment & condition'),
            ],
            'HVAC & Interior': [
                ('air_conditioning', 'Air conditioning & heating performance'),
                ('ventilation', 'Ventilation airflow'),
                ('seat_adjustments', 'Seat adjustments & seat heaters'),
                ('power_windows', 'Power windows & locks'),
            ],
            'Technology & Driver Assist': [
                ('infotainment_system', 'Infotainment system & Bluetooth/USB'),
                ('rear_view_camera', 'Rear-view camera/parking sensors'),
            ],
        }
        
        return context

class CreateInspectionFormView(LoginRequiredMixin, CreateView):
    model = Inspections
    form_class = InspectionForm
    template_name = 'maintenance/create_inspection_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass inspection_id from URL parameter to form
        inspection_id = self.kwargs.get('inspection_id') or self.request.GET.get('inspection_id')
        if inspection_id:
            kwargs['inspection_id'] = inspection_id
        return kwargs
    
    def get_success_url(self):
        """Redirect to the inspection form detail page after creation"""
        return f'/inspection-forms/{self.object.pk}/'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            with transaction.atomic():
                # Set the technician if not already set
                if not form.instance.technician:
                    form.instance.technician = self.request.user
                
                # Save the inspection form
                inspection_form = form.save()
                
                # Log successful creation
                logger.info(
                    f"Inspection form created successfully. "
                    f"Form ID: {inspection_form.id}, "
                    f"Technician: {self.request.user.username}, "
                    f"Inspection: {inspection_form.inspection.inspection_number}, "
                    f"Mileage: {inspection_form.mileage_at_inspection}, "
                    f"Completion: {inspection_form.completion_percentage}%"
                )
                
                # Create success message with health index info if completed
                success_message = f"Inspection form created successfully for {inspection_form.inspection.inspection_number}. Progress: {inspection_form.completion_percentage}% complete."
                
                if inspection_form.is_completed:
                    # Trigger health index calculation and update inspection record
                    inspection_form._update_inspection_record()
                    # Refresh to get updated values
                    inspection_form.inspection.refresh_from_db()
                    success_message += f" Vehicle Health Index: {inspection_form.inspection.vehicle_health_index}."
                
                messages.success(self.request, success_message)
                
                return super().form_valid(form)
                
        except ValidationError as e:
            logger.warning(
                f"Validation error during inspection form creation. "
                f"User: {self.request.user.username}, "
                f"POST data: {dict(self.request.POST)}, "
                f"Error: {str(e)}"
            )
            
            form.add_error(None, str(e))
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(
                f"Unexpected error during inspection form creation. "
                f"User: {self.request.user.username}, "
                f"POST data: {dict(self.request.POST)}, "
                f"Error: {str(e)}", 
                exc_info=True
            )
            
            messages.error(
                self.request,
                "An unexpected error occurred while creating the inspection form. "
                "Please try again or contact support if the problem persists."
            )
            
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors with detailed logging"""
        logger.warning(
            f"Inspection form validation failed. "
            f"User: {self.request.user.username}, "
            f"POST data: {dict(self.request.POST)}, "
            f"Form errors: {form.errors}, "
            f"Non-field errors: {form.non_field_errors()}"
        )
        
        # Add a general error message for the user
        messages.error(
            self.request,
            "Please correct the errors below and try again. Make sure all required fields are filled."
        )
        
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if this is part of the new workflow
        inspection_id = self.kwargs.get('inspection_id') or self.request.GET.get('inspection_id')
        if inspection_id:
            try:
                context['workflow_inspection'] = Inspection.objects.get(id=inspection_id)
                context['is_workflow'] = True
            except Inspection.DoesNotExist:
                pass
        
        # Add available inspections that don't have forms yet
        context['available_inspections'] = Inspection.objects.filter(
            inspections_form__isnull=True
        ).select_related('vehicle').order_by('-inspection_date')
        
        return context

class UpdateInspectionFormView(LoginRequiredMixin, DetailView):
    model = Inspections
    form_class = InspectionForm
    template_name = 'maintenance/update_inspection_form.html'
    context_object_name = 'inspection_form'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = InspectionForm(instance=self.object)
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = InspectionForm(request.POST, instance=self.object)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    inspection_form = form.save()
                    
                    logger.info(
                        f"Inspection form updated successfully. "
                        f"Form ID: {inspection_form.id}, "
                        f"Technician: {request.user.username}, "
                        f"Completion: {inspection_form.completion_percentage}%"
                    )
                    
                    # Prepare response data
                    response_data = {
                        'success': True,
                        'completion_percentage': inspection_form.completion_percentage,
                        'is_completed': inspection_form.is_completed,
                        'message': f'Form updated successfully. Progress: {inspection_form.completion_percentage}% complete.'
                    }
                    
                    # Add health index info if completed
                    if inspection_form.is_completed:
                        health_index, inspection_result = inspection_form.get_health_index_calculation()
                        response_data['health_index'] = health_index
                        response_data['inspection_result'] = dict(Inspection.RESULT_CHOICES)[inspection_result]
                        response_data['message'] += f' Vehicle Health Index: {health_index}.'
                    
                    messages.success(request, response_data['message'])
                    
                    return JsonResponse(response_data)
                    
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'errors': str(e)
                })
                
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

class StartInspectionWorkflowView(LoginRequiredMixin, CreateView):
    """Landing page and first step of inspection workflow"""
    model = Inspection
    form_class = InspectionRecordForm
    template_name = 'maintenance/start_inspection_workflow.html'
    
    def form_valid(self, form):
        """Create inspection record and redirect to 50-point form"""
        try:
            with transaction.atomic():
                # Save the inspection record
                inspection = form.save()
                
                logger.info(
                    f"Inspection workflow started. "
                    f"Inspection ID: {inspection.id}, "
                    f"Number: {inspection.inspection_number}, "
                    f"Vehicle: {inspection.vehicle.vin}, "
                    f"User: {self.request.user.username}"
                )
                
                messages.success(
                    self.request,
                    f"Inspection record created successfully for {inspection.inspection_number}. "
                    f"Now complete the detailed 50-point inspection checklist."
                )
                
                # Redirect to create inspection form with the inspection ID
                return redirect('maintenance_history:create_inspection_form', inspection_id=inspection.id)
                
        except Exception as e:
            logger.error(
                f"Error starting inspection workflow. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}", 
                exc_info=True
            )
            
            messages.error(
                self.request,
                "An error occurred while starting the inspection. Please try again."
            )
            
            return self.form_invalid(form)

class CreateInspectionRecordView(LoginRequiredMixin, CreateView):
    model = Inspection
    form_class = InspectionRecordForm
    template_name = 'maintenance/create_inspection_record.html'
    success_url = '/inspections/'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f"Inspection record created successfully for {form.instance.inspection_number}."
        )
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class InspectionFormAjaxView(View):
    """AJAX view for loading inspection form details in modal"""
    
    def get(self, request, pk):
        try:
            inspection = get_object_or_404(Inspection, pk=pk)
            
            # Check if inspection has a form
            if not hasattr(inspection, 'inspections_form'):
                return JsonResponse({
                    'success': False,
                    'error': 'No detailed inspection form available for this inspection.'
                })
            
            inspection_form = inspection.inspections_form
            
            # Prepare inspection categories data
            inspection_categories = {
                'Engine & Powertrain': [
                    ('engine_oil_level', 'Engine oil level & quality'),
                    ('oil_filter_condition', 'Oil filter condition'),
                    ('coolant_level', 'Coolant level & leaks'),
                    ('drive_belts', 'Drive belts for cracks/wear'),
                    ('hoses_condition', 'Hoses for leaks or soft spots'),
                    ('air_filter', 'Air filter condition'),
                    ('cabin_air_filter', 'Cabin air filter condition'),
                    ('transmission_fluid', 'Transmission fluid level & leaks'),
                    ('engine_mounts', 'Engine/transmission mounts'),
                    ('fluid_leaks', 'Fluid leaks under engine & gearbox'),
                ],
                'Electrical & Battery': [
                    ('battery_voltage', 'Battery voltage & charging system'),
                    ('battery_terminals', 'Battery terminals for corrosion'),
                    ('alternator_output', 'Alternator output'),
                    ('starter_motor', 'Starter motor performance'),
                    ('fuses_relays', 'All fuses and relays'),
                ],
                'Brakes & Suspension': [
                    ('brake_pads', 'Brake pads/shoes thickness'),
                    ('brake_discs', 'Brake discs/drums damage/warping'),
                    ('brake_fluid', 'Brake fluid level & condition'),
                    ('parking_brake', 'Parking brake function'),
                    ('shocks_struts', 'Shocks/struts for leaks'),
                    ('suspension_bushings', 'Suspension bushings & joints'),
                    ('wheel_bearings', 'Wheel bearings for noise/play'),
                ],
                'Steering & Tires': [
                    ('steering_response', 'Steering response & play'),
                    ('steering_fluid', 'Steering fluid level & leaks'),
                    ('tire_tread_depth', 'Tire tread depth (>5/32")'),
                    ('tire_pressure', 'Tire pressure (all tires + spare)'),
                    ('tire_wear_patterns', 'Tire wear patterns'),
                    ('wheels_rims', 'Wheels & rims for damage'),
                ],
                'Exhaust & Emissions': [
                    ('exhaust_system', 'Exhaust for leaks/damage'),
                    ('catalytic_converter', 'Catalytic converter/muffler condition'),
                    ('exhaust_warning_lights', 'No exhaust warning lights'),
                ],
                'Safety Equipment': [
                    ('seat_belts', 'Seat belts operation & condition'),
                    ('airbags', 'Airbags (warning light off)'),
                    ('horn_function', 'Horn function'),
                    ('first_aid_kit', 'First-aid kit contents'),
                    ('warning_triangle', 'Warning triangle/reflective vest present'),
                ],
                'Lighting & Visibility': [
                    ('headlights', 'Headlights (low/high beam)'),
                    ('brake_lights', 'Brake/reverse/fog lights'),
                    ('turn_signals', 'Turn signals & hazard lights'),
                    ('interior_lights', 'Interior dome/courtesy lights'),
                    ('windshield', 'Windshield for cracks/chips'),
                    ('wiper_blades', 'Wiper blades & washer spray'),
                    ('rear_defogger', 'Rear defogger/heater operation'),
                    ('mirrors', 'Mirrors adjustment & condition'),
                ],
                'HVAC & Interior': [
                    ('air_conditioning', 'Air conditioning & heating performance'),
                    ('ventilation', 'Ventilation airflow'),
                    ('seat_adjustments', 'Seat adjustments & seat heaters'),
                    ('power_windows', 'Power windows & locks'),
                ],
                'Technology & Driver Assist': [
                    ('infotainment_system', 'Infotainment system & Bluetooth/USB'),
                    ('rear_view_camera', 'Rear-view camera/parking sensors'),
                ],
            }
            
            # Generate HTML content
            html_content = self._generate_inspection_form_html(inspection_form, inspection_categories)
            
            return JsonResponse({
                'success': True,
                'html': html_content
            })
            
        except Exception as e:
            logger.error(f"Error loading inspection form details for inspection {pk}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while loading the inspection details.'
            })
    
    def _generate_inspection_form_html(self, inspection_form, inspection_categories):
        """Generate HTML content for the inspection form modal"""
        
        # Status choices mapping
        status_choices = {
            'pass': ('Pass', 'text-green-600', 'fas fa-check-circle'),
            'fail': ('Fail', 'text-red-600', 'fas fa-times-circle'),
            'na': ('Not Applicable', 'text-gray-500', 'fas fa-minus-circle'),
            'minor': ('Minor Issue', 'text-yellow-600', 'fas fa-exclamation-triangle'),
            'major': ('Major Issue', 'text-red-600', 'fas fa-exclamation-triangle'),
        }
        
        html = f"""
        <div class="space-y-6">
          <!-- Form Overview -->
          <div class="bg-gray-50 rounded-lg p-4 border">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="text-center">
                <div class="text-2xl font-bold text-green-600">{inspection_form.completion_percentage}%</div>
                <div class="text-sm text-gray-600">Completion</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">{inspection_form.total_points_checked}/50</div>
                <div class="text-sm text-gray-600">Points Checked</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold {'text-green-600' if inspection_form.is_completed else 'text-yellow-600'}">
                  {'✓' if inspection_form.is_completed else '⏳'}
                </div>
                <div class="text-sm text-gray-600">{'Completed' if inspection_form.is_completed else 'In Progress'}</div>
              </div>
            </div>
            
            <div class="mt-4 pt-4 border-t border-gray-200">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-500">Inspection Date:</span>
                  <span class="font-medium ml-2">{inspection_form.inspection_date.strftime('%B %d, %Y at %I:%M %p')}</span>
                </div>
                <div>
                  <span class="text-gray-500">Vehicle Mileage:</span>
                  <span class="font-medium ml-2">{inspection_form.mileage_at_inspection:,} miles</span>
                </div>
                {'<div><span class="text-gray-500">Technician:</span><span class="font-medium ml-2">' + self._get_technician_display_name(inspection_form.technician) + '</span></div>' if inspection_form.technician else ''}
                {'<div><span class="text-gray-500">Completed:</span><span class="font-medium ml-2">' + inspection_form.completed_at.strftime('%B %d, %Y at %I:%M %p') + '</span></div>' if inspection_form.completed_at else ''}
              </div>
            </div>
          </div>
        """
        
        # Add inspection categories
        for category_name, fields in inspection_categories.items():
            html += f"""
            <div class="bg-white border border-gray-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <i class="fas fa-cogs text-blue-600 mr-2"></i>
                {category_name}
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            """
            
            for field_name, field_description in fields:
                field_value = getattr(inspection_form, field_name, '')
                if field_value and field_value in status_choices:
                    status_text, status_color, status_icon = status_choices[field_value]
                    html += f"""
                    <div class="flex items-center justify-between p-2 bg-gray-50 rounded border">
                      <span class="text-sm text-gray-700">{field_description}</span>
                      <span class="{status_color} flex items-center text-sm font-medium">
                        <i class="{status_icon} mr-1"></i>
                        {status_text}
                      </span>
                    </div>
                    """
                else:
                    html += f"""
                    <div class="flex items-center justify-between p-2 bg-gray-50 rounded border">
                      <span class="text-sm text-gray-700">{field_description}</span>
                      <span class="text-gray-400 text-sm">Not Checked</span>
                    </div>
                    """
            
            html += "</div>"
            
            # Add category notes if available
            notes_field = f"{category_name.lower().replace(' & ', '_').replace(' ', '_')}_notes"
            notes_value = getattr(inspection_form, notes_field, '')
            if notes_value:
                html += f"""
                <div class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <h5 class="font-medium text-gray-700 mb-1">Notes:</h5>
                  <p class="text-sm text-gray-600">{notes_value}</p>
                </div>
                """
            
            html += "</div>"
        
        # Add overall notes and recommendations
        if inspection_form.overall_notes or inspection_form.recommendations:
            html += """
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <i class="fas fa-sticky-note text-blue-600 mr-2"></i>
                Summary & Recommendations
              </h4>
            """
            
            if inspection_form.overall_notes:
                html += f"""
                <div class="mb-4">
                  <h5 class="font-medium text-gray-700 mb-2">Overall Notes:</h5>
                  <p class="text-sm text-gray-600 bg-white p-3 rounded border">{inspection_form.overall_notes}</p>
                </div>
                """
            
            if inspection_form.recommendations:
                html += f"""
                <div>
                  <h5 class="font-medium text-gray-700 mb-2">Recommendations:</h5>
                  <p class="text-sm text-gray-600 bg-white p-3 rounded border">{inspection_form.recommendations}</p>
                </div>
                """
            
            html += "</div>"
        
        # Add failed points summary if any
        failed_points = inspection_form.failed_points
        if failed_points:
            html += f"""
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-red-800 mb-4 flex items-center">
                <i class="fas fa-exclamation-triangle text-red-600 mr-2"></i>
                Issues Found ({len(failed_points)} items)
              </h4>
              <div class="space-y-2">
            """
            
            for issue in failed_points:
                html += f"""
                <div class="flex items-center p-2 bg-white rounded border border-red-200">
                  <i class="fas fa-times-circle text-red-500 mr-2"></i>
                  <span class="text-sm text-gray-700">{issue}</span>
                </div>
                """
            
            html += "</div></div>"
        
        html += "</div>"
        
        return html

    def _get_technician_display_name(self, technician):
        """Get a proper display name for the technician"""
        if not technician:
            return "Unknown"
        
        first_name = (technician.first_name or "").strip()
        last_name = (technician.last_name or "").strip()
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return technician.username or f"User {technician.id}"


class StartInspectionWorkflowView(LoginRequiredMixin, CreateView):
    """
    New workflow: Create basic inspection record and redirect to form
    """
    model = Inspection
    template_name = 'maintenance/start_inspection_workflow.html'
    fields = ['vehicle', 'year', 'inspection_date']
    
    def get_success_url(self):
        # Redirect to create the inspection form
        return f'/inspection-forms/create/?inspection_id={self.object.id}'
    
    def form_valid(self, form):
        """Create basic inspection record with default values"""
        try:
            with transaction.atomic():
                # Generate unique inspection number
                from .utils import generate_inspection_number
                form.instance.inspection_number = generate_inspection_number()
                
                # Set default values for required fields
                form.instance.inspection_result = 'FAI'  # Default to Failed, will be updated by form
                form.instance.vehicle_health_index = 'Pending Assessment'
                
                # Save the inspection record
                inspection = form.save()
                
                # Log successful creation
                logger.info(
                    f"Inspection workflow started. "
                    f"Inspection ID: {inspection.id}, "
                    f"Number: {inspection.inspection_number}, "
                    f"Vehicle: {inspection.vehicle.vin}, "
                    f"User: {self.request.user.username}"
                )
                
                messages.success(
                    self.request,
                    f"Inspection {inspection.inspection_number} created. Please complete the inspection form."
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            logger.warning(
                f"Validation error during inspection workflow start. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}"
            )
            
            form.add_error(None, str(e))
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(
                f"Unexpected error during inspection workflow start. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}", 
                exc_info=True
            )
            
            messages.error(
                self.request,
                "An unexpected error occurred while starting the inspection. "
                "Please try again or contact support if the problem persists."
            )
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Start New Inspection'
        return context

# Initial Inspection Views (160-point pre-purchase inspections)
class InitialInspectionListView(LoginRequiredMixin, ListView):
    """List view for initial inspections"""
    model = InitialInspection
    template_name = 'maintenance/initial_inspection_list.html'
    context_object_name = 'initial_inspections'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter initial inspections by technician and apply search/filter parameters"""
        queryset = InitialInspection.objects.select_related('vehicle', 'technician').order_by('-inspection_date')
        
        # Apply filters from GET parameters
        status = self.request.GET.get('status')
        technician = self.request.GET.get('technician')
        date_from = self.request.GET.get('date_from')
        
        if status == 'completed':
            queryset = queryset.filter(is_completed=True)
        elif status == 'in_progress':
            queryset = queryset.filter(is_completed=False)
            
        if technician:
            queryset = queryset.filter(technician_id=technician)
            
        if date_from:
            queryset = queryset.filter(inspection_date__gte=date_from)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add technicians for filter dropdown
        from django.contrib.auth.models import User
        context['technicians'] = User.objects.filter(
            initial_inspections__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        return context


class InitialInspectionDetailView(LoginRequiredMixin, DetailView):
    """Detail view for initial inspection results"""
    model = InitialInspection
    template_name = 'maintenance/initial_inspection_detail.html'
    context_object_name = 'initial_inspection'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add field groupings for template display
        context['engine_performance_fields'] = [
            ('engine_start_condition', 'Engine start condition'),
            ('idle_quality', 'Idle quality'),
            ('acceleration_response', 'Acceleration response'),
            ('engine_noise_levels', 'Engine noise levels'),
            ('exhaust_smoke_color', 'Exhaust smoke color'),
        ]
        
        context['braking_system_fields'] = [
            ('brake_pedal_feel', 'Brake pedal feel'),
            ('brake_response', 'Brake response'),
            ('brake_noise', 'Brake noise'),
            ('parking_brake_operation', 'Parking brake operation'),
        ]
        
        return context


class CreateInitialInspectionView(LoginRequiredMixin, CreateView):
    """Create view for new initial inspection"""
    model = InitialInspection
    form_class = InitialInspectionForm
    template_name = 'maintenance/create_initial_inspection_form.html'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            with transaction.atomic():
                # Set default technician if not specified
                if not form.instance.technician:
                    form.instance.technician = self.request.user
                
                initial_inspection = form.save()
                
                logger.info(
                    f"Initial inspection created successfully. "
                    f"Inspection ID: {initial_inspection.id}, "
                    f"Technician: {self.request.user.username}, "
                    f"Vehicle: {initial_inspection.vehicle.vin}"
                )
                
                messages.success(
                    self.request,
                    f"Initial inspection {initial_inspection.inspection_number} created successfully."
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            logger.warning(
                f"Validation error during initial inspection creation. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}"
            )
            
            form.add_error(None, str(e))
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(
                f"Unexpected error during initial inspection creation. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}", 
                exc_info=True
            )
            
            messages.error(
                self.request,
                "An unexpected error occurred while creating the initial inspection. "
                "Please try again or contact support if the problem persists."
            )
            
            return self.form_invalid(form)
    
    def get_success_url(self):
        return f"/initial-inspections/{self.object.pk}/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Initial Inspection'
        return context


class UpdateInitialInspectionView(LoginRequiredMixin, UpdateView):
    """Update view for initial inspection"""
    model = InitialInspection
    form_class = InitialInspectionForm
    template_name = 'maintenance/update_initial_inspection_form.html'
    context_object_name = 'initial_inspection'
    
    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            with transaction.atomic():
                initial_inspection = form.save()
                
                logger.info(
                    f"Initial inspection updated successfully. "
                    f"Inspection ID: {initial_inspection.id}, "
                    f"User: {self.request.user.username}, "
                    f"Vehicle: {initial_inspection.vehicle.vin}"
                )
                
                messages.success(
                    self.request,
                    f"Initial inspection {initial_inspection.inspection_number} updated successfully."
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            logger.warning(
                f"Validation error during initial inspection update. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}"
            )
            
            form.add_error(None, str(e))
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(
                f"Unexpected error during initial inspection update. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}", 
                exc_info=True
            )
            
            messages.error(
                self.request,
                "An unexpected error occurred while updating the initial inspection. "
                "Please try again or contact support if the problem persists."
            )
            
            return self.form_invalid(form)
    
    def get_success_url(self):
        return f"/maintenance-history/initial-inspections/{self.object.pk}/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Update Initial Inspection - {self.object.inspection_number}'
        
        # Add field groupings for the form
        context['road_test_fields'] = [
            ('engine_start_condition', 'Engine Start Condition'),
            ('idle_quality', 'Idle Quality'),
            ('acceleration_response', 'Acceleration Response'),
            ('engine_noise_levels', 'Engine Noise Levels'),
            ('exhaust_smoke_color', 'Exhaust Smoke Color'),
            ('transmission_shifting', 'Transmission Shifting'),
            ('brake_pedal_feel', 'Brake Pedal Feel'),
            ('brake_response', 'Brake Response'),
            ('brake_noise', 'Brake Noise'),
            ('steering_response', 'Steering Response'),
            ('steering_alignment', 'Steering Alignment'),
            ('suspension_comfort', 'Suspension Comfort'),
            ('tire_wear_patterns', 'Tire Wear Patterns'),
            ('road_noise_levels', 'Road Noise Levels'),
            ('seat_belt_condition', 'Seat Belt Condition'),
            ('seat_belt_operation', 'Seat Belt Operation'),
        ]
        
        context['frame_structure_fields'] = [
            ('frame_unibody_condition', 'Frame/Unibody Condition'),
        ]
        
        return context


class InitialInspectionAjaxView(LoginRequiredMixin, View):
    """AJAX view for initial inspection details modal"""
    
    def get(self, request, pk):
        """Return initial inspection details as JSON for modal display"""
        try:
            initial_inspection = get_object_or_404(InitialInspection, pk=pk)
            
            # Generate HTML content for the modal
            html_content = self._generate_initial_inspection_html(initial_inspection)
            
            return JsonResponse({
                'success': True,
                'html': html_content
            })
            
        except Exception as e:
            logger.error(f"Error loading initial inspection details: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Failed to load initial inspection details'
            })
    
    def _generate_initial_inspection_html(self, initial_inspection):
        """Generate HTML content for initial inspection modal"""
        
        # Get technician display name
        technician_name = self._get_technician_display_name(initial_inspection.technician)
        
        html = f"""
        <div class="space-y-6">
          <!-- Inspection Header -->
          <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div class="flex items-center justify-between mb-3">
              <div>
                <h4 class="text-lg font-semibold text-amber-800">{initial_inspection.inspection_number}</h4>
                <p class="text-sm text-amber-700">160-Point Pre-Purchase Inspection</p>
              </div>
              <div class="text-right">
                <div class="text-sm text-amber-600">
                  <i class="fas fa-calendar mr-1"></i>
                  {initial_inspection.inspection_date.strftime('%B %d, %Y at %I:%M %p')}
                </div>
                <div class="text-sm text-amber-600">
                  <i class="fas fa-tachometer-alt mr-1"></i>
                  {initial_inspection.mileage_at_inspection:,} miles
                </div>
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-amber-600 mb-1">Vehicle</p>
                <p class="font-medium text-amber-800">{initial_inspection.vehicle.make} {initial_inspection.vehicle.model}</p>
                <p class="text-xs text-amber-600">VIN: {initial_inspection.vehicle.vin}</p>
              </div>
              <div>
                <p class="text-xs text-amber-600 mb-1">Technician</p>
                <p class="font-medium text-amber-800">{technician_name}</p>
              </div>
            </div>
            
            <div class="mt-3 pt-3 border-t border-amber-200">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <span class="text-sm text-amber-700">Completion Status:</span>
                  <span class="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {'bg-green-100 text-green-800' if initial_inspection.is_completed else 'bg-yellow-100 text-yellow-800'}">
                    <i class="fas fa-{'check' if initial_inspection.is_completed else 'clock'} mr-1"></i>
                    {'Completed' if initial_inspection.is_completed else 'In Progress'}
                  </span>
                </div>
                <div class="text-right">
                  <div class="text-lg font-semibold text-amber-800">{initial_inspection.completion_percentage}%</div>
                  <div class="text-xs text-amber-600">Progress</div>
                </div>
              </div>
            </div>
          </div>
        """
        
        # Add inspection sections
        sections = [
            {
                'title': 'Road Test Performance',
                'icon': 'fas fa-road',
                'color': 'blue',
                'fields': [
                    ('cold_engine_operation', 'Cold Engine Operation'),
                    ('throttle_operation', 'Throttle Operation'),
                    ('warmup_operation', 'Warm-up Operation'),
                    ('operating_temp_performance', 'Operating Temperature Performance'),
                    ('normal_operating_temp', 'Normal Operating Temperature'),
                    ('brake_vibrations', 'Brake Vibrations'),
                    ('engine_fan_operation', 'Engine Fan Operation'),
                    ('brake_pedal_specs', 'Brake Pedal Specifications'),
                    ('abs_operation', 'ABS Operation'),
                    ('parking_brake_operation', 'Parking Brake Operation'),
                    ('seat_belt_condition', 'Seat Belt Condition'),
                    ('seat_belt_operation', 'Seat Belt Operation'),
                    ('transmission_operation', 'Transmission Operation'),
                    ('auto_trans_cold', 'Auto Transmission (Cold)'),
                    ('auto_trans_operating', 'Auto Transmission (Operating)'),
                    ('steering_feel', 'Steering Feel'),
                    ('steering_centered', 'Steering Centered'),
                    ('vehicle_tracking', 'Vehicle Tracking'),
                    ('tilt_telescopic_steering', 'Tilt & Telescopic Steering'),
                    ('washer_fluid_spray', 'Washer Fluid Spray'),
                    ('front_wipers', 'Front Wipers'),
                    ('rear_wipers', 'Rear Wipers'),
                    ('wiper_rest_position', 'Wiper Rest Position'),
                    ('wiper_blade_replacement', 'Wiper Blade Replacement'),
                    ('speedometer_function', 'Speedometer Function'),
                    ('odometer_function', 'Odometer Function'),
                    ('cruise_control', 'Cruise Control'),
                    ('heater_operation', 'Heater Operation'),
                    ('ac_operation', 'A/C Operation'),
                    ('engine_noise', 'Engine Noise'),
                    ('interior_noise', 'Interior Noise'),
                    ('wind_road_noise', 'Wind/Road Noise'),
                    ('tire_vibration', 'Tire Vibration'),
                ]
            },
            {
                'title': 'Frame, Structure & Underbody',
                'icon': 'fas fa-car',
                'color': 'green',
                'fields': [
                    ('frame_unibody_condition', 'Frame/Unibody Condition'),
                    ('panel_alignment', 'Panel Alignment'),
                    ('underbody_condition', 'Underbody Condition'),
                    ('suspension_leaks_wear', 'Suspension Leaks/Wear'),
                    ('struts_shocks_condition', 'Struts/Shocks Condition'),
                    ('power_steering_leaks', 'Power Steering Leaks'),
                    ('wheel_covers', 'Wheel Covers'),
                    ('tire_condition', 'Tire Condition'),
                    ('tread_depth', 'Tread Depth'),
                    ('tire_specifications', 'Tire Specifications'),
                    ('brake_calipers_lines', 'Brake Calipers & Lines'),
                    ('brake_system_equipment', 'Brake System Equipment'),
                    ('brake_pad_life', 'Brake Pad Life'),
                    ('brake_rotors_drums', 'Brake Rotors/Drums'),
                    ('exhaust_system', 'Exhaust System'),
                    ('engine_trans_mounts', 'Engine/Trans Mounts'),
                    ('drive_axle_shafts', 'Drive/Axle Shafts'),
                    ('cv_joints_boots', 'CV Joints/Boots'),
                    ('engine_fluid_leaks', 'Engine Fluid Leaks'),
                    ('transmission_leaks', 'Transmission Leaks'),
                    ('differential_fluid', 'Differential Fluid'),
                ]
            },
            {
                'title': 'Under Hood Components',
                'icon': 'fas fa-cogs',
                'color': 'purple',
                'fields': [
                    ('drive_belts_hoses', 'Drive Belts & Hoses'),
                    ('underhood_labels', 'Under-hood Labels'),
                    ('air_filter_condition', 'Air Filter Condition'),
                    ('battery_damage', 'Battery Damage'),
                    ('battery_test', 'Battery Test'),
                    ('battery_posts_cables', 'Battery Posts & Cables'),
                    ('battery_secured', 'Battery Secured'),
                    ('charging_system', 'Charging System'),
                    ('coolant_level', 'Coolant Level'),
                    ('coolant_protection', 'Coolant Protection'),
                ]
            }
        ]
        
        for section in sections:
            html += f"""
            <div class="bg-white border border-gray-200 rounded-lg p-4">
              <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <i class="{section['icon']} text-{section['color']}-600 mr-2"></i>
                {section['title']}
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            """
            
            for field_name, field_label in section['fields']:
                field_value = getattr(initial_inspection, field_name, '')
                status_class = self._get_status_class(field_value)
                status_icon = self._get_status_icon(field_value)
                status_text = self._get_status_text(field_value)
                
                html += f"""
                <div class="flex items-center justify-between p-2 bg-gray-50 rounded border">
                  <span class="text-sm text-gray-700">{field_label}</span>
                  <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium {status_class}">
                    <i class="{status_icon} mr-1"></i>
                    {status_text}
                  </span>
                </div>
                """
            
            html += "</div></div>"
        
        # Add summary section if inspection is completed
        if initial_inspection.is_completed:
            failed_points = initial_inspection.failed_points
            if failed_points:
                html += f"""
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 class="text-lg font-semibold text-red-800 mb-4 flex items-center">
                    <i class="fas fa-exclamation-triangle text-red-600 mr-2"></i>
                    Issues Found ({len(failed_points)} items)
                  </h4>
                  <div class="space-y-2">
                """
                
                for issue in failed_points:
                    html += f"""
                    <div class="flex items-center p-2 bg-white rounded border border-red-200">
                      <i class="fas fa-times-circle text-red-500 mr-2"></i>
                      <span class="text-sm text-gray-700">{issue}</span>
                    </div>
                    """
                
                html += "</div></div>"
            else:
                html += """
                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 class="text-lg font-semibold text-green-800 mb-2 flex items-center">
                    <i class="fas fa-check-circle text-green-600 mr-2"></i>
                    Inspection Passed
                  </h4>
                  <p class="text-sm text-green-700">No major issues found during the inspection.</p>
                </div>
                """
        
        # Add notes sections if they exist
        notes_sections = [
            ('road_test_notes', 'Road Test Notes'),
            ('frame_structure_notes', 'Frame & Structure Notes'),
            ('underhood_notes', 'Under Hood Notes'),
            ('overall_notes', 'Overall Notes'),
            ('recommendations', 'Recommendations'),
        ]
        
        for field_name, section_title in notes_sections:
            notes = getattr(initial_inspection, field_name, '')
            if notes:
                html += f"""
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 class="text-lg font-semibold text-gray-800 mb-2 flex items-center">
                    <i class="fas fa-sticky-note text-blue-600 mr-2"></i>
                    {section_title}
                  </h4>
                  <p class="text-sm text-gray-600 bg-white p-3 rounded border">{notes}</p>
                </div>
                """
        
        html += "</div>"
        
        return html
    
    def _get_status_class(self, status):
        """Get CSS class for status display"""
        status_classes = {
            'pass': 'bg-green-100 text-green-800',
            'fail': 'bg-red-100 text-red-800',
            'minor': 'bg-yellow-100 text-yellow-800',
            'major': 'bg-red-100 text-red-800',
            'na': 'bg-gray-100 text-gray-800',
            'needs_attention': 'bg-orange-100 text-orange-800',
        }
        return status_classes.get(status, 'bg-gray-100 text-gray-800')
    
    def _get_status_icon(self, status):
        """Get icon for status display"""
        status_icons = {
            'pass': 'fas fa-check-circle',
            'fail': 'fas fa-times-circle',
            'minor': 'fas fa-exclamation-triangle',
            'major': 'fas fa-exclamation-circle',
            'na': 'fas fa-minus-circle',
            'needs_attention': 'fas fa-exclamation-triangle',
        }
        return status_icons.get(status, 'fas fa-question-circle')
    
    def _get_status_text(self, status):
        """Get display text for status"""
        status_text = {
            'pass': 'Pass',
            'fail': 'Fail',
            'minor': 'Minor Issue',
            'major': 'Major Issue',
            'na': 'N/A',
            'needs_attention': 'Needs Attention',
        }
        return status_text.get(status, 'Not Checked')
    
    def _get_technician_display_name(self, technician):
        """Get a proper display name for the technician"""
        if not technician:
            return "Not Assigned"
        
        first_name = (technician.first_name or "").strip()
        last_name = (technician.last_name or "").strip()
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return technician.username or f"User {technician.id}"