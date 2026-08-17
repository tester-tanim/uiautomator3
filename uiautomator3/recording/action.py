"""RecordedAction: one captured interaction.

Shape matches project spec section 18:
    {
      "action": "click",
      "timestamp": "...",
      "element": "...",
      "locator": "...",
      "coordinates": {},
      "screen": "...",
      "confidence": 0.98
    }
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RecordedAction:
    action: str
    timestamp: float
    coordinates: Optional[Dict[str, int]] = None
    locator: Optional[str] = None
    selector_criteria: Optional[Dict[str, Any]] = None
    element_text: Optional[str] = None
    element_resource_id: Optional[str] = None
    element_class_name: Optional[str] = None
    screen: Optional[str] = None
    confidence: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        data = {
            "action": self.action,
            "timestamp": self.timestamp,
            "coordinates": self.coordinates,
            "locator": self.locator,
            "selector_criteria": self.selector_criteria,
            "element": {
                "text": self.element_text,
                "resource_id": self.element_resource_id,
                "class_name": self.element_class_name,
            }
            if (self.element_text or self.element_resource_id or self.element_class_name)
            else None,
            "screen": self.screen,
            "confidence": self.confidence,
        }
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordedAction":
        known_keys = {"action", "timestamp", "coordinates", "locator", "selector_criteria", "element", "screen", "confidence"}
        element = data.get("element") or {}
        return cls(
            action=data["action"],
            timestamp=data.get("timestamp", 0.0),
            coordinates=data.get("coordinates"),
            locator=data.get("locator"),
            selector_criteria=data.get("selector_criteria"),
            element_text=element.get("text"),
            element_resource_id=element.get("resource_id"),
            element_class_name=element.get("class_name"),
            screen=data.get("screen"),
            confidence=data.get("confidence"),
            extra={k: v for k, v in data.items() if k not in known_keys},
        )
