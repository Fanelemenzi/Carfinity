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
from .models import MaintenanceRecord, PartUsage, Inspection
from .forms import MaintenanceRecordForm
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