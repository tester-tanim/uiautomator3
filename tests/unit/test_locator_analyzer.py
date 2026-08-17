from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.locator.analyzer import analyze_locator
from uiautomator3.selectors.query import Selector


def make_element(id, **overrides):
    defaults = dict(
        id=id,
        text=None,
        content_description=None,
        resource_id=None,
        class_name=None,
        package_name="com.example",
        bounds=Bounds(0, 0, 100, 50),
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
    defaults.update(overrides)
    return UIElement(**defaults)


def test_unique_resource_id_has_high_uniqueness():
    tree = ElementTree([make_element("a", resource_id="com.example:id/login")])
    report = analyze_locator(tree, Selector(resourceId="com.example:id/login"), "resource_id")
    assert report.uniqueness == 1.0
    assert report.match_count == 1


def test_duplicated_resource_id_has_lower_uniqueness():
    tree = ElementTree(
        [
            make_element("a", resource_id="com.example:id/icon"),
            make_element("b", resource_id="com.example:id/icon"),
        ]
    )
    report = analyze_locator(tree, Selector(resourceId="com.example:id/icon"), "resource_id")
    assert report.uniqueness == 0.5
    assert report.match_count == 2


def test_dynamic_resource_id_flagged_as_dynamic_dependency():
    tree = ElementTree([make_element("a", resource_id="com.example:id/a3f9c21b8e77")])
    report = analyze_locator(tree, Selector(resourceId="com.example:id/a3f9c21b8e77"), "resource_id")
    assert report.dynamic_dependency in ("Medium", "High")


def test_class_only_selector_has_high_hierarchy_dependency():
    tree = ElementTree([make_element("a", class_name="android.widget.Button")])
    report = analyze_locator(tree, Selector(className="android.widget.Button"), "class_name")
    assert report.hierarchy_dependency == "High"
    assert report.recommendation is not None


def test_index_based_selector_flagged():
    tree = ElementTree([make_element("a", index=2)])
    report = analyze_locator(tree, Selector(index=2, className="android.widget.TextView"), "class_and_index")
    assert report.index_dependency == "High"
    assert "index" in report.recommendation.lower() or "unique" in report.recommendation.lower()


def test_zero_matches_gives_zero_uniqueness():
    tree = ElementTree([make_element("a", text="Login")])
    report = analyze_locator(tree, Selector(text="Nonexistent"), "text")
    assert report.uniqueness == 0.0
    assert report.match_count == 0


def test_format_includes_key_fields():
    tree = ElementTree([make_element("a", resource_id="com.example:id/login")])
    report = analyze_locator(tree, Selector(resourceId="com.example:id/login"), "resource_id")
    text = report.format()
    assert "Uniqueness" in text
    assert "Stability" in text
    assert "resource_id" in text
