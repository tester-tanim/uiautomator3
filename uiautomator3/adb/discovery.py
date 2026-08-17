"""ADB device discovery.

Wraps adbutils for device enumeration, following uiautomator2's proven
choice of adbutils as the ADB integration library (see
docs/UIAUTOMATOR2_ANALYSIS.md section 3).
"""

from typing import List, Optional

import adbutils

from uiautomator3.exceptions import DeviceNotFoundError
from uiautomator3.logging_config import get_logger

logger = get_logger("adb.discovery")


def list_devices() -> List["adbutils.AdbDevice"]:
    """Return all currently connected/authorized ADB devices."""
    return list(adbutils.adb.device_list())


def get_device(serial: Optional[str] = None) -> "adbutils.AdbDevice":
    """Resolve a single ADB device by serial, or the first attached device."""
    if serial:
        try:
            return adbutils.adb.device(serial=serial)
        except Exception as e:
            raise DeviceNotFoundError(f"No device found with serial {serial!r}: {e}") from e

    devices = list_devices()
    if not devices:
        raise DeviceNotFoundError("No ADB devices attached")
    return devices[0]
