from unittest.mock import MagicMock

import pytest

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.exceptions import ElementAmbiguousError, ElementNotFoundError, XPathError
from uiautomator3.selectors.xpath import XPathLocator, find_all_xpath


def make_element(identifier, parent_id=None, children=None, **overrides):
    values = dict(
        id=identifier,
        text=None,
        content_description=None,
        resource_id=None,
        class_name="android.widget.FrameLayout",
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
        parent_id=parent_id,
        children=children or [],
    )
    values.update(overrides)
    return UIElement(**values)


@pytest.fixture
def tree():
    root = make_element(
        "root",
        children=["login", "cancel", "panel"],
        class_name="android.widget.FrameLayout",
    )
    login = make_element(
        "login",
        "root",
        text="Login now",
        resource_id="com.example:id/login",
        class_name="android.widget.TextView",
        clickable=True,
    )
    cancel = make_element(
        "cancel",
        "root",
        text="Cancel",
        class_name="android.widget.Button",
    )
    panel = make_element(
        "panel",
        "root",
        children=["email", "password"],
        class_name="android.widget.LinearLayout",
    )
    email = make_element(
        "email",
        "panel",
        content_description="Email input",
        class_name="android.widget.EditText",
    )
    password = make_element(
        "password",
        "panel",
        text="Password",
        class_name="android.widget.EditText",
    )
    return ElementTree([root, login, cancel, panel, email, password])


def test_android_attributes_and_class_shorthand(tree):
    assert [element.id for element in find_all_xpath(tree, "//node[@resource-id='com.example:id/login']")] == ["login"]
    assert [element.id for element in find_all_xpath(tree, "//TextView[contains(@text, 'Login')]")] == ["login"]


def test_axes_and_relationship_predicates(tree):
    assert [element.id for element in find_all_xpath(tree, "//node[@content-desc='Email input']/parent::node")] == ["panel"]
    assert [element.id for element in find_all_xpath(tree, "//EditText[@text='Password']/ancestor::node[@class='android.widget.FrameLayout']")] == ["root"]
    assert [element.id for element in find_all_xpath(tree, "//node[@text='Cancel']/following-sibling::node")] == ["panel"]
    assert [element.id for element in find_all_xpath(tree, "//node[@text='Cancel']/preceding-sibling::node")] == ["login"]


def test_functions_positions_and_union_are_document_ordered(tree):
    assert [element.id for element in find_all_xpath(tree, "//EditText[position() = last()]")] == ["password"]
    assert [element.id for element in find_all_xpath(tree, "//node[normalize-space(@text) = 'Cancel' or contains(@content-desc, 'Email')]")] == ["cancel", "email"]
    assert [element.id for element in find_all_xpath(tree, "//node[@text='Password'] | //node[@text='Login now']")] == ["login", "password"]


def test_results_are_original_elements(tree):
    result = find_all_xpath(tree, "//node[@text='Login now']")
    assert result[0] is tree.get("login")


def test_empty_and_invalid_expressions(tree):
    assert find_all_xpath(tree, "//node[@text='missing']") == []
    with pytest.raises(XPathError):
        find_all_xpath(tree, "//node[")
    with pytest.raises(XPathError):
        find_all_xpath(tree, "count(//node)")


def test_xpath_locator_resolves_and_clicks(tree):
    device = MagicMock()
    device.inspect.return_value = tree
    locator = XPathLocator(device, "//node[@text='Login now']")

    assert locator.exists is True
    assert locator.inspect() is tree.get("login")
    locator.click()

    device.gesture.tap.assert_called_once_with(50, 25)
    device.invalidate_cache.assert_called_once_with()


def test_xpath_locator_reports_missing_and_ambiguous_matches(tree):
    device = MagicMock()
    device.inspect.return_value = tree
    with pytest.raises(ElementNotFoundError):
        XPathLocator(device, "//node[@text='missing']").inspect()
    with pytest.raises(ElementAmbiguousError):
        XPathLocator(device, "//EditText").inspect()