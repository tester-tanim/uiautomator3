"""Device information snapshot (Phase 2 scope)."""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import adbutils


@dataclass
class DeviceInfo:
    serial: str
    model: Optional[str]
    brand: Optional[str]
    android_version: Optional[str]
    sdk_version: Optional[str]
    width: int
    height: int
    rotation: int


def collect_device_info(adb_device: "adbutils.AdbDevice") -> DeviceInfo:
    size = adb_device.window_size()
    return DeviceInfo(
        serial=adb_device.serial,
        model=adb_device.prop.model,
        brand=adb_device.prop.get("ro.product.brand"),
        android_version=adb_device.prop.get("ro.build.version.release"),
        sdk_version=adb_device.prop.get("ro.build.version.sdk"),
        width=int(size[0]),
        height=int(size[1]),
        rotation=adb_device.rotation(),
    )
