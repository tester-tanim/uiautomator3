from unittest.mock import MagicMock

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.ocr.collector import collect_ocr
from uiautomator3.ocr.provider import OCRTextRegion


def make_element(id, **overrides):
    defaults = dict(
        id=id,
        text=None,
        content_description=None,
        resource_id=None,
        class_name=None,
        package_name="com.example",
        bounds=Bounds(0, 0, 100, 50),
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
    )
    defaults.update(overrides)
    return UIElement(**defaults)


def make_provider(regions):
    provider = MagicMock()
    provider.detect_text.return_value = regions
    return provider


def test_ocr_text_populated_on_containing_element():
    element = make_element("a", bounds=Bounds(0, 0, 200, 100))
    tree = ElementTree([element])
    region = OCRTextRegion(text="Login", bounds=Bounds(10, 10, 90, 40), confidence=0.95)
    provider = make_provider([region])

    result = collect_ocr(image=MagicMock(), tree=tree, provider=provider)

    matched = result.get("a")
    assert matched.ocr_text == "Login"
    assert matched.visual_confidence == 0.95
    assert "ocr" in matched.source


def test_synthetic_element_created_when_no_containing_element():
    tree = ElementTree([])
    region = OCRTextRegion(text="Canvas Text", bounds=Bounds(10, 10, 90, 40), confidence=0.9)
    provider = make_provider([region])

    result = collect_ocr(image=MagicMock(), tree=tree, provider=provider)

    assert len(result) == 1
    synthetic = result.elements[0]
    assert synthetic.text == "Canvas Text"
    assert synthetic.ocr_text == "Canvas Text"
    assert synthetic.source == frozenset({"ocr"})
    assert synthetic.role == "text"


def test_picks_smallest_containing_element():
    outer = make_element("outer", bounds=Bounds(0, 0, 500, 500))
    inner = make_element("inner", bounds=Bounds(10, 10, 100, 100))
    tree = ElementTree([outer, inner])
    region = OCRTextRegion(text="Login", bounds=Bounds(20, 20, 60, 40), confidence=0.9)
    provider = make_provider([region])

    result = collect_ocr(image=MagicMock(), tree=tree, provider=provider)

    assert result.get("inner").ocr_text == "Login"
    assert result.get("outer").ocr_text is None


def test_original_tree_not_mutated():
    element = make_element("a", bounds=Bounds(0, 0, 200, 100))
    tree = ElementTree([element])
    region = OCRTextRegion(text="Login", bounds=Bounds(10, 10, 90, 40), confidence=0.95)
    provider = make_provider([region])

    collect_ocr(image=MagicMock(), tree=tree, provider=provider)

    assert tree.get("a").ocr_text is None


def test_empty_regions_returns_equivalent_tree():
    element = make_element("a")
    tree = ElementTree([element])
    provider = make_provider([])

    result = collect_ocr(image=MagicMock(), tree=tree, provider=provider)

    assert len(result) == 1
    assert result.get("a").ocr_text is None
