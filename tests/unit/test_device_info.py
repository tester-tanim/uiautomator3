from unittest.mock import MagicMock

from uiautomator3.device.info import collect_device_info


def test_collect_device_info():
    adb_device = MagicMock()
    adb_device.serial = "emulator-5554"
    adb_device.prop.model = "Pixel 8"
    adb_device.prop.get.side_effect = lambda key: {
        "ro.product.brand": "Google",
        "ro.build.version.release": "14",
        "ro.build.version.sdk": "34",
    }[key]
    adb_device.window_size.return_value = (1080, 2400)
    adb_device.rotation.return_value = 0

    info = collect_device_info(adb_device)

    assert info.serial == "emulator-5554"
    assert info.model == "Pixel 8"
    assert info.brand == "Google"
    assert info.android_version == "14"
    assert info.sdk_version == "34"
    assert info.width == 1080
    assert info.height == 2400
    assert info.rotation == 0
