"""
Persona-specific caching for optimized performance.
"""

import hashlib
from typing import Dict, Any, Optional, List
from ..core.persona import Persona
from .memory_cache import MemoryCache


class PersonaCache:
    """
    Cache specifically designed for persona operations.
    """
    
    def __init__(self, max_size: int = 500, default_ttl: float = 1800.0):
        """
        Initialize persona cache.
        
        Args:
            max_size: Maximum number of cached entries
            default_ttl: Default TTL for cached entries (30 minutes)
        """
        self.cache = MemoryCache(max_size=max_size, default_ttl=default_ttl)
        
    def _persona_key(self, persona: Persona) -> str:
        """Generate cache key for a persona."""
        persona_data = persona.to_dict()
        # Create a hash of the persona data for consistent keys
        data_str = str(sorted(persona_data.items()))
        return f"persona:{hashlib.md5(data_str.encode()).hexdigest()}"
    
    def _trait_analysis_key(self, traits: Dict[str, float]) -> str:
        """Generate cache key for trait analysis."""
        traits_str = str(sorted(traits.items()))
        return f"traits:{hashlib.md5(traits_str.encode()).hexdigest()}"
    
    def _similarity_key(self, persona1: str, persona2: str) -> str:
        """Generate cache key for persona similarity."""
        names = tuple(sorted([persona1, persona2]))
        return f"similarity:{names[0]}:{names[1]}"
    
    def cache_persona_analysis(
        self, 
        persona: Persona, 
        analysis_result: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache persona analysis results.
        
        Args:
            persona: Persona that was analyzed
            analysis_result: Analysis results to cache
            ttl: Cache TTL override
        """
        key = f"{self._persona_key(persona)}:analysis"
        self.cache.put(key, analysis_result, ttl)
    
    def get_persona_analysis(self, persona: Persona) -> Optional[Dict[str, Any]]:
        """
        Get cached persona analysis.
        
        Args:
            persona: Persona to get analysis for
            
        Returns:
            Cached analysis or None
        """
        key = f"{self._persona_key(persona)}:analysis"
        return self.cache.get(key)
    
    def cache_trait_validation(
        self,
        traits: Dict[str, float],
        validation_result: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait validation results.
        
        Args:
            traits: Traits that were validated
            validation_result: Validation results
            ttl: Cache TTL override
        """
        key = f"{self._trait_analysis_key(traits)}:validation"
        self.cache.put(key, validation_result, ttl)
    
    def get_trait_validation(self, traits: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Get cached trait validation results.
        
        Args:
            traits: Traits to get validation for
            
        Returns:
            Cached validation or None
        """
        key = f"{self._trait_analysis_key(traits)}:validation"
        return self.cache.get(key)
    
    def cache_persona_similarity(
        self,
        persona1_name: str,
        persona2_name: str,
        similarity_score: float,
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache persona similarity calculation.
        
        Args:
            persona1_name: First persona name
            persona2_name: Second persona name
            similarity_score: Calculated similarity score
            ttl: Cache TTL override
        """
        key = self._similarity_key(persona1_name, persona2_name)
        self.cache.put(key, similarity_score, ttl)
    
    def get_persona_similarity(
        self,
        persona1_name: str,
        persona2_name: str
    ) -> Optional[float]:
        """
        Get cached persona similarity.
        
        Args:
            persona1_name: First persona name
            persona2_name: Second persona name
            
        Returns:
            Cached similarity score or None
        """
        key = self._similarity_key(persona1_name, persona2_name)
        return self.cache.get(key)
    
    def cache_conversation_context(
        self,
        persona_name: str,
        context: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache conversation context for a persona.
        
        Args:
            persona_name: Persona name
            context: Conversation context to cache
            ttl: Cache TTL override
        """
        key = f"context:{persona_name}"
        self.cache.put(key, context, ttl or 300.0)  # 5 minute default
    
    def get_conversation_context(self, persona_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached conversation context.
        
        Args:
            persona_name: Persona name
            
        Returns:
            Cached context or None
        """
        key = f"context:{persona_name}"
        return self.cache.get(key)
    
    def cache_behavior_rules(
        self,
        persona_name: str,
        rules: List[Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache active behavior rules for a persona.
        
        Args:
            persona_name: Persona name
            rules: Active behavior rules
            ttl: Cache TTL override
        """
        key = f"rules:{persona_name}"
        self.cache.put(key, rules, ttl)
    
    def get_behavior_rules(self, persona_name: str) -> Optional[List[Any]]:
        """
        Get cached behavior rules.
        
        Args:
            persona_name: Persona name
            
        Returns:
            Cached rules or None
        """
        key = f"rules:{persona_name}"
        return self.cache.get(key)
    
    def cache_emotional_state(
        self,
        persona_name: str,
        emotional_state: Any,
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache emotional state for a persona.
        
        Args:
            persona_name: Persona name
            emotional_state: Emotional state to cache
            ttl: Cache TTL override
        """
        key = f"emotion:{persona_name}"
        self.cache.put(key, emotional_state, ttl or 180.0)  # 3 minute default
    
    def get_emotional_state(self, persona_name: str) -> Optional[Any]:
        """
        Get cached emotional state.
        
        Args:
            persona_name: Persona name
            
        Returns:
            Cached emotional state or None
        """
        key = f"emotion:{persona_name}"
        return self.cache.get(key)
    
    def invalidate_persona(self, persona_name: str) -> int:
        """
        Invalidate all cached data for a persona.
        
        Args:
            persona_name: Persona name to invalidate
            
        Returns:
            Number of cache entries invalidated
        """
        patterns = [
            f"*:{persona_name}",
            f"*:{persona_name}:*",
            f"similarity:*:{persona_name}*"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += self.cache.invalidate_pattern(pattern)
        
        return total_invalidated
    
    def warm_cache(self, personas: List[Persona]) -> None:
        """
        Pre-populate cache with common operations for given personas.
        
        Args:
            personas: Personas to warm cache for
        """
        # This is a placeholder for cache warming operations
        # In practice, you might pre-compute similarity matrices,
        # trait validations, etc.
        
        for persona in personas:
            # Cache basic persona data
            basic_info = {
                "name": persona.name,
                "trait_count": len(persona.traits),
                "description_length": len(persona.description)
            }
            self.cache_persona_analysis(persona, basic_info, ttl=3600.0)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        base_stats = self.cache.get_stats()
        
        # Add persona-specific metrics
        cache_keys = []
        with self.cache._lock:
            cache_keys = list(self.cache._cache.keys())
        
        key_types = {
            "persona": 0,
            "traits": 0,
            "similarity": 0,
            "context": 0,
            "rules": 0,
            "emotion": 0,
            "other": 0
        }
        
        for key in cache_keys:
            key_type = key.split(":")[0]
            if key_type in key_types:
                key_types[key_type] += 1
            else:
                key_types["other"] += 1
        
        return {
            **base_stats,
            "key_distribution": key_types
        }
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries."""
        return self.cache.cleanup()
    
    def clear_all(self) -> None:
        """Clear all cached data."""
        self.cache.clear()


# Global persona cache instance
global_persona_cache = PersonaCache()