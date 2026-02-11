"""
Tests for agent_personas.cache.memory_cache module.
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock

from agent_personas.cache.memory_cache import (
    CacheEntry,
    MemoryCache,
    LRUCache,
    TTLCache,
    WeightedCache,
)


class TestCacheEntry:
    def test_cache_entry_creation(self):
        entry = CacheEntry(value="test", timestamp=time.time())
        assert entry.value == "test"
        assert entry.access_count == 0
        assert entry.ttl is None
        
    def test_cache_entry_with_ttl(self):
        entry = CacheEntry(value="test", timestamp=time.time(), ttl=60.0)
        assert entry.ttl == 60.0
        
    def test_is_expired_no_ttl(self):
        entry = CacheEntry(value="test", timestamp=time.time())
        assert not entry.is_expired()
        
    def test_is_expired_with_ttl_not_expired(self):
        entry = CacheEntry(value="test", timestamp=time.time(), ttl=60.0)
        assert not entry.is_expired()
        
    def test_is_expired_with_ttl_expired(self):
        past_time = time.time() - 120  # 2 minutes ago
        entry = CacheEntry(value="test", timestamp=past_time, ttl=60.0)
        assert entry.is_expired()
        
    def test_touch_updates_access_count(self):
        entry = CacheEntry(value="test", timestamp=time.time())
        assert entry.access_count == 0
        entry.touch()
        assert entry.access_count == 1
        entry.touch()
        assert entry.access_count == 2


class TestMemoryCache:
    def test_cache_initialization(self):
        cache = MemoryCache(max_size=100, default_ttl=300.0)
        assert cache.max_size == 100
        assert cache.default_ttl == 300.0
        assert cache.size() == 0
        
    def test_put_and_get(self):
        cache = MemoryCache()
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
    def test_get_default(self):
        cache = MemoryCache()
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"
        
    def test_put_with_ttl(self):
        cache = MemoryCache()
        cache.put("key1", "value1", ttl=1.0)
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
        
    def test_delete(self):
        cache = MemoryCache()
        cache.put("key1", "value1")
        assert cache.contains("key1")
        
        assert cache.delete("key1") == True
        assert not cache.contains("key1")
        assert cache.delete("nonexistent") == False
        
    def test_clear(self):
        cache = MemoryCache()
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        assert cache.size() == 2
        
        cache.clear()
        assert cache.size() == 0
        
    def test_contains(self):
        cache = MemoryCache()
        assert not cache.contains("key1")
        
        cache.put("key1", "value1")
        assert cache.contains("key1")
        
    def test_size(self):
        cache = MemoryCache()
        assert cache.size() == 0
        
        cache.put("key1", "value1")
        assert cache.size() == 1
        
        cache.put("key2", "value2")
        assert cache.size() == 2
        
    def test_lru_eviction(self):
        cache = MemoryCache(max_size=2)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # Should evict key1
        
        assert not cache.contains("key1")
        assert cache.contains("key2")
        assert cache.contains("key3")
        
    def test_lru_access_updates_order(self):
        cache = MemoryCache(max_size=2)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Access key1 to move it to end
        cache.get("key1")
        
        # Add key3, should evict key2 (not key1)
        cache.put("key3", "value3")
        
        assert cache.contains("key1")
        assert not cache.contains("key2")
        assert cache.contains("key3")
        
    def test_cleanup_expired_entries(self):
        cache = MemoryCache()
        cache.put("key1", "value1", ttl=0.1)  # Short TTL
        cache.put("key2", "value2")  # No TTL
        
        time.sleep(0.2)
        expired_count = cache.cleanup()
        
        assert expired_count == 1
        assert not cache.contains("key1")
        assert cache.contains("key2")
        
    def test_get_stats(self):
        cache = MemoryCache()
        
        # Initial stats
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        
        # Add some cache operations
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        
    def test_get_or_compute_cache_hit(self):
        cache = MemoryCache()
        cache.put("key1", "cached_value")
        
        compute_func = MagicMock(return_value="computed_value")
        result = cache.get_or_compute("key1", compute_func)
        
        assert result == "cached_value"
        compute_func.assert_not_called()
        
    def test_get_or_compute_cache_miss(self):
        cache = MemoryCache()
        
        compute_func = MagicMock(return_value="computed_value")
        result = cache.get_or_compute("key1", compute_func)
        
        assert result == "computed_value"
        compute_func.assert_called_once()
        assert cache.get("key1") == "computed_value"
        
    def test_invalidate_pattern(self):
        cache = MemoryCache()
        cache.put("user:1", "value1")
        cache.put("user:2", "value2")
        cache.put("session:1", "value3")
        cache.put("user:3", "value4")
        
        invalidated = cache.invalidate_pattern("user:*")
        
        assert invalidated == 3
        assert not cache.contains("user:1")
        assert not cache.contains("user:2")
        assert not cache.contains("user:3")
        assert cache.contains("session:1")
        
    def test_thread_safety(self):
        cache = MemoryCache()
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(100):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"value_{i}"
                    cache.put(key, value)
                    retrieved = cache.get(key)
                    if retrieved != value:
                        errors.append(f"Mismatch in thread {thread_id}")
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Error in thread {thread_id}: {e}")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5
        
    @patch('threading.Timer')
    def test_cleanup_timer_initialization(self, mock_timer):
        mock_timer_instance = MagicMock()
        mock_timer.return_value = mock_timer_instance
        
        cache = MemoryCache(cleanup_interval=30.0)
        
        mock_timer.assert_called_once()
        mock_timer_instance.start.assert_called_once()


class TestLRUCache:
    def test_lru_cache_initialization(self):
        cache = LRUCache(max_size=50)
        assert cache.max_size == 50
        assert cache.default_ttl is None
        
    def test_lru_cache_no_ttl_expiration(self):
        cache = LRUCache()
        cache.put("key1", "value1", ttl=0.1)  # TTL is ignored
        time.sleep(0.2)
        
        # Value should still be there (no TTL support)
        assert cache.get("key1") == "value1"


class TestTTLCache:
    def test_ttl_cache_initialization(self):
        cache = TTLCache(default_ttl=60.0)
        assert cache.default_ttl == 60.0
        assert cache.max_size == float('inf')
        
    def test_ttl_cache_automatic_expiration(self):
        cache = TTLCache(default_ttl=0.1, cleanup_interval=0.1)
        cache.put("key1", "value1")
        
        # Initially present
        assert cache.contains("key1")
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired
        assert not cache.contains("key1")


class TestWeightedCache:
    def test_weighted_cache_initialization(self):
        cache = WeightedCache(max_size=3)
        assert cache.max_size == 3
        
    def test_weighted_eviction(self):
        cache = WeightedCache(max_size=2)
        
        # Add two entries
        cache.put("key1", "value1")
        time.sleep(0.1)  # Ensure different timestamps
        cache.put("key2", "value2")
        
        # Access key1 multiple times to increase its weight
        for _ in range(5):
            cache.get("key1")
        
        # Add third entry - key2 should be evicted due to lower weight
        cache.put("key3", "value3")
        
        assert cache.contains("key1")  # High access count
        assert not cache.contains("key2")  # Should be evicted
        assert cache.contains("key3")  # Newest
        
    def test_weighted_cache_calculate_weight(self):
        cache = WeightedCache()
        
        # Create an entry and test weight calculation
        entry = CacheEntry(value="test", timestamp=time.time())
        weight1 = cache._calculate_weight(entry)
        
        # Access the entry and test weight increases
        entry.touch()
        weight2 = cache._calculate_weight(entry)
        
        assert weight2 > weight1
        
        # Test with older entry
        old_entry = CacheEntry(value="test", timestamp=time.time() - 100)
        old_weight = cache._calculate_weight(old_entry)
        
        assert old_weight < weight1  # Older entry has lower weight


class TestCacheIntegration:
    def test_cache_stress_test(self):
        cache = MemoryCache(max_size=100)
        
        # Fill cache beyond capacity
        for i in range(200):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Should have exactly max_size entries
        assert cache.size() == 100
        
        # Recent entries should still be there
        for i in range(100, 200):
            assert cache.contains(f"key_{i}")
            
    def test_cache_mixed_operations(self):
        cache = MemoryCache()
        
        # Mixed operations
        cache.put("key1", "value1")
        cache.put("key2", "value2", ttl=1.0)
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        cache.delete("key1")
        assert not cache.contains("key1")
        
        time.sleep(1.1)
        assert not cache.contains("key2")  # Expired
        
        stats = cache.get_stats()
        assert stats["hits"] >= 2
        assert stats["expirations"] >= 1