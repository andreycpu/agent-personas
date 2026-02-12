"""
Unit tests for persona composition and blending systems.
"""

import unittest
from unittest.mock import Mock, patch

from ...composition.blender import PersonaBlender, BlendStrategy, BlendConfig
from ...composition.compositor import PersonaCompositor, CompositionRule, CompositionOperation, RulePriority
from ...core.persona import Persona
from .. import create_test_persona


class TestPersonaBlender(unittest.TestCase):
    """Test cases for PersonaBlender class."""
    
    def setUp(self):
        self.blender = PersonaBlender()
        
        # Create test personas
        self.persona1 = create_test_persona(
            "analytical_persona",
            traits={"analytical": 0.9, "methodical": 0.8, "patient": 0.7}
        )
        
        self.persona2 = create_test_persona(
            "creative_persona", 
            traits={"creative": 0.9, "imaginative": 0.8, "spontaneous": 0.6}
        )
        
        self.persona3 = create_test_persona(
            "social_persona",
            traits={"friendly": 0.9, "empathetic": 0.8, "outgoing": 0.7}
        )
    
    def test_basic_blending(self):
        """Test basic persona blending."""
        blended = self.blender.blend_personas(
            [self.persona1, self.persona2],
            "blended_persona"
        )
        
        self.assertIsInstance(blended, Persona)
        self.assertEqual(blended.name, "blended_persona")
        self.assertIn("blend_source_personas", blended.metadata)
        self.assertEqual(len(blended.metadata["blend_source_personas"]), 2)
    
    def test_blend_strategies(self):
        """Test different blending strategies."""
        strategies = [
            BlendStrategy.AVERAGE,
            BlendStrategy.WEIGHTED_AVERAGE,
            BlendStrategy.DOMINANT,
            BlendStrategy.HARMONIC_MEAN,
            BlendStrategy.GEOMETRIC_MEAN
        ]
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                config = BlendConfig(strategy=strategy)
                
                blended = self.blender.blend_personas(
                    [self.persona1, self.persona2],
                    f"blended_{strategy.value}",
                    config
                )
                
                self.assertIsInstance(blended, Persona)
                self.assertEqual(blended.metadata["blend_strategy"], strategy.value)
    
    def test_weighted_blending(self):
        """Test weighted blending with custom weights."""
        config = BlendConfig(
            strategy=BlendStrategy.WEIGHTED_AVERAGE,
            weights={"persona_0": 0.7, "persona_1": 0.3}
        )
        
        blended = self.blender.blend_personas(
            [self.persona1, self.persona2],
            "weighted_blend",
            config
        )
        
        # Check that analytical traits are stronger (higher weight)
        self.assertGreater(
            blended.get_trait("analytical"),
            blended.get_trait("creative")
        )
    
    def test_trait_priorities(self):
        """Test trait priority adjustments."""
        config = BlendConfig(
            trait_priorities={
                "analytical": 1.5,  # Boost analytical
                "creative": 0.5     # Reduce creative
            }
        )
        
        blended = self.blender.blend_personas(
            [self.persona1, self.persona2],
            "priority_blend",
            config
        )
        
        # Check that priorities were applied
        self.assertGreater(blended.get_trait("analytical"), 0.8)
        self.assertLess(blended.get_trait("creative"), 0.5)
    
    def test_blend_compatibility_analysis(self):
        """Test blend compatibility analysis."""
        # Test with compatible personas
        compatible_analysis = self.blender.analyze_blend_compatibility([self.persona1, self.persona2])
        
        self.assertIn("compatibility_score", compatible_analysis)
        self.assertIn("trait_overlap", compatible_analysis)
        self.assertIn("potential_conflicts", compatible_analysis)
        self.assertIn("recommended_strategies", compatible_analysis)
        
        # Compatibility score should be between 0 and 1
        score = compatible_analysis["compatibility_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_multiple_persona_blending(self):
        """Test blending more than two personas."""
        blended = self.blender.blend_personas(
            [self.persona1, self.persona2, self.persona3],
            "triple_blend"
        )
        
        self.assertIsInstance(blended, Persona)
        self.assertEqual(len(blended.metadata["blend_source_personas"]), 3)
        
        # Should have traits from all three personas
        self.assertGreater(blended.get_trait("analytical"), 0)
        self.assertGreater(blended.get_trait("creative"), 0)
        self.assertGreater(blended.get_trait("friendly"), 0)
    
    def test_blend_error_handling(self):
        """Test error handling in blending."""
        # Test with insufficient personas
        with self.assertRaises(ValueError):
            self.blender.blend_personas([self.persona1], "invalid_blend")
        
        # Test with invalid types
        with self.assertRaises(TypeError):
            self.blender.blend_personas([self.persona1, "not_a_persona"], "invalid_blend")


class TestPersonaCompositor(unittest.TestCase):
    """Test cases for PersonaCompositor class."""
    
    def setUp(self):
        self.compositor = PersonaCompositor()
        
        self.base_persona = create_test_persona(
            "base_persona",
            traits={"helpful": 0.6, "analytical": 0.5, "creative": 0.4}
        )
        
        self.source_persona1 = create_test_persona(
            "source1",
            traits={"analytical": 0.9, "methodical": 0.8}
        )
        
        self.source_persona2 = create_test_persona(
            "source2", 
            traits={"creative": 0.9, "imaginative": 0.8}
        )
    
    def test_layer_rule(self):
        """Test layer composition rule."""
        layer_rule = CompositionRule(
            name="layer_analytical",
            operation=CompositionOperation.LAYER,
            target_traits=["analytical", "methodical"],
            parameters={"layer_strength": 0.7}
        )
        
        self.compositor.add_rule(layer_rule)
        
        composed = self.compositor.compose_persona(
            self.base_persona,
            [self.source_persona1],
            "composed_layered"
        )
        
        # Analytical trait should be increased
        self.assertGreater(
            composed.get_trait("analytical"),
            self.base_persona.get_trait("analytical")
        )
        
        # Should have methodical trait from source
        self.assertGreater(composed.get_trait("methodical"), 0)
    
    def test_merge_rule(self):
        """Test merge composition rule."""
        merge_rule = CompositionRule(
            name="merge_traits",
            operation=CompositionOperation.MERGE,
            target_traits=["helpful", "analytical"],
            parameters={"merge_strategy": "average"}
        )
        
        self.compositor.add_rule(merge_rule)
        
        composed = self.compositor.compose_persona(
            self.base_persona,
            [self.source_persona1],
            "composed_merged"
        )
        
        self.assertIn("applied_composition_rules", composed.metadata)
        self.assertIn("merge_traits", composed.metadata["applied_composition_rules"])
    
    def test_replace_rule(self):
        """Test replace composition rule."""
        replace_rule = CompositionRule(
            name="replace_creative",
            operation=CompositionOperation.REPLACE,
            target_traits=["creative"],
            parameters={"replacement_factor": 1.0}
        )
        
        self.compositor.add_rule(replace_rule)
        
        composed = self.compositor.compose_persona(
            self.base_persona,
            [self.source_persona2],
            "composed_replaced"
        )
        
        # Creative trait should be replaced with source value
        self.assertAlmostEqual(
            composed.get_trait("creative"),
            self.source_persona2.get_trait("creative"),
            places=2
        )
    
    def test_enhance_rule(self):
        """Test enhance composition rule."""
        enhance_rule = CompositionRule(
            name="enhance_helpful",
            operation=CompositionOperation.ENHANCE,
            target_traits=["helpful"],
            parameters={"enhancement_factor": 1.3}
        )
        
        self.compositor.add_rule(enhance_rule)
        
        composed = self.compositor.compose_persona(
            self.base_persona,
            [],
            "composed_enhanced"
        )
        
        # Helpful trait should be enhanced
        enhanced_value = self.base_persona.get_trait("helpful") * 1.3
        self.assertAlmostEqual(
            composed.get_trait("helpful"),
            min(1.0, enhanced_value),
            places=2
        )
    
    def test_suppress_rule(self):
        """Test suppress composition rule."""
        suppress_rule = CompositionRule(
            name="suppress_analytical",
            operation=CompositionOperation.SUPPRESS,
            target_traits=["analytical"],
            parameters={"suppression_factor": 0.5}
        )
        
        self.compositor.add_rule(suppress_rule)
        
        composed = self.compositor.compose_persona(
            self.base_persona,
            [],
            "composed_suppressed"
        )
        
        # Analytical trait should be reduced
        suppressed_value = self.base_persona.get_trait("analytical") * 0.5
        self.assertAlmostEqual(
            composed.get_trait("analytical"),
            suppressed_value,
            places=2
        )
    
    def test_conditional_rule(self):
        """Test conditional composition rule."""
        # Create condition function
        def high_analytical_condition(persona):
            return persona.get_trait("analytical") > 0.8
        
        conditional_rule = CompositionRule(
            name="conditional_enhancement",
            operation=CompositionOperation.CONDITIONAL,
            condition=high_analytical_condition,
            parameters={
                "nested_operation": CompositionOperation.ENHANCE,
                "nested_params": {"enhancement_factor": 1.5}
            },
            target_traits=["methodical"]
        )
        
        self.compositor.add_rule(conditional_rule)
        
        # Test with high analytical persona
        high_analytical_persona = create_test_persona(
            "high_analytical",
            traits={"analytical": 0.9, "methodical": 0.6}
        )
        
        composed = self.compositor.compose_persona(
            high_analytical_persona,
            [],
            "conditional_composed"
        )
        
        # Methodical should be enhanced due to high analytical
        self.assertGreater(
            composed.get_trait("methodical"),
            high_analytical_persona.get_trait("methodical")
        )
    
    def test_rule_priority_ordering(self):
        """Test that rules are applied in priority order."""
        # Create rules with different priorities
        high_priority_rule = CompositionRule(
            name="high_priority",
            operation=CompositionOperation.ENHANCE,
            priority=RulePriority.HIGH,
            target_traits=["helpful"],
            parameters={"enhancement_factor": 2.0}
        )
        
        low_priority_rule = CompositionRule(
            name="low_priority",
            operation=CompositionOperation.SUPPRESS,
            priority=RulePriority.LOW,
            target_traits=["helpful"],
            parameters={"suppression_factor": 0.5}
        )
        
        # Add in reverse order to test sorting
        self.compositor.add_rule(low_priority_rule)
        self.compositor.add_rule(high_priority_rule)
        
        composed = self.compositor.compose_persona(
            self.base_persona,
            [],
            "priority_composed"
        )
        
        # High priority rule should be applied first (enhancement),
        # then low priority (suppression), resulting in net change
        base_helpful = self.base_persona.get_trait("helpful")
        expected = min(1.0, base_helpful * 2.0) * 0.5  # Enhance then suppress
        
        self.assertAlmostEqual(
            composed.get_trait("helpful"),
            expected,
            places=2
        )
    
    def test_layered_composition(self):
        """Test simplified layered composition."""
        layers = [
            {"persona": self.source_persona1, "strength": 0.6},
            {"persona": self.source_persona2, "strength": 0.4}
        ]
        
        layered = self.compositor.create_layered_composition(
            self.base_persona,
            layers
        )
        
        self.assertIsInstance(layered, Persona)
        self.assertIn("layered_composition", layered.metadata)
        self.assertEqual(len(layered.metadata["layers"]), 2)
    
    def test_rule_management(self):
        """Test adding and removing rules."""
        test_rule = CompositionRule(
            name="test_rule",
            operation=CompositionOperation.LAYER,
            target_traits=["test_trait"]
        )
        
        # Add rule
        self.compositor.add_rule(test_rule)
        self.assertEqual(len(self.compositor.rules), 1)
        
        # Remove rule
        success = self.compositor.remove_rule("test_rule")
        self.assertTrue(success)
        self.assertEqual(len(self.compositor.rules), 0)
        
        # Try to remove non-existent rule
        success = self.compositor.remove_rule("non_existent")
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()