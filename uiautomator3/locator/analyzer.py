"""Locator stability analysis.

`analyze_locator()` reuses the same scoring path as candidate generation
(docs/UIAUTOMATOR3_ARCHITECTURE.md section 5) against a caller-supplied
Selector, rather than a generated candidate - the Phase 5/7 feature from
the project brief's "Locator Stability Analyzer" section.
"""

from dataclasses import dataclass
from typing import List, Optional

from uiautomator3.elements.tree import ElementTree
from uiautomator3.locator.stability import (
    hierarchy_depth_penalty,
    index_dependency_penalty,
    resource_id_stability,
    text_stability,
)
from uiautomator3.selectors.query import Selector, find_all


@dataclass
class StabilityReport:
    strategy: str
    uniqueness: float
    stability: float
    dynamic_dependency: str  # "None" | "Low" | "Medium" | "High"
    hierarchy_dependency: str
    index_dependency: str
    match_count: int
    recommendation: Optional[str] = None

    def format(self) -> str:
        lines = [
            "Locator Stability Report",
            "",
            f"Strategy: {self.strategy}",
            "",
            f"Uniqueness: {self.uniqueness * 100:.0f}%",
            f"Stability: {self.stability * 100:.0f}%",
            f"Dynamic dependency: {self.dynamic_dependency}",
            f"Hierarchy dependency: {self.hierarchy_dependency}",
            f"Index dependency: {self.index_dependency}",
        ]
        if self.recommendation:
            lines += ["", f"Recommendation:\n{self.recommendation}"]
        return "\n".join(lines)


def _classify(value: float, low: float, high: float) -> str:
    if value >= high:
        return "High"
    if value >= low:
        return "Medium"
    if value > 0:
        return "Low"
    return "None"


def analyze_locator(tree: ElementTree, selector: Selector, strategy_name: str = "custom") -> StabilityReport:
    matches = find_all(tree, selector)
    match_count = len(matches)
    uniqueness = 1.0 / match_count if match_count > 0 else 0.0

    criteria = selector.criteria
    stabilities: List[float] = []
    dynamic_score = 0.0

    if "resourceId" in criteria or "resource_id" in criteria:
        value = criteria.get("resourceId") or criteria.get("resource_id")
        s = resource_id_stability(value)
        stabilities.append(s)
        dynamic_score = max(dynamic_score, 1.0 - s)

    if "text" in criteria:
        s = text_stability(criteria["text"])
        stabilities.append(s)
        dynamic_score = max(dynamic_score, 1.0 - s)

    uses_index = "index" in criteria
    stabilities.append(index_dependency_penalty(uses_index))

    # hierarchy dependency: presence of className-only or index-only criteria
    # implies reliance on structural position rather than identity.
    identity_keys = {"resourceId", "resource_id", "text", "description", "content_description"}
    has_identity_criterion = any(k in criteria for k in identity_keys)
    hierarchy_penalty = hierarchy_depth_penalty(0 if has_identity_criterion else 5)
    stabilities.append(hierarchy_penalty)

    stability = min(stabilities) if stabilities else 0.5

    recommendation = None
    if uses_index:
        recommendation = "Avoid index-based matching; prefer a unique resource-id or text value."
    elif not has_identity_criterion:
        recommendation = "Use resource-id or text instead of structural/class-only matching."
    elif uniqueness < 1.0:
        recommendation = "This locator is not unique in the current screen; add another constraint."

    return StabilityReport(
        strategy=strategy_name,
        uniqueness=uniqueness,
        stability=stability,
        dynamic_dependency=_classify(dynamic_score, 0.3, 0.6),
        hierarchy_dependency="Low" if has_identity_criterion else "High",
        index_dependency="None" if not uses_index else "High",
        match_count=match_count,
        recommendation=recommendation,
    )
