import json

from uiautomator3.codegen.structured_generator import generate_json, generate_yaml
from uiautomator3.recording.session import RecordingSession


def build_session():
    session = RecordingSession()
    session.log(
        "click",
        coordinates={"x": 500, "y": 560},
        selector_criteria={"text": "Login"},
        screen="com.example/.LoginActivity",
    )
    session.log("press", key="back")
    return session


def test_generate_json_is_valid_json():
    output = generate_json(build_session())
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["action"] == "click"
    assert data[0]["coordinates"] == {"x": 500, "y": 560}


def test_generate_json_matches_session_as_list():
    session = build_session()
    output = generate_json(session)
    assert json.loads(output) == session.as_list()


def test_generate_json_empty_session():
    output = generate_json(RecordingSession())
    assert json.loads(output) == []


def test_generate_yaml_contains_actions_key():
    output = generate_yaml(build_session())
    assert output.startswith("actions:")


def test_generate_yaml_contains_action_values():
    output = generate_yaml(build_session())
    assert "action: click" in output
    assert "action: press" in output


def test_generate_yaml_quotes_special_characters():
    session = RecordingSession()
    session.log("send_keys", text="a: b")
    output = generate_yaml(session)
    assert '"a: b"' in output


def test_generate_yaml_empty_session():
    output = generate_yaml(RecordingSession())
    assert "actions:" in output
    assert "[]" in output
