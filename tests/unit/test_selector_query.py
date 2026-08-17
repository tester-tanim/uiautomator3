from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.selectors.query import Selector, find_all, find_first


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


def build_tree():
    return ElementTree(
        [
            make_element("a", text="Login", resource_id="com.example:id/login", clickable=True),
            make_element("b", text="Login", resource_id="com.example:id/login2", clickable=False),
            make_element("c", text="Cancel", class_name="android.widget.Button"),
            make_element("d", content_description="Email input", class_name="android.widget.EditText"),
        ]
    )


def test_exact_text_match():
    tree = build_tree()
    matches = find_all(tree, Selector(text="Login"))
    assert {e.id for e in matches} == {"a", "b"}


def test_exact_resource_id_match_is_unique():
    tree = build_tree()
    matches = find_all(tree, Selector(resourceId="com.example:id/login"))
    assert [e.id for e in matches] == ["a"]


def test_combined_criteria_narrows_match():
    tree = build_tree()
    matches = find_all(tree, Selector(text="Login", clickable=True))
    assert [e.id for e in matches] == ["a"]


def test_text_contains():
    tree = build_tree()
    matches = find_all(tree, Selector(textContains="ogi"))
    assert {e.id for e in matches} == {"a", "b"}


def test_text_starts_with():
    tree = build_tree()
    matches = find_all(tree, Selector(textStartsWith="Can"))
    assert [e.id for e in matches] == ["c"]


def test_text_ends_with():
    tree = build_tree()
    matches = find_all(tree, Selector(textEndsWith="cel"))
    assert [e.id for e in matches] == ["c"]


def test_text_matches_regex():
    tree = build_tree()
    matches = find_all(tree, Selector(textMatches="^Log.*$"))
    assert {e.id for e in matches} == {"a", "b"}


def test_description_alias():
    tree = build_tree()
    matches = find_all(tree, Selector(description="Email input"))
    assert [e.id for e in matches] == ["d"]


def test_class_name_alias():
    tree = build_tree()
    matches = find_all(tree, Selector(className="android.widget.Button"))
    assert [e.id for e in matches] == ["c"]


def test_find_first_returns_none_when_no_match():
    tree = build_tree()
    assert find_first(tree, Selector(text="Nonexistent")) is None


def test_find_first_returns_first_match():
    tree = build_tree()
    result = find_first(tree, Selector(text="Login"))
    assert result.id == "a"


def test_suffix_no_match_when_field_is_none():
    tree = build_tree()
    matches = find_all(tree, Selector(textContains="x"))
    # element c/d have no text at all in some cases; ensure no crash and correct filtering
    assert all(e.text and "x" in e.text for e in matches) or matches == []


def test_selector_repr():
    s = Selector(text="Login", clickable=True)
    assert "text='Login'" in repr(s)
