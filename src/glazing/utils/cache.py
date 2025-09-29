"""Caching utilities for the glazing package.

This module provides caching mechanisms for query results and cross-reference
resolution to improve performance when working with large linguistic datasets.

Classes
-------
LRUCache
    Thread-safe Least Recently Used cache implementation.
TTLCache
    Time-To-Live cache with automatic expiration.
QueryCache
    Specialized cache for dataset queries.
PersistentCache
    Optional file-based persistent cache.

Functions
---------
generate_cache_key
    Generate a unique cache key from function arguments.
cached_method
    Decorator for caching method results.
clear_all_caches
    Clear all active caches in the application.

Notes
-----
The caching system is designed to be thread-safe and can handle concurrent
access from multiple threads. All caches can be disabled globally for testing
or debugging purposes.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import threading
import time
import weakref
from collections import OrderedDict
from collections.abc import Callable, Hashable
from functools import wraps
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")

type CacheValue = (
    str
    | int
    | float
    | bool
    | None
    | list[CacheValue]
    | dict[str, CacheValue]
    | tuple[CacheValue, ...]
)
type QueryParams = dict[
    str, str | int | float | bool | None | list[QueryParams] | dict[str, QueryParams]
]

# Global cache registry for management
_cache_registry: weakref.WeakSet[CacheBase] = weakref.WeakSet()

# Global flag to disable caching
CACHING_ENABLED = True


class CacheBase:
    """Base class for all cache implementations.

    Provides common interface and registration for cache management.
    """

    def __init__(self) -> None:
        """Initialize and register the cache."""
        _cache_registry.add(self)

    def clear(self) -> None:
        """Clear all entries from the cache."""
        # Default implementation does nothing

    def size(self) -> int:
        """Get the number of entries in the cache."""
        return 0  # Default implementation returns 0

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return CACHING_ENABLED


class LRUCache[T](CacheBase):
    """Thread-safe Least Recently Used cache.

    Parameters
    ----------
    max_size : int
        Maximum number of entries to store.

    Attributes
    ----------
    hits : int
        Number of cache hits.
    misses : int
        Number of cache misses.

    Methods
    -------
    get(key, default=None)
        Get a value from the cache.
    put(key, value)
        Store a value in the cache.
    clear()
        Clear all entries.
    get_stats()
        Get cache statistics.

    Examples
    --------
    >>> cache = LRUCache[str](max_size=100)
    >>> cache.put("key1", "value1")
    >>> value = cache.get("key1")
    >>> print(cache.get_stats())
    """

    def __init__(self, max_size: int = 128) -> None:
        """Initialize the LRU cache."""
        super().__init__()
        self.max_size = max_size
        self._cache: OrderedDict[Hashable, T] = OrderedDict()
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Hashable, default: T | None = None) -> T | None:
        """Get a value from the cache.

        Parameters
        ----------
        key : Hashable
            The cache key.
        default : T | None
            Default value if key not found.

        Returns
        -------
        T | None
            The cached value or default.
        """
        if not self.is_enabled():
            return default

        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self.hits += 1
                return self._cache[key]
            self.misses += 1
            return default

    def put(self, key: Hashable, value: T) -> None:
        """Store a value in the cache.

        Parameters
        ----------
        key : Hashable
            The cache key.
        value : T
            The value to cache.
        """
        if not self.is_enabled():
            return

        with self._lock:
            if key in self._cache:
                # Update existing entry
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                # Add new entry
                self._cache[key] = value
                # Remove oldest if over capacity
                if len(self._cache) > self.max_size:
                    self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def size(self) -> int:
        """Get the number of entries in the cache."""
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> dict[str, int | float]:
        """Get cache statistics.

        Returns
        -------
        dict[str, int | float]
            Cache statistics including hits, misses, and hit rate.
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "size": self.size(),
            "max_size": self.max_size,
        }

    def __contains__(self, key: Hashable) -> bool:
        """Check if a key is in the cache."""
        with self._lock:
            return key in self._cache


class TTLCache[T](CacheBase):
    """Time-To-Live cache with automatic expiration.

    Parameters
    ----------
    max_size : int
        Maximum number of entries.
    ttl : float
        Time-to-live in seconds for each entry.

    Methods
    -------
    get(key, default=None)
        Get a value if not expired.
    put(key, value, ttl=None)
        Store a value with optional custom TTL.
    cleanup()
        Remove expired entries.

    Examples
    --------
    >>> cache = TTLCache[str](max_size=100, ttl=60.0)
    >>> cache.put("key1", "value1")
    >>> time.sleep(61)
    >>> cache.get("key1")  # Returns None (expired)
    """

    def __init__(self, max_size: int = 128, ttl: float = 300.0) -> None:
        """Initialize the TTL cache."""
        super().__init__()
        self.max_size = max_size
        self.default_ttl = ttl
        self._cache: dict[Hashable, tuple[T, float]] = {}
        self._lock = threading.RLock()

    def get(self, key: Hashable, default: T | None = None) -> T | None:
        """Get a value if not expired.

        Parameters
        ----------
        key : Hashable
            The cache key.
        default : T | None
            Default value if key not found or expired.

        Returns
        -------
        T | None
            The cached value or default.
        """
        if not self.is_enabled():
            return default

        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    return value
                # Remove expired entry
                del self._cache[key]
            return default

    def put(self, key: Hashable, value: T, ttl: float | None = None) -> None:
        """Store a value with TTL.

        Parameters
        ----------
        key : Hashable
            The cache key.
        value : T
            The value to cache.
        ttl : float | None
            Custom TTL in seconds, or use default.
        """
        if not self.is_enabled():
            return

        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl

        with self._lock:
            self._cache[key] = (value, expiry)

            # Remove oldest if over capacity
            if len(self._cache) > self.max_size:
                self._evict_oldest()

    def _evict_oldest(self) -> None:
        """Evict the oldest entry."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]

    def cleanup(self) -> int:
        """Remove expired entries.

        Returns
        -------
        int
            Number of entries removed.
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items() if current_time >= expiry
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get the number of entries."""
        with self._lock:
            # Clean up expired entries first
            self.cleanup()
            return len(self._cache)


class QueryCache(CacheBase):
    """Specialized cache for dataset queries.

    Combines LRU and TTL strategies for optimal query caching.

    Parameters
    ----------
    max_size : int
        Maximum number of cached queries.
    ttl : float
        Time-to-live for query results.

    Methods
    -------
    get_query_result(query_type, params)
        Get cached query result.
    cache_query_result(query_type, params, result)
        Cache a query result.
    invalidate_query_type(query_type)
        Invalidate all queries of a specific type.
    """

    def __init__(self, max_size: int = 256, ttl: float = 600.0) -> None:
        """Initialize the query cache."""
        super().__init__()
        self._lru_cache = LRUCache[CacheValue](max_size=max_size)
        self._ttl_cache = TTLCache[CacheValue](max_size=max_size, ttl=ttl)

    def get_query_result(self, query_type: str, params: QueryParams) -> CacheValue | None:
        """Get cached query result.

        Parameters
        ----------
        query_type : str
            Type of query (e.g., "frame_by_lemma").
        params : QueryParams
            Query parameters.

        Returns
        -------
        CacheValue | None
            Cached result or None.
        """
        key = self._generate_query_key(query_type, params)

        # Check TTL cache first
        result = self._ttl_cache.get(key)
        if result is not None:
            return result

        # Fall back to LRU cache
        return self._lru_cache.get(key)

    def cache_query_result(
        self, query_type: str, params: QueryParams, result: CacheValue, ttl: float | None = None
    ) -> None:
        """Cache a query result.

        Parameters
        ----------
        query_type : str
            Type of query.
        params : QueryParams
            Query parameters.
        result : CacheValue
            Query result to cache.
        ttl : float | None
            Custom TTL for this result.
        """
        key = self._generate_query_key(query_type, params)

        # Store in both caches
        self._lru_cache.put(key, result)
        self._ttl_cache.put(key, result, ttl)

    def invalidate_query_type(self, query_type: str) -> None:
        """Invalidate all queries of a specific type.

        Parameters
        ----------
        query_type : str
            Type of query to invalidate.
        """
        msg = (
            f"Query type '{query_type}' invalidation not yet implemented. "
            "This method requires implementing key categorization by query type to "
            "selectively invalidate cached queries."
        )
        raise NotImplementedError(msg)

    def _generate_query_key(self, query_type: str, params: QueryParams) -> str:
        """Generate a unique key for a query."""
        key_data = {"type": query_type, "params": params}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()  # noqa: S324

    def clear(self) -> None:
        """Clear all cached queries."""
        self._lru_cache.clear()
        self._ttl_cache.clear()

    def size(self) -> int:
        """Get total number of cached entries."""
        return self._lru_cache.size() + self._ttl_cache.size()

    def get_stats(self) -> dict[str, int | float | dict[str, int | float]]:
        """Get combined cache statistics."""
        return {
            "lru_stats": self._lru_cache.get_stats(),
            "ttl_size": self._ttl_cache.size(),
            "total_size": self.size(),
        }


class PersistentCache(CacheBase):
    """File-based persistent cache.

    Parameters
    ----------
    cache_dir : Path | str
        Directory to store cache files.
    serializer : str
        Serialization method ("json" or "pickle").

    Methods
    -------
    get(key, default=None)
        Get a value from persistent storage.
    put(key, value)
        Store a value persistently.
    """

    def __init__(self, cache_dir: Path | str, serializer: str = "json") -> None:
        """Initialize the persistent cache."""
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.serializer = serializer
        self._lock = threading.RLock()

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Hash the key to create a valid filename
        key_hash = hashlib.md5(key.encode()).hexdigest()  # noqa: S324
        extension = ".json" if self.serializer == "json" else ".pkl"
        return self.cache_dir / f"{key_hash}{extension}"

    def get(self, key: str, default: T | None = None) -> T | None:
        """Get a value from persistent storage.

        Parameters
        ----------
        key : str
            The cache key.
        default : T | None
            Default value if not found.

        Returns
        -------
        T | None
            The cached value or default.
        """
        if not self.is_enabled():
            return default

        with self._lock:
            cache_path = self._get_cache_path(key)

            if not cache_path.exists():
                return default

            try:
                if self.serializer == "json":
                    with cache_path.open("r") as f:
                        return json.load(f)  # type: ignore[no-any-return]
                else:
                    with cache_path.open("rb") as f:
                        return pickle.load(f)  # type: ignore[no-any-return]  # noqa: S301
            except (json.JSONDecodeError, OSError, ValueError):
                # Corrupted cache file
                cache_path.unlink(missing_ok=True)
                return default

    def put(self, key: str, value: T) -> None:
        """Store a value persistently.

        Parameters
        ----------
        key : str
            The cache key.
        value : T
            The value to cache.
        """
        if not self.is_enabled():
            return

        with self._lock:
            cache_path = self._get_cache_path(key)

            try:
                if self.serializer == "json":
                    with cache_path.open("w") as f:
                        json.dump(value, f)
                else:
                    with cache_path.open("wb") as f:
                        pickle.dump(value, f)
            except (OSError, TypeError):
                # Failed to write cache
                cache_path.unlink(missing_ok=True)

    def clear(self) -> None:
        """Clear all cache files."""
        with self._lock:
            for cache_file in self.cache_dir.glob("*"):
                if cache_file.is_file():
                    cache_file.unlink()

    def size(self) -> int:
        """Get the number of cache files."""
        with self._lock:
            return len(list(self.cache_dir.glob("*")))


def generate_cache_key(*args, **kwargs) -> str:  # type: ignore[no-untyped-def]
    """Generate a unique cache key from function arguments.

    Parameters
    ----------
    *args
        Positional arguments.
    **kwargs
        Keyword arguments.

    Returns
    -------
    str
        A unique cache key.
    """
    key_data = {"args": args, "kwargs": kwargs}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()  # noqa: S324


def cached_method(
    cache: CacheBase | None = None, ttl: float | None = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for caching method results.

    Parameters
    ----------
    cache : CacheBase | None
        Cache instance to use, or create LRU cache.
    ttl : float | None
        Time-to-live for cached results.

    Returns
    -------
    Callable[[Callable[..., T]], Callable[..., T]]
        Decorator that adds caching to a function.

    Examples
    --------
    >>> @cached_method(ttl=60.0)
    ... def expensive_function(x: int) -> int:
    ...     return x ** 2
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Create default cache if not provided
        nonlocal cache
        if cache is None:
            cache = TTLCache(ttl=ttl) if ttl is not None else LRUCache()

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:  # type: ignore[no-untyped-def]
            # Generate cache key
            key = generate_cache_key(*args, **kwargs)

            # Check cache
            if isinstance(cache, TTLCache | LRUCache):
                result = cache.get(key)
            else:
                result = cache.get(key) if hasattr(cache, "get") else None

            if result is not None:
                return result  # type: ignore[no-any-return]

            # Compute result
            result = func(*args, **kwargs)

            # Store in cache
            if isinstance(cache, TTLCache):
                cache.put(key, result, ttl)
            elif isinstance(cache, LRUCache) or hasattr(cache, "put"):
                cache.put(key, result)

            return result

        # Attach cache for inspection
        wrapper.cache = cache  # type: ignore[attr-defined]
        return wrapper

    return decorator


def clear_all_caches() -> int:
    """Clear all active caches in the application.

    Returns
    -------
    int
        Number of caches cleared.
    """
    count = 0
    for cache in _cache_registry:
        try:
            cache.clear()
            count += 1
        except (OSError, ValueError):
            pass
    return count


def set_caching_enabled(enabled: bool) -> None:
    """Enable or disable all caching globally.

    Parameters
    ----------
    enabled : bool
        Whether caching should be enabled.
    """
    global CACHING_ENABLED
    CACHING_ENABLED = enabled

    if not enabled:
        clear_all_caches()
