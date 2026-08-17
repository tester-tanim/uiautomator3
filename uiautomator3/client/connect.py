"""Public connection entry points: `u3.connect()` and `u3.devices()`."""

import os
from typing import List, Optional

from uiautomator3.adb.discovery import list_devices as _list_adb_devices
from uiautomator3.device.device import Device


def connect(serial: Optional[str] = None) -> Device:
    """Connect to an Android device.

    :param serial: device serial. Falls back to the ``ANDROID_SERIAL``
        environment variable, then the first attached device.
    """
    serial = serial or os.environ.get("ANDROID_SERIAL")
    return Device(serial=serial)


def devices() -> List[Device]:
    """Return a Device for every currently attached/authorized ADB device."""
    return [Device(serial=d.serial) for d in _list_adb_devices()]
