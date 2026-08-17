from uiautomator3.elements.roles import classify
from uiautomator3.elements.uielement import Bounds, UIElement


def make_element(class_name, **overrides):
    defaults = dict(
        id="e0",
        text=None,
        content_description=None,
        resource_id=None,
        class_name=class_name,
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


def test_button_class():
    assert classify(make_element("android.widget.Button")) == "button"


def test_edit_text_is_input():
    assert classify(make_element("android.widget.EditText")) == "input"


def test_plain_text_view_is_text():
    assert classify(make_element("android.widget.TextView", text="Hello")) == "text"


def test_clickable_text_view_is_button():
    assert classify(make_element("android.widget.TextView", text="Tap me", clickable=True)) == "button"


def test_checkbox():
    assert classify(make_element("android.widget.CheckBox")) == "checkbox"


def test_switch():
    assert classify(make_element("android.widget.Switch")) == "switch"


def test_image_view_is_image():
    assert classify(make_element("android.widget.ImageView")) == "image"


def test_recycler_view_is_list():
    assert classify(make_element("androidx.recyclerview.widget.RecyclerView")) == "list"


def test_scrollable_unknown_class_is_list():
    assert classify(make_element("com.custom.Widget", scrollable=True)) == "list"


def test_clickable_unknown_class_is_button():
    assert classify(make_element("com.custom.Widget", clickable=True)) == "button"


def test_unknown_class_with_text_is_text():
    assert classify(make_element("com.custom.Widget", text="hi")) == "text"


def test_unknown_class_fallback_is_container():
    assert classify(make_element("com.custom.Widget")) == "container"
