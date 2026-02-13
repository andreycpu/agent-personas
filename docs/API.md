# Agent Personas API Documentation

## Overview

The Agent Personas framework provides a comprehensive system for creating, managing, and deploying AI personas with distinct personalities, knowledge bases, and communication styles.

## Core Components

### PersonaManager

The main interface for persona management operations.

```python
from agent_personas import PersonaManager

manager = PersonaManager()

# Create a new persona
persona = manager.create_persona(
    name="Assistant",
    traits={
        "personality": {"extroversion": 0.7, "openness": 0.8},
        "communication_style": "friendly",
        "knowledge_areas": ["technology", "science"]
    }
)

# Load existing persona
persona = manager.load_persona("assistant_id")

# Update persona traits
manager.update_persona_traits("assistant_id", new_traits)
```

### Persona Class

Represents an individual persona with its traits and behaviors.

```python
# Access persona properties
print(persona.name)
print(persona.traits)
print(persona.knowledge_areas)

# Generate responses
response = persona.generate_response(
    message="Hello, how are you?",
    context={"user_id": "user123"}
)

# Update persona state
persona.add_memory("User prefers technical explanations")
persona.update_traits({"enthusiasm": 0.9})
```

### Memory Integration

Manage persona memory and learning capabilities.

```python
from agent_personas.memory_integration import PersonaMemory

memory = PersonaMemory(persona_id="assistant")

# Add memories
memory.add_memory(
    content="User enjoys discussing AI ethics",
    importance=0.8,
    tags=["preferences", "ai", "ethics"]
)

# Retrieve relevant memories
memories = memory.get_relevant_memories(
    query="artificial intelligence",
    limit=5
)

# Update memory importance
memory.update_importance("memory_id", 0.9)
```

### Configuration

Configure persona behavior and system settings.

```python
from agent_personas.config import PersonaConfig

config = PersonaConfig()

# Set global defaults
config.set_default_traits({
    "response_length": "medium",
    "formality_level": 0.6,
    "creativity": 0.7
})

# Validate configuration
config.validate()

# Load from file
config.load_from_file("persona_config.json")
```

## Validation Framework

### Input Validation

```python
from agent_personas.validation import (
    validate_persona_name,
    validate_persona_traits,
    validate_context_data
)

# Validate persona data
try:
    validate_persona_name("My Assistant")
    validate_persona_traits({
        "personality": {"extroversion": 0.7},
        "communication_style": "friendly",
        "knowledge_areas": ["tech"]
    })
except PersonaValidationError as e:
    print(f"Validation error: {e}")
```

### Data Validation

```python
from agent_personas.validation import (
    validate_json_schema,
    validate_required_fields,
    sanitize_input_data
)

# Schema validation
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"}
    },
    "required": ["name"]
}

validate_json_schema(data, schema)

# Sanitize input
clean_data = sanitize_input_data(user_input)
```

### Business Logic Validation

```python
from agent_personas.validation import (
    validate_persona_consistency,
    validate_trait_compatibility
)

# Validate persona consistency
validate_persona_consistency(persona_data)

# Check trait compatibility
validate_trait_compatibility(traits)
```

## Security Features

### Input Sanitization

```python
from agent_personas.security import (
    sanitize_input,
    validate_safe_content,
    filter_pii
)

# Sanitize user input
clean_text = sanitize_input(
    user_input,
    remove_html=True,
    max_length=5000
)

# Check for unsafe content
try:
    validate_safe_content(text, strict_mode=True)
except PersonaValidationError:
    print("Unsafe content detected")

# Filter PII
filtered_text = filter_pii(text, replacement="[REDACTED]")
```

### Rate Limiting

```python
from agent_personas.security import RateLimiter, rate_limit

# Create rate limiter
limiter = RateLimiter(strategy='token_bucket', default_limit=100)

# Check rate limit
if limiter.is_allowed("user_123", limit=50):
    # Process request
    pass

# Use as decorator
@rate_limit(limit=10, window=60)
def expensive_operation():
    pass
```

## Performance Monitoring

### Tracking Performance

```python
from agent_personas.monitoring import (
    PerformanceMonitor,
    track_execution_time
)

# Start monitoring
monitor = PerformanceMonitor()
monitor.start_monitoring()

# Track function execution
@track_execution_time()
def process_request():
    pass

# Get performance stats
stats = monitor.get_stats()
print(monitor.performance_report())
```

### Memory Monitoring

```python
from agent_personas.monitoring import memory_usage_monitor

@memory_usage_monitor
def memory_intensive_operation():
    pass
```

## Logging

### Basic Logging

```python
from agent_personas import logging_config

# Setup logging
logger = logging_config.setup_logging(
    level="INFO",
    log_file="/var/log/personas.log",
    json_format=True
)

# Use context logging
logger.set_context(persona_id="assistant", user_id="user123")
logger.info("Processing user request")
```

### Performance Logging

```python
from agent_personas.logging_config import log_performance

# Log performance metrics
log_performance("generate_response", 0.543, {"persona_id": "assistant"})
```

## Error Handling

### Exception Hierarchy

```python
from agent_personas.exceptions import (
    PersonaError,
    PersonaValidationError,
    PersonaNotFoundError,
    PersonaConfigError
)

try:
    persona = manager.load_persona("nonexistent")
except PersonaNotFoundError:
    print("Persona not found")
except PersonaConfigError:
    print("Configuration error")
except PersonaError:
    print("General persona error")
```

## Utilities

### Helper Functions

```python
from agent_personas.utils import (
    sanitize_string,
    validate_email,
    deep_merge_dict,
    safe_json_loads
)

# String utilities
clean_name = sanitize_string(raw_name, max_length=100)

# Validation
is_valid = validate_email("user@example.com")

# Dictionary operations
merged = deep_merge_dict(base_config, overrides)

# Safe JSON parsing
data = safe_json_loads(json_string, default={})
```

### Decorators

```python
from agent_personas.utils import retry, timeout, validate_input

# Retry with backoff
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def unreliable_operation():
    pass

# Timeout protection
@timeout(30)
def slow_operation():
    pass

# Input validation
@validate_input(
    name=lambda x: len(x) > 0,
    age=lambda x: x >= 0
)
def create_user(name, age):
    pass
```

## Configuration Files

### Persona Configuration

```json
{
  "name": "Technical Assistant",
  "traits": {
    "personality": {
      "extroversion": 0.6,
      "openness": 0.9,
      "conscientiousness": 0.8,
      "agreeableness": 0.7,
      "neuroticism": 0.2
    },
    "communication_style": "professional",
    "knowledge_areas": [
      "software_engineering",
      "data_science",
      "machine_learning"
    ],
    "response_preferences": {
      "length": "detailed",
      "technical_depth": "high",
      "examples": true
    }
  },
  "version": "1.0",
  "metadata": {
    "created_by": "system",
    "last_updated": "2024-02-13T10:00:00Z"
  }
}
```

### System Configuration

```yaml
personas:
  default_traits:
    personality:
      extroversion: 0.5
      openness: 0.7
    communication_style: "balanced"
    
  validation:
    strict_mode: false
    max_name_length: 100
    
  performance:
    monitoring_enabled: true
    metrics_retention_days: 30
    
  security:
    rate_limiting:
      enabled: true
      default_limit: 1000
      window_seconds: 3600
    
    content_filtering:
      enabled: true
      strict_mode: false
      
  logging:
    level: "INFO"
    format: "json"
    include_context: true
```

## Best Practices

### Persona Design

1. **Consistent Traits**: Ensure personality traits align with communication style
2. **Realistic Knowledge**: Don't claim expertise in too many unrelated areas
3. **Balanced Characteristics**: Avoid extreme trait values unless intentional
4. **Clear Purpose**: Define the persona's intended role and use cases

### Memory Management

1. **Relevance Scoring**: Use importance scores to prioritize memories
2. **Regular Cleanup**: Remove outdated or irrelevant memories
3. **Context Awareness**: Consider conversation context when retrieving memories
4. **Privacy Protection**: Filter sensitive information from memories

### Performance Optimization

1. **Monitor Metrics**: Track response times and resource usage
2. **Cache Frequently**: Cache persona data and computed results
3. **Batch Operations**: Group multiple operations when possible
4. **Lazy Loading**: Load persona components on demand

### Security Considerations

1. **Input Validation**: Always validate and sanitize user input
2. **Rate Limiting**: Implement appropriate rate limits for different operations
3. **Content Filtering**: Screen for inappropriate or harmful content
4. **PII Protection**: Filter personally identifiable information

## Migration Guide

### Upgrading from v1.x

```python
# Old API
from agent_personas import Persona
persona = Persona.load("assistant")

# New API
from agent_personas import PersonaManager
manager = PersonaManager()
persona = manager.load_persona("assistant")
```

### Configuration Changes

- `persona.config` → `agent_personas.config`
- `validate_persona()` → `validate_persona_traits()`
- Error classes moved to `agent_personas.exceptions`

## Troubleshooting

### Common Issues

**PersonaNotFoundError**
- Check persona ID spelling
- Verify persona exists in storage
- Check file permissions

**ValidationError**
- Review trait value ranges (0.0-1.0)
- Ensure required fields are present
- Validate communication style values

**Performance Issues**
- Enable monitoring to identify bottlenecks
- Check memory usage for large personas
- Consider caching frequently accessed data

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose logging
logger = logging_config.setup_logging(level="DEBUG")
```