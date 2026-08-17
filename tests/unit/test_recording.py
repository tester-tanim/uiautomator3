from unittest.mock import MagicMock, patch

from uiautomator3.device.device import Device
from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.recording.session import RecordingSession
from uiautomator3.selectors.locator_object import Locator
from uiautomator3.selectors.query import Selector


def make_adb_device(serial="emulator-5554"):
    adb_device = MagicMock()
    adb_device.serial = serial
    adb_device.get_state.return_value = "device"
    return adb_device


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
    )
    defaults.update(overrides)
    return UIElement(**defaults)


# -- RecordingSession --


def test_session_starts_empty():
    session = RecordingSession()
    assert session.actions == []


def test_log_appends_action():
    session = RecordingSession()
    session.log("click", coordinates={"x": 1, "y": 2})
    assert len(session.actions) == 1
    assert session.actions[0].action == "click"
    assert session.actions[0].coordinates == {"x": 1, "y": 2}


def test_log_captures_element_fields():
    session = RecordingSession()
    element = make_element("a")
    session.log("click", element=element, locator="d(text='Login')")
    entry = session.actions[0]
    assert entry.element_text == "Login"
    assert entry.element_resource_id == "com.example:id/login"
    assert entry.locator == "d(text='Login')"


def test_clear_empties_actions():
    session = RecordingSession()
    session.log("click")
    session.clear()
    assert session.actions == []


def test_as_list_returns_dicts():
    session = RecordingSession()
    session.log("click", coordinates={"x": 1, "y": 2})
    result = session.as_list()
    assert isinstance(result, list)
    assert result[0]["action"] == "click"


def test_action_as_dict_omits_element_when_absent():
    session = RecordingSession()
    session.log("press", key="home")
    entry_dict = session.actions[0].as_dict()
    assert entry_dict["element"] is None
    assert entry_dict["key"] == "home"


# -- Device recording integration --


@patch("uiautomator3.device.device.get_device")
def test_start_recording_returns_session(mock_get_device):
    mock_get_device.return_value = make_adb_device()
    device = Device(serial="emulator-5554")

    session = device.start_recording()

    assert isinstance(session, RecordingSession)
    assert device._recording is session


@patch("uiautomator3.device.device.get_device")
def test_no_recording_by_default(mock_get_device):
    adb_device = make_adb_device()
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device.click(10, 20)

    assert device._recording is None


@patch("uiautomator3.device.device.get_device")
def test_click_logged_when_recording(mock_get_device):
    adb_device = make_adb_device()
    adb_device.app_current.return_value = MagicMock(package="com.example", activity=".Main", pid=1)
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device.start_recording()
    device.click(10, 20)
    session = device.stop_recording()

    assert len(session.actions) == 1
    assert session.actions[0].action == "click"
    assert session.actions[0].coordinates == {"x": 10, "y": 20}
    assert session.actions[0].screen == "com.example/.Main"


@patch("uiautomator3.device.device.get_device")
def test_stop_recording_returns_none_if_never_started(mock_get_device):
    mock_get_device.return_value = make_adb_device()
    device = Device(serial="emulator-5554")

    assert device.stop_recording() is None


@patch("uiautomator3.device.device.get_device")
def test_stop_recording_disables_further_logging(mock_get_device):
    adb_device = make_adb_device()
    adb_device.app_current.return_value = MagicMock(package="com.example", activity=None, pid=1)
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device.start_recording()
    device.click(1, 1)
    device.stop_recording()
    device.click(2, 2)  # should not be logged anywhere retrievable

    assert device._recording is None


@patch("uiautomator3.device.device.get_device")
def test_multiple_gesture_types_logged(mock_get_device):
    adb_device = make_adb_device()
    adb_device.app_current.return_value = MagicMock(package="com.example", activity=None, pid=1)
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device.start_recording()
    device.click(1, 1)
    device.long_click(2, 2)
    device.swipe(0, 0, 10, 10)
    device.drag(0, 0, 20, 20)
    device.press("home")
    device.send_keys("hello")
    session = device.stop_recording()

    actions = [a.action for a in session.actions]
    assert actions == ["click", "long_click", "swipe", "drag", "press", "send_keys"]


@patch("uiautomator3.device.device.get_device")
def test_app_launch_and_stop_logged(mock_get_device):
    adb_device = make_adb_device()
    adb_device.app_current.return_value = MagicMock(package="com.example", activity=None, pid=1)
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device.start_recording()
    device.launch_app("com.example.app", "MainActivity")
    device.stop_app("com.example.app")
    session = device.stop_recording()

    assert [a.action for a in session.actions] == ["app_launch", "app_stop"]
    assert session.actions[0].extra["package"] == "com.example.app"


@patch("uiautomator3.device.device.get_device")
def test_locator_click_logs_richer_entry(mock_get_device):
    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = (
        '<hierarchy rotation="0">'
        '<node text="Login" resource-id="com.example:id/login" class="android.widget.Button" '
        'package="com.example" content-desc="" checkable="false" checked="false" clickable="true" '
        'enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" '
        'password="false" selected="false" bounds="[100,500][900,620]" /></hierarchy>'
    )
    adb_device.app_current.return_value = MagicMock(package="com.example", activity=None, pid=1)
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device.start_recording()
    device(text="Login").click()
    session = device.stop_recording()

    assert len(session.actions) == 1
    entry = session.actions[0]
    assert entry.action == "click"
    assert entry.element_text == "Login"
    assert entry.locator == "Selector(text='Login')"
    assert entry.coordinates == {"x": 500, "y": 560}


@patch("uiautomator3.device.device.get_device")
def test_locator_click_not_logged_when_not_recording(mock_get_device):
    adb_device = make_adb_device()
    adb_device.dump_hierarchy.return_value = (
        '<hierarchy rotation="0">'
        '<node text="Login" resource-id="com.example:id/login" class="android.widget.Button" '
        'package="com.example" content-desc="" checkable="false" checked="false" clickable="true" '
        'enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" '
        'password="false" selected="false" bounds="[100,500][900,620]" /></hierarchy>'
    )
    mock_get_device.return_value = adb_device
    device = Device(serial="emulator-5554")

    device(text="Login").click()  # no exception, no-op recording path

    assert device._recording is None


def test_locator_record_noop_when_device_has_no_recording_session():
    device = MagicMock(spec=["inspect", "gesture", "_recording", "_current_screen_label", "invalidate_cache"])
    device._recording = None
    device.inspect.return_value = ElementTree([make_element("a")])

    locator = Locator(device, Selector(text="Login"))
    locator.click()  # must not raise despite spec-limited mock

    device.gesture.tap.assert_called_once()
