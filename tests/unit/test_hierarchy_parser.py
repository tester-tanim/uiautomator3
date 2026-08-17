import pytest

from uiautomator3.hierarchy.parser import HierarchyParseError, parse_hierarchy

SAMPLE_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.example"
        content-desc="" checkable="false" checked="false" clickable="false" enabled="true"
        focusable="false" focused="false" scrollable="false" long-clickable="false"
        password="false" selected="false" bounds="[0,0][1080,2400]">
    <node index="0" text="" resource-id="com.example:id/email" class="android.widget.EditText"
          package="com.example" content-desc="" checkable="false" checked="false" clickable="true"
          enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false"
          password="false" selected="false" bounds="[100,200][900,300]" />
    <node index="1" text="Login" resource-id="com.example:id/login" class="android.widget.Button"
          package="com.example" content-desc="Login button" checkable="false" checked="false"
          clickable="true" enabled="true" focusable="true" focused="false" scrollable="false"
          long-clickable="false" password="false" selected="false" bounds="[100,500][900,620]" />
  </node>
</hierarchy>"""

EMPTY_XML = '<hierarchy rotation="0" />'


def test_parses_rotation():
    tree = parse_hierarchy(SAMPLE_XML)
    assert tree.rotation == 0


def test_parses_all_nodes():
    tree = parse_hierarchy(SAMPLE_XML)
    assert len(tree) == 3  # root FrameLayout + EditText + Button


def test_parses_attributes_correctly():
    tree = parse_hierarchy(SAMPLE_XML)
    login = next(e for e in tree if e.resource_id == "com.example:id/login")
    assert login.text == "Login"
    assert login.content_description == "Login button"
    assert login.class_name == "android.widget.Button"
    assert login.package_name == "com.example"
    assert login.clickable is True
    assert login.enabled is True
    assert login.bounds.left == 100
    assert login.bounds.top == 500
    assert login.bounds.right == 900
    assert login.bounds.bottom == 620


def test_empty_string_attributes_become_none():
    tree = parse_hierarchy(SAMPLE_XML)
    root = next(e for e in tree if e.class_name == "android.widget.FrameLayout")
    assert root.text is None
    assert root.resource_id is None
    assert root.content_description is None


def test_parent_child_relationships():
    tree = parse_hierarchy(SAMPLE_XML)
    root = next(e for e in tree if e.parent_id is None)
    children = tree.children_of(root)
    assert len(children) == 2
    assert {c.resource_id for c in children} == {"com.example:id/email", "com.example:id/login"}


def test_depth_is_tracked():
    tree = parse_hierarchy(SAMPLE_XML)
    root = next(e for e in tree if e.parent_id is None)
    login = next(e for e in tree if e.resource_id == "com.example:id/login")
    assert root.depth == 0
    assert login.depth == 1


def test_role_is_assigned():
    tree = parse_hierarchy(SAMPLE_XML)
    login = next(e for e in tree if e.resource_id == "com.example:id/login")
    email = next(e for e in tree if e.resource_id == "com.example:id/email")
    assert login.role == "button"
    assert email.role == "input"


def test_visible_false_for_zero_area_bounds():
    xml = SAMPLE_XML.replace('bounds="[100,200][900,300]"', 'bounds="[100,200][100,200]"')
    tree = parse_hierarchy(xml)
    email = next(e for e in tree if e.resource_id == "com.example:id/email")
    assert email.visible is False


def test_raises_on_invalid_xml():
    with pytest.raises(HierarchyParseError):
        parse_hierarchy("<not valid xml")


def test_raises_on_invalid_bounds():
    xml = SAMPLE_XML.replace('bounds="[100,500][900,620]"', 'bounds="garbage"')
    with pytest.raises(HierarchyParseError):
        parse_hierarchy(xml)


def test_empty_hierarchy_produces_empty_tree():
    tree = parse_hierarchy(EMPTY_XML)
    assert len(tree) == 0
