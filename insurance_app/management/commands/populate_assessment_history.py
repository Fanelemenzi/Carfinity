from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from assessments.models import VehicleAssessment
from insurance_app.models import AssessmentHistory, AssessmentVersion


class Command(BaseCommand):
    help = 'Populate sample assessment history data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--assessment-id',
            type=str,
            help='Specific assessment ID to populate history for',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of assessments to populate history for (default: 5)',
        )
    
    def handle(self, *args, **options):
        assessment_id = options.get('assessment_id')
        count = options.get('count')
        
        if assessment_id:
            # Populate history for specific assessment
            try:
                assessment = VehicleAssessment.objects.get(assessment_id=assessment_id)
                self.populate_assessment_history(assessment)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully populated history for assessment {assessment_id}')
                )
            except VehicleAssessment.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Assessment {assessment_id} not found')
                )
        else:
            # Populate history for multiple assessments
            assessments = VehicleAssessment.objects.filter(
                assigned_agent__isnull=False
            ).order_by('-assessment_date')[:count]
            
            if not assessments:
                self.stdout.write(
                    self.style.WARNING('No assessments with assigned agents found')
                )
                return
            
            for assessment in assessments:
                self.populate_assessment_history(assessment)
                self.stdout.write(f'Populated history for {assessment.assessment_id}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully populated history for {len(assessments)} assessments')
            )
    
    def populate_assessment_history(self, assessment):
        """Create sample history entries for an assessment"""
        
        # Get users for history entries
        agent = assessment.assigned_agent
        assessor = assessment.user
        
        if not agent:
            self.stdout.write(
                self.style.WARNING(f'No assigned agent for assessment {assessment.assessment_id}')
            )
            return
        
        # Clear existing history to avoid duplicates
        AssessmentHistory.objects.filter(assessment=assessment).delete()
        AssessmentVersion.objects.filter(assessment=assessment).delete()
        
        # Create timeline of activities (in chronological order)
        base_time = assessment.assessment_date
        
        # 1. Initial assessment creation
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='status_change',
            user=assessor,
            description='Assessment created and submitted for review',
            old_value='',
            new_value='pending_review',
            field_name='agent_status'
        )
        
        # Create initial version
        AssessmentVersion.objects.create(
            assessment=assessment,
            version_number=1,
            created_by=assessor,
            assessment_data={
                'assessment_id': assessment.assessment_id,
                'estimated_repair_cost': float(assessment.estimated_repair_cost) if assessment.estimated_repair_cost else 5000.0,
                'agent_status': 'pending_review',
                'agent_notes': '',
                'incident_description': assessment.incident_description or 'Vehicle damage assessment',
            },
            change_summary='Initial assessment submission',
            is_major_version=True
        )
        
        # 2. Agent assignment (1 hour later)
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type='status_change'
        ).update(timestamp=base_time + timedelta(hours=1))
        
        AssessmentHistory.objects.create(
            assessment=assessment,
            activity_type='agent_assignment',
            user=agent,
            timestamp=base_time + timedelta(hours=2),
            description=f'Assessment assigned to agent {agent.get_full_name() or agent.username}',
            new_value=agent.username
        )
        
        # 3. Status change to under review (2 hours later)
        create_assessment_history_entry(
            assessment=assessment,
            activity_type='status_change',
            user=agent,
            description='Assessment review started',
            old_value='pending_review',
            new_value='under_review',
            field_name='agent_status'
        )
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type='status_change',
            description='Assessment review started'
        ).update(timestamp=base_time + timedelta(hours=3))
        
        # 4. Cost adjustment (4 hours later)
        old_cost = assessment.estimated_repair_cost or 5000
        new_cost = old_cost * random.uniform(0.8, 1.2)  # Adjust by ±20%
        
        create_assessment_history_entry(
            assessment=assessment,
            activity_type='cost_adjustment',
            user=agent,
            description='Repair cost estimate adjusted based on market rates',
            old_value=f'£{old_cost:,.2f}',
            new_value=f'£{new_cost:,.2f}',
            field_name='estimated_repair_cost',
            notes='Adjusted based on current parts pricing and labor rates'
        )
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type='cost_adjustment'
        ).update(timestamp=base_time + timedelta(hours=5))
        
        # Update assessment cost
        assessment.estimated_repair_cost = new_cost
        assessment.save()
        
        # Create version for cost adjustment
        create_assessment_version(
            assessment=assessment,
            user=agent,
            change_summary='Cost adjustment based on market rates'
        )
        
        # 5. Comment added (6 hours later)
        create_assessment_history_entry(
            assessment=assessment,
            activity_type='comment_added',
            user=agent,
            description='Agent added review comment',
            notes='Reviewed all damage points. Some additional photos would be helpful for the rear bumper damage assessment.'
        )
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type='comment_added'
        ).update(timestamp=base_time + timedelta(hours=7))
        
        # 6. Photo uploaded (8 hours later)
        create_assessment_history_entry(
            assessment=assessment,
            activity_type='photo_uploaded',
            user=assessor,
            description='Additional photos uploaded',
            related_section='exterior',
            notes='Added requested rear bumper damage photos'
        )
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type='photo_uploaded'
        ).update(timestamp=base_time + timedelta(hours=9))
        
        # 7. Section updated (10 hours later)
        create_assessment_history_entry(
            assessment=assessment,
            activity_type='section_updated',
            user=agent,
            description='Exterior damage section updated with additional findings',
            related_section='exterior',
            notes='Updated rear bumper damage severity from moderate to severe based on new photos'
        )
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type='section_updated'
        ).update(timestamp=base_time + timedelta(hours=11))
        
        # 8. Document update (12 hours later)
        create_assessment_history_entry(
            assessment=assessment,
            activity_type='document_update',
            user=agent,
            description='Assessment notes updated',
            field_name='agent_notes',
            old_value='Initial review in progress',
            new_value='Comprehensive review completed. All damage points assessed and documented.',
        )
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type='document_update'
        ).update(timestamp=base_time + timedelta(hours=13))
        
        # 9. Final approval or request changes (1 day later)
        final_action = random.choice(['approved', 'changes_requested'])
        
        if final_action == 'approved':
            create_assessment_history_entry(
                assessment=assessment,
                activity_type='approval_granted',
                user=agent,
                description='Assessment approved and ready for processing',
                old_value='under_review',
                new_value='approved',
                field_name='agent_status',
                notes='All documentation complete. Assessment meets quality standards.'
            )
            assessment.agent_status = 'approved'
        else:
            create_assessment_history_entry(
                assessment=assessment,
                activity_type='changes_requested',
                user=agent,
                description='Changes requested before approval',
                old_value='under_review',
                new_value='changes_requested',
                field_name='agent_status',
                notes='Please provide additional photos of the engine bay damage and update the mechanical systems assessment.'
            )
            assessment.agent_status = 'changes_requested'
        
        AssessmentHistory.objects.filter(
            assessment=assessment,
            activity_type__in=['approval_granted', 'changes_requested']
        ).update(timestamp=base_time + timedelta(days=1))
        
        # 10. Report generated (if approved)
        if final_action == 'approved':
            create_assessment_history_entry(
                assessment=assessment,
                activity_type='report_generated',
                user=agent,
                description='PDF assessment report generated and shared',
                notes='Report sent to customer and insurance provider'
            )
            AssessmentHistory.objects.filter(
                assessment=assessment,
                activity_type='report_generated'
            ).update(timestamp=base_time + timedelta(days=1, hours=2))
        
        # Create final version
        create_assessment_version(
            assessment=assessment,
            user=agent,
            change_summary=f'Final assessment {final_action}',
            is_major=True
        )
        
        # Save assessment changes
        assessment.save()
        
        self.stdout.write(f'Created {AssessmentHistory.objects.filter(assessment=assessment).count()} history entries')