#!/usr/bin/env python3
"""
Advanced behavior example showing behavior rules, emotional responses, and dynamic adaptation.
"""

from agent_personas import PersonaManager, Persona
from agent_personas.behaviors import BehaviorEngine, BehaviorRule, BehaviorCondition, BehaviorAction, ContextManager
from agent_personas.emotions import EmotionEngine, EmotionalResponseGenerator
from agent_personas.conversation import ToneAdapter
from agent_personas.traits import TraitConflictResolver


def create_personas() -> dict:
    """Create a set of personas with distinct behavioral profiles."""
    
    personas = {}
    
    # Empathetic Counselor
    counselor = Persona(
        name="EmpathicCounselor",
        description="A caring and supportive counselor persona",
        traits={
            "empathy": 0.95,
            "patience": 0.9,
            "supportiveness": 0.9,
            "formality": 0.3,
            "directness": 0.4
        },
        conversation_style="empathetic",
        emotional_baseline="calm"
    )
    personas["counselor"] = counselor
    
    # Energetic Motivator  
    motivator = Persona(
        name="EnergeticMotivator",
        description="An enthusiastic and inspiring motivator",
        traits={
            "enthusiasm": 0.9,
            "confidence": 0.85,
            "supportiveness": 0.8,
            "playfulness": 0.7,
            "directness": 0.8
        },
        conversation_style="enthusiastic",
        emotional_baseline="excited"
    )
    personas["motivator"] = motivator
    
    # Analytical Expert
    analyst = Persona(
        name="AnalyticalExpert", 
        description="A logical and systematic problem-solver",
        traits={
            "precision": 0.9,
            "formality": 0.8,
            "directness": 0.9,
            "patience": 0.7,
            "confidence": 0.8
        },
        conversation_style="professional",
        emotional_baseline="neutral"
    )
    personas["analyst"] = analyst
    
    return personas


def setup_behavior_rules(engine):
    """Set up behavior rules for different scenarios."""
    
    # Rule: Switch to empathetic mode when user is sad
    sad_user_rule = BehaviorRule(
        name="comfort_sad_user",
        description="Become more empathetic when user expresses sadness",
        priority=10
    )
    
    # Condition: User emotion is sad
    sad_condition = BehaviorCondition(
        condition_type="user_input",
        parameters={
            "pattern": "sad|depressed|down|upset|crying",
            "match_type": "regex"
        },
        description="User expresses sadness"
    )
    
    # Actions: Increase empathy, change tone
    empathy_action = BehaviorAction(
        action_type="adjust_trait",
        parameters={
            "trait": "empathy",
            "adjustment": 0.2,
            "type": "relative"
        },
        description="Increase empathy"
    )
    
    tone_action = BehaviorAction(
        action_type="set_response_style",
        parameters={"style": "comforting"},
        description="Switch to comforting tone"
    )
    
    sad_user_rule.add_condition(sad_condition)
    sad_user_rule.add_action(empathy_action)
    sad_user_rule.add_action(tone_action)
    
    engine.add_rule(sad_user_rule)
    
    # Rule: Increase enthusiasm for positive interactions
    positive_rule = BehaviorRule(
        name="match_enthusiasm",
        description="Match user's positive energy",
        priority=8
    )
    
    positive_condition = BehaviorCondition(
        condition_type="user_input",
        parameters={
            "pattern": "excited|awesome|amazing|fantastic|great|wonderful",
            "match_type": "regex"
        }
    )
    
    enthusiasm_action = BehaviorAction(
        action_type="adjust_trait", 
        parameters={
            "trait": "enthusiasm",
            "adjustment": 0.3,
            "type": "relative"
        }
    )
    
    positive_rule.add_condition(positive_condition)
    positive_rule.add_action(enthusiasm_action)
    
    engine.add_rule(positive_rule)
    
    # Rule: Be more direct in technical discussions
    technical_rule = BehaviorRule(
        name="technical_directness",
        description="Be more direct and precise in technical contexts",
        priority=7
    )
    
    tech_condition = BehaviorCondition(
        condition_type="context_value",
        parameters={
            "key": "topic_type",
            "value": "technical",
            "operator": "=="
        }
    )
    
    directness_action = BehaviorAction(
        action_type="adjust_trait",
        parameters={
            "trait": "directness",
            "adjustment": 0.4,
            "type": "relative"
        }
    )
    
    technical_rule.add_condition(tech_condition)
    technical_rule.add_action(directness_action)
    
    engine.add_rule(technical_rule)


def demonstrate_behavior_engine():
    """Demonstrate the behavior engine with dynamic rule processing."""
    
    print("\n🎯 Behavior Engine Demonstration")
    print("-" * 50)
    
    # Create behavior engine
    engine = BehaviorEngine()
    
    # Set up rules
    setup_behavior_rules(engine)
    
    print(f"Loaded {len(engine.list_rules())} behavior rules")
    
    # Test scenarios
    test_scenarios = [
        {
            "user_input": "I'm feeling really sad today",
            "context": {"user_emotion": "sad"},
            "description": "Sad user scenario"
        },
        {
            "user_input": "This is amazing! I'm so excited!",
            "context": {"user_emotion": "excited"},
            "description": "Enthusiastic user scenario"
        },
        {
            "user_input": "Can you help me debug this algorithm?",
            "context": {"topic_type": "technical", "user_emotion": "neutral"},
            "description": "Technical discussion scenario"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nScenario: {scenario['description']}")
        print(f"User input: '{scenario['user_input']}'")
        
        # Process the scenario
        context = {
            "user_input": scenario["user_input"],
            **scenario["context"]
        }
        
        modifications = engine.process_context(context)
        
        print("Behavior modifications:")
        for key, value in modifications.items():
            print(f"  {key}: {value}")
            
        # Show which rules fired
        recent_execution = engine.get_execution_history(limit=1)
        if recent_execution:
            executed_rules = recent_execution[0]["executed_rules"]
            rule_names = [rule["rule_name"] for rule in executed_rules]
            print(f"Rules triggered: {rule_names}")


def demonstrate_emotional_responses():
    """Demonstrate emotional response generation."""
    
    print("\n💭 Emotional Response Generation")
    print("-" * 50)
    
    emotion_engine = EmotionEngine()
    response_generator = EmotionalResponseGenerator()
    
    test_inputs = [
        ("Thank you so much for helping me!", "User expressing gratitude"),
        ("I'm struggling with this problem...", "User expressing difficulty"),
        ("I just got a promotion!", "User celebrating success"),
        ("I don't understand this at all", "User expressing confusion"),
        ("You're not being very helpful", "User expressing frustration")
    ]
    
    for user_input, description in test_inputs:
        print(f"\nScenario: {description}")
        print(f"User: '{user_input}'")
        
        # Process emotional context
        emotional_state = emotion_engine.process_input(user_input)
        emotional_context = emotion_engine.get_emotional_context()
        
        print(f"Detected mood: {emotional_context['current_mood']}")
        print(f"Emotional valence: {emotional_context['valence']:.2f}")
        
        # Generate appropriate response
        response = response_generator.generate_contextual_response(
            emotional_state=emotional_state,
            user_input=user_input,
            conversation_context=emotional_context
        )
        
        print(f"Generated response: '{response}'")


def demonstrate_tone_adaptation():
    """Demonstrate tone adaptation based on context."""
    
    print("\n🎨 Tone Adaptation Demonstration")
    print("-" * 50)
    
    tone_adapter = ToneAdapter()
    
    base_response = "I can help you with that problem."
    
    tone_profiles = [
        ("friendly", "Warm and approachable interaction"),
        ("professional", "Business or formal context"),
        ("empathetic", "User needs emotional support"),
        ("enthusiastic", "Positive and energetic situation"),
        ("calm_confident", "Reassuring and stable presence")
    ]
    
    print(f"Base response: '{base_response}'")
    print("\nTone adaptations:")
    
    for profile_name, description in tone_profiles:
        adapted_response = tone_adapter.apply_profile(
            text=base_response,
            profile_name=profile_name,
            intensity_multiplier=0.8
        )
        
        print(f"\n{profile_name.upper()}:")
        print(f"  Context: {description}")
        print(f"  Adapted: '{adapted_response}'")
        
        # Analyze the change
        analysis = tone_adapter.analyze_current_tone(adapted_response)
        top_tones = sorted(analysis.items(), key=lambda x: x[1], reverse=True)[:2]
        tone_description = ", ".join([f"{tone.value}: {score:.1f}" for tone, score in top_tones])
        print(f"  Analysis: {tone_description}")


def demonstrate_trait_conflicts():
    """Demonstrate trait conflict resolution."""
    
    print("\n⚖️  Trait Conflict Resolution")
    print("-" * 50)
    
    resolver = TraitConflictResolver()
    
    # Create a conflicting trait profile
    conflicting_traits = {
        "formality": 0.9,
        "playfulness": 0.8,  # Conflicts with high formality
        "directness": 0.9,
        "empathy": 0.9,  # Might conflict with high directness
        "enthusiasm": 0.8
    }
    
    print("Original conflicting traits:")
    for trait, value in conflicting_traits.items():
        print(f"  {trait}: {value}")
    
    # Define some conflicts
    mutual_exclusions = [
        {"formality", "playfulness"},  # Can't be both very formal and very playful
    ]
    
    dependencies = {
        "empathy": ["patience"]  # Empathy requires patience
    }
    
    # Detect conflicts
    conflicts = resolver.detect_conflicts(
        trait_values=conflicting_traits,
        mutual_exclusions=mutual_exclusions,
        dependencies=dependencies
    )
    
    print(f"\nDetected {len(conflicts)} conflicts:")
    for conflict in conflicts:
        print(f"  {conflict.description} (severity: {conflict.severity:.2f})")
    
    # Resolve conflicts
    if conflicts:
        resolved_traits = resolver.resolve_all_conflicts(
            trait_values=conflicting_traits,
            conflicts=conflicts
        )
        
        print("\nResolved traits:")
        for trait, value in resolved_traits.items():
            original = conflicting_traits.get(trait, 0)
            change = value - original
            change_str = f"({change:+.2f})" if abs(change) > 0.01 else ""
            print(f"  {trait}: {value:.2f} {change_str}")


def demonstrate_context_management():
    """Demonstrate context management across conversation turns."""
    
    print("\n🔄 Context Management")
    print("-" * 50)
    
    context_manager = ContextManager()
    
    # Start a conversation session
    context_manager.start_session("demo_session")
    print("Started conversation session")
    
    # Simulate conversation turns
    conversation_turns = [
        {
            "user": "Hi, I need help with my project",
            "agent": "I'd be happy to help! What kind of project are you working on?",
            "context": {"topic": "project_help", "user_emotion": "neutral"}
        },
        {
            "user": "It's a web development project, but I'm stuck on the backend",
            "agent": "I can definitely help with backend development. What specific issue are you facing?", 
            "context": {"topic": "web_development", "subtopic": "backend", "user_emotion": "frustrated"}
        },
        {
            "user": "The database queries are running too slowly",
            "agent": "Performance optimization is crucial. Let's look at query optimization strategies.",
            "context": {"topic": "database_optimization", "technical_level": "intermediate"}
        }
    ]
    
    for i, turn in enumerate(conversation_turns, 1):
        context_manager.start_turn()
        
        print(f"\nTurn {i}:")
        print(f"User: {turn['user']}")
        
        # Set context for this turn
        for key, value in turn["context"].items():
            context_manager.set_context(key, value)
        
        # Add to conversation history
        context_manager.add_to_history(
            user_input=turn["user"],
            agent_response=turn["agent"],
            context_snapshot=turn["context"]
        )
        
        print(f"Agent: {turn['agent']}")
        
        # Show context evolution
        current_context = context_manager.get_all_context()
        print(f"Context: {current_context}")
    
    # Analyze conversation patterns
    print("\nConversation Analysis:")
    patterns = context_manager.analyze_conversation_patterns()
    for key, value in patterns.items():
        print(f"  {key}: {value}")


def main():
    """Run the advanced behavior demonstration."""
    
    print("🚀 Agent Personas Framework - Advanced Behavior Examples")
    print("=" * 70)
    
    # Create personas
    personas = create_personas()
    manager = PersonaManager()
    
    for persona in personas.values():
        manager.register_persona(persona)
    
    # Activate the empathetic counselor initially
    manager.activate_persona("EmpathicCounselor")
    print(f"Active persona: {manager.active_persona_name}")
    
    # Run demonstrations
    demonstrate_behavior_engine()
    demonstrate_emotional_responses()
    demonstrate_tone_adaptation()
    demonstrate_trait_conflicts()
    demonstrate_context_management()
    
    print("\n" + "=" * 70)
    print("✨ Advanced behavior examples completed!")
    print("\nAdvanced features demonstrated:")
    print("  • Dynamic behavior rule processing")
    print("  • Contextual emotional response generation")
    print("  • Adaptive tone modification")
    print("  • Intelligent trait conflict resolution")
    print("  • Sophisticated context management")
    print("  • Multi-turn conversation tracking")


if __name__ == "__main__":
    main()