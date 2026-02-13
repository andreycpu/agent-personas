# Agent Personas - Quick Start Guide

Welcome to Agent Personas! This guide will get you up and running in minutes.

## Installation

```bash
pip install agent-personas
```

Or for development:
```bash
git clone https://github.com/andreycpu/agent-personas.git
cd agent-personas
pip install -e .
```

## Quick Examples

### 1. Create a Persona from Template

```python
from agent_personas import create_persona_from_template

# Create a technical assistant
persona = create_persona_from_template(
    "technical_assistant",
    assistant_name="CodeBot",
    specialization="web_development"
)

print(f"Created persona: {persona['name']}")
print(f"Traits: {persona['traits']['communication_style']}")
```

### 2. Interactive Persona Creation

```python
from agent_personas import interactive_config_builder

# Start interactive builder
config = interactive_config_builder()

# Save to file
import json
with open("my_persona.json", "w") as f:
    json.dump(config, f, indent=2)
```

### 3. Using the CLI

```bash
# List available templates
personas templates list

# Create from template
personas create --template friendly_helper --output helper.json

# Interactive creation
personas create --interactive --output custom.json

# Validate configuration
personas validate my_persona.json
```

### 4. Load and Use Existing Persona

```python
from agent_personas import PersonaManager
import json

# Load persona configuration
with open("examples/personas.json") as f:
    personas = json.load(f)

manager = PersonaManager()
tech_persona = manager.load_persona_from_dict(personas["technical_assistant"])

print(f"Loaded: {tech_persona.name}")
print(f"Knowledge areas: {tech_persona.knowledge_areas}")
```

### 5. Validation and Security

```python
from agent_personas.validation import validate_persona_traits
from agent_personas.security import sanitize_input

# Validate persona configuration
traits = {
    "personality": {"extroversion": 0.7},
    "communication_style": "friendly", 
    "knowledge_areas": ["general"]
}

try:
    validate_persona_traits(traits)
    print("✅ Traits are valid")
except Exception as e:
    print(f"❌ Validation failed: {e}")

# Sanitize user input
user_input = "<script>alert('xss')</script>Hello world!"
clean_input = sanitize_input(user_input, remove_html=True)
print(f"Clean input: {clean_input}")
```

### 6. Performance Monitoring

```python
from agent_personas.monitoring import PerformanceMonitor, track_execution_time

# Start monitoring
monitor = PerformanceMonitor()
monitor.start_monitoring()

# Track function performance
@track_execution_time("process_request")
def process_request(data):
    # Your processing logic
    return f"Processed: {data}"

# Use the function
result = process_request("test data")

# Get performance report
print(monitor.performance_report())
```

### 7. Async Operations

```python
from agent_personas.async_utils import AsyncBatch, run_async

# Batch async processing
batch = AsyncBatch(max_concurrent=5)

# Add tasks
for i in range(10):
    batch.add_task(lambda x: x * 2, i)

# Wait for results
results = batch.get_successful_results()
print(f"Results: {results}")
```

## Available Templates

Run `personas templates list` to see all available templates:

- **technical_assistant**: For programming and engineering tasks
- **friendly_helper**: Warm, approachable general assistant
- **academic_researcher**: Rigorous academic work
- **customer_service**: Professional customer support
- **creative_assistant**: Artistic and creative tasks

## Configuration Structure

A persona configuration has this basic structure:

```json
{
  "name": "My Persona",
  "traits": {
    "personality": {
      "extroversion": 0.7,
      "openness": 0.8,
      "conscientiousness": 0.6,
      "agreeableness": 0.8,
      "neuroticism": 0.2
    },
    "communication_style": "friendly",
    "knowledge_areas": ["general", "technology"]
  },
  "version": "1.0"
}
```

### Personality Traits (0.0 - 1.0)

- **extroversion**: Outgoing (1.0) vs Reserved (0.0)
- **openness**: Innovative (1.0) vs Conventional (0.0) 
- **conscientiousness**: Organized (1.0) vs Spontaneous (0.0)
- **agreeableness**: Cooperative (1.0) vs Competitive (0.0)
- **neuroticism**: Anxious (1.0) vs Stable (0.0)

### Communication Styles

- `formal`: Professional, structured communication
- `casual`: Relaxed, informal tone
- `friendly`: Warm, approachable style
- `professional`: Business-appropriate
- `technical`: Precise, technical language

## Common Patterns

### Creating Domain-Specific Personas

```python
# Healthcare assistant
healthcare_persona = create_persona_from_template(
    "friendly_helper",
    helper_name="HealthBot",
    specialty_area="health_wellness"
)

# Educational tutor
tutor_persona = create_persona_from_template(
    "academic_researcher", 
    researcher_name="Professor Smith",
    research_field="mathematics",
    citation_format="MLA"
)
```

### Customizing Existing Templates

```python
from agent_personas.templates import template_registry

# Get base template
template = template_registry.get("technical_assistant")

# Set custom variables
template.set_variables({
    "assistant_name": "DevOps Expert",
    "specialization": "cloud_infrastructure"
})

# Render with additional customizations
config = template.render({
    "expertise_level": "expert",
    "focus_area": "kubernetes"
})
```

### Validation Workflow

```python
from agent_personas.validation import (
    validate_persona_name,
    validate_persona_traits,
    validate_persona_consistency
)

def validate_complete_persona(config):
    """Complete validation workflow."""
    try:
        # Basic validations
        validate_persona_name(config["name"])
        validate_persona_traits(config["traits"])
        
        # Advanced consistency check
        validate_persona_consistency(config)
        
        return True, "Persona is valid"
        
    except Exception as e:
        return False, str(e)

# Usage
is_valid, message = validate_complete_persona(persona_config)
print(f"Validation result: {message}")
```

## Next Steps

1. **Explore Examples**: Check out `examples/personas.json` for more configurations
2. **Read Documentation**: See `docs/API.md` for complete API reference
3. **Join Community**: Contribute templates and improvements
4. **Performance Tuning**: Use monitoring tools to optimize your personas
5. **Security**: Always validate and sanitize inputs in production

## Troubleshooting

### Common Issues

**Template not found**
```bash
# List available templates
personas templates list

# Check template info
personas templates info template_name
```

**Validation errors**
```python
# Use strict validation for detailed errors
from agent_personas.validation import validate_persona_traits

try:
    validate_persona_traits(traits)
except PersonaValidationError as e:
    print(f"Detailed error: {e}")
```

**Performance issues**
```python
# Enable monitoring
from agent_personas.monitoring import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_monitoring()

# Your code here

print(monitor.get_system_stats())
```

### Getting Help

- Check the [API Documentation](API.md)
- Look at [example configurations](../examples/personas.json)
- Use the CLI help: `personas --help`
- Enable debug logging for detailed information

## Advanced Features

### Custom Templates

```python
from agent_personas.templates import PersonaTemplate, template_registry

# Create custom template
custom_template = PersonaTemplate(
    name="my_custom_template",
    description="Custom domain-specific template",
    template_data={
        "name": "{bot_name}",
        "traits": {
            "personality": {"custom_trait": "{trait_value}"},
            "communication_style": "{style}",
            "knowledge_areas": ["{domain}", "general"]
        }
    }
)

# Register it
template_registry.register(custom_template)

# Use it
config = create_persona_from_template(
    "my_custom_template",
    bot_name="DomainBot",
    trait_value=0.8,
    style="professional",
    domain="specialized_field"
)
```

### Async Persona Operations

```python
from agent_personas.async_utils import AsyncContext

async def process_multiple_personas():
    with AsyncContext(max_workers=5) as ctx:
        # Submit multiple persona operations
        tasks = []
        for template in ["technical_assistant", "friendly_helper"]:
            task_id = ctx.submit(create_persona_from_template, template)
            tasks.append(task_id)
        
        # Collect results
        results = []
        for task_id in tasks:
            result = ctx.get_result(task_id)
            if result.success:
                results.append(result.result)
        
        return results
```

### Performance Benchmarking

```python
from agent_personas.benchmarking import Benchmarker

def benchmark_persona_creation():
    benchmarker = Benchmarker()
    
    # Benchmark template creation
    result = benchmarker.benchmark(
        create_persona_from_template,
        runs=100,
        args=("technical_assistant",),
        kwargs={"assistant_name": "Test"}
    )
    
    print(f"Template creation: {result.mean_time:.4f}s avg")
    return result

# Run benchmark
benchmark_result = benchmark_persona_creation()
```

Happy persona building! 🤖✨