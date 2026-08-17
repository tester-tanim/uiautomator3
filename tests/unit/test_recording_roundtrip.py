import json

from uiautomator3.elements.uielement import Bounds, UIElement
from uiautomator3.recording.action import RecordedAction
from uiautomator3.recording.session import RecordingSession


def make_element(text="Login"):
    return UIElement(
        id="e0",
        text=text,
        content_description=None,
        resource_id="com.example:id/login",
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


def test_action_round_trips_through_dict():
    original = RecordedAction(
        action="click",
        timestamp=123.0,
        coordinates={"x": 1, "y": 2},
        locator="Selector(text='Login')",
        selector_criteria={"text": "Login"},
        element_text="Login",
        element_resource_id="com.example:id/login",
        element_class_name="android.widget.Button",
        screen="com.example/.Main",
        confidence=0.9,
        extra={"duration": 1.5},
    )

    restored = RecordedAction.from_dict(original.as_dict())

    assert restored.action == "click"
    assert restored.coordinates == {"x": 1, "y": 2}
    assert restored.selector_criteria == {"text": "Login"}
    assert restored.element_text == "Login"
    assert restored.element_resource_id == "com.example:id/login"
    assert restored.screen == "com.example/.Main"
    assert restored.confidence == 0.9
    assert restored.extra == {"duration": 1.5}


def test_session_round_trips_through_json():
    session = RecordingSession()
    session.log(
        "click",
        coordinates={"x": 10, "y": 20},
        element=make_element(),
        locator="Selector(text='Login')",
        selector_criteria={"text": "Login"},
        screen="com.example/.Main",
    )
    session.log("press", key="back")

    json_text = json.dumps(session.as_list())
    restored = RecordingSession.from_list(json.loads(json_text))

    assert len(restored.actions) == 2
    assert restored.actions[0].action == "click"
    assert restored.actions[0].selector_criteria == {"text": "Login"}
    assert restored.actions[1].extra["key"] == "back"


def test_from_list_empty():
    restored = RecordingSession.from_list([])
    assert restored.actions == []
