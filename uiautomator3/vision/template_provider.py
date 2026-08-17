"""OpenCV template-matching vision provider.

Reimplements uiautomator2's proven template-matching approach
(docs/UIAUTOMATOR2_ANALYSIS.md section 7: `image.py`'s `ImageX.match()`)
directly against `cv2.matchTemplate`, without pulling in v2's `findit`/
`imutils`/`skimage` dependencies - multi-scale matching and the core
algorithm are reproduced with plain OpenCV + numpy, which is already the
`vision` extra's dependency floor.

Imports cv2/numpy lazily so importing uiautomator3.vision never requires
the optional `vision` extra - only constructing a TemplateMatchProvider
does.
"""

from typing import TYPE_CHECKING, Optional, Tuple

from uiautomator3.elements.uielement import Bounds
from uiautomator3.exceptions import VisionProviderError
from uiautomator3.vision.provider import VisionMatch

if TYPE_CHECKING:
    from PIL.Image import Image


class TemplateMatchProvider:
    """Finds a template image within a screenshot via OpenCV template matching."""

    def __init__(self, scales: Tuple[float, float, int] = (0.9, 1.1, 3)) -> None:
        try:
            import cv2
            import numpy as np
        except ImportError as e:
            raise VisionProviderError(
                "opencv-python and numpy are required for TemplateMatchProvider. "
                "Install with: pip install uiautomator3[vision]"
            ) from e

        self._cv2 = cv2
        self._np = np
        self._scales = scales

    def _pil_to_cv(self, image: "Image"):
        arr = self._np.array(image.convert("RGB"))
        return arr[:, :, ::-1].copy()  # RGB -> BGR

    def find(self, screenshot: "Image", template: "Image") -> Optional[VisionMatch]:
        cv2 = self._cv2
        np = self._np

        target = self._pil_to_cv(screenshot)
        template_cv = self._pil_to_cv(template)
        target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template_cv, cv2.COLOR_BGR2GRAY)

        low, high, steps = self._scales
        best_similarity = -1.0
        best_loc: Optional[Tuple[int, int]] = None
        best_size: Optional[Tuple[int, int]] = None

        for scale in np.linspace(low, high, steps):
            th, tw = template_gray.shape[:2]
            scaled_w, scaled_h = int(tw * scale), int(th * scale)
            if scaled_w < 1 or scaled_h < 1:
                continue
            if scaled_w > target_gray.shape[1] or scaled_h > target_gray.shape[0]:
                continue

            resized = cv2.resize(template_gray, (scaled_w, scaled_h))
            result = cv2.matchTemplate(target_gray, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best_similarity:
                best_similarity = max_val
                best_loc = max_loc
                best_size = (scaled_w, scaled_h)

        if best_loc is None or best_size is None:
            return None

        left, top = best_loc
        width, height = best_size
        bounds = Bounds(left=left, top=top, right=left + width, bottom=top + height)
        return VisionMatch(similarity=float(best_similarity), point=bounds.center, bounds=bounds)
