"""UIAutomator 3.0 - Next-generation Android automation framework.

Phase 1 public API: connect(), devices(), doctor().
Phase 2 adds: gestures, screenshots, app management, device info - all
reachable via the Device object returned by connect().
Phase 3 adds: dump_hierarchy()/inspect() and the normalized UIElement /
ElementTree model, plus relationship and spatial queries.
Phase 5 adds: d(...)/d.find(...)/d.locator(...) selectors, the fluent
Locator object, locator candidate generation/scoring, and
d.analyze_locator().
Phase 6 adds: d.ocr(...) and d.visual(...)/d.find_visual(...) - optional,
lazily-imported OCR/vision fallback locators.
Phase 7 adds: d.settings["self_healing"] - opt-in automatic locator
recovery when a selector that previously resolved stops matching.
Phase 8 adds: d.start_recording()/stop_recording() - captures gesture and
selector actions (click/swipe/drag/press/send_keys/app_launch/app_stop)
into a RecordingSession, off by default.
Phase 9 adds: uiautomator3.codegen - turns a RecordingSession into Python/
pytest/POM/JSON/YAML/Robot/raw-action-script automation code.
Phase 10 adds: d.ai (structured, LLM-free element description/matching)
and uiautomator3.mcp (an opt-in MCP server exposing Device/AIController to
AI agents; not imported here since it requires the optional `mcp`
package - see uiautomator3.mcp.server).
Later phases extend this surface incrementally per
docs/UIAUTOMATOR3_ARCHITECTURE.md.
"""

from uiautomator3.ai import AIController, AIElement, ScreenDescription
from uiautomator3.apps.app_manager import AppInfo, AppManager, RunningAppInfo
from uiautomator3.client.connect import connect, devices
from uiautomator3.device.device import Device
from uiautomator3.device.info import DeviceInfo
from uiautomator3.diagnostics.doctor import DoctorReport
from uiautomator3.diagnostics.doctor import run_doctor as doctor
from uiautomator3.elements import Bounds, ElementTree, Point, UIElement
from uiautomator3.exceptions import (
    AdbError,
    AppLaunchError,
    DeviceConnectionError,
    DeviceNotFoundError,
    ElementAmbiguousError,
    ElementNotFoundError,
    InspectorError,
    LocatorHealingError,
    OCRProviderError,
    SelectorError,
    TransportError,
    TransportTimeoutError,
    UIAutomator3Error,
    VisionProviderError,
    XPathError,
)
from uiautomator3.healing import ElementSnapshot, HealingReport
from uiautomator3.locator import LocatorCandidate, LocatorSet, StabilityReport
from uiautomator3.ocr import OCRTextRegion
from uiautomator3.recording import RecordedAction, RecordingSession
from uiautomator3.selectors import Locator, Selector, XPathLocator, find_all_xpath
from uiautomator3.settings import Settings
from uiautomator3.version import __version__
from uiautomator3.vision import VisionMatch

__all__ = [
    "AIController",
    "AIElement",
    "AdbError",
    "AppInfo",
    "AppLaunchError",
    "AppManager",
    "Bounds",
    "Device",
    "DeviceConnectionError",
    "DeviceInfo",
    "DeviceNotFoundError",
    "DoctorReport",
    "ElementAmbiguousError",
    "ElementNotFoundError",
    "ElementSnapshot",
    "ElementTree",
    "HealingReport",
    "InspectorError",
    "Locator",
    "LocatorCandidate",
    "LocatorHealingError",
    "LocatorSet",
    "OCRProviderError",
    "OCRTextRegion",
    "Point",
    "RecordedAction",
    "RecordingSession",
    "RunningAppInfo",
    "ScreenDescription",
    "Selector",
    "SelectorError",
    "Settings",
    "StabilityReport",
    "TransportError",
    "TransportTimeoutError",
    "UIAutomator3Error",
    "UIElement",
    "VisionMatch",
    "VisionProviderError",
    "XPathError",
    "XPathLocator",
    "__version__",
    "connect",
    "devices",
    "doctor",
    "find_all_xpath",
]
