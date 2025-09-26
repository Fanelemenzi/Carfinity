# dashboard_views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.decorators import method_decorator
from django.contrib import messages
from users.permissions import require_group, check_permission_conflicts

# AutoCare Dashboard Views - Matching AutoAssess Pattern
@method_decorator([require_group('AutoCare'), check_permission_conflicts], name='dispatch')
class AutoCareDashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/autocare_dashboard.html'
    context_object_name = 'maintenance_records'
    
    def get_queryset(self):
        # Return empty queryset for now - will be populated with actual maintenance data later
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add context data for the AutoCare dashboard
        context.update({
            'total_vehicles': 156,
            'pending_maintenance': 23,
            'completed_today': 8,
            'avg_health_score': '87.3%',
            'monthly_revenue': '£45.2K',
            'customer_satisfaction': '4.8/5',
        })
        
        return context

@method_decorator([require_group('AutoCare'), check_permission_conflicts], name='dispatch')
class MaintenanceDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/autocare_maintenance_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance_id = kwargs.get('maintenance_id', 'MNT-2024-001')
        
        # Hardcoded maintenance data for the first few records
        maintenance_data = self.get_maintenance_data(maintenance_id)
        
        context.update({
            'maintenance_id': maintenance_id,
            'maintenance_data': maintenance_data,
        })
        
        return context
    
    def get_maintenance_data(self, maintenance_id):
        """
        Get hardcoded maintenance data for specific records
        """
        maintenance_records = {
            'MNT-2024-001': {
                'maintenance_id': 'MNT-2024-001',
                'customer_name': 'Johnson, A.',
                'vehicle': '2020 Ford Focus',
                'vin': 'WF0AXXGCDA1234567',
                'service_date': 'Sep 20, 2024',
                'service_value': '£850',
                'status': 'COMPLETED',
                'service_type': 'Full Service',
                'progress': 100,
                'technician': 'Mike Thompson',
                'location': 'Birmingham, UK',
                'service_description': 'Complete vehicle service including oil change, brake inspection, and safety checks.',
                'sections': [
                    {
                        'id': 'engine',
                        'name': 'ENGINE SERVICE',
                        'icon': '⚙️',
                        'status': 'Complete',
                        'items_checked': '15/15',
                        'cost': '£320',
                        'time_spent': '2.5h'
                    },
                    {
                        'id': 'brakes',
                        'name': 'BRAKE SYSTEM',
                        'icon': '🛑',
                        'status': 'Complete',
                        'items_checked': '8/8',
                        'cost': '£180',
                        'time_spent': '1.5h'
                    },
                    {
                        'id': 'suspension',
                        'name': 'SUSPENSION',
                        'icon': '🔧',
                        'status': 'Complete',
                        'items_checked': '6/6',
                        'cost': '£120',
                        'time_spent': '1h'
                    },
                    {
                        'id': 'electrical',
                        'name': 'ELECTRICAL',
                        'icon': '🔌',
                        'status': 'Complete',
                        'items_checked': '10/10',
                        'cost': '£90',
                        'time_spent': '45m'
                    },
                    {
                        'id': 'fluids',
                        'name': 'FLUIDS & FILTERS',
                        'icon': '💧',
                        'status': 'Complete',
                        'items_checked': '7/7',
                        'cost': '£140',
                        'time_spent': '30m'
                    }
                ]
            },
            'MNT-2024-002': {
                'maintenance_id': 'MNT-2024-002',
                'customer_name': 'Williams, S.',
                'vehicle': '2018 Volkswagen Golf',
                'vin': 'WVWZZZ1JZ1W123456',
                'service_date': 'Sep 21, 2024',
                'service_value': '£450',
                'status': 'IN_PROGRESS',
                'service_type': 'Basic Service',
                'progress': 65,
                'technician': 'Sarah Mitchell',
                'location': 'Manchester, UK',
                'service_description': 'Basic service including oil change and safety inspection.',
                'sections': [
                    {
                        'id': 'engine',
                        'name': 'ENGINE SERVICE',
                        'icon': '⚙️',
                        'status': 'Complete',
                        'items_checked': '12/12',
                        'cost': '£200',
                        'time_spent': '2h'
                    },
                    {
                        'id': 'brakes',
                        'name': 'BRAKE SYSTEM',
                        'icon': '🛑',
                        'status': 'In Progress',
                        'items_checked': '5/8',
                        'cost': '£120',
                        'time_spent': '1h'
                    },
                    {
                        'id': 'suspension',
                        'name': 'SUSPENSION',
                        'icon': '🔧',
                        'status': 'Pending',
                        'items_checked': '0/6',
                        'cost': '£80',
                        'time_spent': '0m'
                    },
                    {
                        'id': 'fluids',
                        'name': 'FLUIDS & FILTERS',
                        'icon': '💧',
                        'status': 'Complete',
                        'items_checked': '5/5',
                        'cost': '£50',
                        'time_spent': '20m'
                    }
                ]
            }
        }
        
        # Return default data if maintenance record not found
        return maintenance_records.get(maintenance_id, {
            'maintenance_id': maintenance_id,
            'customer_name': 'Unknown Customer',
            'vehicle': 'Unknown Vehicle',
            'vin': 'Unknown VIN',
            'service_date': 'Unknown Date',
            'service_value': '£0',
            'status': 'Unknown',
            'service_type': 'Unknown',
            'progress': 0,
            'technician': 'Unassigned',
            'location': 'Unknown Location',
            'service_description': 'No description available.',
            'sections': []
        })

@method_decorator([require_group('AutoCare'), check_permission_conflicts], name='dispatch')
class BookMaintenanceView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/autocare_booking.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        # Return empty queryset for now - will be populated with actual booking data later
        return []
    
    def post(self, request, *args, **kwargs):
        # Handle form submission for booking new maintenance
        # This will be implemented in later tasks
        messages.success(request, 'Maintenance booking submitted successfully!')
        return self.get(request, *args, **kwargs)
