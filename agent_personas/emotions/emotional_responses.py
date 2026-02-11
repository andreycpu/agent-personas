"""
Emotional response generator for creating contextually appropriate emotional expressions.
"""

from typing import Dict, List, Any, Optional, Tuple
import random
from dataclasses import dataclass, field
from enum import Enum

from .emotion_model import EmotionalState, BasicEmotion


class ResponseCategory(Enum):
    """Categories of emotional responses."""
    EMPATHETIC = "empathetic"
    REACTIVE = "reactive"
    SUPPORTIVE = "supportive"
    CELEBRATORY = "celebratory"
    COMFORTING = "comforting"
    ENCOURAGING = "encouraging"
    APOLOGETIC = "apologetic"


@dataclass
class EmotionalResponseTemplate:
    """Template for generating emotional responses."""
    category: ResponseCategory
    emotion_triggers: List[BasicEmotion]
    intensity_range: Tuple[float, float] = (0.0, 1.0)
    
    # Response components
    phrases: List[str] = field(default_factory=list)
    tone_modifiers: List[str] = field(default_factory=list)
    emotional_expressions: List[str] = field(default_factory=list)
    
    # Conditional modifiers
    high_intensity_additions: List[str] = field(default_factory=list)
    low_intensity_additions: List[str] = field(default_factory=list)
    
    # Context-based variations
    formal_variants: List[str] = field(default_factory=list)
    casual_variants: List[str] = field(default_factory=list)
    
    def generate_response(
        self, 
        emotional_state: EmotionalState,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate a response based on the emotional state and context."""
        if context is None:
            context = {}
            
        # Check if this template applies
        dominant_emotion, intensity = emotional_state.get_dominant_emotion()
        
        if dominant_emotion not in self.emotion_triggers:
            return ""
            
        if not (self.intensity_range[0] <= intensity <= self.intensity_range[1]):
            return ""
            
        # Select base phrase
        base_phrases = self.phrases.copy()
        
        # Add formality variants if appropriate
        formality = context.get("formality", 0.0)
        if formality > 0.5 and self.formal_variants:
            base_phrases.extend(self.formal_variants)
        elif formality < -0.5 and self.casual_variants:
            base_phrases.extend(self.casual_variants)
            
        if not base_phrases:
            return ""
            
        selected_phrase = random.choice(base_phrases)
        
        # Add intensity modifiers
        if intensity > 0.7 and self.high_intensity_additions:
            addition = random.choice(self.high_intensity_additions)
            selected_phrase = f"{selected_phrase} {addition}"
        elif intensity < 0.3 and self.low_intensity_additions:
            addition = random.choice(self.low_intensity_additions)
            selected_phrase = f"{addition} {selected_phrase}"
            
        # Add emotional expressions based on arousal
        if emotional_state.arousal > 0.5 and self.emotional_expressions:
            expression = random.choice(self.emotional_expressions)
            selected_phrase = f"{selected_phrase} {expression}"
            
        return selected_phrase.strip()


class EmotionalResponseGenerator:
    """
    Generates appropriate emotional responses based on current emotional state.
    """
    
    def __init__(self):
        self._templates: Dict[str, EmotionalResponseTemplate] = {}
        self._response_history: List[Dict[str, Any]] = []
        
        # Load default templates
        self._load_default_templates()
        
    def add_template(self, name: str, template: EmotionalResponseTemplate) -> None:
        """Add a response template."""
        self._templates[name] = template
        
    def remove_template(self, name: str) -> bool:
        """Remove a response template."""
        if name in self._templates:
            del self._templates[name]
            return True
        return False
        
    def generate_response(
        self, 
        emotional_state: EmotionalState,
        context: Dict[str, Any] = None,
        response_category: Optional[ResponseCategory] = None
    ) -> str:
        """
        Generate an appropriate emotional response.
        
        Args:
            emotional_state: Current emotional state
            context: Context information
            response_category: Optional specific category to use
            
        Returns:
            Generated emotional response
        """
        if context is None:
            context = {}
            
        applicable_templates = []
        
        # Filter templates by category if specified
        if response_category:
            applicable_templates = [
                template for template in self._templates.values()
                if template.category == response_category
            ]
        else:
            applicable_templates = list(self._templates.values())
            
        # Generate responses from applicable templates
        possible_responses = []
        for template in applicable_templates:
            response = template.generate_response(emotional_state, context)
            if response:
                possible_responses.append((response, template))
                
        if not possible_responses:
            return self._generate_fallback_response(emotional_state)
            
        # Select best response (for now, random selection)
        selected_response, used_template = random.choice(possible_responses)
        
        # Record response
        self._record_response(emotional_state, context, selected_response, used_template.category)
        
        return selected_response
        
    def generate_contextual_response(
        self, 
        emotional_state: EmotionalState,
        user_input: str,
        conversation_context: Dict[str, Any] = None
    ) -> str:
        """
        Generate a response considering user input and conversation context.
        
        Args:
            emotional_state: Current emotional state
            user_input: What the user said
            conversation_context: Context from conversation
            
        Returns:
            Contextually appropriate response
        """
        if conversation_context is None:
            conversation_context = {}
            
        # Analyze user input for emotional cues
        user_emotion_cues = self._analyze_user_emotion(user_input)
        
        # Determine appropriate response category
        response_category = self._determine_response_category(
            emotional_state, user_emotion_cues, conversation_context
        )
        
        # Generate response
        return self.generate_response(
            emotional_state, 
            {**conversation_context, **user_emotion_cues},
            response_category
        )
        
    def _analyze_user_emotion(self, user_input: str) -> Dict[str, Any]:
        """Analyze user input for emotional cues."""
        user_input_lower = user_input.lower()
        
        emotion_indicators = {
            "positive": ["happy", "great", "awesome", "wonderful", "excited", "love"],
            "negative": ["sad", "angry", "frustrated", "disappointed", "hate", "terrible"],
            "anxious": ["worried", "nervous", "scared", "concerned", "anxious"],
            "grateful": ["thank", "appreciate", "grateful", "thanks"],
            "confused": ["confused", "don't understand", "unclear", "what do you mean"]
        }
        
        detected_emotions = []
        for emotion, indicators in emotion_indicators.items():
            if any(indicator in user_input_lower for indicator in indicators):
                detected_emotions.append(emotion)
                
        # Detect intensity indicators
        intensity_high = any(word in user_input_lower for word in ["very", "extremely", "really", "so", "!!"])
        intensity_low = any(word in user_input_lower for word in ["a bit", "slightly", "somewhat", "kind of"])
        
        return {
            "user_emotions": detected_emotions,
            "user_intensity": "high" if intensity_high else "low" if intensity_low else "medium",
            "user_input_length": len(user_input),
            "question_asked": "?" in user_input
        }
        
    def _determine_response_category(
        self, 
        emotional_state: EmotionalState,
        user_cues: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ResponseCategory:
        """Determine the most appropriate response category."""
        user_emotions = user_cues.get("user_emotions", [])
        
        # Empathetic responses for negative user emotions
        if any(emotion in ["negative", "anxious", "confused"] for emotion in user_emotions):
            return ResponseCategory.EMPATHETIC
            
        # Celebratory responses for positive user emotions
        if "positive" in user_emotions:
            return ResponseCategory.CELEBRATORY
            
        # Grateful responses for gratitude
        if "grateful" in user_emotions:
            return ResponseCategory.SUPPORTIVE
            
        # Default based on agent's emotional state
        dominant_emotion, intensity = emotional_state.get_dominant_emotion()
        
        if dominant_emotion == BasicEmotion.JOY and intensity > 0.5:
            return ResponseCategory.CELEBRATORY
        elif dominant_emotion == BasicEmotion.SADNESS:
            return ResponseCategory.COMFORTING
        elif dominant_emotion == BasicEmotion.TRUST and intensity > 0.5:
            return ResponseCategory.SUPPORTIVE
        else:
            return ResponseCategory.EMPATHETIC
            
    def _generate_fallback_response(self, emotional_state: EmotionalState) -> str:
        """Generate a fallback response when no templates match."""
        mood_label = emotional_state.get_mood_label()
        
        fallback_responses = {
            "neutral": "I understand.",
            "positive": "That sounds good!",
            "negative": "I can see this is difficult.",
            "excited": "That's exciting!",
            "calm": "I appreciate you sharing that.",
            "sad": "I'm here to help.",
            "angry": "I understand your frustration."
        }
        
        # Try to find a match for the mood
        for mood_key, response in fallback_responses.items():
            if mood_key in mood_label.lower():
                return response
                
        return "I understand."
        
    def _record_response(
        self, 
        emotional_state: EmotionalState,
        context: Dict[str, Any],
        response: str,
        category: ResponseCategory
    ) -> None:
        """Record a generated response for analysis."""
        record = {
            "timestamp": emotional_state.timestamp.isoformat(),
            "emotional_state": emotional_state.get_mood_label(),
            "valence": emotional_state.valence,
            "arousal": emotional_state.arousal,
            "intensity": emotional_state.intensity,
            "context": context,
            "generated_response": response,
            "response_category": category.value
        }
        
        self._response_history.append(record)
        
        # Keep history manageable
        if len(self._response_history) > 100:
            self._response_history = self._response_history[-50:]
            
    def get_response_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in generated responses."""
        if not self._response_history:
            return {"message": "No response history available"}
            
        # Count response categories
        category_counts = {}
        for record in self._response_history:
            category = record["response_category"]
            category_counts[category] = category_counts.get(category, 0) + 1
            
        # Analyze response effectiveness by valence change
        effectiveness_analysis = {}
        for i in range(1, len(self._response_history)):
            prev_valence = self._response_history[i-1]["valence"]
            curr_valence = self._response_history[i]["valence"]
            valence_change = curr_valence - prev_valence
            
            category = self._response_history[i-1]["response_category"]
            if category not in effectiveness_analysis:
                effectiveness_analysis[category] = []
            effectiveness_analysis[category].append(valence_change)
            
        # Calculate average valence change per category
        avg_effectiveness = {}
        for category, changes in effectiveness_analysis.items():
            avg_effectiveness[category] = sum(changes) / len(changes) if changes else 0
            
        return {
            "total_responses": len(self._response_history),
            "category_distribution": category_counts,
            "most_used_category": max(category_counts.items(), key=lambda x: x[1]) if category_counts else None,
            "response_effectiveness": avg_effectiveness,
            "most_effective_category": max(avg_effectiveness.items(), key=lambda x: x[1]) if avg_effectiveness else None
        }
        
    def suggest_response_improvements(self) -> List[str]:
        """Suggest improvements to response generation."""
        patterns = self.get_response_patterns()
        suggestions = []
        
        if "category_distribution" in patterns:
            categories = patterns["category_distribution"]
            total_responses = sum(categories.values())
            
            # Check for over-reliance on certain categories
            for category, count in categories.items():
                ratio = count / total_responses
                if ratio > 0.5:
                    suggestions.append(f"Consider diversifying beyond {category} responses ({ratio:.1%} usage)")
                    
        if "response_effectiveness" in patterns:
            effectiveness = patterns["response_effectiveness"]
            
            # Identify ineffective categories
            for category, avg_change in effectiveness.items():
                if avg_change < -0.1:
                    suggestions.append(f"Review {category} responses - they may be having negative impact")
                    
        if not suggestions:
            suggestions.append("Response patterns look healthy - continue current approach")
            
        return suggestions
        
    def _load_default_templates(self) -> None:
        """Load default response templates."""
        
        # Empathetic responses
        empathetic_template = EmotionalResponseTemplate(
            category=ResponseCategory.EMPATHETIC,
            emotion_triggers=[BasicEmotion.TRUST, BasicEmotion.SADNESS],
            phrases=[
                "I understand how you're feeling.",
                "That must be difficult for you.",
                "I can see this is important to you.",
                "Your feelings are completely valid."
            ],
            high_intensity_additions=[
                "This clearly means a lot to you.",
                "I can really feel your emotion about this."
            ],
            low_intensity_additions=[
                "I can sense that",
                "It seems like"
            ],
            emotional_expressions=["💙", "🤗"],
            formal_variants=[
                "I empathize with your situation.",
                "I recognize the significance of this matter for you."
            ],
            casual_variants=[
                "I totally get it.",
                "I hear you."
            ]
        )
        
        # Celebratory responses
        celebratory_template = EmotionalResponseTemplate(
            category=ResponseCategory.CELEBRATORY,
            emotion_triggers=[BasicEmotion.JOY, BasicEmotion.ANTICIPATION],
            phrases=[
                "That's wonderful!",
                "How exciting!",
                "That's fantastic news!",
                "I'm so happy for you!"
            ],
            high_intensity_additions=[
                "This is absolutely amazing!",
                "What incredible news!"
            ],
            emotional_expressions=["🎉", "😊", "🌟"],
            formal_variants=[
                "Congratulations on this achievement.",
                "This is indeed excellent news."
            ],
            casual_variants=[
                "Awesome!",
                "That rocks!",
                "So cool!"
            ]
        )
        
        # Supportive responses
        supportive_template = EmotionalResponseTemplate(
            category=ResponseCategory.SUPPORTIVE,
            emotion_triggers=[BasicEmotion.TRUST, BasicEmotion.JOY],
            phrases=[
                "I'm here to help you.",
                "You're doing great.",
                "I believe in you.",
                "We can work through this together."
            ],
            high_intensity_additions=[
                "You've got this!",
                "I have complete confidence in you."
            ],
            low_intensity_additions=[
                "I'm here if you need support.",
                "You're on the right track."
            ],
            emotional_expressions=["💪", "🤝"],
            formal_variants=[
                "I am available to assist you.",
                "You have my full support."
            ],
            casual_variants=[
                "I've got your back!",
                "You can do this!"
            ]
        )
        
        # Comforting responses
        comforting_template = EmotionalResponseTemplate(
            category=ResponseCategory.COMFORTING,
            emotion_triggers=[BasicEmotion.SADNESS, BasicEmotion.FEAR],
            phrases=[
                "It's okay to feel this way.",
                "Things will get better.",
                "You're not alone in this.",
                "Take your time."
            ],
            high_intensity_additions=[
                "I'm here with you through this.",
                "This pain won't last forever."
            ],
            emotional_expressions=["🤗", "💚"],
            formal_variants=[
                "Please know that support is available.",
                "These feelings are temporary."
            ],
            casual_variants=[
                "Hang in there.",
                "It's gonna be okay."
            ]
        )
        
        # Add templates
        self.add_template("empathetic_basic", empathetic_template)
        self.add_template("celebratory_basic", celebratory_template)
        self.add_template("supportive_basic", supportive_template)
        self.add_template("comforting_basic", comforting_template)