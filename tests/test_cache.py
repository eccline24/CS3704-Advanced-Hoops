"""
Unit tests for data/cache.py

Covers the TTLCache store and the @cached decorator:
  - miss / set / hit lifecycle
  - TTL expiry (via monkey-patching time.monotonic so tests don't sleep)
  - distinct arg keys, clear(), _cache_enabled bypass
"""

import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))

import cache as cache_module
from cache import TTLCache, cached, MISS


# ---------------------------------------------------------------------------
# TTLCache
# ---------------------------------------------------------------------------

class TestTTLCache:
    def test_get_returns_miss_sentinel_when_empty(self):
        c = TTLCache()
        assert c.get('nope') is MISS

    def test_set_then_get_returns_value(self):
        c = TTLCache()
        c.set('k', {'payload': 42}, ttl=60)
        assert c.get('k') == {'payload': 42}

    def test_none_value_is_cached_and_retrievable(self):
        c = TTLCache()
        c.set('k', None, ttl=60)
        assert c.get('k') is None
        assert c.get('k') is not MISS

    def test_expired_entry_returns_miss_and_is_evicted(self, monkeypatch):
        fake_now = [1000.0]
        monkeypatch.setattr(cache_module.time, 'monotonic', lambda: fake_now[0])

        c = TTLCache()
        c.set('k', 'value', ttl=5)
        assert c.get('k') == 'value'

        fake_now[0] = 1006.0  # past expiry
        assert c.get('k') is MISS
        assert c.size() == 0  # evicted on read

    def test_clear_empties_store(self):
        c = TTLCache()
        c.set('a', 1, ttl=60)
        c.set('b', 2, ttl=60)
        assert c.size() == 2
        c.clear()
        assert c.size() == 0
        assert c.get('a') is MISS

    def test_default_ttl_used_when_none_passed(self, monkeypatch):
        fake_now = [1000.0]
        monkeypatch.setattr(cache_module.time, 'monotonic', lambda: fake_now[0])

        c = TTLCache(default_ttl=10)
        c.set('k', 'v')  # no explicit ttl -> uses default 10
        fake_now[0] = 1011.0
        assert c.get('k') is MISS


# ---------------------------------------------------------------------------
# @cached decorator
# ---------------------------------------------------------------------------

class _Counter:
    """Dummy host class used to verify decorator behavior."""

    def __init__(self):
        self._cache = TTLCache()
        self._cache_enabled = True
        self.calls = 0

    @cached(ttl=60)
    def fetch(self, key: str, limit: int = 5) -> dict:
        self.calls += 1
        return {'key': key, 'limit': limit, 'call_num': self.calls}


class TestCachedDecorator:
    def test_first_call_invokes_underlying(self):
        host = _Counter()
        result = host.fetch('alice')
        assert host.calls == 1
        assert result['key'] == 'alice'

    def test_repeat_call_with_same_args_hits_cache(self):
        host = _Counter()
        first = host.fetch('alice')
        second = host.fetch('alice')
        assert host.calls == 1  # underlying only called once
        assert first == second

    def test_distinct_args_both_invoke_underlying(self):
        host = _Counter()
        host.fetch('alice')
        host.fetch('bob')
        assert host.calls == 2

    def test_distinct_kwargs_both_invoke_underlying(self):
        host = _Counter()
        host.fetch('alice', limit=5)
        host.fetch('alice', limit=10)
        assert host.calls == 2

    def test_cache_enabled_false_bypasses_cache(self):
        host = _Counter()
        host._cache_enabled = False
        host.fetch('alice')
        host.fetch('alice')
        assert host.calls == 2  # cache bypassed on both calls

    def test_clearing_cache_forces_re_execution(self):
        host = _Counter()
        host.fetch('alice')
        host._cache.clear()
        host.fetch('alice')
        assert host.calls == 2

    def test_ttl_expiry_forces_re_execution(self, monkeypatch):
        fake_now = [1000.0]
        monkeypatch.setattr(cache_module.time, 'monotonic', lambda: fake_now[0])

        host = _Counter()
        host.fetch('alice')
        assert host.calls == 1

        fake_now[0] = 1061.0  # past the 60s TTL
        host.fetch('alice')
        assert host.calls == 2
