from unittest.mock import MagicMock

import pytest

from uiautomator3.apps.app_manager import AppManager
from uiautomator3.exceptions import AppLaunchError


def make_manager():
    adb_device = MagicMock()
    return AppManager(adb_device), adb_device


def test_install_delegates():
    manager, adb_device = make_manager()
    manager.install("app.apk", uninstall_first=True)
    adb_device.install.assert_called_once_with("app.apk", uninstall=True)


def test_uninstall_delegates():
    manager, adb_device = make_manager()
    manager.uninstall("com.example.app")
    adb_device.uninstall.assert_called_once_with("com.example.app")


def test_start_delegates():
    manager, adb_device = make_manager()
    manager.start("com.example.app", "MainActivity")
    adb_device.app_start.assert_called_once_with("com.example.app", "MainActivity")


def test_start_wraps_errors():
    manager, adb_device = make_manager()
    adb_device.app_start.side_effect = RuntimeError("boom")
    with pytest.raises(AppLaunchError):
        manager.start("com.example.app")


def test_restart_stops_then_starts():
    manager, adb_device = make_manager()
    manager.restart("com.example.app")
    adb_device.app_stop.assert_called_once_with("com.example.app")
    adb_device.app_start.assert_called_once_with("com.example.app", None)


def test_current_maps_running_app_info():
    manager, adb_device = make_manager()
    info = MagicMock(package="com.example.app", activity=".MainActivity", pid=1234)
    adb_device.app_current.return_value = info

    result = manager.current()

    assert result.package == "com.example.app"
    assert result.activity == ".MainActivity"
    assert result.pid == 1234


def test_is_running_true_when_matches():
    manager, adb_device = make_manager()
    adb_device.app_current.return_value = MagicMock(package="com.example.app", activity=None, pid=1)
    assert manager.is_running("com.example.app") is True


def test_is_running_false_when_no_match():
    manager, adb_device = make_manager()
    adb_device.app_current.return_value = MagicMock(package="com.other.app", activity=None, pid=1)
    assert manager.is_running("com.example.app") is False


def test_is_running_false_on_error():
    manager, adb_device = make_manager()
    adb_device.app_current.side_effect = RuntimeError("boom")
    assert manager.is_running("com.example.app") is False


def test_info_returns_none_when_not_found():
    manager, adb_device = make_manager()
    adb_device.app_info.return_value = None
    assert manager.info("com.example.app") is None


def test_info_maps_app_info():
    manager, adb_device = make_manager()
    adb_device.app_info.return_value = MagicMock(version_name="1.2.3", version_code=45)

    result = manager.info("com.example.app")

    assert result.package_name == "com.example.app"
    assert result.version_name == "1.2.3"
    assert result.version_code == 45


def test_list_packages_delegates():
    manager, adb_device = make_manager()
    adb_device.list_packages.return_value = ["a", "b"]
    assert manager.list_packages() == ["a", "b"]
