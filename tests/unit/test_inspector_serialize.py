from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.inspector.serialize import element_to_dict, tree_to_dict


def make_element(id="e0", **overrides):
    defaults = dict(
        id=id,
        text="Login",
        content_description="Login button",
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
        children=[],
        depth=0,
        index=0,
        role="button",
    )
    defaults.update(overrides)
    return UIElement(**defaults)


def test_element_to_dict_shape():
    e = make_element()
    d = element_to_dict(e)

    assert d["id"] == "e0"
    assert d["text"] == "Login"
    assert d["resource_id"] == "com.example:id/login"
    assert d["bounds"] == {"left": 100, "top": 500, "right": 900, "bottom": 620}
    assert d["center"] == {"x": 500, "y": 560}
    assert d["clickable"] is True
    assert d["role"] == "button"
    assert d["source"] == ["hierarchy"]


def test_element_to_dict_is_json_safe():
    import json

    e = make_element()
    json.dumps(element_to_dict(e))  # must not raise


def test_tree_to_dict_shape():
    a = make_element("a", children=["b"])
    b = make_element("b", parent_id="a", depth=1)
    tree = ElementTree([a, b], rotation=1)

    d = tree_to_dict(tree)

    assert d["rotation"] == 1
    assert d["count"] == 2
    assert len(d["elements"]) == 2
    assert d["elements"][0]["id"] == "a"
    assert d["elements"][1]["parent_id"] == "a"
