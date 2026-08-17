from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.locator.generator import generate_candidates, rank_candidates


def make_element(id, **overrides):
    defaults = dict(
        id=id,
        text=None,
        content_description=None,
        resource_id=None,
        class_name=None,
        package_name="com.example",
        bounds=Bounds(100, 500, 900, 620),
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
        children=[],
    )
    defaults.update(overrides)
    return UIElement(**defaults)


def test_generates_resource_id_candidate_when_present():
    login = make_element("login", resource_id="com.example:id/login", text="Login")
    tree = ElementTree([login])

    candidates = generate_candidates(login, tree)

    strategies = {c.strategy for c in candidates}
    assert "resource_id" in strategies
    assert "text" in strategies
    assert "xpath" in strategies
    assert "coordinate" in strategies


def test_unique_resource_id_scores_higher_than_duplicated_one():
    a = make_element("a", resource_id="com.example:id/icon_title", text="CalcES")
    b = make_element("b", resource_id="com.example:id/icon_title", text="Gboard")
    tree = ElementTree([a, b])

    candidates = generate_candidates(a, tree)
    resource_id_candidate = next(c for c in candidates if c.strategy == "resource_id")
    text_candidate = next(c for c in candidates if c.strategy == "text")

    assert text_candidate.score > resource_id_candidate.score


def test_dynamic_resource_id_scores_lower():
    stable = make_element("stable", resource_id="com.example:id/login_button")
    dynamic = make_element("dynamic", resource_id="com.example:id/a3f9c21b8e77")
    tree_stable = ElementTree([stable])
    tree_dynamic = ElementTree([dynamic])

    stable_candidate = next(c for c in generate_candidates(stable, tree_stable) if c.strategy == "resource_id")
    dynamic_candidate = next(c for c in generate_candidates(dynamic, tree_dynamic) if c.strategy == "resource_id")

    assert stable_candidate.score > dynamic_candidate.score


def test_class_and_text_candidate_generated_when_both_present():
    element = make_element("e", class_name="android.widget.Button", text="Login")
    tree = ElementTree([element])

    candidates = generate_candidates(element, tree)

    assert any(c.strategy == "class_and_text" for c in candidates)


def test_no_class_and_text_when_no_text():
    element = make_element("e", class_name="android.widget.Button")
    tree = ElementTree([element])

    candidates = generate_candidates(element, tree)

    assert not any(c.strategy == "class_and_text" for c in candidates)


def test_xpath_and_coordinate_always_present():
    element = make_element("e")
    tree = ElementTree([element])

    candidates = generate_candidates(element, tree)
    strategies = {c.strategy for c in candidates}

    assert "xpath" in strategies
    assert "coordinate" in strategies


def test_xpath_candidate_uses_index_for_repeated_siblings():
    parent = make_element("p", children=["c1", "c2"])
    c1 = make_element("c1", parent_id="p", class_name="android.widget.TextView")
    c2 = make_element("c2", parent_id="p", class_name="android.widget.TextView")
    tree = ElementTree([parent, c1, c2])

    candidates = generate_candidates(c2, tree)
    xpath_candidate = next(c for c in candidates if c.strategy == "xpath")

    assert "[2]" in xpath_candidate.locator


def test_rank_candidates_marks_top_as_best():
    login = make_element("login", resource_id="com.example:id/login", text="Login")
    tree = ElementTree([login])

    ranked = rank_candidates(generate_candidates(login, tree))

    assert ranked[0].recommendation == "best"
    assert all(c.recommendation == "alternative" for c in ranked[1:])
    scores = [c.score for c in ranked]
    assert scores == sorted(scores, reverse=True)


def test_coordinate_locator_has_lowest_typical_score():
    login = make_element("login", resource_id="com.example:id/login", text="Login")
    tree = ElementTree([login])

    ranked = rank_candidates(generate_candidates(login, tree))
    coordinate = next(c for c in ranked if c.strategy == "coordinate")

    assert coordinate.score <= ranked[0].score


def test_python_code_is_valid_syntax():
    import ast

    login = make_element("login", resource_id="com.example:id/login", text="Login's")
    tree = ElementTree([login])

    for candidate in generate_candidates(login, tree):
        ast.parse(candidate.python_code)
