import pytest
from PIL import Image, ImageDraw

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from uiautomator3.vision.template_provider import TemplateMatchProvider


def _draw_marker(img, origin):
    """Draw a template with internal structure (not a flat color) so
    normalized cross-correlation has a well-defined, non-degenerate peak -
    a solid-color square matches any solid-color region equally, which is
    not representative of real UI icons/buttons."""
    draw = ImageDraw.Draw(img)
    ox, oy = origin
    draw.rectangle((ox, oy, ox + 99, oy + 69), fill=(255, 0, 0))
    draw.ellipse((ox + 20, oy + 15, ox + 50, oy + 45), fill=(0, 255, 0))
    draw.rectangle((ox + 60, oy + 10, ox + 90, oy + 30), fill=(0, 0, 255))
    return img


def make_screenshot_with_marker(size=(400, 400), origin=(150, 150)):
    img = Image.new("RGB", size, color=(30, 30, 30))
    return _draw_marker(img, origin)


def make_marker_template():
    img = Image.new("RGB", (100, 70), color=(30, 30, 30))
    return _draw_marker(img, (0, 0))


def test_find_locates_template_within_screenshot():
    screenshot = make_screenshot_with_marker(origin=(150, 150))
    template = make_marker_template()

    provider = TemplateMatchProvider(scales=(1.0, 1.0, 1))
    match = provider.find(screenshot, template)

    assert match is not None
    assert match.similarity > 0.9
    # matched box center should be close to the true marker center (200, 185)
    assert abs(match.point.x - 200) < 15
    assert abs(match.point.y - 185) < 15


def test_find_returns_low_similarity_when_template_absent():
    screenshot = Image.new("RGB", (400, 400), color=(30, 30, 30))
    template = make_marker_template()

    provider = TemplateMatchProvider(scales=(1.0, 1.0, 1))
    match = provider.find(screenshot, template)

    assert match is not None
    assert match.similarity < 0.5


def test_find_returns_none_when_template_larger_than_screenshot():
    screenshot = Image.new("RGB", (50, 50), color=(30, 30, 30))
    template = Image.new("RGB", (200, 200), color=(255, 0, 0))

    provider = TemplateMatchProvider(scales=(1.0, 1.0, 1))
    match = provider.find(screenshot, template)

    assert match is None


def test_missing_cv2_raises_vision_provider_error(monkeypatch):
    import builtins

    from uiautomator3.exceptions import VisionProviderError

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "cv2":
            raise ImportError("no cv2")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(VisionProviderError):
        TemplateMatchProvider()
