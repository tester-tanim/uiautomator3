"""Locator candidate generation.

One candidate per strategy (resource_id, text, content_desc, class+text,
xpath, coordinate), matching docs/UIAUTOMATOR3_ARCHITECTURE.md section 5.
Relative/OCR/visual strategies are later phases (OCR/vision engines don't
exist yet); xpath here is a structural best-effort path built from the
ElementTree, not a full XPath 1.0 implementation.
"""

from typing import List, Optional

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import UIElement
from uiautomator3.locator.candidate import LocatorCandidate
from uiautomator3.locator.stability import (
    hierarchy_depth_penalty,
    index_dependency_penalty,
    resource_id_stability,
    text_stability,
)

# Base weight per strategy - the starting priority order from the spec
# (resource-id > desc > text > class+attrs > relative hierarchy > xpath >
# ocr > visual > coordinate). Actual ranking is re-sorted by composite
# score, not this table alone - see rank_candidates().
_BASE_WEIGHT = {
    "resource_id": 0.99,
    "content_description": 0.96,
    "text": 0.97,
    "class_and_text": 0.85,
    "class_name": 0.55,
    "xpath": 0.75,
    "coordinate": 0.45,
}


def _count_matches(tree: ElementTree, predicate) -> int:
    return sum(1 for e in tree if predicate(e))


def _uniqueness(matches: int) -> float:
    if matches <= 0:
        return 0.0
    return 1.0 / matches


def _specificity(num_constraints: int, max_constraints: int = 4) -> float:
    return min(1.0, num_constraints / max_constraints)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _build_xpath(element: UIElement, tree: ElementTree) -> str:
    by_id = {e.id: e for e in tree}
    segments: List[str] = []
    current: Optional[UIElement] = element
    uses_index = False

    while current is not None:
        cls = current.class_name or "*"
        parent = by_id.get(current.parent_id) if current.parent_id else None
        if parent:
            same_class_siblings = [
                by_id[cid] for cid in parent.children if cid in by_id and by_id[cid].class_name == current.class_name
            ]
            if len(same_class_siblings) > 1:
                position = next(i for i, e in enumerate(same_class_siblings) if e.id == current.id) + 1
                segments.insert(0, f"{cls}[{position}]")
                uses_index = True
            else:
                segments.insert(0, cls)
        else:
            segments.insert(0, cls)
        current = parent

    return "//" + "/".join(segments), uses_index, len(segments)


def generate_candidates(element: UIElement, tree: ElementTree) -> List[LocatorCandidate]:
    candidates: List[LocatorCandidate] = []

    if element.resource_id:
        matches = _count_matches(tree, lambda e: e.resource_id == element.resource_id)
        uniqueness = _uniqueness(matches)
        stability = resource_id_stability(element.resource_id)
        specificity = _specificity(1)
        score = _BASE_WEIGHT["resource_id"] * uniqueness * stability
        candidates.append(
            LocatorCandidate(
                strategy="resource_id",
                locator=element.resource_id,
                python_code=f"d(resourceId='{_escape(element.resource_id)}')",
                uniqueness=uniqueness,
                stability=stability,
                specificity=specificity,
                score=score,
            )
        )

    if element.content_description:
        matches = _count_matches(tree, lambda e: e.content_description == element.content_description)
        uniqueness = _uniqueness(matches)
        stability = text_stability(element.content_description)
        specificity = _specificity(1)
        score = _BASE_WEIGHT["content_description"] * uniqueness * stability
        candidates.append(
            LocatorCandidate(
                strategy="content_description",
                locator=element.content_description,
                python_code=f"d(description='{_escape(element.content_description)}')",
                uniqueness=uniqueness,
                stability=stability,
                specificity=specificity,
                score=score,
            )
        )

    if element.text:
        matches = _count_matches(tree, lambda e: e.text == element.text)
        uniqueness = _uniqueness(matches)
        stability = text_stability(element.text)
        specificity = _specificity(1)
        score = _BASE_WEIGHT["text"] * uniqueness * stability
        candidates.append(
            LocatorCandidate(
                strategy="text",
                locator=element.text,
                python_code=f"d(text='{_escape(element.text)}')",
                uniqueness=uniqueness,
                stability=stability,
                specificity=specificity,
                score=score,
            )
        )

    if element.class_name:
        matches = _count_matches(tree, lambda e: e.class_name == element.class_name)
        uniqueness = _uniqueness(matches)
        specificity = _specificity(1)
        score = _BASE_WEIGHT["class_name"] * uniqueness
        candidates.append(
            LocatorCandidate(
                strategy="class_name",
                locator=element.class_name,
                python_code=f"d(className='{_escape(element.class_name)}')",
                uniqueness=uniqueness,
                stability=1.0,
                specificity=specificity,
                score=score,
            )
        )

        if element.text:
            matches = _count_matches(tree, lambda e: e.class_name == element.class_name and e.text == element.text)
            uniqueness = _uniqueness(matches)
            stability = text_stability(element.text)
            specificity = _specificity(2)
            score = _BASE_WEIGHT["class_and_text"] * uniqueness * stability
            candidates.append(
                LocatorCandidate(
                    strategy="class_and_text",
                    locator=f"{element.class_name}[text='{element.text}']",
                    python_code=(f"d(className='{_escape(element.class_name)}', text='{_escape(element.text)}')"),
                    uniqueness=uniqueness,
                    stability=stability,
                    specificity=specificity,
                    score=score,
                )
            )

    xpath, uses_index, depth = _build_xpath(element, tree)
    stability = index_dependency_penalty(uses_index) * hierarchy_depth_penalty(depth)
    candidates.append(
        LocatorCandidate(
            strategy="xpath",
            locator=xpath,
            python_code=f"d.xpath('{_escape(xpath)}')",
            uniqueness=1.0,
            stability=stability,
            specificity=_specificity(depth, max_constraints=8),
            score=_BASE_WEIGHT["xpath"] * stability,
        )
    )

    coord_locator = f"({element.center.x}, {element.center.y})"
    candidates.append(
        LocatorCandidate(
            strategy="coordinate",
            locator=coord_locator,
            python_code=f"d.click({element.center.x}, {element.center.y})",
            uniqueness=1.0,
            stability=0.3,
            specificity=0.1,
            score=_BASE_WEIGHT["coordinate"],
        )
    )

    return candidates


def rank_candidates(candidates: List[LocatorCandidate]) -> List[LocatorCandidate]:
    """Sort by composite score descending and mark the top one as 'best'."""
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    for c in ranked:
        c.recommendation = "alternative"
    if ranked:
        ranked[0].recommendation = "best"
    return ranked
