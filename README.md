# Agent Personas

A comprehensive framework for defining and managing AI agent personalities and behaviors.

## Features

- **Persona Definitions**: Rich personality profiles with traits, preferences, and characteristics
- **Trait Systems**: Hierarchical trait management with inheritance and conflicts
- **Behavior Rules**: Contextual behavior patterns and response rules
- **Conversation Styles**: Adaptive communication patterns and language preferences
- **Emotional States**: Dynamic emotional modeling with state transitions
- **Persona Switching**: Seamless personality transitions and context preservation

## Quick Start

```python
from agent_personas import PersonaManager, Persona

# Create a persona manager
manager = PersonaManager()

# Define a persona
persona = Persona(
    name="Assistant",
    traits={"helpful": 0.9, "formal": 0.7, "curious": 0.8},
    conversation_style="professional",
    emotional_baseline="calm"
)

# Register and activate
manager.register_persona(persona)
manager.activate_persona("Assistant")
```

## Installation

```bash
pip install agent-personas
```

## Documentation

See the `docs/` directory for comprehensive documentation.

## License

MIT License