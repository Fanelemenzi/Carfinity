"""
Simple script to create test assessment history data
"""
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from assessments.models import VehicleAssessment
from insurance_app.models import AssessmentHistory, AssessmentVersion


def create_sample_history():
    """Create sample assessment history for testing"""
    
    # Get or create a test assessment
    try:
        # Try to get an existing assessment
        assessment = VehicleAssessment.objects.first()
        if not assessment:
            print("No assessments found. Please create an assessment first.")
            return
        
        # Get or create users
        agent_user, created = User.objects.get_or_create(
            username='test_agent',
            defaults={
                'first_name': 'Test',
                'last_name': 'Agent',
                'email': 'agent@test.com'
            }
        )
        
        assessor_user = assessment.user
        
        # Assign agent if not already assigned
        if not assessment.assigned_agent:
            assessment.assigned_agent = agent_user
            assessment.save()
        
        # Clear existing history
        AssessmentHistory.objects.filter(assessment=assessment).delete()
        AssessmentVersion.objects.filter(assessment=assessment).delete()
        
        print(f"Creating history for assessment: {assessment.assessment_id}")
        
        # Create history entries
        base_time = assessment.assessment_date or timezone.now()
        
        # 1. Initial submission
        history1 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='status_change',
            user=assessor_user,
            timestamp=base_time,
            description='Assessment created and submitted for review',
            field_name='agent_status',
            old_value='',
            new_value='pending_review'
        )
        
        # 2. Agent assignment
        history2 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='agent_assignment',
            user=agent_user,
            timestamp=base_time + timedelta(hours=1),
            description=f'Assessment assigned to agent {agent_user.get_full_name()}',
            new_value=agent_user.username
        )
        
        # 3. Review started
        history3 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='status_change',
            user=agent_user,
            timestamp=base_time + timedelta(hours=2),
            description='Assessment review started',
            field_name='agent_status',
            old_value='pending_review',
            new_value='under_review'
        )
        
        # 4. Cost adjustment
        history4 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='cost_adjustment',
            user=agent_user,
            timestamp=base_time + timedelta(hours=4),
            description='Repair cost estimate adjusted',
            field_name='estimated_repair_cost',
            old_value='£5,000.00',
            new_value='£6,200.00',
            notes='Adjusted based on current market rates for parts and labor'
        )
        
        # 5. Comment added
        history5 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='comment_added',
            user=agent_user,
            timestamp=base_time + timedelta(hours=6),
            description='Agent added review comment',
            notes='Reviewed all damage points. Assessment looks comprehensive and well-documented.'
        )
        
        # 6. Document update
        history6 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='document_update',
            user=agent_user,
            timestamp=base_time + timedelta(hours=8),
            description='Assessment notes updated',
            field_name='agent_notes',
            old_value='Initial review in progress',
            new_value='Comprehensive review completed. All damage points assessed.'
        )
        
        # 7. Final approval
        history7 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='approval_granted',
            user=agent_user,
            timestamp=base_time + timedelta(days=1),
            description='Assessment approved and ready for processing',
            field_name='agent_status',
            old_value='under_review',
            new_value='approved',
            notes='All documentation complete. Assessment meets quality standards.'
        )
        
        # 8. Report generated
        history8 = AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='report_generated',
            user=agent_user,
            timestamp=base_time + timedelta(days=1, hours=1),
            description='PDF assessment report generated and shared',
            notes='Report sent to customer and insurance provider'
        )
        
        # Create versions
        version1 = AssessmentVersion.objects.create(
            assessment=assessment,
            version_number=1,
            created_by=assessor_user,
            created_at=base_time,
            assessment_data={
                'assessment_id': assessment.assessment_id,
                'estimated_repair_cost': 5000.00,
                'agent_status': 'pending_review',
                'agent_notes': '',
                'incident_description': assessment.incident_description or 'Vehicle damage assessment',
            },
            change_summary='Initial assessment submission',
            is_major_version=True
        )
        
        version2 = AssessmentVersion.objects.create(
            assessment=assessment,
            version_number=2,
            created_by=agent_user,
            created_at=base_time + timedelta(hours=4),
            assessment_data={
                'assessment_id': assessment.assessment_id,
                'estimated_repair_cost': 6200.00,
                'agent_status': 'under_review',
                'agent_notes': 'Cost adjusted based on market rates',
                'incident_description': assessment.incident_description or 'Vehicle damage assessment',
            },
            change_summary='Cost adjustment and review notes added',
            is_major_version=False
        )
        
        version3 = AssessmentVersion.objects.create(
            assessment=assessment,
            version_number=3,
            created_by=agent_user,
            created_at=base_time + timedelta(days=1),
            assessment_data={
                'assessment_id': assessment.assessment_id,
                'estimated_repair_cost': 6200.00,
                'agent_status': 'approved',
                'agent_notes': 'Comprehensive review completed. All damage points assessed.',
                'incident_description': assessment.incident_description or 'Vehicle damage assessment',
            },
            change_summary='Final approval and completion',
            is_major_version=True
        )
        
        # Update assessment status
        assessment.agent_status = 'approved'
        assessment.estimated_repair_cost = 6200.00
        assessment.agent_notes = 'Comprehensive review completed. All damage points assessed.'
        assessment.save()
        
        print(f"Created {AssessmentHistory.objects.filter(assessment=assessment).count()} history entries")
        print(f"Created {AssessmentVersion.objects.filter(assessment=assessment).count()} versions")
        print(f"Assessment URL: /insurance/assessments/{assessment.assessment_id}/history/")
        
        return assessment
        
    except Exception as e:
        print(f"Error creating sample history: {e}")
        return None


if __name__ == "__main__":
    create_sample_history()