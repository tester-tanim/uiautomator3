"""JSON/YAML export of a RecordingSession (project spec section 19).

YAML is emitted with a minimal hand-rolled writer, not PyYAML - the action
list is already a shallow, uniform structure (list of flat dicts), so a
full YAML library is unnecessary weight for the core codegen path. If a
recording ever needs a real YAML *parser* (round-tripping), that's a
reason to add PyYAML as an optional extra then, not now.
"""
import json
from typing import Any, Dict, List

from uiautomator3.recording.session import RecordingSession


def generate_json(session: RecordingSession, indent: int = 2) -> str:
    return json.dumps(session.as_list(), indent=indent)


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    needs_quotes = text == "" or any(c in text for c in ":#{}[]&*!|>'\"%@`") or text.strip() != text
    if needs_quotes:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def _yaml_lines(value: Any, indent: int) -> List[str]:
    pad = "  " * indent
    lines: List[str] = []

    if isinstance(value, dict):
        if not value:
            lines.append(f"{pad}{{}}" if indent == 0 else "{}")
            return lines
        for key, val in value.items():
            if isinstance(val, dict):
                if val:
                    lines.append(f"{pad}{key}:")
                    lines.extend(_yaml_lines(val, indent + 1))
                else:
                    lines.append(f"{pad}{key}: {{}}")
            elif isinstance(val, list):
                if val:
                    lines.append(f"{pad}{key}:")
                    lines.extend(_yaml_lines(val, indent + 1))
                else:
                    lines.append(f"{pad}{key}: []")
            else:
                lines.append(f"{pad}{key}: {_yaml_scalar(val)}")
    elif isinstance(value, list):
        if not value:
            lines.append(f"{pad}[]")
            return lines
        for item in value:
            if isinstance(item, dict):
                sub_lines = _yaml_lines(item, indent + 1)
                if sub_lines:
                    first = sub_lines[0].lstrip()
                    lines.append(f"{pad}- {first}")
                    lines.extend(sub_lines[1:])
                else:
                    lines.append(f"{pad}- {{}}")
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
    return lines


def generate_yaml(session: RecordingSession) -> str:
    data: Dict[str, Any] = {"actions": session.as_list()}
    lines = _yaml_lines(data, 0)
    return "\n".join(lines) + "\n"
