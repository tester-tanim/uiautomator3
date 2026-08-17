import time

from uiautomator3.utils.ttl_cache import TTLCache


def test_get_returns_none_when_never_set():
    cache = TTLCache(ttl=1.0)
    assert cache.get() is None


def test_set_and_get_within_ttl():
    cache = TTLCache(ttl=1.0)
    cache.set("value")
    assert cache.get() == "value"


def test_get_returns_none_after_ttl_expires():
    cache = TTLCache(ttl=0.05)
    cache.set("value")
    time.sleep(0.1)
    assert cache.get() is None


def test_invalidate_clears_value():
    cache = TTLCache(ttl=1.0)
    cache.set("value")
    cache.invalidate()
    assert cache.get() is None


def test_get_or_compute_calls_compute_once_within_ttl():
    cache = TTLCache(ttl=1.0)
    calls = []

    def compute():
        calls.append(1)
        return "computed"

    result1 = cache.get_or_compute(compute)
    result2 = cache.get_or_compute(compute)

    assert result1 == "computed"
    assert result2 == "computed"
    assert len(calls) == 1


def test_get_or_compute_recomputes_after_expiry():
    cache = TTLCache(ttl=0.05)
    calls = []

    def compute():
        calls.append(1)
        return f"computed-{len(calls)}"

    cache.get_or_compute(compute)
    time.sleep(0.1)
    cache.get_or_compute(compute)

    assert len(calls) == 2


def test_ttl_can_be_changed_after_construction():
    cache = TTLCache(ttl=10.0)
    cache.set("value")
    cache.ttl = 0.0
    assert cache.get() is None
