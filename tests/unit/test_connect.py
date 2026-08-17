from unittest.mock import MagicMock, patch

import uiautomator3 as u3


def make_adb_device(serial):
    adb_device = MagicMock()
    adb_device.serial = serial
    adb_device.get_state.return_value = "device"
    return adb_device


@patch("uiautomator3.device.device.get_device")
def test_connect_returns_device(mock_get_device):
    mock_get_device.return_value = make_adb_device("emulator-5554")

    device = u3.connect("emulator-5554")

    assert isinstance(device, u3.Device)
    assert device.serial == "emulator-5554"


@patch("uiautomator3.client.connect._list_adb_devices")
@patch("uiautomator3.device.device.get_device")
def test_devices_returns_one_per_attached_device(mock_get_device, mock_list_adb_devices):
    d1, d2 = make_adb_device("dev1"), make_adb_device("dev2")
    mock_list_adb_devices.return_value = [d1, d2]
    mock_get_device.side_effect = lambda serial=None: {"dev1": d1, "dev2": d2}[serial]

    devs = u3.devices()

    assert [d.serial for d in devs] == ["dev1", "dev2"]


@patch("uiautomator3.client.connect.os.environ.get", return_value="env-serial")
@patch("uiautomator3.device.device.get_device")
def test_connect_falls_back_to_env_var(mock_get_device, _mock_env_get):
    mock_get_device.return_value = make_adb_device("env-serial")

    device = u3.connect()

    assert device.serial == "env-serial"
