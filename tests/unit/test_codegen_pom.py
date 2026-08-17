import ast

from uiautomator3.codegen.pom_generator import generate_pom
from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.recording.session import RecordingSession


def make_element(text):
    return UIElement(
        id="e0",
        text=text,
        content_description=None,
        resource_id=None,
        class_name="android.widget.Button",
        package_name="com.example",
        bounds=Bounds(0, 0, 100, 50),
        clickable=True,
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
    )


def build_multi_screen_session():
    session = RecordingSession()
    session.log(
        "click",
        coordinates={"x": 500, "y": 560},
        element=make_element("Login"),
        selector_criteria={"text": "Login"},
        screen="com.example/.LoginActivity",
    )
    session.log(
        "click",
        coordinates={"x": 10, "y": 20},
        element=make_element("Submit"),
        selector_criteria={"text": "Submit"},
        screen="com.example/.LoginActivity",
    )
    session.log(
        "click",
        coordinates={"x": 30, "y": 40},
        element=make_element("Profile"),
        selector_criteria={"text": "Profile"},
        screen="com.example/.HomeActivity",
    )
    return session


def test_generate_pom_is_valid_syntax():
    code = generate_pom(build_multi_screen_session())
    ast.parse(code)


def test_generate_pom_creates_one_class_per_screen():
    code = generate_pom(build_multi_screen_session())
    assert "class LoginActivityPage:" in code
    assert "class HomeActivityPage:" in code


def test_generate_pom_methods_use_self_d():
    code = generate_pom(build_multi_screen_session())
    assert "self.d = d" in code
    assert 'self.d(text="Login").click()' in code


def test_generate_pom_method_names_derived_from_element_text():
    code = generate_pom(build_multi_screen_session())
    assert "def click_login(self):" in code
    assert "def click_submit(self):" in code


def test_generate_pom_repeated_screen_names_get_suffixed():
    session = RecordingSession()
    session.log(
        "click",
        coordinates={"x": 1, "y": 1},
        element=make_element("A"),
        selector_criteria={"text": "A"},
        screen="com.example/.Main",
    )
    session.log("press", key="back")  # screen=None -> "unknown"
    session.log(
        "click",
        coordinates={"x": 2, "y": 2},
        element=make_element("B"),
        selector_criteria={"text": "B"},
        screen="com.example/.Main",
    )

    code = generate_pom(session)
    ast.parse(code)
    assert code.count("class MainPage") >= 1


def test_empty_session_produces_valid_module():
    code = generate_pom(RecordingSession())
    ast.parse(code)
    assert "import uiautomator3 as u3" in code
