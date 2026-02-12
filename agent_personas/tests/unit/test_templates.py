"""
Unit tests for persona templates and archetypes.
"""

import unittest
from datetime import datetime

from ...templates.archetype import Archetype, ArchetypeManager, ArchetypeCategory
from ...templates.template import PersonaTemplate, TemplateManager
from ...templates.builder import PersonaBuilder, BuilderStep
from ...templates.presets import PRESET_ARCHETYPES, PRESET_TEMPLATES
from ...core.persona import Persona


class TestArchetype(unittest.TestCase):
    """Test cases for Archetype class."""
    
    def setUp(self):
        self.archetype = Archetype(
            name="test_archetype",
            description="Test archetype",
            category=ArchetypeCategory.ANALYTICAL,
            core_traits={"analytical": 0.9, "logical": 0.8},
            emotional_tendencies={"calm": 0.7}
        )
    
    def test_archetype_creation(self):
        """Test basic archetype creation."""
        self.assertEqual(self.archetype.name, "test_archetype")
        self.assertEqual(self.archetype.category, ArchetypeCategory.ANALYTICAL)
        self.assertIn("analytical", self.archetype.core_traits)
    
    def test_trait_validation(self):
        """Test trait value validation."""
        with self.assertRaises(ValueError):
            Archetype(
                name="invalid",
                description="Invalid archetype",
                category=ArchetypeCategory.ANALYTICAL,
                core_traits={"invalid_trait": 2.0}  # Invalid value > 1.0
            )
    
    def test_archetype_blending(self):
        """Test archetype blending functionality."""
        archetype2 = Archetype(
            name="creative_archetype", 
            description="Creative archetype",
            category=ArchetypeCategory.CREATIVE,
            core_traits={"creative": 0.9, "imaginative": 0.8},
            emotional_tendencies={"inspired": 0.8}
        )
        
        blend = self.archetype.blend_with(archetype2, ratio=0.5)
        
        self.assertIn("traits", blend)
        self.assertIn("emotional_tendencies", blend)
        self.assertEqual(len(blend["source_archetypes"]), 2)
    
    def test_compatibility_checking(self):
        """Test archetype compatibility."""
        # Create compatible archetype
        compatible = Archetype(
            name="expert",
            description="Expert archetype",
            category=ArchetypeCategory.TECHNICAL,
            core_traits={"knowledgeable": 0.9},
            compatible_archetypes={"test_archetype"}
        )
        
        # Create conflicting archetype
        conflicting = Archetype(
            name="impulsive",
            description="Impulsive archetype", 
            category=ArchetypeCategory.EMOTIONAL,
            core_traits={"impulsive": 0.9},
            conflicting_archetypes={"test_archetype"}
        )
        
        self.assertTrue(self.archetype.is_compatible_with(compatible))
        self.assertTrue(self.archetype.conflicts_with(conflicting))


class TestArchetypeManager(unittest.TestCase):
    """Test cases for ArchetypeManager."""
    
    def setUp(self):
        self.manager = ArchetypeManager()
        self.test_archetype = Archetype(
            name="test",
            description="Test archetype",
            category=ArchetypeCategory.ANALYTICAL,
            core_traits={"analytical": 0.8}
        )
    
    def test_register_archetype(self):
        """Test archetype registration."""
        self.manager.register_archetype(self.test_archetype)
        
        retrieved = self.manager.get_archetype("test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "test")
    
    def test_list_archetypes(self):
        """Test archetype listing."""
        self.manager.register_archetype(self.test_archetype)
        
        all_archetypes = self.manager.list_archetypes()
        self.assertGreater(len(all_archetypes), 0)
        
        analytical_archetypes = self.manager.list_archetypes(ArchetypeCategory.ANALYTICAL)
        self.assertTrue(any(a.name == "test" for a in analytical_archetypes))
    
    def test_create_blend(self):
        """Test archetype blending through manager."""
        archetype2 = Archetype(
            name="creative",
            description="Creative archetype",
            category=ArchetypeCategory.CREATIVE,
            core_traits={"creative": 0.9}
        )
        
        self.manager.register_archetype(self.test_archetype)
        self.manager.register_archetype(archetype2)
        
        blend = self.manager.create_blend("test", "creative", 0.3)
        
        self.assertIn("traits", blend)
        self.assertIn("source_archetypes", blend)


class TestPersonaTemplate(unittest.TestCase):
    """Test cases for PersonaTemplate."""
    
    def setUp(self):
        self.template = PersonaTemplate(
            name="test_template",
            description="Test template",
            category="test",
            base_traits={"helpful": 0.8, "professional": 0.7},
            trait_ranges={
                "helpful": (0.6, 1.0),
                "professional": (0.5, 0.9)
            },
            required_fields=["purpose"]
        )
    
    def test_template_creation(self):
        """Test basic template creation."""
        self.assertEqual(self.template.name, "test_template")
        self.assertIn("helpful", self.template.base_traits)
        self.assertIsInstance(self.template.created_at, datetime)
    
    def test_persona_creation_from_template(self):
        """Test creating persona from template."""
        persona = self.template.create_persona(
            "test_persona",
            purpose="testing",
            description="Test persona from template"
        )
        
        self.assertIsInstance(persona, Persona)
        self.assertEqual(persona.name, "test_persona")
        self.assertIn("template_name", persona.metadata)
    
    def test_trait_range_validation(self):
        """Test trait range validation."""
        customizations = {
            "traits": {"helpful": 1.5}  # Outside range
        }
        
        errors = self.template.validate_customization(customizations)
        self.assertGreater(len(errors), 0)
    
    def test_required_fields_validation(self):
        """Test required fields validation."""
        customizations = {}  # Missing required 'purpose' field
        
        errors = self.template.validate_customization(customizations)
        self.assertTrue(any("purpose" in error for error in errors))


class TestTemplateManager(unittest.TestCase):
    """Test cases for TemplateManager."""
    
    def setUp(self):
        self.manager = TemplateManager()
        self.test_template = PersonaTemplate(
            name="test_template",
            description="Test template",
            category="test",
            base_traits={"helpful": 0.8},
            tags=["test", "sample"]
        )
    
    def test_register_template(self):
        """Test template registration."""
        self.manager.register_template(self.test_template)
        
        retrieved = self.manager.get_template("test_template")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "test_template")
    
    def test_search_templates(self):
        """Test template searching."""
        self.manager.register_template(self.test_template)
        
        # Search by name
        results = self.manager.search_templates("test")
        self.assertGreater(len(results), 0)
        
        # Search by tag
        results = self.manager.search_templates("sample")
        self.assertGreater(len(results), 0)
    
    def test_create_persona_from_template(self):
        """Test persona creation through manager."""
        self.manager.register_template(self.test_template)
        
        persona = self.manager.create_persona_from_template(
            "test_template",
            "new_persona",
            description="Created through manager"
        )
        
        self.assertIsInstance(persona, Persona)
        self.assertEqual(persona.name, "new_persona")


class TestPersonaBuilder(unittest.TestCase):
    """Test cases for PersonaBuilder."""
    
    def setUp(self):
        self.builder = PersonaBuilder()
    
    def test_builder_initialization(self):
        """Test builder initialization."""
        self.assertEqual(self.builder.get_current_step(), BuilderStep.BASIC_INFO)
    
    def test_basic_info_step(self):
        """Test basic info processing."""
        input_data = {
            "name": "test_persona",
            "description": "Test persona created with builder"
        }
        
        result = self.builder.process_input(input_data)
        self.assertTrue(result.get("success", False))
    
    def test_builder_validation(self):
        """Test builder input validation."""
        # Test invalid input
        invalid_input = {
            "name": "",  # Empty name
            "description": "Test"
        }
        
        result = self.builder.process_input(invalid_input)
        self.assertFalse(result.get("success", False))
        self.assertIn("errors", result)
    
    def test_full_builder_workflow(self):
        """Test complete builder workflow."""
        # Step 1: Basic info
        step1_result = self.builder.process_input({
            "name": "built_persona",
            "description": "Built through full workflow"
        })
        self.assertTrue(step1_result.get("success"))
        
        # Step 2: Skip archetype selection
        step2_result = self.builder.process_input({"archetypes": []})
        self.assertTrue(step2_result.get("success"))
        
        # Step 3: Set traits
        step3_result = self.builder.process_input({
            "traits": {"helpful": 0.8, "analytical": 0.6}
        })
        self.assertTrue(step3_result.get("success"))
        
        # Continue through remaining steps with minimal data
        steps_data = [
            {"conversation_style": "professional"},
            {"emotional_baseline": "calm"},
            {},  # Advanced options
            {}   # Validation
        ]
        
        for data in steps_data:
            result = self.builder.process_input(data)
            if not result.get("success"):
                break
        
        # Check if we can create the persona
        if self.builder.get_current_step() == BuilderStep.COMPLETE:
            persona = self.builder.create_persona()
            self.assertIsInstance(persona, Persona)
            self.assertEqual(persona.name, "built_persona")


class TestPresetArchetypesAndTemplates(unittest.TestCase):
    """Test cases for preset archetypes and templates."""
    
    def test_preset_archetypes_validity(self):
        """Test that all preset archetypes are valid."""
        for archetype_name, archetype in PRESET_ARCHETYPES.items():
            with self.subTest(archetype_name=archetype_name):
                self.assertIsInstance(archetype, Archetype)
                self.assertEqual(archetype.name, archetype_name)
                
                # Validate traits are in valid range
                for trait, value in archetype.core_traits.items():
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLessEqual(value, 1.0)
    
    def test_preset_templates_validity(self):
        """Test that all preset templates are valid."""
        for template_name, template in PRESET_TEMPLATES.items():
            with self.subTest(template_name=template_name):
                self.assertIsInstance(template, PersonaTemplate)
                self.assertEqual(template.name, template_name)
                
                # Test template can create personas
                persona = template.create_persona(
                    f"test_{template_name}",
                    description="Test persona from preset template"
                )
                self.assertIsInstance(persona, Persona)
    
    def test_archetype_compatibility_matrix(self):
        """Test that archetype compatibility is properly defined."""
        for archetype_name, archetype in PRESET_ARCHETYPES.items():
            # Check that compatible archetypes exist
            for compatible_name in archetype.compatible_archetypes:
                self.assertIn(compatible_name, PRESET_ARCHETYPES,
                             f"Compatible archetype {compatible_name} not found for {archetype_name}")
            
            # Check that conflicting archetypes exist
            for conflicting_name in archetype.conflicting_archetypes:
                self.assertIn(conflicting_name, PRESET_ARCHETYPES,
                             f"Conflicting archetype {conflicting_name} not found for {archetype_name}")


if __name__ == "__main__":
    unittest.main()