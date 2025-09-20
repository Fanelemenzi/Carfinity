# Administrator Guide: Setting Up Authentication Groups

This guide provides step-by-step instructions for administrators to configure how groups are used to authenticate users and control dashboard access in the Carfinity system.

## Table of Contents

1. [Quick Start Setup](#quick-start-setup)
2. [Understanding Authentication Groups](#understanding-authentication-groups)
3. [Step-by-Step Configuration](#step-by-step-configuration)
4. [Managing User Access](#managing-user-access)
5. [Organization Integration](#organization-integration)
6. [Advanced Configuration](#advanced-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Quick Start Setup

### Option 1: Automated Setup (Recommended for New Installations)

1. **Run the setup command**:
   ```bash
   python manage.py setup_auth_groups
   ```
   This creates default authentication groups for customers and insurance companies.

2. **Access the admin interface**:
   - Go to `/admin/` and log in as a superuser
   - You'll see "Group-Based Authentication Management" section on the main page

3. **Verify setup**:
   - Click "Authentication Group Management"
   - You should see two configured groups: "Customer Users" and "Insurance Company Users"

### Option 2: Manual Setup

If you prefer to configure everything manually, follow the [Step-by-Step Configuration](#step-by-step-configuration) section below.

## Understanding Authentication Groups

### What are Authentication Groups?

Authentication Groups are configurations that link Django Groups to specific dashboards and define how users get access to different parts of the system.

**Key Components:**
- **Django Group**: The base user group (e.g., "customers", "technicians")
- **Dashboard Type**: What kind of dashboard (customer, insurance, admin, technician, custom)
- **Dashboard URL**: Where users go after login (e.g., `/dashboard/`, `/insurance/`)
- **Priority**: Which dashboard is default if user has multiple groups
- **Organization Compatibility**: Which organization types automatically get this group

### How Authentication Works

1. **User logs in** → System checks their Django groups
2. **Group lookup** → System finds active Authentication Group configurations for user's groups
3. **Dashboard routing** → User is redirected based on group configuration and priority
4. **Access control** → System validates access to protected URLs based on group membership

## Step-by-Step Configuration

### Step 1: Create Django Groups

1. **Access Django Admin**:
   - Go to `/admin/`
   - Navigate to **"Authentication and Authorization"** → **"Groups"**

2. **Create a new group**:
   - Click **"Add Group"**
   - Enter group name (e.g., "technicians", "fleet_managers", "claims_adjusters")
   - Optionally add permissions (for Django model access)
   - Click **"Save"**

3. **Repeat for all needed groups**:
   - Create all the groups you need for your organization
   - Common examples: customers, insurance_company, technicians, managers, admins

### Step 2: Configure Authentication Groups

1. **Access Authentication Group Management**:
   - From admin home, click **"Authentication Group Management"**
   - Or go to **"Authentication Group Configurations"** → **"Add Authentication Group Configuration"**

2. **Create Authentication Group Configuration**:
   - **Group**: Select the Django group you created
   - **Display Name**: Human-readable name (e.g., "Service Technicians")
   - **Description**: What this group provides access to
   - **Dashboard Type**: Select appropriate type:
     - `customer` - For customers accessing vehicle/maintenance info
     - `insurance` - For insurance company users
     - `admin` - For administrative users
     - `technician` - For service technicians
     - `custom` - For custom implementations
   - **Dashboard URL**: Where users go after login (e.g., `/technician/`)
   - **Priority**: Higher numbers = higher priority (default dashboard for multi-group users)
   - **Compatible Org Types**: JSON array of organization types (e.g., `["service", "dealership"]`)
   - **Is Active**: Check to enable this configuration

3. **Save the configuration**

### Step 3: Test the Configuration

1. **Use the Test Config button**:
   - In Authentication Group Management, click **"Test Config"** for your new group
   - This validates the configuration and checks for conflicts

2. **Check for issues**:
   - URL format validation
   - Conflicts with other groups
   - Organization compatibility

## Managing User Access

### Method 1: Direct User Assignment

1. **Edit individual users**:
   - Go to **"Users"** → Select a user
   - Scroll to **"Groups"** section
   - Add user to appropriate groups
   - Save

2. **View user permissions**:
   - Use **"User Permissions Overview"** to see all users and their dashboard access
   - Filter by group or organization type
   - Identify users with conflicts or no access

### Method 2: Bulk User Management

1. **Access bulk management**:
   - Go to **"Bulk User Management"**
   - Select multiple users using checkboxes

2. **Perform bulk actions**:
   - **Add to group**: Add selected users to a specific group
   - **Remove from group**: Remove selected users from a group
   - **Sync org groups**: Sync users with their organization's linked groups
   - **Check permissions**: Validate permissions for selected users

### Method 3: Organization-Based Assignment (Recommended)

1. **Configure organization group links**:
   - Go to **"Organizations"** → Select an organization
   - In **"Group Management"** section, select **"Linked Groups"**
   - Choose which groups members of this organization should automatically get

2. **Use auto-assignment**:
   - Use **"Auto-assign recommended groups"** action to automatically link organizations to appropriate groups based on their type

3. **Sync members**:
   - Use **"Sync members to linked groups"** to ensure all organization members have the correct groups

## Organization Integration

### Setting Up Organization-Group Links

1. **Access Organization Group Management**:
   - Go to **"Organization Group Management"**
   - See visual overview of all organization-group relationships

2. **Configure organization compatibility**:
   - In Authentication Group configurations, set **"Compatible Org Types"**
   - Example: `["insurance"]` for insurance company groups
   - Example: `["fleet", "dealership", "service"]` for customer groups

3. **Automatic recommendations**:
   - System will suggest appropriate groups for organizations based on their type
   - Use **"Auto-assign recommended groups"** for bulk setup

### Organization Types and Recommended Groups

| Organization Type | Recommended Groups | Dashboard Access |
|------------------|-------------------|------------------|
| `insurance` | insurance_company | Insurance Dashboard |
| `fleet` | customers | Customer Dashboard |
| `dealership` | customers, technicians | Customer + Technician |
| `service` | customers, technicians | Customer + Technician |
| `other` | customers | Customer Dashboard |

## Advanced Configuration

### Creating Custom Dashboard Types

1. **Add new dashboard type**:
   - Create Authentication Group with `dashboard_type = "custom"`
   - Set custom `dashboard_url` (e.g., `/fleet-management/`)

2. **Implement dashboard view**:
   - Create Django view for your custom dashboard
   - Add URL pattern in your app's urls.py
   - Ensure proper permission checking

### Multi-Group Users

1. **Priority system**:
   - Users with multiple groups get routed to highest priority group's dashboard
   - Set priorities: 1 (lowest) to 10 (highest)

2. **Dashboard selector**:
   - Users with multiple groups can access `/dashboard-selector/` to choose
   - System automatically provides this for multi-group users

### Custom Organization Types

1. **Add new organization types**:
   - Modify `Organization.ORGANIZATION_TYPES` in organizations/models.py
   - Update Authentication Group compatibility settings

2. **Configure group compatibility**:
   - Update `compatible_org_types` in Authentication Group configurations
   - Use organization admin to link new organization types to appropriate groups

## Troubleshooting

### Common Issues and Solutions

#### Users Can't Access Dashboards

**Problem**: User gets "No Groups" or "Access Denied" error

**Solutions**:
1. Check if user is assigned to any groups: **Users** → Edit user → **Groups** section
2. Verify groups have active Authentication Group configurations: **Authentication Group Management**
3. Check if Authentication Groups are active: Edit configuration → **Is Active** checkbox
4. Validate dashboard URLs: Use **Test Config** button

#### Wrong Dashboard Redirect

**Problem**: User goes to wrong dashboard after login

**Solutions**:
1. Check group priorities: Higher priority groups become default
2. Verify user's group assignments: **User Permissions Overview**
3. Check for conflicts: **Permission Conflicts Report**
4. Review organization group links if using organization-based assignment

#### Organization Sync Issues

**Problem**: Organization members don't have expected groups

**Solutions**:
1. Check organization's linked groups: **Organizations** → Edit organization → **Linked Groups**
2. Use **"Sync members to linked groups"** action
3. Verify organization type compatibility in Authentication Group configurations
4. Check **Organization Group Management** for sync status

#### URL Conflicts

**Problem**: Multiple groups have same dashboard URL

**Solutions**:
1. Use **Test Config** to identify conflicts
2. Change dashboard URLs to be unique for each group
3. Review **Authentication Group Management** for duplicate URLs

### Diagnostic Tools

1. **Test Config Button**: Test individual Authentication Group configurations
2. **User Permissions Overview**: See detailed permission status for all users
3. **Permission Conflicts Report**: Identify and resolve permission conflicts
4. **Organization Group Management**: Visual overview of organization-group relationships

### Management Commands for Troubleshooting

```bash
# Check for system-wide permission conflicts
python manage.py manage_auth_system check-conflicts

# Fix permission issues automatically
python manage.py manage_auth_system fix-permissions --fix

# Generate comprehensive report
python manage.py manage_auth_system generate-report --output report.csv

# Validate entire system
python manage.py manage_auth_system validate-system
```

## Best Practices

### Group Design

1. **Keep it simple**: Start with basic groups (customers, insurance_company) and add more as needed
2. **Clear naming**: Use descriptive group names that reflect their purpose
3. **Logical priorities**: Set priorities that make sense for your users (insurance > customer for insurance company employees)

### Organization Integration

1. **Use organization-based assignment**: More maintainable than manual user assignment
2. **Set up compatibility correctly**: Ensure organization types map to appropriate groups
3. **Regular sync**: Use bulk sync actions to keep organization members up to date

### Security

1. **Regular audits**: Use Permission Conflicts Report to identify issues
2. **Test configurations**: Always test new Authentication Group configurations
3. **Monitor access**: Use User Permissions Overview to monitor user access patterns

### Maintenance

1. **Document custom configurations**: Keep notes on any custom dashboard types or organization types
2. **Regular cleanup**: Deactivate unused Authentication Groups instead of deleting them
3. **Backup configurations**: Export user permissions regularly for backup purposes

### Scaling

1. **Plan for growth**: Design group structure that can accommodate new user types
2. **Use priorities effectively**: Plan priority system for complex multi-group scenarios
3. **Automate where possible**: Use organization-based assignment and bulk operations

## Example Scenarios

### Scenario 1: Adding Service Technicians

**Goal**: Create access for service technicians who need a specialized dashboard

**Steps**:
1. Create Django group: "technicians"
2. Create Authentication Group:
   - Group: technicians
   - Display Name: "Service Technicians"
   - Dashboard Type: technician
   - Dashboard URL: /technician/
   - Priority: 1
   - Compatible Org Types: ["service", "dealership"]
3. Link service organizations to technicians group
4. Sync organization members

### Scenario 2: Multi-Role Insurance Company

**Goal**: Insurance company employees who need both insurance and customer access

**Steps**:
1. Ensure both "insurance_company" and "customers" groups exist
2. Set priorities: insurance_company (priority 2), customers (priority 1)
3. Add insurance company users to both groups
4. Users will default to insurance dashboard but can access customer dashboard via selector

### Scenario 3: Fleet Management Company

**Goal**: Fleet company with managers and drivers needing different access levels

**Steps**:
1. Create groups: "fleet_managers", "fleet_drivers"
2. Create Authentication Groups:
   - Fleet Managers: priority 3, dashboard /fleet-management/
   - Fleet Drivers: priority 1, dashboard /driver/
3. Set organization compatibility: both compatible with "fleet" organization type
4. Link fleet organizations to both groups
5. Manually assign users to appropriate roles within the organization

This guide provides comprehensive instructions for setting up and managing authentication groups. Start with the Quick Start section and refer to specific sections as needed for your use case.