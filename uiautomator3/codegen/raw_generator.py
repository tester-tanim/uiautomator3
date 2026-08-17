"""Generate a raw, line-oriented action script from a RecordingSession
(project spec section 19: "raw action scripts").

One action per line: `ACTION arg1=value1 arg2=value2 ...` - a minimal,
tool-agnostic format simpler than JSON/YAML for quick diffing or piping
into another script, distinct from the structured (JSON/YAML) exports.
"""
from uiautomator3.recording.action import RecordedAction
from uiautomator3.recording.session import RecordingSession


def _raw_line(entry: RecordedAction) -> str:
    parts = [entry.action.upper()]

    if entry.selector_criteria:
        for key, value in entry.selector_criteria.items():
            parts.append(f"{key}={value}")
    elif entry.coordinates:
        for key, value in entry.coordinates.items():
            parts.append(f"{key}={value}")

    for key, value in entry.extra.items():
        parts.append(f"{key}={value}")

    return " ".join(parts)


def generate_raw(session: RecordingSession) -> str:
    return "\n".join(_raw_line(entry) for entry in session.actions) + ("\n" if session.actions else "")
