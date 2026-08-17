"""Screenshot capture.

Phase 2 scope: capture via `adb screencap` (through adbutils, which already
returns a decoded PIL.Image), with save-to-disk and format conversion.
Device-side JPEG-encoded fast screenshots (uiautomator2's primary path, see
docs/UIAUTOMATOR2_ANALYSIS.md section 7) require the device-side agent and
are deferred to the phase that introduces it; adb screencap is the
documented fallback path there and is sufficient for Phase 2.

Phase 11 adds a short TTL cache per display_id (project spec section
49-50), invalidated automatically after any Device gesture/action (see
device/device.py).
"""
from typing import TYPE_CHECKING, Dict, Optional

from uiautomator3.exceptions import AdbError
from uiautomator3.logging_config import get_logger
from uiautomator3.utils.ttl_cache import TTLCache

if TYPE_CHECKING:
    import adbutils
    from PIL import Image

logger = get_logger("screenshots")


class ScreenshotEngine:
    """Screen capture for a single device."""

    def __init__(self, adb_device: "adbutils.AdbDevice") -> None:
        self._adb_device = adb_device
        self._caches: Dict[Optional[int], TTLCache] = {}

    def _cache_for(self, display_id: Optional[int]) -> TTLCache:
        if display_id not in self._caches:
            self._caches[display_id] = TTLCache(ttl=0.3)
        return self._caches[display_id]

    def capture(self, display_id: Optional[int] = None, force: bool = False, ttl: Optional[float] = None) -> "Image.Image":
        """Return a full-screen capture as a PIL Image.

        Returns a cached capture for the same `display_id` if one was
        taken within `ttl` seconds and `force` is False.
        """
        cache = self._cache_for(display_id)
        if ttl is not None:
            cache.ttl = ttl
        if force:
            cache.invalidate()

        def compute() -> "Image.Image":
            try:
                return self._adb_device.screenshot(display_id=display_id, error_ok=False)
            except Exception as e:
                raise AdbError(f"screenshot failed: {e}") from e

        return cache.get_or_compute(compute)

    def save(self, path: str, display_id: Optional[int] = None) -> str:
        """Capture the screen and save it to `path`. Returns the path."""
        image = self.capture(display_id=display_id)
        image.save(path)
        return path

    def region(self, left: int, top: int, right: int, bottom: int, display_id: Optional[int] = None) -> "Image.Image":
        """Capture the screen and crop to the given pixel bounds."""
        image = self.capture(display_id=display_id)
        return image.crop((left, top, right, bottom))

    def invalidate(self) -> None:
        for cache in self._caches.values():
            cache.invalidate()
