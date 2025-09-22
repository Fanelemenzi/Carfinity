# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from users.permissions import require_group, require_organization_type, check_permission_conflicts
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import render

# Dashboard Views
@method_decorator([require_group('Insurance Companies'), require_organization_type('insurance'), check_permission_conflicts], name='dispatch')
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

@method_decorator([require_group('Insurance Companies'), require_organization_type('insurance'), check_permission_conflicts], name='dispatch')
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

@method_decorator([require_group('Insurance Companies'), require_organization_type('insurance'), check_permission_conflicts], name='dispatch')
class AssessmentDashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/insurance_assessment_dashboard.html'
    context_object_name = 'assessments'
    
    def get_queryset(self):
        # Return empty queryset for now - will be populated with actual assessment data later
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add context data for the assessment dashboard
        context.update({
            'active_claims': 24,
            'pending_reviews': 8,
            'avg_processing_time': '4.2h',
            'cost_savings': '£18.5K',
            'accuracy_rate': '94.2%',
            'customer_satisfaction': '4.7/5',
        })
        
        return context

@method_decorator([require_group('Insurance Companies'), require_organization_type('insurance'), check_permission_conflicts], name='dispatch')
class BookAssessmentView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/insurance_booking.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        # Return empty queryset for now - will be populated with actual booking data later
        return []
    
    def post(self, request, *args, **kwargs):
        # Handle form submission for booking new assessments
        # This will be implemented in later tasks
        messages.success(request, 'Assessment request submitted successfully!')
        return self.get(request, *args, **kwargs)

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
            'vehicle_age': timezone.now().year - vehicle.year,
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


@require_group('Insurance Companies')
@require_organization_type('insurance')
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