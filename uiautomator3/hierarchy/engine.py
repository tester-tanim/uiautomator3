"""Hierarchy engine: collect + parse in one call.

This is the entry point Device.dump_hierarchy()/Device.inspect() use.

Phase 11 adds a short TTL cache (project spec section 49-50) on the parsed
ElementTree: repeated calls within the TTL window return the same
snapshot instead of re-dumping (a real ~2s ADB round-trip was measured
during Phase 3 device testing). The TTL is read from Settings on every
call (not fixed at construction) so `d.settings["hierarchy_cache_ttl"]`
takes effect immediately; set it to 0 to disable caching entirely. Every
gesture/selector action on Device invalidates the cache immediately after
acting (see device/device.py), since the UI has likely changed.
"""
from typing import TYPE_CHECKING, Optional

from uiautomator3.elements.tree import ElementTree
from uiautomator3.hierarchy.collector import HierarchyCollector
from uiautomator3.hierarchy.parser import parse_hierarchy
from uiautomator3.utils.ttl_cache import TTLCache

if TYPE_CHECKING:
    import adbutils


class HierarchyEngine:
    def __init__(self, adb_device: "adbutils.AdbDevice") -> None:
        self._collector = HierarchyCollector(adb_device)
        self._cache: TTLCache[ElementTree] = TTLCache(ttl=0.3)

    def dump_xml(self) -> str:
        """Return the raw hierarchy XML string. Always fresh - not cached,
        since callers of the raw XML typically want the literal current
        state (e.g. `u3 dump`)."""
        return self._collector.dump()

    def dump(self, force: bool = False, ttl: Optional[float] = None) -> ElementTree:
        """Dump and parse the current hierarchy into an ElementTree.

        Returns a cached snapshot if one was taken within `ttl` seconds
        (default: whatever ttl was last configured, initially 0.3s) and
        `force` is False.
        """
        if ttl is not None:
            self._cache.ttl = ttl
        if force:
            self._cache.invalidate()

        def compute() -> ElementTree:
            xml_data = self._collector.dump()
            return parse_hierarchy(xml_data)

        return self._cache.get_or_compute(compute)

    def invalidate(self) -> None:
        self._cache.invalidate()
