from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse
import logging
import json
from .models import MaintenanceRecord, PartUsage
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