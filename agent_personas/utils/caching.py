"""
Advanced caching utilities for persona framework.
"""

from typing import Any, Optional, Dict, Callable, Union, Tuple
from abc import ABC, abstractmethod
import time
import pickle
import json
import hashlib
import threading
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import gzip

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)
        self._access_order: List[str] = []  # For LRU eviction
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            value, expiry_time = self._cache[key]
            
            # Check if expired
            if expiry_time < time.time():
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats.misses += 1
                return None
            
            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._stats.hits += 1
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            expiry_time = time.time() + ttl
            
            # Evict if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = (value, expiry_time)
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._stats.sets += 1
            self._stats.size = len(self._cache)
            return True
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats.deletes += 1
                self._stats.size = len(self._cache)
                return True
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._stats.size = 0
            return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]


class FileCacheBackend(CacheBackend):
    """File-based cache backend."""
    
    def __init__(self, cache_dir: str = None, max_files: int = 1000, 
                 compression: bool = True, default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir or tempfile.gettempdir()) / "persona_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_files = max_files
        self.compression = compression
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        extension = ".gz" if self.compression else ".cache"
        return self.cache_dir / f"{key_hash}{extension}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            if not cache_path.exists():
                self._stats.misses += 1
                return None
            
            try:
                # Check if expired
                metadata_path = cache_path.with_suffix(cache_path.suffix + ".meta")
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    expiry_time = metadata.get("expiry_time", 0)
                    if time.time() > expiry_time:
                        cache_path.unlink()
                        metadata_path.unlink()
                        self._stats.misses += 1
                        return None
                
                # Load data
                if self.compression:
                    with gzip.open(cache_path, 'rb') as f:
                        data = pickle.load(f)
                else:
                    with open(cache_path, 'rb') as f:
                        data = pickle.load(f)
                
                self._stats.hits += 1
                return data
                
            except Exception as e:
                logger.error(f"Error reading cache file {cache_path}: {e}")
                # Clean up corrupted cache file
                if cache_path.exists():
                    cache_path.unlink()
                self._stats.misses += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            try:
                # Evict old files if needed
                self._evict_old_files()
                
                if ttl is None:
                    ttl = self.default_ttl
                
                expiry_time = time.time() + ttl
                
                # Save data
                if self.compression:
                    with gzip.open(cache_path, 'wb') as f:
                        pickle.dump(value, f)
                else:
                    with open(cache_path, 'wb') as f:
                        pickle.dump(value, f)
                
                # Save metadata
                metadata = {
                    "key": key,
                    "created_time": time.time(),
                    "expiry_time": expiry_time,
                    "size": cache_path.stat().st_size
                }
                
                metadata_path = cache_path.with_suffix(cache_path.suffix + ".meta")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
                
                self._stats.sets += 1
                self._stats.size = len(list(self.cache_dir.glob("*.cache*")))
                return True
                
            except Exception as e:
                logger.error(f"Error writing cache file {cache_path}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    
                    # Remove metadata file
                    metadata_path = cache_path.with_suffix(cache_path.suffix + ".meta")
                    if metadata_path.exists():
                        metadata_path.unlink()
                    
                    self._stats.deletes += 1
                    self._stats.size = len(list(self.cache_dir.glob("*.cache*")))
                    return True
                    
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_path}: {e}")
                    return False
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            try:
                for cache_file in self.cache_dir.glob("*"):
                    cache_file.unlink()
                
                self._stats.size = 0
                return True
                
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            # Update size
            self._stats.size = len(list(self.cache_dir.glob("*.cache*")))
            return self._stats
    
    def _evict_old_files(self):
        """Evict old cache files if limit exceeded."""
        cache_files = list(self.cache_dir.glob("*.cache*"))
        
        if len(cache_files) >= self.max_files:
            # Sort by modification time
            cache_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Remove oldest files
            files_to_remove = cache_files[:len(cache_files) - self.max_files + 1]
            
            for cache_file in files_to_remove:
                try:
                    cache_file.unlink()
                    
                    # Remove corresponding metadata file
                    if not cache_file.name.endswith('.meta'):
                        metadata_path = cache_file.with_suffix(cache_file.suffix + ".meta")
                        if metadata_path.exists():
                            metadata_path.unlink()
                            
                except Exception as e:
                    logger.error(f"Error removing old cache file {cache_file}: {e}")


class PersonaCacheManager:
    """Cache manager for persona framework."""
    
    def __init__(self, backend: CacheBackend, key_prefix: str = "persona"):
        self.backend = backend
        self.key_prefix = key_prefix
        self.logger = logging.getLogger(__name__)
    
    def _make_key(self, *args) -> str:
        """Create cache key from arguments."""
        key_parts = [self.key_prefix] + [str(arg) for arg in args]
        key = ":".join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def get_persona(self, persona_id: str) -> Optional[Any]:
        """Get cached persona."""
        key = self._make_key("persona", persona_id)
        return self.backend.get(key)
    
    def cache_persona(self, persona_id: str, persona_data: Any, ttl: int = 3600) -> bool:
        """Cache persona data."""
        key = self._make_key("persona", persona_id)
        return self.backend.set(key, persona_data, ttl)
    
    def get_evaluation(self, persona_id: str, evaluation_type: str) -> Optional[Any]:
        """Get cached evaluation result."""
        key = self._make_key("evaluation", persona_id, evaluation_type)
        return self.backend.get(key)
    
    def cache_evaluation(self, persona_id: str, evaluation_type: str, 
                        evaluation_data: Any, ttl: int = 1800) -> bool:
        """Cache evaluation result."""
        key = self._make_key("evaluation", persona_id, evaluation_type)
        return self.backend.set(key, evaluation_data, ttl)
    
    def get_blend_result(self, persona_ids: List[str], blend_config: str) -> Optional[Any]:
        """Get cached blend result."""
        # Sort persona IDs for consistent key
        sorted_ids = sorted(persona_ids)
        key = self._make_key("blend", "_".join(sorted_ids), blend_config)
        return self.backend.get(key)
    
    def cache_blend_result(self, persona_ids: List[str], blend_config: str,
                          blend_data: Any, ttl: int = 3600) -> bool:
        """Cache blend result."""
        sorted_ids = sorted(persona_ids)
        key = self._make_key("blend", "_".join(sorted_ids), blend_config)
        return self.backend.set(key, blend_data, ttl)
    
    def get_template_personas(self, template_id: str) -> Optional[Any]:
        """Get cached personas created from template."""
        key = self._make_key("template_personas", template_id)
        return self.backend.get(key)
    
    def cache_template_personas(self, template_id: str, personas: Any, ttl: int = 7200) -> bool:
        """Cache personas created from template."""
        key = self._make_key("template_personas", template_id)
        return self.backend.set(key, personas, ttl)
    
    def invalidate_persona(self, persona_id: str) -> bool:
        """Invalidate all cache entries for a persona."""
        # This is a simple implementation - in a real system, you might track
        # all keys associated with a persona for more efficient invalidation
        keys_to_delete = [
            self._make_key("persona", persona_id),
            self._make_key("evaluation", persona_id, "consistency"),
            self._make_key("evaluation", persona_id, "coherence"),
            self._make_key("evaluation", persona_id, "completeness"),
        ]
        
        success = True
        for key in keys_to_delete:
            if not self.backend.delete(key):
                success = False
        
        return success
    
    def clear_all(self) -> bool:
        """Clear all cached data."""
        return self.backend.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.backend.get_stats()
        return {
            "hits": stats.hits,
            "misses": stats.misses,
            "hit_rate": stats.hit_rate,
            "sets": stats.sets,
            "deletes": stats.deletes,
            "size": stats.size
        }


def cache_function_result(cache_manager: PersonaCacheManager, 
                         cache_key_prefix: str, 
                         ttl: int = 3600):
    """Decorator to cache function results."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [cache_key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = ":".join(key_parts)
            hashed_key = hashlib.md5(cache_key.encode()).hexdigest()[:16]
            
            # Try to get from cache
            cached_result = cache_manager.backend.get(hashed_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result and cache it
            result = func(*args, **kwargs)
            cache_manager.backend.set(hashed_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def create_cache_manager(backend_type: str = "memory", **kwargs) -> PersonaCacheManager:
    """Factory function to create cache manager with specified backend."""
    if backend_type == "memory":
        backend = MemoryCacheBackend(
            max_size=kwargs.get("max_size", 1000),
            default_ttl=kwargs.get("default_ttl", 3600)
        )
    elif backend_type == "file":
        backend = FileCacheBackend(
            cache_dir=kwargs.get("cache_dir"),
            max_files=kwargs.get("max_files", 1000),
            compression=kwargs.get("compression", True),
            default_ttl=kwargs.get("default_ttl", 3600)
        )
    else:
        raise ValueError(f"Unsupported cache backend: {backend_type}")
    
    return PersonaCacheManager(backend, kwargs.get("key_prefix", "persona"))