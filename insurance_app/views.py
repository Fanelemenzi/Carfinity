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

# Dashboard Views
class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/insurance_dashboard.html'
    context_object_name = 'policies'
    
    def get_queryset(self):
        return InsurancePolicy.objects.filter(
            policy_holder=self.request.user,
            status='active'
        ).prefetch_related('vehicles')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all vehicles for user's policies
        vehicles = Vehicle.objects.filter(
            policy__policy_holder=self.request.user,
            policy__status='active'
        )
        
        # Portfolio Maintenance Compliance
        compliance_data = MaintenanceCompliance.objects.filter(
            vehicle__in=vehicles
        ).aggregate(
            avg_compliance=Avg('overall_compliance_rate'),
            avg_critical_compliance=Avg('critical_maintenance_compliance')
        )
        
        # Vehicle Condition Distribution
        condition_distribution = vehicles.values('current_condition').annotate(
            count=Count('id')
        )
        
        # Risk Alerts
        active_alerts = RiskAlert.objects.filter(
            vehicle__in=vehicles,
            is_resolved=False
        ).order_by('-severity', '-created_at')[:10]
        
        # Recent Accidents
        recent_accidents = Accident.objects.filter(
            vehicle__in=vehicles,
            accident_date__gte=timezone.now() - timedelta(days=30)
        ).select_related('vehicle')
        
        # Get high-risk vehicles for the table
        high_risk_vehicles_list = vehicles.filter(risk_score__gte=7).select_related('policy')[:10]
        
        # Calculate average health index
        avg_health_index = vehicles.aggregate(avg_health=Avg('vehicle_health_index'))['avg_health'] or 0
        
        context.update({
            'total_vehicles': vehicles.count(),
            'avg_compliance_rate': compliance_data['avg_compliance'] or 0,
            'avg_critical_compliance': compliance_data['avg_critical_compliance'] or 0,
            'avg_health_index': avg_health_index,
            'condition_distribution': list(condition_distribution),
            'active_alerts': active_alerts,
            'recent_accidents': recent_accidents,
            'high_risk_vehicles': vehicles.filter(risk_score__gte=7).count(),
            'high_risk_vehicles_list': high_risk_vehicles_list,
        })
        
        return context

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