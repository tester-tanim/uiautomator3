"""Application lifecycle management.

Phase 2 scope: install, uninstall, start, stop, restart, clear_data,
current, is_running. Deliberately routed through adbutils'
`pm`/`am`-backed methods rather than a device-side JSON-RPC agent -
uiautomator2's own design keeps app management on raw ADB so it keeps
working even if the automation server itself is down (see
docs/UIAUTOMATOR2_ANALYSIS.md section 10); Phase 2 has no agent yet at all,
so this is the only viable path, and it is also the right long-term choice.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from uiautomator3.exceptions import AppLaunchError

if TYPE_CHECKING:
    import adbutils

from uiautomator3.logging_config import get_logger

logger = get_logger("apps")


@dataclass
class AppInfo:
    package_name: str
    version_name: Optional[str] = None
    version_code: Optional[int] = None


@dataclass
class RunningAppInfo:
    package: str
    activity: Optional[str] = None
    pid: Optional[int] = None


class AppManager:
    """App install/uninstall/lifecycle control for a single device."""

    def __init__(self, adb_device: "adbutils.AdbDevice") -> None:
        self._adb_device = adb_device

    def install(self, path_or_url: str, uninstall_first: bool = False) -> None:
        self._adb_device.install(path_or_url, uninstall=uninstall_first)

    def uninstall(self, package_name: str) -> None:
        self._adb_device.uninstall(package_name)

    def start(self, package_name: str, activity: Optional[str] = None) -> None:
        try:
            self._adb_device.app_start(package_name, activity)
        except Exception as e:
            raise AppLaunchError(f"failed to start {package_name}: {e}") from e

    def stop(self, package_name: str) -> None:
        self._adb_device.app_stop(package_name)

    def restart(self, package_name: str, activity: Optional[str] = None) -> None:
        self.stop(package_name)
        self.start(package_name, activity)

    def clear_data(self, package_name: str) -> None:
        self._adb_device.app_clear(package_name)

    def current(self) -> RunningAppInfo:
        info = self._adb_device.app_current()
        return RunningAppInfo(package=info.package, activity=info.activity, pid=info.pid)

    def is_running(self, package_name: str) -> bool:
        try:
            return self.current().package == package_name
        except Exception:
            return False

    def info(self, package_name: str) -> Optional[AppInfo]:
        result = self._adb_device.app_info(package_name)
        if result is None:
            return None
        return AppInfo(
            package_name=package_name,
            version_name=getattr(result, "version_name", None),
            version_code=getattr(result, "version_code", None),
        )

    def list_packages(self) -> List[str]:
        return self._adb_device.list_packages()
