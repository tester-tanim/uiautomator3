from uiautomator3.ai.matcher import find_all_matches, find_best_match
from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement


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
        role=None,
    )
    defaults.update(overrides)
    return UIElement(**defaults)


def test_exact_text_match_scores_highest():
    login = make_element("a", text="Login", role="button", clickable=True)
    cancel = make_element("b", text="Cancel", role="button", clickable=True)
    tree = ElementTree([login, cancel])

    result = find_best_match(tree, "Login button")

    assert result is not None
    element, confidence = result
    assert element.id == "a"
    assert confidence > 0.5


def test_content_description_also_matches():
    element = make_element("a", content_description="Login button", role="button", clickable=True)
    tree = ElementTree([element])

    result = find_best_match(tree, "the login button")

    assert result is not None
    assert result[0].id == "a"


def test_role_keyword_alone_gives_some_score():
    button = make_element("a", text="Submit", role="button", clickable=True)
    text = make_element("b", text="Some paragraph", role="text")
    tree = ElementTree([button, text])

    result = find_best_match(tree, "button")

    assert result is not None
    assert result[0].role == "button"


def test_no_match_returns_none():
    tree = ElementTree([make_element("a", text="Login")])
    result = find_best_match(tree, "completely unrelated description xyz")
    assert result is None


def test_find_all_matches_sorted_descending():
    exact = make_element("a", text="Login", clickable=True)
    partial = make_element("b", text="Login form", clickable=True)
    tree = ElementTree([partial, exact])

    results = find_all_matches(tree, "Login")

    assert len(results) == 2
    assert results[0][1] >= results[1][1]


def test_find_all_matches_respects_min_confidence():
    weak = make_element("a", text="somewhat related word")
    tree = ElementTree([weak])

    results = find_all_matches(tree, "login", min_confidence=0.9)

    assert results == []


def test_empty_tree_returns_no_matches():
    tree = ElementTree([])
    assert find_best_match(tree, "anything") is None
    assert find_all_matches(tree, "anything") == []


def test_clickable_elements_get_small_boost():
    clickable = make_element("a", text="Login", clickable=True)
    not_clickable = make_element("b", text="Login", clickable=False)
    tree_clickable = ElementTree([clickable])
    tree_not = ElementTree([not_clickable])

    _, score_clickable = find_best_match(tree_clickable, "Login")
    _, score_not = find_best_match(tree_not, "Login")

    assert score_clickable >= score_not
