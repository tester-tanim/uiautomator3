"""AIController: d.ai.inspect()/find()/click()/type(), per project spec section 39.

    d.ai.inspect()
    d.ai.find("Login button")
    d.ai.click("Login button")
    d.ai.type("Email input", "test@example.com")

Everything here is a thin wrapper over Device/Locator/matcher - no
parallel automation logic, matching docs/UIAUTOMATOR3_ARCHITECTURE.md
section 12's "no parallel logic to maintain" principle (also true of the
MCP layer built on top of this in the same phase).
"""
from typing import TYPE_CHECKING, Any, Dict

from uiautomator3.ai.matcher import find_all_matches, find_best_match
from uiautomator3.ai.schema import ScreenDescription, describe_element
from uiautomator3.exceptions import ElementNotFoundError

if TYPE_CHECKING:
    from uiautomator3.device.device import Device


class AIController:
    def __init__(self, device: "Device") -> None:
        self._device = device

    def inspect(self) -> Dict[str, Any]:
        """Structured screen description - role/label/locator/confidence per element,
        never a raw screenshot alone (project spec section 63)."""
        tree = self._device.inspect()
        try:
            current = self._device.app.current()
            screen = f"{current.package}/{current.activity}" if current.activity else current.package
        except Exception:
            screen = "unknown"

        # Only elements an AI agent could actually name/reason about: those
        # with a label (text or content-description). Unlabeled elements -
        # even clickable ones - contribute nothing an agent can refer to by
        # description, and otherwise dominate a raw hierarchy as pure noise
        # (project spec section 63: dense structured data, not everything
        # clickable). get_ui_tree() remains available for the full,
        # unfiltered hierarchy when that's genuinely needed.
        elements = [describe_element(e, tree) for e in tree if e.text or e.content_description]
        return ScreenDescription(screen=screen, elements=elements).as_dict()

    def find(self, description: str) -> Dict[str, Any]:
        """Return {"element": "...", "matches": [{"id":..., "confidence":...}, ...]}."""
        tree = self._device.inspect()
        matches = find_all_matches(tree, description)
        return {
            "element": description,
            "matches": [
                {
                    "id": element.id,
                    "confidence": round(confidence, 4),
                    **describe_element(element, tree).as_dict(),
                }
                for element, confidence in matches
            ],
        }

    def _resolve(self, description: str):
        tree = self._device.inspect()
        result = find_best_match(tree, description)
        if result is None:
            raise ElementNotFoundError(f"no element matched description: {description!r}")
        return result

    def click(self, description: str) -> Dict[str, Any]:
        element, confidence = self._resolve(description)
        self._device.click(element.center.x, element.center.y)
        return {"clicked": description, "confidence": round(confidence, 4)}

    def type(self, description: str, text: str) -> Dict[str, Any]:
        element, confidence = self._resolve(description)
        self._device.click(element.center.x, element.center.y)
        self._device.send_keys(text)
        return {"typed_into": description, "text": text, "confidence": round(confidence, 4)}
