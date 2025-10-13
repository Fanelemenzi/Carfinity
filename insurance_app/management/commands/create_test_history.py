from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from assessments.models import VehicleAssessment
from insurance_app.models import AssessmentHistory, AssessmentVersion


class Command(BaseCommand):
    help = 'Create simple test assessment history data'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating test assessment history data...')
        
        try:
            # Get or create test assessment
            assessment = VehicleAssessment.objects.first()
            if not assessment:
                self.stdout.write(self.style.ERROR('No assessments found. Please create an assessment first.'))
                return
            
            # Get or create test users
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
            
            self.stdout.write(f'Creating history for assessment: {assessment.assessment_id}')
            
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
            
            # 6. Final approval
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
                },
                change_summary='Initial assessment submission',
                is_major_version=True
            )
            
            AssessmentVersion.objects.create(
                assessment=assessment,
                version_number=2,
                created_by=agent_user,
                created_at=base_time + timedelta(days=1),
                assessment_data={
                    'assessment_id': assessment.assessment_id,
                    'estimated_repair_cost': 6200.00,
                    'agent_status': 'approved',
                },
                change_summary='Final approval',
                is_major_version=True
            )
            
            # Update assessment
            assessment.agent_status = 'approved'
            assessment.estimated_repair_cost = 6200.00
            assessment.save()
            
            history_count = AssessmentHistory.objects.filter(assessment=assessment).count()
            version_count = AssessmentVersion.objects.filter(assessment=assessment).count()
            
            self.stdout.write(self.style.SUCCESS(f'Created {history_count} history entries'))
            self.stdout.write(self.style.SUCCESS(f'Created {version_count} versions'))
            self.stdout.write(self.style.SUCCESS(f'Assessment ID: {assessment.assessment_id}'))
            self.stdout.write(self.style.SUCCESS(f'History URL: /insurance/assessments/{assessment.assessment_id}/history/'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            traceback.print_exc()