"""Tests for caching utilities."""

from __future__ import annotations

import threading
import time

import pytest

from glazing.utils.cache import (
    LRUCache,
    PersistentCache,
    QueryCache,
    TTLCache,
    cached_method,
    clear_all_caches,
    generate_cache_key,
    set_caching_enabled,
)


class TestLRUCache:
    """Test the LRU cache implementation."""

    def test_basic_operations(self):
        """Test basic get and put operations."""
        cache: LRUCache[str] = LRUCache(max_size=3)

        # Test put and get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"

        # Test missing key
        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache: LRUCache[int] = LRUCache(max_size=3)

        # Fill cache
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)

        # Access 'a' to make it recently used
        assert cache.get("a") == 1

        # Add new item, should evict 'b' (least recently used)
        cache.put("d", 4)

        assert cache.get("a") == 1  # Still in cache
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") == 3  # Still in cache
        assert cache.get("d") == 4  # Newly added

    def test_update_existing(self):
        """Test updating existing entries."""
        cache: LRUCache[str] = LRUCache(max_size=3)

        cache.put("key", "value1")
        assert cache.get("key") == "value1"

        cache.put("key", "value2")
        assert cache.get("key") == "value2"
        assert cache.size() == 1  # Still only one entry

    def test_statistics(self):
        """Test cache statistics."""
        cache: LRUCache[str] = LRUCache(max_size=3)

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # Generate some hits and misses
        assert cache.get("key1") == "value1"  # Hit
        assert cache.get("key1") == "value1"  # Hit
        assert cache.get("missing") is None  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_requests"] == 3
        assert stats["hit_rate"] == 2 / 3
        assert stats["size"] == 2
        assert stats["max_size"] == 3

    def test_clear(self):
        """Test clearing the cache."""
        cache: LRUCache[str] = LRUCache(max_size=3)

        cache.put("key1", "value1")
        cache.put("key2", "value2")
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None  # This will increment misses
        assert cache.hits == 0
        assert cache.misses == 1  # One miss from the get after clear

    def test_contains(self):
        """Test containment check."""
        cache: LRUCache[str] = LRUCache(max_size=3)

        cache.put("key", "value")
        assert "key" in cache
        assert "missing" not in cache

    def test_thread_safety(self):
        """Test thread-safe operations."""
        cache: LRUCache[int] = LRUCache(max_size=100)
        errors = []

        def worker(start: int):
            try:
                for i in range(start, start + 10):
                    cache.put(f"key{i}", i)
                    assert cache.get(f"key{i}") == i
            except AssertionError as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i * 10,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestTTLCache:
    """Test the TTL cache implementation."""

    def test_basic_operations(self):
        """Test basic operations with TTL."""
        cache: TTLCache[str] = TTLCache(max_size=10, ttl=1.0)

        cache.put("key", "value")
        assert cache.get("key") == "value"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_custom_ttl(self):
        """Test custom TTL per entry."""
        cache: TTLCache[str] = TTLCache(max_size=10, ttl=10.0)

        # Use shorter TTL for this entry
        cache.put("key", "value", ttl=0.5)
        assert cache.get("key") == "value"

        time.sleep(0.6)
        assert cache.get("key") is None

    def test_cleanup(self):
        """Test manual cleanup of expired entries."""
        cache: TTLCache[int] = TTLCache(max_size=10, ttl=0.5)

        cache.put("key1", 1)
        cache.put("key2", 2)
        cache.put("key3", 3)

        time.sleep(0.6)

        # Entries still in cache but expired
        removed = cache.cleanup()
        assert removed == 3
        assert cache.size() == 0

    def test_max_size_eviction(self):
        """Test eviction when max size reached."""
        cache: TTLCache[int] = TTLCache(max_size=3, ttl=10.0)

        cache.put("a", 1)
        time.sleep(0.1)
        cache.put("b", 2)
        time.sleep(0.1)
        cache.put("c", 3)
        time.sleep(0.1)

        # Adding fourth item should evict oldest
        cache.put("d", 4)

        # 'a' should be evicted (oldest)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4


class TestQueryCache:
    """Test the query cache implementation."""

    def test_query_caching(self):
        """Test caching query results."""
        cache = QueryCache(max_size=10, ttl=1.0)

        # Cache a query result
        cache.cache_query_result(
            "frame_by_lemma", {"lemma": "abandon", "pos": "v"}, ["frame1", "frame2"]
        )

        # Retrieve cached result
        result = cache.get_query_result("frame_by_lemma", {"lemma": "abandon", "pos": "v"})
        assert result == ["frame1", "frame2"]

        # Different params should miss
        result2 = cache.get_query_result("frame_by_lemma", {"lemma": "give", "pos": "v"})
        assert result2 is None

    def test_query_type_invalidation(self):
        """Test invalidating queries by type."""
        cache = QueryCache(max_size=10, ttl=10.0)

        cache.cache_query_result("frame_by_lemma", {"lemma": "abandon"}, ["frame1"])
        cache.cache_query_result("frame_by_id", {"id": 123}, "frame123")

        # Invalidate all frame_by_lemma queries - not yet implemented
        with pytest.raises(NotImplementedError) as exc_info:
            cache.invalidate_query_type("frame_by_lemma")

        assert "frame_by_lemma" in str(exc_info.value)
        assert "not yet implemented" in str(exc_info.value)

    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = QueryCache(max_size=10, ttl=10.0)

        cache.cache_query_result("test", {"a": 1}, "result")
        stats = cache.get_stats()

        assert "lru_stats" in stats
        assert "ttl_size" in stats
        assert "total_size" in stats


class TestPersistentCache:
    """Test the persistent file-based cache."""

    def test_json_serialization(self, tmp_path):
        """Test JSON-based persistent cache."""
        cache = PersistentCache(tmp_path / "cache", serializer="json")

        # Store and retrieve
        cache.put("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

        # Missing key
        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_pickle_serialization(self, tmp_path):
        """Test pickle-based persistent cache."""
        cache = PersistentCache(tmp_path / "cache", serializer="pickle")

        # Store complex object
        data = {"list": [1, 2, 3], "tuple": (4, 5), "set": {6, 7}}
        cache.put("complex", data)

        result = cache.get("complex")
        assert result["list"] == [1, 2, 3]
        assert result["tuple"] == (4, 5)
        assert result["set"] == {6, 7}

    def test_persistence(self, tmp_path):
        """Test that cache persists across instances."""
        cache_dir = tmp_path / "cache"

        # First instance
        cache1 = PersistentCache(cache_dir, serializer="json")
        cache1.put("persistent", "data")

        # Second instance
        cache2 = PersistentCache(cache_dir, serializer="json")
        assert cache2.get("persistent") == "data"

    def test_clear(self, tmp_path):
        """Test clearing persistent cache."""
        cache = PersistentCache(tmp_path / "cache", serializer="json")

        cache.put("key1", "value1")
        cache.put("key2", "value2")
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None

    def test_corrupted_cache(self, tmp_path):
        """Test handling corrupted cache files."""
        cache_dir = tmp_path / "cache"
        cache = PersistentCache(cache_dir, serializer="json")

        # Create corrupted cache file
        cache_path = cache._get_cache_path("corrupted")
        cache_path.write_text("not valid json")

        # Should return default, not crash
        assert cache.get("corrupted", "default") == "default"

        # Corrupted file should be removed
        assert not cache_path.exists()


class TestCacheUtilities:
    """Test cache utility functions."""

    def test_generate_cache_key(self):
        """Test cache key generation."""
        # Same arguments should generate same key
        key1 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        assert key1 == key2

        # Different arguments should generate different keys
        key3 = generate_cache_key("arg1", "arg3", kwarg1="value1")
        assert key1 != key3

        # Order of kwargs shouldn't matter
        key4 = generate_cache_key(a=1, b=2)
        key5 = generate_cache_key(b=2, a=1)
        assert key4 == key5

    def test_cached_method_decorator(self):
        """Test the cached_method decorator."""
        call_count = 0

        @cached_method(ttl=1.0)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x**2

        # First call computes
        assert expensive_function(5) == 25
        assert call_count == 1

        # Second call uses cache
        assert expensive_function(5) == 25
        assert call_count == 1

        # Different argument computes
        assert expensive_function(3) == 9
        assert call_count == 2

        # Wait for TTL expiration
        time.sleep(1.1)
        assert expensive_function(5) == 25
        assert call_count == 3

    def test_clear_all_caches(self):
        """Test clearing all registered caches."""
        cache1 = LRUCache[str](max_size=10)
        cache2 = TTLCache[str](max_size=10, ttl=10.0)

        cache1.put("key", "value")
        cache2.put("key", "value")

        count = clear_all_caches()
        assert count >= 2  # At least our two caches

        assert cache1.size() == 0
        assert cache2.size() == 0

    def test_global_caching_toggle(self):
        """Test enabling/disabling caching globally."""
        cache = LRUCache[str](max_size=10)

        # Caching enabled
        set_caching_enabled(True)
        cache.put("key", "value")
        assert cache.get("key") == "value"

        # Disable caching
        set_caching_enabled(False)
        cache.put("key2", "value2")
        assert cache.get("key2") is None  # Not cached

        # Re-enable
        set_caching_enabled(True)
        cache.put("key3", "value3")
        assert cache.get("key3") == "value3"
