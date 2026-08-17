"""Device abstraction.

Phase 1: identity, connectivity, basic health check.
Phase 2 adds: gestures (tap/swipe/drag/keys), screenshots, app management,
and a device info snapshot - all layered on top of the Phase 1 transport,
still with no device-side agent (see docs/UIAUTOMATOR3_ARCHITECTURE.md
section 16).
Phase 3 adds: hierarchy dumping and the normalized UIElement tree.
Phase 5 adds: d(...)/d.find(...)/d.locator(...) selector queries and
d.analyze_locator() locator stability analysis.
Phase 6 adds: d.ocr(...) and d.visual(...)/d.find_visual(...), both lazy -
no OCR/vision dependency is imported unless these are actually called
(see docs/UIAUTOMATOR3_ARCHITECTURE.md sections 9-10).
Phase 7 adds: d.settings (currently just self_healing / min confidence) -
opt-in automatic locator recovery on ElementNotFoundError, see
docs/UIAUTOMATOR3_ARCHITECTURE.md section 7.
Phase 8 adds: d.start_recording()/stop_recording() - gesture and selector
actions log themselves to the active RecordingSession as a side effect
(see project spec section 18); recording is off by default and adds no
overhead when inactive.
Phase 10 adds: d.ai - structured, LLM-free element description/matching
for AI agents (project spec section 39); no external model is required
or called.
Phase 11 adds: short-TTL caching of hierarchy dumps and screenshots
(project spec section 49-50), configurable via d.settings and
automatically invalidated after any gesture/selector action.
"""

from typing import Any, Dict, Optional, Union

from PIL import Image

from uiautomator3.adb.discovery import get_device
from uiautomator3.ai.controller import AIController
from uiautomator3.apps.app_manager import AppManager
from uiautomator3.device.info import DeviceInfo, collect_device_info
from uiautomator3.elements.tree import ElementTree
from uiautomator3.gestures.gestures import GestureEngine
from uiautomator3.hierarchy.engine import HierarchyEngine
from uiautomator3.locator.analyzer import StabilityReport, analyze_locator
from uiautomator3.logging_config import get_logger
from uiautomator3.ocr.locator import OCRLocator
from uiautomator3.ocr.provider import OCRProvider
from uiautomator3.recording.session import RecordingSession
from uiautomator3.screenshots.screenshot import ScreenshotEngine
from uiautomator3.selectors.locator_object import Locator
from uiautomator3.selectors.query import Selector
from uiautomator3.settings import Settings
from uiautomator3.transport import ADBTransport, Transport
from uiautomator3.vision.locator import VisualLocator
from uiautomator3.vision.provider import VisionProvider

logger = get_logger("device")


class Device:
    """A connected Android device."""

    def __init__(self, serial: Optional[str] = None, transport: Optional[Transport] = None) -> None:
        self._adb_device = get_device(serial)
        self.serial: str = self._adb_device.serial
        self.transport: Transport = transport or ADBTransport(self._adb_device)
        self.transport.connect()

        self.gesture = GestureEngine(self._adb_device)
        self.app = AppManager(self._adb_device)
        self.settings = Settings()
        self.ai = AIController(self)
        self._screenshot_engine = ScreenshotEngine(self._adb_device)
        self._hierarchy_engine = HierarchyEngine(self._adb_device)
        self._ocr_provider: Optional[OCRProvider] = None
        self._vision_provider: Optional[VisionProvider] = None
        self._recording: Optional[RecordingSession] = None

    def shell(self, cmd: str, timeout: Optional[float] = None) -> str:
        return self.transport.request(cmd, {"cmd": cmd}, timeout=timeout)

    # -- recording --

    def start_recording(self) -> RecordingSession:
        """Begin capturing gesture/selector actions into a new RecordingSession."""
        self._recording = RecordingSession()
        return self._recording

    def stop_recording(self) -> Optional[RecordingSession]:
        """Stop recording and return the completed session (or None if never started)."""
        session = self._recording
        self._recording = None
        return session

    def _current_screen_label(self) -> Optional[str]:
        try:
            current = self.app.current()
            return f"{current.package}/{current.activity}" if current.activity else current.package
        except Exception:
            return None

    def invalidate_cache(self) -> None:
        """Drop any cached hierarchy/screenshot. Called automatically after
        every gesture/selector action (project spec section 50: invalidate
        intelligently after UI changes) - erring toward invalidating too
        eagerly is far safer than serving stale UI state."""
        self._hierarchy_engine.invalidate()
        self._screenshot_engine.invalidate()

    def _log_action(self, action: str, **kwargs: Any) -> None:
        self.invalidate_cache()
        if self._recording is not None:
            self._recording.log(action, screen=self._current_screen_label(), **kwargs)

    # -- gestures (delegated to self.gesture, exposed at top level for convenience) --

    def click(self, x: int, y: int) -> None:
        self.gesture.tap(x, y)
        self._log_action("click", coordinates={"x": x, "y": y})

    def long_click(self, x: int, y: int, duration: float = 1.0) -> None:
        self.gesture.long_press(x, y, duration=duration)
        self._log_action("long_click", coordinates={"x": x, "y": y}, duration=duration)

    def swipe(self, fx: int, fy: int, tx: int, ty: int, duration: float = 0.5) -> None:
        self.gesture.swipe((fx, fy), (tx, ty), duration=duration)
        self._log_action("swipe", coordinates={"from_x": fx, "from_y": fy, "to_x": tx, "to_y": ty})

    def drag(self, sx: int, sy: int, ex: int, ey: int, duration: float = 0.5) -> None:
        self.gesture.drag((sx, sy), (ex, ey), duration=duration)
        self._log_action("drag", coordinates={"from_x": sx, "from_y": sy, "to_x": ex, "to_y": ey})

    def press(self, key: Union[str, int]) -> None:
        self.gesture.press(key)
        self._log_action("press", key=key)

    def send_keys(self, text: str) -> None:
        self._adb_device.send_keys(text)
        self._log_action("send_keys", text=text)

    def launch_app(self, package_name: str, activity: Optional[str] = None) -> None:
        """`d.app.start(...)` plus a recorded 'app_launch' action, per project spec section 18."""
        self.app.start(package_name, activity)
        self._log_action("app_launch", package=package_name, activity=activity)

    def stop_app(self, package_name: str) -> None:
        self.app.stop(package_name)
        self._log_action("app_stop", package=package_name)

    # -- screenshots --

    def screenshot(self, display_id: Optional[int] = None, force: bool = False) -> "Image.Image":
        """Capture the screen. Returns a cached capture within
        `d.settings["screenshot_cache_ttl"]` seconds unless `force=True`."""
        ttl = self.settings.get("screenshot_cache_ttl", 0.3)
        return self._screenshot_engine.capture(display_id=display_id, force=force, ttl=ttl)

    # -- device info --

    def info(self) -> DeviceInfo:
        return collect_device_info(self._adb_device)

    # -- hierarchy --

    def dump_hierarchy(self) -> str:
        """Return the raw `uiautomator dump` XML for the current screen."""
        return self._hierarchy_engine.dump_xml()

    def inspect(self, force: bool = False) -> ElementTree:
        """Dump and parse the current screen into a normalized ElementTree.

        Returns a cached snapshot when called again within
        `d.settings["hierarchy_cache_ttl"]` seconds; pass `force=True` to
        always re-dump.
        """
        ttl = self.settings.get("hierarchy_cache_ttl", 0.3)
        return self._hierarchy_engine.dump(force=force, ttl=ttl)

    # -- selectors --

    def __call__(self, **kwargs: Any) -> Locator:
        """`d(text="Login")` - the primary selector entry point."""
        return Locator(self, Selector(**kwargs))

    def find(self, **kwargs: Any) -> Locator:
        return self(**kwargs)

    def locator(self, **kwargs: Any) -> Locator:
        return self(**kwargs)

    def analyze_locator(self, **kwargs: Any) -> StabilityReport:
        """Produce a stability report for a selector without resolving it."""
        selector = Selector(**kwargs)
        tree = self.inspect()
        return analyze_locator(tree, selector)

    # -- OCR / vision (optional extras, imported lazily on first use) --

    def _default_ocr_provider(self) -> OCRProvider:
        if self._ocr_provider is None:
            from uiautomator3.ocr.tesseract_provider import TesseractProvider

            self._ocr_provider = TesseractProvider()
        return self._ocr_provider

    def _default_vision_provider(self) -> VisionProvider:
        if self._vision_provider is None:
            from uiautomator3.vision.template_provider import TemplateMatchProvider

            self._vision_provider = TemplateMatchProvider()
        return self._vision_provider

    def ocr(self, text: str, exact: bool = False, provider: Optional[OCRProvider] = None) -> OCRLocator:
        """`d.ocr("Login").click()` - locate text via OCR when hierarchy text is unavailable."""
        return OCRLocator(self, text, provider or self._default_ocr_provider(), exact=exact)

    def visual(self, template, threshold: float = 0.8, provider: Optional[VisionProvider] = None) -> VisualLocator:
        """`d.visual("login_button.png").click()` - locate a UI element by template image."""
        return VisualLocator(self, template, provider or self._default_vision_provider(), threshold=threshold)

    def find_visual(self, template, threshold: float = 0.8, provider: Optional[VisionProvider] = None):
        """Return the VisionMatch for `template`, or None if not found above threshold."""
        return self.visual(template, threshold=threshold, provider=provider).find()

    def health(self) -> Dict[str, Any]:
        """Basic device health/reachability check (Phase 1 scope)."""
        info: Dict[str, Any] = {
            "serial": self.serial,
            "connected": self.transport.is_connected(),
            "adb": False,
            "screen_on": None,
            "battery": None,
        }
        try:
            state = self._adb_device.get_state()
            info["adb"] = state == "device"
        except Exception as e:
            logger.debug("adb state check failed: %s", e)

        try:
            output = self.shell("dumpsys power")
            info["screen_on"] = "mHoldingDisplaySuspendBlocker=true" in output or "Display Power: state=ON" in output
        except Exception as e:
            logger.debug("screen state check failed: %s", e)

        try:
            battery_output = self.shell("dumpsys battery")
            for line in battery_output.splitlines():
                line = line.strip()
                if line.startswith("level:"):
                    info["battery"] = int(line.split(":")[1].strip())
                    break
        except Exception as e:
            logger.debug("battery check failed: %s", e)

        return info

    def __repr__(self) -> str:
        return f"Device(serial={self.serial!r})"
