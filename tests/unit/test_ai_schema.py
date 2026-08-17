from uiautomator3.ai.schema import ScreenDescription, describe_element
from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement


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


def test_describe_element_shape():
    element = make_element("a")
    tree = ElementTree([element])

    described = describe_element(element, tree)

    assert described.role == "button"
    assert described.label == "Login"
    assert described.locator
    assert described.locator_python
    assert 0.0 <= described.confidence <= 1.0
    assert described.clickable is True
    assert described.enabled is True


def test_describe_element_label_falls_back_to_content_description():
    element = make_element("a", text=None, content_description="Login button")
    tree = ElementTree([element])

    described = describe_element(element, tree)

    assert described.label == "Login button"


def test_describe_element_label_none_when_no_text_or_desc():
    element = make_element("a", text=None, content_description=None)
    tree = ElementTree([element])

    described = describe_element(element, tree)

    assert described.label is None


def test_describe_element_as_dict_is_json_safe():
    import json

    element = make_element("a")
    tree = ElementTree([element])
    described = describe_element(element, tree)

    json.dumps(described.as_dict())  # must not raise


def test_screen_description_as_dict():
    element = make_element("a")
    tree = ElementTree([element])
    described = describe_element(element, tree)

    screen = ScreenDescription(screen="com.example/.Main", elements=[described])
    data = screen.as_dict()

    assert data["screen"] == "com.example/.Main"
    assert len(data["elements"]) == 1
    assert data["elements"][0]["label"] == "Login"
