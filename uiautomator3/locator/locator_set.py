"""LocatorSet: the result of generating and ranking candidates for one element."""

from dataclasses import dataclass
from typing import List, Optional

from uiautomator3.locator.candidate import LocatorCandidate


@dataclass
class LocatorSet:
    element_id: str
    candidates: List[LocatorCandidate]

    @property
    def best(self) -> Optional[LocatorCandidate]:
        return self.candidates[0] if self.candidates else None

    @property
    def alternatives(self) -> List[LocatorCandidate]:
        return self.candidates[1:]

    def as_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "best": self.best.as_dict() if self.best else None,
            "alternatives": [c.as_dict() for c in self.alternatives],
        }
