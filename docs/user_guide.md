# User Guide

This guide provides practical instructions for using the Agent Personas framework to create, manage, and deploy AI agent personalities.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Creating Personas](#creating-personas)
4. [Managing Personas](#managing-personas)
5. [Persona Switching](#persona-switching)
6. [Configuration](#configuration)
7. [Advanced Features](#advanced-features)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Installation

### Basic Installation

```bash
pip install agent-personas
```

### Development Installation

```bash
git clone https://github.com/andreycpu/agent-personas.git
cd agent-personas
pip install -e ".[dev]"
```

### Optional Dependencies

```bash
# For examples and tutorials
pip install agent-personas[examples]

# For documentation generation
pip install agent-personas[docs]

# For all optional features
pip install agent-personas[dev,examples,docs]
```

## Quick Start

Here's a minimal example to get you started:

```python
from agent_personas import Persona, PersonaManager

# Create a simple persona
persona = Persona(
    name="assistant",
    description="A helpful assistant",
    traits={"helpfulness": 0.9, "patience": 0.8}
)

# Initialize manager and activate persona
manager = PersonaManager()
manager.register_persona(persona)
manager.activate_persona("assistant")

print(f"Active persona: {manager.active_persona.name}")
```

## Creating Personas

### Basic Persona Creation

```python
from agent_personas import Persona

# Method 1: Direct instantiation
persona = Persona(
    name="creative_writer",
    description="A creative and imaginative writer",
    traits={
        "creativity": 0.95,
        "imagination": 0.90,
        "vocabulary": 0.85,
        "empathy": 0.75
    },
    conversation_style="expressive",
    emotional_baseline="inspired"
)

# Method 2: Using PersonaManager
manager = PersonaManager()
persona = manager.create_persona(
    name="technical_expert",
    description="A precise technical expert",
    traits={
        "technical_knowledge": 0.95,
        "precision": 0.90,
        "analytical_thinking": 0.85
    },
    conversation_style="professional",
    activate=True  # Activate immediately
)
```

### Persona from Configuration

```python
# From dictionary
persona_config = {
    "name": "mentor",
    "description": "A wise and supportive mentor",
    "traits": {
        "wisdom": 0.90,
        "supportiveness": 0.85,
        "patience": 0.95,
        "encouragement": 0.80
    },
    "conversation_style": "supportive",
    "emotional_baseline": "calm",
    "metadata": {
        "version": "1.0",
        "category": "educational"
    }
}

persona = Persona.from_dict(persona_config)

# From JSON file
import json

with open('mentor_persona.json', 'r') as f:
    persona_data = json.load(f)
    
persona = Persona.from_json(json.dumps(persona_data))
```

### Trait Guidelines

Traits should be values between 0.0 and 1.0 representing the strength of that characteristic:

- **0.0 - 0.3**: Low/minimal presence of the trait
- **0.3 - 0.7**: Moderate presence of the trait  
- **0.7 - 1.0**: Strong/dominant presence of the trait

Common trait categories:

```python
# Personality traits
personality_traits = {
    "extraversion": 0.6,      # Social energy and outgoingness
    "agreeableness": 0.8,     # Cooperativeness and trust
    "conscientiousness": 0.7, # Organization and dependability
    "neuroticism": 0.3,       # Emotional stability (inverted)
    "openness": 0.8           # Creativity and curiosity
}

# Communication traits
communication_traits = {
    "formality": 0.4,         # Level of formal language
    "verbosity": 0.6,         # Amount of detail in responses
    "humor": 0.7,             # Use of humor and wit
    "empathy": 0.9            # Emotional understanding
}

# Cognitive traits
cognitive_traits = {
    "analytical_thinking": 0.8,
    "creative_thinking": 0.7,
    "attention_to_detail": 0.9,
    "abstract_reasoning": 0.6
}
```

## Managing Personas

### PersonaManager Operations

```python
from agent_personas import PersonaManager

manager = PersonaManager()

# Register multiple personas
personas = [
    Persona(name="analyst", traits={"analytical": 0.9}),
    Persona(name="creative", traits={"creativity": 0.9}),
    Persona(name="support", traits={"empathy": 0.9})
]

for persona in personas:
    manager.register_persona(persona)

# List available personas
print("Available personas:", manager.list_personas())

# Get manager status
status = manager.get_status()
print(f"Total personas: {status['total_personas']}")
print(f"Active: {status['active_persona']}")
```

### Persona Validation

```python
# Validate before using
try:
    persona.validate()
    print("Persona is valid")
except PersonaValidationError as e:
    print(f"Validation error: {e}")

# Check specific traits
if persona.get_trait("creativity") > 0.7:
    print("This is a highly creative persona")
```

### Persistence

```python
# Save persona to JSON
persona_json = persona.to_json()
with open('my_persona.json', 'w') as f:
    f.write(persona_json)

# Load persona from JSON
with open('my_persona.json', 'r') as f:
    loaded_persona = Persona.from_json(f.read())

# Export all personas
all_personas = {}
for name in manager.list_personas():
    persona = manager.registry.get(name)
    all_personas[name] = persona.to_dict()

with open('all_personas.json', 'w') as f:
    json.dump(all_personas, f, indent=2)
```

## Persona Switching

### Basic Switching

```python
# Activate different personas
manager.activate_persona("analyst")
print(f"Current: {manager.active_persona.name}")

manager.switch_persona("creative")
print(f"Switched to: {manager.active_persona.name}")

# Revert to previous persona
manager.revert_persona()
print(f"Reverted to: {manager.active_persona.name}")
```

### Switch Callbacks

```python
def log_persona_switch(old_persona, new_persona):
    if old_persona and new_persona:
        print(f"Switched from {old_persona.name} to {new_persona.name}")
    elif new_persona:
        print(f"Activated {new_persona.name}")
    elif old_persona:
        print(f"Deactivated {old_persona.name}")

# Register callback
manager.add_switch_callback(log_persona_switch)

# Now switches will be logged
manager.switch_persona("support")  # Logs the switch
```

### Conditional Switching

```python
def smart_switch(manager, target_persona, condition_func):
    """Switch personas based on a condition."""
    current = manager.active_persona
    
    if condition_func(current):
        try:
            manager.activate_persona(target_persona)
            return True
        except PersonaActivationError as e:
            print(f"Switch failed: {e}")
            return False
    return False

# Example usage
def needs_creativity(persona):
    return persona.get_trait("creativity") < 0.5

# Switch to creative persona if current lacks creativity
smart_switch(manager, "creative", needs_creativity)
```

## Configuration

### Basic Configuration

```python
from agent_personas.config import validate_config

config = {
    "framework": {
        "version": "1.0.0",
        "max_history_size": 100
    },
    "personas": {
        "min_traits": 1,
        "max_traits": 20
    },
    "traits": {
        "default_trait_value": 0.5,
        "trait_bounds": {"min": 0.0, "max": 1.0}
    },
    "logging": {
        "level": "INFO",
        "max_file_size_mb": 10
    }
}

# Validate configuration
try:
    validate_config(config)
    print("Configuration is valid")
except ConfigValidationError as e:
    print(f"Configuration error: {e}")
```

### Environment Variables

```bash
# Set log level
export AGENT_PERSONAS_LOG_LEVEL=DEBUG

# Set cache configuration
export AGENT_PERSONAS_CACHE_SIZE=1000
export AGENT_PERSONAS_CACHE_TTL=300
```

## Advanced Features

### Caching

```python
from agent_personas.cache import MemoryCache

# Create cache for persona operations
cache = MemoryCache(max_size=100, default_ttl=300)

# Cache computed traits
def get_derived_trait(persona_name, trait_name):
    cache_key = f"{persona_name}:{trait_name}"
    
    return cache.get_or_compute(
        cache_key,
        lambda: expensive_trait_computation(persona_name, trait_name)
    )

# Cache persona lookup results
persona_cache = MemoryCache(max_size=50)
```

### Trait Utilities

```python
from agent_personas.utils.helpers import (
    clamp_value,
    weighted_average,
    get_trait_category,
    interpolate_value
)

# Normalize trait values
normalized_creativity = clamp_value(persona.get_trait("creativity"))

# Calculate composite scores
traits = {"logic": 0.8, "creativity": 0.9, "speed": 0.6}
weights = {"logic": 2.0, "creativity": 1.5, "speed": 1.0}
composite_score = weighted_average(traits, weights)

# Categorize traits automatically
category = get_trait_category("analytical_thinking")  # Returns "cognitive"

# Interpolate between trait values
mid_value = interpolate_value(0.2, 0.8, 0.5)  # Returns 0.5
```

### Search and Filtering

```python
# Search personas by traits
def find_personas_by_trait(manager, trait_name, min_value=0.7):
    results = []
    for name in manager.list_personas():
        persona = manager.registry.get(name)
        if persona.get_trait(trait_name) >= min_value:
            results.append(persona)
    return results

# Find creative personas
creative_personas = find_personas_by_trait(manager, "creativity", 0.8)

# Search by description
analytical_personas = manager.search_personas("analytical")
```

## Best Practices

### Persona Design

1. **Start Simple**: Begin with 3-5 core traits rather than 20+
2. **Be Consistent**: Ensure traits align with the intended behavior
3. **Use Descriptive Names**: Choose clear, meaningful trait names
4. **Validate Early**: Always validate personas after creation
5. **Document Intent**: Use descriptions to explain the persona's purpose

```python
# Good persona design
persona = Persona(
    name="customer_support",
    description="Empathetic and patient customer support agent",
    traits={
        "empathy": 0.95,           # High emotional intelligence
        "patience": 0.90,          # Calm under pressure  
        "helpfulness": 0.90,       # Strong desire to assist
        "technical_knowledge": 0.70, # Moderate technical skills
        "formality": 0.60          # Professional but approachable
    },
    conversation_style="supportive",
    emotional_baseline="calm"
)
```

### Error Handling

```python
def safe_persona_operation(operation, *args, **kwargs):
    """Safely execute persona operations with comprehensive error handling."""
    try:
        return operation(*args, **kwargs)
    except PersonaValidationError as e:
        logger.error(f"Validation error: {e}")
        return None
    except PersonaActivationError as e:
        logger.error(f"Activation error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

# Usage
result = safe_persona_operation(manager.activate_persona, "analyst")
```

### Performance Optimization

```python
# Use caching for expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def get_persona_summary(persona_name):
    persona = manager.registry.get(persona_name)
    return {
        "name": persona.name,
        "dominant_traits": get_dominant_traits(persona),
        "style": persona.conversation_style
    }

def get_dominant_traits(persona, threshold=0.7):
    return {
        name: value for name, value 
        in persona.traits.items() 
        if value >= threshold
    }
```

### Testing Personas

```python
import unittest

class TestPersonaBehavior(unittest.TestCase):
    def setUp(self):
        self.manager = PersonaManager()
        self.test_persona = Persona(
            name="test_persona",
            traits={"test_trait": 0.8}
        )
        self.manager.register_persona(self.test_persona)
    
    def test_persona_activation(self):
        success = self.manager.activate_persona("test_persona")
        self.assertTrue(success)
        self.assertEqual(
            self.manager.active_persona.name, 
            "test_persona"
        )
    
    def test_trait_values(self):
        trait_value = self.test_persona.get_trait("test_trait")
        self.assertAlmostEqual(trait_value, 0.8)
        
        # Test non-existent trait
        missing_trait = self.test_persona.get_trait("missing")
        self.assertEqual(missing_trait, 0.0)
```

## Troubleshooting

### Common Issues

#### 1. Persona Validation Errors

```python
# Problem: Trait values outside valid range
try:
    persona.set_trait("invalid_trait", 1.5)  # > 1.0
except PersonaValidationError as e:
    print(f"Fix trait value: {e}")

# Solution: Clamp values
from agent_personas.utils.helpers import clamp_value
safe_value = clamp_value(1.5)  # Returns 1.0
persona.set_trait("valid_trait", safe_value)
```

#### 2. Activation Failures

```python
# Problem: Persona not found
try:
    manager.activate_persona("nonexistent")
except PersonaActivationError as e:
    print(f"Persona not found: {e}")

# Solution: Check existence first
if manager.registry.exists("target_persona"):
    manager.activate_persona("target_persona")
else:
    print("Persona not available")
```

#### 3. Serialization Issues

```python
# Problem: Complex metadata types
persona.metadata = {"timestamp": datetime.now()}  # Not JSON serializable

try:
    json_str = persona.to_json()
except PersonaSerializationError as e:
    print(f"Serialization failed: {e}")

# Solution: Use JSON-compatible types
persona.metadata = {"timestamp": datetime.now().isoformat()}
json_str = persona.to_json()  # Success
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# This will now show detailed persona operations
manager.activate_persona("debug_test")  # Logs validation, activation steps
```

### Performance Monitoring

```python
import time

def time_operation(operation_name, func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start_time
    print(f"{operation_name} took {elapsed:.4f}s")
    return result

# Monitor persona operations
result = time_operation(
    "Persona Creation",
    manager.create_persona,
    name="perf_test",
    traits={"test": 0.5}
)
```

### Memory Usage

```python
import psutil
import os

def check_memory_usage():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")

# Monitor memory after persona operations
check_memory_usage()
for i in range(100):
    manager.create_persona(f"persona_{i}", traits={"test": 0.5})
check_memory_usage()
```

## Further Reading

- [API Reference](api_reference.md) - Complete API documentation
- [Examples](../examples/) - Practical usage examples
- [Contributing](../CONTRIBUTING.md) - How to contribute to the project
- [Changelog](../CHANGELOG.md) - Version history and updates