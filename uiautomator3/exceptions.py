"""Typed exception hierarchy for UIAutomator 3.0.

    UIAutomator3Error
    ├── DeviceConnectionError
    │   └── DeviceNotFoundError
    ├── TransportError
    │   └── TransportTimeoutError
    ├── AdbError
    ├── ElementNotFoundError
    ├── ElementAmbiguousError
    ├── SelectorError
    ├── LocatorHealingError
    ├── InspectorError
    ├── OCRProviderError
    ├── VisionProviderError
    └── AppLaunchError

Note: unlike uiautomator2's ``exceptions.py``, the root class here is named
``UIAutomator3Error`` rather than ``BaseException`` so it never shadows the
Python builtin of the same name.
"""


class UIAutomator3Error(Exception):
    """Base class for all UIAutomator 3.0 errors."""


class DeviceConnectionError(UIAutomator3Error):
    """Raised when a device cannot be connected to or communicated with."""


class DeviceNotFoundError(DeviceConnectionError):
    """Raised when no matching device is found."""


class TransportError(UIAutomator3Error):
    """Raised when the transport layer fails to complete a request."""


class TransportTimeoutError(TransportError):
    """Raised when a transport request exceeds its timeout."""


class AdbError(UIAutomator3Error):
    """Raised when an ADB command fails."""


class ElementNotFoundError(UIAutomator3Error):
    """Raised when a locator matches no elements."""


class ElementAmbiguousError(UIAutomator3Error):
    """Raised when a locator matches multiple elements and none can be
    disambiguated automatically."""


class SelectorError(UIAutomator3Error):
    """Raised for invalid or malformed selector input."""


class LocatorHealingError(UIAutomator3Error):
    """Raised when self-healing fails to recover a broken locator."""


class InspectorError(UIAutomator3Error):
    """Raised for inspector pipeline failures."""


class OCRProviderError(UIAutomator3Error):
    """Raised when an OCR provider fails."""


class VisionProviderError(UIAutomator3Error):
    """Raised when a vision provider fails."""


class AppLaunchError(UIAutomator3Error):
    """Raised when an application fails to launch."""
