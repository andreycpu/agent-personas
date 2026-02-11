#!/usr/bin/env python3
"""
Basic usage example for the Agent Personas framework.
"""

from agent_personas import PersonaManager, Persona
from agent_personas.traits import TraitManager
from agent_personas.conversation import ConversationStyleManager
from agent_personas.emotions import EmotionEngine


def main():
    """Demonstrate basic usage of the Agent Personas framework."""
    
    print("🎭 Agent Personas Framework - Basic Usage Example")
    print("=" * 60)
    
    # 1. Create a persona manager
    print("\n1. Creating Persona Manager...")
    manager = PersonaManager()
    
    # 2. Create some personas with different traits
    print("\n2. Creating Personas...")
    
    # Helpful Assistant
    helpful_assistant = Persona(
        name="HelpfulAssistant",
        description="A friendly and knowledgeable assistant",
        traits={
            "helpfulness": 0.9,
            "formality": 0.6,
            "empathy": 0.8,
            "patience": 0.9
        },
        conversation_style="friendly",
        emotional_baseline="calm"
    )
    
    # Technical Expert
    technical_expert = Persona(
        name="TechnicalExpert", 
        description="A knowledgeable technical specialist",
        traits={
            "expertise": 0.95,
            "formality": 0.8,
            "directness": 0.8,
            "precision": 0.9
        },
        conversation_style="professional",
        emotional_baseline="confident"
    )
    
    # Creative Companion
    creative_companion = Persona(
        name="CreativeCompanion",
        description="An imaginative and inspiring creative partner",
        traits={
            "creativity": 0.95,
            "enthusiasm": 0.8,
            "openness": 0.9,
            "playfulness": 0.7
        },
        conversation_style="enthusiastic",
        emotional_baseline="excited"
    )
    
    # Register personas
    personas = [helpful_assistant, technical_expert, creative_companion]
    for persona in personas:
        manager.register_persona(persona)
        print(f"   ✓ Registered: {persona.name}")
    
    # 3. Demonstrate persona activation
    print("\n3. Activating Personas...")
    
    print(f"   Available personas: {manager.list_personas()}")
    
    # Activate the helpful assistant
    success = manager.activate_persona("HelpfulAssistant")
    print(f"   ✓ Activated: {manager.active_persona_name} (success: {success})")
    
    # 4. Demonstrate trait analysis
    print("\n4. Analyzing Traits...")
    trait_manager = TraitManager()
    
    current_persona = manager.active_persona
    if current_persona:
        analysis = trait_manager.analyze_trait_profile(current_persona.traits)
        print(f"   Dominant traits: {analysis['dominant_traits']}")
        print(f"   Trait types: {list(analysis['trait_types'].keys())}")
        
        # Validate traits
        is_valid, errors = trait_manager.validate_trait_values(current_persona.traits)
        print(f"   Trait validation: {'✓ Valid' if is_valid else '✗ Errors: ' + str(errors)}")
    
    # 5. Demonstrate conversation styles
    print("\n5. Testing Conversation Styles...")
    style_manager = ConversationStyleManager()
    
    # Get current style
    current_style = style_manager.get_current_style()
    if current_style:
        print(f"   Current style: {current_style.name}")
        print(f"   Style description: {current_style.get_description_text()}")
    
    # Adapt style to context
    context = {
        "user_emotion": "excited",
        "topic_complexity": "high",
        "formality_preference": "medium"
    }
    adapted_style = style_manager.adapt_current_style(context)
    print(f"   Adapted style: {adapted_style.get_description_text()}")
    
    # 6. Demonstrate emotion processing
    print("\n6. Processing Emotions...")
    emotion_engine = EmotionEngine()
    
    # Process some emotional inputs
    test_inputs = [
        "I'm really excited about this project!",
        "I'm feeling a bit frustrated with this problem.",
        "Thank you so much for your help!"
    ]
    
    for input_text in test_inputs:
        emotional_state = emotion_engine.process_input(input_text)
        print(f"   Input: '{input_text}'")
        print(f"   Emotional response: {emotional_state.get_mood_label()}")
        
        # Get emotional context
        context = emotion_engine.get_emotional_context()
        print(f"   Emotional context: {context['current_mood']} (valence: {context['valence']:.2f})")
    
    # 7. Demonstrate persona switching
    print("\n7. Switching Personas...")
    
    # Switch to technical expert for a technical question
    print("   Switching to TechnicalExpert for technical discussion...")
    success = manager.switch_persona("TechnicalExpert")
    print(f"   ✓ Switched to: {manager.active_persona_name}")
    
    # Show how traits changed
    new_persona = manager.active_persona
    if new_persona:
        print(f"   New traits: {new_persona.traits}")
        
    # Switch to creative companion for creative work
    print("   Switching to CreativeCompanion for creative session...")
    success = manager.switch_persona("CreativeCompanion")
    print(f"   ✓ Switched to: {manager.active_persona_name}")
    
    # 8. Show persona history
    print("\n8. Persona History...")
    history = manager.get_persona_history()
    print(f"   Persona switches: {history}")
    
    # 9. Get manager status
    print("\n9. Manager Status...")
    status = manager.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✨ Basic usage example completed!")
    print("\nKey features demonstrated:")
    print("  • Persona creation and registration")
    print("  • Trait analysis and validation")
    print("  • Conversation style adaptation")
    print("  • Emotion processing and mood tracking")
    print("  • Dynamic persona switching")
    print("  • Context-aware behavior")


if __name__ == "__main__":
    main()