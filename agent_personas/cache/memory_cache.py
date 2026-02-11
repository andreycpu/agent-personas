"""
Memory-based caching implementation for performance optimization.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from collections import OrderedDict


@dataclass
class CacheEntry:
    """Represents a cached value with metadata."""
    value: Any
    timestamp: float
    access_count: int = 0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def touch(self) -> None:
        """Update access information."""
        self.access_count += 1


class MemoryCache:
    """
    Thread-safe memory cache with TTL and LRU eviction.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        cleanup_interval: float = 60.0
    ):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
            cleanup_interval: Interval between cleanup operations
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        # Start cleanup timer
        self._cleanup_timer = None
        self._start_cleanup_timer()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if expired
                if entry.is_expired():
                    del self._cache[key]
                    self._stats["expirations"] += 1
                    self._stats["misses"] += 1
                    return default
                
                # Move to end (LRU)
                self._cache.move_to_end(key)
                entry.touch()
                self._stats["hits"] += 1
                return entry.value
            
            self._stats["misses"] += 1
            return default
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Put value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for default)
        """
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Create new entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            # Evict if necessary
            while len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key existed and was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
    
    def contains(self, key: str) -> bool:
        """Check if key exists in cache (without updating stats)."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                return not entry.is_expired()
            return False
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def cleanup(self) -> int:
        """
        Clean up expired entries.
        
        Returns:
            Number of expired entries removed
        """
        expired_count = 0
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                expired_count += 1
                self._stats["expirations"] += 1
        
        return expired_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"],
                "total_requests": total_requests
            }
    
    def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Any],
        ttl: Optional[float] = None
    ) -> Any:
        """
        Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            compute_func: Function to compute value if not cached
            ttl: Time-to-live for computed value
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache first
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute and cache
        computed_value = compute_func()
        self.put(key, computed_value, ttl)
        return computed_value
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Glob pattern to match keys
            
        Returns:
            Number of keys invalidated
        """
        import fnmatch
        
        invalidated = 0
        with self._lock:
            keys_to_delete = []
            for key in self._cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._cache[key]
                invalidated += 1
        
        return invalidated
    
    def _start_cleanup_timer(self) -> None:
        """Start the automatic cleanup timer."""
        def cleanup_task():
            self.cleanup()
            self._cleanup_timer = threading.Timer(self.cleanup_interval, cleanup_task)
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()
        
        if self.cleanup_interval > 0:
            self._cleanup_timer = threading.Timer(self.cleanup_interval, cleanup_task)
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()
    
    def __del__(self):
        """Cleanup timer on destruction."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()


class LRUCache(MemoryCache):
    """Simple LRU cache without TTL support."""
    
    def __init__(self, max_size: int = 100):
        super().__init__(max_size=max_size, default_ttl=None, cleanup_interval=0)


class TTLCache(MemoryCache):
    """TTL-based cache with automatic expiration."""
    
    def __init__(self, default_ttl: float = 300.0, cleanup_interval: float = 60.0):
        super().__init__(
            max_size=float('inf'), 
            default_ttl=default_ttl,
            cleanup_interval=cleanup_interval
        )


class WeightedCache(MemoryCache):
    """Cache with weighted eviction based on access patterns."""
    
    def _calculate_weight(self, entry: CacheEntry) -> float:
        """Calculate eviction weight for an entry."""
        age = time.time() - entry.timestamp
        access_factor = entry.access_count + 1
        
        # Lower weight = more likely to be evicted
        weight = access_factor / (age + 1)
        return weight
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put with weighted eviction."""
        with self._lock:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Create new entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            # Add to cache
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            # Weighted eviction if necessary
            while len(self._cache) > self.max_size:
                # Find entry with lowest weight
                min_weight = float('inf')
                evict_key = None
                
                for cache_key, cache_entry in list(self._cache.items())[:-1]:  # Don't evict newest
                    weight = self._calculate_weight(cache_entry)
                    if weight < min_weight:
                        min_weight = weight
                        evict_key = cache_key
                
                if evict_key:
                    del self._cache[evict_key]
                    self._stats["evictions"] += 1
                else:
                    # Fallback to LRU
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._stats["evictions"] += 1