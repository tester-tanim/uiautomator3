"""Generate a Python Page Object Model from a RecordingSession (project spec section 19).

Groups consecutive actions by their `screen` label into one class per
distinct screen, with one method per action. This is a straightforward,
literal grouping (not scene-detection/clustering) - good enough for a
recorded linear flow; smarter state-based grouping is a later phase (see
project spec section 17, State-Based UI Model).
"""
import re
from typing import Dict, List, Optional, Tuple

from uiautomator3.codegen.python_generator import _line_for_action
from uiautomator3.recording.action import RecordedAction
from uiautomator3.recording.session import RecordingSession


def _class_name_for_screen(screen: str) -> str:
    # `screen` is "package/activity" (e.g. "com.example/.LoginActivity") or
    # just "package" when no activity was resolved. Prefer the activity's
    # short name since it identifies the actual screen; fall back to the
    # package's last segment otherwise.
    if "/" in screen:
        package, activity = screen.split("/", 1)
        short = activity.rsplit(".", 1)[-1] or package.rsplit(".", 1)[-1]
    else:
        short = screen.rsplit(".", 1)[-1]
    words = re.split(r"[^A-Za-z0-9]+", short)
    # Capitalize only the first letter of each word, preserving any
    # existing internal capitalization (e.g. "LoginActivity" stays as-is
    # rather than becoming "Loginactivity").
    name = "".join(w[:1].upper() + w[1:] for w in words if w)
    return f"{name or 'Unknown'}Page"


def _method_name_for_action(index: int, entry: RecordedAction) -> str:
    if entry.element_text:
        slug = re.sub(r"[^a-z0-9]+", "_", entry.element_text.lower()).strip("_")
        if slug:
            return f"{entry.action}_{slug}"
    return f"{entry.action}_{index}"


def _group_by_screen(actions: List[RecordedAction]) -> List[Tuple[Optional[str], List[RecordedAction]]]:
    groups: List[Tuple[Optional[str], List[RecordedAction]]] = []
    current_screen: Optional[str] = None
    current_actions: List[RecordedAction] = []
    for entry in actions:
        screen = entry.screen or "unknown"
        if screen != current_screen:
            if current_actions:
                groups.append((current_screen, current_actions))
            current_screen = screen
            current_actions = []
        current_actions.append(entry)
    if current_actions:
        groups.append((current_screen, current_actions))
    return groups


def generate_pom(session: RecordingSession) -> str:
    """Return a Python module defining one Page Object class per screen."""
    lines = ["import uiautomator3 as u3"]

    groups = _group_by_screen(session.actions)
    if not groups:
        return "\n".join(lines) + "\n"

    seen_class_names: Dict[str, int] = {}

    for screen, actions in groups:
        base_name = _class_name_for_screen(screen)
        count = seen_class_names.get(base_name, 0)
        seen_class_names[base_name] = count + 1
        class_name = base_name if count == 0 else f"{base_name}{count + 1}"

        lines.append("")
        lines.append("")
        lines.append(f"class {class_name}:")
        lines.append(f'    """Page object for {screen}."""')
        lines.append("")
        lines.append("    def __init__(self, d: u3.Device):")
        lines.append("        self.d = d")

        for index, entry in enumerate(actions):
            method_name = _method_name_for_action(index, entry)
            lines.append("")
            lines.append(f"    def {method_name}(self):")
            lines.append(f"        {_line_for_action(entry, receiver='self.d')}")

    return "\n".join(lines) + "\n"
