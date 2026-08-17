"""Vision provider protocol and result type.

Per docs/UIAUTOMATOR3_ARCHITECTURE.md section 10: same provider-pattern
shape as OCR. `VisionMatch` bounds/point are in device screen pixel
coordinates.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Protocol

from uiautomator3.elements.uielement import Bounds, Point

if TYPE_CHECKING:
    from PIL.Image import Image


@dataclass
class VisionMatch:
    similarity: float
    point: Point
    bounds: Bounds


class VisionProvider(Protocol):
    def find(self, screenshot: "Image", template: "Image") -> Optional[VisionMatch]: ...
