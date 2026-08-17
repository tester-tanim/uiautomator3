"""Fluent OCR locator: `d.ocr("Login").click()` per project spec section 11."""

import time
from typing import TYPE_CHECKING, Optional

from uiautomator3.exceptions import ElementNotFoundError
from uiautomator3.ocr.provider import OCRProvider

if TYPE_CHECKING:
    from uiautomator3.device.device import Device
    from uiautomator3.ocr.provider import OCRTextRegion


class OCRLocator:
    def __init__(self, device: "Device", text: str, provider: OCRProvider, exact: bool = False) -> None:
        self._device = device
        self._text = text
        self._provider = provider
        self._exact = exact

    def _matches(self, region: "OCRTextRegion") -> bool:
        return region.text == self._text if self._exact else self._text in region.text

    def find(self) -> Optional["OCRTextRegion"]:
        image = self._device.screenshot()
        regions = self._provider.detect_text(image)
        for region in regions:
            if self._matches(region):
                return region
        return None

    @property
    def exists(self) -> bool:
        return self.find() is not None

    def wait(self, timeout: float = 10.0, interval: float = 0.5) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists:
                return True
            time.sleep(interval)
        return self.exists

    def click(self) -> None:
        region = self.find()
        if region is None:
            raise ElementNotFoundError(f"no OCR text region matched {self._text!r}")
        self._device.click(region.bounds.center.x, region.bounds.center.y)
