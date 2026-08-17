from uiautomator3.locator.stability import (
    hierarchy_depth_penalty,
    index_dependency_penalty,
    is_dynamic_value,
    resource_id_stability,
    text_stability,
)


def test_is_dynamic_value_detects_hex_ids():
    assert is_dynamic_value("a3f9c21b8e77")


def test_is_dynamic_value_detects_numeric():
    assert is_dynamic_value("123456789")


def test_is_dynamic_value_detects_uuid():
    assert is_dynamic_value("550e8400-e29b-41d4-a716-446655440000")


def test_is_dynamic_value_detects_numeric_suffix():
    assert is_dynamic_value("button_12345")


def test_is_dynamic_value_false_for_normal_names():
    assert not is_dynamic_value("login_button")
    assert not is_dynamic_value("Login")


def test_resource_id_stability_high_for_normal_name():
    assert resource_id_stability("com.example:id/login_button") == 1.0


def test_resource_id_stability_low_for_dynamic_name():
    assert resource_id_stability("com.example:id/a3f9c21b8e77") == 0.4


def test_text_stability_high_for_normal_text():
    assert text_stability("Login") == 1.0


def test_text_stability_low_for_dynamic_text():
    assert text_stability("123456789") == 0.3


def test_text_stability_low_for_clock_text():
    assert text_stability("12:34") == 0.2
    assert text_stability("12:34:56") == 0.2


def test_index_dependency_penalty():
    assert index_dependency_penalty(True) == 0.7
    assert index_dependency_penalty(False) == 1.0


def test_hierarchy_depth_penalty_zero_depth():
    assert hierarchy_depth_penalty(0) == 1.0


def test_hierarchy_depth_penalty_decreases_with_depth():
    shallow = hierarchy_depth_penalty(2)
    deep = hierarchy_depth_penalty(10)
    assert shallow > deep


def test_hierarchy_depth_penalty_has_floor():
    assert hierarchy_depth_penalty(1000) >= 0.3
