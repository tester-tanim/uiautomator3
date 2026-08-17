from unittest.mock import MagicMock

import pytest

from uiautomator3.elements.uielement import Bounds
from uiautomator3.exceptions import ElementNotFoundError
from uiautomator3.ocr.locator import OCRLocator
from uiautomator3.ocr.provider import OCRTextRegion


def make_device_and_provider(regions):
    device = MagicMock()
    device.screenshot.return_value = MagicMock()
    provider = MagicMock()
    provider.detect_text.return_value = regions
    return device, provider


def test_exists_true_on_substring_match():
    region = OCRTextRegion(text="Login Button", bounds=Bounds(0, 0, 100, 40), confidence=0.9)
    device, provider = make_device_and_provider([region])
    locator = OCRLocator(device, "Login", provider)

    assert locator.exists is True


def test_exists_false_when_no_match():
    device, provider = make_device_and_provider([])
    locator = OCRLocator(device, "Login", provider)

    assert locator.exists is False


def test_exact_mode_requires_full_match():
    region = OCRTextRegion(text="Login Button", bounds=Bounds(0, 0, 100, 40), confidence=0.9)
    device, provider = make_device_and_provider([region])

    substring_locator = OCRLocator(device, "Login", provider, exact=False)
    exact_locator = OCRLocator(device, "Login", provider, exact=True)

    assert substring_locator.exists is True
    assert exact_locator.exists is False


def test_click_clicks_region_center():
    region = OCRTextRegion(text="Login", bounds=Bounds(0, 0, 100, 40), confidence=0.9)
    device, provider = make_device_and_provider([region])
    locator = OCRLocator(device, "Login", provider)

    locator.click()

    device.click.assert_called_once_with(50, 20)


def test_click_raises_when_not_found():
    device, provider = make_device_and_provider([])
    locator = OCRLocator(device, "Login", provider)

    with pytest.raises(ElementNotFoundError):
        locator.click()


def test_wait_returns_true_immediately_when_found():
    region = OCRTextRegion(text="Login", bounds=Bounds(0, 0, 100, 40), confidence=0.9)
    device, provider = make_device_and_provider([region])
    locator = OCRLocator(device, "Login", provider)

    assert locator.wait(timeout=1) is True


def test_wait_returns_false_on_timeout():
    device, provider = make_device_and_provider([])
    locator = OCRLocator(device, "Login", provider)

    assert locator.wait(timeout=0.2, interval=0.05) is False
