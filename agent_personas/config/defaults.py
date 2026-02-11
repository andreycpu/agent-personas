"""
Default configurations and presets for the persona framework.
"""

from typing import Dict, Any, List
from ..traits.trait import Trait, TraitType


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration for the persona framework.
    
    Returns:
        Default configuration dictionary
    """
    return {
        # Core framework settings
        "framework": {
            "version": "0.1.0",
            "name": "Agent Personas Framework",
            "auto_save": True,
            "max_history_size": 100
        },
        
        # Persona management
        "personas": {
            "default_persona": None,
            "allow_empty_personas": False,
            "require_description": False,
            "min_traits": 1,
            "max_traits": 20
        },
        
        # Trait system
        "traits": {
            "validation_enabled": True,
            "auto_resolve_conflicts": True,
            "default_trait_value": 0.5,
            "allow_extreme_values": True,
            "trait_bounds": {
                "min": 0.0,
                "max": 1.0
            }
        },
        
        # Behavior system
        "behaviors": {
            "rules_enabled": True,
            "max_rules": 50,
            "execution_timeout": 1.0,
            "allow_custom_conditions": True,
            "priority_range": [-100, 100]
        },
        
        # Emotion system
        "emotions": {
            "processing_enabled": True,
            "decay_rate": 0.1,
            "sensitivity": 0.5,
            "auto_decay": True,
            "decay_interval_minutes": 5,
            "max_intensity": 1.0
        },
        
        # Conversation system
        "conversation": {
            "adaptive_style": True,
            "context_memory_size": 20,
            "auto_style_adaptation": True,
            "max_conversation_length": 1000,
            "response_timeout": 30.0
        },
        
        # Switching system
        "switching": {
            "enabled": True,
            "validation": True,
            "preserve_context": True,
            "max_switches_per_hour": 20,
            "cooldown_seconds": 10
        },
        
        # Performance settings
        "performance": {
            "cache_size": 100,
            "async_processing": False,
            "batch_size": 10,
            "memory_limit_mb": 500,
            "timeout_seconds": 30
        },
        
        # Logging configuration
        "logging": {
            "level": "INFO",
            "to_file": False,
            "file_path": "./logs/agent_personas.log",
            "structured": False,
            "max_file_size_mb": 10,
            "backup_count": 5
        },
        
        # Storage settings
        "storage": {
            "data_directory": "./persona_data",
            "backup_enabled": True,
            "backup_frequency_hours": 24,
            "compression": True,
            "format": "json"
        },
        
        # Security settings
        "security": {
            "validate_inputs": True,
            "sanitize_outputs": True,
            "max_input_length": 10000,
            "allowed_file_types": [".json", ".yaml", ".yml"]
        }
    }


def get_default_traits() -> List[Trait]:
    """
    Get default trait definitions for the framework.
    
    Returns:
        List of default Trait objects
    """
    default_traits = [
        # Personality traits (Big Five)
        Trait(
            name="extraversion",
            description="Tendency to be outgoing, energetic, and assertive",
            trait_type=TraitType.PERSONALITY,
            default_value=0.5,
            metadata={"category": "big_five", "opposite": "introversion"}
        ),
        
        Trait(
            name="agreeableness", 
            description="Tendency to be cooperative, trusting, and empathetic",
            trait_type=TraitType.PERSONALITY,
            default_value=0.6,
            metadata={"category": "big_five", "opposite": "antagonism"}
        ),
        
        Trait(
            name="conscientiousness",
            description="Tendency to be organized, responsible, and goal-directed",
            trait_type=TraitType.PERSONALITY,
            default_value=0.7,
            metadata={"category": "big_five", "opposite": "lack_of_direction"}
        ),
        
        Trait(
            name="neuroticism",
            description="Tendency to experience negative emotions and stress",
            trait_type=TraitType.PERSONALITY,
            default_value=0.3,
            metadata={"category": "big_five", "opposite": "emotional_stability"}
        ),
        
        Trait(
            name="openness",
            description="Openness to experience, creativity, and intellectual curiosity",
            trait_type=TraitType.PERSONALITY,
            default_value=0.6,
            metadata={"category": "big_five", "opposite": "closed_mindedness"}
        ),
        
        # Behavioral traits
        Trait(
            name="assertiveness",
            description="Confidence in expressing opinions and standing up for oneself",
            trait_type=TraitType.BEHAVIORAL,
            default_value=0.5,
            metadata={"category": "interpersonal"}
        ),
        
        Trait(
            name="patience",
            description="Ability to remain calm and tolerant in difficult situations",
            trait_type=TraitType.BEHAVIORAL,
            default_value=0.6,
            metadata={"category": "emotional_regulation"}
        ),
        
        Trait(
            name="curiosity",
            description="Desire to learn, explore, and understand new things",
            trait_type=TraitType.BEHAVIORAL,
            default_value=0.7,
            metadata={"category": "learning"}
        ),
        
        Trait(
            name="risk_tolerance",
            description="Willingness to take risks and try uncertain approaches",
            trait_type=TraitType.BEHAVIORAL,
            default_value=0.4,
            metadata={"category": "decision_making"}
        ),
        
        # Communication traits
        Trait(
            name="verbosity",
            description="Tendency to use many words and provide detailed explanations",
            trait_type=TraitType.COMMUNICATION,
            default_value=0.5,
            metadata={"category": "style"}
        ),
        
        Trait(
            name="formality",
            description="Preference for formal language and structured communication",
            trait_type=TraitType.COMMUNICATION,
            default_value=0.5,
            metadata={"category": "style"}
        ),
        
        Trait(
            name="humor",
            description="Use of humor, jokes, and playful language in communication",
            trait_type=TraitType.COMMUNICATION,
            default_value=0.4,
            metadata={"category": "style"}
        ),
        
        Trait(
            name="directness",
            description="Tendency to communicate clearly and directly without ambiguity",
            trait_type=TraitType.COMMUNICATION,
            default_value=0.6,
            metadata={"category": "clarity"}
        ),
        
        # Emotional traits
        Trait(
            name="empathy",
            description="Ability to understand and share the feelings of others",
            trait_type=TraitType.EMOTIONAL,
            default_value=0.7,
            metadata={"category": "social_emotional"}
        ),
        
        Trait(
            name="optimism",
            description="Tendency to expect positive outcomes and see the bright side",
            trait_type=TraitType.EMOTIONAL,
            default_value=0.6,
            metadata={"category": "outlook"}
        ),
        
        Trait(
            name="emotional_stability",
            description="Ability to remain emotionally balanced under pressure",
            trait_type=TraitType.EMOTIONAL,
            default_value=0.6,
            metadata={"category": "regulation"}
        ),
        
        # Cognitive traits
        Trait(
            name="analytical_thinking",
            description="Preference for logical, systematic problem-solving approaches",
            trait_type=TraitType.COGNITIVE,
            default_value=0.6,
            metadata={"category": "thinking_style"}
        ),
        
        Trait(
            name="creativity",
            description="Ability to generate novel ideas and innovative solutions", 
            trait_type=TraitType.COGNITIVE,
            default_value=0.5,
            metadata={"category": "thinking_style"}
        ),
        
        Trait(
            name="attention_to_detail",
            description="Focus on accuracy, precision, and thoroughness",
            trait_type=TraitType.COGNITIVE,
            default_value=0.6,
            metadata={"category": "processing"}
        ),
        
        # Social traits
        Trait(
            name="sociability",
            description="Enjoyment of social interaction and group activities",
            trait_type=TraitType.SOCIAL,
            default_value=0.5,
            metadata={"category": "interpersonal"}
        ),
        
        Trait(
            name="leadership",
            description="Natural tendency to guide, influence, and organize others",
            trait_type=TraitType.SOCIAL,
            default_value=0.4,
            metadata={"category": "influence"}
        ),
        
        Trait(
            name="supportiveness",
            description="Willingness to help, encourage, and assist others",
            trait_type=TraitType.SOCIAL,
            default_value=0.7,
            metadata={"category": "helping"}
        )
    ]
    
    return default_traits


def get_default_conversation_styles() -> Dict[str, Dict[str, Any]]:
    """
    Get default conversation style definitions.
    
    Returns:
        Dictionary of conversation style configurations
    """
    return {
        "professional": {
            "name": "Professional",
            "description": "Formal, structured, and business-appropriate communication",
            "formality": 0.8,
            "directness": 0.7,
            "verbosity": 0.6,
            "humor": 0.2,
            "empathy": 0.5,
            "vocabulary_level": "advanced",
            "sentence_structure": "complex"
        },
        
        "friendly": {
            "name": "Friendly", 
            "description": "Warm, approachable, and conversational communication",
            "formality": 0.3,
            "directness": 0.5,
            "verbosity": 0.5,
            "humor": 0.6,
            "empathy": 0.8,
            "vocabulary_level": "standard",
            "sentence_structure": "mixed"
        },
        
        "casual": {
            "name": "Casual",
            "description": "Relaxed, informal, and easy-going communication",
            "formality": 0.2,
            "directness": 0.4,
            "verbosity": 0.4,
            "humor": 0.7,
            "empathy": 0.6,
            "vocabulary_level": "simple",
            "sentence_structure": "simple"
        },
        
        "empathetic": {
            "name": "Empathetic",
            "description": "Understanding, supportive, and emotionally aware communication",
            "formality": 0.4,
            "directness": 0.3,
            "verbosity": 0.6,
            "humor": 0.3,
            "empathy": 0.9,
            "vocabulary_level": "standard",
            "sentence_structure": "mixed"
        },
        
        "technical": {
            "name": "Technical",
            "description": "Precise, detailed, and technically accurate communication",
            "formality": 0.7,
            "directness": 0.9,
            "verbosity": 0.7,
            "humor": 0.1,
            "empathy": 0.4,
            "vocabulary_level": "technical",
            "sentence_structure": "complex"
        },
        
        "enthusiastic": {
            "name": "Enthusiastic",
            "description": "Energetic, positive, and motivational communication",
            "formality": 0.3,
            "directness": 0.6,
            "verbosity": 0.6,
            "humor": 0.8,
            "empathy": 0.7,
            "vocabulary_level": "standard",
            "sentence_structure": "mixed"
        }
    }


def get_default_emotional_baselines() -> Dict[str, Dict[str, float]]:
    """
    Get default emotional baseline configurations.
    
    Returns:
        Dictionary of emotional baseline definitions
    """
    return {
        "calm": {
            "joy": 0.2,
            "sadness": 0.1,
            "anger": 0.1,
            "fear": 0.1,
            "trust": 0.6,
            "anticipation": 0.3,
            "valence": 0.1,
            "arousal": -0.2,
            "dominance": 0.2
        },
        
        "excited": {
            "joy": 0.6,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "trust": 0.5,
            "anticipation": 0.7,
            "valence": 0.6,
            "arousal": 0.7,
            "dominance": 0.4
        },
        
        "confident": {
            "joy": 0.4,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "trust": 0.8,
            "anticipation": 0.5,
            "valence": 0.4,
            "arousal": 0.1,
            "dominance": 0.7
        },
        
        "compassionate": {
            "joy": 0.3,
            "sadness": 0.2,
            "anger": 0.0,
            "fear": 0.1,
            "trust": 0.9,
            "anticipation": 0.3,
            "valence": 0.2,
            "arousal": -0.1,
            "dominance": 0.1
        },
        
        "focused": {
            "joy": 0.2,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "trust": 0.5,
            "anticipation": 0.6,
            "valence": 0.0,
            "arousal": 0.0,
            "dominance": 0.5
        },
        
        "neutral": {
            "joy": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "trust": 0.5,
            "anticipation": 0.0,
            "valence": 0.0,
            "arousal": 0.0,
            "dominance": 0.0
        }
    }


def get_default_behavior_rules() -> List[Dict[str, Any]]:
    """
    Get default behavior rule configurations.
    
    Returns:
        List of default behavior rule definitions
    """
    return [
        {
            "name": "greet_user",
            "description": "Respond warmly to greetings",
            "conditions": [
                {
                    "type": "user_input",
                    "pattern": "hello|hi|hey|good morning|good evening",
                    "match_type": "regex"
                }
            ],
            "actions": [
                {
                    "type": "adjust_trait",
                    "trait": "friendliness",
                    "adjustment": 0.1
                },
                {
                    "type": "set_response_style",
                    "style": "friendly"
                }
            ],
            "priority": 5
        },
        
        {
            "name": "handle_frustration",
            "description": "Be more patient when user shows frustration",
            "conditions": [
                {
                    "type": "user_input",
                    "pattern": "frustrat|annoyed|irritated|stuck",
                    "match_type": "regex"
                }
            ],
            "actions": [
                {
                    "type": "adjust_trait", 
                    "trait": "patience",
                    "adjustment": 0.2
                },
                {
                    "type": "adjust_trait",
                    "trait": "empathy", 
                    "adjustment": 0.2
                }
            ],
            "priority": 8
        },
        
        {
            "name": "technical_mode",
            "description": "Adapt to technical discussions",
            "conditions": [
                {
                    "type": "context_value",
                    "key": "topic_type",
                    "value": "technical"
                }
            ],
            "actions": [
                {
                    "type": "adjust_trait",
                    "trait": "precision",
                    "adjustment": 0.3
                },
                {
                    "type": "set_response_style",
                    "style": "technical"
                }
            ],
            "priority": 7
        },
        
        {
            "name": "celebration_response",
            "description": "Match user's excitement and celebration",
            "conditions": [
                {
                    "type": "user_input",
                    "pattern": "amazing|fantastic|awesome|great|wonderful|excited",
                    "match_type": "regex"
                }
            ],
            "actions": [
                {
                    "type": "adjust_trait",
                    "trait": "enthusiasm",
                    "adjustment": 0.3
                },
                {
                    "type": "change_emotion",
                    "emotion": "joy",
                    "intensity": 0.4
                }
            ],
            "priority": 6
        }
    ]


def get_framework_metadata() -> Dict[str, Any]:
    """
    Get metadata about the framework itself.
    
    Returns:
        Framework metadata dictionary
    """
    return {
        "name": "Agent Personas Framework",
        "version": "0.1.0", 
        "description": "A comprehensive framework for defining and managing AI agent personalities and behaviors",
        "author": "Agent Personas Contributors",
        "license": "MIT",
        "repository": "https://github.com/andreycpu/agent-personas",
        "documentation": "https://agent-personas.readthedocs.io/",
        
        "capabilities": [
            "persona definition and management",
            "trait-based personality modeling",
            "behavioral rule processing",
            "emotional state modeling",
            "conversation style adaptation",
            "dynamic persona switching"
        ],
        
        "supported_formats": ["json", "yaml", "pickle"],
        "minimum_python_version": "3.8",
        "dependencies": [],
        
        "modules": {
            "core": "Persona definition and management",
            "traits": "Personality trait system",
            "behaviors": "Behavioral rule engine", 
            "conversation": "Conversation style management",
            "emotions": "Emotional modeling and processing",
            "switching": "Persona switching system",
            "utils": "Utility functions and helpers",
            "config": "Configuration management"
        }
    }