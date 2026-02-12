"""
Performance tests for persona framework components.
"""

import unittest
import time
import psutil
import gc
from memory_profiler import profile
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...core.persona import Persona
from ...templates.archetype import ArchetypeManager
from ...templates.template import TemplateManager
from ...composition.blender import PersonaBlender
from ...evaluation.persona_evaluator import PersonaEvaluator
from ...versioning.version_manager import VersionManager
from ...multilingual.multilingual_persona import MultilingualPersona
from .. import create_test_persona, generate_test_personas, TEST_CONFIG


class PerformanceTestCase(unittest.TestCase):
    """Base class for performance tests with timing and memory utilities."""
    
    def setUp(self):
        """Set up performance monitoring."""
        self.start_time = None
        self.start_memory = None
        gc.collect()  # Clean memory before tests
    
    def start_performance_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    def end_performance_monitoring(self, operation_name: str, max_time: float = None, max_memory: float = None):
        """End performance monitoring and check thresholds."""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        elapsed_time = end_time - self.start_time
        memory_used = end_memory - self.start_memory
        
        print(f"\n{operation_name} Performance:")
        print(f"  Time: {elapsed_time:.3f}s")
        print(f"  Memory: {memory_used:.2f}MB")
        
        if max_time and elapsed_time > max_time:
            self.fail(f"{operation_name} took {elapsed_time:.3f}s, expected < {max_time}s")
        
        if max_memory and memory_used > max_memory:
            self.fail(f"{operation_name} used {memory_used:.2f}MB, expected < {max_memory}MB")
        
        return elapsed_time, memory_used


class TestPersonaPerformance(PerformanceTestCase):
    """Performance tests for basic persona operations."""
    
    def test_persona_creation_performance(self):
        """Test performance of creating many personas."""
        self.start_performance_monitoring()
        
        personas = []
        count = TEST_CONFIG["mock_personas_count"]
        
        for i in range(count):
            persona = create_test_persona(f"persona_{i}")
            personas.append(persona)
        
        elapsed, memory = self.end_performance_monitoring(
            f"Creating {count} personas",
            max_time=5.0,  # Should take less than 5 seconds
            max_memory=50.0  # Should use less than 50MB
        )
        
        self.assertEqual(len(personas), count)
        
        # Test average creation time
        avg_time = elapsed / count
        self.assertLess(avg_time, 0.1, f"Average persona creation time: {avg_time:.4f}s")
    
    def test_persona_trait_operations_performance(self):
        """Test performance of trait operations."""
        persona = create_test_persona("performance_test")
        iterations = 10000
        
        self.start_performance_monitoring()
        
        # Test trait setting
        for i in range(iterations):
            persona.set_trait(f"trait_{i % 10}", 0.5 + (i % 10) / 20)
        
        # Test trait getting
        for i in range(iterations):
            value = persona.get_trait(f"trait_{i % 10}")
        
        elapsed, memory = self.end_performance_monitoring(
            f"Trait operations ({iterations * 2})",
            max_time=2.0
        )
        
        # Should be very fast
        avg_time = elapsed / (iterations * 2)
        self.assertLess(avg_time, 0.001, f"Average trait operation time: {avg_time:.6f}s")
    
    def test_persona_serialization_performance(self):
        """Test performance of persona serialization."""
        personas = generate_test_personas(100)
        
        self.start_performance_monitoring()
        
        # Test to_dict
        dicts = [persona.to_dict() for persona in personas]
        
        # Test to_json  
        jsons = [persona.to_json() for persona in personas]
        
        # Test from_dict
        recreated = [Persona.from_dict(d) for d in dicts]
        
        # Test from_json
        from_json = [Persona.from_json(j) for j in jsons]
        
        elapsed, memory = self.end_performance_monitoring(
            "Persona serialization (400 operations)",
            max_time=3.0
        )
        
        self.assertEqual(len(recreated), 100)
        self.assertEqual(len(from_json), 100)


class TestBlenderPerformance(PerformanceTestCase):
    """Performance tests for persona blending."""
    
    def setUp(self):
        super().setUp()
        self.blender = PersonaBlender()
        self.test_personas = generate_test_personas(20)
    
    def test_blending_performance(self):
        """Test performance of persona blending operations."""
        blend_pairs = [
            (self.test_personas[i], self.test_personas[i+1])
            for i in range(0, len(self.test_personas)-1, 2)
        ]
        
        self.start_performance_monitoring()
        
        blended_personas = []
        for i, (persona1, persona2) in enumerate(blend_pairs):
            blended = self.blender.blend_personas(
                [persona1, persona2],
                f"blended_{i}"
            )
            blended_personas.append(blended)
        
        elapsed, memory = self.end_performance_monitoring(
            f"Blending {len(blend_pairs)} persona pairs",
            max_time=5.0
        )
        
        self.assertEqual(len(blended_personas), len(blend_pairs))
        
        # Test average blending time
        avg_time = elapsed / len(blend_pairs)
        self.assertLess(avg_time, 1.0, f"Average blend time: {avg_time:.3f}s")
    
    def test_compatibility_analysis_performance(self):
        """Test performance of compatibility analysis."""
        test_sets = [
            self.test_personas[i:i+3] for i in range(0, len(self.test_personas)-2, 3)
        ]
        
        self.start_performance_monitoring()
        
        analyses = []
        for persona_set in test_sets:
            analysis = self.blender.analyze_blend_compatibility(persona_set)
            analyses.append(analysis)
        
        elapsed, memory = self.end_performance_monitoring(
            f"Compatibility analysis ({len(test_sets)} sets)",
            max_time=3.0
        )
        
        self.assertEqual(len(analyses), len(test_sets))
    
    def test_large_group_blending_performance(self):
        """Test performance with large groups of personas."""
        large_group = self.test_personas[:10]  # Blend 10 personas
        
        self.start_performance_monitoring()
        
        blended = self.blender.blend_personas(
            large_group,
            "large_group_blend"
        )
        
        elapsed, memory = self.end_performance_monitoring(
            "Large group blending (10 personas)",
            max_time=10.0
        )
        
        self.assertIsNotNone(blended)
        self.assertEqual(len(blended.metadata["blend_source_personas"]), 10)


class TestEvaluationPerformance(PerformanceTestCase):
    """Performance tests for persona evaluation."""
    
    def setUp(self):
        super().setUp()
        self.evaluator = PersonaEvaluator()
        self.test_personas = generate_test_personas(50)
    
    def test_evaluation_performance(self):
        """Test performance of persona evaluation."""
        self.start_performance_monitoring()
        
        evaluations = []
        for persona in self.test_personas:
            evaluation = self.evaluator.evaluate_persona(persona)
            evaluations.append(evaluation)
        
        elapsed, memory = self.end_performance_monitoring(
            f"Evaluating {len(self.test_personas)} personas",
            max_time=30.0  # Evaluation is more complex, allow more time
        )
        
        self.assertEqual(len(evaluations), len(self.test_personas))
        
        # Test average evaluation time
        avg_time = elapsed / len(self.test_personas)
        self.assertLess(avg_time, 1.0, f"Average evaluation time: {avg_time:.3f}s")
    
    def test_comparison_performance(self):
        """Test performance of persona comparison."""
        comparison_groups = [
            self.test_personas[i:i+5] for i in range(0, len(self.test_personas)-4, 5)
        ]
        
        self.start_performance_monitoring()
        
        comparisons = []
        for group in comparison_groups:
            comparison = self.evaluator.compare_personas(group)
            comparisons.append(comparison)
        
        elapsed, memory = self.end_performance_monitoring(
            f"Comparing {len(comparison_groups)} groups",
            max_time=60.0
        )
        
        self.assertEqual(len(comparisons), len(comparison_groups))


class TestVersioningPerformance(PerformanceTestCase):
    """Performance tests for version management."""
    
    def setUp(self):
        super().setUp()
        self.version_manager = VersionManager()
        self.base_personas = generate_test_personas(10)
    
    def test_version_creation_performance(self):
        """Test performance of version creation."""
        versions_per_persona = 20
        
        self.start_performance_monitoring()
        
        total_versions = 0
        for persona in self.base_personas:
            # Create initial version
            self.version_manager.create_initial_version(persona, "1.0.0")
            total_versions += 1
            
            # Create multiple versions
            current_persona = persona
            for i in range(versions_per_persona):
                # Slightly modify persona
                current_persona.set_trait(f"dynamic_trait_{i}", 0.5)
                version = self.version_manager.create_new_version(
                    persona.name,
                    current_persona,
                    "patch" if i % 3 == 0 else "minor",
                    f"Version {i+1}"
                )
                total_versions += 1
        
        elapsed, memory = self.end_performance_monitoring(
            f"Creating {total_versions} versions",
            max_time=15.0
        )
        
        # Test average version creation time
        avg_time = elapsed / total_versions
        self.assertLess(avg_time, 0.1, f"Average version creation time: {avg_time:.4f}s")
    
    def test_version_comparison_performance(self):
        """Test performance of version comparison."""
        persona = self.base_personas[0]
        
        # Create multiple versions
        self.version_manager.create_initial_version(persona, "1.0.0")
        
        versions = []
        for i in range(10):
            persona.set_trait(f"trait_{i}", 0.5 + i * 0.05)
            version = self.version_manager.create_new_version(
                persona.name,
                persona,
                "minor",
                f"Update {i}"
            )
            versions.append(version.version_number)
        
        self.start_performance_monitoring()
        
        # Compare all adjacent versions
        comparisons = []
        for i in range(len(versions)-1):
            comparison = self.version_manager.compare_versions(
                persona.name,
                versions[i],
                versions[i+1]
            )
            comparisons.append(comparison)
        
        elapsed, memory = self.end_performance_monitoring(
            f"Comparing {len(comparisons)} version pairs",
            max_time=5.0
        )
        
        self.assertEqual(len(comparisons), len(versions)-1)


class TestMultilingualPerformance(PerformanceTestCase):
    """Performance tests for multilingual personas."""
    
    def test_multilingual_creation_performance(self):
        """Test performance of multilingual persona creation."""
        base_personas = generate_test_personas(10)
        languages = TEST_CONFIG["mock_languages"]
        
        self.start_performance_monitoring()
        
        multilingual_personas = []
        for persona in base_personas:
            ml_persona = MultilingualPersona(persona, "en")
            
            # Add all test languages
            for lang in languages[1:]:  # Skip 'en' as it's primary
                ml_persona.add_language_profile(lang, 0.8)
            
            multilingual_personas.append(ml_persona)
        
        elapsed, memory = self.end_performance_monitoring(
            f"Creating {len(base_personas)} multilingual personas",
            max_time=10.0
        )
        
        # Test language switching performance
        switch_start = time.time()
        
        for ml_persona in multilingual_personas:
            for lang in languages:
                ml_persona.switch_language(lang)
                adapted = ml_persona.get_active_persona()
        
        switch_elapsed = time.time() - switch_start
        total_switches = len(multilingual_personas) * len(languages)
        avg_switch_time = switch_elapsed / total_switches
        
        print(f"\nLanguage switching performance:")
        print(f"  Total switches: {total_switches}")
        print(f"  Average switch time: {avg_switch_time:.4f}s")
        
        self.assertLess(avg_switch_time, 0.01, f"Language switching too slow: {avg_switch_time:.4f}s")


class TestConcurrencyPerformance(PerformanceTestCase):
    """Performance tests for concurrent operations."""
    
    def test_concurrent_persona_creation(self):
        """Test concurrent persona creation."""
        personas_per_thread = 20
        num_threads = 4
        total_personas = personas_per_thread * num_threads
        
        def create_personas(thread_id):
            """Create personas in a thread."""
            personas = []
            for i in range(personas_per_thread):
                persona = create_test_persona(f"thread_{thread_id}_persona_{i}")
                personas.append(persona)
            return personas
        
        self.start_performance_monitoring()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_personas, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        elapsed, memory = self.end_performance_monitoring(
            f"Concurrent creation of {total_personas} personas",
            max_time=10.0
        )
        
        # Flatten results
        all_personas = [persona for thread_personas in results for persona in thread_personas]
        self.assertEqual(len(all_personas), total_personas)
    
    def test_concurrent_evaluation(self):
        """Test concurrent persona evaluation."""
        personas = generate_test_personas(20)
        
        def evaluate_persona(persona):
            """Evaluate a persona."""
            evaluator = PersonaEvaluator()  # Each thread gets its own evaluator
            return evaluator.evaluate_persona(persona)
        
        self.start_performance_monitoring()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(evaluate_persona, persona) for persona in personas]
            evaluations = [future.result() for future in as_completed(futures)]
        
        elapsed, memory = self.end_performance_monitoring(
            f"Concurrent evaluation of {len(personas)} personas",
            max_time=30.0
        )
        
        self.assertEqual(len(evaluations), len(personas))
        
        # All evaluations should be valid
        for evaluation in evaluations:
            self.assertIsNotNone(evaluation.overall_score)
            self.assertGreaterEqual(evaluation.overall_score, 0.0)
            self.assertLessEqual(evaluation.overall_score, 1.0)


class TestMemoryEfficiency(PerformanceTestCase):
    """Tests for memory efficiency and leak detection."""
    
    def test_memory_usage_scaling(self):
        """Test that memory usage scales reasonably with persona count."""
        persona_counts = [10, 50, 100, 200]
        memory_usage = []
        
        for count in persona_counts:
            gc.collect()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            personas = generate_test_personas(count)
            
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory
            memory_usage.append(memory_used)
            
            print(f"\n{count} personas: {memory_used:.2f}MB")
            
            # Clean up
            del personas
            gc.collect()
        
        # Memory usage should scale reasonably (not exponentially)
        for i in range(1, len(memory_usage)):
            ratio = memory_usage[i] / memory_usage[i-1]
            count_ratio = persona_counts[i] / persona_counts[i-1]
            
            # Memory usage should not grow faster than 2x the persona count ratio
            self.assertLess(ratio, count_ratio * 2, 
                           f"Memory usage growing too fast: {ratio:.2f}x for {count_ratio}x personas")
    
    def test_no_memory_leaks(self):
        """Test for memory leaks in repeated operations."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Perform operations multiple times
        for cycle in range(10):
            # Create and destroy personas
            personas = generate_test_personas(50)
            
            # Perform operations
            blender = PersonaBlender()
            for i in range(0, len(personas)-1, 2):
                blended = blender.blend_personas(
                    [personas[i], personas[i+1]],
                    f"temp_blend_{cycle}_{i}"
                )
            
            # Clean up
            del personas
            del blender
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        print(f"\nMemory growth after 10 cycles: {memory_growth:.2f}MB")
        
        # Memory growth should be minimal (less than 20MB)
        self.assertLess(memory_growth, 20, 
                       f"Potential memory leak detected: {memory_growth:.2f}MB growth")


if __name__ == "__main__":
    # Configure test runner for performance tests
    unittest.TestLoader.sortTestMethodsUsing = None  # Preserve test order
    
    # Run tests with timing
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    print(f"\nTotal test execution time: {end_time - start_time:.2f}s")
    
    if not result.wasSuccessful():
        exit(1)