from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import logging
import json
from .models import MaintenanceRecord, PartUsage, Inspection, Inspections
from .forms import MaintenanceRecordForm, InspectionForm, InspectionRecordForm
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
                    f"Total parts cost: ${parts_summary.get('total_cost', 0):.2f}"
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
            
            messages.success(self.request, base_message + parts_message)
        else:
            messages.success(self.request, base_message)
    
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
    success_url = '/maintenance/inspection-forms/'
    
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
                    f"Completion: {inspection_form.completion_percentage}%"
                )
                
                # Create success message
                messages.success(
                    self.request,
                    f"Inspection form created successfully for {inspection_form.inspection.inspection_number}. "
                    f"Progress: {inspection_form.completion_percentage}% complete."
                )
                
                return super().form_valid(form)
                
        except ValidationError as e:
            logger.warning(
                f"Validation error during inspection form creation. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}"
            )
            
            form.add_error(None, str(e))
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(
                f"Unexpected error during inspection form creation. "
                f"User: {self.request.user.username}, "
                f"Error: {str(e)}", 
                exc_info=True
            )
            
            messages.error(
                self.request,
                "An unexpected error occurred while creating the inspection form. "
                "Please try again or contact support if the problem persists."
            )
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
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
                    
                    messages.success(
                        request,
                        f"Inspection form updated successfully. "
                        f"Progress: {inspection_form.completion_percentage}% complete."
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'completion_percentage': inspection_form.completion_percentage,
                        'is_completed': inspection_form.is_completed,
                        'message': 'Form updated successfully'
                    })
                    
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

class CreateInspectionRecordView(LoginRequiredMixin, CreateView):
    model = Inspection
    form_class = InspectionRecordForm
    template_name = 'maintenance/create_inspection_record.html'
    success_url = '/maintenance/inspections/'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f"Inspection record created successfully for {form.instance.inspection_number}."
        )
        return super().form_valid(form)