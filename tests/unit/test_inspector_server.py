from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.inspector.server import _devices, app


@pytest.fixture(autouse=True)
def clear_device_cache():
    _devices.clear()
    yield
    _devices.clear()


def make_fake_device(serial="emulator-5554"):
    device = MagicMock()
    device.serial = serial
    element = UIElement(
        id="e0",
        text="Login",
        content_description=None,
        resource_id="com.example:id/login",
        class_name="android.widget.Button",
        package_name="com.example",
        bounds=Bounds(0, 0, 100, 50),
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
    device.inspect.return_value = ElementTree([element])
    device.screenshot.return_value = Image.new("RGB", (100, 200))
    device.app.current.return_value = MagicMock(package="com.example", activity=".MainActivity")
    return device


@patch("uiautomator3.inspector.server.u3_connect")
def test_inspect_endpoint_returns_snapshot(mock_connect):
    mock_connect.return_value = make_fake_device()
    client = TestClient(app)

    response = client.get("/api/inspect")

    assert response.status_code == 200
    body = response.json()
    assert body["package_name"] == "com.example"
    assert body["screen_width"] == 100
    assert body["hierarchy"]["count"] == 1
    assert body["hierarchy"]["elements"][0]["resource_id"] == "com.example:id/login"
    assert body["screenshot_png_base64"]


@patch("uiautomator3.inspector.server.u3_connect")
def test_hierarchy_endpoint(mock_connect):
    mock_connect.return_value = make_fake_device()
    client = TestClient(app)

    response = client.get("/api/hierarchy")

    assert response.status_code == 200
    assert response.json()["count"] == 1


@patch("uiautomator3.inspector.server.u3_connect")
def test_screenshot_endpoint(mock_connect):
    mock_connect.return_value = make_fake_device()
    client = TestClient(app)

    response = client.get("/api/screenshot")

    assert response.status_code == 200
    assert "png_base64" in response.json()


@patch("uiautomator3.inspector.server.u3_connect")
def test_click_endpoint(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    client = TestClient(app)

    response = client.post("/api/click", params={"x": 10, "y": 20})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    device.click.assert_called_once_with(10, 20)


@patch("uiautomator3.inspector.server.u3_connect")
def test_inspect_endpoint_returns_500_on_device_error(mock_connect):
    mock_connect.side_effect = RuntimeError("no device")
    client = TestClient(app)

    response = client.get("/api/inspect")

    assert response.status_code == 500


@patch("uiautomator3.adb.discovery.list_devices")
def test_devices_endpoint(mock_list):
    mock_list.return_value = [MagicMock(serial="dev1"), MagicMock(serial="dev2")]
    client = TestClient(app)

    response = client.get("/api/devices")

    assert response.status_code == 200
    assert response.json() == [{"serial": "dev1"}, {"serial": "dev2"}]


@patch("uiautomator3.inspector.server.u3_connect")
def test_get_or_connect_reuses_cached_device(mock_connect):
    from uiautomator3.inspector.server import get_or_connect

    mock_connect.return_value = make_fake_device()

    d1 = get_or_connect("emulator-5554")
    d2 = get_or_connect("emulator-5554")

    assert d1 is d2
    mock_connect.assert_called_once()


@patch("uiautomator3.inspector.server.u3_connect")
def test_websocket_sends_snapshot(mock_connect):
    mock_connect.return_value = make_fake_device()
    client = TestClient(app)

    with client.websocket_connect("/ws/inspect") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "snapshot"
        assert data["package_name"] == "com.example"
        assert data["hierarchy"]["count"] == 1


@patch("uiautomator3.inspector.server.u3_connect")
def test_websocket_sends_error_on_connect_failure(mock_connect):
    mock_connect.side_effect = RuntimeError("no device")
    client = TestClient(app)

    with client.websocket_connect("/ws/inspect") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "error"
