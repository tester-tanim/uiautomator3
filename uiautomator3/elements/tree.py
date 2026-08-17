"""ElementTree - an indexed collection of UIElement.

Built once per hierarchy snapshot; all relationship/spatial queries operate
against these indices rather than re-walking or re-dumping the hierarchy,
addressing the O(n) linear-scan approach uiautomator2 uses for its only
relationship feature (see docs/UIAUTOMATOR2_ANALYSIS.md section 4,
`.right()/.left()/.up()/.down()`).
"""

from collections import defaultdict
from typing import Dict, List, Optional

from uiautomator3.elements.uielement import UIElement


class ElementTree:
    """Indexed view over a list of UIElement produced from one hierarchy dump."""

    def __init__(self, elements: List[UIElement], rotation: int = 0) -> None:
        self.elements: List[UIElement] = elements
        self.rotation: int = rotation

        self.by_id: Dict[str, UIElement] = {e.id: e for e in elements}

        self.by_resource_id: Dict[str, List[UIElement]] = defaultdict(list)
        for e in elements:
            if e.resource_id:
                self.by_resource_id[e.resource_id].append(e)

        self.by_text: Dict[str, List[UIElement]] = defaultdict(list)
        for e in elements:
            if e.text:
                self.by_text[e.text].append(e)

        self.by_class_name: Dict[str, List[UIElement]] = defaultdict(list)
        for e in elements:
            if e.class_name:
                self.by_class_name[e.class_name].append(e)

    def __len__(self) -> int:
        return len(self.elements)

    def __iter__(self):
        return iter(self.elements)

    def get(self, element_id: str) -> Optional[UIElement]:
        return self.by_id.get(element_id)

    def parent_of(self, element: UIElement) -> Optional[UIElement]:
        if element.parent_id is None:
            return None
        return self.by_id.get(element.parent_id)

    def children_of(self, element: UIElement) -> List[UIElement]:
        return [self.by_id[cid] for cid in element.children if cid in self.by_id]

    def ancestors_of(self, element: UIElement) -> List[UIElement]:
        result = []
        current = self.parent_of(element)
        while current is not None:
            result.append(current)
            current = self.parent_of(current)
        return result

    def descendants_of(self, element: UIElement) -> List[UIElement]:
        result = []
        stack = list(self.children_of(element))
        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(self.children_of(node))
        return result

    def siblings_of(self, element: UIElement, include_self: bool = False) -> List[UIElement]:
        parent = self.parent_of(element)
        if parent is None:
            siblings = [e for e in self.elements if e.parent_id is None]
        else:
            siblings = self.children_of(parent)
        if include_self:
            return siblings
        return [e for e in siblings if e.id != element.id]

    def preceding_siblings_of(self, element: UIElement) -> List[UIElement]:
        siblings = self.siblings_of(element, include_self=True)
        idx = next((i for i, e in enumerate(siblings) if e.id == element.id), None)
        return siblings[:idx] if idx is not None else []

    def following_siblings_of(self, element: UIElement) -> List[UIElement]:
        siblings = self.siblings_of(element, include_self=True)
        idx = next((i for i, e in enumerate(siblings) if e.id == element.id), None)
        return siblings[idx + 1 :] if idx is not None else []
