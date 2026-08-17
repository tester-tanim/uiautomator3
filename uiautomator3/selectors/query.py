"""Selector query engine.

Matches UIElement objects in an already-collected ElementTree, unlike
uiautomator2's Selector/UiObject which encodes a UiSelector bitmask and
sends it device-side for matching (see docs/UIAUTOMATOR2_ANALYSIS.md
section 4). Querying against a local snapshot means every locator strategy
- literal selector, XPath (future), OCR (future) - runs over the same
UIElement data, per docs/UIAUTOMATOR3_ARCHITECTURE.md's "one element model"
principle.
"""

import re
from typing import Any, ClassVar, Dict, List, Optional

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import UIElement


class Selector:
    """A set of match criteria for UIElement fields.

    Supports exact-match kwargs (`text="Login"`) and suffixed variants:
    `textContains`, `textStartsWith`, `textEndsWith`, `textMatches` (regex),
    and the equivalent for `resourceId`/`description`/`className`.
    """

    _FIELD_ALIASES: ClassVar[Dict[str, str]] = {
        "resourceId": "resource_id",
        "resource_id": "resource_id",
        "description": "content_description",
        "content_desc": "content_description",
        "content_description": "content_description",
        "className": "class_name",
        "class_name": "class_name",
        "packageName": "package_name",
        "package_name": "package_name",
    }

    _SUFFIXES = ("Contains", "StartsWith", "EndsWith", "Matches")
    _BASE_FIELDS = ("text", "resourceId", "description", "className", "packageName")
    _BOOL_FIELDS = (
        "clickable",
        "enabled",
        "focused",
        "selected",
        "checked",
        "scrollable",
        "long_clickable",
        "checkable",
        "password",
        "visible",
    )

    def __init__(self, **kwargs: Any) -> None:
        self.criteria: Dict[str, Any] = {}
        for key, value in kwargs.items():
            self.criteria[key] = value

    def __repr__(self) -> str:
        parts = ", ".join(f"{k}={v!r}" for k, v in self.criteria.items())
        return f"Selector({parts})"

    def matches(self, element: UIElement) -> bool:
        for key, expected in self.criteria.items():
            if not self._matches_one(element, key, expected):
                return False
        return True

    def _matches_one(self, element: UIElement, key: str, expected: Any) -> bool:
        if key in self._BOOL_FIELDS:
            return getattr(element, key) == expected

        if key == "index":
            return element.index == expected
        if key == "role":
            return element.role == expected
        if key == "id":
            return element.id == expected

        for suffix in self._SUFFIXES:
            if key.endswith(suffix):
                base = key[: -len(suffix)]
                field = self._resolve_field(base)
                actual = getattr(element, field, None)
                return self._apply_suffix(actual, expected, suffix)

        field = self._resolve_field(key)
        actual = getattr(element, field, None)
        return actual == expected

    def _resolve_field(self, base: str) -> str:
        if base in self._FIELD_ALIASES:
            return self._FIELD_ALIASES[base]
        # normalize e.g. "text" -> "text"
        return base

    @staticmethod
    def _apply_suffix(actual: Optional[str], expected: str, suffix: str) -> bool:
        if actual is None:
            return False
        if suffix == "Contains":
            return expected in actual
        if suffix == "StartsWith":
            return actual.startswith(expected)
        if suffix == "EndsWith":
            return actual.endswith(expected)
        if suffix == "Matches":
            return re.search(expected, actual) is not None
        return False


def find_all(tree: ElementTree, selector: Selector) -> List[UIElement]:
    return [e for e in tree if selector.matches(e)]


def find_first(tree: ElementTree, selector: Selector) -> Optional[UIElement]:
    for e in tree:
        if selector.matches(e):
            return e
    return None
