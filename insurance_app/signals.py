# signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from assessments.models import VehicleAssessment
from .models import AssessmentHistory, AssessmentVersion, AssessmentComment, AssessmentWorkflow
import json
from decimal import Decimal


class AssessmentTracker:
    """Utility class to track assessment changes"""
    
    _original_values = {}
    
    @classmethod
    def store_original_values(cls, instance):
        """Store original values before save"""
        if instance.pk:
            cls._original_values[instance.pk] = cls._serialize_instance(instance)
    
    @classmethod
    def _serialize_instance(cls, instance):
        """Serialize instance for comparison"""
        data = {}
        for field in instance._meta.fields:
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                data[field.name] = str(value)
            elif hasattr(value, 'isoformat'):  # datetime objects
                data[field.name] = value.isoformat()
            else:
                data[field.name] = value
        return data
    
    @classmethod
    def get_changes(cls, instance):
        """Get changes between original and current values"""
        if instance.pk not in cls._original_values:
            return []
        
        original = cls._original_values[instance.pk]
        current = cls._serialize_instance(instance)
        
        changes = []
        for field_name, new_value in current.items():
            old_value = original.get(field_name)
            if old_value != new_value:
                changes.append({
                    'field_name': field_name,
                    'old_value': str(old_value) if old_value is not None else '',
                    'new_value': str(new_value) if new_value is not None else '',
                })
        
        return changes
    
    @classmethod
    def clear_original_values(cls, instance):
        """Clear stored original values"""
        if instance.pk in cls._original_values:
            del cls._original_values[instance.pk]


@receiver(pre_save, sender=VehicleAssessment)
def store_assessment_original_values(sender, instance, **kwargs):
    """Store original assessment values before save"""
    AssessmentTracker.store_original_values(instance)


@receiver(post_save, sender=VehicleAssessment)
def track_assessment_changes(sender, instance, created, **kwargs):
    """Track changes to vehicle assessments"""
    
    # Get current user from thread local storage or use system user
    user = getattr(instance, '_current_user', None)
    if not user:
        try:
            user = User.objects.get(username='system')
        except User.DoesNotExist:
            user = User.objects.filter(is_superuser=True).first()
    
    if not user:
        return
    
    if created:
        # Assessment was created
        AssessmentHistory.objects.create(
            assessment=instance,
            activity_type='status_change',
            user=user,
            description=f"Assessment {instance.assessment_id} created",
            new_value=instance.status,
            ip_address=getattr(instance, '_client_ip', None),
            user_agent=getattr(instance, '_user_agent', '')
        )
        
        # Create initial version
        create_assessment_version(instance, user, "Initial assessment creation")
        
    else:
        # Assessment was updated
        changes = AssessmentTracker.get_changes(instance)
        
        for change in changes:
            activity_type = 'status_change' if change['field_name'] == 'status' else 'document_update'
            if 'cost' in change['field_name'].lower() or 'value' in change['field_name'].lower():
                activity_type = 'cost_adjustment'
            elif change['field_name'] == 'assigned_agent':
                activity_type = 'agent_assignment'
            
            AssessmentHistory.objects.create(
                assessment=instance,
                activity_type=activity_type,
                user=user,
                field_name=change['field_name'],
                old_value=change['old_value'],
                new_value=change['new_value'],
                description=f"Field '{change['field_name']}' changed from '{change['old_value']}' to '{change['new_value']}'",
                ip_address=getattr(instance, '_client_ip', None),
                user_agent=getattr(instance, '_user_agent', '')
            )
        
        # Create version if significant changes
        if changes and should_create_version(changes):
            change_summary = f"Updated {len(changes)} field(s): {', '.join([c['field_name'] for c in changes])}"
            create_assessment_version(instance, user, change_summary)
    
    # Clear stored values
    AssessmentTracker.clear_original_values(instance)


@receiver(post_save, sender=AssessmentComment)
def track_comment_creation(sender, instance, created, **kwargs):
    """Track comment creation"""
    if created:
        AssessmentHistory.objects.create(
            assessment=instance.assessment,
            activity_type='comment_added',
            user=instance.author,
            description=f"Comment added: {instance.content[:100]}{'...' if len(instance.content) > 100 else ''}",
            related_comment_id=instance.id,
            related_section=getattr(instance, 'related_section', ''),
        )


@receiver(post_save, sender=AssessmentWorkflow)
def track_workflow_changes(sender, instance, created, **kwargs):
    """Track workflow step changes"""
    if created:
        AssessmentHistory.objects.create(
            assessment=instance.assessment,
            activity_type='workflow_action',
            user=instance.completed_by,
            description=f"Workflow step: {instance.get_step_display()}",
            new_value=instance.step,
            notes=instance.notes,
        )


def should_create_version(changes):
    """Determine if changes warrant creating a new version"""
    significant_fields = [
        'status', 'agent_status', 'overall_severity', 
        'estimated_repair_cost', 'vehicle_market_value', 
        'salvage_value', 'overall_notes', 'recommendations'
    ]
    
    return any(change['field_name'] in significant_fields for change in changes)


def create_assessment_version(assessment, user, change_summary):
    """Create a new assessment version"""
    from .views import AssessmentRollbackView
    
    # Get current version number
    last_version = AssessmentVersion.objects.filter(
        assessment=assessment
    ).order_by('-version_number').first()
    
    version_number = (last_version.version_number + 1) if last_version else 1
    
    # Serialize assessment data
    rollback_view = AssessmentRollbackView()
    assessment_data = rollback_view._serialize_assessment(assessment)
    
    # Create version
    version = AssessmentVersion.objects.create(
        assessment=assessment,
        version_number=version_number,
        created_by=user,
        assessment_data=assessment_data,
        change_summary=change_summary,
        is_major_version=version_number % 5 == 0  # Every 5th version is major
    )
    
    return version


# Utility functions for views to set tracking context
def set_assessment_user_context(assessment, user, request=None):
    """Set user context for assessment tracking"""
    assessment._current_user = user
    if request:
        assessment._client_ip = get_client_ip(request)
        assessment._user_agent = request.META.get('HTTP_USER_AGENT', '')


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Context manager for tracking assessment changes
class AssessmentChangeTracker:
    """Context manager for tracking assessment changes with user context"""
    
    def __init__(self, assessment, user, request=None):
        self.assessment = assessment
        self.user = user
        self.request = request
    
    def __enter__(self):
        set_assessment_user_context(self.assessment, self.user, self.request)
        return self.assessment
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up context
        if hasattr(self.assessment, '_current_user'):
            delattr(self.assessment, '_current_user')
        if hasattr(self.assessment, '_client_ip'):
            delattr(self.assessment, '_client_ip')
        if hasattr(self.assessment, '_user_agent'):
            delattr(self.assessment, '_user_agent')