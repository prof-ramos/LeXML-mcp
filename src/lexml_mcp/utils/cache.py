"""LRU cache with configurable TTL.

ponytail: OrderedDict-based, single global lock. Per-key TTL via monotonic clock.
Upgrade to sharded or disk-backed cache when throughput exceeds ~10k req/s.
"""

import time
from collections import OrderedDict
from threading import Lock
from typing import Any


class TTLCache:
    """Thread-safe LRU cache with per-key TTL expiry."""

    def __init__(self, maxsize: int = 256, ttl: float = 300):
        self._maxsize = maxsize
        self._ttl = ttl
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            if key not in self._store:
                return None
            expires_at, value = self._store[key]
            if now > expires_at:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        now = time.monotonic()
        with self._lock:
            self._store[key] = (now + self._ttl, value)
            self._store.move_to_end(key)
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()