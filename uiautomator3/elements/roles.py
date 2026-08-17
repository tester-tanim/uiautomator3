"""Semantic role classification.

Deterministic, rule-based (not a classifier) per
docs/UIAUTOMATOR3_ARCHITECTURE.md section 8 - fast enough to run on every
normalization pass, and does not depend exclusively on class name (also
consults clickable/checkable/scrollable state).
"""
from uiautomator3.elements.uielement import UIElement

_CLASS_SUFFIX_ROLES = {
    "Button": "button",
    "ImageButton": "button",
    "EditText": "input",
    "AutoCompleteTextView": "input",
    "TextView": "text",
    "CheckBox": "checkbox",
    "RadioButton": "radio",
    "Switch": "switch",
    "ToggleButton": "switch",
    "ImageView": "image",
    "ListView": "list",
    "RecyclerView": "list",
    "GridView": "list",
    "Spinner": "dropdown",
    "SeekBar": "slider",
    "ProgressBar": "progress",
    "TabWidget": "tab",
    "Tab": "tab",
    "Dialog": "dialog",
    "PopupWindow": "menu",
    "ScrollView": "container",
    "LinearLayout": "container",
    "FrameLayout": "container",
    "RelativeLayout": "container",
    "ViewGroup": "container",
}


def classify(element: UIElement) -> str:
    """Return a semantic role string for `element`."""
    class_name = element.class_name or ""
    simple_name = class_name.rsplit(".", 1)[-1]

    for suffix, role in _CLASS_SUFFIX_ROLES.items():
        if simple_name.endswith(suffix):
            # state-based refinement: a clickable/checkable "TextView"-derived
            # widget is more usefully treated as a button, not plain text.
            if role == "text" and element.clickable:
                return "button"
            return role

    if element.checkable and element.checked is not None:
        return "checkbox"
    if element.scrollable:
        return "list"
    if element.clickable:
        return "button"
    if element.text:
        return "text"
    return "container"
