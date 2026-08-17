from unittest.mock import MagicMock

from PIL import Image

from uiautomator3.elements.tree import ElementTree
from uiautomator3.inspector.inspector import Inspector


def make_device():
    device = MagicMock()
    device.inspect.return_value = ElementTree([])
    device.screenshot.return_value = Image.new("RGB", (100, 200))
    device.app.current.return_value = MagicMock(package="com.example", activity=".MainActivity")
    return device


def test_inspect_combines_hierarchy_and_screenshot():
    device = make_device()
    inspector = Inspector(device)

    snapshot = inspector.inspect()

    assert isinstance(snapshot.tree, ElementTree)
    assert snapshot.screen_width == 100
    assert snapshot.screen_height == 200
    assert snapshot.package_name == "com.example"
    assert snapshot.activity == ".MainActivity"
    assert snapshot.screenshot_png_base64  # non-empty base64 string


def test_screenshot_is_valid_base64_png():
    import base64
    import io

    device = make_device()
    snapshot = Inspector(device).inspect()

    raw = base64.b64decode(snapshot.screenshot_png_base64)
    img = Image.open(io.BytesIO(raw))
    assert img.size == (100, 200)


def test_activity_defaults_to_empty_string_when_none():
    device = make_device()
    device.app.current.return_value = MagicMock(package="com.example", activity=None)

    snapshot = Inspector(device).inspect()

    assert snapshot.activity == ""
