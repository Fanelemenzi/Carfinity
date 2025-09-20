# Quick Setup Guide: Group-Based Authentication

This is a practical, step-by-step guide for administrators to quickly set up group-based authentication in Carfinity. For detailed explanations, see the [comprehensive Admin Guide](Admin-Guide-Authentication-Groups.md).

## Prerequisites

- Django admin superuser access
- Basic understanding of Django groups and users

## 5-Minute Quick Setup

### Step 1: Run Automated Setup (Recommended)
```bash
python manage.py setup_auth_groups
```
This creates default configurations for customers and insurance companies.

### Step 2: Access Admin Interface
1. Go to `/admin/` and log in as superuser
2. Look for **"Group-Based Authentication Management"** section on main page
3. Click **"Authentication Group Management"**

### Step 3: Verify Default Setup
You should see two configured groups:
- **Customer Users** (customers group) → `/dashboard/` (Priority 1)
- **Insurance Company Users** (insurance_company group) → `/insurance/` (Priority 2)

### Step 4: Test Configuration
1. Click **"Test Config"** button for each group
2. Verify no conflicts or errors appear
3. Check that dashboard URLs are accessible

**✅ Basic setup complete! Users can now be assigned to groups and will be routed to appropriate dashboards.**

---

## Adding Custom Groups (10 minutes)

### Example: Adding Service Technicians

#### Step 1: Create Django Group
1. Go to **Authentication and Authorization** → **Groups**
2. Click **"Add Group"**
3. Name: `technicians`
4. Save

#### Step 2: Configure Authentication Group
1. Go to **Authentication Group Configurations** → **"Add Authentication Group Configuration"**
2. Fill in:
   - **Group**: technicians
   - **Display Name**: Service Technicians
   - **Description**: Access to technician tools and maintenance dashboard
   - **Dashboard Type**: technician
   - **Dashboard URL**: `/technician/`
   - **Priority**: 1
   - **Compatible Org Types**: `["service", "dealership"]`
   - **Is Active**: ✓ checked
3. Save

#### Step 3: Test New Group
1. Click **"Test Config"** for the new technicians group
2. Verify no conflicts

#### Step 4: Assign Users
**Option A - Individual Assignment:**
1. Go to **Users** → Select user
2. In **Groups** section, add user to "technicians" group
3. Save

**Option B - Organization-Based (Recommended):**
1. Go to **Organizations** → Select service organization
2. In **Group Management** section, add "technicians" to **Linked Groups**
3. Click **"Sync members to linked groups"**

---

## Common Setup Scenarios

### Scenario 1: Insurance Company with Multiple Roles
**Goal**: Insurance employees need both insurance and customer access

**Quick Setup**:
1. Add users to both `insurance_company` and `customers` groups
2. They'll default to insurance dashboard (higher priority)
3. Can access customer dashboard via `/dashboard-selector/`

### Scenario 2: Fleet Management Company
**Goal**: Fleet company with managers and drivers

**Quick Setup**:
1. Create groups: `fleet_managers`, `fleet_drivers`
2. Configure authentication groups:
   - Fleet Managers: `/fleet-management/`, priority 3
   - Fleet Drivers: `/driver/`, priority 1
3. Set both compatible with `["fleet"]` organization type
4. Link fleet organization to both groups

### Scenario 3: Service Center with Multiple Access Levels
**Goal**: Service center with technicians, managers, and customer service

**Quick Setup**:
1. Create groups: `technicians`, `service_managers`, `customer_service`
2. Configure different dashboard URLs and priorities
3. Set all compatible with `["service"]` organization type
4. Use organization-based assignment

---

## User Assignment Quick Reference

### Method 1: Direct User Assignment
```
Admin → Users → [Select User] → Groups → Add to group → Save
```

### Method 2: Organization-Based (Recommended)
```
Admin → Organizations → [Select Org] → Linked Groups → Select groups → Save
Then: Click "Sync members to linked groups"
```

### Method 3: Bulk Assignment
```
Admin → Bulk User Management → Select users → Choose action → Apply
```

---

## Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| User gets "No Groups" error | Add user to a group with active authentication configuration |
| User goes to wrong dashboard | Check group priorities (higher number = higher priority) |
| "Access Denied" error | Verify authentication group is active and dashboard URL exists |
| Organization members missing groups | Use "Sync members to linked groups" in organization admin |
| URL conflicts | Check for duplicate dashboard URLs in authentication configurations |

### Diagnostic Tools
- **Test Config** button: Test individual group configurations
- **User Permissions Overview**: See all user permissions at a glance
- **Organization Group Management**: Visual overview of org-group relationships

---

## Management Commands Quick Reference

```bash
# Initial setup (run once)
python manage.py setup_auth_groups

# Reset all configurations
python manage.py setup_auth_groups --reset

# Check for conflicts
python manage.py manage_auth_system check-conflicts

# Fix permission issues
python manage.py manage_auth_system fix-permissions --fix

# Generate report
python manage.py manage_auth_system generate-report --output report.csv
```

---

## Default Group Configurations

| Group | Dashboard Type | URL | Priority | Compatible Orgs |
|-------|---------------|-----|----------|-----------------|
| customers | customer | /dashboard/ | 1 | fleet, dealership, service, other |
| insurance_company | insurance | /insurance/ | 2 | insurance |

---

## Next Steps

1. **Test with real users**: Create test users and verify they can access correct dashboards
2. **Set up organizations**: Link organizations to appropriate groups for automatic user assignment
3. **Customize dashboards**: Ensure dashboard URLs exist and provide appropriate functionality
4. **Monitor access**: Use admin tools to monitor user access patterns and resolve conflicts

For detailed explanations, advanced configurations, and troubleshooting, see the [comprehensive Admin Guide](Admin-Guide-Authentication-Groups.md).