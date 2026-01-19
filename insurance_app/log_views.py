"""
Log views for the parts-based quote system.
Provides web interface and API endpoints for viewing system logs.
"""

import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.db import models

from .models import QuoteSystemAuditLog


class LogViewerView(LoginRequiredMixin, TemplateView):
    """Main log viewer interface"""
    template_name = 'public/logs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'System Logs'
        return context


@login_required
def logs_api(request):
    """API endpoint for fetching logs with filtering and pagination"""
    try:
        # Get query parameters
        since_id = request.GET.get('since', 0)
        level_filter = request.GET.get('level', '')
        source_filter = request.GET.get('source', '')
        search_term = request.GET.get('search', '')
        limit = min(int(request.GET.get('limit', 100)), 500)  # Max 500 logs
        
        # Build query
        queryset = QuoteSystemAuditLog.objects.all()
        
        # Filter by ID for incremental updates
        if since_id:
            try:
                queryset = queryset.filter(id__gt=int(since_id))
            except ValueError:
                pass
        
        # Filter by severity level
        if level_filter:
            queryset = queryset.filter(severity=level_filter.lower())
        
        # Filter by action type (source)
        if source_filter:
            queryset = queryset.filter(action_type__icontains=source_filter)
        
        # Search in description
        if search_term:
            queryset = queryset.filter(
                Q(description__icontains=search_term) |
                Q(action_type__icontains=search_term) |
                Q(object_type__icontains=search_term)
            )
        
        # Order by most recent first and limit
        logs = queryset.order_by('-timestamp')[:limit]
        
        # Format logs for JSON response
        log_data = []
        for log in logs:
            log_entry = {
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'level': log.severity.upper(),
                'source': log.action_type,
                'message': log.description,
                'details': log.additional_data or {},
                'user': log.user.username if log.user else 'System',
                'object_type': log.object_type,
                'object_id': log.object_id
            }
            log_data.append(log_entry)
        
        return JsonResponse({
            'success': True,
            'logs': log_data,
            'count': len(log_data),
            'has_more': len(log_data) == limit
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'logs': [],
            'count': 0
        }, status=500)


@login_required
def logs_stats_api(request):
    """API endpoint for log statistics"""
    try:
        # Get logs from last 24 hours
        since = timezone.now() - timedelta(hours=24)
        recent_logs = QuoteSystemAuditLog.objects.filter(timestamp__gte=since)
        
        # Count by severity
        stats = {
            'total_logs': recent_logs.count(),
            'by_severity': {
                'info': recent_logs.filter(severity='info').count(),
                'warning': recent_logs.filter(severity='warning').count(),
                'error': recent_logs.filter(severity='error').count(),
                'critical': recent_logs.filter(severity='critical').count(),
                'debug': recent_logs.filter(severity='debug').count(),
            },
            'by_action_type': {},
            'recent_errors': []
        }
        
        # Count by action type (top 10)
        action_counts = recent_logs.values('action_type').annotate(
            count=models.Count('action_type')
        ).order_by('-count')[:10]
        
        for item in action_counts:
            stats['by_action_type'][item['action_type']] = item['count']
        
        # Get recent errors
        recent_errors = recent_logs.filter(
            severity__in=['error', 'critical']
        ).order_by('-timestamp')[:5]
        
        for error in recent_errors:
            stats['recent_errors'].append({
                'timestamp': error.timestamp.isoformat(),
                'severity': error.severity,
                'description': error.description,
                'action_type': error.action_type
            })
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
def clear_logs_api(request):
    """API endpoint for clearing old logs"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    
    try:
        # Only allow clearing logs older than 7 days by default
        cutoff_days = int(request.POST.get('days', 7))
        if cutoff_days < 1:
            cutoff_days = 7
        
        cutoff_date = timezone.now() - timedelta(days=cutoff_days)
        deleted_count, _ = QuoteSystemAuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def export_logs_api(request):
    """API endpoint for exporting logs as JSON"""
    try:
        # Get query parameters for filtering
        days = int(request.GET.get('days', 7))
        level_filter = request.GET.get('level', '')
        
        # Build query
        since = timezone.now() - timedelta(days=days)
        queryset = QuoteSystemAuditLog.objects.filter(timestamp__gte=since)
        
        if level_filter:
            queryset = queryset.filter(severity=level_filter.lower())
        
        # Get logs
        logs = queryset.order_by('-timestamp')
        
        # Format for export
        export_data = {
            'export_timestamp': timezone.now().isoformat(),
            'filter_days': days,
            'filter_level': level_filter,
            'total_logs': logs.count(),
            'logs': []
        }
        
        for log in logs:
            export_data['logs'].append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'severity': log.severity,
                'action_type': log.action_type,
                'user': log.user.username if log.user else None,
                'description': log.description,
                'object_type': log.object_type,
                'object_id': log.object_id,
                'additional_data': log.additional_data,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent
            })
        
        response = JsonResponse(export_data)
        response['Content-Disposition'] = f'attachment; filename="logs_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)