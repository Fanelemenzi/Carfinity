from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Organization, OrganizationUser, InsuranceOrganization


@login_required
def organization_list(request):
    """List all organizations"""
    organizations = Organization.objects.all()
    insurance_orgs = organizations.filter(is_insurance_provider=True)
    
    context = {
        'organizations': organizations,
        'insurance_organizations': insurance_orgs,
        'total_organizations': organizations.count(),
        'total_insurance_orgs': insurance_orgs.count(),
    }
    
    return render(request, 'organizations/organization_list.html', context)


@login_required
def organization_detail(request, pk):
    """Organization detail view"""
    organization = get_object_or_404(Organization, pk=pk)
    members = organization.organization_members.filter(is_active=True)
    vehicles = organization.organization_vehicles.filter(is_active=True)
    linked_groups = organization.linked_groups.all()
    
    context = {
        'organization': organization,
        'members': members,
        'vehicles': vehicles,
        'linked_groups': linked_groups,
    }
    
    # Add insurance details if it's an insurance provider
    if organization.is_insurance_provider:
        try:
            context['insurance_details'] = organization.insurance_details
        except InsuranceOrganization.DoesNotExist:
            context['insurance_details'] = None
    
    return render(request, 'organizations/organization_detail.html', context)


@login_required
def insurance_dashboard(request):
    """Dashboard for insurance organizations"""
    insurance_orgs = Organization.objects.filter(is_insurance_provider=True)
    
    # Calculate some basic metrics
    total_policies = 0
    total_premium = 0
    
    for org in insurance_orgs:
        policies = org.insurance_policies.all()
        total_policies += policies.count()
        total_premium += sum(policy.premium_amount for policy in policies)
    
    context = {
        'insurance_organizations': insurance_orgs,
        'total_policies': total_policies,
        'total_premium': total_premium,
        'total_insurance_orgs': insurance_orgs.count(),
    }
    
    return render(request, 'organizations/insurance_dashboard.html', context)


# AJAX views
@require_http_methods(["GET"])
@login_required
def available_groups(request):
    """Get available Django groups for linking"""
    groups = Group.objects.all().values('id', 'name')
    return JsonResponse({'groups': list(groups)})


@require_http_methods(["POST"])
@login_required
def link_group_to_organization(request, org_id):
    """Link a Django group to an organization"""
    organization = get_object_or_404(Organization, pk=org_id)
    group_id = request.POST.get('group_id')
    
    if not group_id:
        return JsonResponse({'error': 'Group ID is required'}, status=400)
    
    try:
        group = Group.objects.get(id=group_id)
        organization.linked_groups.add(group)
        
        # Sync all active members to the new group
        organization.sync_all_members_to_groups()
        
        return JsonResponse({
            'success': True,
            'message': f'Group "{group.name}" linked to organization successfully'
        })
        
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)
