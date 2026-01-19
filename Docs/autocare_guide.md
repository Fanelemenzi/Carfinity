# Django Auto Care Platform - Calendar Scheduling Integration Guide

## Overview

This guide details how to integrate an automated calendar scheduling system into an **existing** Django auto care platform that already has Vehicle and Maintenance apps. The calendar system will:

- Schedule initial full inspections on vehicle onboarding
- Schedule minor inspections every 4 months (3 inspections per year)
- Schedule maintenance activities based on existing maintenance schedule templates
- Provide calendar views and APIs for all scheduled activities

## Prerequisites

Your existing platform must have:
- **Vehicle App**: With vehicle models containing at least `onboarding_date` field
- **Maintenance App**: With maintenance-related models and schedule templates
- Django 4.2+
- Django REST Framework (for API endpoints)

---

## Integration Strategy

### Phase 1: Analyze Existing Apps
### Phase 2: Create New Calendar App
### Phase 3: Extend Existing Models (Non-Invasive)
### Phase 4: Create Scheduling Services
### Phase 5: Integrate with Existing Apps
### Phase 6: Add API Endpoints
### Phase 7: Testing & Validation

---

## PHASE 1: Analyze Existing Apps

### Step 1.1: Document Existing Vehicle App Structure

**Action Required**: Examine your existing `vehicles` app and document:

```python
# Expected existing structure in vehicles/models.py
class Vehicle(models.Model):
    # Document these fields:
    # - Primary key field name (usually 'id')
    # - VIN or unique identifier field
    # - Make, model, year fields
    # - onboarding_date field (CRITICAL - needed for scheduling)
    # - is_active or status field
    # - Any related_name configurations
    pass
```

**Checklist**:
- [ ] Vehicle model has `onboarding_date` DateField
- [ ] Vehicle model has active/status indicator
- [ ] Identify primary key field name
- [ ] Document any custom managers or querysets
- [ ] Note any existing related_name attributes that might conflict

**Example Documentation**:
```markdown
Existing Vehicle Model Fields:
- id: AutoField (PK)
- vin: CharField(max_length=17, unique=True)
- make: CharField(max_length=50)
- model: CharField(max_length=50)
- year: IntegerField()
- license_plate: CharField(max_length=20)
- onboarding_date: DateField() ✓ EXISTS
- status: CharField(choices=['active', 'inactive']) ✓ EXISTS
- Related name conflicts: None found
```

### Step 1.2: Document Existing Maintenance App Structure

**Action Required**: Examine your existing `maintenance` app:

```python
# Expected existing structure in maintenance/models.py
class MaintenanceActivity(models.Model):
    # Document these fields:
    # - Name of maintenance type
    # - Category or type classification
    # - Any duration/time estimates
    pass

class MaintenanceSchedule(models.Model):
    # Document these fields:
    # - Reference to maintenance activity
    # - Interval configuration (days, months, mileage)
    # - Active status
    pass
```

**Checklist**:
- [ ] Maintenance activity/type model exists
- [ ] Maintenance schedule template exists
- [ ] Document field names for intervals (days/months)
- [ ] Note any existing calendar/scheduling features
- [ ] Check for any inspection-related models

**Example Documentation**:
```markdown
Existing Maintenance Models:
- MaintenanceType: Contains service types (oil change, tire rotation, etc.)
  - Fields: name, category, estimated_duration
- MaintenanceScheduleTemplate: Contains recurring schedules
  - Fields: maintenance_type_fk, interval_months, is_active
- No existing calendar/scheduling system found ✓
```

---

## PHASE 2: Create New Calendar App

### Step 2.1: Create Calendar Django App

```bash
# Create new calendar app
python manage.py startapp calendar_scheduler

# Create service directory for business logic
mkdir calendar_scheduler/services
touch calendar_scheduler/services/__init__.py
```

### Step 2.2: Register App in Settings

**File**: `config/settings.py` or your main settings file

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'vehicles',  # Your existing app
    'maintenance',  # Your existing app
    'calendar_scheduler',  # NEW: Calendar scheduling app
    # ... other apps ...
]
```

### Step 2.3: Create Calendar Models

**File**: `calendar_scheduler/models.py`

```python
from django.db import models
from django.utils import timezone
from django.conf import settings

# Import existing models - ADJUST IMPORTS TO YOUR STRUCTURE
from vehicles.models import Vehicle
from maintenance.models import MaintenanceType, MaintenanceScheduleTemplate


class ActivityType(models.Model):
    """
    Defines types of schedulable activities (inspections + maintenance).
    This wraps your existing MaintenanceType and adds inspection types.
    """
    INSPECTION = 'inspection'
    MAINTENANCE = 'maintenance'
    
    ACTIVITY_CATEGORIES = [
        (INSPECTION, 'Inspection'),
        (MAINTENANCE, 'Maintenance'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=ACTIVITY_CATEGORIES)
    description = models.TextField(blank=True)
    estimated_duration = models.DurationField(
        help_text="Expected time to complete"
    )
    
    # Link to existing maintenance type if applicable
    maintenance_type = models.OneToOneField(
        MaintenanceType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_activity_type',
        help_text="Link to existing maintenance type"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
        db_table = 'calendar_activity_type'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ScheduledActivity(models.Model):
    """
    Core calendar model: individual scheduled events for vehicles.
    This is the calendar system's main table.
    """
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    MISSED = 'missed'
    CANCELLED = 'cancelled'
    IN_PROGRESS = 'in_progress'
    
    STATUS_CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (MISSED, 'Missed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    # Link to existing Vehicle model
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='calendar_scheduled_activities'  # Unique name to avoid conflicts
    )
    
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.CASCADE
    )
    
    scheduled_date = models.DateField(db_index=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=SCHEDULED,
        db_index=True
    )
    
    completed_date = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_activities'
    )
    
    notes = models.TextField(blank=True)
    
    # Tracking fields for recurring activities
    is_initial_inspection = models.BooleanField(
        default=False,
        help_text="True if this is the onboarding inspection"
    )
    
    recurrence_number = models.IntegerField(
        default=0,
        help_text="Which occurrence: 0=first, 1=second, etc."
    )
    
    # Link to existing maintenance schedule template
    maintenance_schedule = models.ForeignKey(
        MaintenanceScheduleTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_scheduled_activities',
        help_text="Source template that created this activity"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['vehicle', 'scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['scheduled_date', 'status']),
        ]
        db_table = 'calendar_scheduled_activity'
        verbose_name_plural = "Scheduled Activities"
    
    def __str__(self):
        return f"{self.vehicle} - {self.activity_type.name} on {self.scheduled_date}"
    
    def mark_completed(self, user=None, notes=""):
        """Helper method to mark activity as completed"""
        self.status = self.COMPLETED
        self.completed_date = timezone.now()
        self.completed_by = user
        if notes:
            self.notes = notes
        self.save()


class CalendarSettings(models.Model):
    """
    Configuration settings for the calendar system.
    Singleton model - only one instance should exist.
    """
    inspection_interval_months = models.IntegerField(
        default=4,
        help_text="Interval for minor inspections in months"
    )
    
    schedule_horizon_months = models.IntegerField(
        default=12,
        help_text="How many months ahead to schedule activities"
    )
    
    auto_schedule_on_onboarding = models.BooleanField(
        default=True,
        help_text="Automatically schedule activities when vehicle is onboarded"
    )
    
    send_reminders = models.BooleanField(
        default=True,
        help_text="Send reminder notifications for upcoming activities"
    )
    
    reminder_days_before = models.IntegerField(
        default=3,
        help_text="Days before activity to send reminder"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'calendar_settings'
        verbose_name_plural = "Calendar Settings"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion"""
        pass
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
```

### Step 2.4: Create Initial Migration

```bash
python manage.py makemigrations calendar_scheduler
python manage.py migrate
```

---

## PHASE 3: Extend Existing Models (Non-Invasive)

### Step 3.1: Add Helper Methods to Vehicle Model

**Important**: Do NOT modify the existing Vehicle model fields directly. Instead, add methods via model inheritance or use managers.

**Option A: Create Proxy Model** (Recommended - Non-Invasive)

**File**: `calendar_scheduler/models.py` (add to existing file)

```python
class VehicleCalendarProxy(Vehicle):
    """
    Proxy model for Vehicle that adds calendar-specific methods.
    Does not create a new database table.
    """
    class Meta:
        proxy = True
    
    def get_scheduled_activities(self, start_date=None, end_date=None):
        """Get all scheduled activities for this vehicle"""
        from .models import ScheduledActivity
        
        queryset = ScheduledActivity.objects.filter(vehicle=self)
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        return queryset.order_by('scheduled_date')
    
    def get_next_activity(self):
        """Get the next upcoming scheduled activity"""
        from .models import ScheduledActivity
        today = timezone.now().date()
        
        return ScheduledActivity.objects.filter(
            vehicle=self,
            status=ScheduledActivity.SCHEDULED,
            scheduled_date__gte=today
        ).order_by('scheduled_date').first()
    
    def has_initial_inspection_scheduled(self):
        """Check if initial inspection is already scheduled"""
        from .models import ScheduledActivity
        return ScheduledActivity.objects.filter(
            vehicle=self,
            is_initial_inspection=True
        ).exists()
```

**Option B: Monkey Patch Methods** (Alternative)

**File**: `calendar_scheduler/vehicle_extensions.py`

```python
from vehicles.models import Vehicle
from django.utils import timezone


def get_scheduled_activities(self, start_date=None, end_date=None):
    """Get all scheduled activities for this vehicle"""
    from calendar_scheduler.models import ScheduledActivity
    
    queryset = ScheduledActivity.objects.filter(vehicle=self)
    
    if start_date:
        queryset = queryset.filter(scheduled_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(scheduled_date__lte=end_date)
    
    return queryset.order_by('scheduled_date')


# Add methods to existing Vehicle model
Vehicle.add_to_class('get_scheduled_activities', get_scheduled_activities)
```

**File**: `calendar_scheduler/apps.py`

```python
from django.apps import AppConfig


class CalendarSchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calendar_scheduler'
    
    def ready(self):
        # Import signals
        import calendar_scheduler.signals
        
        # Optional: Import vehicle extensions if using monkey patching
        # import calendar_scheduler.vehicle_extensions
```

### Step 3.2: Create Data Migration to Sync Existing Data

**File**: Create a data migration to link existing maintenance types

```bash
python manage.py makemigrations calendar_scheduler --empty --name sync_existing_maintenance_types
```

**File**: `calendar_scheduler/migrations/000X_sync_existing_maintenance_types.py`

```python
from django.db import migrations
from datetime import timedelta


def sync_maintenance_types(apps, schema_editor):
    """
    Create ActivityType records for all existing MaintenanceType records.
    This links the calendar system with existing maintenance data.
    """
    MaintenanceType = apps.get_model('maintenance', 'MaintenanceType')
    ActivityType = apps.get_model('calendar_scheduler', 'ActivityType')
    
    for maint_type in MaintenanceType.objects.all():
        # Create corresponding ActivityType if it doesn't exist
        ActivityType.objects.get_or_create(
            maintenance_type=maint_type,
            defaults={
                'name': maint_type.name,
                'category': 'maintenance',
                'description': getattr(maint_type, 'description', ''),
                'estimated_duration': getattr(maint_type, 'estimated_duration', timedelta(hours=1)),
                'is_active': getattr(maint_type, 'is_active', True),
            }
        )


def reverse_sync(apps, schema_editor):
    """Reverse migration - delete synced activity types"""
    ActivityType = apps.get_model('calendar_scheduler', 'ActivityType')
    ActivityType.objects.filter(category='maintenance').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('calendar_scheduler', '0001_initial'),  # Adjust to your latest migration
        ('maintenance', '__latest__'),  # Depends on maintenance app
    ]
    
    operations = [
        migrations.RunPython(sync_maintenance_types, reverse_sync),
    ]
```

```bash
python manage.py migrate
```

---

## PHASE 4: Create Scheduling Services

### Step 4.1: Create Activity Scheduler Service

**File**: `calendar_scheduler/services/activity_scheduler.py`

```python
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction

from calendar_scheduler.models import ActivityType, ScheduledActivity, CalendarSettings
from vehicles.models import Vehicle  # Adjust import to your structure
from maintenance.models import MaintenanceScheduleTemplate  # Adjust import


class ActivityScheduler:
    """
    Core scheduling engine that creates calendar events for vehicles.
    Integrates with existing Vehicle and Maintenance apps.
    """
    
    def __init__(self):
        self.settings = CalendarSettings.get_settings()
    
    @transaction.atomic
    def schedule_all_activities_for_vehicle(self, vehicle, schedule_months=None):
        """
        Main entry point: Schedule ALL activities for a vehicle.
        
        Args:
            vehicle: Vehicle instance from existing Vehicle model
            schedule_months: Override default schedule horizon
        """
        if schedule_months is None:
            schedule_months = self.settings.schedule_horizon_months
        
        print(f"📅 Scheduling activities for {vehicle} (ID: {vehicle.id})...")
        
        # Schedule different activity types
        self.schedule_initial_inspection(vehicle)
        self.schedule_minor_inspections(vehicle, schedule_months)
        self.schedule_maintenance_activities(vehicle, schedule_months)
        
        total_count = ScheduledActivity.objects.filter(vehicle=vehicle).count()
        print(f"✓ Completed: {total_count} total activities scheduled for {vehicle}")
        
        return total_count
    
    def schedule_initial_inspection(self, vehicle):
        """
        Schedule the full initial inspection on vehicle onboarding date.
        Only scheduled once per vehicle.
        """
        # Check if already scheduled
        if ScheduledActivity.objects.filter(
            vehicle=vehicle,
            is_initial_inspection=True
        ).exists():
            print(f"  ⊙ Initial inspection already scheduled")
            return None
        
        # Get or create initial inspection activity type
        initial_inspection_type, created = ActivityType.objects.get_or_create(
            name="Initial Full Inspection",
            category=ActivityType.INSPECTION,
            defaults={
                'description': 'Complete vehicle inspection upon onboarding to platform',
                'estimated_duration': timedelta(hours=2),
                'is_active': True
            }
        )
        
        # Create scheduled activity on onboarding date
        activity = ScheduledActivity.objects.create(
            vehicle=vehicle,
            activity_type=initial_inspection_type,
            scheduled_date=vehicle.onboarding_date,
            is_initial_inspection=True,
            status=ScheduledActivity.SCHEDULED
        )
        
        print(f"  ✓ Initial inspection scheduled for {vehicle.onboarding_date}")
        return activity
    
    def schedule_minor_inspections(self, vehicle, schedule_months):
        """
        Schedule minor inspections at regular intervals.
        Default: every 4 months (configurable in settings).
        
        Args:
            vehicle: Vehicle instance
            schedule_months: How many months ahead to schedule
        """
        # Get inspection interval from settings
        inspection_interval = self.settings.inspection_interval_months
        
        # Get or create minor inspection activity type
        minor_inspection_type, created = ActivityType.objects.get_or_create(
            name="Minor Inspection",
            category=ActivityType.INSPECTION,
            defaults={
                'description': f'Routine inspection every {inspection_interval} months',
                'estimated_duration': timedelta(minutes=45),
                'is_active': True
            }
        )
        
        base_date = vehicle.onboarding_date
        number_of_inspections = schedule_months // inspection_interval
        scheduled_count = 0
        
        for inspection_number in range(1, number_of_inspections + 1):
            # Calculate scheduled date
            scheduled_date = base_date + relativedelta(
                months=inspection_interval * inspection_number
            )
            
            # Check for duplicates
            if ScheduledActivity.objects.filter(
                vehicle=vehicle,
                activity_type=minor_inspection_type,
                scheduled_date=scheduled_date
            ).exists():
                continue
            
            # Create scheduled inspection
            ScheduledActivity.objects.create(
                vehicle=vehicle,
                activity_type=minor_inspection_type,
                scheduled_date=scheduled_date,
                recurrence_number=inspection_number,
                status=ScheduledActivity.SCHEDULED
            )
            scheduled_count += 1
        
        print(f"  ✓ Scheduled {scheduled_count} minor inspections (every {inspection_interval} months)")
    
    def schedule_maintenance_activities(self, vehicle, schedule_months):
        """
        Schedule maintenance activities based on existing MaintenanceScheduleTemplate records.
        Integrates with your existing maintenance app.
        
        Args:
            vehicle: Vehicle instance
            schedule_months: Planning horizon in months
        """
        # Query existing maintenance schedule templates
        # ADJUST THIS QUERY TO MATCH YOUR EXISTING MODEL STRUCTURE
        active_templates = MaintenanceScheduleTemplate.objects.filter(
            is_active=True
        ).select_related('maintenance_type')  # Adjust relation name
        
        if not active_templates.exists():
            print(f"  ⚠ No active maintenance templates found")
            return
        
        base_date = vehicle.onboarding_date
        total_scheduled = 0
        
        for template in active_templates:
            # Get or create corresponding ActivityType
            activity_type, created = ActivityType.objects.get_or_create(
                maintenance_type=template.maintenance_type,  # Adjust field name
                defaults={
                    'name': template.maintenance_type.name,
                    'category': ActivityType.MAINTENANCE,
                    'description': getattr(template.maintenance_type, 'description', ''),
                    'estimated_duration': getattr(template.maintenance_type, 'estimated_duration', timedelta(hours=1)),
                }
            )
            
            # Calculate interval in days
            # ADJUST THESE FIELD NAMES TO MATCH YOUR TEMPLATE MODEL
            if hasattr(template, 'interval_months') and template.interval_months > 0:
                interval_days = template.interval_months * 30
            elif hasattr(template, 'interval_days'):
                interval_days = template.interval_days
            else:
                print(f"  ⚠ Template {template} has no interval configured")
                continue
            
            # Calculate how many occurrences fit in schedule period
            total_days = schedule_months * 30
            number_of_occurrences = total_days // interval_days
            
            for occurrence in range(1, number_of_occurrences + 1):
                scheduled_date = base_date + timedelta(days=interval_days * occurrence)
                
                # Don't schedule beyond planning horizon
                if scheduled_date > base_date + relativedelta(months=schedule_months):
                    break
                
                # Check for duplicates
                if ScheduledActivity.objects.filter(
                    vehicle=vehicle,
                    activity_type=activity_type,
                    scheduled_date=scheduled_date,
                    maintenance_schedule=template
                ).exists():
                    continue
                
                # Create scheduled maintenance
                ScheduledActivity.objects.create(
                    vehicle=vehicle,
                    activity_type=activity_type,
                    scheduled_date=scheduled_date,
                    recurrence_number=occurrence,
                    maintenance_schedule=template,
                    status=ScheduledActivity.SCHEDULED
                )
                total_scheduled += 1
        
        print(f"  ✓ Scheduled {total_scheduled} maintenance activities from {active_templates.count()} templates")
    
    @transaction.atomic
    def reschedule_future_activities(self, vehicle):
        """
        Delete and recreate all future scheduled activities.
        Used when templates change or manual reschedule is needed.
        
        Args:
            vehicle: Vehicle instance to reschedule
        """
        today = timezone.now().date()
        
        # Delete future activities that are still scheduled (not completed)
        deleted_count, _ = ScheduledActivity.objects.filter(
            vehicle=vehicle,
            status=ScheduledActivity.SCHEDULED,
            scheduled_date__gte=today
        ).delete()
        
        print(f"  🗑 Deleted {deleted_count} future activities")
        
        # Recreate schedule
        self.schedule_minor_inspections(vehicle, self.settings.schedule_horizon_months)
        self.schedule_maintenance_activities(vehicle, self.settings.schedule_horizon_months)
        
        print(f"  ✓ Rescheduled all future activities for {vehicle}")
    
    def schedule_all_vehicles(self, active_only=True):
        """
        Schedule activities for all vehicles in the system.
        Useful for initial setup or bulk rescheduling.
        
        Args:
            active_only: Only schedule for active vehicles
        """
        # ADJUST FILTER TO MATCH YOUR VEHICLE MODEL'S STATUS FIELD
        vehicles = Vehicle.objects.all()
        if active_only:
            # Adjust this filter based on your Vehicle model
            vehicles = vehicles.filter(status='active')  # or is_active=True
        
        total_vehicles = vehicles.count()
        print(f"\n🚗 Scheduling activities for {total_vehicles} vehicles...")
        
        success_count = 0
        error_count = 0
        
        for vehicle in vehicles:
            try:
                self.schedule_all_activities_for_vehicle(vehicle)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"  ✗ Error scheduling {vehicle}: {str(e)}")
        
        print(f"\n✓ Completed: {success_count}/{total_vehicles} vehicles")
        if error_count > 0:
            print(f"✗ Errors: {error_count} vehicles")
        
        return success_count, error_count
```

### Step 4.2: Create Calendar Query Service

**File**: `calendar_scheduler/services/calendar_service.py`

```python
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Prefetch, Count

from calendar_scheduler.models import ScheduledActivity
from vehicles.models import Vehicle


class CalendarService:
    """
    Service for querying and displaying scheduled activities.
    Provides various calendar views and reports.
    """
    
    def get_monthly_calendar(self, year, month):
        """
        Get all activities for a specific month, grouped by date.
        
        Args:
            year: Calendar year
            month: Month (1-12)
            
        Returns:
            dict: {date: [list of ScheduledActivity objects]}
        """
        start_date = datetime(year, month, 1).date()
        
        # Calculate end date (first day of next month)
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        
        # Query activities with related data
        activities = ScheduledActivity.objects.filter(
            scheduled_date__gte=start_date,
            scheduled_date__lt=end_date
        ).select_related(
            'vehicle',
            'activity_type',
            'maintenance_schedule',
            'completed_by'
        ).order_by('scheduled_date', 'scheduled_time')
        
        # Group by date
        calendar_data = {}
        for activity in activities:
            date_key = activity.scheduled_date
            if date_key not in calendar_data:
                calendar_data[date_key] = []
            calendar_data[date_key].append(activity)
        
        return calendar_data
    
    def get_vehicle_schedule(self, vehicle, start_date=None, end_date=None, status=None):
        """
        Get all activities for a specific vehicle within date range.
        
        Args:
            vehicle: Vehicle instance
            start_date: Optional start date filter
            end_date: Optional end date filter
            status: Optional status filter
            
        Returns:
            QuerySet of ScheduledActivity
        """
        queryset = ScheduledActivity.objects.filter(vehicle=vehicle)
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.select_related(
            'activity_type',
            'maintenance_schedule',
            'completed_by'
        ).order_by('scheduled_date')
    
    def get_upcoming_activities(self, days_ahead=7, vehicle=None):
        """
        Get activities scheduled in next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            vehicle: Optional vehicle filter
            
        Returns:
            QuerySet of ScheduledActivity
        """
        today = timezone.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        queryset = ScheduledActivity.objects.filter(
            scheduled_date__gte=today,
            scheduled_date__lte=end_date,
            status=ScheduledActivity.SCHEDULED
        )
        
        if vehicle:
            queryset = queryset.filter(vehicle=vehicle)
        
        return queryset.select_related(
            'vehicle',
            'activity_type'
        ).order_by('scheduled_date', 'scheduled_time')
    
    def get_overdue_activities(self, vehicle=None):
        """
        Get all overdue activities (past scheduled date, not completed).
        
        Args:
            vehicle: Optional vehicle filter
            
        Returns:
            QuerySet of ScheduledActivity
        """
        today = timezone.now().date()
        
        queryset = ScheduledActivity.objects.filter(
            scheduled_date__lt=today,
            status=ScheduledActivity.SCHEDULED
        )
        
        if vehicle:
            queryset = queryset.filter(vehicle=vehicle)
        
        return queryset.select_related(
            'vehicle',
            'activity_type'
        ).order_by('scheduled_date')
    
    def get_daily_schedule(self, date=None):
        """
        Get all activities for a specific date.
        
        Args:
            date: Target date (defaults to today)
            
        Returns:
            QuerySet of ScheduledActivity
        """
        if date is None:
            date = timezone.now().date()
        
        return ScheduledActivity.objects.filter(
            scheduled_date=date
        ).select_related(
            'vehicle',
            'activity_type',
            'completed_by'
        ).order_by('scheduled_time', 'vehicle')
    
    def get_activity_statistics(self, start_date=None, end_date=None):
        """
        Get statistics about scheduled activities.
        
        Returns:
            dict: Statistics about activities
        """
        queryset = ScheduledActivity.objects.all()
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        stats = queryset.aggregate(
            total=Count('id'),
            scheduled=Count('id', filter=Q(status=ScheduledActivity.SCHEDULED)),
            completed=Count('id', filter=Q(status=ScheduledActivity.COMPLETED)),
            in_progress=Count('id', filter=Q(status=ScheduledActivity.IN_PROGRESS)),
            missed=Count('id', filter=Q(status=ScheduledActivity.MISSED)),
            cancelled=Count('id', filter=Q(status=ScheduledActivity.CANCELLED))
        )
        
        return stats
    
    def get_vehicles_with_upcoming_activities(self, days_ahead=7):
        """
        Get all vehicles that have activities scheduled in next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            QuerySet of Vehicles with activity counts
        """
        today = timezone.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        return Vehicle.objects.filter(
            calendar_scheduled_activities__scheduled_date__gte=today,
            calendar_scheduled_activities__scheduled_date__lte=end_date,
            calendar_scheduled_activities__status=ScheduledActivity.SCHEDULED
        ).annotate(
            upcoming_count=Count('calendar_scheduled_activities')
        ).distinct().order_by('-upcoming_count')
```

---

## PHASE 5: Integrate with Existing Apps

### Step 5.1: Create Django Signals for Auto-Scheduling

**File**: `calendar_scheduler/signals.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

from vehicles.models import Vehicle  # Adjust import
from calendar_scheduler.models import CalendarSettings
from calendar_scheduler.services.activity_scheduler import ActivityScheduler


@receiver(post_save, sender=Vehicle)
def auto_schedule_vehicle_activities(sender, instance, created, **kwargs):
    """
    Automatically schedule activities when a new vehicle is onboarded.
    Triggered by Django signals on Vehicle creation.
    """
    # Only schedule for newly created vehicles
    if not created:
        return
    
    # Check if auto-scheduling is enabled
    settings = CalendarSettings.get_settings()
    if not settings.auto_schedule_on_onboarding:
        return
    
    # Check if vehicle is active (adjust condition to your Vehicle model)
    # Example conditions:
    if hasattr(instance, 'is_active') and not instance.is_active:
        return
    if hasattr(instance, 'status') and instance.status != 'active':
        return
    
    # Check if vehicle has onboarding_date
    if not instance.onboarding_date:
        print(f"⚠ Cannot schedule activities for {instance}: No onboarding_date")
        return
    
    print(f"\n🚗 New vehicle onboarded: {instance}")
    
    try:
        scheduler = ActivityScheduler()
        scheduler.schedule_all_activities_for_vehicle(instance)
        print(f"✓ Auto-scheduling completed for {instance}\n")
    except Exception as e:
        print(f"✗ Error auto-scheduling {instance}: {str(e)}\n")
```

**File**: `calendar_scheduler/apps.py` (update)

```python
from django.apps import AppConfig


class CalendarSchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calendar_scheduler'
    verbose_name = 'Calendar Scheduler'
    
    def ready(self):
        """Import signals when app is ready"""
        import calendar_scheduler.signals
```

### Step 5.2: Create Management Commands

**File**: `calendar_scheduler/management/commands/schedule_all_vehicles.py`

```python
from django.core.management.base import BaseCommand, CommandError
from vehicles.models import Vehicle
from calendar_scheduler.services.activity_scheduler import ActivityScheduler


class Command(BaseCommand):
    help = 'Schedule activities for all active vehicles'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reschedule',
            action='store_true',
            help='Delete existing future activities and recreate them',
        )
        
        parser.add_argument(
            '--vehicle-id',
            type=int,
            help='Schedule only for specific vehicle ID',
        )
        
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Number of months to schedule ahead (default: 12)',
        )
    
    def handle(self, *args, **options):
        scheduler = ActivityScheduler()
        
        # Get vehicles to process
        if options['vehicle_id']:
            try:
                vehicles = [Vehicle.objects.get(id=options['vehicle_id'])]
                self.stdout.write(f"Processing single vehicle ID: {options['vehicle_id']}")
            except Vehicle.DoesNotExist:
                raise CommandError(f"Vehicle with ID {options['vehicle_id']} does not exist")
        else:
            # Adjust filter based on your Vehicle model
            vehicles = Vehicle.objects.filter(status='active')  # or is_active=True
            self.stdout.write(f"Processing {vehicles.count()} active vehicles")
        
        # Process each vehicle
        success_count = 0
        error_count = 0
        
        for vehicle in vehicles:
            try:
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"Processing: {vehicle}")
                
                if options['reschedule']:
                    self.stdout.write("  Rescheduling (deleting future activities)...")
                    scheduler.reschedule_future_activities(vehicle)
                else:
                    scheduler.schedule_all_activities_for_vehicle(
                        vehicle,
                        schedule_months=options['months']
                    )
                
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Success"))
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✓ Completed: {success_count} vehicles"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count} vehicles"))
```

**File**: `calendar_scheduler/management/commands/sync_maintenance_types.py`

```python
from django.core.management.base import BaseCommand
from maintenance.models import MaintenanceType
from calendar_scheduler.models import ActivityType
from datetime import timedelta


class Command(BaseCommand):
    help = 'Sync existing maintenance types with calendar activity types'
    
    def handle(self, *args, **options):
        self.stdout.write("Syncing maintenance types with calendar system...")
        
        maintenance_types = MaintenanceType.objects.all()
        synced_count = 0
        
        for maint_type in maintenance_types:
            activity_type, created = ActivityType.objects.get_or_create(
                maintenance_type=maint_type,
                defaults={
                    'name': maint_type.name,
                    'category': ActivityType.MAINTENANCE,
                    'description': getattr(maint_type, 'description', ''),
                    'estimated_duration': getattr(
                        maint_type, 
                        'estimated_duration', 
                        timedelta(hours=1)
                    ),
                    'is_active': getattr(maint_type, 'is_active', True),
                }
            )
            
            if created:
                synced_count += 1
                self.stdout.write(f"  ✓ Created: {activity_type.name}")
            else:
                self.stdout.write(f"  ⊙ Exists: {activity_type.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Synced {synced_count} new maintenance types")
        )
```

### Step 5.3: Create Admin Interface

**File**: `calendar_scheduler/admin.py`

```python
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import ActivityType, ScheduledActivity, CalendarSettings


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'category', 
        'estimated_duration', 
        'maintenance_type_link',
        'is_active',
        'scheduled_count'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'estimated_duration', 'is_active')
        }),
        ('Integration', {
            'fields': ('maintenance_type',),
            'description': 'Link to existing maintenance type from maintenance app'
        }),
        ('System', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def maintenance_type_link(self, obj):
        if obj.maintenance_type:
            url = reverse('admin:maintenance_maintenancetype_change', args=[obj.maintenance_type.id])
            return format_html('<a href="{}">{}</a>', url, obj.maintenance_type.name)
        return '-'
    maintenance_type_link.short_description = 'Linked Maintenance Type'
    
    def scheduled_count(self, obj):
        count = obj.scheduledactivity_set.count()
        return count
    scheduled_count.short_description = 'Scheduled'


@admin.register(ScheduledActivity)
class ScheduledActivityAdmin(admin.ModelAdmin):
    list_display = [
        'vehicle_link',
        'activity_type',
        'scheduled_date',
        'scheduled_time',
        'status_badge',
        'is_initial_inspection',
        'recurrence_number'
    ]
    list_filter = [
        'status',
        'activity_type__category',
        'is_initial_inspection',
        'scheduled_date'
    ]
    search_fields = [
        'vehicle__license_plate',
        'vehicle__vin',
        'activity_type__name',
        'notes'
    ]
    date_hierarchy = 'scheduled_date'
    readonly_fields = ['created_at', 'updated_at', 'recurrence_number']
    
    fieldsets = (
        ('Scheduling', {
            'fields': (
                'vehicle',
                'activity_type',
                'scheduled_date',
                'scheduled_time',
                'status'
            )
        }),
        ('Tracking', {
            'fields': (
                'is_initial_inspection',
                'recurrence_number',
                'maintenance_schedule'
            ),
            'description': 'Tracking information for recurring activities'
        }),
        ('Completion', {
            'fields': ('completed_date', 'completed_by', 'notes')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_completed', 'mark_in_progress', 'mark_cancelled']
    
    def vehicle_link(self, obj):
        url = reverse('admin:vehicles_vehicle_change', args=[obj.vehicle.id])
        return format_html('<a href="{}">{}</a>', url, obj.vehicle)
    vehicle_link.short_description = 'Vehicle'
    vehicle_link.admin_order_field = 'vehicle'
    
    def status_badge(self, obj):
        colors = {
            'scheduled': '#2196F3',
            'in_progress': '#FF9800',
            'completed': '#4CAF50',
            'missed': '#F44336',
            'cancelled': '#9E9E9E'
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(
            status=ScheduledActivity.COMPLETED,
            completed_date=timezone.now(),
            completed_by=request.user
        )
        self.message_user(request, f'{updated} activities marked as completed.')
    mark_completed.short_description = 'Mark selected as completed'
    
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status=ScheduledActivity.IN_PROGRESS)
        self.message_user(request, f'{updated} activities marked as in progress.')
    mark_in_progress.short_description = 'Mark selected as in progress'
    
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status=ScheduledActivity.CANCELLED)
        self.message_user(request, f'{updated} activities marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected as cancelled'


@admin.register(CalendarSettings)
class CalendarSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'inspection_interval_months',
        'schedule_horizon_months',
        'auto_schedule_on_onboarding',
        'send_reminders',
        'updated_at'
    ]
    
    fieldsets = (
        ('Scheduling Configuration', {
            'fields': (
                'inspection_interval_months',
                'schedule_horizon_months',
                'auto_schedule_on_onboarding'
            ),
            'description': 'Configure how activities are scheduled'
        }),
        ('Notifications', {
            'fields': (
                'send_reminders',
                'reminder_days_before'
            ),
            'description': 'Configure reminder notifications'
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not CalendarSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False
```

---

## PHASE 6: Create API Endpoints

### Step 6.1: Create Serializers

**File**: `calendar_scheduler/api/serializers.py`

```python
from rest_framework import serializers
from calendar_scheduler.models import ActivityType, ScheduledActivity, CalendarSettings
from vehicles.models import Vehicle


class ActivityTypeSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = ActivityType
        fields = [
            'id', 'name', 'category', 'category_display', 
            'description', 'estimated_duration', 'is_active'
        ]


class VehicleMinimalSerializer(serializers.ModelSerializer):
    """Minimal vehicle info for nested serialization"""
    class Meta:
        model = Vehicle
        fields = ['id', 'license_plate', 'make', 'model', 'year', 'vin']


class ScheduledActivitySerializer(serializers.ModelSerializer):
    vehicle = VehicleMinimalSerializer(read_only=True)
    activity_type = ActivityTypeSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ScheduledActivity
        fields = [
            'id', 'vehicle', 'activity_type', 'scheduled_date',
            'scheduled_time', 'status', 'status_display',
            'completed_date', 'notes', 'is_initial_inspection',
            'recurrence_number', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ScheduledActivityUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating scheduled activities"""
    class Meta:
        model = ScheduledActivity
        fields = ['status', 'scheduled_date', 'scheduled_time', 'notes']


class VehicleScheduleSerializer(serializers.ModelSerializer):
    """Vehicle with nested scheduled activities"""
    upcoming_activities = serializers.SerializerMethodField()
    upcoming_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()
    next_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'make', 'model', 'year',
            'onboarding_date', 'upcoming_activities', 'upcoming_count',
            'completed_count', 'next_activity'
        ]
    
    def get_upcoming_activities(self, obj):
        from django.utils import timezone
        activities = ScheduledActivity.objects.filter(
            vehicle=obj,
            status=ScheduledActivity.SCHEDULED,
            scheduled_date__gte=timezone.now().date()
        ).select_related('activity_type')[:5]  # Limit to 5
        
        return ScheduledActivitySerializer(activities, many=True).data
    
    def get_upcoming_count(self, obj):
        from django.utils import timezone
        return ScheduledActivity.objects.filter(
            vehicle=obj,
            status=ScheduledActivity.SCHEDULED,
            scheduled_date__gte=timezone.now().date()
        ).count()
    
    def get_completed_count(self, obj):
        return ScheduledActivity.objects.filter(
            vehicle=obj,
            status=ScheduledActivity.COMPLETED
        ).count()
    
    def get_next_activity(self, obj):
        from django.utils import timezone
        next_activity = ScheduledActivity.objects.filter(
            vehicle=obj,
            status=ScheduledActivity.SCHEDULED,
            scheduled_date__gte=timezone.now().date()
        ).select_related('activity_type').order_by('scheduled_date').first()
        
        if next_activity:
            return ScheduledActivitySerializer(next_activity).data
        return None


class CalendarSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarSettings
        fields = [
            'inspection_interval_months', 'schedule_horizon_months',
            'auto_schedule_on_onboarding', 'send_reminders',
            'reminder_days_before', 'updated_at'
        ]
        read_only_fields = ['updated_at']
```

### Step 6.2: Create API Views

**File**: `calendar_scheduler/api/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime

from calendar_scheduler.models import ScheduledActivity, ActivityType, CalendarSettings
from calendar_scheduler.services.calendar_service import CalendarService
from calendar_scheduler.services.activity_scheduler import ActivityScheduler
from vehicles.models import Vehicle

from .serializers import (
    ScheduledActivitySerializer,
    ScheduledActivityUpdateSerializer,
    ActivityTypeSerializer,
    VehicleScheduleSerializer,
    CalendarSettingsSerializer
)


class ScheduledActivityViewSet(viewsets.ModelViewSet):
    """API endpoint for scheduled activities - main calendar data"""
    queryset = ScheduledActivity.objects.all()
    serializer_class = ScheduledActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by query parameters"""
        queryset = super().get_queryset()
        
        # Filter by vehicle
        vehicle_id = self.request.query_params.get('vehicle_id')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(activity_type__category=category)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        return queryset.select_related('vehicle', 'activity_type', 'maintenance_schedule')
    
    def get_serializer_class(self):
        """Use different serializer for updates"""
        if self.action in ['update', 'partial_update']:
            return ScheduledActivityUpdateSerializer
        return ScheduledActivitySerializer
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """
        GET /api/calendar/scheduled-activities/calendar/?year=2025&month=11
        
        Returns all activities for a specific month grouped by date
        """
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        calendar_service = CalendarService()
        calendar_data = calendar_service.get_monthly_calendar(year, month)
        
        # Convert to serializable format
        response_data = {}
        for date, activities in calendar_data.items():
            response_data[str(date)] = ScheduledActivitySerializer(
                activities,
                many=True
            ).data
        
        return Response({
            'year': year,
            'month': month,
            'calendar': response_data,
            'total_activities': sum(len(acts) for acts in calendar_data.values())
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        GET /api/calendar/scheduled-activities/upcoming/?days=7&vehicle_id=1
        
        Returns activities scheduled in the next N days
        """
        days = int(request.query_params.get('days', 7))
        vehicle_id = request.query_params.get('vehicle_id')
        
        vehicle = None
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
            except Vehicle.DoesNotExist:
                return Response(
                    {'error': 'Vehicle not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        calendar_service = CalendarService()
        activities = calendar_service.get_upcoming_activities(
            days_ahead=days,
            vehicle=vehicle
        )
        
        serializer = self.get_serializer(activities, many=True)
        return Response({
            'days_ahead': days,
            'vehicle_id': vehicle_id,
            'count': activities.count(),
            'activities': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        GET /api/calendar/scheduled-activities/overdue/
        
        Returns all overdue activities
        """
        vehicle_id = request.query_params.get('vehicle_id')
        
        vehicle = None
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
            except Vehicle.DoesNotExist:
                return Response(
                    {'error': 'Vehicle not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        calendar_service = CalendarService()
        activities = calendar_service.get_overdue_activities(vehicle=vehicle)
        
        serializer = self.get_serializer(activities, many=True)
        return Response({
            'count': activities.count(),
            'activities': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        GET /api/calendar/scheduled-activities/today/
        
        Returns activities scheduled for today
        """
        calendar_service = CalendarService()
        activities = calendar_service.get_daily_schedule()
        
        serializer = self.get_serializer(activities, many=True)
        return Response({
            'date': timezone.now().date(),
            'count': activities.count(),
            'activities': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        GET /api/calendar/scheduled-activities/statistics/
        
        Returns statistics about scheduled activities
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        calendar_service = CalendarService()
        stats = calendar_service.get_activity_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        POST /api/calendar/scheduled-activities/{id}/complete/
        Body: {"notes": "Optional completion notes"}
        
        Mark an activity as completed
        """
        activity = self.get_object()
        notes = request.data.get('notes', '')
        
        activity.mark_completed(user=request.user, notes=notes)
        
        return Response({
            'status': 'success',
            'message': 'Activity marked as completed',
            'activity': self.get_serializer(activity).data
        })
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        POST /api/calendar/scheduled-activities/{id}/start/
        
        Mark an activity as in progress
        """
        activity = self.get_object()
        activity.status = ScheduledActivity.IN_PROGRESS
        activity.save()
        
        return Response({
            'status': 'success',
            'message': 'Activity marked as in progress',
            'activity': self.get_serializer(activity).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        POST /api/calendar/scheduled-activities/{id}/cancel/
        Body: {"notes": "Reason for cancellation"}
        
        Cancel a scheduled activity
        """
        activity = self.get_object()
        notes = request.data.get('notes', '')
        
        activity.status = ScheduledActivity.CANCELLED
        if notes:
            activity.notes = notes
        activity.save()
        
        return Response({
            'status': 'success',
            'message': 'Activity cancelled',
            'activity': self.get_serializer(activity).data
        })


class VehicleScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for vehicle schedules"""
    queryset = Vehicle.objects.all()
    serializer_class = VehicleScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """
        GET /api/calendar/vehicles/{id}/schedule/?start_date=2024-01-01&end_date=2024-12-31
        
        Get all scheduled activities for a specific vehicle
        """
        vehicle = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        status_filter = request.query_params.get('status')
        
        # Parse dates if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        calendar_service = CalendarService()
        activities = calendar_service.get_vehicle_schedule(
            vehicle,
            start_date=start_date,
            end_date=end_date,
            status=status_filter
        )
        
        return Response({
            'vehicle': VehicleMinimalSerializer(vehicle).data,
            'activities': ScheduledActivitySerializer(activities, many=True).data,
            'count': activities.count()
        })
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """
        POST /api/calendar/vehicles/{id}/reschedule/
        
        Reschedule all future activities for a vehicle
        """
        vehicle = self.get_object()
        scheduler = ActivityScheduler()
        
        try:
            scheduler.reschedule_future_activities(vehicle)
            return Response({
                'status': 'success',
                'message': f'Activities rescheduled for {vehicle.license_plate}'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def schedule_activities(self, request, pk=None):
        """
        POST /api/calendar/vehicles/{id}/schedule_activities/
        Body: {"months": 12}
        
        Manually trigger scheduling for a vehicle
        """
        vehicle = self.get_object()
        months = request.data.get('months', 12)
        
        scheduler = ActivityScheduler()
        
        try:
            count = scheduler.schedule_all_activities_for_vehicle(
                vehicle,
                schedule_months=months
            )
            return Response({
                'status': 'success',
                'message': f'Scheduled {count} activities for {vehicle.license_plate}',
                'count': count
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ActivityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for activity types (read-only)"""
    queryset = ActivityType.objects.filter(is_active=True)
    serializer_class = ActivityTypeSerializer
    permission_classes = [IsAuthenticated]


class CalendarSettingsViewSet(viewsets.ModelViewSet):
    """API endpoint for calendar settings"""
    queryset = CalendarSettings.objects.all()
    serializer_class = CalendarSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Always return the singleton settings instance"""
        return CalendarSettings.get_settings()
    
    def list(self, request):
        """Return singleton settings as a single object"""
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
```

### Step 6.3: Configure URLs

**File**: `calendar_scheduler/api/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScheduledActivityViewSet,
    VehicleScheduleViewSet,
    ActivityTypeViewSet,
    CalendarSettingsViewSet
)

router = DefaultRouter()
router.register(r'scheduled-activities', ScheduledActivityViewSet, basename='scheduled-activity')
router.register(r'vehicles', VehicleScheduleViewSet, basename='vehicle-schedule')
router.register(r'activity-types', ActivityTypeViewSet, basename='activity-type')
router.register(r'settings', CalendarSettingsViewSet, basename='calendar-settings')

app_name = 'calendar'

urlpatterns = [
    path('', include(router.urls)),
]
```

**File**: Update main `urls.py` (your project's main URL config)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # ... your existing URL patterns ...
    path('api/calendar/', include('calendar_scheduler.api.urls')),  # NEW
]
```

---

## PHASE 7: Testing & Validation

### Step 7.1: Run Migrations

```bash
# Create migrations for the calendar app
python manage.py makemigrations calendar_scheduler

# Apply migrations
python manage.py migrate

# Create calendar settings
python manage.py shell
>>> from calendar_scheduler.models import CalendarSettings
>>> CalendarSettings.get_settings()
>>> exit()
```

### Step 7.2: Sync Existing Data

```bash
# Sync existing maintenance types with calendar system
python manage.py sync_maintenance_types

# Schedule activities for all existing vehicles
python manage.py schedule_all_vehicles
```

### Step 7.3: Test Auto-Scheduling

**Via Django Shell**:

```python
python manage.py shell

from vehicles.models import Vehicle
from datetime import date

# Create a test vehicle
vehicle = Vehicle.objects.create(
    vin='TEST123456789',
    make='Toyota',
    model='Test',
    year=2024,
    license_plate='TEST123',
    onboarding_date=date.today(),
    status='active'  # Adjust field name to your model
)

# Check if activities were auto-scheduled
from calendar_scheduler.models import ScheduledActivity
activities = ScheduledActivity.objects.filter(vehicle=vehicle)
print(f"Auto-scheduled {activities.count()} activities")

for activity in activities.order_by('scheduled_date')[:10]:
    print(f"  - {activity.scheduled_date}: {activity.activity_type.name}")
```

### Step 7.4: Test API Endpoints

```bash
# Get authentication token (adjust based on your auth system)
# Assuming you have token authentication

# Get monthly calendar
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/calendar/scheduled-activities/calendar/?year=2025&month=11"

# Get upcoming activities
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/calendar/scheduled-activities/upcoming/?days=7"

# Get vehicle schedule
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/calendar/vehicles/1/schedule/"

# Get today's schedule
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/calendar/scheduled-activities/today/"

# Get overdue activities
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/calendar/scheduled-activities/overdue/"

# Complete an activity
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Completed successfully"}' \
  "http://localhost:8000/api/calendar/scheduled-activities/1/complete/"

# Reschedule a vehicle
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/calendar/vehicles/1/reschedule/"

# Get statistics
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/calendar/scheduled-activities/statistics/"
```

### Step 7.5: Test Admin Interface

1. Navigate to `http://localhost:8000/admin/`
2. Go to **Calendar Scheduler** section
3. View **Scheduled Activities** - should see all auto-generated events
4. Test filters: by status, date, vehicle
5. Test bulk actions: mark as completed, cancel
6. View **Activity Types** - should see synced maintenance types
7. Edit **Calendar Settings** - adjust intervals and scheduling options

---

## Integration Checklist

### Pre-Integration Verification

- [ ] **Vehicle Model Check**
  - [ ] Has `onboarding_date` field (DateField)
  - [ ] Has status/active indicator field
  - [ ] Document field names and structure
  - [ ] No conflicting `related_name` attributes

- [ ] **Maintenance Model Check**
  - [ ] MaintenanceType or equivalent exists
  - [ ] MaintenanceScheduleTemplate or equivalent exists
  - [ ] Document interval field names (days/months)
  - [ ] Document relationship field names

- [ ] **Dependencies Installed**
  ```bash
  pip install python-dateutil
  ```

### Installation Steps

- [ ] **Create Calendar App**
  - [ ] `python manage.py startapp calendar_scheduler`
  - [ ] Create `services/` directory
  - [ ] Add to `INSTALLED_APPS`

- [ ] **Create Models**
  - [ ] `ActivityType` model
  - [ ] `ScheduledActivity` model
  - [ ] `CalendarSettings` model
  - [ ] Adjust foreign key imports to match your app structure

- [ ] **Create Services**
  - [ ] `ActivityScheduler` service
  - [ ] `CalendarService` service
  - [ ] Adjust model imports in services

- [ ] **Configure Integration**
  - [ ] Create signals (`signals.py`)
  - [ ] Update `apps.py` to load signals
  - [ ] Create data migration to sync maintenance types

- [ ] **Create Management Commands**
  - [ ] `schedule_all_vehicles` command
  - [ ] `sync_maintenance_types` command

- [ ] **Setup Admin Interface**
  - [ ] Register models in admin
  - [ ] Configure list displays and filters
  - [ ] Add custom actions

- [ ] **Create API**
  - [ ] Create serializers
  - [ ] Create viewsets
  - [ ] Configure URLs
  - [ ] Add to main URL configuration

- [ ] **Run Migrations**
  - [ ] `python manage.py makemigrations`
  - [ ] Review migrations
  - [ ] `python manage.py migrate`

- [ ] **Sync Existing Data**
  - [ ] Run `sync_maintenance_types` command
  - [ ] Run `schedule_all_vehicles` command
  - [ ] Verify data in admin

- [ ] **Testing**
  - [ ] Test auto-scheduling on new vehicle creation
  - [ ] Test manual scheduling via command
  - [ ] Test API endpoints
  - [ ] Test admin interface
  - [ ] Test rescheduling functionality

---

## Configuration Adjustments Guide

### Adjust for Your Vehicle Model

If your Vehicle model uses different field names, update these locations:

**Location 1**: `calendar_scheduler/models.py` - ScheduledActivity model
```python
# Change this line if your foreign key uses different related_name
vehicle = models.ForeignKey(
    Vehicle,
    on_delete=models.CASCADE,
    related_name='calendar_scheduled_activities'  # Adjust if conflicts exist
)
```

**Location 2**: `calendar_scheduler/signals.py` - Auto-scheduling signal
```python
# Adjust these conditions based on your Vehicle model
if hasattr(instance, 'is_active') and not instance.is_active:
    return
# OR
if hasattr(instance, 'status') and instance.status != 'active':
    return
```

**Location 3**: `calendar_scheduler/services/activity_scheduler.py` - Vehicle filtering
```python
# In schedule_all_vehicles method
vehicles = vehicles.filter(status='active')  # Adjust field name
# OR
vehicles = vehicles.filter(is_active=True)  # Use your field
```

### Adjust for Your Maintenance Model

If your maintenance models use different names or structure:

**Location 1**: `calendar_scheduler/models.py` - ActivityType model
```python
# Change FK to match your maintenance type model
maintenance_type = models.OneToOneField(
    'maintenance.YourMaintenanceTypeModel',  # Adjust model name
    on_delete=models.CASCADE,
    null=True,
    blank=True
)
```

**Location 2**: `calendar_scheduler/services/activity_scheduler.py`
```python
# In schedule_maintenance_activities method
active_templates = YourScheduleTemplateModel.objects.filter(
    is_active=True
).select_related('your_maintenance_type_field')  # Adjust field name

# Adjust interval field access
if hasattr(template, 'your_interval_months_field'):
    interval_days = template.your_interval_months_field * 30
```

### Adjust Database Table Names

If you need custom table names for the calendar app:

```python
# In each model's Meta class
class Meta:
    db_table = 'your_custom_prefix_scheduled_activity'
```

---

## Expected Scheduling Output Example

For a vehicle onboarded on **January 1, 2025**, with these maintenance templates:
- Oil Change: Every 3 months
- Tire Rotation: Every 6 months
- Brake Inspection: Every 4 months

**Generated Schedule**:
```
✓ January 1, 2025  - Initial Full Inspection (onboarding)
✓ March 1, 2025    - Oil Change (3 months)
✓ April 1, 2025    - Brake Inspection (4 months)
✓ May 1, 2025      - Minor Inspection (4 months)
✓ June 1, 2025     - Oil Change (6 months)
✓ July 1, 2025     - Tire Rotation (6 months)
✓ August 1, 2025   - Brake Inspection (8 months)
✓ September 1, 2025 - Minor Inspection (8 months)
✓ September 1, 2025 - Oil Change (9 months)
✓ December 1, 2025  - Oil Change (12 months)
✓ December 1, 2025  - Tire Rotation (12 months)
✓ December 1, 2025  - Brake Inspection (12 months)
✓ January 1, 2026   - Minor Inspection (12 months)
```

---

## API Endpoint Reference

### Scheduled Activities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/scheduled-activities/` | List all activities (with filters) |
| GET | `/api/calendar/scheduled-activities/{id}/` | Get single activity details |
| PUT/PATCH | `/api/calendar/scheduled-activities/{id}/` | Update activity |
| DELETE | `/api/calendar/scheduled-activities/{id}/` | Delete activity |
| GET | `/api/calendar/scheduled-activities/calendar/?year=2025&month=11` | Monthly calendar view |
| GET | `/api/calendar/scheduled-activities/upcoming/?days=7` | Upcoming activities |
| GET | `/api/calendar/scheduled-activities/today/` | Today's schedule |
| GET | `/api/calendar/scheduled-activities/overdue/` | Overdue activities |
| GET | `/api/calendar/scheduled-activities/statistics/` | Activity statistics |
| POST | `/api/calendar/scheduled-activities/{id}/complete/` | Mark as completed |
| POST | `/api/calendar/scheduled-activities/{id}/start/` | Mark as in progress |
| POST | `/api/calendar/scheduled-activities/{id}/cancel/` | Cancel activity |

### Vehicle Schedules

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/vehicles/{id}/` | Vehicle with upcoming activities |
| GET | `/api/calendar/vehicles/{id}/schedule/` | Full vehicle schedule |
| POST | `/api/calendar/vehicles/{id}/reschedule/` | Reschedule all future activities |
| POST | `/api/calendar/vehicles/{id}/schedule_activities/` | Manually trigger scheduling |

### Activity Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/activity-types/` | List all activity types |
| GET | `/api/calendar/activity-types/{id}/` | Get activity type details |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/settings/` | Get calendar settings |
| PUT/PATCH | `/api/calendar/settings/1/` | Update calendar settings |

---

## Query Parameters

### Filter Activities
```
?vehicle_id=1              # Filter by vehicle
?status=scheduled          # Filter by status
?category=inspection       # Filter by category
?start_date=2025-01-01     # Filter by start date
?end_date=2025-12-31       # Filter by end date
```

---

## Troubleshooting

### Issue: Activities Not Auto-Scheduling

**Solution 1**: Check signals are loaded
```python
# In calendar_scheduler/apps.py
def ready(self):
    import calendar_scheduler.signals  # Must be present
```

**Solution 2**: Check auto-schedule setting
```python
from calendar_scheduler.models import CalendarSettings
settings = CalendarSettings.get_settings()
print(settings.auto_schedule_on_onboarding)  # Should be True
```

**Solution 3**: Check vehicle has onboarding_date
```python
vehicle = Vehicle.objects.get(id=1)
print(vehicle.onboarding_date)  # Should not be None
```

### Issue: Import Errors

**Solution**: Adjust imports to match your app structure
```python
# Change from:
from vehicles.models import Vehicle

# To match your structure:
from your_app_name.models import YourVehicleModel as Vehicle
```

### Issue: Duplicate Activities Being Created

**Solution**: Check for existing activities before creating
```python
# Already handled in scheduler, but verify:
if not ScheduledActivity.objects.filter(...).exists():
    ScheduledActivity.objects.create(...)
```

### Issue: Maintenance Types Not Syncing

**Solution**: Run sync command manually
```bash
python manage.py sync_maintenance_types
```

Or create them manually:
```python
from maintenance.models import MaintenanceType
from calendar_scheduler.models import ActivityType

for mt in MaintenanceType.objects.all():
    ActivityType.objects.get_or_create(
        maintenance_type=mt,
        defaults={'name': mt.name, 'category': 'maintenance', ...}
    )
```

---

## Production Considerations

### Performance Optimization

1. **Database Indexing**: Already included in model Meta
```python
indexes = [
    models.Index(fields=['vehicle', 'scheduled_date']),
    models.Index(fields=['status', 'scheduled_date']),
]
```

2. **Query Optimization**: Use `select_related` and `prefetch_related`
```python
ScheduledActivity.objects.select_related(
    'vehicle', 'activity_type', 'maintenance_schedule'
)
```

3. **Caching**: Add Redis caching for calendar queries
```python
from django.core.cache import cache

def get_monthly_calendar(year, month):
    cache_key = f'calendar_{year}_{month}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    # ... fetch from database ...
    cache.set(cache_key, data, timeout=3600)
    return data
```

### Background Tasks

Move scheduling to Celery for large fleets:

```python
# tasks.py
from celery import shared_task

@shared_task
def schedule_vehicle_activities(vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    scheduler = ActivityScheduler()
    scheduler.schedule_all_activities_for_vehicle(vehicle)
```

### Monitoring

Add logging to track scheduling operations:

```python
import logging
logger = logging.getLogger(__name__)

def schedule_all_activities_for_vehicle(self, vehicle):
    logger.info(f"Starting scheduling for vehicle {vehicle.id}")
    # ... scheduling logic ...
    logger.info(f"Completed scheduling for vehicle {vehicle.id}: {count} activities")
```

---

## Next Steps

1. **Notifications**: Add email/SMS reminders for upcoming activities
2. **Technician Assignment**: Link activities to technicians
3. **Parts Integration**: Link activities to required parts
4. **Mobile App**: Create mobile endpoints for mechanics
5. **Reporting**: Add activity completion reports
6. **Calendar UI**: Build frontend calendar interface
7. **Webhook Integration**: Notify external systems of activity updates

---

## Summary

This integration guide provides a **non-invasive** approach to adding calendar scheduling functionality to your existing Django auto care platform. The calendar system:

- **Integrates** with existing Vehicle and Maintenance apps without modifying them
- **Syncs** existing maintenance types automatically
- **Schedules** activities based on vehicle onboarding dates
- **Provides** comprehensive API for calendar operations
- **Maintains** data integrity through proper foreign keys and signals
- **Scales** efficiently with proper indexing and query optimization

The calendar app can be deployed independently and removed if needed without affecting your core Vehicle and Maintenance functionality.