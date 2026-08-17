"""Fluent vision locator: `d.visual(template).click()` per project spec section 12."""
import time
from typing import TYPE_CHECKING, Optional, Union

from uiautomator3.exceptions import ElementNotFoundError
from uiautomator3.vision.provider import VisionMatch, VisionProvider

if TYPE_CHECKING:
    from PIL.Image import Image

    from uiautomator3.device.device import Device


class VisualLocator:
    def __init__(
        self,
        device: "Device",
        template: Union[str, "Image"],
        provider: VisionProvider,
        threshold: float = 0.8,
    ) -> None:
        self._device = device
        self._template = self._load_template(template)
        self._provider = provider
        self._threshold = threshold

    @staticmethod
    def _load_template(template: Union[str, "Image"]) -> "Image":
        if isinstance(template, str):
            from PIL import Image

            return Image.open(template)
        return template

    def find(self) -> Optional[VisionMatch]:
        screenshot = self._device.screenshot()
        match = self._provider.find(screenshot, self._template)
        if match is None or match.similarity < self._threshold:
            return None
        return match

    @property
    def exists(self) -> bool:
        return self.find() is not None

    def wait(self, timeout: float = 10.0, interval: float = 0.5) -> Optional[VisionMatch]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            match = self.find()
            if match is not None:
                return match
            time.sleep(interval)
        return self.find()

    def click(self) -> None:
        match = self.find()
        if match is None:
            raise ElementNotFoundError("no visual match found above threshold")
        self._device.click(match.point.x, match.point.y)
