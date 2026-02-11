"""
Command-line interface for the Agent Personas framework.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .core.persona import Persona
from .core.manager import PersonaManager
from .traits.trait_manager import TraitManager
from .conversation.style_manager import ConversationStyleManager
from .emotions.emotion_engine import EmotionEngine


def load_persona_templates(filepath: str) -> Dict[str, Any]:
    """Load persona templates from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Template file '{filepath}' not found")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in template file '{filepath}'")
        return {}


def create_persona_from_template(template_data: Dict[str, Any]) -> Persona:
    """Create a Persona instance from template data."""
    return Persona(
        name=template_data["name"],
        description=template_data["description"],
        traits=template_data.get("traits", {}),
        conversation_style=template_data.get("conversation_style", "neutral"),
        emotional_baseline=template_data.get("emotional_baseline", "calm"),
        metadata={
            "use_cases": template_data.get("use_cases", []),
            "personality_notes": template_data.get("personality_notes", "")
        }
    )


def cmd_list_templates(args):
    """List available persona templates."""
    templates_path = args.templates or "examples/persona_templates.json"
    
    templates_data = load_persona_templates(templates_path)
    if not templates_data:
        return
        
    persona_templates = templates_data.get("persona_templates", {})
    
    print("Available Persona Templates:")
    print("=" * 50)
    
    for template_id, template_data in persona_templates.items():
        print(f"\n{template_id}:")
        print(f"  Name: {template_data['name']}")
        print(f"  Description: {template_data['description']}")
        print(f"  Use cases: {', '.join(template_data.get('use_cases', []))}")


def cmd_show_template(args):
    """Show detailed information about a specific template."""
    templates_path = args.templates or "examples/persona_templates.json"
    
    templates_data = load_persona_templates(templates_path)
    if not templates_data:
        return
        
    persona_templates = templates_data.get("persona_templates", {})
    
    if args.template_id not in persona_templates:
        print(f"Error: Template '{args.template_id}' not found")
        return
        
    template_data = persona_templates[args.template_id]
    
    print(f"Template: {args.template_id}")
    print("=" * 50)
    print(f"Name: {template_data['name']}")
    print(f"Description: {template_data['description']}")
    print(f"Conversation Style: {template_data.get('conversation_style', 'neutral')}")
    print(f"Emotional Baseline: {template_data.get('emotional_baseline', 'calm')}")
    
    print("\nTraits:")
    for trait, value in template_data.get("traits", {}).items():
        print(f"  {trait}: {value}")
        
    print(f"\nUse Cases: {', '.join(template_data.get('use_cases', []))}")
    print(f"Notes: {template_data.get('personality_notes', '')}")


def cmd_create_persona(args):
    """Create a persona from a template."""
    templates_path = args.templates or "examples/persona_templates.json"
    
    templates_data = load_persona_templates(templates_path)
    if not templates_data:
        return
        
    persona_templates = templates_data.get("persona_templates", {})
    
    if args.template_id not in persona_templates:
        print(f"Error: Template '{args.template_id}' not found")
        return
        
    template_data = persona_templates[args.template_id]
    
    # Create persona
    persona = create_persona_from_template(template_data)
    
    # Save to file
    output_path = args.output or f"{persona.name.lower()}.json"
    
    with open(output_path, 'w') as f:
        json.dump(persona.to_dict(), f, indent=2)
        
    print(f"Created persona '{persona.name}' and saved to '{output_path}'")


def cmd_validate_persona(args):
    """Validate a persona file."""
    try:
        with open(args.persona_file, 'r') as f:
            persona_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Persona file '{args.persona_file}' not found")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in persona file '{args.persona_file}'")
        return
        
    # Create persona and validate
    try:
        persona = Persona.from_dict(persona_data)
        print(f"✓ Persona '{persona.name}' is valid")
        
        # Validate traits
        trait_manager = TraitManager()
        is_valid, errors = trait_manager.validate_trait_values(persona.traits)
        
        if is_valid:
            print("✓ Traits are valid")
        else:
            print("✗ Trait validation errors:")
            for error in errors:
                print(f"  - {error}")
                
        # Analyze trait profile
        analysis = trait_manager.analyze_trait_profile(persona.traits)
        print(f"Dominant traits: {analysis.get('dominant_traits', [])}")
        print(f"Trait conflicts: {len(analysis.get('conflicts', []))}")
        
    except Exception as e:
        print(f"✗ Persona validation failed: {e}")


def cmd_demo(args):
    """Run a demo of the framework."""
    print("🎭 Agent Personas Framework Demo")
    print("=" * 40)
    
    # Create a persona manager
    manager = PersonaManager()
    
    # Load and create personas from templates
    templates_path = args.templates or "examples/persona_templates.json"
    templates_data = load_persona_templates(templates_path)
    
    if not templates_data:
        print("Using built-in demo personas...")
        # Create a simple demo persona
        demo_persona = Persona(
            name="DemoAssistant",
            description="A helpful demo assistant",
            traits={"helpfulness": 0.9, "friendliness": 0.8},
            conversation_style="friendly"
        )
        manager.register_persona(demo_persona)
    else:
        # Create personas from templates
        persona_templates = templates_data.get("persona_templates", {})
        
        for template_id, template_data in list(persona_templates.items())[:3]:  # Load first 3
            persona = create_persona_from_template(template_data)
            manager.register_persona(persona)
            print(f"✓ Loaded persona: {persona.name}")
    
    # Activate first persona
    personas = manager.list_personas()
    if personas:
        manager.activate_persona(personas[0])
        print(f"✓ Activated persona: {manager.active_persona_name}")
        
        # Show persona details
        active_persona = manager.active_persona
        print(f"Description: {active_persona.description}")
        print(f"Traits: {active_persona.traits}")
        print(f"Style: {active_persona.conversation_style}")
        
    # Test emotion processing
    print("\nTesting emotion processing...")
    emotion_engine = EmotionEngine()
    
    test_inputs = [
        "I'm excited about this project!",
        "I'm feeling frustrated with this problem.",
    ]
    
    for user_input in test_inputs:
        state = emotion_engine.process_input(user_input)
        context = emotion_engine.get_emotional_context()
        print(f"Input: '{user_input}' -> Mood: {context['current_mood']}")
        
    print("\n✨ Demo completed!")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Personas Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent-personas list                          # List available templates
  agent-personas show helpful_assistant        # Show template details
  agent-personas create helpful_assistant      # Create persona from template
  agent-personas validate my_persona.json     # Validate a persona file
  agent-personas demo                          # Run framework demo
        """
    )
    
    # Global options
    parser.add_argument(
        "--templates",
        help="Path to persona templates JSON file (default: examples/persona_templates.json)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List templates command
    list_parser = subparsers.add_parser("list", help="List available persona templates")
    list_parser.set_defaults(func=cmd_list_templates)
    
    # Show template command
    show_parser = subparsers.add_parser("show", help="Show details of a specific template")
    show_parser.add_argument("template_id", help="ID of the template to show")
    show_parser.set_defaults(func=cmd_show_template)
    
    # Create persona command
    create_parser = subparsers.add_parser("create", help="Create a persona from a template")
    create_parser.add_argument("template_id", help="ID of the template to use")
    create_parser.add_argument("-o", "--output", help="Output file path")
    create_parser.set_defaults(func=cmd_create_persona)
    
    # Validate persona command
    validate_parser = subparsers.add_parser("validate", help="Validate a persona file")
    validate_parser.add_argument("persona_file", help="Path to persona JSON file")
    validate_parser.set_defaults(func=cmd_validate_persona)
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run a framework demo")
    demo_parser.set_defaults(func=cmd_demo)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()