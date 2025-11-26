# tests_parts_identification.py
"""
Comprehensive tests for the PartsIdentificationEngine.

Tests cover parts identification across all assessment section types,
consolidation of duplicate parts, labor hour estimation, and image linking.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import Mock, patch

from .parts_identification import PartsIdentificationEngine
from .models import DamagedPart
from assessments.models import (
    VehicleAssessment, ExteriorBodyDamage, WheelsAndTires, InteriorDamage,
    MechanicalSystems, ElectricalSystems, AssessmentPhoto
)
from vehicles.models import Vehicle


class PartsIdentificationEngineTestCase(TestCase):
    """Test cases for PartsIdentificationEngine functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.engine = PartsIdentificationEngine()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            make='Toyota',
            model='Camry',
            year=2020,
            vin='1HGBH41JXMN109186'
        )
        
        # Create test assessment
        self.assessment = VehicleAssessment.objects.create(
            assessment_id='TEST-001',
            assessment_type='crash',
            status='completed',
            user=self.user,
            vehicle=self.vehicle,
            assessor_name='Test Assessor',
            overall_severity='moderate'
        )
    
    def test_identify_damaged_parts_success(self):
        """Test successful identification of damaged parts."""
        # Create exterior damage with multiple damaged parts
        exterior = ExteriorBodyDamage.objects.create(
            assessment=self.assessment,
            front_bumper='moderate',
            front_bumper_notes='Cracked and dented',
            hood='severe',
            hood_notes='Large dent requiring replacement',
            headlight_housings='light',
            side_mirrors='destroyed'
        )
        
        # Create wheels damage
        wheels = WheelsAndTires.objects.create(
            assessment=self.assessment,
            front_left_tire='severe',
            front_left_tire_notes='Sidewall damage',
            front_left_wheel='moderate',
            rear_right_tire='light'
        )
        
        # Run identification
        parts = self.engine.identify_damaged_parts(self.assessment)
        
        # Verify parts were created
        self.assertEqual(len(parts), 6)  # 4 exterior + 2 wheels
        
        # Check specific parts
        bumper_part = next((p for p in parts if 'bumper' in p.part_name.lower()), None)
        self.assertIsNotNone(bumper_part)
        self.assertEqual(bumper_part.damage_severity, 'moderate')
        self.assertEqual(bumper_part.part_category, 'body')
        self.assertIn('Cracked and dented', bumper_part.damage_description)
        
        hood_part = next((p for p in parts if 'hood' in p.part_name.lower()), None)
        self.assertIsNotNone(hood_part)
        self.assertEqual(hood_part.damage_severity, 'severe')
        self.assertTrue(hood_part.requires_replacement)
        
        # Verify assessment is marked as complete
        self.assessment.refresh_from_db()
        self.assertTrue(self.assessment.parts_identification_complete)
    
    def test_identify_damaged_parts_invalid_assessment(self):
        """Test error handling for invalid assessments."""
        # Test None assessment
        with self.assertRaises(ValueError):
            self.engine.identify_damaged_parts(None)
        
        # Test incomplete assessment
        self.assessment.status = 'pending'
        self.assessment.save()
        
        with self.assertRaises(ValueError):
            self.engine.identify_damaged_parts(self.assessment)
    
    def test_get_assessment_sections(self):
        """Test retrieval of assessment sections."""
        # Create sections
        exterior = ExteriorBodyDamage.objects.create(assessment=self.assessment)
        wheels = WheelsAndTires.objects.create(assessment=self.assessment)
        
        sections = self.engine.get_assessment_sections(self.assessment)
        
        self.assertIn('exterior', sections)
        self.assertIn('wheels', sections)
        self.assertEqual(sections['exterior'], exterior)
        self.assertEqual(sections['wheels'], wheels)
        
        # Test missing sections
        self.assertIsNone(sections['interior'])
        self.assertIsNone(sections['mechanical'])
    
    def test_extract_parts_from_exterior_section(self):
        """Test extraction of parts from exterior damage section."""
        exterior = ExteriorBodyDamage.objects.create(
            assessment=self.assessment,
            front_bumper='moderate',
            front_bumper_notes='Impact damage',
            hood='severe',
            headlight_housings='light',
            side_mirrors='destroyed',
            # No damage items should be ignored
            rear_bumper='none',
            trunk_hatch='none'
        )
        
        parts = self.engine.extract_parts_from_section(exterior, 'exterior')
        
        # Should extract 4 damaged parts, ignore 2 undamaged
        self.assertEqual(len(parts), 4)
        
        # Check specific part data
        bumper_part = next((p for p in parts if 'bumper' in p['part_name'].lower()), None)
        self.assertIsNotNone(bumper_part)
        self.assertEqual(bumper_part['section_type'], 'exterior')
        self.assertEqual(bumper_part['damage_severity'], 'moderate')
        self.assertEqual(bumper_part['part_category'], 'body')
        self.assertIn('Impact damage', bumper_part['damage_description'])
        
        # Check destroyed part requires replacement
        mirror_part = next((p for p in parts if 'mirror' in p['part_name'].lower()), None)
        self.assertIsNotNone(mirror_part)
        self.assertTrue(mirror_part['requires_replacement'])
    
    def test_extract_parts_from_wheels_section(self):
        """Test extraction of parts from wheels and tires section."""
        wheels = WheelsAndTires.objects.create(
            assessment=self.assessment,
            front_left_tire='severe',
            front_left_tire_notes='Sidewall puncture',
            front_left_wheel='moderate',
            rear_right_tire='light',
            spare_tire='none',  # Should be ignored
            tire_pressure_sensors='moderate'
        )
        
        parts = self.engine.extract_parts_from_section(wheels, 'wheels')
        
        # Should extract 4 damaged parts
        self.assertEqual(len(parts), 4)
        
        # Check tire part
        tire_part = next((p for p in parts if 'front left tire' in p['part_name'].lower()), None)
        self.assertIsNotNone(tire_part)
        self.assertEqual(tire_part['part_category'], 'wheels')
        self.assertEqual(tire_part['damage_severity'], 'severe')
        
        # Check sensor part (electrical category)
        sensor_part = next((p for p in parts if 'sensor' in p['part_name'].lower()), None)
        self.assertIsNotNone(sensor_part)
        self.assertEqual(sensor_part['part_category'], 'electrical')
    
    def test_extract_parts_from_interior_section(self):
        """Test extraction of parts from interior damage section."""
        interior = InteriorDamage.objects.create(
            assessment=self.assessment,
            driver_seat='moderate',
            dashboard='severe',
            steering_wheel='light',
            windshield='moderate',
            windshield_notes='Cracked windshield',
            # Undamaged items
            passenger_seat='none',
            floor_mats='none'
        )
        
        parts = self.engine.extract_parts_from_section(interior, 'interior')
        
        # Should extract 4 damaged parts
        self.assertEqual(len(parts), 4)
        
        # Check windshield (glass category)
        windshield_part = next((p for p in parts if 'windshield' in p['part_name'].lower()), None)
        self.assertIsNotNone(windshield_part)
        self.assertEqual(windshield_part['part_category'], 'glass')
        self.assertIn('Cracked windshield', windshield_part['damage_description'])
    
    def test_extract_parts_from_mechanical_section(self):
        """Test extraction of parts from mechanical systems section."""
        mechanical = MechanicalSystems.objects.create(
            assessment=self.assessment,
            engine_block='poor',
            radiator='fair',
            battery='failed',
            shock_absorbers='poor',
            # Good condition items should be ignored
            belts_and_hoses='good',
            springs='excellent'
        )
        
        parts = self.engine.extract_parts_from_section(mechanical, 'mechanical')
        
        # Should extract 4 damaged parts
        self.assertEqual(len(parts), 4)
        
        # Check battery (failed = replace)
        battery_part = next((p for p in parts if 'battery' in p['part_name'].lower()), None)
        self.assertIsNotNone(battery_part)
        self.assertEqual(battery_part['damage_severity'], 'replace')
        self.assertTrue(battery_part['requires_replacement'])
    
    def test_extract_parts_from_electrical_section(self):
        """Test extraction of parts from electrical systems section."""
        electrical = ElectricalSystems.objects.create(
            assessment=self.assessment,
            headlight_function='not_working',
            power_windows='intermittent',
            air_conditioning='not_working',
            # Working items should be ignored
            horn='working',
            heating_system='working'
        )
        
        parts = self.engine.extract_parts_from_section(electrical, 'electrical')
        
        # Should extract 3 damaged parts
        self.assertEqual(len(parts), 3)
        
        # Check intermittent item maps to minor
        windows_part = next((p for p in parts if 'window' in p['part_name'].lower()), None)
        self.assertIsNotNone(windows_part)
        self.assertEqual(windows_part['damage_severity'], 'minor')
    
    def test_map_damage_severity(self):
        """Test mapping of damage values to severity levels."""
        test_cases = [
            ('light', 'minor'),
            ('moderate', 'moderate'),
            ('severe', 'severe'),
            ('destroyed', 'replace'),
            ('fair', 'minor'),
            ('poor', 'moderate'),
            ('failed', 'replace'),
            ('intermittent', 'minor'),
            ('not_working', 'severe'),
            ('none', None),
            ('working', None),
            ('excellent', None),
            ('good', None),
        ]
        
        for damage_value, expected in test_cases:
            result = self.engine.map_damage_severity(damage_value, 'exterior')
            self.assertEqual(result, expected, f"Failed for {damage_value}")
    
    def test_consolidate_duplicate_parts(self):
        """Test consolidation of duplicate parts across sections."""
        parts = [
            {
                'part_name': 'Front Bumper',
                'part_category': 'body',
                'section_type': 'exterior',
                'damage_severity': 'moderate',
                'damage_description': 'Front bumper shows moderate damage',
                'requires_replacement': False,
                'estimated_labor_hours': Decimal('4.0'),
                'notes': 'Impact damage'
            },
            {
                'part_name': 'front bumper',  # Same part, different case
                'part_category': 'body',
                'section_type': 'structural',  # Different section
                'damage_severity': 'severe',  # More severe
                'damage_description': 'Front bumper structural damage',
                'requires_replacement': True,
                'estimated_labor_hours': Decimal('6.0'),
                'notes': 'Structural impact'
            },
            {
                'part_name': 'Side Mirror',
                'part_category': 'electrical',
                'section_type': 'exterior',
                'damage_severity': 'minor',
                'damage_description': 'Side mirror minor damage',
                'requires_replacement': False,
                'estimated_labor_hours': Decimal('1.0'),
                'notes': 'Scratched'
            }
        ]
        
        consolidated = self.engine.consolidate_duplicate_parts(parts)
        
        # Should consolidate to 2 parts (bumpers merged, mirror separate)
        self.assertEqual(len(consolidated), 2)
        
        # Find consolidated bumper part
        bumper_part = next((p for p in consolidated if 'bumper' in p['part_name'].lower()), None)
        self.assertIsNotNone(bumper_part)
        
        # Should use more severe damage level
        self.assertEqual(bumper_part['damage_severity'], 'severe')
        self.assertTrue(bumper_part['requires_replacement'])
        
        # Should use higher labor estimate
        self.assertEqual(bumper_part['estimated_labor_hours'], Decimal('6.0'))
        
        # Should combine descriptions
        self.assertIn('Also:', bumper_part['damage_description'])
        
        # Should track multiple sections
        self.assertIn('sections', bumper_part)
        self.assertEqual(len(bumper_part['sections']), 2)
    
    def test_estimate_labor_hours(self):
        """Test labor hour estimation by category and severity."""
        test_cases = [
            ('body', 'minor', Decimal('2.0')),
            ('body', 'moderate', Decimal('4.0')),
            ('body', 'severe', Decimal('8.0')),
            ('body', 'replace', Decimal('6.0')),
            ('mechanical', 'severe', Decimal('6.0')),
            ('electrical', 'moderate', Decimal('2.0')),
            ('glass', 'replace', Decimal('1.5')),
            ('unknown_category', 'moderate', Decimal('2.0')),  # Default
        ]
        
        for category, severity, expected in test_cases:
            result = self.engine.estimate_labor_hours(category, severity)
            self.assertEqual(result, expected, f"Failed for {category}/{severity}")
    
    def test_generate_damage_description(self):
        """Test generation of damage descriptions."""
        description = self.engine.generate_damage_description(
            'Front Bumper', 'moderate', 'moderate', 'Impact damage from collision'
        )
        
        self.assertIn('Front Bumper', description)
        self.assertIn('moderate damage', description)
        self.assertIn('Impact damage from collision', description)
        
        # Test with different original value
        description2 = self.engine.generate_damage_description(
            'Hood', 'severe', 'destroyed', ''
        )
        
        self.assertIn('Hood', description2)
        self.assertIn('severe damage', description2)
        self.assertIn('(assessed as destroyed)', description2)
    
    def test_create_damaged_part_record(self):
        """Test creation of DamagedPart records."""
        part_data = {
            'section_type': 'exterior',
            'part_name': 'Front Bumper',
            'part_category': 'body',
            'damage_severity': 'moderate',
            'damage_description': 'Front bumper shows moderate damage',
            'requires_replacement': False,
            'estimated_labor_hours': Decimal('4.0'),
            'notes': 'Impact damage'
        }
        
        damaged_part = self.engine.create_damaged_part_record(self.assessment, part_data)
        
        self.assertIsNotNone(damaged_part)
        self.assertEqual(damaged_part.assessment, self.assessment)
        self.assertEqual(damaged_part.part_name, 'Front Bumper')
        self.assertEqual(damaged_part.part_category, 'body')
        self.assertEqual(damaged_part.damage_severity, 'moderate')
        self.assertEqual(damaged_part.estimated_labor_hours, Decimal('4.0'))
        
        # Verify it was saved to database
        self.assertTrue(DamagedPart.objects.filter(id=damaged_part.id).exists())
    
    @patch('insurance_app.parts_identification.AssessmentPhoto')
    def test_link_damage_images(self, mock_photo_model):
        """Test linking of damage images to parts."""
        # Create a damaged part
        damaged_part = DamagedPart.objects.create(
            assessment=self.assessment,
            section_type='exterior',
            part_name='Front Bumper',
            part_category='body',
            damage_severity='moderate',
            damage_description='Test damage'
        )
        
        # Mock photos
        mock_photo1 = Mock()
        mock_photo1.description = 'Front bumper damage photo'
        mock_photo1.image = 'front_bumper_001.jpg'
        
        mock_photo2 = Mock()
        mock_photo2.description = 'Side view of vehicle'
        mock_photo2.image = 'side_view.jpg'
        
        mock_photo_model.objects.filter.return_value = [mock_photo1, mock_photo2]
        
        part_data = {'section_type': 'exterior'}
        
        # Test image linking
        self.engine.link_damage_images(damaged_part, part_data)
        
        # Verify filter was called correctly
        mock_photo_model.objects.filter.assert_called_once_with(
            assessment=self.assessment
        )
    
    def test_get_part_keywords(self):
        """Test generation of keywords for photo matching."""
        keywords = self.engine.get_part_keywords('Front Bumper')
        
        self.assertIn('front', keywords)
        self.assertIn('bumper', keywords)
        
        # Test with complex part name
        keywords2 = self.engine.get_part_keywords('Side Mirror/Housing')
        
        self.assertIn('side', keywords2)
        self.assertIn('mirror', keywords2)
        self.assertIn('housing', keywords2)
        
        # Test keyword variations
        keywords3 = self.engine.get_part_keywords('Headlight')
        
        self.assertIn('headlight', keywords3)
        self.assertIn('light', keywords3)
        self.assertIn('lamp', keywords3)
    
    def test_get_severity_weight(self):
        """Test severity weight calculation for comparison."""
        weights = [
            ('minor', 1),
            ('moderate', 2),
            ('severe', 3),
            ('replace', 4),
            ('unknown', 0),
        ]
        
        for severity, expected in weights:
            result = self.engine.get_severity_weight(severity)
            self.assertEqual(result, expected)
    
    def test_comprehensive_workflow(self):
        """Test complete workflow with multiple sections and complex damage."""
        # Create comprehensive damage across multiple sections
        exterior = ExteriorBodyDamage.objects.create(
            assessment=self.assessment,
            front_bumper='severe',
            front_bumper_notes='Major impact damage',
            hood='moderate',
            headlight_housings='destroyed',
            side_mirrors='light',
            rear_bumper='moderate'
        )
        
        wheels = WheelsAndTires.objects.create(
            assessment=self.assessment,
            front_left_tire='severe',
            front_left_wheel='moderate',
            rear_right_tire='light'
        )
        
        interior = InteriorDamage.objects.create(
            assessment=self.assessment,
            dashboard='moderate',
            windshield='severe',
            driver_seat='light'
        )
        
        mechanical = MechanicalSystems.objects.create(
            assessment=self.assessment,
            radiator='poor',
            battery='failed'
        )
        
        # Run complete identification
        parts = self.engine.identify_damaged_parts(self.assessment)
        
        # Verify comprehensive results
        self.assertGreaterEqual(len(parts), 10)  # Should identify multiple parts
        
        # Check variety of categories
        categories = {part.part_category for part in parts}
        self.assertIn('body', categories)
        self.assertIn('wheels', categories)
        self.assertIn('glass', categories)
        self.assertIn('electrical', categories)
        
        # Check variety of severities
        severities = {part.damage_severity for part in parts}
        self.assertIn('minor', severities)
        self.assertIn('moderate', severities)
        self.assertIn('severe', severities)
        
        # Verify some parts require replacement
        replacement_parts = [p for p in parts if p.requires_replacement]
        self.assertGreater(len(replacement_parts), 0)
        
        # Verify labor hours are estimated
        for part in parts:
            self.assertGreater(part.estimated_labor_hours, 0)
        
        # Verify assessment is marked complete
        self.assessment.refresh_from_db()
        self.assertTrue(self.assessment.parts_identification_complete)
    
    def test_no_damage_scenario(self):
        """Test scenario where no damage is found."""
        # Create sections with no damage
        exterior = ExteriorBodyDamage.objects.create(
            assessment=self.assessment,
            front_bumper='none',
            hood='none',
            rear_bumper='none'
        )
        
        wheels = WheelsAndTires.objects.create(
            assessment=self.assessment,
            front_left_tire='none',
            front_right_tire='none'
        )
        
        # Run identification
        parts = self.engine.identify_damaged_parts(self.assessment)
        
        # Should return empty list
        self.assertEqual(len(parts), 0)
        
        # Assessment should still be marked complete
        self.assessment.refresh_from_db()
        self.assertTrue(self.assessment.parts_identification_complete)
    
    def test_missing_sections_handling(self):
        """Test handling of assessments with missing sections."""
        # Only create exterior damage, leave other sections missing
        exterior = ExteriorBodyDamage.objects.create(
            assessment=self.assessment,
            front_bumper='moderate',
            hood='severe'
        )
        
        # Run identification (should not fail on missing sections)
        parts = self.engine.identify_damaged_parts(self.assessment)
        
        # Should still identify parts from existing sections
        self.assertEqual(len(parts), 2)
        
        # All parts should be from exterior section
        for part in parts:
            self.assertEqual(part.section_type, 'exterior')