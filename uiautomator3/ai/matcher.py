"""Natural-language-ish element matching, no LLM required.

`d.ai.find("Login button")` needs to resolve a free-text description to a
concrete UIElement without calling out to an external model (project spec
section 39: "Do not make an external LLM mandatory"). This uses
deterministic token-overlap scoring against text/content-description, with
a role-keyword boost, in the same spirit as the rule-based locator scoring
engine from Phase 5 (docs/UIAUTOMATOR3_ARCHITECTURE.md section 5).
"""

import re
from typing import List, Optional, Tuple

from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import UIElement

# Common UI role words a description might contain, mapped to the role(s)
# elements/roles.py can classify. Matching one gives a modest confidence
# boost - it's a hint, not a hard filter, since roles are heuristic too.
_ROLE_KEYWORDS = {
    "button": {"button"},
    "btn": {"button"},
    "input": {"input"},
    "field": {"input"},
    "textbox": {"input"},
    "text": {"text"},
    "label": {"text"},
    "checkbox": {"checkbox"},
    "radio": {"radio"},
    "switch": {"switch"},
    "toggle": {"switch"},
    "image": {"image"},
    "icon": {"image"},
    "list": {"list"},
    "dropdown": {"dropdown"},
    "spinner": {"dropdown"},
    "slider": {"slider"},
    "tab": {"tab"},
    "menu": {"menu"},
    "dialog": {"dialog"},
}

_STOPWORDS = {"the", "a", "an", "on", "in", "for", "to", "of", "that", "this"}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOPWORDS]


def _element_text_tokens(element: UIElement) -> List[str]:
    combined = " ".join(filter(None, [element.text, element.content_description]))
    return _tokenize(combined)


def _score(description_tokens: List[str], role_hints: set, element: UIElement) -> float:
    element_tokens = _element_text_tokens(element)
    if not element_tokens:
        text_score = 0.0
    else:
        overlap = len(set(description_tokens) & set(element_tokens))
        text_score = overlap / max(len(description_tokens), 1)

    role_score = 0.0
    if role_hints and element.role in role_hints:
        role_score = 0.3

    if text_score == 0.0 and role_score == 0.0:
        return 0.0

    # weighted so text overlap dominates but a role match alone can still
    # surface a plausible candidate (e.g. "the button" with no text match)
    score = min(1.0, text_score * 0.8 + role_score)
    if element.clickable:
        score = min(1.0, score + 0.05)
    return score


def find_best_match(tree: ElementTree, description: str) -> Optional[Tuple[UIElement, float]]:
    """Return the (element, confidence) pair best matching `description`, or None."""
    tokens = _tokenize(description)
    role_hints: set = set()
    for word in tokens:
        role_hints |= _ROLE_KEYWORDS.get(word, set())
    # role keywords themselves shouldn't count as text tokens to overlap
    # against (an element literally named "Button" is rare and coincidental)
    text_tokens = [t for t in tokens if t not in _ROLE_KEYWORDS]

    best: Optional[Tuple[UIElement, float]] = None
    for element in tree:
        score = _score(text_tokens, role_hints, element)
        if score <= 0:
            continue
        if best is None or score > best[1]:
            best = (element, score)
    return best


def find_all_matches(tree: ElementTree, description: str, min_confidence: float = 0.2) -> List[Tuple[UIElement, float]]:
    tokens = _tokenize(description)
    role_hints: set = set()
    for word in tokens:
        role_hints |= _ROLE_KEYWORDS.get(word, set())
    text_tokens = [t for t in tokens if t not in _ROLE_KEYWORDS]

    results = []
    for element in tree:
        score = _score(text_tokens, role_hints, element)
        if score >= min_confidence:
            results.append((element, score))
    results.sort(key=lambda pair: pair[1], reverse=True)
    return results
