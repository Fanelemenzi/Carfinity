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
from .services import AuthenticationService, OrganizationService
from organizations.models import Organization, OrganizationUser
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
        
        # Filter by organization type if specified
        org_type_filter = self.request.GET.get('org_type', '')
        if org_type_filter:
            org_users = OrganizationUser.objects.filter(
                organization__organization_type=org_type_filter,
                is_active=True
            ).values_list('user_id', flat=True)
            users = users.filter(id__in=org_users)
        
        # Paginate results
        paginator = Paginator(users, 25)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Build user permission data
        user_permissions = []
        for user in page_obj:
            permissions = AuthenticationService.get_user_permissions(user)
            org = OrganizationService.get_user_organization(user)
            
            user_permissions.append({
                'user': user,
                'permissions': permissions,
                'organization': org,
                'organization_role': OrganizationService.get_user_organization_role(user),
                'groups': list(user.groups.values_list('name', flat=True)),
            })
        
        # Get filter options
        all_groups = Group.objects.all().order_by('name')
        org_types = Organization.ORGANIZATION_TYPES
        
        # Get summary statistics
        total_users = User.objects.count()
        users_with_groups = User.objects.filter(groups__isnull=False).distinct().count()
        users_with_orgs = User.objects.filter(
            id__in=OrganizationUser.objects.filter(is_active=True).values_list('user_id', flat=True)
        ).count()
        
        context.update({
            'user_permissions': user_permissions,
            'page_obj': page_obj,
            'search_query': search_query,
            'group_filter': group_filter,
            'org_type_filter': org_type_filter,
            'all_groups': all_groups,
            'org_types': org_types,
            'total_users': total_users,
            'users_with_groups': users_with_groups,
            'users_with_orgs': users_with_orgs,
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
        
        elif action == 'sync_org_groups':
            synced_count = 0
            for user in users:
                org = OrganizationService.get_user_organization(user)
                if org:
                    org.add_user_to_groups(user)
                    synced_count += 1
            messages.success(request, f'Synced {synced_count} users with their organization groups.')
        
        elif action == 'check_permissions':
            conflict_count = 0
            for user in users:
                permissions = AuthenticationService.get_user_permissions(user)
                if permissions.has_conflicts:
                    conflict_count += 1
                    logger.warning(f"Permission conflict for user {user.username}: {permissions.conflict_details}")
            
            if conflict_count > 0:
                messages.warning(request, f'Found permission conflicts for {conflict_count} users. Check logs for details.')
            else:
                messages.success(request, f'No permission conflicts found for {users.count()} users.')
        
        return redirect('admin:users_bulk_management')
    
    # GET request - show the form
    users = User.objects.select_related('profile').prefetch_related('groups').all()
    groups = Group.objects.all().order_by('name')
    
    context = {
        'users': users,
        'groups': groups,
        'title': 'Bulk User Management',
    }
    
    return render(request, 'admin/users/bulk_management.html', context)


@staff_member_required
def permission_conflicts_report(request):
    """Admin view for viewing permission conflicts report"""
    users = User.objects.select_related('profile').prefetch_related('groups').all()
    
    conflicts_data = []
    for user in users:
        permissions = AuthenticationService.get_user_permissions(user)
        if permissions.has_conflicts:
            org = OrganizationService.get_user_organization(user)
            conflicts_data.append({
                'user': user,
                'permissions': permissions,
                'organization': org,
                'groups': list(user.groups.values_list('name', flat=True)),
            })
    
    context = {
        'conflicts_data': conflicts_data,
        'total_conflicts': len(conflicts_data),
        'title': 'Permission Conflicts Report',
    }
    
    return render(request, 'admin/users/permission_conflicts.html', context)


@staff_member_required
def export_user_permissions(request):
    """Export user permissions data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_permissions.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'Email', 'First Name', 'Last Name', 'Groups', 
        'Organization', 'Organization Type', 'Organization Role',
        'Available Dashboards', 'Default Dashboard', 'Has Conflicts', 'Conflict Details'
    ])
    
    users = User.objects.select_related('profile').prefetch_related('groups').all()
    
    for user in users:
        permissions = AuthenticationService.get_user_permissions(user)
        org = OrganizationService.get_user_organization(user)
        org_role = OrganizationService.get_user_organization_role(user)
        
        writer.writerow([
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            ', '.join(user.groups.values_list('name', flat=True)),
            org.name if org else '',
            org.organization_type if org else '',
            org_role or '',
            ', '.join(permissions.available_dashboards),
            permissions.default_dashboard or '',
            'Yes' if permissions.has_conflicts else 'No',
            permissions.conflict_details or ''
        ])
    
    return response


@staff_member_required
def group_organization_mapping(request):
    """Admin view for viewing group-organization mappings"""
    groups = Group.objects.annotate(user_count=Count('user')).all()
    organizations = Organization.objects.prefetch_related('linked_groups').all()
    
    # Build mapping data
    group_data = []
    for group in groups:
        linked_orgs = Organization.objects.filter(linked_groups=group)
        group_data.append({
            'group': group,
            'user_count': group.user_count,
            'linked_organizations': linked_orgs,
            'dashboard_access': get_dashboard_for_group(group.name),
        })
    
    org_data = []
    for org in organizations:
        members = OrganizationUser.objects.filter(organization=org, is_active=True)
        org_data.append({
            'organization': org,
            'member_count': members.count(),
            'linked_groups': org.linked_groups.all(),
            'members_without_groups': get_members_without_groups(org),
        })
    
    context = {
        'group_data': group_data,
        'org_data': org_data,
        'title': 'Group-Organization Mapping',
    }
    
    return render(request, 'admin/users/group_org_mapping.html', context)


def get_dashboard_for_group(group_name):
    """Get dashboard access for a group"""
    dashboard_mapping = {
        'customers': 'Customer Dashboard',
        'insurance_company': 'Insurance Dashboard'
    }
    return dashboard_mapping.get(group_name, 'No specific dashboard')


def get_members_without_groups(organization):
    """Get organization members who don't have any groups"""
    members = OrganizationUser.objects.filter(
        organization=organization, 
        is_active=True
    ).select_related('user')
    
    members_without_groups = []
    for member in members:
        if not member.user.groups.exists():
            members_without_groups.append(member.user)
    
    return members_without_groups


@staff_member_required
def ajax_user_permissions(request):
    """AJAX endpoint for getting user permissions data"""
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
        permissions = AuthenticationService.get_user_permissions(user)
        org = OrganizationService.get_user_organization(user)
        org_role = OrganizationService.get_user_organization_role(user)
        
        data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'groups': list(user.groups.values_list('name', flat=True)),
            'organization': org.name if org else None,
            'organization_type': org.organization_type if org else None,
            'organization_role': org_role,
            'available_dashboards': permissions.available_dashboards,
            'default_dashboard': permissions.default_dashboard,
            'has_conflicts': permissions.has_conflicts,
            'conflict_details': permissions.conflict_details,
        }
        
        return JsonResponse(data)
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting user permissions for user {user_id}: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@staff_member_required
def authentication_group_management(request):
    """Admin view for comprehensive authentication group management"""
    from .models import AuthenticationGroup
    
    # Get all authentication groups
    auth_groups = AuthenticationGroup.objects.select_related('group').order_by('-priority', 'display_name')
    
    # Get all Django groups that don't have auth configurations
    configured_group_ids = auth_groups.values_list('group_id', flat=True)
    unconfigured_groups = Group.objects.exclude(id__in=configured_group_ids)
    
    # Get statistics
    total_auth_groups = auth_groups.count()
    active_auth_groups = auth_groups.filter(is_active=True).count()
    total_users_in_auth_groups = User.objects.filter(
        groups__in=auth_groups.values_list('group', flat=True)
    ).distinct().count()
    
    context = {
        'auth_groups': auth_groups,
        'unconfigured_groups': unconfigured_groups,
        'total_auth_groups': total_auth_groups,
        'active_auth_groups': active_auth_groups,
        'total_users_in_auth_groups': total_users_in_auth_groups,
        'title': 'Authentication Group Management',
    }
    
    return render(request, 'admin/users/authentication_group_management.html', context)


@staff_member_required
def ajax_test_auth_group_config(request):
    """AJAX endpoint for testing authentication group configuration"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    group_id = request.POST.get('group_id')
    if not group_id:
        return JsonResponse({'error': 'Group ID required'}, status=400)
    
    try:
        from .models import AuthenticationGroup
        auth_group = AuthenticationGroup.objects.get(id=group_id)
        
        # Test the configuration
        test_results = {
            'group_name': auth_group.group.name,
            'display_name': auth_group.display_name,
            'dashboard_url': auth_group.dashboard_url,
            'dashboard_type': auth_group.dashboard_type,
            'is_active': auth_group.is_active,
            'user_count': auth_group.group.user_set.count(),
            'compatible_org_types': auth_group.compatible_org_types,
            'priority': auth_group.priority
        }
        
        # Check if URL is valid (basic check)
        url_valid = auth_group.dashboard_url.startswith('/') and auth_group.dashboard_url.endswith('/')
        test_results['url_valid'] = url_valid
        
        # Check for conflicts with other groups
        conflicts = AuthenticationGroup.objects.filter(
            dashboard_url=auth_group.dashboard_url,
            is_active=True
        ).exclude(id=auth_group.id)
        
        test_results['has_conflicts'] = conflicts.exists()
        test_results['conflicting_groups'] = [ag.display_name for ag in conflicts]
        
        return JsonResponse({
            'success': True,
            'test_results': test_results
        })
        
    except AuthenticationGroup.DoesNotExist:
        return JsonResponse({'error': 'Authentication group not found'}, status=404)
    except Exception as e:
        logger.error(f"Error testing auth group config {group_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)