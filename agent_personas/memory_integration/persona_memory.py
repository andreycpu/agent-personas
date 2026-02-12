"""
Persona-integrated memory system that adapts memory formation based on personality traits.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
import math
import hashlib

from ..core.persona import Persona

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memories in the persona system."""
    EPISODIC = "episodic"  # Specific events and experiences
    SEMANTIC = "semantic"  # General knowledge and concepts
    EMOTIONAL = "emotional"  # Emotionally significant memories
    PROCEDURAL = "procedural"  # Skills and procedures
    PREFERENCE = "preference"  # Learned preferences and patterns
    SOCIAL = "social"  # Interpersonal interactions and relationships


class MemoryImportance(Enum):
    """Importance levels for memories."""
    TRIVIAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


class EmotionalValence(Enum):
    """Emotional charge of memories."""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


@dataclass
class MemoryTrace:
    """
    Individual memory trace with persona-influenced characteristics.
    """
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    importance: MemoryImportance
    emotional_valence: EmotionalValence
    
    # Persona-influenced attributes
    personal_relevance: float = 0.5  # 0.0-1.0, how personally relevant
    emotional_intensity: float = 0.0  # 0.0-1.0, emotional strength
    retrieval_strength: float = 1.0  # 0.0-1.0, how easily recalled
    decay_rate: float = 0.1  # How quickly memory fades
    
    # Associative connections
    associated_memories: Set[str] = field(default_factory=set)
    contextual_tags: Set[str] = field(default_factory=set)
    entity_references: Set[str] = field(default_factory=set)
    
    # Metadata
    source: Optional[str] = None  # Source of the memory
    confidence: float = 1.0  # Confidence in memory accuracy
    access_count: int = 0  # How many times accessed
    last_accessed: Optional[datetime] = None
    consolidation_level: float = 0.0  # How well consolidated (0.0-1.0)
    
    def __post_init__(self):
        """Initialize memory trace."""
        if not self.id:
            self.id = self._generate_id()
        
        if not 0.0 <= self.personal_relevance <= 1.0:
            raise ValueError("Personal relevance must be between 0.0 and 1.0")
        
        if not 0.0 <= self.emotional_intensity <= 1.0:
            raise ValueError("Emotional intensity must be between 0.0 and 1.0")
        
        if not 0.0 <= self.retrieval_strength <= 1.0:
            raise ValueError("Retrieval strength must be between 0.0 and 1.0")
    
    def _generate_id(self) -> str:
        """Generate a unique ID for the memory."""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        return f"mem_{timestamp_str}_{content_hash}"
    
    def access(self, current_time: Optional[datetime] = None) -> None:
        """Record memory access and update retrieval strength."""
        if current_time is None:
            current_time = datetime.now()
        
        self.access_count += 1
        self.last_accessed = current_time
        
        # Strengthen memory through access (spaced repetition effect)
        access_boost = 0.1 * (1.0 / (1.0 + math.exp(-0.1 * (self.access_count - 3))))
        self.retrieval_strength = min(1.0, self.retrieval_strength + access_boost)
    
    def decay(self, time_delta: timedelta) -> None:
        """Apply decay to memory strength based on time and decay rate."""
        days_passed = time_delta.days + (time_delta.seconds / 86400)
        decay_factor = math.exp(-self.decay_rate * days_passed)
        
        # Apply different decay to different aspects
        self.retrieval_strength *= decay_factor
        self.confidence *= (decay_factor ** 0.5)  # Confidence decays slower
        
        # Emotional memories decay slower
        if self.emotional_intensity > 0.5:
            emotion_protection = 1.0 + self.emotional_intensity * 0.5
            self.retrieval_strength *= emotion_protection
    
    def get_retrieval_probability(self) -> float:
        """Calculate probability of successful retrieval."""
        base_probability = self.retrieval_strength
        
        # Adjust for importance
        importance_boost = (self.importance.value - 1) / 4 * 0.3  # 0-0.3 boost
        
        # Adjust for emotional intensity
        emotion_boost = self.emotional_intensity * 0.2  # 0-0.2 boost
        
        # Adjust for personal relevance
        relevance_boost = self.personal_relevance * 0.2  # 0-0.2 boost
        
        # Adjust for consolidation
        consolidation_boost = self.consolidation_level * 0.15  # 0-0.15 boost
        
        total_probability = base_probability + importance_boost + emotion_boost + relevance_boost + consolidation_boost
        return min(1.0, max(0.0, total_probability))
    
    def add_association(self, memory_id: str) -> None:
        """Add an association to another memory."""
        self.associated_memories.add(memory_id)
    
    def add_contextual_tag(self, tag: str) -> None:
        """Add a contextual tag."""
        self.contextual_tags.add(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory trace to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance.value,
            "emotional_valence": self.emotional_valence.value,
            "personal_relevance": self.personal_relevance,
            "emotional_intensity": self.emotional_intensity,
            "retrieval_strength": self.retrieval_strength,
            "decay_rate": self.decay_rate,
            "associated_memories": list(self.associated_memories),
            "contextual_tags": list(self.contextual_tags),
            "entity_references": list(self.entity_references),
            "source": self.source,
            "confidence": self.confidence,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "consolidation_level": self.consolidation_level
        }


class PersonaMemory:
    """
    Memory system that adapts based on persona characteristics.
    
    Integrates personality traits with memory formation, storage, and retrieval
    to create persona-consistent memory behaviors.
    """
    
    def __init__(self, persona: Persona):
        self.persona = persona
        self.memories: Dict[str, MemoryTrace] = {}
        self.memory_index: Dict[str, Set[str]] = {}  # Tag -> memory IDs
        self.importance_thresholds: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)
        
        # Configure memory system based on persona traits
        self._configure_memory_system()
        
    def _configure_memory_system(self):
        """Configure memory parameters based on persona traits."""
        traits = self.persona.traits
        
        # Base memory configuration on traits
        self.base_decay_rate = 0.1 * (1.0 - traits.get("methodical", 0.5))  # Methodical people remember longer
        self.emotional_sensitivity = traits.get("empathetic", 0.5) + traits.get("emotional", 0.5) / 2
        self.detail_focus = traits.get("analytical", 0.5) + traits.get("precise", 0.5) / 2
        self.social_memory_bias = traits.get("social", 0.5) + traits.get("friendly", 0.5) / 2
        
        # Set importance thresholds for different memory types based on persona
        self.importance_thresholds = {
            MemoryType.EMOTIONAL.value: 0.3 + self.emotional_sensitivity * 0.4,
            MemoryType.SOCIAL.value: 0.3 + self.social_memory_bias * 0.4,
            MemoryType.SEMANTIC.value: 0.4 + self.detail_focus * 0.3,
            MemoryType.PROCEDURAL.value: 0.5 + traits.get("practical", 0.5) * 0.3,
            MemoryType.PREFERENCE.value: 0.4,
            MemoryType.EPISODIC.value: 0.5
        }
        
        self.logger.debug(f"Configured memory system for persona {self.persona.name}")
    
    def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: Optional[MemoryImportance] = None,
        emotional_valence: Optional[EmotionalValence] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> MemoryTrace:
        """
        Store a new memory with persona-influenced characteristics.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Memory importance (auto-calculated if not provided)
            emotional_valence: Emotional charge (auto-detected if not provided)
            context: Additional context for memory formation
            
        Returns:
            The created memory trace
        """
        if context is None:
            context = {}
        
        # Auto-calculate importance if not provided
        if importance is None:
            importance = self._calculate_importance(content, memory_type, context)
        
        # Auto-detect emotional valence if not provided
        if emotional_valence is None:
            emotional_valence = self._detect_emotional_valence(content)
        
        # Create memory trace
        memory = MemoryTrace(
            id="",  # Will be generated in __post_init__
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            importance=importance,
            emotional_valence=emotional_valence,
            source=context.get("source")
        )
        
        # Apply persona-specific memory formation
        self._apply_persona_influence(memory, context)
        
        # Store memory
        self.memories[memory.id] = memory
        
        # Update index
        self._index_memory(memory)
        
        self.logger.info(f"Stored {memory_type.value} memory: {memory.id}")
        return memory
    
    def _calculate_importance(
        self,
        content: str,
        memory_type: MemoryType,
        context: Dict[str, Any]
    ) -> MemoryImportance:
        """Calculate memory importance based on persona traits and content."""
        base_importance = 3  # Moderate
        
        # Adjust based on memory type and persona preferences
        threshold = self.importance_thresholds.get(memory_type.value, 0.5)
        
        # Content-based importance signals
        importance_signals = 0.0
        
        # Length and detail (appreciated by analytical personas)
        if len(content) > 100:
            importance_signals += 0.1 * self.detail_focus
        
        # Emotional content (appreciated by empathetic personas)
        emotional_words = ["love", "hate", "fear", "joy", "anger", "sad", "happy", "excited"]
        emotional_count = sum(1 for word in emotional_words if word in content.lower())
        importance_signals += emotional_count * 0.05 * self.emotional_sensitivity
        
        # Social content (appreciated by social personas)
        social_words = ["friend", "family", "relationship", "together", "team", "group"]
        social_count = sum(1 for word in social_words if word in content.lower())
        importance_signals += social_count * 0.05 * self.social_memory_bias
        
        # Context-based importance
        if context.get("user_emphasized", False):
            importance_signals += 0.3
        
        if context.get("repeated_topic", False):
            importance_signals += 0.2
        
        # Calculate final importance
        final_score = threshold + importance_signals
        
        if final_score >= 0.8:
            return MemoryImportance.CRITICAL
        elif final_score >= 0.65:
            return MemoryImportance.HIGH
        elif final_score >= 0.5:
            return MemoryImportance.MODERATE
        elif final_score >= 0.3:
            return MemoryImportance.LOW
        else:
            return MemoryImportance.TRIVIAL
    
    def _detect_emotional_valence(self, content: str) -> EmotionalValence:
        """Simple emotional valence detection."""
        positive_words = ["great", "excellent", "wonderful", "amazing", "love", "happy", "joy", "fantastic", "awesome"]
        negative_words = ["terrible", "awful", "hate", "sad", "angry", "frustrated", "horrible", "disappointing"]
        
        words = content.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_emotional = positive_count + negative_count
        if total_emotional == 0:
            return EmotionalValence.NEUTRAL
        
        sentiment_score = (positive_count - negative_count) / total_emotional
        
        if sentiment_score >= 0.6:
            return EmotionalValence.VERY_POSITIVE
        elif sentiment_score >= 0.2:
            return EmotionalValence.POSITIVE
        elif sentiment_score <= -0.6:
            return EmotionalValence.VERY_NEGATIVE
        elif sentiment_score <= -0.2:
            return EmotionalValence.NEGATIVE
        else:
            return EmotionalValence.NEUTRAL
    
    def _apply_persona_influence(self, memory: MemoryTrace, context: Dict[str, Any]) -> None:
        """Apply persona-specific influences to memory formation."""
        traits = self.persona.traits
        
        # Personal relevance based on persona interests
        base_relevance = 0.5
        
        # Increase relevance for memory types aligned with persona
        if memory.memory_type == MemoryType.EMOTIONAL and self.emotional_sensitivity > 0.6:
            base_relevance += 0.3
        
        if memory.memory_type == MemoryType.SOCIAL and self.social_memory_bias > 0.6:
            base_relevance += 0.3
        
        if memory.memory_type == MemoryType.SEMANTIC and self.detail_focus > 0.6:
            base_relevance += 0.2
        
        memory.personal_relevance = min(1.0, base_relevance)
        
        # Emotional intensity based on persona emotional traits
        if memory.emotional_valence != EmotionalValence.NEUTRAL:
            base_intensity = 0.3
            intensity_multiplier = 1.0 + self.emotional_sensitivity
            memory.emotional_intensity = min(1.0, base_intensity * intensity_multiplier)
        
        # Decay rate influenced by persona memory traits
        memory.decay_rate = self.base_decay_rate
        
        # Adjust decay for important memories (conscientious personas retain more)
        if memory.importance.value >= 4:  # High or Critical
            conscientiousness = traits.get("methodical", 0.5) + traits.get("organized", 0.5) / 2
            memory.decay_rate *= (1.0 - conscientiousness * 0.3)
        
        # Add contextual tags based on persona focus areas
        if self.social_memory_bias > 0.6:
            memory.add_contextual_tag("social_context")
        
        if self.emotional_sensitivity > 0.6:
            memory.add_contextual_tag("emotional_context")
        
        if self.detail_focus > 0.6:
            memory.add_contextual_tag("detail_oriented")
    
    def _index_memory(self, memory: MemoryTrace) -> None:
        """Index memory for efficient retrieval."""
        # Index by memory type
        type_key = f"type:{memory.memory_type.value}"
        if type_key not in self.memory_index:
            self.memory_index[type_key] = set()
        self.memory_index[type_key].add(memory.id)
        
        # Index by importance
        importance_key = f"importance:{memory.importance.value}"
        if importance_key not in self.memory_index:
            self.memory_index[importance_key] = set()
        self.memory_index[importance_key].add(memory.id)
        
        # Index by contextual tags
        for tag in memory.contextual_tags:
            tag_key = f"tag:{tag}"
            if tag_key not in self.memory_index:
                self.memory_index[tag_key] = set()
            self.memory_index[tag_key].add(memory.id)
        
        # Index by emotional valence
        valence_key = f"valence:{memory.emotional_valence.value}"
        if valence_key not in self.memory_index:
            self.memory_index[valence_key] = set()
        self.memory_index[valence_key].add(memory.id)
    
    def retrieve_memories(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        min_importance: Optional[MemoryImportance] = None,
        max_results: int = 10
    ) -> List[MemoryTrace]:
        """
        Retrieve memories based on query and filters.
        
        Uses persona-influenced retrieval that prioritizes memories
        relevant to the persona's characteristics.
        """
        candidates = set(self.memories.keys())
        
        # Apply type filter
        if memory_types:
            type_candidates = set()
            for mem_type in memory_types:
                type_key = f"type:{mem_type.value}"
                if type_key in self.memory_index:
                    type_candidates.update(self.memory_index[type_key])
            candidates &= type_candidates
        
        # Apply importance filter
        if min_importance:
            importance_candidates = set()
            for imp_value in range(min_importance.value, 6):  # 6 is max + 1
                importance_key = f"importance:{imp_value}"
                if importance_key in self.memory_index:
                    importance_candidates.update(self.memory_index[importance_key])
            candidates &= importance_candidates
        
        # Score and rank memories
        scored_memories = []
        query_lower = query.lower()
        
        for memory_id in candidates:
            memory = self.memories[memory_id]
            
            # Calculate retrieval score
            score = self._calculate_retrieval_score(memory, query_lower)
            
            if score > 0.1:  # Only include memories with meaningful scores
                scored_memories.append((score, memory))
        
        # Sort by score and return top results
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        results = [memory for _, memory in scored_memories[:max_results]]
        
        # Update access tracking for retrieved memories
        for memory in results:
            memory.access()
        
        self.logger.info(f"Retrieved {len(results)} memories for query: {query}")
        return results
    
    def _calculate_retrieval_score(self, memory: MemoryTrace, query: str) -> float:
        """Calculate retrieval score for a memory given a query."""
        # Base retrieval probability
        score = memory.get_retrieval_probability()
        
        # Content relevance
        content_lower = memory.content.lower()
        query_words = set(query.split())
        content_words = set(content_lower.split())
        
        if query_words & content_words:  # Any word overlap
            overlap_ratio = len(query_words & content_words) / len(query_words)
            score += overlap_ratio * 0.5
        
        # Exact phrase match bonus
        if query in content_lower:
            score += 0.3
        
        # Persona-influenced scoring adjustments
        traits = self.persona.traits
        
        # Boost emotional memories for emotionally sensitive personas
        if memory.emotional_intensity > 0.5 and self.emotional_sensitivity > 0.6:
            score += 0.2
        
        # Boost social memories for social personas
        if memory.memory_type == MemoryType.SOCIAL and self.social_memory_bias > 0.6:
            score += 0.15
        
        # Boost detailed memories for analytical personas
        if len(memory.content) > 100 and self.detail_focus > 0.6:
            score += 0.1
        
        return min(1.0, score)
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about the memory system."""
        if not self.memories:
            return {"total_memories": 0}
        
        # Basic counts
        total_memories = len(self.memories)
        
        # Memory type distribution
        type_distribution = {}
        for memory in self.memories.values():
            mem_type = memory.memory_type.value
            type_distribution[mem_type] = type_distribution.get(mem_type, 0) + 1
        
        # Importance distribution
        importance_distribution = {}
        for memory in self.memories.values():
            importance = memory.importance.name
            importance_distribution[importance] = importance_distribution.get(importance, 0) + 1
        
        # Average retrieval strength
        avg_retrieval_strength = sum(m.retrieval_strength for m in self.memories.values()) / total_memories
        
        # Most accessed memories
        most_accessed = sorted(self.memories.values(), key=lambda m: m.access_count, reverse=True)[:5]
        
        return {
            "total_memories": total_memories,
            "type_distribution": type_distribution,
            "importance_distribution": importance_distribution,
            "average_retrieval_strength": round(avg_retrieval_strength, 3),
            "base_decay_rate": self.base_decay_rate,
            "emotional_sensitivity": self.emotional_sensitivity,
            "detail_focus": self.detail_focus,
            "social_memory_bias": self.social_memory_bias,
            "most_accessed_memories": [{"id": m.id, "access_count": m.access_count, "content_preview": m.content[:50]} for m in most_accessed]
        }