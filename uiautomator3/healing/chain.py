"""The self-healing fallback chain.

Per docs/UIAUTOMATOR3_ARCHITECTURE.md section 7:

    locator.click()
         |
         v
     primary strategy fails (ElementNotFoundError)
         |
         v
     HealingChain: [resource_id, accessibility_id, text, class+text,
                     relative_hierarchy, ocr, visual]
         |  (skip strategies already tried; try next in order)
         v
     candidate found? --no--> raise with full HealingReport attached
         | yes
         v
     confidence >= settings.self_healing_min_confidence?
         | yes
         v
     execute action, attach HealingReport

OCR/visual strategies are intentionally NOT included in the default chain
here - they require a provider instance and a live screenshot, which is a
meaningfully more expensive/optional fallback than a hierarchy re-query.
Callers who want OCR/visual healing can extend the chain explicitly (see
`extra_strategies` on `heal()`); the hierarchy-based chain covers the
common "resource-id renamed but text/class stayed the same" case that
motivates this feature.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import UIElement
from uiautomator3.healing.snapshot import ElementSnapshot
from uiautomator3.selectors.query import Selector, find_all

# Default strategy order, matching the architecture doc. Each entry is
# (name, selector_builder) where selector_builder returns None if the
# snapshot doesn't have the attribute this strategy needs (that strategy
# is then skipped, not tried with a null value).
StrategyBuilder = Callable[[ElementSnapshot], Optional[Selector]]


def _resource_id_strategy(snapshot: ElementSnapshot) -> Optional[Selector]:
    if not snapshot.resource_id:
        return None
    return Selector(resourceId=snapshot.resource_id)


def _content_description_strategy(snapshot: ElementSnapshot) -> Optional[Selector]:
    if not snapshot.content_description:
        return None
    return Selector(description=snapshot.content_description)


def _text_strategy(snapshot: ElementSnapshot) -> Optional[Selector]:
    if not snapshot.text:
        return None
    return Selector(text=snapshot.text)


def _class_and_text_strategy(snapshot: ElementSnapshot) -> Optional[Selector]:
    if not snapshot.class_name or not snapshot.text:
        return None
    return Selector(className=snapshot.class_name, text=snapshot.text)


def _class_and_role_strategy(snapshot: ElementSnapshot) -> Optional[Selector]:
    if not snapshot.class_name:
        return None
    return Selector(className=snapshot.class_name)


DEFAULT_CHAIN: List[StrategyBuilder] = [
    _resource_id_strategy,
    _content_description_strategy,
    _text_strategy,
    _class_and_text_strategy,
    _class_and_role_strategy,
]

_STRATEGY_NAMES = [
    "resource_id",
    "content_description",
    "text",
    "class_and_text",
    "class_name",
]


@dataclass
class HealingCandidate:
    strategy: str
    selector: Selector
    element: UIElement
    confidence: float


@dataclass
class HealingReport:
    original_selector: Selector
    attempted_strategies: List[str] = field(default_factory=list)
    recovered: bool = False
    recovered_via: Optional[str] = None
    recovered_element: Optional[UIElement] = None
    confidence: float = 0.0

    def format(self) -> str:
        lines = [
            "Original locator:",
            repr(self.original_selector),
            "",
            "FAILED",
            "",
        ]
        if self.recovered:
            lines += [
                "Recovered using:",
                self.recovered_via or "?",
                "",
                "Confidence:",
                f"{self.confidence * 100:.0f}%",
            ]
        else:
            lines += ["No recovery candidate found.", f"Strategies tried: {', '.join(self.attempted_strategies)}"]
        return "\n".join(lines)


def _confidence_for(strategy_index: int, match_count: int) -> float:
    """Earlier strategies (resource_id, description) are inherently more
    trustworthy than later ones (bare class_name); uniqueness of the match
    within the current tree further scales confidence down."""
    base = [0.95, 0.9, 0.85, 0.75, 0.5][min(strategy_index, 4)]
    uniqueness = 1.0 / match_count if match_count > 0 else 0.0
    return base * uniqueness


def heal(
    tree: ElementTree,
    original_selector: Selector,
    snapshot: ElementSnapshot,
    min_confidence: float = 0.85,
    chain: Optional[List[StrategyBuilder]] = None,
) -> HealingReport:
    """Attempt to recover a broken locator using `snapshot`'s remembered attributes."""
    chain = chain if chain is not None else DEFAULT_CHAIN
    report = HealingReport(original_selector=original_selector)

    for index, builder in enumerate(chain):
        selector = builder(snapshot)
        if selector is None:
            continue

        strategy_name = _STRATEGY_NAMES[index] if index < len(_STRATEGY_NAMES) else f"strategy_{index}"
        report.attempted_strategies.append(strategy_name)

        matches = find_all(tree, selector)
        if not matches:
            continue

        confidence = _confidence_for(index, len(matches))
        if confidence < min_confidence:
            continue

        report.recovered = True
        report.recovered_via = strategy_name
        report.recovered_element = matches[0]
        report.confidence = confidence
        return report

    return report
