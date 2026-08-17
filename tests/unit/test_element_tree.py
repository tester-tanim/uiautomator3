from uiautomator3.elements.tree import ElementTree
from uiautomator3.elements.uielement import Bounds, UIElement


def make_element(id, parent_id=None, children=None, resource_id=None, text=None, class_name=None, **overrides):
    defaults = dict(
        id=id,
        text=text,
        content_description=None,
        resource_id=resource_id,
        class_name=class_name,
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
        parent_id=parent_id,
        children=children or [],
    )
    defaults.update(overrides)
    return UIElement(**defaults)


def build_sample_tree():
    # root
    #  ├── a (resource_id=btn1, text=Login)
    #  └── b
    #       ├── c (text=Login)
    #       └── d
    root = make_element("root", children=["a", "b"])
    a = make_element("a", parent_id="root", resource_id="btn1", text="Login")
    b = make_element("b", parent_id="root", children=["c", "d"])
    c = make_element("c", parent_id="b", text="Login")
    d = make_element("d", parent_id="b")
    return ElementTree([root, a, b, c, d])


def test_by_id_lookup():
    tree = build_sample_tree()
    assert tree.get("a").id == "a"
    assert tree.get("missing") is None


def test_by_resource_id_index():
    tree = build_sample_tree()
    assert [e.id for e in tree.by_resource_id["btn1"]] == ["a"]


def test_by_text_index_has_multiple_matches():
    tree = build_sample_tree()
    assert sorted(e.id for e in tree.by_text["Login"]) == ["a", "c"]


def test_parent_of():
    tree = build_sample_tree()
    assert tree.parent_of(tree.get("a")).id == "root"
    assert tree.parent_of(tree.get("root")) is None


def test_children_of():
    tree = build_sample_tree()
    assert [e.id for e in tree.children_of(tree.get("b"))] == ["c", "d"]


def test_ancestors_of():
    tree = build_sample_tree()
    assert [e.id for e in tree.ancestors_of(tree.get("c"))] == ["b", "root"]


def test_descendants_of():
    tree = build_sample_tree()
    descendant_ids = {e.id for e in tree.descendants_of(tree.get("root"))}
    assert descendant_ids == {"a", "b", "c", "d"}


def test_siblings_of_excludes_self_by_default():
    tree = build_sample_tree()
    assert [e.id for e in tree.siblings_of(tree.get("c"))] == ["d"]


def test_siblings_of_includes_self_when_requested():
    tree = build_sample_tree()
    assert [e.id for e in tree.siblings_of(tree.get("c"), include_self=True)] == ["c", "d"]


def test_siblings_of_root_level():
    tree = build_sample_tree()
    assert [e.id for e in tree.siblings_of(tree.get("a"))] == ["b"]


def test_preceding_and_following_siblings():
    tree = build_sample_tree()
    assert [e.id for e in tree.preceding_siblings_of(tree.get("d"))] == ["c"]
    assert [e.id for e in tree.following_siblings_of(tree.get("c"))] == ["d"]
    assert tree.preceding_siblings_of(tree.get("c")) == []
    assert tree.following_siblings_of(tree.get("d")) == []


def test_len_and_iter():
    tree = build_sample_tree()
    assert len(tree) == 5
    assert {e.id for e in tree} == {"root", "a", "b", "c", "d"}
