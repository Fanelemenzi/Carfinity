# Configurable Group-Based Authentication Setup

This document describes the setup and configuration of the flexible group-based authentication system that allows administrators to dynamically configure authentication groups without code changes.

## System Overview

The authentication system now uses **configurable authentication groups** instead of hardcoded groups. Administrators can:
- Create any number of authentication groups
- Configure dashboard access for each group
- Set priorities for multi-group users
- Define organization type compatibility
- Enable/disable groups without deletion

## Default Authentication Groups

The system comes with two default authentication groups that can be customized:

### 1. Customer Users (customers group)
- **Purpose**: Regular customers accessing vehicle and maintenance information
- **Dashboard**: Customer Dashboard (`/dashboard/`)
- **Priority**: 1 (lower priority)
- **Compatible Organizations**: fleet, dealership, service, other

### 2. Insurance Company Users (insurance_company group)
- **Purpose**: Insurance company users accessing policies and risk assessments
- **Dashboard**: Insurance Dashboard (`/insurance/`)
- **Priority**: 2 (higher priority - becomes default for multi-group users)
- **Compatible Organizations**: insurance

## Initial Setup Instructions

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup command to create default authentication groups
python manage.py setup_auth_groups

# To reset and recreate all configurations
python manage.py setup_auth_groups --reset
```

### Option 2: Manual Django Admin Setup
1. Log into Django Admin as a superuser
2. Navigate to **"Authentication Group Management"** in the main admin dashboard
3. Click **"Setup Default Groups"** or manually add authentication groups
4. Configure each group's dashboard access and settings

### Option 3: Legacy Group Setup
```bash
# Create basic Django groups (legacy method)
python manage.py setup_groups
```

## Authentication Group Configuration

### Creating New Authentication Groups

1. **Access Authentication Group Management**:
   - Go to Django Admin → **"Group-Based Authentication Management"**
   - Click **"Authentication Group Management"**

2. **Create Django Group** (if needed):
   - Go to **Groups** → **Add Group**
   - Create the base Django group (e.g., "technicians", "managers")

3. **Configure Authentication Group**:
   - Go to **Authentication Group Configurations** → **Add Authentication Group Configuration**
   - Link to the Django group
   - Configure dashboard access and settings

### Configuration Options

#### Dashboard Types
- **customer** - Customer dashboard for vehicle/maintenance access
- **insurance** - Insurance dashboard for policies and risk assessment
- **admin** - Administrative dashboard with full system access
- **technician** - Service technician dashboard for maintenance tools
- **custom** - Custom dashboard implementations

#### Priority System
- Higher priority groups become the default dashboard for multi-group users
- Priority 1 = lowest, higher numbers = higher priority
- Example: insurance_company (priority 2) overrides customers (priority 1)

#### Organization Compatibility
Configure which organization types automatically get assigned to each group:
```json
["insurance", "fleet", "dealership", "service", "other"]
```

### Example Configurations

#### Service Technician Group
```
Group: technicians
Display Name: Service Technicians
Dashboard Type: technician
Dashboard URL: /technician/
Priority: 1
Compatible Org Types: ["service", "dealership"]
```

#### Fleet Manager Group
```
Group: fleet_managers
Display Name: Fleet Managers
Dashboard Type: customer
Dashboard URL: /fleet-dashboard/
Priority: 3
Compatible Org Types: ["fleet"]
```

## User Assignment Methods

### 1. Automatic Assignment (Recommended)
- Users are automatically assigned to groups based on their organization type
- Configured through **Organization Group Management**
- Uses the compatibility settings from authentication group configurations

### 2. Manual Assignment
- **Django Admin**: Edit user → Groups section → Add to groups
- **Bulk Management**: Use **Bulk User Management** for multiple users
- **Organization Admin**: Manage through organization member management

### 3. Organization-Based Assignment
- **Organization Linking**: Organizations can be linked to specific groups
- **Auto-sync**: Members automatically get organization's linked groups
- **Compatibility Matching**: System recommends groups based on organization type

## Enhanced Authentication Flow

1. **User Login**: User submits credentials
2. **Group Resolution**: System checks user's authentication groups (not just Django groups)
3. **Dashboard Selection**:
   - Single active group → Direct redirect to group's dashboard
   - Multiple active groups → Dashboard selector or highest priority dashboard
   - No active groups → Error page with guidance
4. **Permission Validation**: Ongoing validation using configurable group permissions
5. **Conflict Resolution**: System handles conflicts between group and organization permissions

## Administrative Tools

### Authentication Group Management (`/admin/users/auth-group-management/`)
- **Overview Dashboard**: Statistics and group status
- **Configuration Testing**: Test group configurations for conflicts
- **Bulk Operations**: Activate/deactivate multiple groups
- **Unconfigured Groups**: Identify Django groups needing authentication configuration

### User Permissions Overview (`/admin/users/user-permissions/`)
- **User Dashboard Access**: See which dashboards each user can access
- **Group Sync Status**: Identify users with sync issues
- **Conflict Detection**: Find and resolve permission conflicts
- **Bulk User Management**: Perform bulk operations on user groups

### Organization Group Management (`/admin/organizations/group-management/`)
- **Organization-Group Links**: Visual mapping of organization-group relationships
- **Member Sync Status**: See which organization members need group sync
- **Automatic Recommendations**: System suggests appropriate groups for organizations
- **One-click Sync**: Fix sync issues with single button clicks

## URL Configuration (Dynamic)

The system now dynamically generates URL patterns based on authentication group configurations:

### Default URLs
- `/login/` - Login page
- `/logout/` - Logout functionality  
- `/register/` - User registration
- `/dashboard-selector/` - Multi-dashboard selection (when user has multiple groups)

### Configurable Dashboard URLs
- Configured per authentication group
- Examples: `/dashboard/`, `/insurance/`, `/technician/`, `/fleet-dashboard/`
- System validates URL format and checks for conflicts

## Management Commands

### Setup Authentication Groups
```bash
# Create default authentication group configurations
python manage.py setup_auth_groups

# Reset all configurations and recreate defaults
python manage.py setup_auth_groups --reset
```

### Legacy Group Setup
```bash
# Create basic Django groups (for backward compatibility)
python manage.py setup_groups
```

### System Management
```bash
# Check for permission conflicts
python manage.py manage_auth_system check-conflicts

# Fix permission issues automatically  
python manage.py manage_auth_system fix-permissions --fix

# Generate comprehensive permission report
python manage.py manage_auth_system generate-report --output report.csv

# Validate entire authentication system
python manage.py manage_auth_system validate-system
```

## Security Features

### Enhanced Security
- **Dynamic permission validation** using configurable groups
- **Priority-based access control** prevents unauthorized dashboard access
- **Organization-group compatibility validation** ensures proper access levels
- **Conflict detection and resolution** for complex permission scenarios
- **Audit trail** for all authentication group configuration changes

### Access Control
- **Active/Inactive groups**: Disable groups without deleting configurations
- **URL validation**: Ensures dashboard URLs are properly formatted
- **Conflict prevention**: System detects and warns about conflicting configurations
- **Fallback mechanisms**: Falls back to default behavior if configurations are missing

### Session Management
- **Secure logout** with session cleanup
- **Multi-dashboard session handling** for users with multiple group access
- **Permission caching** for improved performance
- **Real-time permission updates** when group configurations change

## Migration from Legacy System

### For Existing Installations
1. **Run setup command**: `python manage.py setup_auth_groups`
2. **Verify configurations**: Check Authentication Group Management dashboard
3. **Test user access**: Ensure existing users can still access their dashboards
4. **Customize as needed**: Modify configurations through admin interface

### Backward Compatibility
- System falls back to hardcoded mappings if no configurations exist
- Existing Django groups continue to work
- Legacy management commands still function
- No breaking changes to existing user assignments

## Troubleshooting

### Common Issues
1. **Users can't access dashboards**: Check if authentication groups are active and properly configured
2. **Wrong dashboard redirect**: Verify group priorities and user group assignments
3. **Organization sync issues**: Use bulk sync actions in organization management
4. **URL conflicts**: Check for duplicate dashboard URLs in authentication group configurations

### Diagnostic Tools
- **Test Config button**: Test individual authentication group configurations
- **Permission Conflicts Report**: Identify and resolve permission conflicts
- **User Permissions Overview**: See detailed permission status for all users
- **System validation command**: Comprehensive system health check