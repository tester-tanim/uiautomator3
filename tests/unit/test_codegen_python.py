import ast

import pytest

from uiautomator3.codegen.python_generator import _format_kwargs, generate_python
from uiautomator3.recording.session import RecordingSession


def build_session():
    session = RecordingSession()
    session.log(
        "click",
        coordinates={"x": 500, "y": 560},
        locator="Selector(text='Login')",
        selector_criteria={"text": "Login"},
        screen="com.example/.LoginActivity",
    )
    session.log("press", key="back", screen="com.example/.HomeActivity")
    session.log("swipe", coordinates={"from_x": 0, "from_y": 100, "to_x": 0, "to_y": 900})
    session.log("send_keys", text="hello world")
    session.log("app_launch", package="com.example.app", activity="MainActivity")
    session.log("app_stop", package="com.example.app")
    session.log("click", coordinates={"x": 10, "y": 20})  # no locator -> raw coords
    return session


def test_generate_python_is_valid_syntax():
    session = build_session()
    code = generate_python(session)
    ast.parse(code)  # must not raise


def test_generate_python_includes_connect():
    session = build_session()
    code = generate_python(session)
    assert "import uiautomator3 as u3" in code
    assert "d = u3.connect()" in code


def test_generate_python_with_serial():
    session = build_session()
    code = generate_python(session, connect_serial="emulator-5554")
    assert "d = u3.connect('emulator-5554')" in code


def test_locator_click_uses_selector_syntax():
    session = build_session()
    code = generate_python(session)
    assert 'd(text="Login").click()' in code


def test_coordinate_only_click_uses_raw_coordinates():
    session = build_session()
    code = generate_python(session)
    assert "d.click(10, 20)" in code


def test_press_action():
    session = build_session()
    code = generate_python(session)
    assert "d.press('back')" in code


def test_swipe_action():
    session = build_session()
    code = generate_python(session)
    assert "d.swipe(0, 100, 0, 900)" in code


def test_send_keys_action():
    session = build_session()
    code = generate_python(session)
    assert 'd.send_keys("hello world")' in code


def test_app_launch_and_stop():
    session = build_session()
    code = generate_python(session)
    assert "d.launch_app('com.example.app', 'MainActivity')" in code
    assert "d.stop_app('com.example.app')" in code


def test_empty_session_still_valid():
    session = RecordingSession()
    code = generate_python(session)
    ast.parse(code)
    assert "u3.connect()" in code


# -- security: selector_criteria keys must not be interpretable as Python
# syntax; they originate from a recording JSON file that may be
# hand-crafted or tampered with, not just genuinely recorded (see security
# review) --


def test_format_kwargs_rejects_syntax_breaking_key():
    malicious_key = 'text="x"); import os; os.system("echo PWNED") #'
    with pytest.raises(ValueError):
        _format_kwargs({malicious_key: "y"})


def test_format_kwargs_rejects_non_identifier_keys():
    for bad_key in ["has space", "has-dash", "1leading_digit", "", "trailing.dot"]:
        with pytest.raises(ValueError):
            _format_kwargs({bad_key: "value"})


def test_format_kwargs_rejects_python_keyword_as_key():
    with pytest.raises(ValueError):
        _format_kwargs({"class": "value"})  # 'class' is a reserved keyword


def test_format_kwargs_accepts_normal_identifier_keys():
    result = _format_kwargs({"text": "Login", "resourceId": "com.example:id/login"})
    assert result == 'text="Login", resourceId="com.example:id/login"'


def test_generate_python_raises_on_malicious_selector_criteria_key():
    session = RecordingSession()
    malicious_key = 'text="x"); import os; os.system("echo PWNED") #'
    session.log("click", coordinates={"x": 1, "y": 1}, selector_criteria={malicious_key: "y"})

    with pytest.raises(ValueError):
        generate_python(session)


def test_generate_pytest_raises_on_malicious_selector_criteria_key():
    from uiautomator3.codegen.pytest_generator import generate_pytest

    session = RecordingSession()
    malicious_key = 'text="x"); import os; os.system("echo PWNED") #'
    session.log("click", coordinates={"x": 1, "y": 1}, selector_criteria={malicious_key: "y"})

    with pytest.raises(ValueError):
        generate_pytest(session)


def test_generate_pom_raises_on_malicious_selector_criteria_key():
    from uiautomator3.codegen.pom_generator import generate_pom

    session = RecordingSession()
    malicious_key = 'text="x"); import os; os.system("echo PWNED") #'
    session.log(
        "click", coordinates={"x": 1, "y": 1}, selector_criteria={malicious_key: "y"}, screen="com.example/.Main"
    )

    with pytest.raises(ValueError):
        generate_pom(session)
