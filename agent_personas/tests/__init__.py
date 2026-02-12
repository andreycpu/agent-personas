"""
Comprehensive test suites for the agent-personas framework.

Includes unit tests, integration tests, and performance tests
for all major components and features.
"""

# Test configuration
TEST_CONFIG = {
    "test_data_dir": "test_data",
    "performance_test_iterations": 1000,
    "stress_test_duration": 30,  # seconds
    "mock_personas_count": 100,
    "mock_languages": ["en", "es", "fr", "de", "ja", "zh"],
    "test_log_level": "WARNING"
}

# Common test fixtures and utilities
def create_test_persona(name="test_persona", **kwargs):
    """Create a test persona with default values."""
    from ..core.persona import Persona
    
    default_traits = {
        "helpful": 0.8,
        "analytical": 0.6,
        "creative": 0.7,
        "empathetic": 0.5,
        "patient": 0.9
    }
    
    traits = kwargs.pop("traits", default_traits)
    
    return Persona(
        name=name,
        description=kwargs.get("description", f"Test persona named {name}"),
        traits=traits,
        conversation_style=kwargs.get("conversation_style", "professional"),
        emotional_baseline=kwargs.get("emotional_baseline", "calm"),
        metadata=kwargs.get("metadata", {"test": True})
    )


def create_test_archetype():
    """Create a test archetype for testing."""
    from ..templates.archetype import Archetype, ArchetypeCategory
    
    return Archetype(
        name="test_archetype",
        description="Test archetype for unit testing",
        category=ArchetypeCategory.ANALYTICAL,
        core_traits={
            "analytical": 0.9,
            "methodical": 0.8,
            "logical": 0.85
        },
        emotional_tendencies={
            "calm": 0.8,
            "focused": 0.9
        }
    )


def create_test_template():
    """Create a test template for testing."""
    from ..templates.template import PersonaTemplate
    
    return PersonaTemplate(
        name="test_template",
        description="Test template for unit testing",
        category="test",
        base_traits={
            "helpful": 0.8,
            "professional": 0.7
        },
        trait_ranges={
            "helpful": (0.6, 1.0),
            "professional": (0.5, 0.9)
        }
    )


# Test data generators
def generate_test_personas(count=10):
    """Generate multiple test personas."""
    personas = []
    for i in range(count):
        persona = create_test_persona(f"test_persona_{i}")
        personas.append(persona)
    return personas


def generate_random_traits(count=5):
    """Generate random trait dictionary."""
    import random
    
    trait_names = [
        "helpful", "creative", "analytical", "empathetic", "patient",
        "confident", "friendly", "professional", "curious", "wise",
        "energetic", "calm", "focused", "supportive", "innovative"
    ]
    
    traits = {}
    selected_traits = random.sample(trait_names, min(count, len(trait_names)))
    
    for trait in selected_traits:
        traits[trait] = round(random.uniform(0.1, 1.0), 2)
    
    return traits