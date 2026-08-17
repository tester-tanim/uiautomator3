"""Inspector pipeline (Phase 4 scope: hierarchy + screenshot only).

This is the same object both `Device`/Python callers and the web inspector
backend use - the FastAPI layer never reimplements inspection logic (see
docs/UIAUTOMATOR3_ARCHITECTURE.md section 11). OCR/vision collectors
described in the architecture doc's full pipeline (section 3) are later
phases and not wired in yet.
"""

import base64
import io
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from uiautomator3.elements.tree import ElementTree

if TYPE_CHECKING:
    from uiautomator3.device.device import Device


@dataclass
class InspectionSnapshot:
    tree: ElementTree
    screenshot_png_base64: str
    screen_width: int
    screen_height: int
    package_name: str
    activity: str
    timestamp: float


class Inspector:
    """Combines a hierarchy dump and a screenshot into one inspection snapshot."""

    def __init__(self, device: "Device") -> None:
        self._device = device

    def inspect(self) -> InspectionSnapshot:
        tree = self._device.inspect()
        image = self._device.screenshot()

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        screenshot_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

        current = self._device.app.current()

        return InspectionSnapshot(
            tree=tree,
            screenshot_png_base64=screenshot_b64,
            screen_width=image.width,
            screen_height=image.height,
            package_name=current.package,
            activity=current.activity or "",
            timestamp=time.time(),
        )
