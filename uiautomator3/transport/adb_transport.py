"""ADB shell transport.

Phase 1 needs a transport that works without the (not-yet-built) device-side
agent, so `u3.devices()`/`u3.doctor()` can prove connectivity against real
hardware. ADBTransport issues plain `adb shell` commands - no JSON-RPC agent
required. Later phases add an HTTPTransport that talks to the bundled
device-side agent (mirroring uiautomator2's proven "push a jar, talk
JSON-RPC over an adb tunnel" approach - see docs/UIAUTOMATOR2_ANALYSIS.md
section 2), while both share this same Transport interface.
"""
from typing import Any, Optional

import adbutils

from uiautomator3.config import get_config
from uiautomator3.exceptions import AdbError, TransportError
from uiautomator3.logging_config import get_logger
from uiautomator3.transport.base import Transport

logger = get_logger("transport.adb")


class ADBTransport(Transport):
    """Executes requests as `adb shell` commands against a single device."""

    def __init__(self, adb_device: "adbutils.AdbDevice") -> None:
        self._adb_device = adb_device
        self._connected = False

    def connect(self) -> None:
        try:
            self._adb_device.get_state()
        except Exception as e:
            raise TransportError(f"Failed to reach device via adb: {e}") from e
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def request(self, method: str, params: Optional[dict] = None, timeout: Optional[float] = None) -> Any:
        """`method` is treated as a raw shell command for this transport."""
        params = params or {}
        cmd = params.get("cmd", method)
        req_timeout = timeout or get_config().request_timeout
        try:
            return self._adb_device.shell(cmd, timeout=req_timeout)
        except Exception as e:
            raise AdbError(f"adb shell command failed: {cmd!r}: {e}") from e
