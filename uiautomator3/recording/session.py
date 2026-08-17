"""RecordingSession: accumulates RecordedAction entries during d.start_recording()."""

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from uiautomator3.recording.action import RecordedAction

if TYPE_CHECKING:
    from uiautomator3.elements.uielement import UIElement


class RecordingSession:
    """Holds recorded actions for one recording session on a Device.

    Attached to Device via start_recording()/stop_recording() rather than
    wrapping Device's public methods - gesture/selector code checks
    `self._device._recording` and calls `.log(...)` as a side effect, so
    d.click(...) behaves identically whether or not a session is active
    (see project spec section 18, and the "session-based" design decision
    for this phase).
    """

    def __init__(self) -> None:
        self.actions: List[RecordedAction] = []

    def log(
        self,
        action: str,
        coordinates: Optional[Dict[str, int]] = None,
        element: Optional["UIElement"] = None,
        locator: Optional[str] = None,
        selector_criteria: Optional[Dict[str, Any]] = None,
        screen: Optional[str] = None,
        confidence: Optional[float] = None,
        **extra: Any,
    ) -> RecordedAction:
        entry = RecordedAction(
            action=action,
            timestamp=time.time(),
            coordinates=coordinates,
            locator=locator,
            selector_criteria=selector_criteria,
            element_text=element.text if element else None,
            element_resource_id=element.resource_id if element else None,
            element_class_name=element.class_name if element else None,
            screen=screen,
            confidence=confidence,
            extra=extra,
        )
        self.actions.append(entry)
        return entry

    def clear(self) -> None:
        self.actions.clear()

    def as_list(self) -> List[Dict[str, Any]]:
        return [a.as_dict() for a in self.actions]

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "RecordingSession":
        """Reconstruct a session from `as_list()`-shaped data (e.g. a JSON export)."""
        session = cls()
        session.actions = [RecordedAction.from_dict(item) for item in data]
        return session
