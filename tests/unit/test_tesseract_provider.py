import builtins

import pytest

from uiautomator3.exceptions import OCRProviderError


def test_missing_pytesseract_raises_ocr_provider_error(monkeypatch):
    from uiautomator3.ocr.tesseract_provider import TesseractProvider

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("no pytesseract")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(OCRProviderError):
        TesseractProvider()


def test_detect_text_parses_pytesseract_output(monkeypatch):
    from uiautomator3.ocr.tesseract_provider import TesseractProvider

    provider = TesseractProvider.__new__(TesseractProvider)
    fake_pytesseract = type(
        "FakeModule",
        (),
        {
            "Output": type("Output", (), {"DICT": "dict"}),
            "image_to_data": staticmethod(
                lambda image, lang, output_type: {
                    "text": ["", "Login", "  ", "Cancel"],
                    "conf": ["-1", "95.5", "-1", "88.0"],
                    "left": [0, 10, 0, 200],
                    "top": [0, 20, 0, 20],
                    "width": [0, 80, 0, 60],
                    "height": [0, 30, 0, 30],
                }
            ),
        },
    )
    provider._pytesseract = fake_pytesseract
    provider._lang = "eng"

    regions = provider.detect_text(image=None)

    assert len(regions) == 2
    assert regions[0].text == "Login"
    assert regions[0].confidence == pytest.approx(0.955)
    assert regions[0].bounds.left == 10
    assert regions[0].bounds.right == 90
    assert regions[1].text == "Cancel"


def test_detect_text_wraps_errors(monkeypatch):
    from uiautomator3.ocr.tesseract_provider import TesseractProvider

    provider = TesseractProvider.__new__(TesseractProvider)

    def raise_error(*args, **kwargs):
        raise RuntimeError("tesseract not installed")

    fake_pytesseract = type(
        "FakeModule", (), {"Output": type("Output", (), {"DICT": "dict"}), "image_to_data": staticmethod(raise_error)}
    )
    provider._pytesseract = fake_pytesseract
    provider._lang = "eng"

    with pytest.raises(OCRProviderError):
        provider.detect_text(image=None)
