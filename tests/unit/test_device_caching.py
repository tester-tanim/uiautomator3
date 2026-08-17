from unittest.mock import MagicMock, patch

from PIL import Image

from uiautomator3.device.device import Device

VALID_XML = (
    '<hierarchy rotation="0">'
    '<node text="Login" resource-id="com.example:id/login" class="android.widget.Button" '
    'package="com.example" content-desc="" checkable="false" checked="false" clickable="true" '
    'enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" '
    'password="false" selected="false" bounds="[0,0][100,50]" /></hierarchy>'
)


def make_adb_device(serial="emulator-5554"):
    adb_device = MagicMock()
    adb_device.serial = serial
    adb_device.get_state.return_value = "device"
    adb_device.dump_hierarchy.return_value = VALID_XML
    adb_device.screenshot.return_value = Image.new("RGB", (10, 10))
    return adb_device


@patch("uiautomator3.device.device.get_device")
def test_inspect_caches_within_ttl(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["hierarchy_cache_ttl"] = 10.0

    tree1 = device.inspect()
    tree2 = device.inspect()

    assert tree1 is tree2
    assert adb_device.dump_hierarchy.call_count == 1


@patch("uiautomator3.device.device.get_device")
def test_inspect_force_bypasses_cache(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["hierarchy_cache_ttl"] = 10.0

    device.inspect()
    device.inspect(force=True)

    assert adb_device.dump_hierarchy.call_count == 2


@patch("uiautomator3.device.device.get_device")
def test_screenshot_caches_within_ttl(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["screenshot_cache_ttl"] = 10.0

    img1 = device.screenshot()
    img2 = device.screenshot()

    assert img1 is img2
    assert adb_device.screenshot.call_count == 1


@patch("uiautomator3.device.device.get_device")
def test_click_invalidates_hierarchy_cache(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["hierarchy_cache_ttl"] = 10.0

    device.inspect()
    device.click(10, 20)
    device.inspect()

    assert adb_device.dump_hierarchy.call_count == 2


@patch("uiautomator3.device.device.get_device")
def test_click_invalidates_screenshot_cache(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["screenshot_cache_ttl"] = 10.0

    device.screenshot()
    device.click(10, 20)
    device.screenshot()

    assert adb_device.screenshot.call_count == 2


@patch("uiautomator3.device.device.get_device")
def test_swipe_invalidates_hierarchy_cache(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["hierarchy_cache_ttl"] = 10.0

    device.inspect()
    device.swipe(0, 0, 100, 100)
    device.inspect()

    assert adb_device.dump_hierarchy.call_count == 2


@patch("uiautomator3.device.device.get_device")
def test_press_invalidates_hierarchy_cache(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["hierarchy_cache_ttl"] = 10.0

    device.inspect()
    device.press("back")
    device.inspect()

    assert adb_device.dump_hierarchy.call_count == 2


@patch("uiautomator3.device.device.get_device")
def test_locator_click_invalidates_hierarchy_cache(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["hierarchy_cache_ttl"] = 10.0

    device.inspect()
    device(text="Login").click()  # this triggers Device.click's own invalidation
    device.inspect()

    assert adb_device.dump_hierarchy.call_count >= 2


@patch("uiautomator3.device.device.get_device")
def test_zero_ttl_disables_hierarchy_caching(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")
    device.settings["hierarchy_cache_ttl"] = 0

    device.inspect()
    device.inspect()

    assert adb_device.dump_hierarchy.call_count == 2


@patch("uiautomator3.device.device.get_device")
def test_default_ttl_is_short_but_nonzero(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device.inspect()
    device.inspect()

    # default TTL (0.3s) means two immediate calls should be cached
    assert adb_device.dump_hierarchy.call_count == 1
