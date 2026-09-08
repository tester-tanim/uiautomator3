"""XPath 1.0 evaluation over the normalized UI element tree."""

import re
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import UIElement
from uiautomator3.exceptions import XPathError

if TYPE_CHECKING:
    from uiautomator3.elements.tree import ElementTree


_CLASS_STEP = re.compile(r"(?P<prefix>/+)(?P<name>[A-Za-z_][\w.-]*)")


def _class_names(tree: ElementTree) -> Dict[str, Set[str]]:
    result: Dict[str, Set[str]] = {}
    for element in tree:
        if not element.class_name:
            continue
        short_name = element.class_name.rsplit(".", 1)[-1]
        result.setdefault(short_name, set()).add(element.class_name)
    return result


def _rewrite_class_shorthand(expression: str, tree: ElementTree) -> str:
    """Rewrite ``//TextView`` to an attribute test without touching strings."""
    class_names = _class_names(tree)
    pieces: List[str] = []
    start = 0
    quote: Optional[str] = None
    for index, character in enumerate(expression):
        if character in ("'", '"'):
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
        if quote is not None or character not in ("'", '"'):
            continue
        pieces.append(expression[start : index + 1])
        start = index + 1
    pieces.append(expression[start:])

    rewritten: List[str] = []
    for piece in pieces:
        if piece.startswith("'") or piece.startswith('"'):
            rewritten.append(piece)
            continue

        def replace(match: re.Match) -> str:
            names = class_names.get(match.group("name"))
            if not names or match.group("name") == "node":
                return match.group(0)
            if len(names) > 1:
                return match.group(0)
            return "%s*[@class=%r]" % (match.group("prefix"), next(iter(names)))

        rewritten.append(_CLASS_STEP.sub(replace, piece))
    return "".join(rewritten)


def _build_xml(tree: ElementTree):
    try:
        from lxml import etree
    except ImportError as error:
        raise XPathError("XPath support requires the optional dependency; install with `pip install uiautomator3[xpath]`") from error

    root = etree.Element("hierarchy")
    xml_nodes = {}
    for element in tree:
        if tree.parent_of(element) is None:
            parent = root
        else:
            parent = xml_nodes[element.parent_id]
        attributes = {
            "text": element.text or "",
            "content-desc": element.content_description or "",
            "resource-id": element.resource_id or "",
            "class": element.class_name or "",
            "package": element.package_name or "",
            "clickable": str(element.clickable).lower(),
            "enabled": str(element.enabled).lower(),
            "focused": str(element.focused).lower(),
            "selected": str(element.selected).lower(),
            "checked": str(element.checked).lower(),
            "scrollable": str(element.scrollable).lower(),
            "long-clickable": str(element.long_clickable).lower(),
            "checkable": str(element.checkable).lower(),
            "password": str(element.password).lower(),
            "bounds": "[%d,%d][%d,%d]" % (
                element.bounds.left,
                element.bounds.top,
                element.bounds.right,
                element.bounds.bottom,
            ),
            "data-uiautomator3-id": element.id,
        }
        xml_nodes[element.id] = etree.SubElement(parent, "node", attrib=attributes)
    return etree, root, xml_nodes


def find_all_xpath(tree: ElementTree, expression: str) -> List[UIElement]:
    """Evaluate an XPath 1.0 expression and return matching UI elements."""
    if not isinstance(expression, str) or not expression.strip():
        raise XPathError("XPath expression must be a non-empty string")

    etree, root, _ = _build_xml(tree)
    expression = _rewrite_class_shorthand(expression, tree)
    try:
        result = etree.XPath(expression)(root)
    except (etree.XPathError, etree.XMLSyntaxError, TypeError, ValueError) as error:
        raise XPathError("invalid XPath expression %r: %s" % (expression, error)) from error

    if not isinstance(result, list):
        raise XPathError("XPath expression must return a node-set, got %s" % type(result).__name__)

    by_id = {element.id: element for element in tree}
    matched_ids = []
    for node in result:
        if not isinstance(node, etree._Element):
            raise XPathError("XPath expression returned a non-element node")
        element_id = node.get("data-uiautomator3-id")
        if element_id is not None and element_id in by_id and element_id not in matched_ids:
            matched_ids.append(element_id)

    order = {element.id: index for index, element in enumerate(tree)}
    matched_ids.sort(key=order.__getitem__)
    return [by_id[element_id] for element_id in matched_ids]


class XPathLocator:
    """A lazily evaluated XPath expression bound to a device."""

    def __init__(self, device, expression: str) -> None:
        if not isinstance(expression, str) or not expression.strip():
            raise XPathError("XPath expression must be a non-empty string")
        self._device = device
        self.expression = expression

    def __repr__(self) -> str:
        return "XPathLocator(%r)" % self.expression

    def _current_tree(self):
        return self._device.inspect()

    def all(self) -> List[UIElement]:
        return find_all_xpath(self._current_tree(), self.expression)

    def first(self) -> Optional[UIElement]:
        matches = self.all()
        return matches[0] if matches else None

    @property
    def exists(self) -> bool:
        return self.first() is not None

    def count(self) -> int:
        return len(self.all())

    def _resolve_single(self) -> UIElement:
        from uiautomator3.exceptions import ElementAmbiguousError, ElementNotFoundError

        matches = self.all()
        if not matches:
            raise ElementNotFoundError("no element matched XPath %r" % self.expression)
        if len(matches) > 1:
            raise ElementAmbiguousError(
                "%d elements matched XPath %r; use .all() or add a more specific predicate"
                % (len(matches), self.expression)
            )
        return matches[0]

    def _click_target(self, element: UIElement, tree: "ElementTree") -> UIElement:
        if element.clickable:
            return element
        current = tree.parent_of(element)
        while current is not None:
            if current.clickable:
                return current
            current = tree.parent_of(current)
        return element

    def _record(self, action: str, element: UIElement, target: UIElement, **extra) -> None:
        recording = getattr(self._device, "_recording", None)
        if recording is None:
            return
        recording.log(
            action,
            coordinates={"x": target.center.x, "y": target.center.y},
            element=element,
            locator="XPath(%r)" % self.expression,
            screen=self._device._current_screen_label(),
            **extra,
        )

    def click(self) -> None:
        tree = self._current_tree()
        element = self._resolve_single()
        target = self._click_target(element, tree)
        self._device.gesture.tap(target.center.x, target.center.y)
        self._device.invalidate_cache()
        self._record("click", element, target)

    def long_click(self, duration: float = 1.0) -> None:
        tree = self._current_tree()
        element = self._resolve_single()
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

    def inspect(self) -> UIElement:
        return self._resolve_single()

    def assert_exists(self) -> "XPathLocator":
        if not self.exists:
            from uiautomator3.exceptions import ElementNotFoundError

            raise ElementNotFoundError("expected XPath to match: %r" % self.expression)
        return self

    def assert_visible(self) -> "XPathLocator":
        element = self._resolve_single()
        if not element.visible:
            from uiautomator3.exceptions import ElementNotFoundError

            raise ElementNotFoundError("expected XPath match to be visible: %r" % self.expression)
        return self

    def assert_enabled(self) -> "XPathLocator":
        element = self._resolve_single()
        if not element.enabled:
            from uiautomator3.exceptions import ElementNotFoundError

            raise ElementNotFoundError("expected XPath match to be enabled: %r" % self.expression)
        return self

    def assert_text(self, expected: str) -> "XPathLocator":
        element = self._resolve_single()
        if element.text != expected:
            from uiautomator3.exceptions import ElementNotFoundError

            raise ElementNotFoundError("expected text %r, got %r" % (expected, element.text))
        return self