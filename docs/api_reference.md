# API Reference

This document provides comprehensive API reference for the Agent Personas framework.

## Core Module

### Persona Class

The `Persona` class is the core entity representing an AI agent's personality and characteristics.

#### Constructor

```python
Persona(
    name: str,
    description: str = "",
    traits: Optional[Dict[str, float]] = None,
    conversation_style: str = "neutral",
    emotional_baseline: str = "calm",
    metadata: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `name` (str): Unique identifier for the persona. Must be non-empty.
- `description` (str, optional): Human-readable description of the persona.
- `traits` (Dict[str, float], optional): Dictionary mapping trait names to strength values (0.0-1.0).
- `conversation_style` (str, optional): Default conversation style identifier. Default: "neutral".
- `emotional_baseline` (str, optional): Default emotional state. Default: "calm".
- `metadata` (Dict[str, Any], optional): Additional metadata for the persona.

#### Methods

##### get_trait(trait_name: str) → float
Returns the strength of a specific trait.

**Parameters:**
- `trait_name` (str): Name of the trait to retrieve.

**Returns:**
- `float`: Trait strength value (0.0 if trait doesn't exist).

##### set_trait(trait_name: str, strength: float) → None
Sets the strength of a specific trait with validation.

**Parameters:**
- `trait_name` (str): Name of the trait to set.
- `strength` (float): Strength value between 0.0 and 1.0.

**Raises:**
- `PersonaValidationError`: If parameters are invalid.

##### validate() → bool
Validates the persona configuration.

**Returns:**
- `bool`: True if valid.

**Raises:**
- `PersonaValidationError`: If validation fails.

##### to_dict() → Dict[str, Any]
Converts persona to dictionary representation.

**Returns:**
- `Dict[str, Any]`: Dictionary containing all persona data.

##### to_json() → str
Converts persona to JSON string.

**Returns:**
- `str`: JSON representation of the persona.

**Raises:**
- `PersonaSerializationError`: If serialization fails.

#### Class Methods

##### from_dict(data: Dict[str, Any]) → Persona
Creates a persona from a dictionary.

**Parameters:**
- `data` (Dict[str, Any]): Dictionary containing persona data.

**Returns:**
- `Persona`: New persona instance.

**Raises:**
- `PersonaValidationError`: If data is invalid.

##### from_json(json_str: str) → Persona
Creates a persona from a JSON string.

**Parameters:**
- `json_str` (str): JSON string containing persona data.

**Returns:**
- `Persona`: New persona instance.

**Raises:**
- `PersonaSerializationError`: If JSON is invalid.
- `PersonaValidationError`: If data is invalid.

### PersonaManager Class

High-level manager for persona operations including activation and switching.

#### Constructor

```python
PersonaManager(
    registry: Optional[PersonaRegistry] = None,
    default_persona: Optional[str] = None
)
```

**Parameters:**
- `registry` (PersonaRegistry, optional): Registry instance to use.
- `default_persona` (str, optional): Name of default persona to activate.

#### Properties

##### active_persona → Optional[Persona]
Returns the currently active persona.

##### active_persona_name → Optional[str]
Returns the name of the currently active persona.

#### Methods

##### register_persona(persona: Persona) → None
Registers a new persona with validation.

**Parameters:**
- `persona` (Persona): Persona instance to register.

**Raises:**
- `PersonaRegistrationError`: If registration fails.

##### create_persona(...) → Persona
Creates and registers a new persona.

**Parameters:**
- `name` (str): Persona name.
- `description` (str, optional): Description.
- `traits` (Dict[str, float], optional): Trait dictionary.
- `conversation_style` (str, optional): Conversation style.
- `emotional_baseline` (str, optional): Emotional baseline.
- `metadata` (Dict[str, Any], optional): Additional metadata.
- `activate` (bool, optional): Whether to activate after creation.

**Returns:**
- `Persona`: Created persona instance.

**Raises:**
- `PersonaRegistrationError`: If creation fails.

##### activate_persona(name: str) → bool
Activates a persona by name with comprehensive error handling.

**Parameters:**
- `name` (str): Name of persona to activate.

**Returns:**
- `bool`: True if successfully activated.

**Raises:**
- `PersonaActivationError`: If activation fails.

##### switch_persona(name: str) → bool
Switches to a different persona.

**Parameters:**
- `name` (str): Name of persona to switch to.

**Returns:**
- `bool`: True if successfully switched.

##### deactivate_persona() → Optional[Persona]
Deactivates the current persona.

**Returns:**
- `Optional[Persona]`: Previously active persona, if any.

##### add_switch_callback(callback: Callable) → None
Adds a callback for persona switches.

**Parameters:**
- `callback`: Function to call when personas are switched.

**Raises:**
- `PersonaManagerError`: If callback is invalid.

##### get_status() → Dict[str, Any]
Returns current manager status.

**Returns:**
- `Dict[str, Any]`: Status information including active persona and statistics.

## Cache Module

### MemoryCache Class

Thread-safe memory cache with TTL and LRU eviction capabilities.

#### Constructor

```python
MemoryCache(
    max_size: int = 1000,
    default_ttl: Optional[float] = None,
    cleanup_interval: float = 60.0
)
```

**Parameters:**
- `max_size` (int): Maximum number of cache entries.
- `default_ttl` (float, optional): Default time-to-live in seconds.
- `cleanup_interval` (float): Cleanup interval in seconds.

#### Methods

##### get(key: str, default: Any = None) → Any
Retrieves a value from the cache.

**Parameters:**
- `key` (str): Cache key.
- `default` (Any, optional): Default value if key not found.

**Returns:**
- `Any`: Cached value or default.

##### put(key: str, value: Any, ttl: Optional[float] = None) → None
Stores a value in the cache.

**Parameters:**
- `key` (str): Cache key.
- `value` (Any): Value to cache.
- `ttl` (float, optional): Time-to-live override.

##### get_or_compute(key: str, compute_func: Callable, ttl: Optional[float] = None) → Any
Gets value from cache or computes and caches it.

**Parameters:**
- `key` (str): Cache key.
- `compute_func` (Callable): Function to compute value if not cached.
- `ttl` (float, optional): Time-to-live for computed value.

**Returns:**
- `Any`: Cached or computed value.

##### get_stats() → Dict[str, Any]
Returns cache statistics.

**Returns:**
- `Dict[str, Any]`: Statistics including hit rate, size, evictions, etc.

## Configuration Module

### Validators

#### validate_config(config: Dict[str, Any]) → bool
Validates a complete configuration dictionary.

**Parameters:**
- `config` (Dict[str, Any]): Configuration to validate.

**Returns:**
- `bool`: True if valid.

**Raises:**
- `ConfigValidationError`: If validation fails.

#### validate_persona_definition(persona_data: Dict[str, Any]) → bool
Validates a persona definition dictionary.

**Parameters:**
- `persona_data` (Dict[str, Any]): Persona data to validate.

**Returns:**
- `bool`: True if valid.

**Raises:**
- `ConfigValidationError`: If validation fails.

## Utility Module

### Helper Functions

#### generate_persona_id(prefix: str = "persona", length: int = 8) → str
Generates a unique persona ID.

#### normalize_trait_name(name: str) → str
Normalizes trait names to standard format.

#### clamp_value(value: float, min_val: float = 0.0, max_val: float = 1.0) → float
Clamps a value to specified range.

#### weighted_average(values: Dict[str, float], weights: Optional[Dict[str, float]] = None) → float
Calculates weighted average of values.

#### fuzzy_match(text: str, patterns: List[str], threshold: float = 0.6) → bool
Performs fuzzy text matching.

#### deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) → Dict[str, Any]
Deep merges two dictionaries.

#### interpolate_value(value1: float, value2: float, factor: float) → float
Interpolates between two values.

#### get_trait_category(trait_name: str) → str
Estimates trait category from name.

## Exceptions

### PersonaValidationError
Raised when persona validation fails.

### PersonaSerializationError
Raised when persona serialization/deserialization fails.

### PersonaManagerError
Base exception for persona manager errors.

### PersonaActivationError
Raised when persona activation fails.

### PersonaRegistrationError
Raised when persona registration fails.

### ConfigValidationError
Raised when configuration validation fails.

## Usage Examples

### Basic Usage

```python
from agent_personas import Persona, PersonaManager

# Create a persona
persona = Persona(
    name="helpful_assistant",
    description="A friendly and helpful AI assistant",
    traits={
        "helpfulness": 0.9,
        "friendliness": 0.8,
        "patience": 0.7
    },
    conversation_style="friendly",
    emotional_baseline="positive"
)

# Create manager and register persona
manager = PersonaManager()
manager.register_persona(persona)

# Activate persona
manager.activate_persona("helpful_assistant")

# Check status
status = manager.get_status()
print(f"Active persona: {status['active_persona']}")
```

### Advanced Usage

```python
from agent_personas import PersonaManager
from agent_personas.cache import MemoryCache

# Create manager with caching
cache = MemoryCache(max_size=100, default_ttl=300)
manager = PersonaManager()

# Create persona with validation
try:
    persona = manager.create_persona(
        name="analytical_expert",
        description="An analytical and detail-oriented expert",
        traits={
            "analytical_thinking": 0.95,
            "attention_to_detail": 0.90,
            "patience": 0.85
        },
        activate=True
    )
    print("Persona created and activated successfully")
except Exception as e:
    print(f"Error: {e}")

# Add switch callback
def on_persona_switch(old_persona, new_persona):
    if new_persona:
        print(f"Switched to: {new_persona.name}")

manager.add_switch_callback(on_persona_switch)
```