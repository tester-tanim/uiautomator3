"""Spatial relationship queries over UIElement bounds.

Pure geometry, computed against an already-collected ElementTree - no
device round-trip per query. Generalizes uiautomator2's
`.right()/.left()/.up()/.down()` (which each require a second live
selector query, see docs/UIAUTOMATOR2_ANALYSIS.md section 4) into
one-shot geometry over a snapshot.
"""

from typing import List

from uiautomator3.elements.uielement import UIElement


def is_above(a: UIElement, b: UIElement) -> bool:
    """True if `a` is entirely above `b` (a's bottom <= b's top)."""
    return a.bounds.bottom <= b.bounds.top


def is_below(a: UIElement, b: UIElement) -> bool:
    return a.bounds.top >= b.bounds.bottom


def is_left_of(a: UIElement, b: UIElement) -> bool:
    return a.bounds.right <= b.bounds.left


def is_right_of(a: UIElement, b: UIElement) -> bool:
    return a.bounds.left >= b.bounds.right


def is_inside(a: UIElement, b: UIElement) -> bool:
    """True if `a`'s bounds are fully contained within `b`'s bounds."""
    return (
        a.bounds.left >= b.bounds.left
        and a.bounds.top >= b.bounds.top
        and a.bounds.right <= b.bounds.right
        and a.bounds.bottom <= b.bounds.bottom
    )


def contains(a: UIElement, b: UIElement) -> bool:
    return is_inside(b, a)


def overlaps(a: UIElement, b: UIElement) -> bool:
    return a.bounds.intersects(b.bounds)


def same_row(a: UIElement, b: UIElement, tolerance: int = 5) -> bool:
    """True if `a` and `b` vertically overlap within `tolerance` px."""
    return not (a.bounds.bottom + tolerance <= b.bounds.top or b.bounds.bottom + tolerance <= a.bounds.top)


def same_column(a: UIElement, b: UIElement, tolerance: int = 5) -> bool:
    """True if `a` and `b` horizontally overlap within `tolerance` px."""
    return not (a.bounds.right + tolerance <= b.bounds.left or b.bounds.right + tolerance <= a.bounds.left)


def aligned_with(a: UIElement, b: UIElement, tolerance: int = 5) -> bool:
    """True if `a` and `b` share either a row or column alignment."""
    return same_row(a, b, tolerance) or same_column(a, b, tolerance)


def distance(a: UIElement, b: UIElement) -> float:
    """Euclidean distance between element centers."""
    ac, bc = a.bounds.center, b.bounds.center
    return ((ac.x - bc.x) ** 2 + (ac.y - bc.y) ** 2) ** 0.5


def nearest(target: UIElement, candidates: List[UIElement]) -> UIElement:
    """Return the candidate closest (by center distance) to `target`."""
    if not candidates:
        raise ValueError("candidates must not be empty")
    return min(candidates, key=lambda c: distance(target, c))
