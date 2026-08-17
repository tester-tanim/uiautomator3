"""Global per-Device settings, accessed as `d.settings["key"]`.

Phase 7 added self_healing / self_healing_min_confidence. Phase 11 adds
hierarchy_cache_ttl / screenshot_cache_ttl (project spec section 49-50:
Performance / Caching) - set to 0 to disable caching for a given kind of
data. Later phases can extend this further the way uiautomator2's
Settings does (wait_timeout, operation_delay, ...) without changing the
access pattern.
"""
from typing import Any, Dict


class Settings:
    _DEFAULTS: Dict[str, Any] = {
        "self_healing": False,
        "self_healing_min_confidence": 0.85,
        "hierarchy_cache_ttl": 0.3,
        "screenshot_cache_ttl": 0.3,
    }

    def __init__(self) -> None:
        self._values: Dict[str, Any] = dict(self._DEFAULTS)

    def __getitem__(self, key: str) -> Any:
        if key not in self._values:
            raise KeyError(f"unknown setting: {key!r}")
        return self._values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in self._DEFAULTS:
            raise KeyError(f"unknown setting: {key!r}")
        expected_type = type(self._DEFAULTS[key])
        # bool is a subclass of int, so explicitly reject bools for numeric
        # settings; otherwise allow int where float is expected (0 is a
        # valid float-compatible value, e.g. to disable a TTL).
        if expected_type is float and isinstance(value, bool):
            raise TypeError(f"setting {key!r} expects float, got {type(value).__name__}")
        if expected_type is float and isinstance(value, int):
            value = float(value)
        elif not isinstance(value, expected_type):
            raise TypeError(f"setting {key!r} expects {expected_type.__name__}, got {type(value).__name__}")
        self._values[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._values

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)
