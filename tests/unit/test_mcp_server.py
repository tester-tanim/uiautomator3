import asyncio
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

pytest.importorskip("mcp")

from uiautomator3.ai.controller import AIController  # noqa: E402
from uiautomator3.elements.tree import ElementTree  # noqa: E402
from uiautomator3.elements.uielement import Bounds, UIElement  # noqa: E402
from uiautomator3.mcp.server import _devices, build_server  # noqa: E402


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


def make_fake_device(serial="emulator-5554"):
    device = MagicMock()
    device.serial = serial
    device.inspect.return_value = ElementTree([make_element("a")])
    device.screenshot.return_value = Image.new("RGB", (100, 200))
    device.app.current.return_value = MagicMock(package="com.example", activity=".Main", pid=123)
    info = MagicMock()
    info.serial = serial
    info.model = "Pixel 8"
    info.brand = "Google"
    info.android_version = "14"
    info.sdk_version = "34"
    info.width = 1080
    info.height = 2400
    info.rotation = 0
    device.info.return_value = info
    device.ai = AIController(device)  # real AIController wrapping the mock, like the real Device wires it
    return device


@pytest.fixture(autouse=True)
def clear_device_cache():
    _devices.clear()
    yield
    _devices.clear()


def call(server, tool_name, arguments=None):
    result = asyncio.run(server.call_tool(tool_name, arguments or {}))
    assert not result.is_error, result
    return result.structured_content["result"]


@patch("uiautomator3.mcp.server.u3_connect")
def test_default_tools_registered(mock_connect):
    server = build_server()
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    expected = {
        "connect_device", "get_device_info", "inspect_screen", "find_element",
        "click_element", "type_text", "swipe", "scroll", "take_screenshot",
        "get_ui_tree", "get_current_activity", "launch_app", "stop_app", "install_app",
    }
    assert expected <= names
    assert "run_script" not in names


@patch("uiautomator3.mcp.server.u3_connect")
def test_run_script_only_registered_with_allow_shell(mock_connect):
    server = build_server(allow_shell=True)
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    assert "run_script" in names


@patch("uiautomator3.mcp.server.u3_connect")
def test_connect_device_tool(mock_connect):
    mock_connect.return_value = make_fake_device()
    server = build_server()

    result = call(server, "connect_device")

    assert result["serial"] == "emulator-5554"
    assert result["connected"] is True


@patch("uiautomator3.mcp.server.u3_connect")
def test_get_device_info_tool(mock_connect):
    mock_connect.return_value = make_fake_device()
    server = build_server()

    result = call(server, "get_device_info")

    assert result["model"] == "Pixel 8"
    assert result["width"] == 1080


@patch("uiautomator3.mcp.server.u3_connect")
def test_inspect_screen_tool_returns_structured_elements(mock_connect):
    mock_connect.return_value = make_fake_device()
    server = build_server()

    result = call(server, "inspect_screen")

    assert result["screen"] == "com.example/.Main"
    assert len(result["elements"]) == 1
    assert result["elements"][0]["label"] == "Login"
    assert "locator" in result["elements"][0]
    assert "confidence" in result["elements"][0]


@patch("uiautomator3.mcp.server.u3_connect")
def test_find_element_tool(mock_connect):
    mock_connect.return_value = make_fake_device()
    server = build_server()

    result = call(server, "find_element", {"description": "Login button"})

    assert result["element"] == "Login button"
    assert len(result["matches"]) >= 1


@patch("uiautomator3.mcp.server.u3_connect")
def test_click_element_tool(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "click_element", {"description": "Login"})

    device.click.assert_called_once()
    assert result["clicked"] == "Login"


@patch("uiautomator3.mcp.server.u3_connect")
def test_type_text_tool(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "type_text", {"description": "Login", "text": "hello"})

    device.send_keys.assert_called_once_with("hello")
    assert result["text"] == "hello"


@patch("uiautomator3.mcp.server.u3_connect")
def test_swipe_tool(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "swipe", {"from_x": 0, "from_y": 0, "to_x": 100, "to_y": 100})

    device.swipe.assert_called_once_with(0, 0, 100, 100, duration=0.5)
    assert result["ok"] is True


@patch("uiautomator3.mcp.server.u3_connect")
def test_scroll_tool_down(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "scroll", {"direction": "down"})

    assert result["ok"] is True
    device.swipe.assert_called_once()


@patch("uiautomator3.mcp.server.u3_connect")
def test_scroll_tool_invalid_direction(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "scroll", {"direction": "sideways"})

    assert result["ok"] is False


@patch("uiautomator3.mcp.server.u3_connect")
def test_take_screenshot_tool(mock_connect):
    mock_connect.return_value = make_fake_device()
    server = build_server()

    result = call(server, "take_screenshot")

    assert result["width"] == 100
    assert result["height"] == 200
    assert result["png_base64"]


@patch("uiautomator3.mcp.server.u3_connect")
def test_get_ui_tree_tool(mock_connect):
    mock_connect.return_value = make_fake_device()
    server = build_server()

    result = call(server, "get_ui_tree")

    assert result["count"] == 1


@patch("uiautomator3.mcp.server.u3_connect")
def test_get_current_activity_tool(mock_connect):
    mock_connect.return_value = make_fake_device()
    server = build_server()

    result = call(server, "get_current_activity")

    assert result["package"] == "com.example"
    assert result["activity"] == ".Main"


@patch("uiautomator3.mcp.server.u3_connect")
def test_launch_app_tool(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "launch_app", {"package_name": "com.example.app"})

    device.launch_app.assert_called_once_with("com.example.app", None)
    assert result["ok"] is True


@patch("uiautomator3.mcp.server.u3_connect")
def test_stop_app_tool(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "stop_app", {"package_name": "com.example.app"})

    device.stop_app.assert_called_once_with("com.example.app")
    assert result["ok"] is True


@patch("uiautomator3.mcp.server.u3_connect")
def test_install_app_tool(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    result = call(server, "install_app", {"path_or_url": "/tmp/app.apk"})

    device.app.install.assert_called_once_with("/tmp/app.apk")
    assert result["ok"] is True


@patch("uiautomator3.mcp.server.u3_connect")
def test_run_script_tool_when_enabled(mock_connect):
    device = make_fake_device()
    device.shell.return_value = "output text"
    mock_connect.return_value = device
    server = build_server(allow_shell=True)

    result = call(server, "run_script", {"shell_command": "echo hi"})

    device.shell.assert_called_once_with("echo hi")
    assert result["output"] == "output text"


@patch("uiautomator3.mcp.server.u3_connect")
def test_devices_are_cached_across_tool_calls(mock_connect):
    device = make_fake_device()
    mock_connect.return_value = device
    server = build_server()

    call(server, "connect_device")
    call(server, "get_device_info")

    mock_connect.assert_called_once()
