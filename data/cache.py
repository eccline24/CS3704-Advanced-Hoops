"""
In-memory TTL cache for DataService.

TTLCache stores values keyed by an arbitrary string, each with an expiry time
measured against time.monotonic() so wall-clock jumps (NTP sync, DST) cannot
prematurely expire or extend entries.

The `cached` decorator wraps a bound method and caches its return value on the
instance's `_cache` attribute. Each DataService instance therefore gets its own
isolated cache, which also keeps unit tests naturally independent.
"""

import functools
import time
from typing import Any, Callable, Optional


MISS = object()


class TTLCache:
    def __init__(self, default_ttl: int = 3600):
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return MISS
        value, expires_at = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            return MISS
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        effective_ttl = self._default_ttl if ttl is None else ttl
        self._store[key] = (value, time.monotonic() + effective_ttl)

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)


def cached(ttl: int = 3600) -> Callable:
    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not getattr(self, '_cache_enabled', True):
                return method(self, *args, **kwargs)

            key = f"{method.__name__}:{args}:{tuple(sorted(kwargs.items()))}"
            hit = self._cache.get(key)
            if hit is not MISS:
                return hit

            value = method(self, *args, **kwargs)
            self._cache.set(key, value, ttl)
            return value
        return wrapper
    return decorator
