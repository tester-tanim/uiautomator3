"""LocatorCandidate: one generated locator plus its computed scores."""

from dataclasses import dataclass


@dataclass
class LocatorCandidate:
    strategy: str
    locator: str
    python_code: str
    uniqueness: float
    stability: float
    specificity: float
    score: float
    recommendation: str = "alternative"  # "best" | "alternative"

    def as_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "locator": self.locator,
            "python_code": self.python_code,
            "uniqueness": round(self.uniqueness, 4),
            "stability": round(self.stability, 4),
            "specificity": round(self.specificity, 4),
            "score": round(self.score, 4),
            "recommendation": self.recommendation,
        }
