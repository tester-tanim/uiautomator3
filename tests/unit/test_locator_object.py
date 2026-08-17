from unittest.mock import MagicMock

import pytest

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.exceptions import ElementAmbiguousError, ElementNotFoundError
from uiautomator3.selectors.locator_object import Locator
from uiautomator3.selectors.query import Selector


def make_element(id, **overrides):
    defaults = dict(
        id=id,
        text=None,
        content_description=None,
        resource_id=None,
        class_name=None,
        package_name="com.example",
        bounds=Bounds(100, 500, 900, 620),
        clickable=True,
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


def make_device_with_tree(elements):
    device = MagicMock()
    device.inspect.return_value = ElementTree(elements)
    return device


def test_exists_true_when_match_found():
    device = make_device_with_tree([make_element("a", text="Login")])
    locator = Locator(device, Selector(text="Login"))
    assert locator.exists is True


def test_exists_false_when_no_match():
    device = make_device_with_tree([make_element("a", text="Login")])
    locator = Locator(device, Selector(text="Nope"))
    assert locator.exists is False


def test_count():
    device = make_device_with_tree([make_element("a", text="Login"), make_element("b", text="Login")])
    locator = Locator(device, Selector(text="Login"))
    assert locator.count() == 2


def test_click_resolves_and_clicks_center():
    element = make_element("a", text="Login", bounds=Bounds(100, 500, 900, 620))
    device = make_device_with_tree([element])
    locator = Locator(device, Selector(text="Login"))

    locator.click()

    device.gesture.tap.assert_called_once_with(500, 560)


def test_click_walks_up_to_clickable_ancestor_when_matched_element_is_not_clickable():
    # a launcher-icon-label style hierarchy: the matched TextView is not
    # clickable, but its RelativeLayout ancestor (icon + label) is.
    parent = make_element(
        "parent", clickable=True, bounds=Bounds(33, 1079, 287, 1378), children=["label"]
    )
    label = make_element(
        "label", text="WhatsApp", clickable=False, parent_id="parent", bounds=Bounds(33, 1234, 287, 1378)
    )
    device = make_device_with_tree([parent, label])
    locator = Locator(device, Selector(text="WhatsApp"))

    locator.click()

    device.gesture.tap.assert_called_once_with(parent.bounds.center.x, parent.bounds.center.y)


def test_click_falls_back_to_own_center_when_no_clickable_ancestor():
    parent = make_element("parent", clickable=False, bounds=Bounds(0, 0, 300, 300), children=["label"])
    label = make_element(
        "label", text="WhatsApp", clickable=False, parent_id="parent", bounds=Bounds(100, 500, 900, 620)
    )
    device = make_device_with_tree([parent, label])
    locator = Locator(device, Selector(text="WhatsApp"))

    locator.click()

    device.gesture.tap.assert_called_once_with(500, 560)


def test_click_raises_when_not_found():
    device = make_device_with_tree([])
    locator = Locator(device, Selector(text="Missing"))
    with pytest.raises(ElementNotFoundError):
        locator.click()


def test_click_raises_when_ambiguous():
    device = make_device_with_tree([make_element("a", text="Login"), make_element("b", text="Login")])
    locator = Locator(device, Selector(text="Login"))
    with pytest.raises(ElementAmbiguousError):
        locator.click()


def test_long_click_delegates_with_duration():
    element = make_element("a", text="Login", bounds=Bounds(0, 0, 100, 100))
    device = make_device_with_tree([element])
    locator = Locator(device, Selector(text="Login"))

    locator.long_click(duration=2.0)

    device.gesture.long_press.assert_called_once_with(50, 50, duration=2.0)


def test_wait_returns_true_immediately_when_exists():
    device = make_device_with_tree([make_element("a", text="Login")])
    locator = Locator(device, Selector(text="Login"))
    assert locator.wait(timeout=1) is True


def test_wait_returns_false_when_timeout_exceeded():
    device = make_device_with_tree([])
    locator = Locator(device, Selector(text="Missing"))
    assert locator.wait(timeout=0.2, interval=0.05) is False


def test_wait_gone_true_when_already_gone():
    device = make_device_with_tree([])
    locator = Locator(device, Selector(text="Login"))
    assert locator.wait_gone(timeout=0.2) is True


def test_best_locator_returns_top_candidate():
    element = make_element("a", resource_id="com.example:id/login", text="Login")
    device = make_device_with_tree([element])
    locator = Locator(device, Selector(text="Login"))

    best = locator.best_locator()

    assert best is not None


def test_confidence_is_between_0_and_1():
    element = make_element("a", resource_id="com.example:id/login", text="Login")
    device = make_device_with_tree([element])
    locator = Locator(device, Selector(text="Login"))

    assert 0.0 <= locator.confidence <= 1.0


def test_alternatives_excludes_best():
    element = make_element("a", resource_id="com.example:id/login", text="Login")
    device = make_device_with_tree([element])
    locator = Locator(device, Selector(text="Login"))

    best = locator.best_locator()
    alternatives = locator.alternatives()

    assert best not in alternatives


def test_assert_exists_passes_when_present():
    device = make_device_with_tree([make_element("a", text="Login")])
    locator = Locator(device, Selector(text="Login"))
    assert locator.assert_exists() is locator


def test_assert_exists_raises_when_absent():
    device = make_device_with_tree([])
    locator = Locator(device, Selector(text="Login"))
    with pytest.raises(ElementNotFoundError):
        locator.assert_exists()


def test_assert_visible_raises_when_not_visible():
    device = make_device_with_tree([make_element("a", text="Login", visible=False)])
    locator = Locator(device, Selector(text="Login"))
    with pytest.raises(ElementNotFoundError):
        locator.assert_visible()


def test_assert_enabled_raises_when_disabled():
    device = make_device_with_tree([make_element("a", text="Login", enabled=False)])
    locator = Locator(device, Selector(text="Login"))
    with pytest.raises(ElementNotFoundError):
        locator.assert_enabled()


def test_assert_text_passes_on_match():
    device = make_device_with_tree([make_element("a", text="Login")])
    locator = Locator(device, Selector(text="Login"))
    assert locator.assert_text("Login") is locator


def test_assert_text_raises_on_mismatch():
    device = make_device_with_tree([make_element("a", text="Login")])
    locator = Locator(device, Selector(text="Login"))
    with pytest.raises(ElementNotFoundError):
        locator.assert_text("Wrong")


def test_repr():
    device = MagicMock()
    locator = Locator(device, Selector(text="Login"))
    assert "Login" in repr(locator)
