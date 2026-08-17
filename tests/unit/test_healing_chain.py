from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.healing.chain import heal
from uiautomator3.healing.snapshot import ElementSnapshot
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


def test_snapshot_from_element():
    element = make_element(
        "a",
        text="Login",
        content_description="Login btn",
        resource_id="id/login",
        class_name="android.widget.Button",
        role="button",
    )
    snapshot = ElementSnapshot.from_element(element)
    assert snapshot.text == "Login"
    assert snapshot.resource_id == "id/login"
    assert snapshot.role == "button"


def test_heal_recovers_via_text_when_resource_id_changed():
    # original element had resource_id="old_id" and text="Login"; the app
    # rebuilt with a new resource_id but the same text.
    snapshot = ElementSnapshot(
        text="Login", content_description=None, resource_id="old_id", class_name="android.widget.Button", role="button"
    )
    current_element = make_element("a", text="Login", resource_id="new_id", class_name="android.widget.Button")
    tree = ElementTree([current_element])

    report = heal(tree, Selector(resourceId="old_id"), snapshot)

    assert report.recovered is True
    assert report.recovered_via == "text"
    assert report.recovered_element.id == "a"
    assert report.confidence > 0


def test_heal_prefers_resource_id_when_still_present():
    snapshot = ElementSnapshot(
        text="Login",
        content_description=None,
        resource_id="id/login",
        class_name="android.widget.Button",
        role="button",
    )
    current_element = make_element("a", text="Different now", resource_id="id/login")
    tree = ElementTree([current_element])

    report = heal(tree, Selector(resourceId="id/login"), snapshot)

    assert report.recovered_via == "resource_id"


def test_heal_fails_when_nothing_matches():
    snapshot = ElementSnapshot(
        text="Login", content_description=None, resource_id="old_id", class_name="android.widget.Button", role="button"
    )
    tree = ElementTree([make_element("a", text="Completely Different")])

    report = heal(tree, Selector(resourceId="old_id"), snapshot)

    assert report.recovered is False
    assert report.recovered_element is None
    assert "resource_id" in report.attempted_strategies
    assert "text" in report.attempted_strategies


def test_heal_respects_min_confidence():
    # two elements share the same text -> low uniqueness -> low confidence
    snapshot = ElementSnapshot(text="Login", content_description=None, resource_id="old_id", class_name=None, role=None)
    tree = ElementTree([make_element("a", text="Login"), make_element("b", text="Login")])

    report = heal(tree, Selector(resourceId="old_id"), snapshot, min_confidence=0.85)

    # text strategy alone with 2 matches yields confidence 0.85 * 0.5 = 0.425 < 0.85
    assert report.recovered is False


def test_heal_skips_strategies_with_no_snapshot_value():
    snapshot = ElementSnapshot(text=None, content_description=None, resource_id=None, class_name=None, role=None)
    tree = ElementTree([make_element("a", text="Login")])

    report = heal(tree, Selector(resourceId="old_id"), snapshot)

    assert report.recovered is False
    assert report.attempted_strategies == []


def test_report_format_when_recovered():
    snapshot = ElementSnapshot(text="Login", content_description=None, resource_id="old_id", class_name=None, role=None)
    tree = ElementTree([make_element("a", text="Login")])
    report = heal(tree, Selector(resourceId="old_id"), snapshot)

    text = report.format()
    assert "Recovered using" in text
    assert "text" in text


def test_report_format_when_not_recovered():
    snapshot = ElementSnapshot(text=None, content_description=None, resource_id=None, class_name=None, role=None)
    tree = ElementTree([])
    report = heal(tree, Selector(resourceId="old_id"), snapshot)

    text = report.format()
    assert "No recovery candidate found" in text
