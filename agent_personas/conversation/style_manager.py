"""
Conversation style management for adaptive communication patterns.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class CommunicationAxis(Enum):
    """Different axes of communication style."""
    FORMALITY = "formality"          # Formal <-> Casual
    VERBOSITY = "verbosity"          # Concise <-> Verbose
    DIRECTNESS = "directness"        # Direct <-> Indirect
    EMOTIVENESS = "emotiveness"      # Neutral <-> Emotional
    SUPPORTIVENESS = "supportiveness" # Critical <-> Supportive
    PLAYFULNESS = "playfulness"      # Serious <-> Playful


@dataclass
class ConversationStyle:
    """
    Represents a conversation style with multiple communication dimensions.
    """
    name: str
    description: str
    
    # Communication axes (values from -1.0 to 1.0)
    formality: float = 0.0        # -1=casual, +1=formal
    verbosity: float = 0.0        # -1=concise, +1=verbose
    directness: float = 0.0       # -1=indirect, +1=direct
    emotiveness: float = 0.0      # -1=neutral, +1=emotional
    supportiveness: float = 0.0   # -1=critical, +1=supportive
    playfulness: float = 0.0      # -1=serious, +1=playful
    
    # Style-specific patterns
    greeting_patterns: List[str] = field(default_factory=list)
    response_patterns: List[str] = field(default_factory=list)
    question_patterns: List[str] = field(default_factory=list)
    closing_patterns: List[str] = field(default_factory=list)
    
    # Language preferences
    vocabulary_level: str = "standard"  # simple, standard, advanced, technical
    sentence_structure: str = "mixed"   # simple, compound, complex, mixed
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_axis_value(self, axis: CommunicationAxis) -> float:
        """Get the value for a specific communication axis."""
        axis_map = {
            CommunicationAxis.FORMALITY: self.formality,
            CommunicationAxis.VERBOSITY: self.verbosity,
            CommunicationAxis.DIRECTNESS: self.directness,
            CommunicationAxis.EMOTIVENESS: self.emotiveness,
            CommunicationAxis.SUPPORTIVENESS: self.supportiveness,
            CommunicationAxis.PLAYFULNESS: self.playfulness
        }
        return axis_map.get(axis, 0.0)
        
    def set_axis_value(self, axis: CommunicationAxis, value: float) -> None:
        """Set the value for a specific communication axis."""
        value = max(-1.0, min(1.0, value))  # Clamp to valid range
        
        if axis == CommunicationAxis.FORMALITY:
            self.formality = value
        elif axis == CommunicationAxis.VERBOSITY:
            self.verbosity = value
        elif axis == CommunicationAxis.DIRECTNESS:
            self.directness = value
        elif axis == CommunicationAxis.EMOTIVENESS:
            self.emotiveness = value
        elif axis == CommunicationAxis.SUPPORTIVENESS:
            self.supportiveness = value
        elif axis == CommunicationAxis.PLAYFULNESS:
            self.playfulness = value
            
    def calculate_similarity(self, other: "ConversationStyle") -> float:
        """
        Calculate similarity to another conversation style.
        
        Returns:
            Similarity score between 0.0 (completely different) and 1.0 (identical)
        """
        total_difference = 0.0
        
        for axis in CommunicationAxis:
            diff = abs(self.get_axis_value(axis) - other.get_axis_value(axis))
            total_difference += diff
            
        # Normalize to 0-1 scale (max difference per axis is 2.0)
        max_possible_difference = len(CommunicationAxis) * 2.0
        similarity = 1.0 - (total_difference / max_possible_difference)
        
        return max(0.0, min(1.0, similarity))
        
    def blend_with(self, other: "ConversationStyle", weight: float = 0.5) -> "ConversationStyle":
        """
        Create a blended style between this and another style.
        
        Args:
            other: Other conversation style
            weight: Weight of the other style (0.0-1.0)
            
        Returns:
            New blended conversation style
        """
        weight = max(0.0, min(1.0, weight))
        self_weight = 1.0 - weight
        
        blended = ConversationStyle(
            name=f"{self.name}_x_{other.name}",
            description=f"Blend of {self.name} and {other.name}",
            formality=self.formality * self_weight + other.formality * weight,
            verbosity=self.verbosity * self_weight + other.verbosity * weight,
            directness=self.directness * self_weight + other.directness * weight,
            emotiveness=self.emotiveness * self_weight + other.emotiveness * weight,
            supportiveness=self.supportiveness * self_weight + other.supportiveness * weight,
            playfulness=self.playfulness * self_weight + other.playfulness * weight,
            vocabulary_level=self.vocabulary_level,  # Take from primary style
            sentence_structure=self.sentence_structure
        )
        
        # Blend patterns (simple concatenation for now)
        blended.greeting_patterns = self.greeting_patterns + other.greeting_patterns
        blended.response_patterns = self.response_patterns + other.response_patterns
        blended.question_patterns = self.question_patterns + other.question_patterns
        blended.closing_patterns = self.closing_patterns + other.closing_patterns
        
        return blended
        
    def adapt_to_context(self, context: Dict[str, Any]) -> "ConversationStyle":
        """
        Create an adapted version of this style based on context.
        
        Args:
            context: Current conversation context
            
        Returns:
            Adapted conversation style
        """
        adapted = ConversationStyle(
            name=f"{self.name}_adapted",
            description=f"Context-adapted {self.name}",
            formality=self.formality,
            verbosity=self.verbosity,
            directness=self.directness,
            emotiveness=self.emotiveness,
            supportiveness=self.supportiveness,
            playfulness=self.playfulness,
            greeting_patterns=self.greeting_patterns.copy(),
            response_patterns=self.response_patterns.copy(),
            question_patterns=self.question_patterns.copy(),
            closing_patterns=self.closing_patterns.copy(),
            vocabulary_level=self.vocabulary_level,
            sentence_structure=self.sentence_structure,
            metadata=self.metadata.copy()
        )
        
        # Adapt based on context
        if "user_emotion" in context:
            user_emotion = context["user_emotion"]
            if user_emotion in ["sad", "frustrated", "angry"]:
                # Increase supportiveness, reduce playfulness
                adapted.supportiveness = min(1.0, adapted.supportiveness + 0.3)
                adapted.playfulness = max(-1.0, adapted.playfulness - 0.2)
            elif user_emotion in ["happy", "excited"]:
                # Increase playfulness and emotiveness
                adapted.playfulness = min(1.0, adapted.playfulness + 0.2)
                adapted.emotiveness = min(1.0, adapted.emotiveness + 0.2)
                
        if "conversation_length" in context:
            length = context["conversation_length"]
            if length > 20:  # Long conversation
                # Reduce verbosity to avoid fatigue
                adapted.verbosity = max(-1.0, adapted.verbosity - 0.2)
                
        if "topic_complexity" in context:
            complexity = context["topic_complexity"]
            if complexity == "high":
                # Increase formality and directness for clarity
                adapted.formality = min(1.0, adapted.formality + 0.2)
                adapted.directness = min(1.0, adapted.directness + 0.2)
                
        if "urgency" in context:
            urgency = context["urgency"]
            if urgency == "high":
                # Increase directness, reduce playfulness
                adapted.directness = min(1.0, adapted.directness + 0.3)
                adapted.playfulness = max(-1.0, adapted.playfulness - 0.3)
                
        return adapted
        
    def get_description_text(self) -> str:
        """Get a human-readable description of this style."""
        descriptions = []
        
        # Describe each axis
        if abs(self.formality) > 0.2:
            if self.formality > 0:
                descriptions.append(f"formal ({self.formality:.1f})")
            else:
                descriptions.append(f"casual ({self.formality:.1f})")
                
        if abs(self.verbosity) > 0.2:
            if self.verbosity > 0:
                descriptions.append(f"verbose ({self.verbosity:.1f})")
            else:
                descriptions.append(f"concise ({self.verbosity:.1f})")
                
        if abs(self.directness) > 0.2:
            if self.directness > 0:
                descriptions.append(f"direct ({self.directness:.1f})")
            else:
                descriptions.append(f"indirect ({self.directness:.1f})")
                
        if abs(self.emotiveness) > 0.2:
            if self.emotiveness > 0:
                descriptions.append(f"emotional ({self.emotiveness:.1f})")
            else:
                descriptions.append(f"neutral ({self.emotiveness:.1f})")
                
        if abs(self.supportiveness) > 0.2:
            if self.supportiveness > 0:
                descriptions.append(f"supportive ({self.supportiveness:.1f})")
            else:
                descriptions.append(f"critical ({self.supportiveness:.1f})")
                
        if abs(self.playfulness) > 0.2:
            if self.playfulness > 0:
                descriptions.append(f"playful ({self.playfulness:.1f})")
            else:
                descriptions.append(f"serious ({self.playfulness:.1f})")
                
        if not descriptions:
            return "neutral across all dimensions"
            
        return ", ".join(descriptions)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert style to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "formality": self.formality,
            "verbosity": self.verbosity,
            "directness": self.directness,
            "emotiveness": self.emotiveness,
            "supportiveness": self.supportiveness,
            "playfulness": self.playfulness,
            "greeting_patterns": self.greeting_patterns,
            "response_patterns": self.response_patterns,
            "question_patterns": self.question_patterns,
            "closing_patterns": self.closing_patterns,
            "vocabulary_level": self.vocabulary_level,
            "sentence_structure": self.sentence_structure,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationStyle":
        """Create style from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            formality=data.get("formality", 0.0),
            verbosity=data.get("verbosity", 0.0),
            directness=data.get("directness", 0.0),
            emotiveness=data.get("emotiveness", 0.0),
            supportiveness=data.get("supportiveness", 0.0),
            playfulness=data.get("playfulness", 0.0),
            greeting_patterns=data.get("greeting_patterns", []),
            response_patterns=data.get("response_patterns", []),
            question_patterns=data.get("question_patterns", []),
            closing_patterns=data.get("closing_patterns", []),
            vocabulary_level=data.get("vocabulary_level", "standard"),
            sentence_structure=data.get("sentence_structure", "mixed"),
            metadata=data.get("metadata", {})
        )


class ConversationStyleManager:
    """
    Manages conversation styles and their application.
    """
    
    def __init__(self):
        self._styles: Dict[str, ConversationStyle] = {}
        self._current_style: Optional[ConversationStyle] = None
        self._style_history: List[Tuple[str, str]] = []  # (timestamp, style_name)
        
        # Load default styles
        self._load_default_styles()
        
    def add_style(self, style: ConversationStyle) -> None:
        """Add a conversation style."""
        self._styles[style.name] = style
        
    def remove_style(self, name: str) -> Optional[ConversationStyle]:
        """Remove a conversation style."""
        return self._styles.pop(name, None)
        
    def get_style(self, name: str) -> Optional[ConversationStyle]:
        """Get a conversation style by name."""
        return self._styles.get(name)
        
    def list_styles(self) -> List[ConversationStyle]:
        """Get all conversation styles."""
        return list(self._styles.values())
        
    def list_style_names(self) -> List[str]:
        """Get all style names."""
        return list(self._styles.keys())
        
    def set_current_style(self, name: str) -> bool:
        """Set the current conversation style."""
        style = self._styles.get(name)
        if style:
            self._current_style = style
            self._style_history.append((str(len(self._style_history)), name))
            return True
        return False
        
    def get_current_style(self) -> Optional[ConversationStyle]:
        """Get the current conversation style."""
        return self._current_style
        
    def adapt_current_style(self, context: Dict[str, Any]) -> ConversationStyle:
        """
        Adapt the current style to the given context.
        
        Returns:
            Adapted style (does not change the stored current style)
        """
        if self._current_style:
            return self._current_style.adapt_to_context(context)
        else:
            # Return a neutral default style
            return self._create_default_style()
            
    def find_similar_styles(self, target_style: ConversationStyle, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Find styles similar to the target style.
        
        Args:
            target_style: Style to find similarities for
            limit: Maximum number of results
            
        Returns:
            List of (style_name, similarity_score) tuples
        """
        similarities = []
        
        for name, style in self._styles.items():
            if name != target_style.name:  # Don't include self
                similarity = target_style.calculate_similarity(style)
                similarities.append((name, similarity))
                
        # Sort by similarity (highest first) and limit results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
        
    def create_blended_style(
        self, 
        style1_name: str, 
        style2_name: str, 
        weight: float = 0.5,
        new_name: Optional[str] = None
    ) -> Optional[ConversationStyle]:
        """
        Create a blended style from two existing styles.
        
        Args:
            style1_name: Name of first style
            style2_name: Name of second style
            weight: Weight of second style (0.0-1.0)
            new_name: Name for the new style
            
        Returns:
            New blended style or None if styles not found
        """
        style1 = self._styles.get(style1_name)
        style2 = self._styles.get(style2_name)
        
        if not style1 or not style2:
            return None
            
        blended = style1.blend_with(style2, weight)
        
        if new_name:
            blended.name = new_name
            
        return blended
        
    def analyze_style_progression(self) -> Dict[str, Any]:
        """Analyze how conversation styles have changed over time."""
        if len(self._style_history) < 2:
            return {"message": "Not enough style history for analysis"}
            
        changes = []
        for i in range(1, len(self._style_history)):
            prev_style_name = self._style_history[i-1][1]
            curr_style_name = self._style_history[i][1]
            
            if prev_style_name != curr_style_name:
                changes.append({
                    "from": prev_style_name,
                    "to": curr_style_name,
                    "turn": i
                })
                
        most_used = {}
        for _, style_name in self._style_history:
            most_used[style_name] = most_used.get(style_name, 0) + 1
            
        return {
            "total_changes": len(changes),
            "changes": changes,
            "most_used_styles": sorted(most_used.items(), key=lambda x: x[1], reverse=True),
            "current_style": self._current_style.name if self._current_style else None,
            "style_diversity": len(set(name for _, name in self._style_history))
        }
        
    def recommend_style_for_context(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Recommend a conversation style based on context.
        
        Args:
            context: Current conversation context
            
        Returns:
            Recommended style name or None
        """
        # Simple rule-based recommendations
        user_emotion = context.get("user_emotion", "neutral")
        topic_type = context.get("topic_type", "general")
        urgency = context.get("urgency", "normal")
        formality_preference = context.get("formality_preference", "neutral")
        
        if urgency == "high":
            return "professional"
        elif user_emotion in ["sad", "frustrated"]:
            return "empathetic"
        elif user_emotion in ["happy", "excited"]:
            return "enthusiastic"
        elif topic_type == "technical":
            return "technical"
        elif formality_preference == "high":
            return "professional"
        elif formality_preference == "low":
            return "casual"
        else:
            return "friendly"
            
    def export_styles(self, filepath: str) -> None:
        """Export all styles to a JSON file."""
        data = {
            "styles": [style.to_dict() for style in self._styles.values()],
            "current_style": self._current_style.name if self._current_style else None,
            "style_history": self._style_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def import_styles(self, filepath: str) -> None:
        """Import styles from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Import styles
        for style_data in data.get("styles", []):
            style = ConversationStyle.from_dict(style_data)
            self._styles[style.name] = style
            
        # Set current style if specified
        current_style_name = data.get("current_style")
        if current_style_name and current_style_name in self._styles:
            self._current_style = self._styles[current_style_name]
            
        # Import history
        self._style_history = data.get("style_history", [])
        
    def _create_default_style(self) -> ConversationStyle:
        """Create a neutral default conversation style."""
        return ConversationStyle(
            name="default",
            description="Neutral conversation style",
            vocabulary_level="standard",
            sentence_structure="mixed"
        )
        
    def _load_default_styles(self) -> None:
        """Load default conversation styles."""
        
        # Professional/Formal style
        professional = ConversationStyle(
            name="professional",
            description="Formal and structured communication",
            formality=0.8,
            directness=0.6,
            verbosity=0.3,
            emotiveness=-0.3,
            supportiveness=0.2,
            playfulness=-0.5,
            greeting_patterns=[
                "Good morning/afternoon",
                "I hope this message finds you well",
                "Thank you for reaching out"
            ],
            response_patterns=[
                "I would recommend",
                "Please consider",
                "It would be advisable to"
            ],
            vocabulary_level="advanced",
            sentence_structure="complex"
        )
        
        # Casual/Friendly style
        casual = ConversationStyle(
            name="casual",
            description="Relaxed and friendly communication",
            formality=-0.6,
            directness=0.3,
            verbosity=-0.2,
            emotiveness=0.4,
            supportiveness=0.6,
            playfulness=0.5,
            greeting_patterns=[
                "Hey there!",
                "Hi!",
                "What's up?"
            ],
            response_patterns=[
                "Sure thing!",
                "No problem",
                "That sounds great"
            ],
            vocabulary_level="simple",
            sentence_structure="simple"
        )
        
        # Empathetic style
        empathetic = ConversationStyle(
            name="empathetic",
            description="Understanding and supportive communication",
            formality=0.1,
            directness=-0.2,
            verbosity=0.4,
            emotiveness=0.7,
            supportiveness=0.9,
            playfulness=0.1,
            greeting_patterns=[
                "I'm here to help",
                "I understand this might be difficult",
                "Thank you for sharing that with me"
            ],
            response_patterns=[
                "I can see why you'd feel that way",
                "That must be challenging",
                "Your feelings are completely valid"
            ]
        )
        
        # Technical style
        technical = ConversationStyle(
            name="technical",
            description="Precise and detailed technical communication",
            formality=0.5,
            directness=0.8,
            verbosity=0.6,
            emotiveness=-0.4,
            supportiveness=0.3,
            playfulness=-0.3,
            vocabulary_level="technical",
            sentence_structure="complex"
        )
        
        # Enthusiastic style
        enthusiastic = ConversationStyle(
            name="enthusiastic",
            description="Energetic and positive communication",
            formality=-0.2,
            directness=0.4,
            verbosity=0.3,
            emotiveness=0.8,
            supportiveness=0.7,
            playfulness=0.8,
            greeting_patterns=[
                "Awesome!",
                "That's fantastic!",
                "I'm excited to help!"
            ],
            response_patterns=[
                "That's amazing!",
                "Wow, great question!",
                "I love that idea!"
            ]
        )
        
        # Add all default styles
        styles = [professional, casual, empathetic, technical, enthusiastic]
        for style in styles:
            self._styles[style.name] = style
            
        # Set default current style
        self._current_style = casual