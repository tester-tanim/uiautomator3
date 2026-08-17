"""Generate a pytest test module from a RecordingSession (project spec section 19)."""

from uiautomator3.codegen.python_generator import _line_for_action
from uiautomator3.recording.session import RecordingSession


def generate_pytest(session: RecordingSession, test_name: str = "test_recorded_flow") -> str:
    lines = [
        "import pytest",
        "",
        "import uiautomator3 as u3",
        "",
        "",
        "@pytest.fixture",
        "def d():",
        "    return u3.connect()",
        "",
        "",
        f"def {test_name}(d):",
    ]

    if not session.actions:
        lines.append("    pass")
        return "\n".join(lines) + "\n"

    for entry in session.actions:
        if entry.screen:
            lines.append(f"    # {entry.screen}")
        lines.append(f"    {_line_for_action(entry)}")

    return "\n".join(lines) + "\n"
