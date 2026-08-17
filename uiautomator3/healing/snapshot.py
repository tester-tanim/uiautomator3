"""ElementSnapshot: the remembered identity of a successfully-resolved element.

Captured the first time a Locator resolves (see selectors/locator_object.py
`_maybe_snapshot`), so a later failure has something concrete to search
for. This is deliberately a plain attribute snapshot, not a persisted
database - see docs/UIAUTOMATOR3_ARCHITECTURE.md section 7 and the
project's own note that healing must not change behavior unless
explicitly enabled.
"""
from dataclasses import dataclass
from typing import Optional

from uiautomator3.elements.uielement import UIElement


@dataclass(frozen=True)
class ElementSnapshot:
    text: Optional[str]
    content_description: Optional[str]
    resource_id: Optional[str]
    class_name: Optional[str]
    role: Optional[str]

    @classmethod
    def from_element(cls, element: UIElement) -> "ElementSnapshot":
        return cls(
            text=element.text,
            content_description=element.content_description,
            resource_id=element.resource_id,
            class_name=element.class_name,
            role=element.role,
        )
