"""Generate Robot Framework style pseudo-output from a RecordingSession
(project spec section 19: "Robot Framework style output").

This targets a custom `UIAutomator3` Robot library surface
(`Click`/`Long Click`/`Swipe`/`Press Key`/`Send Keys`/`Launch App`), not
an actual existing Robot Framework keyword library - the project does not
ship one. The output documents intent in Robot's tabular syntax; wiring a
real Robot Framework library is future work if that integration is
prioritized.
"""
from uiautomator3.recording.action import RecordedAction
from uiautomator3.recording.session import RecordingSession


def _robot_locator_arg(entry: RecordedAction) -> str:
    parts = "    ".join(f"{k}={v}" for k, v in (entry.selector_criteria or {}).items())
    return parts


def _robot_line(entry: RecordedAction) -> str:
    if entry.action == "click":
        if entry.selector_criteria:
            return f"    Click    {_robot_locator_arg(entry)}"
        c = entry.coordinates
        return f"    Click Coordinates    {c['x']}    {c['y']}"

    if entry.action == "long_click":
        if entry.selector_criteria:
            return f"    Long Click    {_robot_locator_arg(entry)}"
        c = entry.coordinates
        return f"    Long Click Coordinates    {c['x']}    {c['y']}"

    if entry.action == "swipe":
        c = entry.coordinates
        return f"    Swipe    {c['from_x']}    {c['from_y']}    {c['to_x']}    {c['to_y']}"

    if entry.action == "drag":
        c = entry.coordinates
        return f"    Drag    {c['from_x']}    {c['from_y']}    {c['to_x']}    {c['to_y']}"

    if entry.action == "press":
        return f"    Press Key    {entry.extra.get('key')}"

    if entry.action == "send_keys":
        return f"    Send Keys    {entry.extra.get('text', '')}"

    if entry.action == "app_launch":
        return f"    Launch App    {entry.extra.get('package')}"

    if entry.action == "app_stop":
        return f"    Stop App    {entry.extra.get('package')}"

    return f"    # unrecognized action: {entry.action}"


def generate_robot(session: RecordingSession, test_name: str = "Recorded Flow") -> str:
    lines = [
        "*** Settings ***",
        "Library    UIAutomator3",
        "",
        "*** Test Cases ***",
        test_name,
    ]
    if not session.actions:
        lines.append("    No Operation")
        return "\n".join(lines) + "\n"

    for entry in session.actions:
        lines.append(_robot_line(entry))

    return "\n".join(lines) + "\n"
