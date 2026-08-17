"""OCR provider protocol and result type.

Per docs/UIAUTOMATOR3_ARCHITECTURE.md section 9: OCR is a pluggable
provider, never imported by core modules. `OCRTextRegion` bounds are in
device screen pixel coordinates, matching UIElement.bounds, so the two can
be composed directly by the collector.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Protocol

from uiautomator3.elements.uielement import Bounds

if TYPE_CHECKING:
    from PIL.Image import Image


@dataclass
class OCRTextRegion:
    text: str
    bounds: Bounds
    confidence: float


class OCRProvider(Protocol):
    def detect_text(self, image: "Image") -> List[OCRTextRegion]: ...
