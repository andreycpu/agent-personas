"""
Business logic validation for persona operations.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from ..exceptions import PersonaValidationError


def validate_persona_consistency(persona: Dict[str, Any]) -> bool:
    """Validate internal consistency of persona definition."""
    traits = persona.get('traits', {})
    
    # Check consistency between personality and communication style
    personality = traits.get('personality', {})
    comm_style = traits.get('communication_style', '')
    
    # If personality indicates introversion but communication style is very outgoing
    if personality.get('extroversion', 0.5) < 0.3 and comm_style in ['enthusiastic', 'bubbly']:
        raise PersonaValidationError("Communication style inconsistent with introverted personality")
    
    # If personality indicates high formality but communication style is casual
    if personality.get('formality', 0.5) > 0.8 and comm_style in ['casual', 'slang']:
        raise PersonaValidationError("Casual communication style inconsistent with formal personality")
    
    # Check knowledge areas against claimed expertise
    knowledge_areas = traits.get('knowledge_areas', [])
    expertise_level = traits.get('expertise_level', 'intermediate')
    
    if len(knowledge_areas) > 10 and expertise_level == 'expert':
        raise PersonaValidationError("Too many knowledge areas for expert-level expertise")
    
    return True


def validate_trait_compatibility(traits: Dict[str, Any]) -> bool:
    """Validate that traits are compatible with each other."""
    personality = traits.get('personality', {})
    
    # Check for contradictory personality traits
    contradictions = [
        ('creativity', 'analytical_thinking'),
        ('spontaneity', 'planning_oriented'),
        ('risk_taking', 'cautious')
    ]
    
    for trait1, trait2 in contradictions:
        if trait1 in personality and trait2 in personality:
            val1 = personality[trait1]
            val2 = personality[trait2]
            
            # If both traits are very high (>0.8), they may be contradictory
            if val1 > 0.8 and val2 > 0.8:
                raise PersonaValidationError(f"Contradictory traits: high {trait1} and high {trait2}")
    
    # Validate trait value ranges
    for trait, value in personality.items():
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise PersonaValidationError(f"Trait '{trait}' must be between 0 and 1, got {value}")
    
    return True


def validate_conversation_flow(conversation: List[Dict[str, Any]]) -> bool:
    """Validate the logical flow of conversation."""
    if not conversation:
        return True
    
    # Check chronological order
    for i in range(1, len(conversation)):
        if conversation[i]['timestamp'] < conversation[i-1]['timestamp']:
            raise PersonaValidationError(f"Message {i} has timestamp earlier than previous message")
    
    # Check role alternation (shouldn't have multiple consecutive messages from same role)
    consecutive_count = 1
    current_role = conversation[0]['role']
    
    for i in range(1, len(conversation)):
        if conversation[i]['role'] == current_role:
            consecutive_count += 1
            if consecutive_count > 3:  # Allow up to 3 consecutive messages from same role
                raise PersonaValidationError(f"Too many consecutive messages from role '{current_role}'")
        else:
            consecutive_count = 1
            current_role = conversation[i]['role']
    
    # Check for appropriate conversation starters/enders
    if conversation[0]['role'] == 'assistant':
        # Assistant shouldn't start conversations unless it's a system prompt
        if 'system' not in conversation[0].get('content', '').lower():
            raise PersonaValidationError("Conversation should typically start with user message")
    
    return True


def validate_memory_coherence(memories: List[Dict[str, Any]], persona_traits: Dict[str, Any]) -> bool:
    """Validate that memories are coherent with persona traits."""
    knowledge_areas = persona_traits.get('knowledge_areas', [])
    personality = persona_traits.get('personality', {})
    
    # Check if memories align with knowledge areas
    memory_topics = set()
    for memory in memories:
        content = memory.get('content', '').lower()
        tags = memory.get('tags', [])
        
        # Extract topics from tags
        memory_topics.update(tag.lower() for tag in tags)
        
        # Simple keyword matching for knowledge areas
        for area in knowledge_areas:
            if area.lower() in content:
                memory_topics.add(area.lower())
    
    # Check if memory topics significantly deviate from knowledge areas
    knowledge_set = set(area.lower() for area in knowledge_areas)
    overlap = memory_topics.intersection(knowledge_set)
    
    if len(knowledge_set) > 0 and len(overlap) / len(knowledge_set) < 0.3:
        raise PersonaValidationError("Memories show little relation to declared knowledge areas")
    
    # Check memory importance distribution
    importances = [memory.get('importance', 0.5) for memory in memories]
    if importances:
        avg_importance = sum(importances) / len(importances)
        
        # If average importance is too high, it's unrealistic
        if avg_importance > 0.8:
            raise PersonaValidationError("Average memory importance too high (suggests poor filtering)")
        
        # If all memories have same importance, it's suspicious
        if len(set(importances)) == 1 and len(memories) > 5:
            raise PersonaValidationError("All memories have identical importance (lacks nuance)")
    
    return True


def validate_context_appropriateness(context: Dict[str, Any], persona_traits: Dict[str, Any]) -> bool:
    """Validate that context is appropriate for the persona."""
    comm_style = persona_traits.get('communication_style', '')
    personality = persona_traits.get('personality', {})
    
    # Check if context suggests inappropriate behavior for the persona
    formality_level = personality.get('formality', 0.5)
    
    if 'inappropriate_content' in context:
        if formality_level > 0.7:  # Highly formal persona
            raise PersonaValidationError("Context contains inappropriate content for formal persona")
    
    if 'technical_complexity' in context:
        knowledge_areas = persona_traits.get('knowledge_areas', [])
        complexity = context['technical_complexity']
        
        # Check if technical complexity matches expertise
        has_technical_knowledge = any(
            area in ['technology', 'science', 'engineering', 'programming']
            for area in knowledge_areas
        )
        
        if complexity > 0.8 and not has_technical_knowledge:
            raise PersonaValidationError("High technical complexity context doesn't match persona knowledge")
    
    return True


def validate_response_appropriateness(response: str, persona_traits: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Validate that a response is appropriate for the persona and context."""
    comm_style = persona_traits.get('communication_style', '')
    personality = persona_traits.get('personality', {})
    
    # Check response length appropriateness
    verbosity = personality.get('verbosity', 0.5)
    response_length = len(response.split())
    
    if verbosity < 0.3 and response_length > 100:
        raise PersonaValidationError("Response too verbose for low-verbosity persona")
    
    if verbosity > 0.8 and response_length < 20:
        raise PersonaValidationError("Response too brief for high-verbosity persona")
    
    # Check formality level
    formality = personality.get('formality', 0.5)
    informal_markers = ['gonna', 'wanna', 'kinda', 'sorta', 'ya', 'ur']
    
    if formality > 0.7 and any(marker in response.lower() for marker in informal_markers):
        raise PersonaValidationError("Informal language used by formal persona")
    
    # Check emotional appropriateness
    enthusiasm = personality.get('enthusiasm', 0.5)
    exclamation_count = response.count('!')
    
    if enthusiasm < 0.3 and exclamation_count > 2:
        raise PersonaValidationError("Too much enthusiasm for low-enthusiasm persona")
    
    return True