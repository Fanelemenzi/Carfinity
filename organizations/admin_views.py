"""
Custom admin views for organization-group management.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.http import JsonResponse
from .models import Organization, OrganizationUser


@staff_member_required
def organization_group_management(request):
    """Admin view for comprehensive organization-group management"""
    
    # Get all organizations with their group and member info
    organizations = Organization.objects.prefetch_related(
        'linked_groups', 'organization_members__user'
    ).annotate(
        active_member_count=Count('organization_members', filter=Q(organization_members__is_active=True))
    )
    
    # Get all groups with organization info
    groups = Group.objects.prefetch_related('organizations').annotate(
        user_count=Count('user'),
        org_count=Count('organizations')
    )
    
    # Build organization data
    org_data = []
    for org in organizations:
        linked_groups = org.linked_groups.all()
        active_members = org.organization_members.filter(is_active=True)
        
        # Check sync status
        sync_issues = 0
        for member in active_members:
            user_groups = set(member.user.groups.values_list('name', flat=True))
            org_groups = set(linked_groups.values_list('name', flat=True))
            if not org_groups.issubset(user_groups):
                sync_issues += 1
        
        org_data.append({
            'organization': org,
            'linked_groups': linked_groups,
            'active_members': active_members,
            'sync_issues': sync_issues,
            'recommended_groups': get_recommended_groups(org.organization_type),
        })
    
    # Build group data
    group_data = []
    for group in groups:
        linked_orgs = group.organizations.all()
        group_data.append({
            'group': group,
            'linked_organizations': linked_orgs,
            'user_count': group.user_count,
            'org_count': group.org_count,
            'dashboard_access': get_dashboard_for_group(group.name),
        })
    
    context = {
        'org_data': org_data,
        'group_data': group_data,
        'title': 'Organization-Group Management',
    }
    
    return render(request, 'admin/organizations/group_management.html', context)


@staff_member_required
def ajax_sync_organization_groups(request):
    """AJAX endpoint for syncing organization groups"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    org_id = request.POST.get('org_id')
    if not org_id:
        return JsonResponse({'error': 'Organization ID required'}, status=400)
    
    try:
        org = Organization.objects.get(id=org_id)
        org.sync_all_members_to_groups()
        
        # Get updated sync status
        active_members = org.organization_members.filter(is_active=True)
        sync_issues = 0
        for member in active_members:
            user_groups = set(member.user.groups.values_list('name', flat=True))
            org_groups = set(org.linked_groups.values_list('name', flat=True))
            if not org_groups.issubset(user_groups):
                sync_issues += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Synced {active_members.count()} members',
            'sync_issues': sync_issues
        })
        
    except Organization.DoesNotExist:
        return JsonResponse({'error': 'Organization not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_recommended_groups(org_type):
    """Get recommended groups based on organization type using configurable system"""
    try:
        from users.models import AuthenticationGroup
        return AuthenticationGroup.get_recommended_groups_for_org_type(org_type)
    except ImportError:
        # Fallback to hardcoded recommendations if AuthenticationGroup not available
        recommendations = {
            'insurance': ['insurance_company'],
            'fleet': ['customers'],
            'dealership': ['customers'],
            'service': ['customers'],
            'other': ['customers']
        }
        return recommendations.get(org_type, [])


def get_dashboard_for_group(group_name):
    """Get dashboard access description for a group using configurable system"""
    try:
        from users.models import AuthenticationGroup
        auth_group = AuthenticationGroup.objects.filter(
            group__name=group_name, 
            is_active=True
        ).first()
        
        if auth_group:
            return auth_group.get_dashboard_display()
    except ImportError:
        pass
    
    # Fallback to hardcoded mapping
    dashboard_mapping = {
        'customers': 'Customer Dashboard',
        'insurance_company': 'Insurance Dashboard'
    }
    return dashboard_mapping.get(group_name, 'No specific dashboard')