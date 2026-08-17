"""OCR collector: maps detected text regions onto the current ElementTree.

Per docs/UIAUTOMATOR3_ARCHITECTURE.md section 9: runs only when triggered
(hierarchy match failed, or an OCR-based locator is used explicitly) -
never on a plain hierarchy refresh. Existing hierarchy elements whose
bounds contain an OCR region get their `ocr_text` populated; regions with
no containing hierarchy element become synthetic UIElements tagged
source={"ocr"} (e.g. canvas-rendered text with no accessibility node).
"""
import dataclasses
from typing import TYPE_CHECKING, List, Optional

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import UIElement
from uiautomator3.ocr.provider import OCRProvider, OCRTextRegion

if TYPE_CHECKING:
    from PIL.Image import Image


def _find_containing_element(tree: ElementTree, region: OCRTextRegion) -> Optional[UIElement]:
    """Return the smallest-area hierarchy element whose bounds contain the region's center."""
    cx, cy = region.bounds.center.x, region.bounds.center.y
    best: Optional[UIElement] = None
    for element in tree:
        if element.bounds.contains_point(cx, cy):
            if best is None or element.bounds.area < best.bounds.area:
                best = element
    return best


def _make_synthetic_element(region: OCRTextRegion, index: int) -> UIElement:
    return UIElement(
        id=f"ocr{index}",
        text=region.text,
        content_description=None,
        resource_id=None,
        class_name=None,
        package_name=None,
        bounds=region.bounds,
        clickable=False,
        enabled=True,
        visible=True,
        focused=False,
        selected=False,
        checked=False,
        scrollable=False,
        long_clickable=False,
        checkable=False,
        password=False,
        parent_id=None,
        role="text",
        ocr_text=region.text,
        visual_confidence=region.confidence,
        source=frozenset({"ocr"}),
    )


def collect_ocr(image: "Image", tree: ElementTree, provider: OCRProvider) -> ElementTree:
    """Run OCR and merge results into a copy of `tree`.

    Returns a new ElementTree; does not mutate the input tree's element
    list in place (UIElement instances shared with the input tree that get
    an ocr_text update are replaced, not mutated, to avoid surprising
    aliasing for callers still holding the original tree).
    """
    regions = provider.detect_text(image)
    elements: List[UIElement] = list(tree.elements)
    by_index = {e.id: i for i, e in enumerate(elements)}

    synthetic_count = 0
    for region in regions:
        containing = _find_containing_element(tree, region)
        if containing is not None:
            idx = by_index[containing.id]
            existing = elements[idx]
            elements[idx] = dataclasses.replace(
                existing,
                ocr_text=region.text,
                visual_confidence=region.confidence,
                source=existing.source | {"ocr"},
            )
        else:
            elements.append(_make_synthetic_element(region, synthetic_count))
            synthetic_count += 1

    return ElementTree(elements, rotation=tree.rotation)
