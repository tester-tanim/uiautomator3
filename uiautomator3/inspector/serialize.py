"""JSON serialization for UIElement/ElementTree.

The web inspector and any Python caller (`d.inspect()`) must see
structurally identical data - this module is the single place that turns
the typed dataclasses into JSON-safe dicts, so the FastAPI layer in
server.py never reimplements element shaping. See
docs/UIAUTOMATOR3_ARCHITECTURE.md section 11.
"""
from typing import Any, Dict, List

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import UIElement


def element_to_dict(element: UIElement) -> Dict[str, Any]:
    return {
        "id": element.id,
        "text": element.text,
        "content_description": element.content_description,
        "resource_id": element.resource_id,
        "class_name": element.class_name,
        "package_name": element.package_name,
        "bounds": {
            "left": element.bounds.left,
            "top": element.bounds.top,
            "right": element.bounds.right,
            "bottom": element.bounds.bottom,
        },
        "center": {"x": element.center.x, "y": element.center.y},
        "clickable": element.clickable,
        "enabled": element.enabled,
        "visible": element.visible,
        "focused": element.focused,
        "selected": element.selected,
        "checked": element.checked,
        "scrollable": element.scrollable,
        "long_clickable": element.long_clickable,
        "checkable": element.checkable,
        "password": element.password,
        "parent_id": element.parent_id,
        "children": list(element.children),
        "depth": element.depth,
        "index": element.index,
        "role": element.role,
        "ocr_text": element.ocr_text,
        "visual_confidence": element.visual_confidence,
        "source": sorted(element.source),
    }


def tree_to_dict(tree: ElementTree) -> Dict[str, Any]:
    return {
        "rotation": tree.rotation,
        "count": len(tree),
        "elements": [element_to_dict(e) for e in tree],
    }
