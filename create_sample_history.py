#!/usr/bin/env python
"""
Django shell script to create sample assessment history data
Run with: python manage.py shell < create_sample_history.py
"""

import os
import django
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from assessments.models import VehicleAssessment
from insurance_app.models import AssessmentHistory, AssessmentVersion

def create_sample_history():
    """Create sample assessment history for testing"""
    
    print("Creating sample assessment history data...")
    
    # Get or create a test assessment
    try:
        # Try to get an existing assessment
        assessment = VehicleAssessment.objects.first()
        if not assessment:
            print("No assessments found. Creating a test assessment...")
            
            # Get or create test user
            test_user, created = User.objects.get_or_create(
                username='test_assessor',
                defaults={
                    'first_name': 'Test',
                    'last_name': 'Assessor',
                    'email': 'assessor@test.com'
                }
            )
            
            # Create a test assessment (simplified)
            assessment = VehicleAssessment.objects.create(
                assessment_id='TEST-001',
                assessment_type='insurance_claim',
                user=test_user,
                vehicle_id=1,  # Assuming vehicle with ID 1 exists
                assessor_name='Test Assessor',
                overall_severity='moderate',
                estimated_repair_cost=5000.00,
                incident_description='Test vehicle damage for assessment history demo',
                incident_location='Test Location'
            )
            print(f"Created test assessment: {assessment.assessment_id}")
        
        # Get or create agent user
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
        AssessmentHistory.objects.create(
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
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='agent_assignment',
            user=agent_user,
            timestamp=base_time + timedelta(hours=1),
            description=f'Assessment assigned to agent {agent_user.get_full_name()}',
            new_value=agent_user.username
        )
        
        # 3. Review started
        AssessmentHistory.objects.create(
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
        AssessmentHistory.objects.create(
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
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='comment_added',
            user=agent_user,
            timestamp=base_time + timedelta(hours=6),
            description='Agent added review comment',
            notes='Reviewed all damage points. Assessment looks comprehensive and well-documented.'
        )
        
        # 6. Section updated
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='section_updated',
            user=agent_user,
            timestamp=base_time + timedelta(hours=7),
            description='Exterior damage section updated',
            related_section='exterior',
            notes='Updated damage severity for front bumper based on additional analysis'
        )
        
        # 7. Photo uploaded
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='photo_uploaded',
            user=assessor_user,
            timestamp=base_time + timedelta(hours=8),
            description='Additional photos uploaded',
            related_section='exterior',
            notes='Added close-up photos of bumper damage as requested'
        )
        
        # 8. Document update
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='document_update',
            user=agent_user,
            timestamp=base_time + timedelta(hours=10),
            description='Assessment notes updated',
            field_name='agent_notes',
            old_value='Initial review in progress',
            new_value='Comprehensive review completed. All damage points assessed.'
        )
        
        # 9. Workflow action
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='workflow_action',
            user=agent_user,
            timestamp=base_time + timedelta(hours=12),
            description='Assessment moved to final review stage',
            notes='All required documentation and photos have been provided'
        )
        
        # 10. Final approval
        AssessmentHistory.objects.create(
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
        
        # 11. Report generated
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='report_generated',
            user=agent_user,
            timestamp=base_time + timedelta(days=1, hours=1),
            description='PDF assessment report generated and shared',
            notes='Report sent to customer and insurance provider'
        )
        
        # Create versions
        AssessmentVersion.objects.create(
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
                'incident_location': assessment.incident_location or 'Unknown location',
            },
            change_summary='Initial assessment submission',
            is_major_version=True
        )
        
        AssessmentVersion.objects.create(
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
                'incident_location': assessment.incident_location or 'Unknown location',
            },
            change_summary='Cost adjustment and review notes added',
            is_major_version=False
        )
        
        AssessmentVersion.objects.create(
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
                'incident_location': assessment.incident_location or 'Unknown location',
            },
            change_summary='Final approval and completion',
            is_major_version=True
        )
        
        # Update assessment status
        assessment.agent_status = 'approved'
        assessment.estimated_repair_cost = 6200.00
        assessment.agent_notes = 'Comprehensive review completed. All damage points assessed.'
        assessment.save()
        
        history_count = AssessmentHistory.objects.filter(assessment=assessment).count()
        version_count = AssessmentVersion.objects.filter(assessment=assessment).count()
        
        print(f"✓ Created {history_count} history entries")
        print(f"✓ Created {version_count} versions")
        print(f"✓ Assessment ID: {assessment.assessment_id}")
        print(f"✓ Assessment URL: /insurance/assessments/{assessment.assessment_id}/history/")
        
        return assessment
        
    except Exception as e:
        print(f"❌ Error creating sample history: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run the function
if __name__ == "__main__":
    create_sample_history()
else:
    # When run via shell
    create_sample_history()