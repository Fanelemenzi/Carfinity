"""
Custom admin views for group-based authentication system.

This module provides additional admin views for managing user permissions,
viewing access logs, and bulk user management operations.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from .services import AuthenticationService
import csv
import logging

logger = logging.getLogger(__name__)


def is_admin_user(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@method_decorator(user_passes_test(is_admin_user), name='dispatch')
class UserPermissionsView(TemplateView):
    """Admin view for viewing and managing user permissions"""
    template_name = 'admin/users/user_permissions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all users with their permission details
        users = User.objects.select_related('profile').prefetch_related('groups').all()
        
        # Filter users if search query provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Filter by group if specified
        group_filter = self.request.GET.get('group', '')
        if group_filter:
            users = users.filter(groups__name=group_filter)
        
        # Filter by dashboard access if specified
        dashboard_filter = self.request.GET.get('dashboard', '')
        if dashboard_filter:
            # Filter users who have access to specific dashboard
            dashboard_groups = {
                'Staff': ['Staff'],
                'AutoCare': ['AutoCare'],
                'AutoAssess': ['AutoAssess']
            }
            if dashboard_filter in dashboard_groups:
                users = users.filter(groups__name__in=dashboard_groups[dashboard_filter])
        
        # Paginate results
        paginator = Paginator(users, 25)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Build user permission data
        user_permissions = []
        for user in page_obj:
            permissions = AuthenticationService.get_user_permissions(user)
            
            user_permissions.append({
                'user': user,
                'permissions': permissions,
                'groups': list(user.groups.values_list('name', flat=True)),
            })
        
        # Get filter options
        all_groups = Group.objects.filter(name__in=['Staff', 'AutoCare', 'AutoAssess']).order_by('name')
        dashboard_options = ['Staff', 'AutoCare', 'AutoAssess']
        
        # Get summary statistics
        total_users = User.objects.count()
        users_with_groups = User.objects.filter(groups__isnull=False).distinct().count()
        users_with_dashboard_access = User.objects.filter(
            groups__name__in=['Staff', 'AutoCare', 'AutoAssess']
        ).distinct().count()
        
        context.update({
            'user_permissions': user_permissions,
            'page_obj': page_obj,
            'search_query': search_query,
            'group_filter': group_filter,
            'dashboard_filter': dashboard_filter,
            'all_groups': all_groups,
            'dashboard_options': dashboard_options,
            'total_users': total_users,
            'users_with_groups': users_with_groups,
            'users_with_dashboard_access': users_with_dashboard_access,
        })
        
        return context


@staff_member_required
def bulk_user_management(request):
    """Admin view for bulk user management operations"""
    if request.method == 'POST':
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')
        
        if not user_ids:
            messages.error(request, 'No users selected.')
            return redirect('admin:users_bulk_management')
        
        users = User.objects.filter(id__in=user_ids)
        
        if action == 'add_to_group':
            group_id = request.POST.get('group_id')
            if group_id:
                try:
                    group = Group.objects.get(id=group_id)
                    for user in users:
                        user.groups.add(group)
                    messages.success(request, f'Added {users.count()} users to group "{group.name}".')
                except Group.DoesNotExist:
                    messages.error(request, 'Selected group does not exist.')
            else:
                messages.error(request, 'No group selected.')
        
        elif action == 'remove_from_group':
            group_id = request.POST.get('group_id')
            if group_id:
                try:
                    group = Group.objects.get(id=group_id)
                    for user in users:
                        user.groups.remove(group)
                    messages.success(request, f'Removed {users.count()} users from group "{group.name}".')
                except Group.DoesNotExist:
                    messages.error(request, 'Selected group does not exist.')
            else:
                messages.error(request, 'No group selected.')
        
        elif action == 'assign_default_groups':
            # Assign users to AutoCare group by default if they have no groups
            assigned_count = 0
            try:
                autocare_group = Group.objects.get(name='AutoCare')
                for user in users:
                    if not user.groups.exists():
                        user.groups.add(autocare_group)
                        assigned_count += 1
                messages.success(request, f'Assigned {assigned_count} users to AutoCare group.')
            except Group.DoesNotExist:
                messages.error(request, 'AutoCare group does not exist. Run setup_three_groups command first.')
        
        elif action == 'check_permissions':
            no_access_count = 0
            for user in users:
                permissions = AuthenticationService.get_user_permissions(user)
                if not permissions.has_access:
                    no_access_count += 1
                    logger.warning(f"No dashboard access for user {user.username}: groups={permissions.groups}")
            
            if no_access_count > 0:
                messages.warning(request, f'Found {no_access_count} users without dashboard access. Check logs for details.')
            else:
                messages.success(request, f'All {users.count()} users have dashboard access.')
        
        return redirect('admin:users_bulk_management')
    
    # GET request - show the form
    users = User.objects.select_related('profile').prefetch_related('groups').all()
    groups = Group.objects.filter(name__in=['Staff', 'AutoCare', 'AutoAssess']).order_by('name')
    
    context = {
        'users': users,
        'groups': groups,
        'title': 'Bulk User Management',
    }
    
    return render(request, 'admin/users/bulk_management.html', context)


@staff_member_required
def users_without_access_report(request):
    """Admin view for viewing users without dashboard access report"""
    users = User.objects.select_related('profile').prefetch_related('groups').all()
    
    no_access_data = []
    for user in users:
        permissions = AuthenticationService.get_user_permissions(user)
        if not permissions.has_access:
            no_access_data.append({
                'user': user,
                'permissions': permissions,
                'groups': list(user.groups.values_list('name', flat=True)),
            })
    
    context = {
        'no_access_data': no_access_data,
        'total_without_access': len(no_access_data),
        'title': 'Users Without Dashboard Access Report',
    }
    
    return render(request, 'admin/users/users_without_access.html', context)


@staff_member_required
def export_user_permissions(request):
    """Export user permissions data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_permissions.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'Email', 'First Name', 'Last Name', 'Groups', 
        'Available Dashboards', 'Default Dashboard', 'Has Access'
    ])
    
    users = User.objects.select_related('profile').prefetch_related('groups').all()
    
    for user in users:
        permissions = AuthenticationService.get_user_permissions(user)
        
        writer.writerow([
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            ', '.join(user.groups.values_list('name', flat=True)),
            ', '.join(permissions.available_dashboards),
            permissions.default_dashboard or '',
            'Yes' if permissions.has_access else 'No'
        ])
    
    return response


@staff_member_required
def group_dashboard_mapping(request):
    """Admin view for viewing group-dashboard mappings"""
    groups = Group.objects.filter(name__in=['Staff', 'AutoCare', 'AutoAssess']).annotate(user_count=Count('user')).all()
    
    # Build mapping data
    group_data = []
    for group in groups:
        group_data.append({
            'group': group,
            'user_count': group.user_count,
            'dashboard_access': get_dashboard_for_group(group.name),
            'description': get_group_description(group.name),
        })
    
    context = {
        'group_data': group_data,
        'title': 'Group-Dashboard Mapping',
    }
    
    return render(request, 'admin/users/group_dashboard_mapping.html', context)


def get_dashboard_for_group(group_name):
    """Get dashboard access for a group"""
    dashboard_mapping = {
        'Staff': '/admin/ (Administrative Dashboard)',
        'AutoCare': '/dashboard/ (Vehicle Maintenance)',
        'AutoAssess': '/insurance/ (Vehicle Assessment)'
    }
    return dashboard_mapping.get(group_name, 'No specific dashboard')

def get_group_description(group_name):
    """Get description for a group"""
    descriptions = {
        'Staff': 'Administrative users with full system access',
        'AutoCare': 'Vehicle maintenance technicians and managers',
        'AutoAssess': 'Insurance assessors and claims processors'
    }
    return descriptions.get(group_name, 'Custom group')


@staff_member_required
def ajax_user_permissions(request):
    """AJAX endpoint for getting user permissions data"""
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
        permissions = AuthenticationService.get_user_permissions(user)
        
        data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'groups': list(user.groups.values_list('name', flat=True)),
            'available_dashboards': permissions.available_dashboards,
            'default_dashboard': permissions.default_dashboard,
            'has_access': permissions.has_access,
        }
        
        return JsonResponse(data)
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting user permissions for user {user_id}: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@staff_member_required
def three_group_management(request):
    """Admin view for managing the 3-group authentication system"""
    # Get the three main groups
    main_groups = Group.objects.filter(name__in=['Staff', 'AutoCare', 'AutoAssess']).annotate(
        user_count=Count('user')
    ).order_by('name')
    
    # Get statistics
    total_users = User.objects.count()
    users_in_main_groups = User.objects.filter(
        groups__name__in=['Staff', 'AutoCare', 'AutoAssess']
    ).distinct().count()
    users_without_groups = User.objects.filter(groups__isnull=True).count()
    
    # Build group data
    group_data = []
    for group in main_groups:
        group_data.append({
            'group': group,
            'user_count': group.user_count,
            'dashboard_access': get_dashboard_for_group(group.name),
            'description': get_group_description(group.name),
        })
    
    context = {
        'group_data': group_data,
        'total_users': total_users,
        'users_in_main_groups': users_in_main_groups,
        'users_without_groups': users_without_groups,
        'title': '3-Group Authentication Management',
    }
    
    return render(request, 'admin/users/three_group_management.html', context)


@staff_member_required
def ajax_test_group_config(request):
    """AJAX endpoint for testing group configuration"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    group_id = request.POST.get('group_id')
    if not group_id:
        return JsonResponse({'error': 'Group ID required'}, status=400)
    
    try:
        group = Group.objects.get(id=group_id)
        
        # Test the configuration
        test_results = {
            'group_name': group.name,
            'user_count': group.user_set.count(),
            'dashboard_access': get_dashboard_for_group(group.name),
            'description': get_group_description(group.name),
            'is_main_group': group.name in ['Staff', 'AutoCare', 'AutoAssess']
        }
        
        # Check users with permissions
        users_with_access = 0
        for user in group.user_set.all():
            permissions = AuthenticationService.get_user_permissions(user)
            if permissions.has_access:
                users_with_access += 1
        
        test_results['users_with_access'] = users_with_access
        test_results['users_without_access'] = test_results['user_count'] - users_with_access
        
        return JsonResponse({
            'success': True,
            'test_results': test_results
        })
        
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error testing group config {group_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)