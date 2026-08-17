from unittest.mock import MagicMock

from uiautomator3.hierarchy.engine import HierarchyEngine

VALID_XML = (
    '<hierarchy rotation="0">'
    '<node text="Login" resource-id="com.example:id/login" class="android.widget.Button" '
    'package="com.example" content-desc="" checkable="false" checked="false" clickable="true" '
    'enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" '
    'password="false" selected="false" bounds="[0,0][100,50]" />'
    "</hierarchy>"
)


def test_dump_xml_returns_raw_string():
    adb_device = MagicMock()
    adb_device.dump_hierarchy.return_value = VALID_XML
    engine = HierarchyEngine(adb_device)

    assert engine.dump_xml() == VALID_XML


def test_dump_returns_parsed_element_tree():
    adb_device = MagicMock()
    adb_device.dump_hierarchy.return_value = VALID_XML
    engine = HierarchyEngine(adb_device)

    tree = engine.dump()

    assert len(tree) == 1
    assert tree.elements[0].text == "Login"


def test_dump_xml_always_bypasses_cache():
    adb_device = MagicMock()
    adb_device.dump_hierarchy.return_value = VALID_XML
    engine = HierarchyEngine(adb_device)

    engine.dump_xml()
    engine.dump_xml()

    assert adb_device.dump_hierarchy.call_count == 2


def test_dump_is_cached_within_ttl():
    adb_device = MagicMock()
    adb_device.dump_hierarchy.return_value = VALID_XML
    engine = HierarchyEngine(adb_device)

    tree1 = engine.dump(ttl=10.0)
    tree2 = engine.dump(ttl=10.0)

    assert tree1 is tree2
    assert adb_device.dump_hierarchy.call_count == 1


def test_dump_force_bypasses_cache():
    adb_device = MagicMock()
    adb_device.dump_hierarchy.return_value = VALID_XML
    engine = HierarchyEngine(adb_device)

    engine.dump(ttl=10.0)
    engine.dump(ttl=10.0, force=True)

    assert adb_device.dump_hierarchy.call_count == 2


def test_dump_zero_ttl_never_caches():
    adb_device = MagicMock()
    adb_device.dump_hierarchy.return_value = VALID_XML
    engine = HierarchyEngine(adb_device)

    engine.dump(ttl=0)
    engine.dump(ttl=0)

    assert adb_device.dump_hierarchy.call_count == 2


def test_invalidate_forces_recompute_on_next_dump():
    adb_device = MagicMock()
    adb_device.dump_hierarchy.return_value = VALID_XML
    engine = HierarchyEngine(adb_device)

    engine.dump(ttl=10.0)
    engine.invalidate()
    engine.dump(ttl=10.0)

    assert adb_device.dump_hierarchy.call_count == 2
