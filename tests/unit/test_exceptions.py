import uiautomator3 as u3
from uiautomator3.exceptions import (
    AdbError,
    DeviceConnectionError,
    DeviceNotFoundError,
    TransportError,
    TransportTimeoutError,
    UIAutomator3Error,
)


def test_hierarchy():
    assert issubclass(DeviceNotFoundError, DeviceConnectionError)
    assert issubclass(DeviceConnectionError, UIAutomator3Error)
    assert issubclass(TransportTimeoutError, TransportError)
    assert issubclass(TransportError, UIAutomator3Error)
    assert issubclass(AdbError, UIAutomator3Error)
    assert issubclass(UIAutomator3Error, Exception)


def test_does_not_shadow_builtin_base_exception():
    assert u3.UIAutomator3Error is not BaseException
    assert issubclass(u3.UIAutomator3Error, Exception)
