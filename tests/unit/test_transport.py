from unittest.mock import MagicMock

import pytest

from uiautomator3.exceptions import AdbError, TransportError
from uiautomator3.transport.adb_transport import ADBTransport


def make_transport(adb_device=None):
    adb_device = adb_device or MagicMock()
    return ADBTransport(adb_device), adb_device


def test_connect_success():
    transport, adb_device = make_transport()
    adb_device.get_state.return_value = "device"

    transport.connect()

    assert transport.is_connected()


def test_connect_failure_raises_transport_error():
    transport, adb_device = make_transport()
    adb_device.get_state.side_effect = RuntimeError("boom")

    with pytest.raises(TransportError):
        transport.connect()
    assert not transport.is_connected()


def test_request_shells_out():
    transport, adb_device = make_transport()
    adb_device.shell.return_value = "hello"

    result = transport.request("echo hello", {"cmd": "echo hello"})

    assert result == "hello"
    adb_device.shell.assert_called_once()


def test_request_failure_raises_adb_error():
    transport, adb_device = make_transport()
    adb_device.shell.side_effect = RuntimeError("shell broke")

    with pytest.raises(AdbError):
        transport.request("bad cmd", {"cmd": "bad cmd"})


def test_close_marks_disconnected():
    transport, adb_device = make_transport()
    adb_device.get_state.return_value = "device"
    transport.connect()

    transport.close()

    assert not transport.is_connected()
