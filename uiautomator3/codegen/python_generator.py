"""Generate plain Python uiautomator3 automation code from a RecordingSession.

Per project spec section 19:
    import uiautomator3 as u3
    d = u3.connect()
    d(text="Login").click()
    d(resource_id="com.example:id/email").set_text("test@example.com")
    ...

Prefers the recorded selector (d(**criteria).action()) when available -
this is what makes the generated code resilient to screen coordinates
changing between runs; falls back to raw coordinates/keys only for
actions that have no associated element (plain swipes, key presses).
"""
from typing import List, Optional

from uiautomator3.recording.action import RecordedAction
from uiautomator3.recording.session import RecordingSession


def _format_kwargs(criteria: dict) -> str:
    parts = []
    for key, value in criteria.items():
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{key}="{escaped}"')
        else:
            parts.append(f"{key}={value!r}")
    return ", ".join(parts)


def _locator_expr(entry: RecordedAction, receiver: str) -> str:
    return f"{receiver}({_format_kwargs(entry.selector_criteria)})"


def _line_for_action(entry: RecordedAction, receiver: str = "d") -> str:
    has_locator = bool(entry.selector_criteria)

    if entry.action == "click":
        if has_locator:
            return f"{_locator_expr(entry, receiver)}.click()"
        x, y = entry.coordinates["x"], entry.coordinates["y"]
        return f"{receiver}.click({x}, {y})"

    if entry.action == "long_click":
        duration = entry.extra.get("duration", 1.0)
        if has_locator:
            return f"{_locator_expr(entry, receiver)}.long_click(duration={duration})"
        x, y = entry.coordinates["x"], entry.coordinates["y"]
        return f"{receiver}.long_click({x}, {y}, duration={duration})"

    if entry.action == "swipe":
        c = entry.coordinates
        return f"{receiver}.swipe({c['from_x']}, {c['from_y']}, {c['to_x']}, {c['to_y']})"

    if entry.action == "drag":
        c = entry.coordinates
        return f"{receiver}.drag({c['from_x']}, {c['from_y']}, {c['to_x']}, {c['to_y']})"

    if entry.action == "press":
        key = entry.extra.get("key")
        return f"{receiver}.press({key!r})"

    if entry.action == "send_keys":
        text = entry.extra.get("text", "")
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'{receiver}.send_keys("{escaped}")'

    if entry.action == "app_launch":
        package = entry.extra.get("package")
        activity = entry.extra.get("activity")
        if activity:
            return f"{receiver}.launch_app({package!r}, {activity!r})"
        return f"{receiver}.launch_app({package!r})"

    if entry.action == "app_stop":
        package = entry.extra.get("package")
        return f"{receiver}.stop_app({package!r})"

    return f"# unrecognized action: {entry.action}"


def generate_python(session: RecordingSession, connect_serial: Optional[str] = None) -> str:
    """Return a standalone Python script reproducing `session`'s actions."""
    lines: List[str] = ["import uiautomator3 as u3", ""]
    if connect_serial:
        lines.append(f"d = u3.connect({connect_serial!r})")
    else:
        lines.append("d = u3.connect()")
    lines.append("")

    for entry in session.actions:
        comment = f"# {entry.screen}" if entry.screen else None
        if comment:
            lines.append(comment)
        lines.append(_line_for_action(entry))

    return "\n".join(lines) + "\n"
