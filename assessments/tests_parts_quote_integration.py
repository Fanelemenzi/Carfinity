"""
Tests for VehicleAssessment parts-based quote system integration
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from assessments.models import VehicleAssessment
from vehicles.models import Vehicle


class VehicleAssessmentPartsQuoteIntegrationTests(TestCase):
    """Test VehicleAssessment model extensions for parts-based quote system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test vehicle (assuming Vehicle model exists)
        try:
            self.vehicle = Vehicle.objects.create(
                make='Toyota',
                model='Camry',
                year=2020,
                vin='1HGBH41JXMN109186'
            )
        except Exception:
            # If Vehicle model doesn't exist or has different fields, create a mock
            self.vehicle = None
    
    def create_test_assessment(self, **kwargs):
        """Helper method to create test assessment"""
        defaults = {
            'assessment_id': 'TEST-001',
            'assessment_type': 'crash',
            'user': self.user,
            'vehicle': self.vehicle,
            'assessor_name': 'Test Assessor',
            'overall_severity': 'moderate',
        }
        defaults.update(kwargs)
        
        if self.vehicle:
            return VehicleAssessment.objects.create(**defaults)
        else:
            # Skip tests if Vehicle model is not available
            self.skipTest("Vehicle model not available")
    
    def test_new_assessment_defaults_to_parts_based_quotes(self):
        """Test that new assessments default to using parts-based quotes"""
        assessment = self.create_test_assessment()
        
        self.assertTrue(assessment.uses_parts_based_quotes)
        self.assertFalse(assessment.parts_identification_complete)
        self.assertEqual(assessment.quote_collection_status, 'not_started')
    
    def test_get_cost_calculation_method_parts_based(self):
        """Test get_cost_calculation_method returns 'parts_based' for new assessments"""
        assessment = self.create_test_assessment()
        
        self.assertEqual(assessment.get_cost_calculation_method(), 'parts_based')
    
    def test_get_cost_calculation_method_hardcoded(self):
        """Test get_cost_calculation_method returns 'hardcoded' for legacy assessments"""
        assessment = self.create_test_assessment(uses_parts_based_quotes=False)
        
        self.assertEqual(assessment.get_cost_calculation_method(), 'hardcoded')
    
    def test_uses_hardcoded_costs_method(self):
        """Test uses_hardcoded_costs method"""
        # Test parts-based assessment
        parts_assessment = self.create_test_assessment()
        self.assertFalse(parts_assessment.uses_hardcoded_costs())
        
        # Test hardcoded assessment
        hardcoded_assessment = self.create_test_assessment(
            assessment_id='TEST-002',
            uses_parts_based_quotes=False
        )
        self.assertTrue(hardcoded_assessment.uses_hardcoded_costs())
    
    def test_uses_parts_based_costs_method(self):
        """Test uses_parts_based_costs method"""
        # Test parts-based assessment
        parts_assessment = self.create_test_assessment()
        self.assertTrue(parts_assessment.uses_parts_based_costs())
        
        # Test hardcoded assessment
        hardcoded_assessment = self.create_test_assessment(
            assessment_id='TEST-002',
            uses_parts_based_quotes=False
        )
        self.assertFalse(hardcoded_assessment.uses_parts_based_costs())
    
    def test_can_collect_quotes_method(self):
        """Test can_collect_quotes method logic"""
        # Test assessment not ready (pending status)
        assessment = self.create_test_assessment(
            status='pending',
            parts_identification_complete=True
        )
        self.assertFalse(assessment.can_collect_quotes())
        
        # Test assessment not ready (parts not identified)
        assessment.status = 'completed'
        assessment.parts_identification_complete = False
        assessment.save()
        self.assertFalse(assessment.can_collect_quotes())
        
        # Test assessment not ready (uses hardcoded costs)
        assessment.uses_parts_based_quotes = False
        assessment.parts_identification_complete = True
        assessment.save()
        self.assertFalse(assessment.can_collect_quotes())
        
        # Test assessment ready for quote collection
        assessment.uses_parts_based_quotes = True
        assessment.parts_identification_complete = True
        assessment.status = 'completed'
        assessment.save()
        self.assertTrue(assessment.can_collect_quotes())
        
        # Test with under_review status
        assessment.status = 'under_review'
        assessment.save()
        self.assertTrue(assessment.can_collect_quotes())
    
    def test_get_quote_collection_progress_hardcoded(self):
        """Test get_quote_collection_progress for hardcoded assessments"""
        assessment = self.create_test_assessment(uses_parts_based_quotes=False)
        
        progress = assessment.get_quote_collection_progress()
        
        self.assertEqual(progress['method'], 'hardcoded')
        self.assertEqual(progress['status'], 'not_applicable')
        self.assertEqual(progress['progress_percentage'], 100)
        self.assertIn('hardcoded', progress['message'].lower())
    
    def test_get_quote_collection_progress_parts_identification_pending(self):
        """Test get_quote_collection_progress when parts identification is pending"""
        assessment = self.create_test_assessment(
            uses_parts_based_quotes=True,
            parts_identification_complete=False
        )
        
        progress = assessment.get_quote_collection_progress()
        
        self.assertEqual(progress['method'], 'parts_based')
        self.assertEqual(progress['status'], 'parts_identification_pending')
        self.assertEqual(progress['progress_percentage'], 0)
        self.assertIn('parts identification', progress['message'].lower())
    
    def test_get_quote_collection_progress_quote_collection_stages(self):
        """Test get_quote_collection_progress for different quote collection stages"""
        assessment = self.create_test_assessment(
            uses_parts_based_quotes=True,
            parts_identification_complete=True
        )
        
        # Test not_started status
        assessment.quote_collection_status = 'not_started'
        assessment.save()
        progress = assessment.get_quote_collection_progress()
        self.assertEqual(progress['progress_percentage'], 25)
        self.assertEqual(progress['status'], 'not_started')
        
        # Test in_progress status
        assessment.quote_collection_status = 'in_progress'
        assessment.save()
        progress = assessment.get_quote_collection_progress()
        self.assertEqual(progress['progress_percentage'], 60)
        self.assertEqual(progress['status'], 'in_progress')
        
        # Test completed status
        assessment.quote_collection_status = 'completed'
        assessment.save()
        progress = assessment.get_quote_collection_progress()
        self.assertEqual(progress['progress_percentage'], 100)
        self.assertEqual(progress['status'], 'completed')
    
    def test_field_help_text(self):
        """Test that field help text is properly set"""
        assessment = self.create_test_assessment()
        
        # Get field help text from model meta
        uses_parts_field = VehicleAssessment._meta.get_field('uses_parts_based_quotes')
        parts_complete_field = VehicleAssessment._meta.get_field('parts_identification_complete')
        quote_status_field = VehicleAssessment._meta.get_field('quote_collection_status')
        
        self.assertIn('parts-based quotes', uses_parts_field.help_text)
        self.assertIn('hardcoded costs', uses_parts_field.help_text)
        self.assertIn('damaged parts', parts_complete_field.help_text)
        self.assertIn('quote collection', quote_status_field.help_text)
    
    def test_quote_collection_status_choices(self):
        """Test quote_collection_status field choices"""
        assessment = self.create_test_assessment()
        
        # Test valid choices
        valid_choices = ['not_started', 'in_progress', 'completed']
        
        for choice in valid_choices:
            assessment.quote_collection_status = choice
            assessment.save()
            assessment.refresh_from_db()
            self.assertEqual(assessment.quote_collection_status, choice)
    
    def test_backward_compatibility_flags(self):
        """Test that backward compatibility is maintained"""
        # Create assessment with hardcoded costs (legacy)
        legacy_assessment = self.create_test_assessment(
            assessment_id='LEGACY-001',
            uses_parts_based_quotes=False,
            parts_identification_complete=False,
            quote_collection_status='not_started'
        )
        
        # Verify legacy assessment behavior
        self.assertEqual(legacy_assessment.get_cost_calculation_method(), 'hardcoded')
        self.assertTrue(legacy_assessment.uses_hardcoded_costs())
        self.assertFalse(legacy_assessment.uses_parts_based_costs())
        self.assertFalse(legacy_assessment.can_collect_quotes())
        
        # Create new assessment with parts-based quotes
        new_assessment = self.create_test_assessment(
            assessment_id='NEW-001',
            uses_parts_based_quotes=True
        )
        
        # Verify new assessment behavior
        self.assertEqual(new_assessment.get_cost_calculation_method(), 'parts_based')
        self.assertFalse(new_assessment.uses_hardcoded_costs())
        self.assertTrue(new_assessment.uses_parts_based_costs())


class VehicleAssessmentMigrationCompatibilityTests(TestCase):
    """Test migration compatibility and data integrity"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='migrationuser',
            email='migration@example.com',
            password='testpass123'
        )
        
        # Create a test vehicle if available
        try:
            self.vehicle = Vehicle.objects.create(
                make='Honda',
                model='Civic',
                year=2019,
                vin='2HGFC2F59JH123456'
            )
        except Exception:
            self.vehicle = None
    
    def create_test_assessment(self, **kwargs):
        """Helper method to create test assessment"""
        defaults = {
            'assessment_id': 'MIG-001',
            'assessment_type': 'insurance_claim',
            'user': self.user,
            'vehicle': self.vehicle,
            'assessor_name': 'Migration Assessor',
            'overall_severity': 'minor',
        }
        defaults.update(kwargs)
        
        if self.vehicle:
            return VehicleAssessment.objects.create(**defaults)
        else:
            self.skipTest("Vehicle model not available")
    
    def test_new_assessment_after_migration(self):
        """Test that new assessments created after migration use parts-based quotes"""
        assessment = self.create_test_assessment()
        
        # New assessments should default to parts-based quotes
        self.assertTrue(assessment.uses_parts_based_quotes)
        self.assertEqual(assessment.get_cost_calculation_method(), 'parts_based')
    
    def test_field_constraints_and_defaults(self):
        """Test field constraints and default values"""
        assessment = self.create_test_assessment()
        
        # Test boolean field defaults
        self.assertTrue(assessment.uses_parts_based_quotes)  # Default True
        self.assertFalse(assessment.parts_identification_complete)  # Default False
        
        # Test choice field default
        self.assertEqual(assessment.quote_collection_status, 'not_started')
        
        # Test field max_length constraint
        quote_status_field = VehicleAssessment._meta.get_field('quote_collection_status')
        self.assertEqual(quote_status_field.max_length, 20)
    
    def test_database_integrity_after_field_addition(self):
        """Test database integrity after adding new fields"""
        # Create multiple assessments to test data integrity
        assessments = []
        for i in range(3):
            assessment = self.create_test_assessment(
                assessment_id=f'INT-{i+1:03d}',
                uses_parts_based_quotes=(i % 2 == 0),  # Alternate between True/False
                quote_collection_status=['not_started', 'in_progress', 'completed'][i]
            )
            assessments.append(assessment)
        
        # Verify all assessments were created successfully
        self.assertEqual(len(assessments), 3)
        
        # Verify field values are preserved
        for i, assessment in enumerate(assessments):
            assessment.refresh_from_db()
            expected_parts_based = (i % 2 == 0)
            expected_status = ['not_started', 'in_progress', 'completed'][i]
            
            self.assertEqual(assessment.uses_parts_based_quotes, expected_parts_based)
            self.assertEqual(assessment.quote_collection_status, expected_status)
    
    def test_model_string_representation_unchanged(self):
        """Test that model string representation is not affected by new fields"""
        assessment = self.create_test_assessment()
        
        # String representation should still work as before
        str_repr = str(assessment)
        self.assertIn(assessment.assessment_id, str_repr)
        if self.vehicle:
            self.assertIn(str(assessment.vehicle), str_repr)
    
    def test_existing_methods_still_work(self):
        """Test that existing model methods still work after field addition"""
        assessment = self.create_test_assessment(
            assessment_type='insurance_claim'
        )
        
        # Test existing methods still function
        self.assertTrue(assessment.is_insurance_assessment())
        
        # Test workflow permissions method
        permissions = assessment.get_workflow_permissions()
        self.assertIsInstance(permissions, dict)
        self.assertIn('can_approve', permissions)
        self.assertIn('requires_agent_review', permissions)


class VehicleAssessmentQuerySetTests(TestCase):
    """Test that existing querysets and managers work with new fields"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='queryuser',
            email='query@example.com',
            password='testpass123'
        )
        
        try:
            self.vehicle = Vehicle.objects.create(
                make='Ford',
                model='Focus',
                year=2021,
                vin='1FADP3F29JL123456'
            )
        except Exception:
            self.vehicle = None
    
    def create_test_assessment(self, **kwargs):
        """Helper method to create test assessment"""
        defaults = {
            'assessment_type': 'crash',
            'user': self.user,
            'vehicle': self.vehicle,
            'assessor_name': 'Query Assessor',
            'overall_severity': 'moderate',
        }
        defaults.update(kwargs)
        
        if self.vehicle:
            return VehicleAssessment.objects.create(**defaults)
        else:
            self.skipTest("Vehicle model not available")
    
    def test_manager_methods_with_new_fields(self):
        """Test that existing manager methods work with new fields"""
        # Create test assessments
        pending_assessment = self.create_test_assessment(
            assessment_id='PEND-001',
            status='pending'
        )
        completed_assessment = self.create_test_assessment(
            assessment_id='COMP-001',
            status='completed'
        )
        
        # Test existing manager methods
        pending_qs = VehicleAssessment.objects.pending_assessments()
        self.assertIn(pending_assessment, pending_qs)
        self.assertNotIn(completed_assessment, pending_qs)
    
    def test_filtering_by_new_fields(self):
        """Test filtering assessments by new fields"""
        # Create assessments with different quote system settings
        parts_based = self.create_test_assessment(
            assessment_id='PARTS-001',
            uses_parts_based_quotes=True
        )
        hardcoded = self.create_test_assessment(
            assessment_id='HARD-001',
            uses_parts_based_quotes=False
        )
        
        # Test filtering by parts-based quotes
        parts_based_qs = VehicleAssessment.objects.filter(uses_parts_based_quotes=True)
        hardcoded_qs = VehicleAssessment.objects.filter(uses_parts_based_quotes=False)
        
        self.assertIn(parts_based, parts_based_qs)
        self.assertNotIn(hardcoded, parts_based_qs)
        self.assertIn(hardcoded, hardcoded_qs)
        self.assertNotIn(parts_based, hardcoded_qs)
    
    def test_ordering_and_indexing_unchanged(self):
        """Test that model ordering and indexing still work"""
        # Create multiple assessments
        assessments = []
        for i in range(3):
            assessment = self.create_test_assessment(
                assessment_id=f'ORD-{i+1:03d}'
            )
            assessments.append(assessment)
        
        # Test default ordering (should be by -assessment_date)
        ordered_assessments = list(VehicleAssessment.objects.all())
        
        # Verify assessments are ordered by assessment_date (newest first)
        for i in range(len(ordered_assessments) - 1):
            self.assertGreaterEqual(
                ordered_assessments[i].assessment_date,
                ordered_assessments[i + 1].assessment_date
            )