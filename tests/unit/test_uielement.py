from uiautomator3.elements.uielement import Bounds, Point, UIElement


def make_bounds(left=0, top=0, right=100, bottom=50):
    return Bounds(left=left, top=top, right=right, bottom=bottom)


def test_bounds_width_height():
    b = make_bounds(10, 20, 110, 70)
    assert b.width == 100
    assert b.height == 50


def test_bounds_center():
    b = make_bounds(0, 0, 100, 50)
    assert b.center == Point(50, 25)


def test_bounds_area():
    b = make_bounds(0, 0, 100, 50)
    assert b.area == 5000


def test_bounds_zero_area_when_degenerate():
    b = make_bounds(10, 10, 10, 10)
    assert b.area == 0


def test_bounds_contains_point():
    b = make_bounds(0, 0, 100, 100)
    assert b.contains_point(50, 50)
    assert not b.contains_point(100, 100)
    assert not b.contains_point(-1, 50)


def test_bounds_intersects():
    a = make_bounds(0, 0, 50, 50)
    b = make_bounds(25, 25, 75, 75)
    c = make_bounds(100, 100, 150, 150)
    assert a.intersects(b)
    assert not a.intersects(c)


def make_element(**overrides):
    defaults = dict(
        id="e0",
        text="Login",
        content_description=None,
        resource_id="com.example:id/login",
        class_name="android.widget.Button",
        package_name="com.example",
        bounds=make_bounds(),
        clickable=True,
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
    defaults.update(overrides)
    return UIElement(**defaults)


def test_uielement_center_delegates_to_bounds():
    e = make_element(bounds=make_bounds(0, 0, 100, 50))
    assert e.center == Point(50, 25)


def test_uielement_default_source():
    e = make_element()
    assert e.source == frozenset({"hierarchy"})
