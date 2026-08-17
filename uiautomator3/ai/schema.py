"""Structured element representation for AI consumption.

Per project spec section 63 ("Important Rule for AI"): AI agents must
never be handed raw screenshots alone. Every element is described with
role/label/locator/confidence so an agent can reason about *what* is on
screen and *how* to act on it without vision-model inference.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from uiautomator3.elements.uielement import UIElement
from uiautomator3.locator.generator import generate_candidates, rank_candidates


@dataclass
class AIElement:
    role: Optional[str]
    label: Optional[str]
    locator: str
    locator_python: str
    confidence: float
    bounds: Dict[str, int]
    clickable: bool
    enabled: bool

    def as_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "label": self.label,
            "locator": self.locator,
            "locator_python": self.locator_python,
            "confidence": round(self.confidence, 4),
            "bounds": self.bounds,
            "clickable": self.clickable,
            "enabled": self.enabled,
        }


def _label_for(element: UIElement) -> Optional[str]:
    return element.text or element.content_description or None


def describe_element(element: UIElement, tree) -> AIElement:
    """Build the AI-facing structured description of one element."""
    candidates = rank_candidates(generate_candidates(element, tree))
    best = candidates[0] if candidates else None

    return AIElement(
        role=element.role,
        label=_label_for(element),
        locator=best.locator if best else "",
        locator_python=best.python_code if best else "",
        confidence=best.score if best else 0.0,
        bounds={
            "left": element.bounds.left,
            "top": element.bounds.top,
            "right": element.bounds.right,
            "bottom": element.bounds.bottom,
        },
        clickable=element.clickable,
        enabled=element.enabled,
    )


@dataclass
class ScreenDescription:
    screen: str
    elements: List[AIElement]

    def as_dict(self) -> Dict[str, Any]:
        return {"screen": self.screen, "elements": [e.as_dict() for e in self.elements]}
