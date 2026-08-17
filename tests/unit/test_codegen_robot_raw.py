from uiautomator3.codegen.raw_generator import generate_raw
from uiautomator3.codegen.robot_generator import generate_robot
from uiautomator3.recording.session import RecordingSession


def build_session():
    session = RecordingSession()
    session.log(
        "click",
        coordinates={"x": 500, "y": 560},
        selector_criteria={"text": "Login"},
    )
    session.log("press", key="back")
    session.log("swipe", coordinates={"from_x": 0, "from_y": 0, "to_x": 0, "to_y": 500})
    session.log("click", coordinates={"x": 10, "y": 20})  # no selector
    return session


# -- Robot Framework generator --


def test_generate_robot_has_settings_and_test_case_sections():
    code = generate_robot(build_session())
    assert "*** Settings ***" in code
    assert "*** Test Cases ***" in code
    assert "Library    UIAutomator3" in code


def test_generate_robot_custom_test_name():
    code = generate_robot(build_session(), test_name="Login Flow")
    assert "Login Flow" in code


def test_generate_robot_click_with_locator():
    code = generate_robot(build_session())
    assert "Click    text=Login" in code


def test_generate_robot_click_without_locator_uses_coordinates():
    code = generate_robot(build_session())
    assert "Click Coordinates    10    20" in code


def test_generate_robot_press_and_swipe():
    code = generate_robot(build_session())
    assert "Press Key    back" in code
    assert "Swipe    0    0    0    500" in code


def test_generate_robot_empty_session():
    code = generate_robot(RecordingSession())
    assert "No Operation" in code


# -- Raw action script generator --


def test_generate_raw_one_line_per_action():
    output = generate_raw(build_session())
    lines = output.strip().splitlines()
    assert len(lines) == 4


def test_generate_raw_uses_selector_criteria_when_present():
    output = generate_raw(build_session())
    assert "CLICK text=Login" in output


def test_generate_raw_uses_coordinates_when_no_selector():
    output = generate_raw(build_session())
    assert "CLICK x=10 y=20" in output


def test_generate_raw_includes_extra_fields():
    output = generate_raw(build_session())
    assert "PRESS key=back" in output


def test_generate_raw_empty_session():
    assert generate_raw(RecordingSession()) == ""


# -- security: a newline embedded in a key/value must not inject an extra
# line into either line-oriented format (see security review) --


def test_generate_raw_strips_embedded_newlines_from_values():
    session = RecordingSession()
    session.log("click", coordinates={"x": 1, "y": 1}, selector_criteria={"text": "a\nFAKE_LINE b"})

    output = generate_raw(session)

    # a single action must still produce a single line (plus the trailing
    # newline generate_raw always appends) - not an extra injected line
    assert output.count("\n") == 1
    assert "FAKE_LINE" in output  # content preserved, just not as a new line


def test_generate_raw_strips_embedded_newlines_from_keys():
    session = RecordingSession()
    session.log("click", coordinates={"x": 1, "y": 1}, selector_criteria={"text\nFAKE_LINE": "value"})

    output = generate_raw(session)

    assert output.count("\n") == 1


def test_generate_robot_strips_embedded_newlines():
    session = RecordingSession()
    session.log("click", coordinates={"x": 1, "y": 1}, selector_criteria={"text": "a\nFAKE KEYWORD"})

    code = generate_robot(session)

    # the injected content must not appear on its own Robot Framework line
    for line in code.splitlines():
        assert line.strip() != "FAKE KEYWORD"
