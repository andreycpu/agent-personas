"""
Trait-specific caching for computational optimizations.
"""

import hashlib
from typing import Dict, Any, Optional, List, Tuple
from .memory_cache import MemoryCache


class TraitCache:
    """
    Cache specifically optimized for trait-related computations.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0):
        """
        Initialize trait cache.
        
        Args:
            max_size: Maximum number of cached entries
            default_ttl: Default TTL for cached entries (1 hour)
        """
        self.cache = MemoryCache(max_size=max_size, default_ttl=default_ttl)
    
    def _traits_hash(self, traits: Dict[str, float]) -> str:
        """Generate consistent hash for trait dictionary."""
        sorted_traits = tuple(sorted(traits.items()))
        return hashlib.md5(str(sorted_traits).encode()).hexdigest()
    
    def _constraint_hash(self, constraints: Dict[str, Any]) -> str:
        """Generate hash for constraint configuration."""
        sorted_constraints = tuple(sorted(constraints.items()))
        return hashlib.md5(str(sorted_constraints).encode()).hexdigest()
    
    def cache_trait_validation(
        self,
        traits: Dict[str, float],
        constraints: Dict[str, Any],
        result: Tuple[bool, List[str]],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait validation result.
        
        Args:
            traits: Trait values that were validated
            constraints: Constraints used for validation
            result: Validation result (is_valid, errors)
            ttl: Cache TTL override
        """
        traits_hash = self._traits_hash(traits)
        constraints_hash = self._constraint_hash(constraints)
        key = f"validation:{traits_hash}:{constraints_hash}"
        
        self.cache.put(key, result, ttl)
    
    def get_trait_validation(
        self,
        traits: Dict[str, float],
        constraints: Dict[str, Any]
    ) -> Optional[Tuple[bool, List[str]]]:
        """
        Get cached trait validation result.
        
        Args:
            traits: Trait values to validate
            constraints: Validation constraints
            
        Returns:
            Cached validation result or None
        """
        traits_hash = self._traits_hash(traits)
        constraints_hash = self._constraint_hash(constraints)
        key = f"validation:{traits_hash}:{constraints_hash}"
        
        return self.cache.get(key)
    
    def cache_trait_analysis(
        self,
        traits: Dict[str, float],
        analysis: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait analysis result.
        
        Args:
            traits: Traits that were analyzed
            analysis: Analysis result
            ttl: Cache TTL override
        """
        traits_hash = self._traits_hash(traits)
        key = f"analysis:{traits_hash}"
        
        self.cache.put(key, analysis, ttl)
    
    def get_trait_analysis(self, traits: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Get cached trait analysis.
        
        Args:
            traits: Traits to get analysis for
            
        Returns:
            Cached analysis or None
        """
        traits_hash = self._traits_hash(traits)
        key = f"analysis:{traits_hash}"
        
        return self.cache.get(key)
    
    def cache_conflict_resolution(
        self,
        original_traits: Dict[str, float],
        resolved_traits: Dict[str, float],
        strategy: str,
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache conflict resolution result.
        
        Args:
            original_traits: Original conflicting traits
            resolved_traits: Resolved traits
            strategy: Resolution strategy used
            ttl: Cache TTL override
        """
        original_hash = self._traits_hash(original_traits)
        key = f"conflict:{original_hash}:{strategy}"
        
        self.cache.put(key, resolved_traits, ttl)
    
    def get_conflict_resolution(
        self,
        original_traits: Dict[str, float],
        strategy: str
    ) -> Optional[Dict[str, float]]:
        """
        Get cached conflict resolution.
        
        Args:
            original_traits: Original conflicting traits
            strategy: Resolution strategy
            
        Returns:
            Cached resolved traits or None
        """
        original_hash = self._traits_hash(original_traits)
        key = f"conflict:{original_hash}:{strategy}"
        
        return self.cache.get(key)
    
    def cache_trait_suggestions(
        self,
        current_traits: Dict[str, float],
        suggestions: Dict[str, float],
        context: str = "general",
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait adjustment suggestions.
        
        Args:
            current_traits: Current trait values
            suggestions: Suggested adjustments
            context: Context for suggestions
            ttl: Cache TTL override
        """
        traits_hash = self._traits_hash(current_traits)
        key = f"suggestions:{traits_hash}:{context}"
        
        self.cache.put(key, suggestions, ttl)
    
    def get_trait_suggestions(
        self,
        current_traits: Dict[str, float],
        context: str = "general"
    ) -> Optional[Dict[str, float]]:
        """
        Get cached trait suggestions.
        
        Args:
            current_traits: Current trait values
            context: Context for suggestions
            
        Returns:
            Cached suggestions or None
        """
        traits_hash = self._traits_hash(current_traits)
        key = f"suggestions:{traits_hash}:{context}"
        
        return self.cache.get(key)
    
    def cache_trait_compatibility(
        self,
        traits1: Dict[str, float],
        traits2: Dict[str, float],
        compatibility_score: float,
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait compatibility calculation.
        
        Args:
            traits1: First trait set
            traits2: Second trait set
            compatibility_score: Calculated compatibility
            ttl: Cache TTL override
        """
        hash1 = self._traits_hash(traits1)
        hash2 = self._traits_hash(traits2)
        
        # Create symmetric key (order independent)
        key_parts = sorted([hash1, hash2])
        key = f"compatibility:{key_parts[0]}:{key_parts[1]}"
        
        self.cache.put(key, compatibility_score, ttl)
    
    def get_trait_compatibility(
        self,
        traits1: Dict[str, float],
        traits2: Dict[str, float]
    ) -> Optional[float]:
        """
        Get cached trait compatibility.
        
        Args:
            traits1: First trait set
            traits2: Second trait set
            
        Returns:
            Cached compatibility score or None
        """
        hash1 = self._traits_hash(traits1)
        hash2 = self._traits_hash(traits2)
        
        # Create symmetric key (order independent)
        key_parts = sorted([hash1, hash2])
        key = f"compatibility:{key_parts[0]}:{key_parts[1]}"
        
        return self.cache.get(key)
    
    def cache_trait_normalization(
        self,
        original_traits: Dict[str, float],
        normalized_traits: Dict[str, float],
        method: str = "standard",
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait normalization result.
        
        Args:
            original_traits: Original trait values
            normalized_traits: Normalized trait values
            method: Normalization method
            ttl: Cache TTL override
        """
        original_hash = self._traits_hash(original_traits)
        key = f"normalization:{original_hash}:{method}"
        
        self.cache.put(key, normalized_traits, ttl)
    
    def get_trait_normalization(
        self,
        original_traits: Dict[str, float],
        method: str = "standard"
    ) -> Optional[Dict[str, float]]:
        """
        Get cached trait normalization.
        
        Args:
            original_traits: Original trait values
            method: Normalization method
            
        Returns:
            Cached normalized traits or None
        """
        original_hash = self._traits_hash(original_traits)
        key = f"normalization:{original_hash}:{method}"
        
        return self.cache.get(key)
    
    def cache_trait_clustering(
        self,
        traits_list: List[Dict[str, float]],
        clusters: List[List[int]],
        method: str = "kmeans",
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait clustering result.
        
        Args:
            traits_list: List of trait dictionaries
            clusters: Clustering result
            method: Clustering method
            ttl: Cache TTL override
        """
        # Create hash from all trait sets
        all_hashes = [self._traits_hash(traits) for traits in traits_list]
        combined_hash = hashlib.md5(str(sorted(all_hashes)).encode()).hexdigest()
        key = f"clustering:{combined_hash}:{method}"
        
        self.cache.put(key, clusters, ttl or 7200.0)  # 2 hour default for clustering
    
    def get_trait_clustering(
        self,
        traits_list: List[Dict[str, float]],
        method: str = "kmeans"
    ) -> Optional[List[List[int]]]:
        """
        Get cached trait clustering.
        
        Args:
            traits_list: List of trait dictionaries
            method: Clustering method
            
        Returns:
            Cached clusters or None
        """
        all_hashes = [self._traits_hash(traits) for traits in traits_list]
        combined_hash = hashlib.md5(str(sorted(all_hashes)).encode()).hexdigest()
        key = f"clustering:{combined_hash}:{method}"
        
        return self.cache.get(key)
    
    def cache_trait_statistics(
        self,
        traits_list: List[Dict[str, float]],
        statistics: Dict[str, Any],
        ttl: Optional[float] = None
    ) -> None:
        """
        Cache trait statistics for a collection.
        
        Args:
            traits_list: List of trait dictionaries
            statistics: Computed statistics
            ttl: Cache TTL override
        """
        all_hashes = [self._traits_hash(traits) for traits in traits_list]
        combined_hash = hashlib.md5(str(sorted(all_hashes)).encode()).hexdigest()
        key = f"statistics:{combined_hash}"
        
        self.cache.put(key, statistics, ttl)
    
    def get_trait_statistics(
        self,
        traits_list: List[Dict[str, float]]
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached trait statistics.
        
        Args:
            traits_list: List of trait dictionaries
            
        Returns:
            Cached statistics or None
        """
        all_hashes = [self._traits_hash(traits) for traits in traits_list]
        combined_hash = hashlib.md5(str(sorted(all_hashes)).encode()).hexdigest()
        key = f"statistics:{combined_hash}"
        
        return self.cache.get(key)
    
    def invalidate_trait_cache(self, traits: Dict[str, float]) -> int:
        """
        Invalidate all cache entries related to specific traits.
        
        Args:
            traits: Traits to invalidate cache for
            
        Returns:
            Number of cache entries invalidated
        """
        traits_hash = self._traits_hash(traits)
        patterns = [
            f"*:{traits_hash}",
            f"*:{traits_hash}:*"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += self.cache.invalidate_pattern(pattern)
        
        return total_invalidated
    
    def precompute_common_validations(
        self,
        trait_sets: List[Dict[str, float]],
        constraint_sets: List[Dict[str, Any]]
    ) -> int:
        """
        Precompute and cache common trait validations.
        
        Args:
            trait_sets: Common trait configurations
            constraint_sets: Common constraint configurations
            
        Returns:
            Number of validations precomputed
        """
        precomputed = 0
        
        for traits in trait_sets:
            for constraints in constraint_sets:
                # Check if already cached
                if self.get_trait_validation(traits, constraints) is None:
                    # Compute and cache (this would call actual validation logic)
                    # For now, we'll cache a placeholder
                    result = (True, [])  # Placeholder
                    self.cache_trait_validation(traits, constraints, result)
                    precomputed += 1
        
        return precomputed
    
    def get_cache_efficiency(self) -> Dict[str, Any]:
        """
        Get cache efficiency metrics.
        
        Returns:
            Cache efficiency statistics
        """
        base_stats = self.cache.get_stats()
        
        # Analyze cache key distribution
        cache_keys = []
        with self.cache._lock:
            cache_keys = list(self.cache._cache.keys())
        
        key_types = {}
        for key in cache_keys:
            key_type = key.split(":")[0]
            key_types[key_type] = key_types.get(key_type, 0) + 1
        
        return {
            **base_stats,
            "key_type_distribution": key_types,
            "avg_key_length": sum(len(k) for k in cache_keys) / len(cache_keys) if cache_keys else 0
        }
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        return self.cache.cleanup()
    
    def clear_all(self) -> None:
        """Clear all cached data."""
        self.cache.clear()


# Global trait cache instance
global_trait_cache = TraitCache()