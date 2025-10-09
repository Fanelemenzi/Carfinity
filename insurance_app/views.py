# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, F, Sum
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from .forms import AssessmentCommentForm, CommentReplyForm, CommentResolutionForm
from assessments.models import AssessmentComment, AssessmentWorkflow
from users.permissions import require_group, check_permission_conflicts
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timesince import timesince
from django.views import View

# Dashboard Views
@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/insurance_dashboard.html'
    context_object_name = 'policies'
    
    def get_queryset(self):
        return InsurancePolicy.objects.filter(
            policy_holder=self.request.user,
            status='active'
        ).prefetch_related('vehicles')
    
    def get_context_data(self, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        context = super().get_context_data(**kwargs)
        
        # Initialize error context
        error_context = {
            'has_errors': False,
            'error_messages': [],
            'warning_messages': []
        }
        
        try:
            # Get all vehicles for user's policies with error handling
            vehicles = Vehicle.objects.filter(
                policy__policy_holder=self.request.user,
                policy__status='active'
            )
            
            if not vehicles.exists():
                error_context['warning_messages'].append("No active vehicles found in your insurance policies.")
                
        except Exception as e:
            logger.error(f"Error retrieving vehicles for insurance dashboard, user {self.request.user.id}: {str(e)}")
            error_context['has_errors'] = True
            error_context['error_messages'].append("Unable to load vehicle data. Please try again later.")
            vehicles = Vehicle.objects.none()
        
        # Portfolio Maintenance Compliance with error handling
        try:
            compliance_data = MaintenanceCompliance.objects.filter(
                vehicle__in=vehicles
            ).aggregate(
                avg_compliance=Avg('overall_compliance_rate'),
                avg_critical_compliance=Avg('critical_maintenance_compliance')
            )
        except Exception as e:
            logger.warning(f"Error retrieving compliance data for user {self.request.user.id}: {str(e)}")
            compliance_data = {'avg_compliance': 0, 'avg_critical_compliance': 0}
            error_context['warning_messages'].append("Unable to load compliance data.")
        
        # Vehicle Condition Distribution with error handling
        try:
            condition_distribution = vehicles.values('current_condition').annotate(
                count=Count('id')
            )
        except Exception as e:
            logger.warning(f"Error retrieving condition distribution for user {self.request.user.id}: {str(e)}")
            condition_distribution = []
            error_context['warning_messages'].append("Unable to load vehicle condition data.")
        
        # Risk Alerts with error handling
        try:
            active_alerts = RiskAlert.objects.filter(
                vehicle__in=vehicles,
                is_resolved=False
            ).order_by('-severity', '-created_at')[:10]
        except Exception as e:
            logger.warning(f"Error retrieving risk alerts for user {self.request.user.id}: {str(e)}")
            active_alerts = []
            error_context['warning_messages'].append("Unable to load risk alerts.")
        
        # Recent Accidents with error handling
        try:
            recent_accidents = Accident.objects.filter(
                vehicle__in=vehicles,
                accident_date__gte=timezone.now() - timedelta(days=30)
            ).select_related('vehicle')
        except Exception as e:
            logger.warning(f"Error retrieving recent accidents for user {self.request.user.id}: {str(e)}")
            recent_accidents = []
            error_context['warning_messages'].append("Unable to load recent accident data.")
        
        # Get high-risk vehicles for the table with error handling
        try:
            high_risk_vehicles_list = vehicles.filter(risk_score__gte=7).select_related('policy')[:10]
        except Exception as e:
            logger.warning(f"Error retrieving high-risk vehicles for user {self.request.user.id}: {str(e)}")
            high_risk_vehicles_list = []
            error_context['warning_messages'].append("Unable to load high-risk vehicle data.")
        
        # Calculate average health index with error handling
        try:
            avg_health_index = vehicles.aggregate(avg_health=Avg('vehicle_health_index'))['avg_health'] or 0
        except Exception as e:
            logger.warning(f"Error calculating average health index for user {self.request.user.id}: {str(e)}")
            avg_health_index = 0
            error_context['warning_messages'].append("Unable to calculate average health index.")
        
        # Add error messages to Django messages framework
        from django.contrib import messages
        if error_context['has_errors']:
            for error_msg in error_context['error_messages']:
                messages.error(self.request, error_msg)
        
        if error_context['warning_messages']:
            for warning_msg in error_context['warning_messages']:
                messages.warning(self.request, warning_msg)
        
        # Calculate high-risk vehicle count safely
        try:
            high_risk_count = vehicles.filter(risk_score__gte=7).count()
        except Exception as e:
            logger.warning(f"Error counting high-risk vehicles for user {self.request.user.id}: {str(e)}")
            high_risk_count = 0
        
        context.update({
            'total_vehicles': vehicles.count() if vehicles else 0,
            'avg_compliance_rate': compliance_data['avg_compliance'] or 0,
            'avg_critical_compliance': compliance_data['avg_critical_compliance'] or 0,
            'avg_health_index': avg_health_index,
            'condition_distribution': list(condition_distribution),
            'active_alerts': active_alerts,
            'recent_accidents': recent_accidents,
            'high_risk_vehicles': high_risk_count,
            'high_risk_vehicles_list': high_risk_vehicles_list,
            'error_context': error_context,
        })
        
        return context

@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class VehicleDetailView(LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'dashboard/insurance_detail.html'
    context_object_name = 'vehicle'
    
    def get_queryset(self):
        return Vehicle.objects.filter(
            policy__policy_holder=self.request.user
        ).select_related('policy', 'compliance')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = self.object
        
        # Maintenance Schedule
        upcoming_maintenance = vehicle.maintenance_schedules.filter(
            is_completed=False,
            scheduled_date__gte=timezone.now().date()
        ).order_by('scheduled_date')[:5]
        
        overdue_maintenance = vehicle.maintenance_schedules.filter(
            is_completed=False,
            scheduled_date__lt=timezone.now().date()
        ).order_by('scheduled_date')
        
        # Condition History
        condition_history = vehicle.condition_scores.all()[:12]
        
        # Risk Alerts
        vehicle_alerts = vehicle.risk_alerts.filter(
            is_resolved=False
        ).order_by('-severity', '-created_at')
        
        # Comprehensive Accident Data
        from .utils import AccidentHistorySyncManager
        comprehensive_accidents = AccidentHistorySyncManager.get_comprehensive_accident_data(vehicle)
        
        context.update({
            'upcoming_maintenance': upcoming_maintenance,
            'overdue_maintenance': overdue_maintenance,
            'condition_history': condition_history,
            'vehicle_alerts': vehicle_alerts,
            'comprehensive_accidents': comprehensive_accidents,
        })
        
        return context

@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentDashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/insurance_assessment_dashboard_new.html'
    context_object_name = 'assessments'
    paginate_by = 20
    
    def get_queryset(self):
        # Import VehicleAssessment from assessments app
        from assessments.models import VehicleAssessment
        from organizations.models import Organization
        
        # Get user's organizations
        user_organizations = Organization.objects.filter(
            organization_members__user=self.request.user,
            organization_members__is_active=True
        ).distinct()
        
        # Get assessments for user's organizations OR assigned to the current user OR created by the user
        queryset = VehicleAssessment.objects.filter(
            models.Q(organization__in=user_organizations) |
            models.Q(assigned_agent=self.request.user) |
            models.Q(user=self.request.user)
        ).select_related(
            'vehicle', 'user', 'assigned_agent', 'organization'
        ).prefetch_related(
            'exterior_damage', 'wheels_tires', 'interior_damage',
            'mechanical_systems', 'electrical_systems', 'safety_systems',
            'frame_structural', 'fluid_systems'
        ).distinct().order_by('-assessment_date')
        
        # Apply filters from request parameters
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(agent_status=status_filter)
            
        organization_filter = self.request.GET.get('organization')
        if organization_filter:
            queryset = queryset.filter(organization_id=organization_filter)
            
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(assessment_id__icontains=search_query) |
                models.Q(vehicle__vin__icontains=search_query) |
                models.Q(vehicle__make__icontains=search_query) |
                models.Q(vehicle__model__icontains=search_query) |
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query) |
                models.Q(organization__name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Import VehicleAssessment from assessments app
        from assessments.models import VehicleAssessment
        from organizations.models import Organization
        from django.db.models import Count, Avg, Sum, Q
        from datetime import timedelta
        
        # Get user's organizations
        user_organizations = Organization.objects.filter(
            organization_members__user=self.request.user,
            organization_members__is_active=True
        ).distinct()
        
        # Get all assessments for the user's organizations OR assigned to the user OR created by the user
        organization_assessments = VehicleAssessment.objects.filter(
            models.Q(organization__in=user_organizations) |
            models.Q(assigned_agent=self.request.user) |
            models.Q(user=self.request.user)
        ).distinct()
        
        # Get organizations for filtering (user's organizations)
        organizations = user_organizations.order_by('name')
        
        # Calculate real statistics based on organization assessments
        total_assessments = organization_assessments.count()
        pending_reviews = organization_assessments.filter(agent_status='pending_review').count()
        approved_assessments = organization_assessments.filter(agent_status='approved').count()
        rejected_assessments = organization_assessments.filter(agent_status='rejected').count()
        changes_requested = organization_assessments.filter(agent_status='changes_requested').count()
        
        # Calculate total estimated cost
        total_estimated_cost = organization_assessments.aggregate(
            total_cost=Sum('estimated_repair_cost')
        )['total_cost'] or 0
        
        # Status distribution for charts
        status_distribution = organization_assessments.values('agent_status').annotate(
            count=Count('id')
        ).order_by('agent_status')
        
        # Recent assessments for quick access
        recent_assessments = organization_assessments.order_by('-assessment_date')[:5]
        
        # Urgent assessments (those with review deadlines approaching)
        urgent_assessments = organization_assessments.filter(
            review_deadline__lte=timezone.now() + timedelta(days=2),
            agent_status__in=['pending_review', 'under_review']
        ).order_by('review_deadline')
        
        # Calculate average processing time based on completed assessments
        completed_assessments = organization_assessments.filter(
            agent_status__in=['approved', 'rejected'],
            completed_date__isnull=False
        )
        
        avg_processing_time = None
        if completed_assessments.exists():
            # Calculate average time between assessment_date and completed_date
            processing_times = []
            for assessment in completed_assessments:
                if assessment.completed_date and assessment.assessment_date:
                    delta = assessment.completed_date - assessment.assessment_date
                    processing_times.append(delta.total_seconds() / 3600)  # Convert to hours
            
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        # Calculate accuracy rate based on approved vs rejected assessments
        total_reviewed = approved_assessments + rejected_assessments
        accuracy_rate = (approved_assessments / total_reviewed * 100) if total_reviewed > 0 else 0
        
        # Priority assessments (high value or urgent deadlines)
        high_priority_assessments = organization_assessments.filter(
            Q(estimated_repair_cost__gte=10000) |
            Q(review_deadline__lte=timezone.now() + timedelta(days=1))
        ).count()
        
        context.update({
            'total_assessments': total_assessments,
            'pending_reviews': pending_reviews,
            'approved_assessments': approved_assessments,
            'rejected_assessments': rejected_assessments,
            'changes_requested': changes_requested,
            'high_priority_assessments': high_priority_assessments,
            'avg_processing_time': f'{avg_processing_time:.1f}h' if avg_processing_time else 'N/A',
            'total_estimated_cost': f'£{total_estimated_cost:,.0f}' if total_estimated_cost else '£0',
            'status_distribution': list(status_distribution),
            'recent_assessments': recent_assessments,
            'urgent_assessments': urgent_assessments,
            'accuracy_rate': f'{accuracy_rate:.1f}%',
            'customer_satisfaction': 'N/A',  # Will be calculated from actual feedback data
            'organizations': organizations,
            
            # Filter values for maintaining state
            'current_status_filter': self.request.GET.get('status', ''),
            'current_search_query': self.request.GET.get('search', ''),
            'current_organization_filter': self.request.GET.get('organization', ''),
        })
        
        return context

@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class BookAssessmentView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/insurance_booking.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        # Get actual booking data from the database
        from assessments.models import VehicleAssessment
        return VehicleAssessment.objects.filter(
            user=self.request.user,
            agent_status='pending_assignment'
        ).select_related('vehicle').order_by('-created_at')
    
    def post(self, request, *args, **kwargs):
        # Handle form submission for booking new assessments
        from assessments.models import VehicleAssessment
        from vehicles.models import Vehicle
        
        vehicle_id = request.POST.get('vehicle_id')
        incident_description = request.POST.get('incident_description', '')
        incident_location = request.POST.get('incident_location', '')
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, policy__policy_holder=request.user)
            
            # Create new assessment request
            assessment = VehicleAssessment.objects.create(
                user=request.user,
                vehicle=vehicle,
                incident_description=incident_description,
                incident_location=incident_location,
                agent_status='pending_assignment'
            )
            
            messages.success(request, f'Assessment request #{assessment.assessment_id} submitted successfully!')
            
        except Vehicle.DoesNotExist:
            messages.error(request, 'Invalid vehicle selected.')
        except Exception as e:
            messages.error(request, f'Error submitting assessment request: {str(e)}')
        
        return self.get(request, *args, **kwargs)

@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentDetailView(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/insurance_assessment_detail.html'
    context_object_name = 'assessment'
    
    def get_object(self):
        # Import VehicleAssessment from assessments app
        from assessments.models import VehicleAssessment
        
        assessment_id = self.kwargs.get('claim_id')
        
        # Try to get by assessment_id first, then by pk if it's numeric
        try:
            if assessment_id.isdigit():
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related(
                        'vehicle', 'user', 'assigned_agent'
                    ).prefetch_related(
                        'exterior_damage', 'wheels_tires', 'interior_damage',
                        'mechanical_systems', 'electrical_systems', 'safety_systems',
                        'frame_structural', 'fluid_systems', 'documentation', 'photos'
                    ),
                    pk=assessment_id,
                    assigned_agent=self.request.user
                )
            else:
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related(
                        'vehicle', 'user', 'assigned_agent'
                    ).prefetch_related(
                        'exterior_damage', 'wheels_tires', 'interior_damage',
                        'mechanical_systems', 'electrical_systems', 'safety_systems',
                        'frame_structural', 'fluid_systems', 'documentation', 'photos'
                    ),
                    assessment_id=assessment_id,
                    assigned_agent=self.request.user
                )
        except VehicleAssessment.DoesNotExist:
            # Fallback to any assessment for the agent if specific one not found
            assessment = get_object_or_404(
                VehicleAssessment.objects.select_related(
                    'vehicle', 'user', 'assigned_agent'
                ).prefetch_related(
                    'exterior_damage', 'wheels_tires', 'interior_damage',
                    'mechanical_systems', 'electrical_systems', 'safety_systems',
                    'frame_structural', 'fluid_systems', 'documentation', 'photos'
                ),
                assigned_agent=self.request.user
            )
        
        return assessment
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object
        
        # Get all related assessment section data
        assessment_sections = []
        
        # Exterior Damage Section
        try:
            exterior_damage = assessment.exterior_damage
            exterior_cost = self.calculate_section_cost(exterior_damage, 'exterior')
            damage_details = self.get_section_damage_details(exterior_damage, 'exterior')
            repair_timeline = self.get_section_repair_timeline(exterior_damage, 'exterior')
            assessment_sections.append({
                'id': 'exterior',
                'name': 'EXTERIOR DAMAGE',
                'icon': '🚗',
                'points': self.get_section_completion(exterior_damage, 'exterior'),
                'status': 'Complete' if exterior_damage else 'Pending',
                'severity': self.get_section_severity(exterior_damage, 'exterior'),
                'cost': f'£{exterior_cost:,.0f}',
                'damageLevel': self.get_section_severity(exterior_damage, 'exterior'),
                'estimatedCost': f'£{exterior_cost:,.0f}',
                'componentCount': self.get_component_count('exterior'),
                'data': exterior_damage,
                'damageDetails': damage_details,
                'repairTimeline': repair_timeline,
                'rawCost': exterior_cost
            })
        except:
            assessment_sections.append({
                'id': 'exterior',
                'name': 'EXTERIOR DAMAGE',
                'icon': '🚗',
                'points': '0/38 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 38,
                'data': None,
                'damageDetails': {'damaged_components': 0, 'total_components': 38, 'damage_percentage': 0, 'critical_damage': False, 'repair_priority': 'Low'},
                'repairTimeline': {'days': 0, 'description': 'No repairs needed'},
                'rawCost': 0
            })
        
        # Wheels & Tires Section
        try:
            wheels_tires = assessment.wheels_tires
            wheels_cost = self.calculate_section_cost(wheels_tires, 'wheels')
            assessment_sections.append({
                'id': 'wheels',
                'name': 'WHEELS & TIRES',
                'icon': '🛞',
                'points': self.get_section_completion(wheels_tires, 'wheels'),
                'status': 'Complete' if wheels_tires else 'Pending',
                'severity': self.get_section_severity(wheels_tires, 'wheels'),
                'cost': f'£{wheels_cost:,.0f}',
                'damageLevel': self.get_section_severity(wheels_tires, 'wheels'),
                'estimatedCost': f'£{wheels_cost:,.0f}',
                'componentCount': self.get_component_count('wheels'),
                'data': wheels_tires
            })
        except:
            assessment_sections.append({
                'id': 'wheels',
                'name': 'WHEELS & TIRES',
                'icon': '🛞',
                'points': '0/12 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 12,
                'data': None
            })
        
        # Interior Damage Section
        try:
            interior_damage = assessment.interior_damage
            interior_cost = self.calculate_section_cost(interior_damage, 'interior')
            assessment_sections.append({
                'id': 'interior',
                'name': 'INTERIOR DAMAGE',
                'icon': '🪑',
                'points': self.get_section_completion(interior_damage, 'interior'),
                'status': 'Complete' if interior_damage else 'Pending',
                'severity': self.get_section_severity(interior_damage, 'interior'),
                'cost': f'£{interior_cost:,.0f}',
                'damageLevel': self.get_section_severity(interior_damage, 'interior'),
                'estimatedCost': f'£{interior_cost:,.0f}',
                'componentCount': self.get_component_count('interior'),
                'data': interior_damage
            })
        except:
            assessment_sections.append({
                'id': 'interior',
                'name': 'INTERIOR DAMAGE',
                'icon': '🪑',
                'points': '0/19 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 19,
                'data': None
            })
        
        # Mechanical Systems Section
        try:
            mechanical_systems = assessment.mechanical_systems
            mechanical_cost = self.calculate_section_cost(mechanical_systems, 'mechanical')
            assessment_sections.append({
                'id': 'mechanical',
                'name': 'MECHANICAL SYSTEMS',
                'icon': '⚙️',
                'points': self.get_section_completion(mechanical_systems, 'mechanical'),
                'status': 'Complete' if mechanical_systems else 'Pending',
                'severity': self.get_section_severity(mechanical_systems, 'mechanical'),
                'cost': f'£{mechanical_cost:,.0f}',
                'damageLevel': self.get_section_severity(mechanical_systems, 'mechanical'),
                'estimatedCost': f'£{mechanical_cost:,.0f}',
                'componentCount': self.get_component_count('mechanical'),
                'data': mechanical_systems
            })
        except:
            assessment_sections.append({
                'id': 'mechanical',
                'name': 'MECHANICAL SYSTEMS',
                'icon': '⚙️',
                'points': '0/20 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 20,
                'data': None
            })
        
        # Electrical Systems Section
        try:
            electrical_systems = assessment.electrical_systems
            electrical_cost = self.calculate_section_cost(electrical_systems, 'electrical')
            assessment_sections.append({
                'id': 'electrical',
                'name': 'ELECTRICAL SYSTEMS',
                'icon': '🔌',
                'points': self.get_section_completion(electrical_systems, 'electrical'),
                'status': 'Complete' if electrical_systems else 'Pending',
                'severity': self.get_section_severity(electrical_systems, 'electrical'),
                'cost': f'£{electrical_cost:,.0f}',
                'damageLevel': self.get_section_severity(electrical_systems, 'electrical'),
                'estimatedCost': f'£{electrical_cost:,.0f}',
                'componentCount': self.get_component_count('electrical'),
                'data': electrical_systems
            })
        except:
            assessment_sections.append({
                'id': 'electrical',
                'name': 'ELECTRICAL SYSTEMS',
                'icon': '🔌',
                'points': '0/9 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 9,
                'data': None
            })
        
        # Safety Systems Section
        try:
            safety_systems = assessment.safety_systems
            safety_cost = self.calculate_section_cost(safety_systems, 'safety')
            assessment_sections.append({
                'id': 'safety',
                'name': 'SAFETY SYSTEMS',
                'icon': '🛡️',
                'points': self.get_section_completion(safety_systems, 'safety'),
                'status': 'Complete' if safety_systems else 'Pending',
                'severity': self.get_section_severity(safety_systems, 'safety'),
                'cost': f'£{safety_cost:,.0f}',
                'damageLevel': self.get_section_severity(safety_systems, 'safety'),
                'estimatedCost': f'£{safety_cost:,.0f}',
                'componentCount': self.get_component_count('safety'),
                'data': safety_systems
            })
        except:
            assessment_sections.append({
                'id': 'safety',
                'name': 'SAFETY SYSTEMS',
                'icon': '🛡️',
                'points': '0/6 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 6,
                'data': None
            })
        
        # Structural Section
        try:
            frame_structural = assessment.frame_structural
            structural_cost = self.calculate_section_cost(frame_structural, 'structural')
            assessment_sections.append({
                'id': 'structural',
                'name': 'FRAME & STRUCTURAL',
                'icon': '🏗️',
                'points': self.get_section_completion(frame_structural, 'structural'),
                'status': 'Complete' if frame_structural else 'Pending',
                'severity': self.get_section_severity(frame_structural, 'structural'),
                'cost': f'£{structural_cost:,.0f}',
                'damageLevel': self.get_section_severity(frame_structural, 'structural'),
                'estimatedCost': f'£{structural_cost:,.0f}',
                'componentCount': self.get_component_count('structural'),
                'data': frame_structural
            })
        except:
            assessment_sections.append({
                'id': 'structural',
                'name': 'FRAME & STRUCTURAL',
                'icon': '🏗️',
                'points': '0/6 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 6,
                'data': None
            })
        
        # Fluid Systems Section
        try:
            fluid_systems = assessment.fluid_systems
            fluid_cost = self.calculate_section_cost(fluid_systems, 'fluids')
            assessment_sections.append({
                'id': 'fluids',
                'name': 'FLUID SYSTEMS',
                'icon': '💧',
                'points': self.get_section_completion(fluid_systems, 'fluids'),
                'status': 'Complete' if fluid_systems else 'Pending',
                'severity': self.get_section_severity(fluid_systems, 'fluids'),
                'cost': f'£{fluid_cost:,.0f}',
                'damageLevel': self.get_section_severity(fluid_systems, 'fluids'),
                'estimatedCost': f'£{fluid_cost:,.0f}',
                'componentCount': self.get_component_count('fluids'),
                'data': fluid_systems
            })
        except:
            assessment_sections.append({
                'id': 'fluids',
                'name': 'FLUID SYSTEMS',
                'icon': '💧',
                'points': '0/6 ⚠️',
                'status': 'Pending',
                'severity': 'Unknown',
                'cost': '£0',
                'damageLevel': 'Unknown',
                'estimatedCost': '£0',
                'componentCount': 6,
                'data': None
            })
        
        # Calculate assessment progress
        total_sections = len(assessment_sections)
        completed_sections = sum(1 for section in assessment_sections if section['status'] == 'Complete')
        assessment_progress = int((completed_sections / total_sections) * 100) if total_sections > 0 else 0
        
        # Get assessment photos
        photos = assessment.photos.all().order_by('category', 'taken_at')
        
        # Calculate detailed cost breakdown
        detailed_costs = self.calculate_detailed_cost_breakdown(assessment)
        
        # Generate repair quote comparisons
        repair_quotes = self.generate_repair_quote_comparisons(assessment)
        
        # Calculate settlement details
        settlement_details = self.calculate_settlement_details(assessment)
        
        # Create assessment data structure compatible with template
        assessment_data = {
            'claim_id': assessment.assessment_id,
            'customer_name': f"{assessment.user.last_name}, {assessment.user.first_name[0]}." if assessment.user.first_name else assessment.user.username,
            'vehicle': str(assessment.vehicle) if assessment.vehicle else 'Unknown Vehicle',
            'vin': assessment.vehicle.vin if assessment.vehicle else 'Unknown VIN',
            'incident_date': assessment.incident_date.strftime('%b %d, %Y') if assessment.incident_date else assessment.assessment_date.strftime('%b %d, %Y'),
            'claim_value': f'£{assessment.estimated_repair_cost:,.0f}' if assessment.estimated_repair_cost else '£0',
            'status': assessment.get_agent_status_display(),
            'damage_type': assessment.get_overall_severity_display() if assessment.overall_severity else 'Unknown',
            'assessment_progress': assessment_progress,
            'estimated_repair_cost': f'£{assessment.estimated_repair_cost:,.0f}' if assessment.estimated_repair_cost else '£0',
            'assessor': assessment.assessor_name or 'Unassigned',
            'location': assessment.incident_location or 'Unknown Location',
            'incident_description': assessment.overall_notes or 'No description available.',
            'sections': assessment_sections
        }
        
        context.update({
            'claim_id': assessment.assessment_id,
            'assessment_data': assessment_data,
            'photos': photos,
            'detailed_costs': detailed_costs,
            'repair_quotes': repair_quotes,
            'settlement_details': settlement_details,
        })
        
        return context
    
    def calculate_section_cost(self, section_obj, section_type):
        """Calculate estimated repair cost for a section based on damage severity"""
        if not section_obj:
            return 0
        
        # Enhanced base costs per component type with more realistic pricing (in GBP)
        base_costs = {
            'exterior': {
                'none': 0, 'light': 250, 'moderate': 650, 'severe': 1500, 'destroyed': 3200
            },
            'wheels': {
                'none': 0, 'light': 75, 'moderate': 200, 'severe': 500, 'destroyed': 950
            },
            'interior': {
                'none': 0, 'light': 150, 'moderate': 400, 'severe': 950, 'destroyed': 1800
            },
            'mechanical': {
                'excellent': 0, 'good': 0, 'fair': 300, 'poor': 800, 'failed': 2200
            },
            'electrical': {
                'working': 0, 'intermittent': 150, 'not_working': 550, 'not_tested': 250
            },
            'safety': {
                'working': 0, 'fault': 450, 'deployed': 1200, 'not_working': 800, 'not_tested': 300
            },
            'structural': {
                'intact': 0, 'minor_damage': 750, 'moderate_damage': 2200, 'severe_damage': 5500, 'compromised': 12000
            },
            'fluids': {
                'good': 0, 'low': 80, 'contaminated': 300, 'leaking': 550, 'empty': 400
            }
        }
        
        # Component-specific multipliers for high-value parts
        component_multipliers = {
            'exterior': {
                'hood': 1.5, 'front_bumper': 1.2, 'rear_bumper': 1.2, 'headlight_housings': 2.0,
                'taillight_housings': 1.8, 'front_fenders': 1.3, 'rear_quarter_panels': 1.4
            },
            'mechanical': {
                'engine_block': 3.0, 'radiator': 1.5, 'transmission': 2.5, 'steering_rack': 2.0
            },
            'safety': {
                'airbag_systems': 2.5, 'abs_system': 2.0, 'stability_control': 1.8
            },
            'structural': {
                'frame_rails': 2.0, 'firewall': 1.8, 'cross_members': 1.5
            }
        }
        
        total_cost = 0
        costs = base_costs.get(section_type, {})
        multipliers = component_multipliers.get(section_type, {})
        
        # Get all fields that represent damage/condition assessments
        for field in section_obj._meta.fields:
            if field.name.endswith('_notes') or field.name in ['assessment', 'id']:
                continue
            
            field_value = getattr(section_obj, field.name, None)
            if field_value and field_value in costs:
                base_cost = costs[field_value]
                # Apply component-specific multiplier if available
                multiplier = multipliers.get(field.name, 1.0)
                total_cost += base_cost * multiplier
        
        return total_cost
    
    def get_section_completion(self, section_obj, section_type):
        """Get completion status for a section"""
        if not section_obj:
            total_points = self.get_component_count(section_type)
            return f'0/{total_points} ⚠️'
        
        # Count completed assessments (non-default values)
        completed = 0
        total = 0
        
        for field in section_obj._meta.fields:
            if field.name.endswith('_notes') or field.name in ['assessment', 'id']:
                continue
            
            total += 1
            field_value = getattr(section_obj, field.name, None)
            
            # Consider field completed if it has a non-default value
            if field_value and field_value not in ['none', 'good', 'working', 'intact', 'excellent', 'present']:
                completed += 1
            elif field_value in ['none', 'good', 'working', 'intact', 'excellent', 'present']:
                completed += 1  # These are valid assessments too
        
        if completed == total:
            return f'{completed}/{total} ✓'
        else:
            return f'{completed}/{total} ⚠️'
    
    def get_section_severity(self, section_obj, section_type):
        """Determine overall severity for a section"""
        if not section_obj:
            return 'Unknown'
        
        severity_levels = {
            'none': 0, 'light': 1, 'moderate': 2, 'severe': 3, 'destroyed': 4,
            'excellent': 0, 'good': 0, 'fair': 1, 'poor': 2, 'failed': 3,
            'working': 0, 'intermittent': 1, 'not_working': 2, 'not_tested': 1,
            'fault': 2, 'deployed': 3,
            'intact': 0, 'minor_damage': 1, 'moderate_damage': 2, 'severe_damage': 3, 'compromised': 4,
            'low': 1, 'contaminated': 2, 'leaking': 2, 'empty': 1,
            'present': 0, 'damaged': 2, 'missing': 3, 'tampered': 3
        }
        
        max_severity = 0
        
        for field in section_obj._meta.fields:
            if field.name.endswith('_notes') or field.name in ['assessment', 'id']:
                continue
            
            field_value = getattr(section_obj, field.name, None)
            if field_value in severity_levels:
                max_severity = max(max_severity, severity_levels[field_value])
        
        severity_map = {0: 'None', 1: 'Minor', 2: 'Moderate', 3: 'Major', 4: 'Severe'}
        return severity_map.get(max_severity, 'Unknown')
    
    def get_component_count(self, section_type):
        """Get total number of components for each section type"""
        component_counts = {
            'exterior': 38,
            'wheels': 12,
            'interior': 19,
            'mechanical': 20,
            'electrical': 9,
            'safety': 6,
            'structural': 6,
            'fluids': 6
        }
        return component_counts.get(section_type, 0)
    
    def get_section_damage_details(self, section_obj, section_type):
        """Get detailed damage information for a section"""
        if not section_obj:
            return {
                'damaged_components': 0,
                'total_components': self.get_component_count(section_type),
                'damage_percentage': 0,
                'critical_damage': False,
                'repair_priority': 'Low'
            }
        
        damaged_components = 0
        critical_damage = False
        total_components = 0
        
        # Define critical damage indicators
        critical_indicators = ['severe', 'destroyed', 'failed', 'compromised', 'deployed']
        
        for field in section_obj._meta.fields:
            if field.name.endswith('_notes') or field.name in ['assessment', 'id']:
                continue
            
            total_components += 1
            field_value = getattr(section_obj, field.name, None)
            
            if field_value and field_value not in ['none', 'good', 'working', 'intact', 'excellent', 'present']:
                damaged_components += 1
                
                if field_value in critical_indicators:
                    critical_damage = True
        
        damage_percentage = (damaged_components / total_components * 100) if total_components > 0 else 0
        
        # Determine repair priority
        if critical_damage or damage_percentage > 50:
            repair_priority = 'Critical'
        elif damage_percentage > 25:
            repair_priority = 'High'
        elif damage_percentage > 10:
            repair_priority = 'Medium'
        else:
            repair_priority = 'Low'
        
        return {
            'damaged_components': damaged_components,
            'total_components': total_components,
            'damage_percentage': round(damage_percentage, 1),
            'critical_damage': critical_damage,
            'repair_priority': repair_priority
        }
    
    def get_section_repair_timeline(self, section_obj, section_type):
        """Estimate repair timeline for a section"""
        if not section_obj:
            return {'days': 0, 'description': 'No repairs needed'}
        
        # Base repair times by section type (in days)
        base_times = {
            'exterior': 3,
            'wheels': 1,
            'interior': 2,
            'mechanical': 5,
            'electrical': 2,
            'safety': 3,
            'structural': 7,
            'fluids': 1
        }
        
        severity = self.get_section_severity(section_obj, section_type)
        base_time = base_times.get(section_type, 2)
        
        # Adjust time based on severity
        severity_multipliers = {
            'None': 0,
            'Minor': 0.5,
            'Moderate': 1.0,
            'Major': 1.5,
            'Severe': 2.5
        }
        
        multiplier = severity_multipliers.get(severity, 1.0)
        estimated_days = int(base_time * multiplier)
        
        if estimated_days == 0:
            description = 'No repairs needed'
        elif estimated_days <= 1:
            description = 'Same day repair'
        elif estimated_days <= 3:
            description = 'Quick repair'
        elif estimated_days <= 7:
            description = 'Standard repair'
        else:
            description = 'Extended repair time'
        
        return {
            'days': estimated_days,
            'description': description
        }
    
    def calculate_detailed_cost_breakdown(self, assessment):
        """Calculate detailed cost breakdown with labor, parts, and additional costs"""
        section_costs = {}
        total_parts_cost = 0
        
        # Calculate costs for each section
        sections = [
            ('exterior', assessment.exterior_damage),
            ('wheels', assessment.wheels_tires),
            ('interior', assessment.interior_damage),
            ('mechanical', assessment.mechanical_systems),
            ('electrical', assessment.electrical_systems),
            ('safety', assessment.safety_systems),
            ('structural', assessment.frame_structural),
            ('fluids', assessment.fluid_systems)
        ]
        
        for section_type, section_obj in sections:
            if section_obj:
                parts_cost = self.calculate_section_cost(section_obj, section_type)
                # Labor cost is typically 60-80% of parts cost for automotive repairs
                labor_cost = parts_cost * 0.7
                section_total = parts_cost + labor_cost
                
                section_costs[section_type] = {
                    'parts_cost': parts_cost,
                    'labor_cost': labor_cost,
                    'total_cost': section_total,
                    'severity': self.get_section_severity(section_obj, section_type)
                }
                total_parts_cost += section_total
        
        # Additional costs
        paint_materials = total_parts_cost * 0.15  # 15% for paint and materials
        shop_supplies = total_parts_cost * 0.08    # 8% for shop supplies
        
        return {
            'section_costs': section_costs,
            'subtotal': total_parts_cost,
            'paint_materials': paint_materials,
            'shop_supplies': shop_supplies,
            'total_before_tax': total_parts_cost + paint_materials + shop_supplies,
            'vat': (total_parts_cost + paint_materials + shop_supplies) * 0.20,  # 20% VAT
            'grand_total': (total_parts_cost + paint_materials + shop_supplies) * 1.20
        }
    
    def generate_repair_quote_comparisons(self, assessment):
        """Generate repair quote comparisons from multiple sources"""
        base_cost = float(assessment.estimated_repair_cost or 0)
        if base_cost == 0:
            return []
        
        # Generate realistic quote variations
        quotes = [
            {
                'source': 'Assessor Estimate',
                'provider': f'{assessment.assessor_name}',
                'amount': base_cost,
                'type': 'primary',
                'confidence': 'High',
                'notes': 'Professional assessment based on inspection'
            },
            {
                'source': 'Authorized Dealer',
                'provider': f'{assessment.vehicle.make} Main Dealer',
                'amount': base_cost * 1.25,  # Dealers typically 25% higher
                'type': 'dealer',
                'confidence': 'High',
                'notes': 'OEM parts and certified technicians'
            },
            {
                'source': 'Independent Garage',
                'provider': 'Local Certified Garage',
                'amount': base_cost * 0.85,  # Independent shops typically 15% lower
                'type': 'independent',
                'confidence': 'Medium',
                'notes': 'Aftermarket parts, competitive pricing'
            },
            {
                'source': 'Insurance Network',
                'provider': 'Preferred Repair Network',
                'amount': base_cost * 0.92,  # Network shops slightly lower
                'type': 'network',
                'confidence': 'High',
                'notes': 'Pre-negotiated rates, guaranteed work'
            },
            {
                'source': 'Market Average',
                'provider': 'Regional Market Data',
                'amount': base_cost * 1.08,  # Market average slightly higher
                'type': 'market',
                'confidence': 'Medium',
                'notes': 'Based on regional repair cost data'
            }
        ]
        
        return quotes
    
    def calculate_settlement_details(self, assessment):
        """Calculate detailed settlement information with depreciation and deductibles"""
        if not assessment.estimated_repair_cost or not assessment.vehicle_market_value:
            return None
        
        repair_cost = float(assessment.estimated_repair_cost)
        market_value = float(assessment.vehicle_market_value)
        salvage_value = float(assessment.salvage_value or 0)
        
        # Vehicle age-based depreciation calculation
        vehicle_age = timezone.now().year - assessment.vehicle.manufacture_year
        age_depreciation_rate = min(0.15, 0.02 * vehicle_age)  # 2% per year, max 15%
        
        # Damage-based depreciation
        severity_depreciation = {
            'cosmetic': 0.02,
            'minor': 0.03,
            'moderate': 0.05,
            'major': 0.08,
            'total_loss': 0.15
        }
        damage_depreciation = severity_depreciation.get(assessment.overall_severity, 0.05)
        
        total_depreciation_rate = age_depreciation_rate + damage_depreciation
        depreciation_amount = market_value * total_depreciation_rate
        
        # Policy deductible - get from actual policy
        deductible = getattr(assessment.vehicle.policy, 'deductible', 500) if hasattr(assessment.vehicle, 'policy') else 500
        
        # Total loss threshold (typically 70-75% of market value)
        total_loss_threshold = market_value * 0.70
        is_total_loss = repair_cost > total_loss_threshold
        
        if is_total_loss:
            # Total loss settlement
            settlement_amount = market_value - depreciation_amount - deductible
            if salvage_value > 0:
                settlement_amount += salvage_value
        else:
            # Repair settlement
            settlement_amount = repair_cost - deductible
        
        return {
            'repair_cost': repair_cost,
            'market_value': market_value,
            'salvage_value': salvage_value,
            'vehicle_age': vehicle_age,
            'age_depreciation_rate': age_depreciation_rate,
            'damage_depreciation_rate': damage_depreciation,
            'total_depreciation_rate': total_depreciation_rate,
            'depreciation_amount': depreciation_amount,
            'deductible': deductible,
            'total_loss_threshold': total_loss_threshold,
            'is_total_loss': is_total_loss,
            'settlement_amount': max(0, settlement_amount),
            'recommendation': 'Total Loss Settlement' if is_total_loss else 'Repair Settlement'
        }


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentReportView(LoginRequiredMixin, DetailView):
    """View for generating and downloading assessment reports"""
    
    def get_object(self):
        from assessments.models import VehicleAssessment
        
        assessment_id = self.kwargs.get('assessment_id')
        
        # Get assessment ensuring user has access
        try:
            if assessment_id.isdigit():
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related(
                        'vehicle', 'user', 'assigned_agent'
                    ).prefetch_related(
                        'exterior_damage', 'wheels_tires', 'interior_damage',
                        'mechanical_systems', 'electrical_systems', 'safety_systems',
                        'frame_structural', 'fluid_systems', 'documentation', 'photos'
                    ),
                    pk=assessment_id,
                    assigned_agent=self.request.user
                )
            else:
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related(
                        'vehicle', 'user', 'assigned_agent'
                    ).prefetch_related(
                        'exterior_damage', 'wheels_tires', 'interior_damage',
                        'mechanical_systems', 'electrical_systems', 'safety_systems',
                        'frame_structural', 'fluid_systems', 'documentation', 'photos'
                    ),
                    assessment_id=assessment_id,
                    assigned_agent=self.request.user
                )
        except VehicleAssessment.DoesNotExist:
            # Return 404 if assessment not found or user doesn't have access
            from django.http import Http404
            raise Http404("Assessment not found or access denied")
        
        return assessment
    
    def get(self, request, *args, **kwargs):
        """Generate and return PDF report"""
        from .report_generator import generate_assessment_report
        
        assessment = self.get_object()
        report_type = request.GET.get('type', 'detailed')
        
        # Validate report type
        if report_type not in ['summary', 'detailed', 'photos_only']:
            report_type = 'detailed'
        
        try:
            # Generate PDF report
            response = generate_assessment_report(assessment, report_type)
            
            # Log report generation
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Generated {report_type} report for assessment {assessment.id} by user {request.user.id}")
            
            return response
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating report for assessment {assessment.id}: {str(e)}")
            
            # Return error response
            messages.error(request, "Error generating report. Please try again.")
            return redirect('insurance_app:assessment_detail', claim_id=assessment.id)


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentReportShareView(LoginRequiredMixin, View):
    """View for sharing assessment reports via email"""
    
    def post(self, request, assessment_id):
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string
        from .report_generator import AssessmentReportGenerator
        from assessments.models import VehicleAssessment
        import tempfile
        import os
        
        try:
            # Get assessment
            if assessment_id.isdigit():
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related('vehicle', 'user', 'assigned_agent'),
                    pk=assessment_id,
                    assigned_agent=request.user
                )
            else:
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related('vehicle', 'user', 'assigned_agent'),
                    assessment_id=assessment_id,
                    assigned_agent=request.user
                )
            
            # Get form data
            recipient_emails = request.POST.get('emails', '').strip()
            report_type = request.POST.get('report_type', 'detailed')
            message = request.POST.get('message', '').strip()
            include_photos = request.POST.get('include_photos') == 'on'
            
            # Validate inputs
            if not recipient_emails:
                return JsonResponse({'success': False, 'error': 'Email addresses are required'})
            
            # Parse and validate email addresses
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            emails = [email.strip() for email in recipient_emails.replace(',', ';').split(';')]
            valid_emails = [email for email in emails if re.match(email_pattern, email)]
            
            if not valid_emails:
                return JsonResponse({'success': False, 'error': 'No valid email addresses provided'})
            
            # Generate PDF report
            generator = AssessmentReportGenerator(assessment)
            
            # Create temporary file for the PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                # Generate PDF content
                pdf_response = generator.generate_report(report_type)
                temp_file.write(pdf_response.content)
                temp_file_path = temp_file.name
            
            try:
                # Prepare email
                subject = f"Vehicle Assessment Report - {assessment.vehicle.manufacture_year} {assessment.vehicle.make} {assessment.vehicle.model}"
                
                # Render email template
                email_context = {
                    'assessment': assessment,
                    'sender_name': request.user.get_full_name() or request.user.username,
                    'message': message,
                    'report_type': report_type.replace('_', ' ').title(),
                }
                
                html_content = render_to_string('emails/assessment_report_share.html', email_context)
                text_content = render_to_string('emails/assessment_report_share.txt', email_context)
                
                # Create email
                email = EmailMessage(
                    subject=subject,
                    body=text_content,
                    from_email=f"{request.user.get_full_name() or request.user.username} <noreply@carfinity.com>",
                    to=valid_emails,
                    reply_to=[request.user.email] if request.user.email else None
                )
                
                # Add HTML version
                email.attach_alternative(html_content, "text/html")
                
                # Attach PDF report
                filename = f"assessment_report_{assessment.id}_{report_type}.pdf"
                with open(temp_file_path, 'rb') as pdf_file:
                    email.attach(filename, pdf_file.read(), 'application/pdf')
                
                # Send email
                email.send()
                
                # Log the sharing activity
                logger = logging.getLogger(__name__)
                logger.info(f"Assessment report {assessment.id} shared by user {request.user.id} to {len(valid_emails)} recipients")
                
                # Create notification record (optional)
                AssessmentNotification.objects.create(
                    assessment=assessment,
                    recipient=request.user,
                    notification_type='report_shared',
                    title='Report Shared',
                    message=f'Assessment report shared with {len(valid_emails)} recipient(s)'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Report successfully shared with {len(valid_emails)} recipient(s)',
                    'recipients': valid_emails
                })
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error sharing assessment report {assessment_id}: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Failed to share report. Please try again.'})


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentHistoryView(LoginRequiredMixin, View):
    """View for comprehensive assessment history and audit trail"""
    
    def get(self, request, assessment_id):
        from assessments.models import VehicleAssessment
        from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
        from django.contrib.contenttypes.models import ContentType
        
        try:
            # Get assessment
            if assessment_id.isdigit():
                assessment = get_object_or_404(VehicleAssessment, pk=assessment_id, assigned_agent=request.user)
            else:
                assessment = get_object_or_404(VehicleAssessment, assessment_id=assessment_id, assigned_agent=request.user)
            
            # Check if this is an AJAX request for JSON response
            if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
                return self._get_json_response(request, assessment)
            
            # Return HTML template response
            return self._get_html_response(request, assessment)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving assessment history for {assessment_id}: {str(e)}")
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f"Error loading assessment history: {str(e)}")
                return redirect('insurance_app:assessment_detail', assessment_id=assessment_id)
    
    def _get_html_response(self, request, assessment):
        """Return HTML template response with history data"""
        
        # Get comprehensive history data
        history_entries = AssessmentHistory.objects.filter(
            assessment=assessment
        ).select_related('user').order_by('-timestamp')[:100]
        
        # Get workflow history
        workflow_history = AssessmentWorkflow.objects.filter(
            assessment=assessment
        ).select_related('completed_by').order_by('-started_at')
        
        # Get comments
        comments = AssessmentComment.objects.filter(
            assessment=assessment
        ).select_related('user').order_by('-created_at')
        
        # Get versions for comparison
        versions = AssessmentVersion.objects.filter(
            assessment=assessment
        ).select_related('created_by').order_by('-version_number')[:10]
        
        # Get activity summary
        activity_summary = self._get_activity_summary(assessment)
        
        context = {
            'assessment': assessment,
            'history_entries': history_entries,
            'workflow_history': workflow_history,
            'comments': comments,
            'versions': versions,
            'activity_summary': activity_summary,
            'can_rollback': request.user.has_perm('insurance_app.change_assessmentversion'),
        }
        
        return render(request, 'dashboard/assessment_history.html', context)
    
    def _get_json_response(self, request, assessment):
        """Return JSON response for AJAX requests"""
        
        history_data = []
        
        # 1. Get comprehensive history from AssessmentHistory model
        history_entries = AssessmentHistory.objects.filter(
            assessment=assessment
        ).select_related('user').order_by('-timestamp')[:50]
        
        for entry in history_entries:
            history_data.append({
                'type': 'history',
                'action': entry.activity_type,
                'title': self._get_activity_title(entry),
                'description': entry.description,
                'user': entry.user.get_full_name() or entry.user.username,
                'user_id': entry.user.id,
                'timestamp': entry.timestamp,
                'timestamp_str': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_relative': timesince(entry.timestamp),
                'field_name': entry.field_name,
                'old_value': entry.old_value,
                'new_value': entry.new_value,
                'notes': entry.notes,
                'icon': self._get_activity_icon(entry.activity_type),
                'color': self._get_activity_color(entry.activity_type),
                'related_section': entry.related_section,
            })
        
        # 2. Get workflow history
        workflow_history = AssessmentWorkflow.objects.filter(
            assessment=assessment
        ).select_related('completed_by').order_by('-started_at')
        
        for entry in workflow_history:
            history_data.append({
                'type': 'workflow',
                'action': entry.step,
                'title': f"Workflow: {entry.get_step_display()}",
                'description': entry.notes,
                'user': entry.completed_by.get_full_name() or entry.completed_by.username,
                'user_id': entry.completed_by.id,
                'timestamp': entry.completed_at or entry.started_at,
                'timestamp_str': (entry.completed_at or entry.started_at).strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_relative': timesince(entry.completed_at or entry.started_at),
                'status': entry.status,
                'duration_minutes': entry.duration_minutes,
                'icon': self._get_workflow_icon(entry.step),
                'color': self._get_workflow_color(entry.step)
            })
        
        # 3. Get assessment comments
        comments = AssessmentComment.objects.filter(
            assessment=assessment
        ).select_related('user').order_by('-created_at')
        
        for comment in comments:
            history_data.append({
                'type': 'comment',
                'action': 'comment_added',
                'title': f"Comment: {comment.get_comment_type_display()}",
                'description': comment.content[:200] + ('...' if len(comment.content) > 200 else ''),
                'user': comment.user.get_full_name() or comment.user.username,
                'user_id': comment.user.id,
                'timestamp': comment.created_at,
                'timestamp_str': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_relative': timesince(comment.created_at),
                'status': 'resolved' if comment.is_resolved else 'active',
                'icon': 'fas fa-comment',
                'color': 'blue',
                'comment_type': comment.comment_type,
                'related_section': comment.related_section,
            })
        
        # 4. Get notifications
        notifications = AssessmentNotification.objects.filter(
            assessment=assessment
        ).select_related('recipient').order_by('-created_at')[:20]
        
        for notification in notifications:
            history_data.append({
                'type': 'notification',
                'action': notification.notification_type,
                'title': notification.title,
                'description': notification.message,
                'user': notification.recipient.get_full_name() or notification.recipient.username,
                'user_id': notification.recipient.id,
                'timestamp': notification.created_at,
                'timestamp_str': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_relative': timesince(notification.created_at),
                'status': notification.status,
                'icon': self._get_notification_icon(notification.notification_type),
                'color': self._get_notification_color(notification.notification_type)
            })
        
        # 5. Sort all history by timestamp (newest first)
        history_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 6. Limit to last 100 entries
        history_data = history_data[:100]
        
        # 7. Convert timestamps to strings for JSON serialization
        for entry in history_data:
            entry['timestamp'] = entry['timestamp_str']
        
        return JsonResponse({
            'success': True,
            'history': history_data,
            'total_entries': len(history_data),
            'assessment_id': assessment.assessment_id,
            'assessment_status': assessment.agent_status,
            'activity_summary': self._get_activity_summary(assessment)
        })
    
    def _get_activity_summary(self, assessment):
        """Get summary of assessment activities"""
        from django.db.models import Count
        
        # Count activities by type
        activity_counts = AssessmentHistory.objects.filter(
            assessment=assessment
        ).values('activity_type').annotate(count=Count('id'))
        
        # Count workflow steps
        workflow_counts = AssessmentWorkflow.objects.filter(
            assessment=assessment
        ).values('step').annotate(count=Count('id'))
        
        # Count comments
        comment_count = AssessmentComment.objects.filter(
            assessment=assessment
        ).count()
        
        # Get recent activity (last 7 days)
        recent_cutoff = timezone.now() - timedelta(days=7)
        recent_activity_count = AssessmentHistory.objects.filter(
            assessment=assessment,
            timestamp__gte=recent_cutoff
        ).count()
        
        return {
            'total_activities': AssessmentHistory.objects.filter(assessment=assessment).count(),
            'total_workflow_steps': AssessmentWorkflow.objects.filter(assessment=assessment).count(),
            'total_comments': comment_count,
            'recent_activity_count': recent_activity_count,
            'activity_by_type': {item['activity_type']: item['count'] for item in activity_counts},
            'workflow_by_step': {item['step']: item['count'] for item in workflow_counts},
        }
    
    def _get_activity_title(self, entry):
        """Get human-readable title for activity"""
        titles = {
            'status_change': f"Status changed from {entry.old_value} to {entry.new_value}",
            'cost_adjustment': f"Cost adjusted: {entry.field_name}",
            'document_update': f"Document updated: {entry.field_name}",
            'agent_assignment': f"Agent assigned: {entry.new_value}",
            'comment_added': "Comment added",
            'photo_uploaded': "Photo uploaded",
            'photo_deleted': "Photo deleted",
            'section_updated': f"Section updated: {entry.related_section}",
            'workflow_action': f"Workflow action: {entry.description}",
            'report_generated': "Report generated",
            'approval_granted': "Assessment approved",
            'rejection_issued': "Assessment rejected",
            'changes_requested': "Changes requested",
        }
        return titles.get(entry.activity_type, entry.description)
    
    def _get_activity_icon(self, activity_type):
        """Get icon for activity type"""
        icons = {
            'status_change': 'fas fa-exchange-alt',
            'cost_adjustment': 'fas fa-dollar-sign',
            'document_update': 'fas fa-file-alt',
            'agent_assignment': 'fas fa-user-plus',
            'comment_added': 'fas fa-comment',
            'photo_uploaded': 'fas fa-camera',
            'photo_deleted': 'fas fa-trash',
            'section_updated': 'fas fa-edit',
            'workflow_action': 'fas fa-cogs',
            'report_generated': 'fas fa-file-pdf',
            'approval_granted': 'fas fa-check-circle',
            'rejection_issued': 'fas fa-times-circle',
            'changes_requested': 'fas fa-exclamation-triangle',
        }
        return icons.get(activity_type, 'fas fa-circle')
    
    def _get_activity_color(self, activity_type):
        """Get color for activity type"""
        colors = {
            'status_change': 'blue',
            'cost_adjustment': 'green',
            'document_update': 'purple',
            'agent_assignment': 'indigo',
            'comment_added': 'blue',
            'photo_uploaded': 'teal',
            'photo_deleted': 'red',
            'section_updated': 'yellow',
            'workflow_action': 'gray',
            'report_generated': 'orange',
            'approval_granted': 'green',
            'rejection_issued': 'red',
            'changes_requested': 'orange',
        }
        return colors.get(activity_type, 'gray')


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentVersionCompareView(LoginRequiredMixin, View):
    """View for comparing different versions of assessment data"""
    
    def get(self, request, assessment_id):
        from assessments.models import VehicleAssessment
        import json
        
        try:
            # Get assessment
            if assessment_id.isdigit():
                assessment = get_object_or_404(VehicleAssessment, pk=assessment_id, assigned_agent=request.user)
            else:
                assessment = get_object_or_404(VehicleAssessment, assessment_id=assessment_id, assigned_agent=request.user)
            
            version_a_id = request.GET.get('version_a')
            version_b_id = request.GET.get('version_b')
            
            if not version_a_id or not version_b_id:
                return JsonResponse({'success': False, 'error': 'Both version IDs are required'})
            
            # Get versions
            version_a = get_object_or_404(AssessmentVersion, id=version_a_id, assessment=assessment)
            version_b = get_object_or_404(AssessmentVersion, id=version_b_id, assessment=assessment)
            
            # Compare the data
            comparison = self._compare_versions(version_a, version_b)
            
            # Generate HTML for comparison
            comparison_html = self._generate_comparison_html(version_a, version_b, comparison)
            
            return JsonResponse({
                'success': True,
                'comparison_html': comparison_html,
                'version_a': {
                    'number': version_a.version_number,
                    'created_at': version_a.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_by': version_a.created_by.get_full_name() or version_a.created_by.username,
                },
                'version_b': {
                    'number': version_b.version_number,
                    'created_at': version_b.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_by': version_b.created_by.get_full_name() or version_b.created_by.username,
                }
            })
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error comparing assessment versions: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    def _compare_versions(self, version_a, version_b):
        """Compare two assessment versions and return differences"""
        import json
        from deepdiff import DeepDiff
        
        try:
            data_a = version_a.assessment_data
            data_b = version_b.assessment_data
            
            # Use deepdiff to find differences
            diff = DeepDiff(data_a, data_b, ignore_order=True)
            
            changes = []
            
            # Process value changes
            if 'values_changed' in diff:
                for path, change in diff['values_changed'].items():
                    field_name = path.replace("root['", "").replace("']", "").replace("']['", ".")
                    changes.append({
                        'type': 'changed',
                        'field': field_name,
                        'old_value': change['old_value'],
                        'new_value': change['new_value']
                    })
            
            # Process added items
            if 'dictionary_item_added' in diff:
                for path in diff['dictionary_item_added']:
                    field_name = path.replace("root['", "").replace("']", "").replace("']['", ".")
                    changes.append({
                        'type': 'added',
                        'field': field_name,
                        'new_value': data_b.get(field_name.split('.')[0], {}).get(field_name.split('.')[-1], 'N/A')
                    })
            
            # Process removed items
            if 'dictionary_item_removed' in diff:
                for path in diff['dictionary_item_removed']:
                    field_name = path.replace("root['", "").replace("']", "").replace("']['", ".")
                    changes.append({
                        'type': 'removed',
                        'field': field_name,
                        'old_value': data_a.get(field_name.split('.')[0], {}).get(field_name.split('.')[-1], 'N/A')
                    })
            
            return changes
            
        except Exception as e:
            # Fallback to simple comparison if deepdiff fails
            return self._simple_compare(version_a.assessment_data, version_b.assessment_data)
    
    def _simple_compare(self, data_a, data_b):
        """Simple comparison fallback"""
        changes = []
        
        # Compare top-level fields
        all_keys = set(data_a.keys()) | set(data_b.keys())
        
        for key in all_keys:
            if key not in data_a:
                changes.append({
                    'type': 'added',
                    'field': key,
                    'new_value': data_b[key]
                })
            elif key not in data_b:
                changes.append({
                    'type': 'removed',
                    'field': key,
                    'old_value': data_a[key]
                })
            elif data_a[key] != data_b[key]:
                changes.append({
                    'type': 'changed',
                    'field': key,
                    'old_value': data_a[key],
                    'new_value': data_b[key]
                })
        
        return changes
    
    def _generate_comparison_html(self, version_a, version_b, changes):
        """Generate HTML for version comparison"""
        
        if not changes:
            return '<div class="text-center py-4 text-gray-500">No differences found between these versions.</div>'
        
        html = f'''
        <div class="comparison-header mb-4">
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-red-50 p-3 rounded">
                    <h4 class="font-semibold text-red-800">Version {version_a.version_number}</h4>
                    <p class="text-sm text-red-600">{version_a.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p class="text-sm text-red-600">by {version_a.created_by.get_full_name() or version_a.created_by.username}</p>
                </div>
                <div class="bg-green-50 p-3 rounded">
                    <h4 class="font-semibold text-green-800">Version {version_b.version_number}</h4>
                    <p class="text-sm text-green-600">{version_b.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p class="text-sm text-green-600">by {version_b.created_by.get_full_name() or version_b.created_by.username}</p>
                </div>
            </div>
        </div>
        
        <div class="changes-list">
            <h4 class="font-semibold mb-3">Changes ({len(changes)})</h4>
        '''
        
        for change in changes:
            if change['type'] == 'changed':
                html += f'''
                <div class="change-item mb-3 p-3 border rounded">
                    <div class="font-medium text-gray-900">{change['field']}</div>
                    <div class="grid grid-cols-2 gap-2 mt-2">
                        <div class="bg-red-50 p-2 rounded">
                            <div class="text-xs text-red-600 font-medium">OLD</div>
                            <div class="text-sm text-red-800">{change['old_value']}</div>
                        </div>
                        <div class="bg-green-50 p-2 rounded">
                            <div class="text-xs text-green-600 font-medium">NEW</div>
                            <div class="text-sm text-green-800">{change['new_value']}</div>
                        </div>
                    </div>
                </div>
                '''
            elif change['type'] == 'added':
                html += f'''
                <div class="change-item mb-3 p-3 border rounded bg-green-50">
                    <div class="font-medium text-green-900">
                        <i class="fas fa-plus mr-2"></i>{change['field']} (Added)
                    </div>
                    <div class="text-sm text-green-800 mt-1">{change['new_value']}</div>
                </div>
                '''
            elif change['type'] == 'removed':
                html += f'''
                <div class="change-item mb-3 p-3 border rounded bg-red-50">
                    <div class="font-medium text-red-900">
                        <i class="fas fa-minus mr-2"></i>{change['field']} (Removed)
                    </div>
                    <div class="text-sm text-red-800 mt-1">{change['old_value']}</div>
                </div>
                '''
        
        html += '</div>'
        
        return html


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentRollbackView(LoginRequiredMixin, View):
    """View for rolling back assessment to a previous version"""
    
    def post(self, request, assessment_id):
        from assessments.models import VehicleAssessment
        import json
        
        try:
            # Get assessment
            if assessment_id.isdigit():
                assessment = get_object_or_404(VehicleAssessment, pk=assessment_id, assigned_agent=request.user)
            else:
                assessment = get_object_or_404(VehicleAssessment, assessment_id=assessment_id, assigned_agent=request.user)
            
            # Check permissions
            if not request.user.has_perm('insurance_app.change_assessmentversion'):
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            version_id = request.POST.get('version_id')
            rollback_reason = request.POST.get('reason', '')
            
            if not version_id:
                return JsonResponse({'success': False, 'error': 'Version ID is required'})
            
            # Get the version to rollback to
            target_version = get_object_or_404(AssessmentVersion, id=version_id, assessment=assessment)
            
            # Create a backup of current state before rollback
            current_data = self._serialize_assessment(assessment)
            backup_version = AssessmentVersion.objects.create(
                assessment=assessment,
                version_number=AssessmentVersion.objects.filter(assessment=assessment).count() + 1,
                created_by=request.user,
                assessment_data=current_data,
                change_summary=f"Backup before rollback to v{target_version.version_number}",
                is_major_version=True
            )
            
            # Restore assessment data from target version
            self._restore_assessment_data(assessment, target_version.assessment_data)
            
            # Create history entry
            AssessmentHistory.objects.create(
                assessment=assessment,
                activity_type='workflow_action',
                user=request.user,
                description=f"Assessment rolled back to version {target_version.version_number}",
                notes=rollback_reason,
                old_value=f"v{backup_version.version_number}",
                new_value=f"v{target_version.version_number}",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Assessment successfully rolled back to version {target_version.version_number}',
                'backup_version': backup_version.version_number
            })
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error rolling back assessment: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    def _serialize_assessment(self, assessment):
        """Serialize assessment data for versioning"""
        from django.core import serializers
        
        # Get all related assessment data
        data = {
            'assessment': {
                'assessment_id': assessment.assessment_id,
                'status': assessment.status,
                'agent_status': assessment.agent_status,
                'overall_severity': assessment.overall_severity,
                'estimated_repair_cost': str(assessment.estimated_repair_cost) if assessment.estimated_repair_cost else None,
                'vehicle_market_value': str(assessment.vehicle_market_value) if assessment.vehicle_market_value else None,
                'salvage_value': str(assessment.salvage_value) if assessment.salvage_value else None,
                'overall_notes': assessment.overall_notes,
                'recommendations': assessment.recommendations,
                'agent_notes': assessment.agent_notes,
            }
        }
        
        # Add related section data
        if hasattr(assessment, 'exterior_damage'):
            data['exterior_damage'] = self._serialize_model_instance(assessment.exterior_damage)
        if hasattr(assessment, 'mechanical_systems'):
            data['mechanical_systems'] = self._serialize_model_instance(assessment.mechanical_systems)
        if hasattr(assessment, 'interior_damage'):
            data['interior_damage'] = self._serialize_model_instance(assessment.interior_damage)
        if hasattr(assessment, 'wheels_tires'):
            data['wheels_tires'] = self._serialize_model_instance(assessment.wheels_tires)
        if hasattr(assessment, 'electrical_systems'):
            data['electrical_systems'] = self._serialize_model_instance(assessment.electrical_systems)
        
        return data
    
    def _serialize_model_instance(self, instance):
        """Serialize a model instance to dict"""
        from django.forms.models import model_to_dict
        return model_to_dict(instance)
    
    def _restore_assessment_data(self, assessment, data):
        """Restore assessment data from version"""
        
        # Restore main assessment fields
        if 'assessment' in data:
            assessment_data = data['assessment']
            for field, value in assessment_data.items():
                if hasattr(assessment, field) and value is not None:
                    if field in ['estimated_repair_cost', 'vehicle_market_value', 'salvage_value']:
                        setattr(assessment, field, Decimal(value) if value else None)
                    else:
                        setattr(assessment, field, value)
            assessment.save()
        
        # Restore section data
        for section_name, section_data in data.items():
            if section_name != 'assessment' and hasattr(assessment, section_name):
                section_instance = getattr(assessment, section_name)
                for field, value in section_data.items():
                    if hasattr(section_instance, field):
                        setattr(section_instance, field, value)
                section_instance.save()
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_workflow_icon(self, step):
        """Get icon for workflow step"""
        icons = {
            'submitted': 'fas fa-upload',
            'review_started': 'fas fa-eye',
            'approved': 'fas fa-check-circle',
            'rejected': 'fas fa-times-circle',
            'changes_requested': 'fas fa-edit',
            'on_hold': 'fas fa-pause-circle',
            'completed': 'fas fa-flag-checkered'
        }
        return icons.get(step, 'fas fa-circle')
    
    def _get_workflow_color(self, step):
        """Get color for workflow step"""
        colors = {
            'submitted': 'blue',
            'review_started': 'yellow',
            'approved': 'green',
            'rejected': 'red',
            'changes_requested': 'orange',
            'on_hold': 'gray',
            'completed': 'green'
        }
        return colors.get(step, 'gray')
    
    def _get_notification_icon(self, notification_type):
        """Get icon for notification type"""
        icons = {
            'status_change': 'fas fa-exchange-alt',
            'comment_added': 'fas fa-comment',
            'deadline_reminder': 'fas fa-clock',
            'approval_required': 'fas fa-hand-paper',
            'rejection_notice': 'fas fa-exclamation-triangle',
            'changes_requested': 'fas fa-edit',
            'report_shared': 'fas fa-share'
        }
        return icons.get(notification_type, 'fas fa-bell')
    
    def _get_notification_color(self, notification_type):
        """Get color for notification type"""
        colors = {
            'status_change': 'blue',
            'comment_added': 'green',
            'deadline_reminder': 'yellow',
            'approval_required': 'orange',
            'rejection_notice': 'red',
            'changes_requested': 'orange',
            'report_shared': 'purple'
        }
        return colors.get(notification_type, 'gray')


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentReportHistoryView(LoginRequiredMixin, View):
    """View for tracking report generation and sharing history"""
    
    def get(self, request, assessment_id):
        from assessments.models import VehicleAssessment
        
        try:
            # Get assessment
            if assessment_id.isdigit():
                assessment = get_object_or_404(VehicleAssessment, pk=assessment_id, assigned_agent=request.user)
            else:
                assessment = get_object_or_404(VehicleAssessment, assessment_id=assessment_id, assigned_agent=request.user)
            
            # Get report-related notifications
            report_notifications = AssessmentNotification.objects.filter(
                assessment=assessment,
                notification_type__in=['report_generated', 'report_shared']
            ).order_by('-created_at')[:20]
            
            history_data = []
            for notification in report_notifications:
                history_data.append({
                    'type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_at_relative': timesince(notification.created_at)
                })
            
            return JsonResponse({
                'success': True,
                'history': history_data
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


# API ViewSets
class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceScheduleSerializer
    
    def get_queryset(self):
        return MaintenanceSchedule.objects.filter(
            vehicle__policy__policy_holder=self.request.user
        ).select_related('vehicle', 'scheduled_maintenance')
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue maintenance schedules"""
        overdue_schedules = self.get_queryset().filter(
            is_completed=False,
            scheduled_date__lt=timezone.now().date()
        ).order_by('scheduled_date')
        
        serializer = self.get_serializer(overdue_schedules, many=True)
        return Response({
            'overdue_schedules': serializer.data,
            'count': overdue_schedules.count()
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming maintenance schedules"""
        days_ahead = int(request.query_params.get('days', 30))
        end_date = timezone.now().date() + timedelta(days=days_ahead)
        
        upcoming_schedules = self.get_queryset().filter(
            is_completed=False,
            scheduled_date__gte=timezone.now().date(),
            scheduled_date__lte=end_date
        ).order_by('scheduled_date')
        
        serializer = self.get_serializer(upcoming_schedules, many=True)
        return Response({
            'upcoming_schedules': serializer.data,
            'count': upcoming_schedules.count(),
            'days_ahead': days_ahead
        })
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark maintenance schedule as completed"""
        schedule = self.get_object()
        completed_date = request.data.get('completed_date', timezone.now().date())
        cost = request.data.get('cost')
        service_provider = request.data.get('service_provider', '')
        
        schedule.is_completed = True
        schedule.completed_date = completed_date
        if cost:
            schedule.cost = cost
        if service_provider:
            schedule.service_provider = service_provider
        schedule.save()
        
        # Update compliance for the vehicle
        if hasattr(schedule.vehicle, 'compliance'):
            schedule.vehicle.compliance.calculate_compliance()
        
        return Response({'status': 'Maintenance marked as completed'})
    
    @action(detail=False, methods=['post'])
    def sync_with_maintenance_app(self, request):
        """Sync all schedules with maintenance app"""
        schedules = self.get_queryset()
        synced_count = 0
        
        for schedule in schedules:
            if schedule.scheduled_maintenance:
                schedule.sync_with_maintenance_app()
                synced_count += 1
        
        return Response({
            'status': 'Sync completed',
            'synced_count': synced_count,
            'total_schedules': schedules.count()
        })

class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    
    def get_queryset(self):
        return Vehicle.objects.filter(
            policy__policy_holder=self.request.user
        ).select_related('policy', 'compliance')
    
    @action(detail=True, methods=['get'])
    def risk_assessment(self, request, pk=None):
        vehicle = self.get_object()
        
        # Calculate current risk factors
        compliance = getattr(vehicle, 'compliance', None)
        overdue_maintenance = vehicle.maintenance_schedules.filter(
            is_completed=False,
            scheduled_date__lt=timezone.now().date()
        ).count()
        
        recent_accidents = vehicle.accidents.filter(
            accident_date__gte=timezone.now() - timedelta(days=365)
        ).count()
        
        latest_condition = vehicle.condition_scores.first()
        condition_score = latest_condition.overall_score if latest_condition else 100
        
        # Risk calculation algorithm
        risk_factors = {
            'maintenance_compliance': compliance.overall_compliance_rate if compliance else 100,
            'overdue_maintenance': overdue_maintenance,
            'recent_accidents': recent_accidents,
            'condition_score': condition_score,
            'vehicle_age': timezone.now().year - vehicle.manufacture_year,
            'mileage': vehicle.mileage
        }
        
        # Calculate weighted risk score
        risk_score = self.calculate_risk_score(risk_factors)
        
        return Response({
            'vehicle_id': vehicle.id,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'risk_level': self.get_risk_level(risk_score)
        })
    
    def calculate_risk_score(self, factors):
        # Weighted risk calculation
        compliance_weight = 0.25
        maintenance_weight = 0.20
        accident_weight = 0.25
        condition_weight = 0.20
        age_weight = 0.05
        mileage_weight = 0.05
        
        compliance_risk = (100 - factors['maintenance_compliance']) / 10
        maintenance_risk = min(factors['overdue_maintenance'] * 2, 10)
        accident_risk = min(factors['recent_accidents'] * 3, 10)
        condition_risk = (100 - factors['condition_score']) / 10
        age_risk = min(factors['vehicle_age'] / 2, 10)
        mileage_risk = min(factors['mileage'] / 50000, 10)
        
        total_risk = (
            compliance_risk * compliance_weight +
            maintenance_risk * maintenance_weight +
            accident_risk * accident_weight +
            condition_risk * condition_weight +
            age_risk * age_weight +
            mileage_risk * mileage_weight
        )
        
        return round(min(total_risk, 10), 2)
    
    def get_risk_level(self, score):
        if score <= 2:
            return 'Low'
        elif score <= 5:
            return 'Medium'
        elif score <= 7:
            return 'High'
        else:
            return 'Critical'

class MaintenanceComplianceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MaintenanceComplianceSerializer
    
    def get_queryset(self):
        return MaintenanceCompliance.objects.filter(
            vehicle__policy__policy_holder=self.request.user
        ).select_related('vehicle')
    
    @action(detail=False, methods=['get'])
    def portfolio_compliance(self, request):
        """Get portfolio-wide compliance metrics"""
        vehicles = Vehicle.objects.filter(
            policy__policy_holder=request.user,
            policy__status='active'
        )
        
        compliance_data = MaintenanceCompliance.objects.filter(
            vehicle__in=vehicles
        ).aggregate(
            avg_overall_compliance=Avg('overall_compliance_rate'),
            avg_critical_compliance=Avg('critical_maintenance_compliance'),
            total_overdue=models.Sum('overdue_count'),
            total_completed_on_time=models.Sum('completed_on_time_count')
        )
        
        # Compliance distribution
        compliance_ranges = [
            ('excellent', 90, 100),
            ('good', 75, 89),
            ('fair', 60, 74),
            ('poor', 0, 59)
        ]
        
        distribution = {}
        for label, min_score, max_score in compliance_ranges:
            count = MaintenanceCompliance.objects.filter(
                vehicle__in=vehicles,
                overall_compliance_rate__gte=min_score,
                overall_compliance_rate__lte=max_score
            ).count()
            distribution[label] = count
        
        return Response({
            'portfolio_metrics': compliance_data,
            'compliance_distribution': distribution,
            'total_vehicles': vehicles.count()
        })

class RiskAlertViewSet(viewsets.ModelViewSet):
    serializer_class = RiskAlertSerializer
    
    def get_queryset(self):
        return RiskAlert.objects.filter(
            vehicle__policy__policy_holder=self.request.user
        ).select_related('vehicle')
    
    @action(detail=True, methods=['post'])
    def resolve_alert(self, request, pk=None):
        alert = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        alert.is_resolved = True
        alert.resolved_date = timezone.now()
        alert.resolution_notes = resolution_notes
        alert.save()
        
        return Response({'status': 'Alert resolved'})
    
    @action(detail=False, methods=['get'])
    def high_risk_vehicles(self, request):
        """Get vehicles with critical or high severity alerts"""
        high_risk_alerts = RiskAlert.objects.filter(
            vehicle__policy__policy_holder=request.user,
            is_resolved=False,
            severity__in=['high', 'critical']
        ).select_related('vehicle')
        
        # Group by vehicle
        vehicles_data = {}
        for alert in high_risk_alerts:
            vehicle_id = alert.vehicle.id
            if vehicle_id not in vehicles_data:
                vehicles_data[vehicle_id] = {
                    'vehicle': VehicleSerializer(alert.vehicle).data,
                    'alerts': []
                }
            vehicles_data[vehicle_id]['alerts'].append(
                RiskAlertSerializer(alert).data
            )
        
        return Response({
            'high_risk_vehicles': list(vehicles_data.values()),
            'total_count': len(vehicles_data)
        })

# API endpoint for metrics calculation
def calculate_portfolio_metrics(request):
    """Calculate and return current portfolio metrics"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    policies = InsurancePolicy.objects.filter(
        policy_holder=request.user,
        status='active'
    )
    
    vehicles = Vehicle.objects.filter(policy__in=policies)
    
    # Calculate metrics
    metrics = {}
    
    # Portfolio Maintenance Compliance
    compliance_data = MaintenanceCompliance.objects.filter(
        vehicle__in=vehicles
    ).aggregate(
        avg_compliance=Avg('overall_compliance_rate'),
        avg_critical_compliance=Avg('critical_maintenance_compliance')
    )
    
    metrics['maintenance_compliance'] = {
        'overall_rate': round(compliance_data['avg_compliance'] or 0, 2),
        'critical_rate': round(compliance_data['avg_critical_compliance'] or 0, 2)
    }
    
    # Vehicle Condition Scoring
    condition_data = vehicles.aggregate(
        avg_health_index=Avg('vehicle_health_index')
    )
    
    condition_distribution = vehicles.values('current_condition').annotate(
        count=Count('id')
    )
    
    metrics['vehicle_condition'] = {
        'avg_health_index': round(condition_data['avg_health_index'] or 0, 2),
        'distribution': {item['current_condition']: item['count'] 
                        for item in condition_distribution}
    }
    
    # Accident Correlation
    total_accidents = Accident.objects.filter(vehicle__in=vehicles).count()
    maintenance_related = Accident.objects.filter(
        vehicle__in=vehicles,
        maintenance_related=True
    ).count()
    
    metrics['accident_correlation'] = {
        'total_accidents': total_accidents,
        'maintenance_related': maintenance_related,
        'correlation_rate': round(
            (maintenance_related / total_accidents * 100) if total_accidents > 0 else 0, 2
        )
    }
    
    # High-Risk Vehicle Identification
    high_risk_count = vehicles.filter(risk_score__gte=7).count()
    active_alerts = RiskAlert.objects.filter(
        vehicle__in=vehicles,
        is_resolved=False
    ).count()
    
    metrics['risk_identification'] = {
        'high_risk_vehicles': high_risk_count,
        'active_alerts': active_alerts,
        'risk_percentage': round(
            (high_risk_count / vehicles.count() * 100) if vehicles.count() > 0 else 0, 2
        )
    }
    
    return JsonResponse({
        'metrics': metrics,
        'calculation_timestamp': timezone.now().isoformat(),
        'total_vehicles': vehicles.count()
    })

def get_comprehensive_accident_data(request, vehicle_id):
    """Get comprehensive accident data combining insurance and vehicle history"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        vehicle = Vehicle.objects.get(
            id=vehicle_id,
            policy__policy_holder=request.user
        )
        
        from .utils import AccidentHistorySyncManager
        comprehensive_data = AccidentHistorySyncManager.get_comprehensive_accident_data(vehicle)
        
        # Convert datetime objects to strings for JSON serialization
        for data in comprehensive_data:
            if hasattr(data['date'], 'isoformat'):
                data['date'] = data['date'].isoformat()
            if data.get('detailed_info') and data['detailed_info'].get('reported_by'):
                data['detailed_info']['reported_by'] = str(data['detailed_info']['reported_by'])
            if data.get('detailed_info') and data['detailed_info'].get('verified_by'):
                data['detailed_info']['verified_by'] = str(data['detailed_info']['verified_by'])
        
        return JsonResponse({
            'vehicle_id': vehicle_id,
            'accidents': comprehensive_data,
            'total_accidents': len(comprehensive_data),
            'insurance_accidents': len([d for d in comprehensive_data if d['type'] == 'insurance_accident']),
            'history_only_accidents': len([d for d in comprehensive_data if d['type'] == 'vehicle_history'])
        })
        
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Comment and Feedback System Views

@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentCommentCreateView(LoginRequiredMixin, CreateView):
    """View for creating new assessment comments"""
    model = AssessmentComment
    form_class = AssessmentCommentForm
    template_name = 'dashboard/assessment_comment_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from assessments.models import VehicleAssessment
        
        assessment_id = self.kwargs.get('assessment_id')
        assessment = get_object_or_404(
            VehicleAssessment,
            pk=assessment_id,
            assigned_agent=self.request.user
        )
        context['assessment'] = assessment
        return context
    
    def form_valid(self, form):
        from assessments.models import VehicleAssessment
        
        assessment_id = self.kwargs.get('assessment_id')
        assessment = get_object_or_404(
            VehicleAssessment,
            pk=assessment_id,
            assigned_agent=self.request.user
        )
        
        comment = form.save(commit=False)
        comment.assessment = assessment
        comment.author = self.request.user
        comment.save()
        
        # Create notification for the assessor
        self.create_comment_notification(comment)
        
        messages.success(self.request, 'Comment added successfully!')
        return redirect('insurance:assessment_detail', claim_id=assessment_id)
    
    def create_comment_notification(self, comment):
        """Create notification for new comment"""
        # Notify the original assessor (vehicle owner)
        if comment.assessment.user != comment.author:
            AssessmentNotification.objects.create(
                assessment=comment.assessment,
                recipient=comment.assessment.user,
                notification_type='comment_added',
                title=f'New comment on assessment {comment.assessment.assessment_id}',
                message=f'{comment.author.get_full_name() or comment.author.username} added a comment: "{comment.content[:100]}..."',
                related_comment=comment
            )


@login_required
@require_POST
@require_group('AutoAssess')
def add_comment_reply(request, assessment_id, parent_comment_id):
    """Add a new comment in response to an existing comment"""
    from assessments.models import VehicleAssessment
    
    assessment = get_object_or_404(
        VehicleAssessment,
        pk=assessment_id,
        assigned_agent=request.user
    )
    
    parent_comment = get_object_or_404(
        AssessmentComment,
        pk=parent_comment_id,
        assessment=assessment
    )
    
    form = CommentReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.assessment = assessment
        reply.author = request.user
        reply.comment_type = 'internal'  # Default to internal for replies
        reply.subject = f"Re: {parent_comment.subject or 'Comment'}"
        reply.save()
        
        # Create notification for the parent comment author
        if parent_comment.author != request.user:
            AssessmentNotification.objects.create(
                assessment=assessment,
                recipient=parent_comment.author,
                notification_type='comment_added',
                title=f'Reply to your comment on assessment {assessment.assessment_id}',
                message=f'{request.user.get_full_name() or request.user.username} replied: "{reply.content[:100]}..."',
                related_comment=reply
            )
        
        messages.success(request, 'Reply added successfully!')
    else:
        messages.error(request, 'Error adding reply. Please check your input.')
    
    return redirect('insurance:assessment_detail', claim_id=assessment_id)


@login_required
@require_POST
@require_group('AutoAssess')
def resolve_comment(request, assessment_id, comment_id):
    """Mark a comment as resolved (no action required)"""
    from assessments.models import VehicleAssessment
    
    assessment = get_object_or_404(
        VehicleAssessment,
        pk=assessment_id,
        assigned_agent=request.user
    )
    
    comment = get_object_or_404(
        AssessmentComment,
        pk=comment_id,
        assessment=assessment
    )
    
    if comment.requires_action:
        comment.requires_action = False
        comment.save()
        
        # Create notification for the comment author
        if comment.author != request.user:
            AssessmentNotification.objects.create(
                assessment=assessment,
                recipient=comment.author,
                notification_type='status_change',
                title=f'Your comment has been resolved',
                message=f'Your comment on assessment {assessment.assessment_id} has been marked as resolved by {request.user.get_full_name() or request.user.username}.',
                related_comment=comment
            )
        
        messages.success(request, 'Comment marked as resolved!')
    else:
        messages.info(request, 'Comment does not require action.')
    
    return redirect('insurance:assessment_detail', claim_id=assessment_id)


@login_required
@require_group('AutoAssess')
def assessment_comments_api(request, assessment_id):
    """API endpoint to get assessment comments"""
    from assessments.models import VehicleAssessment
    
    assessment = get_object_or_404(
        VehicleAssessment,
        pk=assessment_id,
        assigned_agent=request.user
    )
    
    # Get all comments for this assessment
    comments = AssessmentComment.objects.filter(
        assessment=assessment
    ).select_related('author').order_by('-created_at')
    
    # Convert comments to list format
    comment_list = []
    for comment in comments:
        comment_list.append({
            'id': comment.id,
            'subject': comment.subject,
            'content': comment.content,
            'comment_type': comment.get_comment_type_display(),
            'author': comment.author.get_full_name() or comment.author.username,
            'created_at': comment.created_at.isoformat(),
            'is_important': comment.is_important,
            'requires_action': comment.requires_action,
            'is_customer_visible': comment.is_customer_visible,
        })
    
    return JsonResponse({
        'assessment_id': assessment_id,
        'comments': comment_list,
        'total_comments': comments.count()
    })


@login_required
@require_group('AutoAssess')
def user_notifications(request):
    """Get user's assessment notifications"""
    notifications = AssessmentNotification.objects.filter(
        recipient=request.user
    ).select_related('assessment', 'related_comment').order_by('-created_at')[:20]
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.get_notification_type_display(),
            'status': notification.get_status_display(),
            'created_at': notification.created_at.isoformat(),
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'assessment_id': notification.assessment.id,
            'assessment_number': notification.assessment.assessment_id,
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'unread_count': notifications.filter(status='unread').count()
    })


@login_required
@require_POST
@require_group('AutoAssess')
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(
        AssessmentNotification,
        pk=notification_id,
        recipient=request.user
    )
    
    notification.mark_as_read()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Notification marked as read'
    })


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentWorkflowActionView(LoginRequiredMixin, View):
    """Handle workflow actions for assessments (approve, reject, request changes)"""
    
    def post(self, request, assessment_id):
        try:
            assessment = get_object_or_404(VehicleAssessment, assessment_id=assessment_id)
            action = request.POST.get('action')
            notes = request.POST.get('notes', '')
            
            # Verify user has permission to perform workflow actions
            if not request.user.groups.filter(name='AutoAssess').exists():
                return JsonResponse({'success': False, 'error': 'Insufficient permissions'})
            
            old_status = assessment.agent_status
            
            if action == 'approve':
                assessment.agent_status = 'approved'
                assessment.agent_notes = notes
                assessment.completed_date = timezone.now()
                
                # Create workflow history entry
                AssessmentWorkflow.objects.create(
                    assessment=assessment,
                    step='approved',
                    status='completed',
                    notes=f'Assessment approved by {request.user.get_full_name() or request.user.username}. Notes: {notes}',
                    completed_by=request.user
                )
                
                message = 'Assessment approved successfully'
                
            elif action == 'reject':
                assessment.agent_status = 'rejected'
                assessment.agent_notes = notes
                
                # Create workflow history entry
                AssessmentWorkflow.objects.create(
                    assessment=assessment,
                    step='rejected',
                    status='completed',
                    notes=f'Assessment rejected by {request.user.get_full_name() or request.user.username}. Reason: {notes}',
                    completed_by=request.user
                )
                
                message = 'Assessment rejected'
                
            elif action == 'request_changes':
                assessment.agent_status = 'changes_requested'
                assessment.agent_notes = notes
                
                # Create workflow history entry
                AssessmentWorkflow.objects.create(
                    assessment=assessment,
                    step='changes_requested',
                    status='pending',
                    notes=f'Changes requested by {request.user.get_full_name() or request.user.username}. Details: {notes}',
                    completed_by=request.user
                )
                
                message = 'Changes requested'
                
            elif action == 'start_review':
                assessment.agent_status = 'under_review'
                assessment.assigned_agent = request.user
                
                # Create workflow history entry
                AssessmentWorkflow.objects.create(
                    assessment=assessment,
                    step='review_started',
                    status='in_progress',
                    notes=f'Review started by {request.user.get_full_name() or request.user.username}',
                    completed_by=request.user
                )
                
                message = 'Review started'
                
            elif action == 'put_on_hold':
                assessment.agent_status = 'on_hold'
                assessment.agent_notes = notes
                
                # Create workflow history entry
                AssessmentWorkflow.objects.create(
                    assessment=assessment,
                    step='on_hold',
                    status='paused',
                    notes=f'Assessment put on hold by {request.user.get_full_name() or request.user.username}. Reason: {notes}',
                    completed_by=request.user
                )
                
                message = 'Assessment put on hold'
                
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'})
            
            assessment.save()
            
            # Create status change notification
            create_status_change_notification(assessment, old_status, assessment.agent_status, request.user)
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'new_status': assessment.agent_status,
                'status_display': assessment.get_agent_status_display()
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentWorkflowHistoryView(LoginRequiredMixin, View):
    """View workflow history for an assessment"""
    
    def get(self, request, assessment_id):
        try:
            assessment = get_object_or_404(VehicleAssessment, assessment_id=assessment_id)
            
            # Get workflow history
            workflow_history = AssessmentWorkflow.objects.filter(
                assessment=assessment
            ).select_related('completed_by').order_by('-completed_at')
            
            history_data = []
            for entry in workflow_history:
                history_data.append({
                    'step': entry.step,
                    'status': entry.status,
                    'notes': entry.notes,
                    'completed_by': entry.completed_by.get_full_name() or entry.completed_by.username,
                    'completed_at': entry.completed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'completed_at_relative': timesince(entry.completed_at)
                })
            
            return JsonResponse({
                'success': True,
                'history': history_data,
                'current_status': assessment.agent_status,
                'current_status_display': assessment.get_agent_status_display()
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


def create_status_change_notification(assessment, old_status, new_status, changed_by):
    """Utility function to create status change notifications"""
    # Notify the assessor (vehicle owner)
    if assessment.user != changed_by:
        AssessmentNotification.objects.create(
            assessment=assessment,
            recipient=assessment.user,
            notification_type='status_change',
            title=f'Assessment status changed to {new_status}',
            message=f'Your assessment {assessment.assessment_id} status has been changed from {old_status} to {new_status} by {changed_by.get_full_name() or changed_by.username}.'
        )
    
    # Notify other relevant parties (e.g., supervisors, other agents)
    # This can be extended based on business requirements


@require_group('AutoAssess')
@check_permission_conflicts
def insurance_dashboard_view(request):
    """
    Function-based view for insurance dashboard with comprehensive error handling.
    Alternative to the class-based DashboardView for consistency with customer dashboard.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Initialize default values
    policies = []
    total_vehicles = 0
    avg_compliance_rate = 0
    avg_critical_compliance = 0
    avg_health_index = 0
    condition_distribution = []
    active_alerts = []
    recent_accidents = []
    high_risk_vehicles = 0
    high_risk_vehicles_list = []
    
    # Error handling context
    error_context = {
        'has_errors': False,
        'error_messages': [],
        'warning_messages': []
    }
    
    try:
        # Get user's insurance policies
        policies = InsurancePolicy.objects.filter(
            policy_holder=request.user,
            status='active'
        ).prefetch_related('vehicles')
        
        if not policies.exists():
            error_context['warning_messages'].append("No active insurance policies found.")
        
        # Get all vehicles for user's policies
        vehicles = Vehicle.objects.filter(
            policy__policy_holder=request.user,
            policy__status='active'
        )
        
        if not vehicles.exists():
            error_context['warning_messages'].append("No vehicles found in your active insurance policies.")
        else:
            total_vehicles = vehicles.count()
            
            # Portfolio Maintenance Compliance
            try:
                compliance_data = MaintenanceCompliance.objects.filter(
                    vehicle__in=vehicles
                ).aggregate(
                    avg_compliance=Avg('overall_compliance_rate'),
                    avg_critical_compliance=Avg('critical_maintenance_compliance')
                )
                avg_compliance_rate = compliance_data['avg_compliance'] or 0
                avg_critical_compliance = compliance_data['avg_critical_compliance'] or 0
            except Exception as e:
                logger.warning(f"Error calculating compliance data for user {request.user.id}: {str(e)}")
                error_context['warning_messages'].append("Unable to calculate compliance metrics.")
            
            # Vehicle Condition Distribution
            try:
                condition_distribution = list(vehicles.values('current_condition').annotate(count=Count('id')))
            except Exception as e:
                logger.warning(f"Error getting condition distribution for user {request.user.id}: {str(e)}")
                error_context['warning_messages'].append("Unable to load vehicle condition data.")
            
            # Risk Alerts
            try:
                active_alerts = RiskAlert.objects.filter(
                    vehicle__in=vehicles,
                    is_resolved=False
                ).order_by('-severity', '-created_at')[:10]
            except Exception as e:
                logger.warning(f"Error getting risk alerts for user {request.user.id}: {str(e)}")
                error_context['warning_messages'].append("Unable to load risk alerts.")
            
            # Recent Accidents
            try:
                recent_accidents = Accident.objects.filter(
                    vehicle__in=vehicles,
                    accident_date__gte=timezone.now() - timedelta(days=30)
                ).select_related('vehicle')
            except Exception as e:
                logger.warning(f"Error getting recent accidents for user {request.user.id}: {str(e)}")
                error_context['warning_messages'].append("Unable to load recent accident data.")
            
            # High-risk vehicles
            try:
                high_risk_vehicles = vehicles.filter(risk_score__gte=7).count()
                high_risk_vehicles_list = vehicles.filter(risk_score__gte=7).select_related('policy')[:10]
            except Exception as e:
                logger.warning(f"Error getting high-risk vehicles for user {request.user.id}: {str(e)}")
                error_context['warning_messages'].append("Unable to load high-risk vehicle data.")
            
            # Average health index
            try:
                avg_health_index = vehicles.aggregate(avg_health=Avg('vehicle_health_index'))['avg_health'] or 0
            except Exception as e:
                logger.warning(f"Error calculating health index for user {request.user.id}: {str(e)}")
                error_context['warning_messages'].append("Unable to calculate average health index.")
    
    except Exception as e:
        logger.error(f"Error in insurance dashboard for user {request.user.id}: {str(e)}")
        error_context['has_errors'] = True
        error_context['error_messages'].append("Unable to load dashboard data. Please try again later.")
    
    # Add error context to messages
    if error_context['has_errors']:
        for error_msg in error_context['error_messages']:
            messages.error(request, error_msg)
    
    if error_context['warning_messages']:
        for warning_msg in error_context['warning_messages']:
            messages.warning(request, warning_msg)
    
    context = {
        'policies': policies,
        'total_vehicles': total_vehicles,
        'avg_compliance_rate': avg_compliance_rate,
        'avg_critical_compliance': avg_critical_compliance,
        'avg_health_index': avg_health_index,
        'condition_distribution': condition_distribution,
        'active_alerts': active_alerts,
        'recent_accidents': recent_accidents,
        'high_risk_vehicles': high_risk_vehicles,
        'high_risk_vehicles_list': high_risk_vehicles_list,
        'error_context': error_context,
    }
    
    return render(request, 'dashboard/insurance_dashboard.html', context)


class AssessmentSectionDetailView(LoginRequiredMixin, TemplateView):
    """
    View for detailed assessment section breakdown
    """
    template_name = 'dashboard/insurance_assessment_section_detail.html'
    
    def get_context_data(self, **kwargs):
        import json
        context = super().get_context_data(**kwargs)
        claim_id = kwargs.get('claim_id')
        section_id = kwargs.get('section_id')
        
        # Get real assessment data from database
        assessment = self.get_assessment(claim_id)
        section_data = self.get_section_data(section_id, assessment)
        
        context.update({
            'claim_id': claim_id,
            'section_id': section_id,
            'assessment': assessment,
            'section_data': json.dumps(section_data),
            'section_data_dict': section_data,  # For template use
        })
        
        return context
    
    def get_assessment(self, claim_id):
        """Get the VehicleAssessment object"""
        from assessments.models import VehicleAssessment
        
        try:
            if claim_id.isdigit():
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related(
                        'vehicle', 'user', 'assigned_agent'
                    ).prefetch_related(
                        'exterior_damage', 'wheels_tires', 'interior_damage',
                        'mechanical_systems', 'electrical_systems', 'safety_systems',
                        'frame_structural', 'fluid_systems', 'documentation', 'photos'
                    ),
                    pk=claim_id,
                    assigned_agent=self.request.user
                )
            else:
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related(
                        'vehicle', 'user', 'assigned_agent'
                    ).prefetch_related(
                        'exterior_damage', 'wheels_tires', 'interior_damage',
                        'mechanical_systems', 'electrical_systems', 'safety_systems',
                        'frame_structural', 'fluid_systems', 'documentation', 'photos'
                    ),
                    assessment_id=claim_id,
                    assigned_agent=self.request.user
                )
        except VehicleAssessment.DoesNotExist:
            # Fallback to any assessment for the agent if specific one not found
            assessment = get_object_or_404(
                VehicleAssessment.objects.select_related(
                    'vehicle', 'user', 'assigned_agent'
                ).prefetch_related(
                    'exterior_damage', 'wheels_tires', 'interior_damage',
                    'mechanical_systems', 'electrical_systems', 'safety_systems',
                    'frame_structural', 'fluid_systems', 'documentation', 'photos'
                ),
                assigned_agent=self.request.user
            )
        
        return assessment
    
    def get_section_data(self, section_id, assessment):
        """
        Get detailed data for a specific assessment section from database
        """
        section_mapping = {
            'exterior': {
                'name': 'EXTERIOR DAMAGE',
                'icon': '🚗',
                'model_attr': 'exterior_damage',
                'fields': [
                    ('front_bumper', 'Front Bumper', 850),
                    ('hood', 'Hood', 1200),
                    ('front_fenders', 'Front Fenders', 650),
                    ('driver_side_door', 'Driver Side Door', 900),
                    ('passenger_side_door', 'Passenger Side Door', 300),
                    ('rear_bumper', 'Rear Bumper', 400),
                    ('trunk_hatch', 'Trunk/Hatch', 600),
                    ('roof_panel', 'Roof Panel', 1500),
                    ('side_mirrors', 'Side Mirrors', 400),
                    ('headlight_housings', 'Headlight Housings', 800),
                    ('taillight_housings', 'Taillight Housings', 300),
                    ('front_grille', 'Front Grille', 250),
                ]
            },
            'wheels': {
                'name': 'WHEELS & TIRES',
                'icon': '🛞',
                'model_attr': 'wheels_tires',
                'fields': [
                    ('front_left_tire', 'Front Left Tire', 150),
                    ('front_right_tire', 'Front Right Tire', 150),
                    ('rear_left_tire', 'Rear Left Tire', 150),
                    ('rear_right_tire', 'Rear Right Tire', 150),
                    ('front_left_wheel', 'Front Left Wheel', 450),
                    ('front_right_wheel', 'Front Right Wheel', 450),
                    ('rear_left_wheel', 'Rear Left Wheel', 450),
                    ('rear_right_wheel', 'Rear Right Wheel', 450),
                    ('spare_tire', 'Spare Tire', 150),
                    ('wheel_lug_nuts', 'Wheel Lug Nuts', 50),
                    ('tire_pressure_sensors', 'Tire Pressure Sensors', 200),
                    ('center_caps', 'Center Caps', 100),
                ]
            },
            'interior': {
                'name': 'INTERIOR DAMAGE',
                'icon': '🪑',
                'model_attr': 'interior_damage',
                'fields': [
                    ('driver_seat', 'Driver Seat', 400),
                    ('passenger_seat', 'Passenger Seat', 400),
                    ('rear_seats', 'Rear Seats', 600),
                    ('dashboard', 'Dashboard', 800),
                    ('steering_wheel', 'Steering Wheel', 300),
                    ('center_console', 'Center Console', 250),
                    ('door_panels', 'Door Panels', 200),
                    ('floor_mats', 'Floor Mats', 100),
                    ('windshield', 'Windshield', 500),
                    ('side_windows_interior', 'Side Windows', 300),
                    ('interior_mirrors', 'Interior Mirrors', 150),
                    ('visors', 'Visors', 100),
                    ('seat_belts', 'Seat Belts', 200),
                    ('headrests', 'Headrests', 150),
                    ('armrests', 'Armrests', 100),
                    ('instrument_cluster', 'Instrument Cluster', 600),
                    ('climate_controls', 'Climate Controls', 400),
                    ('radio_infotainment', 'Radio/Infotainment', 800),
                    ('glove_compartment', 'Glove Compartment', 100),
                ]
            },
            'mechanical': {
                'name': 'MECHANICAL SYSTEMS',
                'icon': '⚙️',
                'model_attr': 'mechanical_systems',
                'fields': [
                    ('engine_block', 'Engine Block', 3000),
                    ('radiator', 'Radiator', 400),
                    ('battery', 'Battery', 150),
                    ('air_filter_housing', 'Air Filter Housing', 100),
                    ('belts_and_hoses', 'Belts and Hoses', 200),
                    ('fluid_reservoirs', 'Fluid Reservoirs', 150),
                    ('wiring_harnesses', 'Wiring Harnesses', 300),
                    ('engine_mounts', 'Engine Mounts', 250),
                    ('shock_absorbers', 'Shock Absorbers', 600),
                    ('struts', 'Struts', 800),
                    ('springs', 'Springs', 400),
                    ('control_arms', 'Control Arms', 500),
                    ('tie_rods', 'Tie Rods', 300),
                    ('steering_rack', 'Steering Rack', 800),
                    ('brake_lines', 'Brake Lines', 200),
                    ('exhaust_manifold', 'Exhaust Manifold', 600),
                    ('catalytic_converter', 'Catalytic Converter', 1200),
                    ('muffler', 'Muffler', 300),
                    ('exhaust_pipes', 'Exhaust Pipes', 200),
                    ('heat_shields', 'Heat Shields', 100),
                ]
            },
            'electrical': {
                'name': 'ELECTRICAL SYSTEMS',
                'icon': '🔌',
                'model_attr': 'electrical_systems',
                'fields': [
                    ('headlight_function', 'Headlight Function', 200),
                    ('taillight_function', 'Taillight Function', 150),
                    ('interior_lighting', 'Interior Lighting', 100),
                    ('warning_lights', 'Warning Lights', 150),
                    ('horn', 'Horn', 50),
                    ('power_windows', 'Power Windows', 300),
                    ('power_locks', 'Power Locks', 200),
                    ('air_conditioning', 'Air Conditioning', 800),
                    ('heating_system', 'Heating System', 400),
                ]
            },
            'safety': {
                'name': 'SAFETY SYSTEMS',
                'icon': '🛡️',
                'model_attr': 'safety_systems',
                'fields': [
                    ('airbag_systems', 'Airbag Systems', 1500),
                    ('abs_system', 'ABS System', 600),
                    ('stability_control', 'Stability Control', 800),
                    ('parking_sensors', 'Parking Sensors', 300),
                    ('backup_camera_system', 'Backup Camera System', 400),
                    ('emergency_brake', 'Emergency Brake', 500),
                ]
            },
            'structural': {
                'name': 'FRAME & STRUCTURAL',
                'icon': '🏗️',
                'model_attr': 'frame_structural',
                'fields': [
                    ('frame_rails', 'Frame Rails', 3000),
                    ('cross_members', 'Cross Members', 1500),
                    ('firewall', 'Firewall', 2000),
                    ('floor_pans', 'Floor Pans', 1000),
                    ('door_jambs', 'Door Jambs', 800),
                    ('trunk_floor', 'Trunk Floor', 600),
                ]
            },
            'fluids': {
                'name': 'FLUID SYSTEMS',
                'icon': '💧',
                'model_attr': 'fluid_systems',
                'fields': [
                    ('engine_oil', 'Engine Oil', 50),
                    ('transmission_fluid', 'Transmission Fluid', 100),
                    ('brake_fluid', 'Brake Fluid', 30),
                    ('coolant', 'Coolant', 80),
                    ('power_steering_fluid', 'Power Steering Fluid', 40),
                    ('windshield_washer_fluid', 'Windshield Washer Fluid', 20),
                ]
            }
        }
        
        if section_id not in section_mapping:
            return {
                'name': 'UNKNOWN SECTION',
                'icon': '❓',
                'status': 'Unknown',
                'damage_level': 'Unknown',
                'estimated_cost': '£0',
                'component_count': 0,
                'completion_percentage': 0,
                'components': [],
                'inspection_points': []
            }
        
        section_config = section_mapping[section_id]
        section_model = getattr(assessment, section_config['model_attr'], None)
        
        components = []
        total_cost = 0
        damaged_count = 0
        
        if section_model:
            for field_name, display_name, base_cost in section_config['fields']:
                field_value = getattr(section_model, field_name, 'none')
                notes_field = f"{field_name}_notes"
                notes = getattr(section_model, notes_field, '')
                
                # Map field values to display status and severity
                status_mapping = {
                    'none': ('Good', 'None', 0),
                    'light': ('Light Damage', 'Minor', 0.3),
                    'moderate': ('Moderate Damage', 'Moderate', 0.6),
                    'severe': ('Severe Damage', 'Major', 1.0),
                    'destroyed': ('Destroyed', 'Severe', 1.2),
                    'excellent': ('Excellent', 'None', 0),
                    'good': ('Good', 'None', 0),
                    'fair': ('Fair', 'Minor', 0.2),
                    'poor': ('Poor', 'Moderate', 0.5),
                    'failed': ('Failed', 'Major', 1.0),
                    'working': ('Working', 'None', 0),
                    'intermittent': ('Intermittent', 'Minor', 0.3),
                    'not_working': ('Not Working', 'Major', 0.8),
                    'not_tested': ('Not Tested', 'Unknown', 0),
                    'fault': ('Fault Detected', 'Moderate', 0.6),
                    'deployed': ('Deployed/Activated', 'Severe', 1.0),
                    'intact': ('Intact', 'None', 0),
                    'minor_damage': ('Minor Damage', 'Minor', 0.3),
                    'moderate_damage': ('Moderate Damage', 'Moderate', 0.6),
                    'severe_damage': ('Severe Damage', 'Major', 1.0),
                    'compromised': ('Structurally Compromised', 'Severe', 1.2),
                    'low': ('Low Level', 'Minor', 0.2),
                    'contaminated': ('Contaminated', 'Moderate', 0.4),
                    'leaking': ('Leaking', 'Major', 0.8),
                    'empty': ('Empty', 'Major', 0.6),
                    'present': ('Present', 'None', 0),
                    'damaged': ('Damaged', 'Moderate', 0.5),
                    'missing': ('Missing', 'Major', 0.8),
                    'tampered': ('Tampered', 'Severe', 1.0),
                }
                
                status, severity, cost_multiplier = status_mapping.get(field_value, ('Unknown', 'Unknown', 0))
                cost = int(base_cost * cost_multiplier) if cost_multiplier > 0 else 0
                total_cost += cost
                
                if severity not in ['None', 'Unknown']:
                    damaged_count += 1
                
                # Generate repair recommendations based on severity
                repair_recommendations = self.get_repair_recommendations(field_name, severity, status)
                
                # Calculate repair timeline
                repair_timeline = self.get_repair_timeline(severity, cost)
                
                # Get photos for this specific inspection point
                photos = self.get_inspection_point_photos(assessment, section_id, field_name)
                
                components.append({
                    'name': display_name,
                    'status': status,
                    'cost': f'£{cost:,}',
                    'severity': severity,
                    'notes': notes,
                    'field_name': field_name,
                    'raw_cost': cost,
                    'repair_recommendations': repair_recommendations,
                    'repair_timeline': repair_timeline,
                    'parts_cost': int(cost * 0.6) if cost > 0 else 0,
                    'labor_cost': int(cost * 0.4) if cost > 0 else 0,
                    'photos': photos,
                    'photo_count': len(photos),
                })
        
        # Calculate overall section metrics
        total_components = len(section_config['fields'])
        completion_percentage = 100 if section_model else 0
        
        # Determine overall damage level
        if damaged_count == 0:
            damage_level = 'None'
        elif damaged_count <= total_components * 0.2:
            damage_level = 'Minor'
        elif damaged_count <= total_components * 0.5:
            damage_level = 'Moderate'
        elif damaged_count <= total_components * 0.8:
            damage_level = 'Major'
        else:
            damage_level = 'Severe'
        
        status = 'Complete' if section_model else 'Pending'
        
        return {
            'name': section_config['name'],
            'icon': section_config['icon'],
            'status': status,
            'damage_level': damage_level,
            'estimated_cost': f'£{total_cost:,}',
            'component_count': total_components,
            'completion_percentage': completion_percentage,
            'components': components,
            'inspection_points': components,  # Alias for template compatibility
            'damaged_components': damaged_count,
            'total_cost': total_cost
        }
    
    def get_repair_recommendations(self, field_name, severity, status):
        """Generate repair recommendations based on component and severity"""
        recommendations = []
        
        if severity == 'Minor':
            recommendations = [
                "Minor repair or touch-up required",
                "Can be addressed during routine maintenance",
                "Monitor for further deterioration"
            ]
        elif severity == 'Moderate':
            recommendations = [
                "Professional repair recommended",
                "Should be addressed within 30 days",
                "May affect vehicle performance if ignored"
            ]
        elif severity == 'Major':
            recommendations = [
                "Immediate professional repair required",
                "May affect vehicle safety or performance",
                "Obtain multiple repair quotes"
            ]
        elif severity == 'Severe':
            recommendations = [
                "Component replacement required",
                "Urgent repair needed for safety",
                "Vehicle may be unsafe to drive"
            ]
        else:
            recommendations = ["No action required at this time"]
        
        # Add component-specific recommendations
        component_specific = {
            'airbag_systems': ["Replace all deployed airbags", "Reset airbag control module", "Inspect seat belt pretensioners"],
            'engine_block': ["Pressure test cooling system", "Check for internal damage", "Consider engine rebuild if severe"],
            'frame_rails': ["Professional frame alignment required", "Structural integrity assessment needed", "May require specialized repair facility"],
            'brake_lines': ["Immediate brake system inspection", "Replace all affected brake lines", "Bleed brake system after repair"],
        }
        
        if field_name in component_specific and severity not in ['None', 'Unknown']:
            recommendations.extend(component_specific[field_name])
        
        return recommendations
    
    def get_repair_timeline(self, severity, cost):
        """Estimate repair timeline based on severity and cost"""
        if severity == 'None' or severity == 'Unknown':
            return {'days': 0, 'description': 'No repair needed'}
        elif severity == 'Minor':
            return {'days': 1, 'description': '1 day - Quick repair'}
        elif severity == 'Moderate':
            return {'days': 3, 'description': '2-3 days - Standard repair'}
        elif severity == 'Major':
            if cost > 2000:
                return {'days': 7, 'description': '5-7 days - Complex repair'}
            else:
                return {'days': 5, 'description': '3-5 days - Major repair'}
        elif severity == 'Severe':
            if cost > 5000:
                return {'days': 14, 'description': '10-14 days - Extensive work'}
            else:
                return {'days': 10, 'description': '7-10 days - Replacement needed'}
        else:
            return {'days': 0, 'description': 'Timeline to be determined'}
    
    def get_inspection_point_photos(self, assessment, section_id, field_name):
        """Get photos associated with a specific inspection point"""
        from assessments.models import AssessmentPhoto
        
        # Map section_id to section_reference values
        section_mapping = {
            'exterior': 'exterior_damage',
            'wheels': 'wheels_tires',
            'interior': 'interior_damage',
            'mechanical': 'mechanical_systems',
            'electrical': 'electrical_systems',
            'safety': 'safety_systems',
            'structural': 'frame_structural',
            'fluids': 'fluid_systems'
        }
        
        section_reference = section_mapping.get(section_id)
        if not section_reference:
            return []
        
        # Get photos for this specific inspection point
        photos = AssessmentPhoto.objects.filter(
            assessment=assessment,
            section_reference=section_reference,
            damage_point_id=field_name
        ).order_by('-is_primary', 'taken_at')
        
        # If no specific photos found, get general section photos
        if not photos.exists():
            photos = AssessmentPhoto.objects.filter(
                assessment=assessment,
                section_reference=section_reference,
                damage_point_id__isnull=True
            ).order_by('-is_primary', 'taken_at')[:2]  # Limit to 2 general photos
        
        # Convert to list with additional metadata
        photo_list = []
        for photo in photos:
            photo_list.append({
                'id': photo.id,
                'image_url': photo.image.url if photo.image else '',
                'thumbnail_url': photo.image.url if photo.image else '',  # In production, use thumbnail
                'description': photo.description,
                'is_primary': photo.is_primary,
                'taken_at': photo.taken_at,
                'category': photo.get_category_display(),
            })
        
        # Return actual photos only - no demo data
        
        return photo_list
    



# Assessment History and Audit Trail Views

@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentHistoryView(LoginRequiredMixin, DetailView):
    """View for displaying chronological history of assessment activities"""
    
    template_name = 'dashboard/assessment_history.html'
    context_object_name = 'assessment'
    
    def get_object(self):
        from assessments.models import VehicleAssessment
        
        assessment_id = self.kwargs.get('assessment_id')
        
        # Get assessment ensuring user has access
        try:
            if assessment_id.isdigit():
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related('vehicle', 'user', 'assigned_agent'),
                    pk=assessment_id,
                    assigned_agent=self.request.user
                )
            else:
                assessment = get_object_or_404(
                    VehicleAssessment.objects.select_related('vehicle', 'user', 'assigned_agent'),
                    assessment_id=assessment_id,
                    assigned_agent=self.request.user
                )
        except VehicleAssessment.DoesNotExist:
            # Fallback for any assessment the user has access to
            assessment = get_object_or_404(
                VehicleAssessment.objects.select_related('vehicle', 'user', 'assigned_agent'),
                assigned_agent=self.request.user
            )
        
        return assessment
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.object
        
        # Handle JSON format for AJAX requests
        if self.request.GET.get('format') == 'json':
            return self.get_json_response()
        
        # Get history entries with pagination
        offset = int(self.request.GET.get('offset', 0))
        limit = 100
        
        history_entries = AssessmentHistory.objects.filter(
            assessment=assessment
        ).select_related('user').order_by('-timestamp')[offset:offset + limit]
        
        # Calculate activity summary
        activity_summary = self.calculate_activity_summary(assessment)
        
        # Get assessment versions for comparison
        versions = AssessmentVersion.objects.filter(
            assessment=assessment
        ).select_related('created_by').order_by('-version_number')[:10]
        
        # Check if user can rollback (admin or original assessor)
        can_rollback = (
            self.request.user.is_staff or 
            assessment.user == self.request.user or
            assessment.assigned_agent == self.request.user
        )
        
        context.update({
            'history_entries': history_entries,
            'activity_summary': activity_summary,
            'versions': versions,
            'can_rollback': can_rollback,
        })
        
        return context
    
    def get_json_response(self):
        """Return JSON response for AJAX requests"""
        assessment = self.object
        offset = int(self.request.GET.get('offset', 0))
        limit = 50
        
        history_entries = AssessmentHistory.objects.filter(
            assessment=assessment
        ).select_related('user').order_by('-timestamp')[offset:offset + limit]
        
        history_data = []
        for entry in history_entries:
            history_data.append({
                'action': entry.activity_type,
                'title': self.get_activity_title(entry),
                'description': entry.description,
                'user': entry.user.get_full_name() or entry.user.username,
                'timestamp': entry.timestamp.isoformat(),
                'timestamp_relative': timesince(entry.timestamp),
                'icon': self.get_activity_icon(entry.activity_type),
            })
        
        return JsonResponse({
            'success': True,
            'history': history_data,
            'has_more': len(history_data) == limit
        })
    
    def calculate_activity_summary(self, assessment):
        """Calculate summary statistics for assessment activities"""
        from datetime import timedelta
        
        all_activities = AssessmentHistory.objects.filter(assessment=assessment)
        
        # Count activities by type
        workflow_steps = all_activities.filter(
            activity_type__in=['status_change', 'workflow_action', 'approval_granted', 'rejection_issued']
        ).count()
        
        comments = all_activities.filter(activity_type='comment_added').count()
        
        # Recent activity (last 7 days)
        recent_cutoff = timezone.now() - timedelta(days=7)
        recent_activities = all_activities.filter(timestamp__gte=recent_cutoff).count()
        
        return {
            'total_activities': all_activities.count(),
            'total_workflow_steps': workflow_steps,
            'total_comments': comments,
            'recent_activity_count': recent_activities,
        }
    
    def get_activity_title(self, entry):
        """Generate human-readable title for activity"""
        titles = {
            'status_change': f'Status changed from {entry.old_value} to {entry.new_value}',
            'cost_adjustment': f'Cost adjusted: {entry.field_name}',
            'document_update': f'Document updated: {entry.field_name}',
            'agent_assignment': f'Agent assigned: {entry.new_value}',
            'comment_added': 'Comment added',
            'photo_uploaded': 'Photo uploaded',
            'photo_deleted': 'Photo deleted',
            'section_updated': f'Section updated: {entry.related_section}',
            'workflow_action': 'Workflow action taken',
            'report_generated': 'Report generated',
            'approval_granted': 'Assessment approved',
            'rejection_issued': 'Assessment rejected',
            'changes_requested': 'Changes requested',
        }
        return titles.get(entry.activity_type, entry.description)
    
    def get_activity_icon(self, activity_type):
        """Get FontAwesome icon for activity type"""
        icons = {
            'status_change': 'fas fa-exchange-alt',
            'cost_adjustment': 'fas fa-pound-sign',
            'document_update': 'fas fa-file-alt',
            'agent_assignment': 'fas fa-user-plus',
            'comment_added': 'fas fa-comment',
            'photo_uploaded': 'fas fa-camera',
            'photo_deleted': 'fas fa-trash',
            'section_updated': 'fas fa-edit',
            'workflow_action': 'fas fa-cogs',
            'report_generated': 'fas fa-file-pdf',
            'approval_granted': 'fas fa-check-circle',
            'rejection_issued': 'fas fa-times-circle',
            'changes_requested': 'fas fa-exclamation-triangle',
        }
        return icons.get(activity_type, 'fas fa-circle')


@method_decorator([require_group('AutoAssess'), check_permission_conflicts], name='dispatch')
class AssessmentVersionCompareView(LoginRequiredMixin, View):
    """View for comparing different versions of assessment data"""
    
    def get(self, request, assessment_id):
        from assessments.models import VehicleAssessment
        
        # Get assessment
        assessment = get_object_or_404(
            VehicleAssessment,
            assessment_id=assessment_id,
            assigned_agent=request.user
        )
        
        version_a_id = request.GET.get('version_a')
        version_b_id = request.GET.get('version_b')
        
        if not version_a_id or not version_b_id:
            return JsonResponse({'success': False, 'error': 'Both versions must be specified'})
        
        try:
            version_a = AssessmentVersion.objects.get(
                id=version_a_id,
                assessment=assessment
            )
            version_b = AssessmentVersion.objects.get(
                id=version_b_id,
                assessment=assessment
            )
        except AssessmentVersion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid version specified'})
        
        # Compare the versions
        comparison_data = self.compare_versions(version_a, version_b)
        
        # Generate HTML for comparison
        comparison_html = self.render_comparison_html(comparison_data, version_a, version_b)
        
        return JsonResponse({
            'success': True,
            'comparison_html': comparison_html
        })
    
    def compare_versions(self, version_a, version_b):
        """Compare two assessment versions and return differences"""
        data_a = version_a.assessment_data
        data_b = version_b.assessment_data
        
        differences = []
        
        # Compare key fields
        fields_to_compare = [
            'estimated_repair_cost',
            'agent_status',
            'agent_notes',
            'incident_description',
            'incident_location',
        ]
        
        for field in fields_to_compare:
            value_a = data_a.get(field)
            value_b = data_b.get(field)
            
            if value_a != value_b:
                differences.append({
                    'field': field,
                    'field_display': field.replace('_', ' ').title(),
                    'value_a': value_a,
                    'value_b': value_b,
                    'type': 'field_change'
                })
        
        return differences
    
    def render_comparison_html(self, differences, version_a, version_b):
        """Render HTML for version comparison"""
        if not differences:
            return '<p class="text-gray-600">No differences found between these versions.</p>'
        
        html = f'''
        <div class="version-comparison-header mb-4">
            <div class="grid grid-cols-2 gap-4">
                <div class="text-center">
                    <h3 class="font-semibold">Version {version_a.version_number}</h3>
                    <p class="text-sm text-gray-600">{version_a.created_at.strftime("%b %d, %Y %H:%M")}</p>
                    <p class="text-sm text-gray-600">by {version_a.created_by.get_full_name() or version_a.created_by.username}</p>
                </div>
                <div class="text-center">
                    <h3 class="font-semibold">Version {version_b.version_number}</h3>
                    <p class="text-sm text-gray-600">{version_b.created_at.strftime("%b %d, %Y %H:%M")}</p>
                    <p class="text-sm text-gray-600">by {version_b.created_by.get_full_name() or version_b.created_by.username}</p>
                </div>
            </div>
        </div>
        
        <div class="differences">
        '''
        
        for diff in differences:
            html += f'''
            <div class="difference-item mb-4 p-4 border rounded">
                <h4 class="font-medium mb-2">{diff['field_display']}</h4>
                <div class="grid grid-cols-2 gap-4">
                    <div class="old-value">
                        <span class="text-sm text-gray-600">Version {version_a.version_number}:</span>
                        <div class="p-2 bg-red-50 border border-red-200 rounded text-red-800">
                            {diff['value_a'] or 'None'}
                        </div>
                    </div>
                    <div class="new-value">
                        <span class="text-sm text-gray-600">Version {version_b.version_number}:</span>
                        <div class="p-2 bg-green-50 border border-green-200 rounded text-green-800">
                            {diff['value_b'] or 'None'}
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        html += '</div>'
        return html





# Utility functions for assessment history tracking

def create_assessment_history_entry(assessment, activity_type, user, description, **kwargs):
    """Utility function to create assessment history entries"""
    
    # Extract additional parameters
    field_name = kwargs.get('field_name', '')
    old_value = kwargs.get('old_value', '')
    new_value = kwargs.get('new_value', '')
    notes = kwargs.get('notes', '')
    related_section = kwargs.get('related_section', '')
    related_comment_id = kwargs.get('related_comment_id')
    related_photo_id = kwargs.get('related_photo_id')
    
    # Get IP address and user agent from request if available
    ip_address = None
    user_agent = ''
    
    # Try to get request from thread local storage or other means
    # This is a simplified version - in production you'd want proper request handling
    
    return AssessmentHistory.objects.create(
        assessment=assessment,
        activity_type=activity_type,
        user=user,
        description=description,
        field_name=field_name,
        old_value=str(old_value) if old_value else '',
        new_value=str(new_value) if new_value else '',
        notes=notes,
        related_section=related_section,
        related_comment_id=related_comment_id,
        related_photo_id=related_photo_id,
        ip_address=ip_address,
        user_agent=user_agent
    )


def create_assessment_version(assessment, user, change_summary, is_major=False):
    """Create a new version snapshot of assessment data"""
    
    # Get the next version number
    last_version = AssessmentVersion.objects.filter(
        assessment=assessment
    ).order_by('-version_number').first()
    
    next_version = (last_version.version_number + 1) if last_version else 1
    
    # Create assessment data snapshot
    assessment_data = {
        'assessment_id': assessment.assessment_id,
        'estimated_repair_cost': float(assessment.estimated_repair_cost) if assessment.estimated_repair_cost else 0,
        'agent_status': assessment.agent_status,
        'agent_notes': assessment.agent_notes,
        'incident_description': assessment.incident_description,
        'incident_location': assessment.incident_location,
        'assessment_date': assessment.assessment_date.isoformat() if assessment.assessment_date else None,
        'completed_date': assessment.completed_date.isoformat() if assessment.completed_date else None,
        'review_deadline': assessment.review_deadline.isoformat() if assessment.review_deadline else None,
        # Add more fields as needed
    }
    
    # Create version record
    version = AssessmentVersion.objects.create(
        assessment=assessment,
        version_number=next_version,
        created_by=user,
        assessment_data=assessment_data,
        change_summary=change_summary,
        is_major_version=is_major
    )
    
    return version