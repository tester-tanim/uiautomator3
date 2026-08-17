"""The fluent Locator object returned by Device.__call__()/find()/locator().

Per project spec section 58:
    locator = d.find("Login")
    locator.best_locator()
    locator.confidence
    locator.click()

Phase 7 adds opt-in self-healing (see healing/chain.py and
docs/UIAUTOMATOR3_ARCHITECTURE.md section 7): the first time a Locator
resolves successfully, it remembers the matched element's attributes; if a
later resolution finds zero matches and `d.settings["self_healing"]` is
True, it searches the current tree using that remembered snapshot instead
of immediately raising.
"""
import time
from typing import TYPE_CHECKING, List, Optional

from uiautomator3.exceptions import ElementAmbiguousError, ElementNotFoundError, LocatorHealingError
from uiautomator3.healing.chain import HealingReport, heal
from uiautomator3.healing.snapshot import ElementSnapshot
from uiautomator3.locator.generator import generate_candidates, rank_candidates
from uiautomator3.locator.locator_set import LocatorSet
from uiautomator3.selectors.query import Selector, find_all, find_first

if TYPE_CHECKING:
    from uiautomator3.device.device import Device
    from uiautomator3.elements.tree import ElementTree
    from uiautomator3.elements.uielement import UIElement


class Locator:
    """A lazily-evaluated selector bound to a Device.

    Each call to a resolving method (exists/click/wait/...) re-dumps the
    hierarchy and re-applies the selector - matching uiautomator2's
    default no-caching behavior for its XPath selector (see
    docs/UIAUTOMATOR2_ANALYSIS.md section 5), since UI state can change
    between calls.
    """

    def __init__(self, device: "Device", selector: Selector) -> None:
        self._device = device
        self.selector = selector
        self._snapshot: Optional[ElementSnapshot] = None
        self.last_healing_report: Optional[HealingReport] = None

    def __repr__(self) -> str:
        return f"Locator({self.selector!r})"

    # -- resolution --

    def _current_tree(self):
        return self._device.inspect()

    def all(self) -> List["UIElement"]:
        return find_all(self._current_tree(), self.selector)

    def first(self) -> Optional["UIElement"]:
        return find_first(self._current_tree(), self.selector)

    @property
    def exists(self) -> bool:
        return self.first() is not None

    def count(self) -> int:
        return len(self.all())

    def _healing_enabled(self) -> bool:
        return bool(self._device.settings.get("self_healing", False))

    def _try_heal(self, tree: "ElementTree") -> "UIElement":
        if self._snapshot is None:
            raise ElementNotFoundError(
                f"no element matched {self.selector!r}; self-healing has no prior snapshot to recover from "
                f"(this locator never resolved successfully before)"
            )

        min_confidence = self._device.settings.get("self_healing_min_confidence", 0.85)
        report = heal(tree, self.selector, self._snapshot, min_confidence=min_confidence)
        self.last_healing_report = report

        if not report.recovered or report.recovered_element is None:
            raise LocatorHealingError(
                f"self-healing failed for {self.selector!r}\n\n{report.format()}"
            )
        return report.recovered_element

    def _resolve_single_in(self, tree: "ElementTree") -> "UIElement":
        matches = find_all(tree, self.selector)
        if not matches:
            if self._healing_enabled():
                return self._try_heal(tree)
            raise ElementNotFoundError(f"no element matched {self.selector!r}")
        if len(matches) > 1:
            raise ElementAmbiguousError(
                f"{len(matches)} elements matched {self.selector!r}; "
                f"use .all() or add a more specific constraint"
            )
        element = matches[0]
        self._snapshot = ElementSnapshot.from_element(element)
        return element

    def _resolve_single(self) -> "UIElement":
        return self._resolve_single_in(self._current_tree())

    # -- locator intelligence --

    def locator_set(self) -> LocatorSet:
        tree = self._current_tree()
        element = self._resolve_single_in(tree)
        candidates = rank_candidates(generate_candidates(element, tree))
        return LocatorSet(element_id=element.id, candidates=candidates)

    def best_locator(self) -> Optional[str]:
        locator_set = self.locator_set()
        return locator_set.best.locator if locator_set.best else None

    @property
    def confidence(self) -> float:
        locator_set = self.locator_set()
        return locator_set.best.score if locator_set.best else 0.0

    def alternatives(self) -> List[str]:
        return [c.locator for c in self.locator_set().alternatives]

    def score(self) -> float:
        return self.confidence

    # -- actions --

    def _click_target(self, element: "UIElement", tree: "ElementTree") -> "UIElement":
        """Resolve the element a real tap would actually hit.

        Android's touch dispatch delivers a tap to the deepest *clickable*
        view under the point, not necessarily the exact node a selector
        matched (e.g. matching a launcher icon's label TextView, whose
        clickable ancestor is a RelativeLayout spanning icon+label - tapping
        the label's own center can miss the tap target entirely on some
        OEM launchers). Walk up to the nearest clickable ancestor; fall
        back to the matched element itself if none is clickable.
        """
        if element.clickable:
            return element
        current = tree.parent_of(element)
        while current is not None:
            if current.clickable:
                return current
            current = tree.parent_of(current)
        return element

    def _record(self, action: str, element: "UIElement", target: "UIElement", **extra) -> None:
        recording = getattr(self._device, "_recording", None)
        if recording is None:
            return
        recording.log(
            action,
            coordinates={"x": target.center.x, "y": target.center.y},
            element=element,
            locator=repr(self.selector),
            selector_criteria=dict(self.selector.criteria),
            screen=self._device._current_screen_label(),
            **extra,
        )

    def click(self) -> None:
        tree = self._current_tree()
        element = self._resolve_single_in(tree)
        target = self._click_target(element, tree)
        self._device.gesture.tap(target.center.x, target.center.y)
        self._device.invalidate_cache()
        self._record("click", element, target)

    def long_click(self, duration: float = 1.0) -> None:
        tree = self._current_tree()
        element = self._resolve_single_in(tree)
        target = self._click_target(element, tree)
        self._device.gesture.long_press(target.center.x, target.center.y, duration=duration)
        self._device.invalidate_cache()
        self._record("long_click", element, target, duration=duration)

    def wait(self, timeout: float = 10.0, interval: float = 0.3) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists:
                return True
            time.sleep(interval)
        return self.exists

    def wait_gone(self, timeout: float = 10.0, interval: float = 0.3) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self.exists:
                return True
            time.sleep(interval)
        return not self.exists

    def inspect(self) -> "UIElement":
        return self._resolve_single()

    # -- assertions --

    def assert_exists(self) -> "Locator":
        if not self.exists:
            raise ElementNotFoundError(f"expected element to exist: {self.selector!r}")
        return self

    def assert_visible(self) -> "Locator":
        element = self._resolve_single()
        if not element.visible:
            raise ElementNotFoundError(f"expected element to be visible: {self.selector!r}")
        return self

    def assert_enabled(self) -> "Locator":
        element = self._resolve_single()
        if not element.enabled:
            raise ElementNotFoundError(f"expected element to be enabled: {self.selector!r}")
        return self

    def assert_text(self, expected: str) -> "Locator":
        element = self._resolve_single()
        if element.text != expected:
            raise ElementNotFoundError(f"expected text {expected!r}, got {element.text!r}")
        return self
