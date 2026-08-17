from unittest.mock import MagicMock

import pytest

from uiautomator3.exceptions import AdbError
from uiautomator3.gestures.gestures import GestureEngine


def make_engine():
    adb_device = MagicMock()
    return GestureEngine(adb_device), adb_device


def test_tap_calls_click():
    engine, adb_device = make_engine()
    engine.tap(100, 200)
    adb_device.click.assert_called_once_with(100, 200)


def test_tap_wraps_errors():
    engine, adb_device = make_engine()
    adb_device.click.side_effect = RuntimeError("boom")
    with pytest.raises(AdbError):
        engine.tap(1, 1)


def test_long_press_uses_swipe_in_place():
    engine, adb_device = make_engine()
    engine.long_press(50, 60, duration=1.5)
    adb_device.swipe.assert_called_once_with(50, 60, 50, 60, duration=1.5)


def test_swipe_tuple_form():
    engine, adb_device = make_engine()
    engine.swipe((10, 20), (30, 40), duration=0.3)
    adb_device.swipe.assert_called_once_with(10, 20, 30, 40, duration=0.3)


def test_swipe_points_chains_segments():
    engine, adb_device = make_engine()
    engine.swipe_points([(0, 0), (10, 10), (20, 20)], duration=1.0)
    assert adb_device.swipe.call_count == 2
    adb_device.swipe.assert_any_call(0, 0, 10, 10, duration=0.5)
    adb_device.swipe.assert_any_call(10, 10, 20, 20, duration=0.5)


def test_swipe_points_requires_two_points():
    engine, _ = make_engine()
    with pytest.raises(ValueError):
        engine.swipe_points([(0, 0)])


def test_drag_calls_adb_drag():
    engine, adb_device = make_engine()
    engine.drag((1, 2), (3, 4), duration=0.7)
    adb_device.drag.assert_called_once_with(1, 2, 3, 4, duration=0.7)


def test_press_maps_known_key_name():
    engine, adb_device = make_engine()
    engine.press("home")
    adb_device.keyevent.assert_called_once_with(3)


def test_press_passes_through_unknown_key():
    engine, adb_device = make_engine()
    engine.press("KEYCODE_A")
    adb_device.keyevent.assert_called_once_with("KEYCODE_A")


def test_press_passes_through_int_code():
    engine, adb_device = make_engine()
    engine.press(29)
    adb_device.keyevent.assert_called_once_with(29)


def test_long_press_key_shells_longpress():
    engine, adb_device = make_engine()
    engine.long_press_key("back")
    adb_device.shell.assert_called_once_with("input keyevent --longpress 4")
