from uiautomator3.elements.spatial import (
    aligned_with,
    contains,
    distance,
    is_above,
    is_below,
    is_inside,
    is_left_of,
    is_right_of,
    nearest,
    overlaps,
    same_column,
    same_row,
)
from uiautomator3.elements.uielement import Bounds, UIElement


def make_element(id, left, top, right, bottom):
    return UIElement(
        id=id,
        text=None,
        content_description=None,
        resource_id=None,
        class_name=None,
        package_name=None,
        bounds=Bounds(left, top, right, bottom),
        clickable=False,
        enabled=True,
        visible=True,
        focused=False,
        selected=False,
        checked=False,
        scrollable=False,
        long_clickable=False,
        checkable=False,
        password=False,
        parent_id=None,
    )


def test_is_above_and_below():
    top = make_element("top", 0, 0, 100, 50)
    bottom = make_element("bottom", 0, 100, 100, 150)
    assert is_above(top, bottom)
    assert is_below(bottom, top)
    assert not is_above(bottom, top)


def test_is_left_of_and_right_of():
    left = make_element("left", 0, 0, 50, 50)
    right = make_element("right", 100, 0, 150, 50)
    assert is_left_of(left, right)
    assert is_right_of(right, left)


def test_is_inside_and_contains():
    outer = make_element("outer", 0, 0, 200, 200)
    inner = make_element("inner", 10, 10, 50, 50)
    assert is_inside(inner, outer)
    assert contains(outer, inner)
    assert not is_inside(outer, inner)


def test_overlaps():
    a = make_element("a", 0, 0, 50, 50)
    b = make_element("b", 25, 25, 75, 75)
    c = make_element("c", 100, 100, 150, 150)
    assert overlaps(a, b)
    assert not overlaps(a, c)


def test_same_row():
    a = make_element("a", 0, 0, 50, 50)
    b = make_element("b", 100, 10, 150, 60)
    c = make_element("c", 200, 200, 250, 250)
    assert same_row(a, b)
    assert not same_row(a, c)


def test_same_column():
    a = make_element("a", 0, 0, 50, 50)
    b = make_element("b", 10, 100, 60, 150)
    c = make_element("c", 200, 200, 250, 250)
    assert same_column(a, b)
    assert not same_column(a, c)


def test_aligned_with():
    a = make_element("a", 0, 0, 50, 50)
    row_match = make_element("row", 100, 10, 150, 60)
    col_match = make_element("col", 10, 100, 60, 150)
    unrelated = make_element("unrelated", 500, 500, 550, 550)
    assert aligned_with(a, row_match)
    assert aligned_with(a, col_match)
    assert not aligned_with(a, unrelated)


def test_distance():
    a = make_element("a", 0, 0, 10, 10)  # center (5,5)
    b = make_element("b", 10, 0, 20, 10)  # center (15,5)
    assert distance(a, b) == 10


def test_nearest():
    target = make_element("target", 0, 0, 10, 10)
    near = make_element("near", 20, 0, 30, 10)
    far = make_element("far", 1000, 0, 1010, 10)
    assert nearest(target, [far, near]).id == "near"


def test_nearest_raises_on_empty():
    target = make_element("target", 0, 0, 10, 10)
    try:
        nearest(target, [])
        assert False, "expected ValueError"
    except ValueError:
        pass
