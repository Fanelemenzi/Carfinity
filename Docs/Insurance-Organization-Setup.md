# Insurance Organization Setup Guide

## Overview
This guide explains how to set up and use the insurance organization feature that links organizations to Django groups for permission management.

## Features Implemented

### 1. Enhanced Organization Model
- Added `organization_type` field with choices including 'insurance'
- Added `is_insurance_provider` boolean field
- Added `insurance_license_number` and `insurance_rating` fields
- Added `linked_groups` ManyToMany relationship with Django Groups
- Added methods for automatic group management

### 2. Extended User Roles
- Added insurance-specific roles: AGENT, UNDERWRITER, CLAIMS_ADJUSTER
- Automatic group assignment when users join organizations
- Automatic group removal when users leave organizations

### 3. InsuranceOrganization Model
- Extended insurance-specific data (NAIC number, A.M. Best rating, etc.)
- Business metrics tracking (total policies, premium volume)
- Risk management settings
- Notification preferences

### 4. Admin Interface Enhancements
- Group management interface in Organization admin
- Bulk actions for syncing members to groups
- Insurance details creation for insurance providers
- Visual indicators for linked groups and insurance status

## Setup Instructions

### 1. Install Dependencies
```bash
pip install celery cloudinary
```

### 2. Run Migrations
```bash
python manage.py makemigrations organizations
python manage.py makemigrations insurance_app
python manage.py migrate
```

### 3. Set Up Default Groups
```bash
python manage.py setup_insurance_groups --create-sample-org
```

This command will create:
- Insurance Admins group
- Insurance Agents group
- Underwriters group
- Claims Adjusters group
- Fleet Managers group
- Sample insurance organization with linked groups

### 4. Add URLs to Main URLconf
Add to your main `urls.py`:
```python
path('organizations/', include('organizations.urls')),
```

## Usage Guide

### Creating Insurance Organizations

1. **Via Admin Interface:**
   - Go to Django Admin → Organizations → Organizations
   - Create new organization with `organization_type = 'insurance'`
   - Set `is_insurance_provider = True`
   - Select groups in the "Linked Groups" field
   - Insurance details will be created automatically

2. **Via Management Command:**
   ```bash
   python manage.py setup_insurance_groups --create-sample-org
   ```

### Linking Groups to Organizations

1. **In Admin Interface:**
   - Edit an organization
   - In the "Group Management" section, select desired groups
   - Save the organization
   - All active members will automatically be added to selected groups

2. **Admin Actions:**
   - Select organizations in the list view
   - Use "Sync members to linked groups" action
   - Use "Create insurance details for insurance providers" action

### Managing Organization Members

1. **Adding Users:**
   - Go to Organization Users in admin
   - Create new OrganizationUser record
   - User will automatically be added to organization's linked groups

2. **Removing Users:**
   - Set `is_active = False` or delete the OrganizationUser record
   - User will automatically be removed from organization's linked groups

### Group Permissions

The setup command creates groups with appropriate permissions:

- **Insurance Admins:** Full access to insurance policies, organizations, and risk alerts
- **Insurance Agents:** Can create/modify policies, view organizations
- **Underwriters:** Can assess risk, modify policies, view condition scores
- **Claims Adjusters:** Can view policies, manage accidents, view maintenance
- **Fleet Managers:** Can manage organization vehicles and view policies

## API Endpoints

### Template Views
- `/organizations/` - List all organizations
- `/organizations/<id>/` - Organization detail view
- `/organizations/insurance/dashboard/` - Insurance dashboard

### AJAX Endpoints
- `/organizations/ajax/available-groups/` - Get available Django groups
- `/organizations/ajax/<org_id>/link-group/` - Link group to organization

## Key Features

### Automatic Group Management
- Users are automatically added to organization's linked groups when they join
- Users are automatically removed from groups when they leave or become inactive
- Bulk sync functionality for existing members

### Insurance-Specific Features
- Extended insurance organization data
- Business metrics tracking
- Risk management settings
- Integration with insurance policies

### Admin Interface
- Visual indicators for insurance providers
- Group management interface
- Bulk actions for common tasks
- Comprehensive filtering and search

## Models Overview

### Organization
- Basic organization information
- Type classification
- Insurance provider flag
- Group linking functionality

### OrganizationUser
- User-organization relationships
- Role-based access
- Automatic group management

### InsuranceOrganization
- Extended insurance data
- Business metrics
- Risk settings
- Notification preferences

## Security Considerations

1. **Group Permissions:** Ensure groups have appropriate permissions before linking
2. **User Access:** Review user roles and group memberships regularly
3. **Insurance Data:** Protect sensitive insurance information with proper permissions
4. **Audit Trail:** Monitor group membership changes through Django admin logs

## Troubleshooting

### Common Issues

1. **Groups not syncing:**
   - Use admin action "Sync members to linked groups"
   - Check that users are active in the organization

2. **Insurance details missing:**
   - Use admin action "Create insurance details for insurance providers"
   - Ensure `is_insurance_provider = True`

3. **Permissions not working:**
   - Verify group permissions are set correctly
   - Check user group memberships in Django admin

### Migration Issues
If you encounter migration issues due to missing dependencies:
1. Install required packages: `pip install celery cloudinary`
2. Comment out problematic imports in settings.py temporarily
3. Run migrations
4. Uncomment imports after installation

## Future Enhancements

Potential improvements:
- Role-based group mapping (different groups for different roles)
- Organization hierarchy support
- Advanced permission management
- Integration with external insurance systems
- Automated compliance reporting