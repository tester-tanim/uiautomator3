from unittest.mock import MagicMock

import pytest

from uiautomator3.elements.uielement import Bounds, Point
from uiautomator3.exceptions import ElementNotFoundError
from uiautomator3.vision.locator import VisualLocator
from uiautomator3.vision.provider import VisionMatch


def make_device_and_provider(match):
    device = MagicMock()
    device.screenshot.return_value = MagicMock()
    provider = MagicMock()
    provider.find.return_value = match
    return device, provider


def test_exists_true_above_threshold():
    match = VisionMatch(similarity=0.95, point=Point(50, 50), bounds=Bounds(0, 0, 100, 100))
    device, provider = make_device_and_provider(match)
    locator = VisualLocator(device, MagicMock(), provider, threshold=0.8)

    assert locator.exists is True


def test_exists_false_below_threshold():
    match = VisionMatch(similarity=0.5, point=Point(50, 50), bounds=Bounds(0, 0, 100, 100))
    device, provider = make_device_and_provider(match)
    locator = VisualLocator(device, MagicMock(), provider, threshold=0.8)

    assert locator.exists is False


def test_exists_false_when_no_match():
    device, provider = make_device_and_provider(None)
    locator = VisualLocator(device, MagicMock(), provider)

    assert locator.exists is False


def test_click_clicks_match_point():
    match = VisionMatch(similarity=0.95, point=Point(123, 456), bounds=Bounds(0, 0, 100, 100))
    device, provider = make_device_and_provider(match)
    locator = VisualLocator(device, MagicMock(), provider)

    locator.click()

    device.click.assert_called_once_with(123, 456)


def test_click_raises_when_not_found():
    device, provider = make_device_and_provider(None)
    locator = VisualLocator(device, MagicMock(), provider)

    with pytest.raises(ElementNotFoundError):
        locator.click()


def test_wait_returns_match_when_found():
    match = VisionMatch(similarity=0.95, point=Point(1, 1), bounds=Bounds(0, 0, 10, 10))
    device, provider = make_device_and_provider(match)
    locator = VisualLocator(device, MagicMock(), provider)

    result = locator.wait(timeout=1)

    assert result is match


def test_wait_returns_none_on_timeout():
    device, provider = make_device_and_provider(None)
    locator = VisualLocator(device, MagicMock(), provider)

    assert locator.wait(timeout=0.2, interval=0.05) is None


def test_load_template_accepts_pil_image_directly():
    device = MagicMock()
    provider = MagicMock()
    from PIL import Image

    img = Image.new("RGB", (10, 10))
    locator = VisualLocator(device, img, provider)

    assert locator._template is img
