"""Stability heuristics for locator scoring.

Deterministic, rule-based (not ML) per docs/UIAUTOMATOR3_ARCHITECTURE.md
section 5: stability = f(depends_on_index, depends_on_dynamic_attrs,
resource_id_naming_pattern).
"""
import re

# Text/resource-id values that look auto-generated / dynamic: long hex/digit
# runs, UUID-like strings, or trailing numeric-only suffixes. These are
# less stable across app builds and sessions than human-authored names.
_DYNAMIC_VALUE_PATTERN = re.compile(
    r"""
    ^[0-9a-fA-F]{8,}$                       # long hex/id-like string
    | ^[0-9]+$                              # pure numeric
    | [0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}  # UUID
    | _[0-9]{3,}$                           # trailing numeric suffix like foo_12345
    """,
    re.VERBOSE,
)


def is_dynamic_value(value: str) -> bool:
    """Heuristically detect an auto-generated / session-specific value."""
    return bool(_DYNAMIC_VALUE_PATTERN.search(value))


def resource_id_stability(resource_id: str) -> float:
    """Score a resource-id's naming pattern: 1.0 stable, lower if dynamic-looking."""
    local_name = resource_id.split("/")[-1] if "/" in resource_id else resource_id
    if is_dynamic_value(local_name):
        return 0.4
    return 1.0


def text_stability(text: str) -> float:
    """Score text content stability: locale-independent numbers/timestamps score lower."""
    if is_dynamic_value(text):
        return 0.3
    if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", text):  # clock/timer-looking text
        return 0.2
    return 1.0


def index_dependency_penalty(uses_index: bool) -> float:
    """Multiplier applied when a locator depends on sibling position (index)."""
    return 0.7 if uses_index else 1.0


def hierarchy_depth_penalty(depth: int, max_reasonable_depth: int = 12) -> float:
    """Deeper XPath-style locators are more brittle to layout changes."""
    if depth <= 0:
        return 1.0
    return max(0.3, 1.0 - (depth / max_reasonable_depth) * 0.5)
