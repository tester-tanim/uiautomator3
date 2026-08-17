import pytest

from uiautomator3.settings import Settings


def test_defaults():
    s = Settings()
    assert s["self_healing"] is False
    assert s["self_healing_min_confidence"] == 0.85


def test_set_and_get():
    s = Settings()
    s["self_healing"] = True
    assert s["self_healing"] is True


def test_unknown_key_get_raises():
    s = Settings()
    with pytest.raises(KeyError):
        s["nonexistent"]


def test_unknown_key_set_raises():
    s = Settings()
    with pytest.raises(KeyError):
        s["nonexistent"] = True


def test_type_checked_assignment():
    s = Settings()
    with pytest.raises(TypeError):
        s["self_healing"] = "yes"


def test_contains():
    s = Settings()
    assert "self_healing" in s
    assert "nonexistent" not in s


def test_get_with_default():
    s = Settings()
    assert s.get("self_healing") is False
    assert s.get("nonexistent", "fallback") == "fallback"


def test_settings_are_independent_per_instance():
    a = Settings()
    b = Settings()
    a["self_healing"] = True
    assert b["self_healing"] is False


def test_cache_ttl_defaults():
    s = Settings()
    assert s["hierarchy_cache_ttl"] == 0.3
    assert s["screenshot_cache_ttl"] == 0.3


def test_int_accepted_for_float_setting():
    s = Settings()
    s["hierarchy_cache_ttl"] = 0
    assert s["hierarchy_cache_ttl"] == 0.0
    assert isinstance(s["hierarchy_cache_ttl"], float)


def test_int_coerced_to_float_preserves_value():
    s = Settings()
    s["hierarchy_cache_ttl"] = 2
    assert s["hierarchy_cache_ttl"] == 2.0


def test_bool_rejected_for_float_setting():
    s = Settings()
    with pytest.raises(TypeError):
        s["hierarchy_cache_ttl"] = True


def test_float_accepted_for_float_setting():
    s = Settings()
    s["screenshot_cache_ttl"] = 1.5
    assert s["screenshot_cache_ttl"] == 1.5
