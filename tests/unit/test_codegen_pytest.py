import ast

from uiautomator3.codegen.pytest_generator import generate_pytest
from uiautomator3.recording.session import RecordingSession


def build_session():
    session = RecordingSession()
    session.log(
        "click",
        coordinates={"x": 500, "y": 560},
        selector_criteria={"text": "Login"},
        screen="com.example/.LoginActivity",
    )
    session.log("press", key="home")
    return session


def test_generate_pytest_is_valid_syntax():
    code = generate_pytest(build_session())
    ast.parse(code)


def test_generate_pytest_has_fixture_and_test_function():
    code = generate_pytest(build_session())
    assert "@pytest.fixture" in code
    assert "def d():" in code
    assert "def test_recorded_flow(d):" in code


def test_generate_pytest_custom_test_name():
    code = generate_pytest(build_session(), test_name="test_login_flow")
    assert "def test_login_flow(d):" in code


def test_generate_pytest_uses_d_fixture_not_bare_d():
    code = generate_pytest(build_session())
    assert "d(text=\"Login\").click()" in code
    assert "d = u3.connect()" not in code  # connection lives in the fixture


def test_empty_session_generates_pass():
    code = generate_pytest(RecordingSession())
    ast.parse(code)
    assert "pass" in code
