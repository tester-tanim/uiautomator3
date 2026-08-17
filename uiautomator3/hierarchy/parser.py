"""Hierarchy XML parsing and normalization into ElementTree.

Uses the standard library's xml.etree.ElementTree - not lxml - since Phase
3 needs attribute-based tree walking only, not XPath (XPath support is a
later phase and can add lxml as an optional extra then, keeping the core
dependency-light per docs/UIAUTOMATOR3_ARCHITECTURE.md principle "core
stays light").

This is the single normalization point all locator strategies build on,
directly addressing the structural split identified in
docs/UIAUTOMATOR2_ANALYSIS.md section 6 (selector RPC objects vs. parsed
XML being two incompatible representations in uiautomator2).
"""
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple

from uiautomator3.elements.roles import classify
from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.exceptions import UIAutomator3Error
from uiautomator3.logging_config import get_logger

logger = get_logger("hierarchy.parser")


class HierarchyParseError(UIAutomator3Error):
    """Raised when hierarchy XML cannot be parsed."""


def _parse_bounds(bounds_str: str) -> Bounds:
    # Format: "[left,top][right,bottom]"
    try:
        parts = bounds_str.replace("][", ",").strip("[]").split(",")
        left, top, right, bottom = (int(p) for p in parts)
        return Bounds(left=left, top=top, right=right, bottom=bottom)
    except (ValueError, AttributeError) as e:
        raise HierarchyParseError(f"invalid bounds attribute: {bounds_str!r}: {e}") from e


def _bool_attr(node: ET.Element, name: str) -> bool:
    return node.attrib.get(name, "false") == "true"


def _text_attr(node: ET.Element, name: str) -> Optional[str]:
    value = node.attrib.get(name, "")
    return value if value else None


def _parse_rotation(root: ET.Element) -> int:
    try:
        return int(root.attrib.get("rotation", "0"))
    except ValueError:
        return 0


def parse_hierarchy(xml_data: str) -> ElementTree:
    """Parse `uiautomator dump` XML into a normalized ElementTree."""
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise HierarchyParseError(f"failed to parse hierarchy XML: {e}") from e

    rotation = _parse_rotation(root)
    elements: List[UIElement] = []

    def walk(node: ET.Element, parent_id: Optional[str], depth: int) -> List[str]:
        child_ids: List[str] = []
        for i, child in enumerate(node):
            if child.tag != "node":
                continue
            element_id = f"e{len(elements)}"
            bounds = _parse_bounds(child.attrib.get("bounds", "[0,0][0,0]"))

            element = UIElement(
                id=element_id,
                text=_text_attr(child, "text"),
                content_description=_text_attr(child, "content-desc"),
                resource_id=_text_attr(child, "resource-id"),
                class_name=_text_attr(child, "class"),
                package_name=_text_attr(child, "package"),
                bounds=bounds,
                clickable=_bool_attr(child, "clickable"),
                enabled=_bool_attr(child, "enabled"),
                visible=bounds.area > 0,
                focused=_bool_attr(child, "focused"),
                selected=_bool_attr(child, "selected"),
                checked=_bool_attr(child, "checked"),
                scrollable=_bool_attr(child, "scrollable"),
                long_clickable=_bool_attr(child, "long-clickable"),
                checkable=_bool_attr(child, "checkable"),
                password=_bool_attr(child, "password"),
                parent_id=parent_id,
                depth=depth,
                index=i,
            )
            element.role = classify(element)
            elements.append(element)
            child_ids.append(element_id)
            element.children = walk(child, element_id, depth + 1)
        return child_ids

    walk(root, None, 0)
    return ElementTree(elements, rotation=rotation)
