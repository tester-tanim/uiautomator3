"""A minimal single-value TTL cache.

Not a general-purpose caching framework - just enough to hold "the last
hierarchy dump" / "the last screenshot" for a short, configurable window,
per project spec section 49-50 (Performance Requirements / Caching):
back-to-back calls within the same UI state shouldn't each pay a fresh
adb round-trip.
"""

import time
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Holds one cached value, valid for `ttl` seconds after it was set."""

    def __init__(self, ttl: float = 0.3) -> None:
        self.ttl = ttl
        self._value: Optional[T] = None
        self._set_at: Optional[float] = None

    def get(self) -> Optional[T]:
        if self._set_at is None:
            return None
        if time.time() - self._set_at > self.ttl:
            return None
        return self._value

    def set(self, value: T) -> None:
        self._value = value
        self._set_at = time.time()

    def invalidate(self) -> None:
        self._value = None
        self._set_at = None

    def get_or_compute(self, compute: Callable[[], T]) -> T:
        cached = self.get()
        if cached is not None:
            return cached
        value = compute()
        self.set(value)
        return value
