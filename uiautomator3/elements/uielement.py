"""The normalized UIElement model.

This is the single representation every locator strategy (resource-id,
XPath, OCR, vision - later phases) produces and consumes. It replaces
uiautomator2's split between RPC-object-based `UiObject.info` and
lxml-based `XMLElement` (see docs/UIAUTOMATOR2_ANALYSIS.md section 6) with
one typed dataclass built once per hierarchy snapshot.
"""
from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional


@dataclass(frozen=True)
class Bounds:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def center(self) -> "Point":
        return Point(self.left + self.width // 2, self.top + self.height // 2)

    @property
    def area(self) -> int:
        return max(0, self.width) * max(0, self.height)

    def contains_point(self, x: int, y: int) -> bool:
        return self.left <= x < self.right and self.top <= y < self.bottom

    def intersects(self, other: "Bounds") -> bool:
        return not (
            self.right <= other.left
            or other.right <= self.left
            or self.bottom <= other.top
            or other.bottom <= self.top
        )


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass
class UIElement:
    id: str
    text: Optional[str]
    content_description: Optional[str]
    resource_id: Optional[str]
    class_name: Optional[str]
    package_name: Optional[str]
    bounds: Bounds
    clickable: bool
    enabled: bool
    visible: bool
    focused: bool
    selected: bool
    checked: bool
    scrollable: bool
    long_clickable: bool
    checkable: bool
    password: bool
    parent_id: Optional[str]
    children: List[str] = field(default_factory=list)
    depth: int = 0
    index: int = 0
    role: Optional[str] = None
    ocr_text: Optional[str] = None
    visual_confidence: Optional[float] = None
    source: FrozenSet[str] = frozenset({"hierarchy"})

    @property
    def center(self) -> Point:
        return self.bounds.center
