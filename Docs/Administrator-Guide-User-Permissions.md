# Administrator Guide: Managing User Permissions

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Understanding the Permission System](#understanding-the-permission-system)
4. [Daily Administrative Tasks](#daily-administrative-tasks)
5. [User Management Workflows](#user-management-workflows)
6. [Troubleshooting Common Issues](#troubleshooting-common-issues)
7. [Maintenance and Monitoring](#maintenance-and-monitoring)
8. [Best Practices](#best-practices)
9. [Emergency Procedures](#emergency-procedures)
10. [Reporting and Auditing](#reporting-and-auditing)

## Overview

This guide provides step-by-step instructions for administrators to manage user permissions in the Carfinity group-based authentication system. The system controls user access to different dashboards and features based on their group membership and organization association.

### Key Concepts
- **Groups**: Define user roles (customers, insurance_company)
- **Organizations**: Business entities users belong to
- **Dashboards**: Different interfaces users can access
- **Permissions**: Combination of groups and organization types that determine access

## Getting Started

### Accessing the Admin Interface

1. **Login to Admin**
   ```
   URL: https://your-domain.com/admin/
   Credentials: Use your staff/superuser account
   ```

2. **Navigate to Authentication Management**
   - From the admin dashboard, look for the "Group-Based Authentication Management" section
   - This provides quick access to all permission management tools

### Admin Dashboard Overview

The enhanced admin dashboard includes:
- **User Permissions Overview**: View all user permissions at a glance
- **Bulk User Management**: Perform operations on multiple users
- **Permission Conflicts Report**: Identify and resolve permission issues
- **Group-Organization Mapping**: Understand system relationships
- **Export User Permissions**: Generate reports for auditing

## Understanding the Permission System

### Group Types

#### 1. customers Group
- **Purpose**: For regular business users
- **Compatible Organizations**: 
  - Fleet Management
  - Dealership
  - Service Provider
  - Other
- **Dashboard Access**: Customer Dashboard (`/dashboard/`)

#### 2. insurance_company Group
- **Purpose**: For insurance company users
- **Compatible Organizations**: 
  - Insurance Company
- **Dashboard Access**: Insurance Dashboard (`/insurance-dashboard/`)

### Organization Types

| Organization Type | Compatible Groups | Default Dashboard |
|------------------|-------------------|-------------------|
| Fleet Management | customers | Customer Dashboard |
| Dealership | customers | Customer Dashboard |
| Service Provider | customers | Customer Dashboard |
| Insurance Company | insurance_company | Insurance Dashboard |
| Other | customers | Customer Dashboard |

### Permission Matrix

The system uses a permission matrix to determine access:

```
(Group, Organization Type) → Dashboard Access
├── (customers, fleet) → Customer Dashboard
├── (customers, dealership) → Customer Dashboard
├── (customers, service) → Customer Dashboard
├── (customers, other) → Customer Dashboard
├── (insurance_company, insurance) → Insurance Dashboard
└── (customers, insurance) → Both Dashboards (Selector)
```

## Daily Administrative Tasks

### 1. Checking System Health

**Frequency**: Daily (morning routine)

1. Navigate to **User Permissions Overview**
2. Review the statistics dashboard:
   - Total users
   - Users with groups
   - Users with organizations
3. Look for any red indicators (conflicts)

**What to Look For**:
- Users without groups (red indicators)
- Users without organizations
- Permission conflicts

### 2. Reviewing New User Registrations

**Frequency**: As needed when new users register

1. Go to **Users** in the admin
2. Filter by recent registrations (use date joined filter)
3. For each new user:
   - Verify they have appropriate groups
   - Confirm organization assignment
   - Check dashboard access

### 3. Monitoring Permission Conflicts

**Frequency**: Daily

1. Access **Permission Conflicts Report**
2. Review any users listed
3. Follow resolution steps for each conflict
4. Re-check after fixes are applied

## User Management Workflows

### Adding a New User

#### Step 1: Create User Account
1. Navigate to **Users** → **Add User**
2. Fill in required information:
   - Username
   - Email
   - Password
   - First/Last Name
3. Save the user

#### Step 2: Assign Groups
1. In the user edit form, scroll to **Groups**
2. Select appropriate group based on user role:
   - **customers**: For fleet, dealership, service users
   - **insurance_company**: For insurance company users
3. Save changes

#### Step 3: Associate with Organization
1. Navigate to **Organization Users** → **Add**
2. Select the user and organization
3. Choose appropriate role
4. Save the association

#### Step 4: Verify Permissions
1. Go to **User Permissions Overview**
2. Search for the new user
3. Verify:
   - Groups are correctly assigned
   - Organization is associated
   - Dashboard access is appropriate
   - No conflicts are shown

### Modifying Existing User Permissions

#### Changing User Groups
1. Navigate to **Users** and find the user
2. Edit the user
3. Modify **Groups** section
4. Save changes
5. Verify in **User Permissions Overview**

#### Changing Organization Assignment
1. Navigate to **Organization Users**
2. Find the user's organization assignment
3. Edit or delete/recreate as needed
4. Use **Sync with organization groups** action if needed

### Bulk Operations

#### Bulk Group Assignment
1. Go to **Bulk User Management**
2. Select users to modify
3. Choose "Add to group" action
4. Select the target group
5. Execute action
6. Verify results in **User Permissions Overview**

#### Bulk Organization Sync
1. Go to **Bulk User Management**
2. Select users to sync
3. Choose "Sync users with their organization groups"
4. Execute action
5. Check for any error messages

## Troubleshooting Common Issues

### Issue 1: User Can't Access Dashboard

**Symptoms**: User gets "Access Denied" error when trying to access dashboard

**Diagnosis Steps**:
1. Go to **User Permissions Overview**
2. Search for the user
3. Check the "Dashboard Access" column

**Common Causes & Solutions**:

#### No Groups Assigned
- **Cause**: User has no group membership
- **Solution**: 
  1. Edit user in **Users** admin
  2. Assign appropriate group (customers or insurance_company)
  3. Save changes

#### No Organization Assignment
- **Cause**: User not associated with any organization
- **Solution**:
  1. Go to **Organization Users** → **Add**
  2. Associate user with correct organization
  3. Save changes

#### Group-Organization Mismatch
- **Cause**: User's group doesn't match organization type
- **Solution**:
  1. Review user's organization type
  2. Assign correct group:
     - Insurance org → insurance_company group
     - Other orgs → customers group

### Issue 2: Permission Conflicts

**Symptoms**: User appears in Permission Conflicts Report

**Resolution Process**:
1. Access **Permission Conflicts Report**
2. Find the user in the list
3. Read the conflict details
4. Follow the recommended actions provided
5. Use quick action buttons to edit user/organization
6. Re-check conflicts after changes

### Issue 3: Bulk Operations Failing

**Symptoms**: Bulk actions don't complete or show errors

**Troubleshooting Steps**:
1. Verify all selected users exist and are active
2. Ensure target group exists (for group operations)
3. Check admin error messages
4. Try operation on smaller batches
5. Use management commands for detailed error analysis

### Issue 4: Organization Groups Not Syncing

**Symptoms**: Users not automatically getting organization groups

**Resolution Steps**:
1. Go to **Group-Organization Mapping**
2. Verify organization has linked groups
3. If no linked groups:
   - Edit organization in **Organizations** admin
   - Add appropriate groups to "Linked groups" field
4. Use "Sync members to linked groups" action
5. Verify users now have correct groups

## Maintenance and Monitoring

### Weekly Maintenance Tasks

#### 1. System Validation
```bash
# Run system validation command
python manage.py manage_auth_system validate-system --verbose
```

#### 2. Conflict Check
```bash
# Check for permission conflicts
python manage.py manage_auth_system check-conflicts --verbose
```

#### 3. Generate Reports
```bash
# Generate weekly permission report
python manage.py manage_auth_system generate-report --output weekly_report.csv
```

### Monthly Maintenance Tasks

#### 1. Full System Sync
```bash
# Sync all organization groups
python manage.py manage_auth_system sync-org-groups --verbose
```

#### 2. Comprehensive Audit
1. Export full permission report
2. Review for any anomalies
3. Document any changes made
4. Archive reports for compliance

### Monitoring Checklist

**Daily**:
- [ ] Check Permission Conflicts Report
- [ ] Review new user registrations
- [ ] Verify system statistics in User Permissions Overview

**Weekly**:
- [ ] Run system validation command
- [ ] Generate and review permission reports
- [ ] Check for users without groups/organizations

**Monthly**:
- [ ] Full system sync
- [ ] Comprehensive audit
- [ ] Review and update documentation
- [ ] Archive reports

## Best Practices

### User Management

1. **Consistent Group Assignment**
   - Always assign groups based on organization type
   - Use bulk operations for efficiency
   - Verify assignments after changes

2. **Organization Setup**
   - Link organizations to appropriate groups
   - Use descriptive organization names
   - Maintain accurate organization types

3. **Regular Auditing**
   - Export permission reports monthly
   - Review conflict reports daily
   - Document all changes

### Security Practices

1. **Access Control**
   - Limit admin access to necessary personnel
   - Use strong passwords for admin accounts
   - Regular review of admin user list

2. **Change Management**
   - Document all permission changes
   - Test changes in staging environment
   - Have rollback procedures ready

3. **Monitoring**
   - Set up alerts for permission conflicts
   - Monitor admin access logs
   - Regular security audits

### Performance Optimization

1. **Efficient Operations**
   - Use bulk operations for multiple users
   - Schedule maintenance during low-usage periods
   - Monitor system performance during operations

2. **Data Management**
   - Regular cleanup of inactive users
   - Archive old reports
   - Optimize database queries

## Emergency Procedures

### User Locked Out of System

**Immediate Actions**:
1. Verify user identity
2. Check **User Permissions Overview** for the user
3. Identify the issue (no groups, no org, conflicts)
4. Apply appropriate fix:
   - Add missing groups
   - Associate with organization
   - Resolve conflicts
5. Test user access
6. Document the incident

### Mass Permission Issues

**If Multiple Users Affected**:
1. Don't panic - assess the scope
2. Check **Permission Conflicts Report** for affected users
3. Identify common cause (org changes, group deletions, etc.)
4. Use bulk operations to fix:
   ```bash
   # Emergency sync all users
   python manage.py manage_auth_system sync-org-groups --verbose
   
   # Fix permissions automatically
   python manage.py manage_auth_system fix-permissions --fix --verbose
   ```
5. Verify fixes with system validation
6. Communicate with affected users
7. Document incident and prevention measures

### System Corruption

**If Permission System Appears Corrupted**:
1. **DO NOT** make bulk changes immediately
2. Export current state:
   ```bash
   python manage.py manage_auth_system generate-report --output emergency_backup.csv
   ```
3. Run system validation:
   ```bash
   python manage.py manage_auth_system validate-system --verbose
   ```
4. Contact technical team with validation results
5. Follow technical team guidance for recovery

## Reporting and Auditing

### Regular Reports

#### Daily Dashboard Check
- Access **User Permissions Overview**
- Note statistics and any red indicators
- Document any actions taken

#### Weekly Permission Report
```bash
# Generate weekly report
python manage.py manage_auth_system generate-report --output reports/weekly_$(date +%Y%m%d).csv
```

#### Monthly Audit Report
1. Generate comprehensive permission export
2. Review for:
   - Users without proper assignments
   - Unusual permission patterns
   - Inactive users with permissions
3. Document findings and actions

### Compliance Reporting

#### User Access Audit
- Export all user permissions
- Review against business requirements
- Document any exceptions or special cases
- Maintain audit trail of changes

#### Security Review
- Review admin access logs
- Check for unauthorized changes
- Verify all admin accounts are legitimate
- Document security incidents

### Report Templates

#### Daily Status Report
```
Date: [DATE]
Total Users: [NUMBER]
Users with Groups: [NUMBER]
Users with Organizations: [NUMBER]
Permission Conflicts: [NUMBER]
Actions Taken: [DESCRIPTION]
```

#### Weekly Summary Report
```
Week of: [DATE RANGE]
New Users Added: [NUMBER]
Permission Issues Resolved: [NUMBER]
Bulk Operations Performed: [NUMBER]
System Health: [GOOD/FAIR/POOR]
Recommendations: [LIST]
```

#### Monthly Audit Report
```
Month: [MONTH YEAR]
Total System Users: [NUMBER]
Permission Accuracy: [PERCENTAGE]
Security Incidents: [NUMBER]
System Changes: [DESCRIPTION]
Compliance Status: [COMPLIANT/NON-COMPLIANT]
Action Items: [LIST]
```

## Quick Reference

### Common Admin URLs
- User Permissions Overview: `/admin/users/user-permissions/`
- Bulk Management: `/admin/users/bulk-management/`
- Permission Conflicts: `/admin/users/permission-conflicts/`
- Group-Org Mapping: `/admin/users/group-org-mapping/`
- Export Permissions: `/admin/users/export-permissions/`

### Essential Commands
```bash
# Check system health
python manage.py manage_auth_system validate-system

# Fix permission issues
python manage.py manage_auth_system fix-permissions --fix

# Generate report
python manage.py manage_auth_system generate-report --output report.csv

# Sync organization groups
python manage.py manage_auth_system sync-org-groups
```

### Status Indicators
- 🟢 **Green**: Good status, no issues
- 🟡 **Yellow**: Warning, attention needed
- 🔴 **Red**: Error, immediate action required
- 🔵 **Blue**: Informational, no action needed

### Emergency Contacts
- Technical Team: [CONTACT INFO]
- System Administrator: [CONTACT INFO]
- Security Team: [CONTACT INFO]

---

**Remember**: When in doubt, document your actions and consult with the technical team. It's better to ask for help than to make changes that could affect multiple users.