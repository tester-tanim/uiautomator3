from unittest.mock import MagicMock, patch

from uiautomator3.device.device import Device


def make_adb_device(serial="emulator-5554"):
    adb_device = MagicMock()
    adb_device.serial = serial
    adb_device.get_state.return_value = "device"
    return adb_device


@patch("uiautomator3.device.device.get_device")
def test_device_init_connects_transport(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")

    assert device.serial == "emulator-5554"
    assert device.transport.is_connected()


@patch("uiautomator3.device.device.get_device")
def test_device_shell_delegates_to_transport(mock_get_device):
    adb_device = make_adb_device()
    adb_device.shell.return_value = "pong"
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    result = device.shell("echo pong")

    assert result == "pong"


@patch("uiautomator3.device.device.get_device")
def test_health_reports_battery_level(mock_get_device):
    adb_device = make_adb_device()

    def shell_side_effect(cmd, timeout=None):
        if "battery" in cmd:
            return "Current Battery Service state:\n  level: 84\n  scale: 100"
        return "Display Power: state=ON"

    adb_device.shell.side_effect = shell_side_effect
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    health = device.health()

    assert health["serial"] == "emulator-5554"
    assert health["connected"] is True
    assert health["adb"] is True
    assert health["battery"] == 84


@patch("uiautomator3.device.device.get_device")
def test_repr(mock_get_device):
    mock_get_device.return_value = make_adb_device("R3CN123")
    device = Device(serial="R3CN123")
    assert repr(device) == "Device(serial='R3CN123')"


@patch("uiautomator3.device.device.get_device")
def test_click_delegates_to_gesture_engine(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    device.click(10, 20)

    adb_device.click.assert_called_once_with(10, 20)


@patch("uiautomator3.device.device.get_device")
def test_swipe_delegates_to_gesture_engine(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    device.swipe(0, 0, 100, 100, duration=0.2)

    adb_device.swipe.assert_called_once_with(0, 0, 100, 100, duration=0.2)


@patch("uiautomator3.device.device.get_device")
def test_press_delegates_to_gesture_engine(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    device.press("back")

    adb_device.keyevent.assert_called_once_with(4)


@patch("uiautomator3.device.device.get_device")
def test_screenshot_delegates_to_screenshot_engine(mock_get_device):
    from PIL import Image

    adb_device = make_adb_device()
    fake_image = Image.new("RGB", (10, 10))
    adb_device.screenshot.return_value = fake_image
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    result = device.screenshot()

    assert result is fake_image


@patch("uiautomator3.device.device.get_device")
def test_app_is_an_app_manager(mock_get_device):
    from uiautomator3.apps.app_manager import AppManager

    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")

    assert isinstance(device.app, AppManager)


@patch("uiautomator3.device.device.get_device")
def test_info_returns_device_info(mock_get_device):
    adb_device = make_adb_device()
    adb_device.prop.model = "Pixel 8"
    adb_device.prop.get.side_effect = lambda key: {
        "ro.product.brand": "Google",
        "ro.build.version.release": "14",
        "ro.build.version.sdk": "34",
    }[key]
    adb_device.window_size.return_value = (1080, 2400)
    adb_device.rotation.return_value = 0
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    info = device.info()

    assert info.model == "Pixel 8"
    assert info.width == 1080


@patch("uiautomator3.device.device.get_device")
def test_dump_hierarchy_returns_raw_xml(mock_get_device):
    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = '<hierarchy rotation="0"><node bounds="[0,0][1,1]" /></hierarchy>'
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    xml = device.dump_hierarchy()

    assert "<hierarchy" in xml


@patch("uiautomator3.device.device.get_device")
def test_inspect_returns_element_tree(mock_get_device):
    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = (
        '<hierarchy rotation="0">'
        '<node text="Login" resource-id="btn" class="android.widget.Button" package="com.example" '
        'content-desc="" checkable="false" checked="false" clickable="true" enabled="true" '
        'focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" '
        'selected="false" bounds="[0,0][100,50]" /></hierarchy>'
    )
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    tree = device.inspect()

    assert len(tree) == 1
    assert tree.elements[0].text == "Login"


LOGIN_HIERARCHY_XML = (
    '<hierarchy rotation="0">'
    '<node text="Login" resource-id="com.example:id/login" class="android.widget.Button" '
    'package="com.example" content-desc="" checkable="false" checked="false" clickable="true" '
    'enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" '
    'password="false" selected="false" bounds="[100,500][900,620]" /></hierarchy>'
)


@patch("uiautomator3.device.device.get_device")
def test_call_returns_locator(mock_get_device):
    from uiautomator3.selectors.locator_object import Locator

    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    locator = device(text="Login")

    assert isinstance(locator, Locator)


@patch("uiautomator3.device.device.get_device")
def test_call_locator_resolves_against_real_hierarchy(mock_get_device):
    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = LOGIN_HIERARCHY_XML
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")

    assert device(text="Login").exists is True
    assert device(text="Nonexistent").exists is False


@patch("uiautomator3.device.device.get_device")
def test_find_and_locator_are_aliases_of_call(mock_get_device):
    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = LOGIN_HIERARCHY_XML
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")

    assert device.find(text="Login").exists is True
    assert device.locator(text="Login").exists is True


@patch("uiautomator3.device.device.get_device")
def test_device_click_via_locator_uses_real_center(mock_get_device):
    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = LOGIN_HIERARCHY_XML
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    device(text="Login").click()

    adb_device.click.assert_called_once_with(500, 560)


@patch("uiautomator3.device.device.get_device")
def test_analyze_locator_returns_stability_report(mock_get_device):
    from uiautomator3.locator.analyzer import StabilityReport

    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = LOGIN_HIERARCHY_XML
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    report = device.analyze_locator(resourceId="com.example:id/login")

    assert isinstance(report, StabilityReport)
    assert report.uniqueness == 1.0


@patch("uiautomator3.device.device.get_device")
def test_ocr_uses_injected_provider_without_importing_tesseract(mock_get_device):
    from PIL import Image

    from uiautomator3.ocr.locator import OCRLocator
    from uiautomator3.ocr.provider import OCRTextRegion

    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    device.screenshot = MagicMock(return_value=Image.new("RGB", (10, 10)))

    fake_provider = MagicMock()
    fake_provider.detect_text.return_value = [
        OCRTextRegion(text="Login", bounds=MagicMock(center=MagicMock(x=5, y=5)), confidence=0.9)
    ]

    locator = device.ocr("Login", provider=fake_provider)

    assert isinstance(locator, OCRLocator)
    assert locator.exists is True


@patch("uiautomator3.device.device.get_device")
def test_visual_uses_injected_provider_without_importing_cv2(mock_get_device):
    from PIL import Image

    from uiautomator3.elements.uielement import Bounds, Point
    from uiautomator3.vision.locator import VisualLocator
    from uiautomator3.vision.provider import VisionMatch

    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    device.screenshot = MagicMock(return_value=Image.new("RGB", (10, 10)))

    fake_provider = MagicMock()
    fake_provider.find.return_value = VisionMatch(similarity=0.95, point=Point(5, 5), bounds=Bounds(0, 0, 10, 10))

    template = Image.new("RGB", (5, 5))
    locator = device.visual(template, provider=fake_provider)

    assert isinstance(locator, VisualLocator)
    assert locator.exists is True


@patch("uiautomator3.device.device.get_device")
def test_find_visual_returns_match_directly(mock_get_device):
    from PIL import Image

    from uiautomator3.elements.uielement import Bounds, Point
    from uiautomator3.vision.provider import VisionMatch

    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device

    device = Device(serial="emulator-5554")
    device.screenshot = MagicMock(return_value=Image.new("RGB", (10, 10)))

    fake_provider = MagicMock()
    expected_match = VisionMatch(similarity=0.95, point=Point(5, 5), bounds=Bounds(0, 0, 10, 10))
    fake_provider.find.return_value = expected_match

    result = device.find_visual(Image.new("RGB", (5, 5)), provider=fake_provider)

    assert result is expected_match
