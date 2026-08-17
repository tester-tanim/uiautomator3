"""Tesseract-backed OCR provider.

Imports pytesseract lazily (inside __init__, not at module load) so that
importing uiautomator3.ocr never requires the optional `ocr` extra to be
installed - only constructing a TesseractProvider does. This matches
docs/UIAUTOMATOR3_ARCHITECTURE.md's "core stays light" principle.
"""

from typing import TYPE_CHECKING, List, Optional

from uiautomator3.elements.uielement import Bounds
from uiautomator3.exceptions import OCRProviderError
from uiautomator3.ocr.provider import OCRTextRegion

if TYPE_CHECKING:
    from PIL.Image import Image


class TesseractProvider:
    """OCR via the Tesseract engine (requires the `ocr` extra + the tesseract binary)."""

    def __init__(self, tesseract_cmd: Optional[str] = None, lang: str = "eng") -> None:
        try:
            import pytesseract
        except ImportError as e:
            raise OCRProviderError(
                "pytesseract is required for TesseractProvider. Install with: pip install uiautomator3[ocr]"
            ) from e

        self._pytesseract = pytesseract
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self._lang = lang

    def detect_text(self, image: "Image") -> List[OCRTextRegion]:
        try:
            data = self._pytesseract.image_to_data(image, lang=self._lang, output_type=self._pytesseract.Output.DICT)
        except Exception as e:
            raise OCRProviderError(f"tesseract OCR failed: {e}") from e

        regions: List[OCRTextRegion] = []
        n = len(data.get("text", []))
        for i in range(n):
            text = data["text"][i].strip()
            if not text:
                continue
            try:
                confidence = float(data["conf"][i])
            except (ValueError, TypeError):
                confidence = -1.0
            if confidence < 0:
                continue

            left = data["left"][i]
            top = data["top"][i]
            width = data["width"][i]
            height = data["height"][i]
            regions.append(
                OCRTextRegion(
                    text=text,
                    bounds=Bounds(left=left, top=top, right=left + width, bottom=top + height),
                    confidence=confidence / 100.0,
                )
            )
        return regions
