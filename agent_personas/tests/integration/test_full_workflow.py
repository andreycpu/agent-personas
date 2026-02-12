"""
Integration tests for full persona workflow scenarios.
"""

import unittest
from unittest.mock import Mock

from ...core.persona import Persona
from ...templates.archetype import ArchetypeManager
from ...templates.template import TemplateManager
from ...templates.builder import PersonaBuilder, BuilderStep
from ...composition.blender import PersonaBlender, BlendConfig
from ...evaluation.persona_evaluator import PersonaEvaluator
from ...versioning.version_manager import VersionManager, VersionType
from ...multilingual.multilingual_persona import MultilingualPersona
from .. import create_test_persona


class TestFullPersonaWorkflow(unittest.TestCase):
    """Test complete persona workflow integration."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.archetype_manager = ArchetypeManager()
        self.template_manager = TemplateManager()
        self.persona_blender = PersonaBlender()
        self.evaluator = PersonaEvaluator()
        self.version_manager = VersionManager()
    
    def test_complete_persona_lifecycle(self):
        """Test complete persona lifecycle from creation to evaluation."""
        
        # 1. Create initial persona using builder
        builder = PersonaBuilder(self.archetype_manager, self.template_manager)
        
        # Build persona step by step
        steps_data = [
            {"name": "assistant_persona", "description": "A helpful assistant persona"},
            {"archetypes": []},  # Skip archetype selection
            {"traits": {"helpful": 0.9, "analytical": 0.7, "patient": 0.8}},
            {"conversation_style": "professional"},
            {"emotional_baseline": "calm"},
            {"metadata": {"purpose": "customer_support"}},
            {}  # Validation
        ]
        
        for step_data in steps_data:
            result = builder.process_input(step_data)
            if not result.get("success"):
                self.fail(f"Builder step failed: {result}")
        
        # Create persona
        if builder.get_current_step() == BuilderStep.COMPLETE:
            persona = builder.create_persona()
        else:
            self.fail("Builder did not complete successfully")
        
        self.assertIsInstance(persona, Persona)
        
        # 2. Version the persona
        initial_version = self.version_manager.create_initial_version(
            persona,
            "1.0.0",
            "Initial assistant persona"
        )
        
        self.assertIsNotNone(initial_version)
        
        # 3. Evaluate the persona
        evaluation = self.evaluator.evaluate_persona(persona)
        
        self.assertIsNotNone(evaluation)
        self.assertGreaterEqual(evaluation.overall_score, 0.0)
        self.assertLessEqual(evaluation.overall_score, 1.0)
        
        # 4. Create multilingual version
        multilingual_persona = MultilingualPersona(persona, "en")
        multilingual_persona.add_language_profile("es", 0.8)
        multilingual_persona.add_language_profile("fr", 0.7)
        
        self.assertEqual(len(multilingual_persona.language_profiles), 3)  # en, es, fr
        
        # 5. Modify persona and create new version
        persona.set_trait("empathetic", 0.9)
        persona.description = "Updated helpful assistant with empathy"
        
        new_version = self.version_manager.create_new_version(
            persona.name,
            persona,
            VersionType.MINOR,
            "Added empathy trait"
        )
        
        self.assertEqual(new_version.version_type, VersionType.MINOR)
        self.assertGreater(len(new_version.changes), 0)
        
        # 6. Re-evaluate after changes
        new_evaluation = self.evaluator.evaluate_persona(persona)
        
        # Store evaluation in history for comparison
        self.assertIsNotNone(new_evaluation)
        
        # 7. Compare versions
        comparison = self.version_manager.compare_versions(
            persona.name,
            initial_version.version_number,
            new_version.version_number
        )
        
        self.assertIn("trait_differences", comparison)
        self.assertGreater(comparison["summary"]["traits_modified"], 0)
    
    def test_persona_blending_workflow(self):
        """Test workflow involving persona blending and evaluation."""
        
        # Create source personas
        analytical_persona = create_test_persona(
            "analytical_expert",
            traits={"analytical": 0.95, "methodical": 0.9, "logical": 0.85},
            description="Highly analytical expert"
        )
        
        creative_persona = create_test_persona(
            "creative_innovator", 
            traits={"creative": 0.95, "imaginative": 0.9, "original": 0.8},
            description="Creative innovator"
        )
        
        supportive_persona = create_test_persona(
            "supportive_mentor",
            traits={"empathetic": 0.9, "patient": 0.95, "supportive": 0.9},
            description="Supportive mentor"
        )
        
        # Version all source personas
        for persona in [analytical_persona, creative_persona, supportive_persona]:
            self.version_manager.create_initial_version(persona, "1.0.0")
        
        # Evaluate source personas
        source_evaluations = {}
        for persona in [analytical_persona, creative_persona, supportive_persona]:
            evaluation = self.evaluator.evaluate_persona(persona)
            source_evaluations[persona.name] = evaluation
        
        # Test blending compatibility
        compatibility = self.persona_blender.analyze_blend_compatibility(
            [analytical_persona, creative_persona]
        )
        
        self.assertIn("compatibility_score", compatibility)
        
        # Blend personas with custom configuration
        blend_config = BlendConfig(
            weights={"persona_0": 0.4, "persona_1": 0.4, "persona_2": 0.2},
            preserve_dominant_traits=True
        )
        
        blended_persona = self.persona_blender.blend_personas(
            [analytical_persona, creative_persona, supportive_persona],
            "balanced_assistant",
            blend_config
        )
        
        self.assertIsInstance(blended_persona, Persona)
        
        # Version the blended persona
        blended_version = self.version_manager.create_initial_version(
            blended_persona,
            "1.0.0",
            "Initial blended persona from 3 sources"
        )
        
        # Evaluate blended persona
        blended_evaluation = self.evaluator.evaluate_persona(blended_persona)
        
        # Check that blended persona has reasonable performance
        self.assertGreater(blended_evaluation.overall_score, 0.5)
        
        # Compare blended persona with sources
        persona_list = [analytical_persona, creative_persona, supportive_persona, blended_persona]
        comparison_results = self.evaluator.compare_personas(persona_list)
        
        self.assertEqual(comparison_results["persona_count"], 4)
        self.assertIn("overall_rankings", comparison_results)
    
    def test_multilingual_persona_workflow(self):
        """Test workflow with multilingual persona features."""
        
        # Create base persona
        base_persona = create_test_persona(
            "global_assistant",
            traits={"helpful": 0.9, "cultural_awareness": 0.8, "patient": 0.9},
            description="Globally-aware assistant"
        )
        
        # Create multilingual version
        multilingual_persona = MultilingualPersona(base_persona, "en")
        
        # Add multiple languages with cultural adaptations
        languages = [
            ("es", 0.9),  # Spanish - high proficiency
            ("fr", 0.8),  # French - good proficiency  
            ("ja", 0.6),  # Japanese - moderate proficiency
            ("de", 0.7)   # German - good proficiency
        ]
        
        for lang_code, proficiency in languages:
            multilingual_persona.add_language_profile(lang_code, proficiency)
        
        # Test language switching and persona adaptation
        language_evaluations = {}
        
        for lang_code, _ in languages:
            # Switch to language
            success = multilingual_persona.switch_language(lang_code)
            self.assertTrue(success)
            
            # Get adapted persona
            adapted_persona = multilingual_persona.get_active_persona()
            
            # Evaluate adapted persona
            evaluation = self.evaluator.evaluate_persona(adapted_persona)
            language_evaluations[lang_code] = evaluation
            
            # Version the adapted persona
            version_description = f"Adapted for {lang_code} language/culture"
            version = self.version_manager.create_initial_version(
                adapted_persona,
                "1.0.0",
                version_description
            )
            
            self.assertIsNotNone(version)
        
        # Analyze cultural adaptation effectiveness
        adaptation_scores = {}
        for lang_code, _ in languages:
            score = multilingual_persona.get_cultural_adaptation_score(lang_code)
            adaptation_scores[lang_code] = score
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        
        # Check that high-context cultures have appropriate adaptations
        if "ja" in adaptation_scores:
            # Japanese should have good cultural adaptation
            self.assertGreater(adaptation_scores["ja"], 0.6)
        
        # Get multilingual statistics
        ml_stats = multilingual_persona.get_language_statistics()
        self.assertEqual(ml_stats["total_languages"], len(languages) + 1)  # +1 for primary
    
    def test_template_to_evaluation_workflow(self):
        """Test workflow from template creation to persona evaluation."""
        
        # Create custom template
        from ...templates.template import PersonaTemplate
        
        custom_template = PersonaTemplate(
            name="customer_service_pro",
            description="Professional customer service representative",
            category="business",
            base_traits={
                "helpful": 0.95,
                "patient": 0.9,
                "professional": 0.8,
                "empathetic": 0.85
            },
            trait_ranges={
                "helpful": (0.8, 1.0),
                "patient": (0.7, 1.0),
                "professional": (0.6, 0.9),
                "empathetic": (0.6, 0.9)
            },
            required_fields=["department", "experience_level"]
        )
        
        # Register template
        self.template_manager.register_template(custom_template)
        
        # Create persona from template
        persona = custom_template.create_persona(
            "sarah_support",
            department="technical_support",
            experience_level="senior",
            description="Senior technical support specialist"
        )
        
        self.assertIsInstance(persona, Persona)
        self.assertIn("template_name", persona.metadata)
        
        # Version the persona
        version = self.version_manager.create_initial_version(
            persona,
            "1.0.0", 
            "Initial version from custom template"
        )
        
        # Evaluate persona
        evaluation = self.evaluator.evaluate_persona(persona)
        
        # Template-based personas should score well on completeness
        completeness_score = evaluation.dimension_scores.get("completeness")
        if completeness_score:
            self.assertGreater(completeness_score.score, 0.7)
        
        # Create variations using the template
        variations = []
        
        for i in range(3):
            variation = custom_template.create_persona(
                f"support_agent_{i}",
                department="general_support",
                experience_level="junior",
                traits={"patient": 0.8 + (i * 0.05)}  # Vary patience
            )
            variations.append(variation)
        
        # Evaluate all variations
        variation_evaluations = []
        for variation in variations:
            eval_result = self.evaluator.evaluate_persona(variation)
            variation_evaluations.append(eval_result)
        
        # Compare variations
        all_personas = [persona] + variations
        comparison = self.evaluator.compare_personas(all_personas)
        
        self.assertEqual(comparison["persona_count"], 4)
        
        # All should be reasonably good (template-based)
        for evaluation in variation_evaluations:
            self.assertGreater(evaluation.overall_score, 0.6)
    
    def test_error_handling_workflow(self):
        """Test workflow error handling and recovery."""
        
        # Test invalid persona creation
        with self.assertRaises(Exception):
            invalid_persona = Persona(
                name="",  # Empty name should fail validation
                description="Invalid persona",
                traits={"invalid_trait": 2.0}  # Invalid trait value
            )
            invalid_persona.validate()
        
        # Test version manager with non-existent persona
        non_existent_version = self.version_manager.get_version("non_existent_persona")
        self.assertIsNone(non_existent_version)
        
        # Test evaluation with minimal persona
        minimal_persona = Persona(
            name="minimal",
            description="Minimal persona for testing",
            traits={}  # No traits
        )
        
        # Should still be evaluable, but with lower scores
        evaluation = self.evaluator.evaluate_persona(minimal_persona)
        self.assertIsNotNone(evaluation)
        self.assertLess(evaluation.overall_score, 0.5)  # Should score lower
        
        # Test multilingual with invalid language
        base_persona = create_test_persona("test_multilingual")
        multilingual = MultilingualPersona(base_persona)
        
        # Switch to non-existent language should fail gracefully
        success = multilingual.switch_language("invalid_lang")
        self.assertFalse(success)
        
        # Should still have original language active
        self.assertEqual(multilingual.active_language, multilingual.primary_language)


if __name__ == "__main__":
    unittest.main()