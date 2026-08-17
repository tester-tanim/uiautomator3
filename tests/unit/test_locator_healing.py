from unittest.mock import MagicMock

import pytest

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.exceptions import ElementNotFoundError, LocatorHealingError
from uiautomator3.selectors.locator_object import Locator
from uiautomator3.selectors.query import Selector
from uiautomator3.settings import Settings


def make_element(id, **overrides):
    defaults = dict(
        id=id,
        text=None,
        content_description=None,
        resource_id=None,
        class_name=None,
        package_name="com.example",
        bounds=Bounds(100, 500, 900, 620),
        clickable=True,
        enabled=True,
        visible=True,
        focused=False,
        selected=False,
        checked=False,
        scrollable=False,
        long_clickable=False,
        checkable=False,
        password=False,
        parent_id=None,
    )
    defaults.update(overrides)
    return UIElement(**defaults)


def make_device_with_sequential_trees(tree_sequence):
    """Device.inspect() returns each tree in `tree_sequence` in order,
    repeating the last one once exhausted."""
    device = MagicMock()
    device.settings = Settings()
    remaining = list(tree_sequence)

    def _inspect():
        if len(remaining) > 1:
            return remaining.pop(0)
        return remaining[0]

    device.inspect.side_effect = _inspect
    return device


def test_healing_disabled_by_default_raises_immediately():
    tree = ElementTree([])
    device = make_device_with_sequential_trees([tree])
    locator = Locator(device, Selector(resourceId="old_id"))

    with pytest.raises(ElementNotFoundError):
        locator.click()


def test_healing_without_prior_snapshot_raises_element_not_found():
    tree = ElementTree([])
    device = make_device_with_sequential_trees([tree])
    device.settings["self_healing"] = True
    locator = Locator(device, Selector(resourceId="old_id"))

    # never resolved successfully before -> nothing to heal from
    with pytest.raises(ElementNotFoundError):
        locator.click()


def test_healing_recovers_after_resource_id_changes():
    original = make_element("a", resource_id="old_id", text="Login")
    tree_v1 = ElementTree([original])

    renamed = make_element("a", resource_id="new_id", text="Login")
    tree_v2 = ElementTree([renamed])

    device = make_device_with_sequential_trees([tree_v1, tree_v2])
    device.settings["self_healing"] = True
    locator = Locator(device, Selector(resourceId="old_id"))

    # first click succeeds normally and captures a snapshot
    locator.click()
    device.gesture.tap.assert_called_with(500, 560)

    # second click: resourceId="old_id" no longer matches (tree_v2), but
    # healing should recover via the remembered text="Login"
    locator.click()
    assert device.gesture.tap.call_count == 2
    assert locator.last_healing_report is not None
    assert locator.last_healing_report.recovered is True
    assert locator.last_healing_report.recovered_via == "text"


def test_healing_raises_locator_healing_error_when_no_candidate_found():
    original = make_element("a", resource_id="old_id", text="Login")
    tree_v1 = ElementTree([original])
    tree_v2 = ElementTree([])  # element disappeared entirely

    device = make_device_with_sequential_trees([tree_v1, tree_v2])
    device.settings["self_healing"] = True
    locator = Locator(device, Selector(resourceId="old_id"))

    locator.click()  # captures snapshot

    with pytest.raises(LocatorHealingError):
        locator.click()


def test_exists_does_not_trigger_healing_or_snapshot():
    tree = ElementTree([make_element("a", resource_id="id/login", text="Login")])
    device = make_device_with_sequential_trees([tree])
    device.settings["self_healing"] = True
    locator = Locator(device, Selector(resourceId="id/login"))

    assert locator.exists is True
    # .exists uses find_first directly, not _resolve_single_in, so no
    # snapshot is captured as a side effect of merely checking existence
    assert locator._snapshot is None
