"""Gesture engine.

Phase 2 scope: tap, long press, swipe, drag, key events, multi-point swipe.
Built directly on adbutils' `input`/`sendevent`-backed primitives (click,
swipe, drag, keyevent) rather than a device-side agent, since a JSON-RPC
agent is not required until Phase 3+ (hierarchy/selectors). This mirrors
uiautomator2's app-management design lesson (see
docs/UIAUTOMATOR2_ANALYSIS.md section 10): keep basic device control
working over plain ADB, independent of any richer server process.

True multi-touch (independent simultaneous pointers) is out of scope here -
adb `input swipe`/`input tap` are single-pointer. Multi-touch gestures
(pinch, two-finger scroll) require the device-side agent and are deferred
to a later phase per docs/UIAUTOMATOR3_ARCHITECTURE.md.
"""

from typing import TYPE_CHECKING, List, Tuple, Union

from uiautomator3.exceptions import AdbError
from uiautomator3.logging_config import get_logger

if TYPE_CHECKING:
    import adbutils

logger = get_logger("gestures")

# Common Android key names not directly exposed by adbutils.AdbDevice.keyevent
# as convenience strings; mapped to their KEYCODE_* integer values.
_KEY_NAME_TO_CODE = {
    "home": 3,
    "back": 4,
    "call": 5,
    "endcall": 6,
    "volume_up": 24,
    "volume_down": 25,
    "power": 26,
    "camera": 27,
    "menu": 82,
    "search": 84,
    "enter": 66,
    "delete": 67,
    "recent": 187,
    "recents": 187,
    "app_switch": 187,
}


class GestureEngine:
    """Tap / long-press / swipe / drag / key-event gestures for a single device."""

    def __init__(self, adb_device: "adbutils.AdbDevice") -> None:
        self._adb_device = adb_device

    def tap(self, x: int, y: int) -> None:
        try:
            self._adb_device.click(x, y)
        except Exception as e:
            raise AdbError(f"tap({x}, {y}) failed: {e}") from e

    def long_press(self, x: int, y: int, duration: float = 1.0) -> None:
        """Long press by holding a swipe in place for `duration` seconds."""
        self.swipe((x, y), (x, y), duration=duration)

    def swipe(self, start: Tuple[int, int], end: Tuple[int, int], *, duration: float = 0.5) -> None:
        """Swipe from `start` to `end`, e.g. ``swipe((x1, y1), (x2, y2))``."""
        sx, sy = start
        ex, ey = end
        try:
            self._adb_device.swipe(sx, sy, ex, ey, duration=duration)
        except Exception as e:
            raise AdbError(f"swipe({sx},{sy} -> {ex},{ey}) failed: {e}") from e

    def swipe_points(self, points: List[Tuple[int, int]], duration: float = 0.5) -> None:
        """Swipe through a path of points by issuing sequential two-point swipes."""
        if len(points) < 2:
            raise ValueError("swipe_points requires at least 2 points")
        per_segment = duration / (len(points) - 1)
        for (sx, sy), (ex, ey) in zip(points, points[1:]):
            self.swipe((sx, sy), (ex, ey), duration=per_segment)

    def drag(self, source: Tuple[int, int], target: Tuple[int, int], duration: float = 0.5) -> None:
        sx, sy = source
        ex, ey = target
        try:
            self._adb_device.drag(sx, sy, ex, ey, duration=duration)
        except Exception as e:
            raise AdbError(f"drag({sx},{sy} -> {ex},{ey}) failed: {e}") from e

    def press(self, key: Union[str, int]) -> None:
        """Press a key by name (e.g. 'home', 'back') or raw keycode."""
        code: Union[str, int]
        if isinstance(key, str) and key.lower() in _KEY_NAME_TO_CODE:
            code = _KEY_NAME_TO_CODE[key.lower()]
        else:
            code = key
        try:
            self._adb_device.keyevent(code)
        except Exception as e:
            raise AdbError(f"press({key!r}) failed: {e}") from e

    def long_press_key(self, key: Union[str, int]) -> None:
        code = _KEY_NAME_TO_CODE.get(key.lower(), key) if isinstance(key, str) else key
        try:
            self._adb_device.shell(f"input keyevent --longpress {code}")
        except Exception as e:
            raise AdbError(f"long_press_key({key!r}) failed: {e}") from e
