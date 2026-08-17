from unittest.mock import MagicMock

import pytest
from PIL import Image

from uiautomator3.exceptions import AdbError
from uiautomator3.screenshots.screenshot import ScreenshotEngine


def make_engine():
    adb_device = MagicMock()
    return ScreenshotEngine(adb_device), adb_device


def test_capture_returns_image():
    engine, adb_device = make_engine()
    fake_image = Image.new("RGB", (100, 200))
    adb_device.screenshot.return_value = fake_image

    result = engine.capture()

    assert result is fake_image
    adb_device.screenshot.assert_called_once_with(display_id=None, error_ok=False)


def test_capture_wraps_errors():
    engine, adb_device = make_engine()
    adb_device.screenshot.side_effect = RuntimeError("boom")
    with pytest.raises(AdbError):
        engine.capture()


def test_save_writes_file(tmp_path):
    engine, adb_device = make_engine()
    adb_device.screenshot.return_value = Image.new("RGB", (10, 10))

    out_path = str(tmp_path / "shot.png")
    result = engine.save(out_path)

    assert result == out_path
    assert (tmp_path / "shot.png").exists()


def test_region_crops_image():
    engine, adb_device = make_engine()
    adb_device.screenshot.return_value = Image.new("RGB", (100, 100))

    cropped = engine.region(10, 10, 50, 50)

    assert cropped.size == (40, 40)


def test_capture_is_cached_within_ttl():
    engine, adb_device = make_engine()
    adb_device.screenshot.return_value = Image.new("RGB", (10, 10))

    img1 = engine.capture(ttl=10.0)
    img2 = engine.capture(ttl=10.0)

    assert img1 is img2
    assert adb_device.screenshot.call_count == 1


def test_capture_force_bypasses_cache():
    engine, adb_device = make_engine()
    adb_device.screenshot.return_value = Image.new("RGB", (10, 10))

    engine.capture(ttl=10.0)
    engine.capture(ttl=10.0, force=True)

    assert adb_device.screenshot.call_count == 2


def test_capture_zero_ttl_never_caches():
    engine, adb_device = make_engine()
    adb_device.screenshot.return_value = Image.new("RGB", (10, 10))

    engine.capture(ttl=0)
    engine.capture(ttl=0)

    assert adb_device.screenshot.call_count == 2


def test_different_display_ids_cached_independently():
    engine, adb_device = make_engine()
    adb_device.screenshot.return_value = Image.new("RGB", (10, 10))

    engine.capture(display_id=0, ttl=10.0)
    engine.capture(display_id=1, ttl=10.0)

    assert adb_device.screenshot.call_count == 2


def test_invalidate_clears_all_display_caches():
    engine, adb_device = make_engine()
    adb_device.screenshot.return_value = Image.new("RGB", (10, 10))

    engine.capture(display_id=0, ttl=10.0)
    engine.capture(display_id=1, ttl=10.0)
    engine.invalidate()
    engine.capture(display_id=0, ttl=10.0)
    engine.capture(display_id=1, ttl=10.0)

    assert adb_device.screenshot.call_count == 4
