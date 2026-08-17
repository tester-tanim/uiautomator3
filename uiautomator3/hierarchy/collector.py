"""Hierarchy collection.

Uses the standard `uiautomator dump` shell command (via adbutils), the same
mechanism uiautomator2 uses for `dump_hierarchy()` (see
docs/UIAUTOMATOR2_ANALYSIS.md section 6), requiring no device-side agent.
Retries on the known empty-dump flakiness uiautomator2 also works around.
"""

import time
from typing import TYPE_CHECKING

from uiautomator3.exceptions import UIAutomator3Error
from uiautomator3.logging_config import get_logger

if TYPE_CHECKING:
    import adbutils

logger = get_logger("hierarchy.collector")


class HierarchyEmptyError(UIAutomator3Error):
    """Raised when the device repeatedly returns an empty hierarchy dump."""


class HierarchyCollector:
    """Collects raw hierarchy XML from a device."""

    def __init__(self, adb_device: "adbutils.AdbDevice") -> None:
        self._adb_device = adb_device

    def dump(self, retries: int = 3, retry_delay: float = 1.0) -> str:
        last_error = None
        for attempt in range(retries):
            try:
                xml_data = self._adb_device.dump_hierarchy()
            except Exception as e:
                last_error = e
                logger.debug("hierarchy dump attempt %d failed: %s", attempt + 1, e)
                time.sleep(retry_delay)
                continue

            if self._is_empty(xml_data):
                last_error = HierarchyEmptyError("device returned an empty hierarchy dump")
                logger.debug("hierarchy dump attempt %d was empty, retrying", attempt + 1)
                time.sleep(retry_delay)
                continue

            return xml_data

        raise last_error or HierarchyEmptyError("hierarchy dump failed after retries")

    @staticmethod
    def _is_empty(xml_data: str) -> bool:
        stripped = xml_data.strip()
        return "<node" not in stripped
