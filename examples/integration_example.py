#!/usr/bin/env python3
"""
Integration example showing how to combine multiple framework components.
"""

import asyncio
from agent_personas import PersonaManager, Persona
from agent_personas.traits import TraitManager
from agent_personas.emotions import EmotionEngine
from agent_personas.behaviors import BehaviorEngine, BehaviorRule, BehaviorCondition, BehaviorAction
from agent_personas.conversation import ConversationStyleManager, ToneAdapter
from agent_personas.switching import SwitchManager, SwitchReason
from agent_personas.utils.logging import get_persona_logger


async def main():
    """Demonstrate integrated framework usage."""
    
    # Setup logging
    logger = get_persona_logger("integration_demo", json_format=True)
    logger.info("Starting integration demonstration")
    
    print("🚀 Agent Personas Framework - Integration Demo")
    print("=" * 60)
    
    # 1. Setup core managers
    print("\n1. Setting up core managers...")
    persona_manager = PersonaManager()
    trait_manager = TraitManager()
    emotion_engine = EmotionEngine()
    behavior_engine = BehaviorEngine()
    style_manager = ConversationStyleManager()
    tone_adapter = ToneAdapter()
    
    # 2. Create diverse personas
    print("\n2. Creating diverse personas...")
    
    therapist = Persona(
        name="TherapistBot",
        description="A compassionate AI therapist specialized in emotional support",
        traits={
            "empathy": 0.95,
            "patience": 0.9,
            "supportiveness": 0.9,
            "formality": 0.6,
            "directness": 0.4
        },
        conversation_style="empathetic",
        emotional_baseline="compassionate"
    )
    
    coach = Persona(
        name="MotivationalCoach", 
        description="An energetic coach focused on achievement and growth",
        traits={
            "enthusiasm": 0.9,
            "confidence": 0.85,
            "supportiveness": 0.8,
            "directness": 0.8,
            "optimism": 0.9
        },
        conversation_style="enthusiastic",
        emotional_baseline="excited"
    )
    
    analyst = Persona(
        name="DataAnalyst",
        description="A logical analyst focused on facts and systematic thinking",
        traits={
            "analytical_thinking": 0.95,
            "precision": 0.9,
            "objectivity": 0.85,
            "formality": 0.8,
            "directness": 0.9
        },
        conversation_style="technical",
        emotional_baseline="focused"
    )
    
    # Register personas
    for persona in [therapist, coach, analyst]:
        persona_manager.register_persona(persona)
        print(f"   ✓ Registered: {persona.name}")
    
    # 3. Setup behavior rules
    print("\n3. Setting up adaptive behavior rules...")
    
    # Rule: Switch to therapist when user is sad
    sad_user_rule = BehaviorRule(
        name="comfort_sad_user",
        description="Switch to therapist persona when user expresses sadness"
    )
    
    sad_condition = BehaviorCondition(
        condition_type="user_input",
        parameters={"pattern": "sad|depressed|down|upset", "match_type": "regex"}
    )
    
    switch_action = BehaviorAction(
        action_type="trigger_behavior",
        parameters={"behavior": "switch_to_therapist"}
    )
    
    sad_user_rule.add_condition(sad_condition)
    sad_user_rule.add_action(switch_action)
    behavior_engine.add_rule(sad_user_rule)
    
    # Rule: Switch to coach for motivation
    motivation_rule = BehaviorRule(
        name="motivate_user",
        description="Switch to coach when user needs motivation"
    )
    
    motivation_condition = BehaviorCondition(
        condition_type="user_input", 
        parameters={"pattern": "motivated|goals|achieve|success", "match_type": "regex"}
    )
    
    motivation_action = BehaviorAction(
        action_type="trigger_behavior",
        parameters={"behavior": "switch_to_coach"}
    )
    
    motivation_rule.add_condition(motivation_condition)
    motivation_rule.add_action(motivation_action)
    behavior_engine.add_rule(motivation_rule)
    
    print(f"   ✓ Added {len(behavior_engine.list_rules())} behavior rules")
    
    # 4. Setup switching manager
    print("\n4. Configuring persona switching...")
    switch_manager = SwitchManager(persona_manager)
    
    def handle_switch(switch_context):
        logger.info(f"Persona switched: {switch_context.from_persona} -> {switch_context.to_persona}")
        print(f"   🔄 Switched: {switch_context.from_persona} -> {switch_context.to_persona}")
    
    switch_manager.add_switch_callback(handle_switch)
    
    # 5. Simulate conversation scenarios
    print("\n5. Simulating conversation scenarios...")
    
    scenarios = [
        {
            "input": "I'm feeling really sad today, everything seems hopeless",
            "expected_persona": "TherapistBot",
            "description": "User expressing sadness"
        },
        {
            "input": "I want to achieve my goals and be more motivated",
            "expected_persona": "MotivationalCoach", 
            "description": "User seeking motivation"
        },
        {
            "input": "Can you help me analyze this data set?",
            "expected_persona": "DataAnalyst",
            "description": "User requesting analysis"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n   Scenario {i}: {scenario['description']}")
        print(f"   User: '{scenario['input']}'")
        
        # Process with behavior engine
        context = {
            "user_input": scenario["input"],
            "conversation_turn_count": i,
            "user_emotion": "neutral"
        }
        
        modifications = behavior_engine.process_context(context)
        print(f"   Behavior modifications: {list(modifications.keys())}")
        
        # Process emotions
        emotional_state = emotion_engine.process_input(scenario["input"])
        emotional_context = emotion_engine.get_emotional_context()
        print(f"   Detected mood: {emotional_context['current_mood']}")
        
        # Determine appropriate persona (simplified logic)
        if "sad" in scenario["input"].lower() or "depressed" in scenario["input"].lower():
            target_persona = "TherapistBot"
        elif "motivat" in scenario["input"].lower() or "goal" in scenario["input"].lower():
            target_persona = "MotivationalCoach"
        elif "analyz" in scenario["input"].lower() or "data" in scenario["input"].lower():
            target_persona = "DataAnalyst"
        else:
            target_persona = None
        
        # Switch persona if needed
        if target_persona and persona_manager.active_persona_name != target_persona:
            success, message = switch_manager.switch_persona(
                target_persona,
                reason=SwitchReason.CONTEXT_CHANGE,
                notes=f"Switched for scenario: {scenario['description']}"
            )
            
            if success:
                print(f"   ✓ Switched to: {target_persona}")
            else:
                print(f"   ✗ Switch failed: {message}")
        
        # Generate contextual response
        current_persona = persona_manager.active_persona
        if current_persona:
            # Adapt conversation style
            adapted_style = style_manager.adapt_current_style(context)
            print(f"   Style adapted: {adapted_style.get_description_text()}")
            
            # Apply tone
            base_response = f"As {current_persona.name}, I understand your situation."
            
            if current_persona.name == "TherapistBot":
                tone_profile = "empathetic"
            elif current_persona.name == "MotivationalCoach":
                tone_profile = "enthusiastic"
            else:
                tone_profile = "professional"
            
            adapted_response = tone_adapter.apply_profile(base_response, tone_profile)
            print(f"   Agent Response: '{adapted_response}'")
        
        print()
    
    # 6. Analytics and insights
    print("\n6. Generating analytics and insights...")
    
    # Persona usage statistics
    switch_patterns = switch_manager.analyze_switch_patterns(days_back=1)
    print(f"   Persona switches: {switch_patterns.get('total_switches', 0)}")
    print(f"   Most used persona: {switch_patterns.get('most_used_persona', 'None')}")
    
    # Emotional patterns
    emotion_patterns = emotion_engine.analyze_emotional_patterns(days_back=1)
    print(f"   Emotional events: {emotion_patterns.get('total_emotional_events', 0)}")
    print(f"   Average valence: {emotion_patterns.get('average_valence', 0):.2f}")
    
    # Behavior rule effectiveness  
    behavior_stats = behavior_engine.get_statistics()
    print(f"   Behavior rules: {behavior_stats['enabled_rules']}/{behavior_stats['total_rules']} enabled")
    
    # 7. Cleanup and summary
    print("\n7. Integration demo completed!")
    print("=" * 60)
    print("✨ Successfully demonstrated:")
    print("  • Multi-persona management")
    print("  • Adaptive behavior rules") 
    print("  • Emotional state processing")
    print("  • Dynamic persona switching")
    print("  • Conversation style adaptation")
    print("  • Contextual tone adjustment")
    print("  • Integrated analytics")


if __name__ == "__main__":
    asyncio.run(main())