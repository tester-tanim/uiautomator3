from unittest.mock import MagicMock

import pytest

from uiautomator3.ai.controller import AIController
from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.exceptions import ElementNotFoundError


def make_element(id, **overrides):
    defaults = dict(
        id=id,
        text="Login",
        content_description=None,
        resource_id="com.example:id/login",
        class_name="android.widget.Button",
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
        role="button",
    )
    defaults.update(overrides)
    return UIElement(**defaults)


def make_device_with_elements(elements):
    device = MagicMock()
    device.inspect.return_value = ElementTree(elements)
    device.app.current.return_value = MagicMock(package="com.example", activity=".Main")
    return device


def test_inspect_returns_screen_and_elements():
    device = make_device_with_elements([make_element("a")])
    ai = AIController(device)

    result = ai.inspect()

    assert result["screen"] == "com.example/.Main"
    assert len(result["elements"]) == 1
    assert result["elements"][0]["label"] == "Login"


def test_inspect_excludes_uninteresting_elements():
    labeled = make_element("a", text="Login")
    blank_container = make_element("b", text=None, content_description=None, clickable=False, role="container")
    device = make_device_with_elements([labeled, blank_container])
    ai = AIController(device)

    result = ai.inspect()

    assert len(result["elements"]) == 1


def test_inspect_excludes_unlabeled_clickable_elements():
    # a clickable element with no text/description contributes nothing an
    # AI agent could refer to by description, and is exactly the kind of
    # layout-container noise that dominates a raw hierarchy dump (project
    # spec section 63: dense structured data, not everything clickable)
    noisy = make_element("a", text=None, content_description=None, clickable=True)
    device = make_device_with_elements([noisy])
    ai = AIController(device)

    result = ai.inspect()

    assert result["elements"] == []


def test_inspect_handles_app_current_failure_gracefully():
    device = make_device_with_elements([make_element("a")])
    device.app.current.side_effect = RuntimeError("boom")
    ai = AIController(device)

    result = ai.inspect()

    assert result["screen"] == "unknown"


def test_find_returns_matches_list():
    device = make_device_with_elements([make_element("a", text="Login")])
    ai = AIController(device)

    result = ai.find("Login button")

    assert result["element"] == "Login button"
    assert len(result["matches"]) == 1
    assert result["matches"][0]["confidence"] > 0


def test_find_no_matches():
    device = make_device_with_elements([make_element("a", text="Login")])
    ai = AIController(device)

    result = ai.find("completely unrelated xyz")

    assert result["matches"] == []


def test_click_clicks_best_match_center():
    device = make_device_with_elements([make_element("a", text="Login", bounds=Bounds(0, 0, 100, 50))])
    ai = AIController(device)

    result = ai.click("Login")

    device.click.assert_called_once_with(50, 25)
    assert result["clicked"] == "Login"
    assert result["confidence"] > 0


def test_click_raises_when_no_match():
    device = make_device_with_elements([make_element("a", text="Login")])
    ai = AIController(device)

    with pytest.raises(ElementNotFoundError):
        ai.click("completely unrelated xyz")


def test_type_clicks_then_sends_keys():
    device = make_device_with_elements(
        [make_element("a", text="Email input", resource_id="com.example:id/email", bounds=Bounds(0, 0, 100, 50))]
    )
    ai = AIController(device)

    result = ai.type("Email input", "test@example.com")

    device.click.assert_called_once_with(50, 25)
    device.send_keys.assert_called_once_with("test@example.com")
    assert result["typed_into"] == "Email input"
    assert result["text"] == "test@example.com"


def test_type_raises_when_no_match():
    device = make_device_with_elements([make_element("a", text="Login")])
    ai = AIController(device)

    with pytest.raises(ElementNotFoundError):
        ai.type("nonexistent field xyz", "hello")
