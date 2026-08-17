from unittest.mock import MagicMock

import pytest

from uiautomator3.hierarchy.collector import HierarchyCollector, HierarchyEmptyError

VALID_XML = "<hierarchy rotation=\"0\"><node bounds=\"[0,0][100,100]\" /></hierarchy>"
EMPTY_XML = "<hierarchy rotation=\"0\" />"


def make_collector():
    adb_device = MagicMock()
    return HierarchyCollector(adb_device), adb_device


def test_dump_returns_xml_on_first_success():
    collector, adb_device = make_collector()
    adb_device.dump_hierarchy.return_value = VALID_XML

    result = collector.dump()

    assert result == VALID_XML
    adb_device.dump_hierarchy.assert_called_once()


def test_dump_retries_on_empty_hierarchy():
    collector, adb_device = make_collector()
    adb_device.dump_hierarchy.side_effect = [EMPTY_XML, EMPTY_XML, VALID_XML]

    result = collector.dump(retries=3, retry_delay=0)

    assert result == VALID_XML
    assert adb_device.dump_hierarchy.call_count == 3


def test_dump_raises_after_exhausting_retries_on_empty():
    collector, adb_device = make_collector()
    adb_device.dump_hierarchy.return_value = EMPTY_XML

    with pytest.raises(HierarchyEmptyError):
        collector.dump(retries=2, retry_delay=0)
    assert adb_device.dump_hierarchy.call_count == 2


def test_dump_retries_on_exception():
    collector, adb_device = make_collector()
    adb_device.dump_hierarchy.side_effect = [RuntimeError("boom"), VALID_XML]

    result = collector.dump(retries=2, retry_delay=0)

    assert result == VALID_XML


def test_dump_raises_last_error_after_exhausting_retries_on_exception():
    collector, adb_device = make_collector()
    adb_device.dump_hierarchy.side_effect = RuntimeError("persistent failure")

    with pytest.raises(RuntimeError, match="persistent failure"):
        collector.dump(retries=2, retry_delay=0)
