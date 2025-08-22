from django.http import JsonResponse
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from maintenance.models import Part, ScheduledMaintenance
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json


class PartSearchAPIView(View):
    """
    API endpoint for searching parts with filtering and pagination
    """
    
    def get(self, request):
        # Get search parameters
        query = request.GET.get('q', '')
        category = request.GET.get('category', '')
        page = request.GET.get('page', 1)
        page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 items per page
        
        # Build queryset with filters
        parts = Part.objects.all()
        
        if query:
            parts = parts.filter(
                Q(name__icontains=query) |
                Q(part_number__icontains=query) |
                Q(description__icontains=query)
            )
        
        if category:
            parts = parts.filter(category__icontains=category)
        
        # Order by name for consistent results
        parts = parts.order_by('name')
        
        # Paginate results
        paginator = Paginator(parts, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        parts_data = []
        for part in page_obj:
            parts_data.append({
                'id': part.id,
                'name': part.name,
                'part_number': part.part_number,
                'description': part.description,
                'manufacturer': part.manufacturer,
                'category': part.category,
                'cost': str(part.cost) if part.cost else None,
                'stock_quantity': part.stock_quantity,
                'minimum_stock_level': part.minimum_stock_level,
                'is_low_stock': part.is_low_stock,
            })
        
        return JsonResponse({
            'results': parts_data,
            'pagination': {
                'page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })


class PartDetailsAPIView(View):
    """
    API endpoint for retrieving individual part details
    """
    
    def get(self, request, part_id):
        try:
            part = Part.objects.get(id=part_id)
            
            part_data = {
                'id': part.id,
                'name': part.name,
                'part_number': part.part_number,
                'description': part.description,
                'manufacturer': part.manufacturer,
                'category': part.category,
                'cost': str(part.cost) if part.cost else None,
                'stock_quantity': part.stock_quantity,
                'minimum_stock_level': part.minimum_stock_level,
                'is_low_stock': part.is_low_stock,
                'created_at': part.created_at.isoformat(),
                'updated_at': part.updated_at.isoformat(),
            }
            
            return JsonResponse({'part': part_data})
            
        except Part.DoesNotExist:
            return JsonResponse({
                'error': 'Part not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'error': 'An error occurred while retrieving part details'
            }, status=500)


class ScheduledMaintenanceAPIView(View):
    """
    API endpoint for retrieving scheduled maintenance filtered by vehicle
    """
    
    def get(self, request):
        vehicle_id = request.GET.get('vehicle')
        
        if not vehicle_id:
            return JsonResponse({
                'error': 'Vehicle ID is required'
            }, status=400)
        
        try:
            # Get scheduled maintenance for the specified vehicle
            scheduled_maintenance = ScheduledMaintenance.objects.filter(
                assigned_plan__vehicle_id=vehicle_id,
                status='PENDING'  # Only show pending maintenance
            ).select_related('task', 'assigned_plan__vehicle').order_by('due_date')
            
            # Serialize data
            maintenance_data = []
            for sm in scheduled_maintenance:
                maintenance_data.append({
                    'id': sm.id,
                    'task_name': sm.task.name,
                    'description': sm.task.description,
                    'due_date': sm.due_date.strftime('%Y-%m-%d'),
                    'due_mileage': sm.due_mileage,
                    'priority': sm.task.priority,
                    'estimated_time': str(sm.task.estimated_time) if sm.task.estimated_time else None,
                })
            
            return JsonResponse(maintenance_data, safe=False)
            
        except Exception as e:
            return JsonResponse({
                'error': 'An error occurred while retrieving scheduled maintenance'
            }, status=500)