import tomllib
from dataclasses import FrozenInstanceError

import pytest

from timeline_kun.actions import ActionManager
from timeline_kun.actions.config import WindowKeyActionConfig, parse_action_configs
from timeline_kun.app_timer import _build_timer_config
from timeline_kun.config_toml import make_events_json


@pytest.fixture
def settings():
    return {
        "type": "window_key", "keyword": "(pose_recording)",
        "start_lead_sec": 5, "stop_delay_sec": 2,
        "window_title": "カメラ位置確認", "start_hotkey": ["F9"], "stop_hotkey": ["F10"],
    }


def test_multiple_actions_preserve_values_and_do_not_register_runtime_actions(settings, monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    settings.update(start_hotkey=["CTRL", "SHIFT", "R"], stop_hotkey=["CTRL", "SHIFT", "R"])
    settings.update(keyword=" (Pose) ", window_title=" カメラ位置確認 ", start_lead_sec=0, stop_delay_sec=0.5)
    configs = parse_action_configs({"pose": settings, "other": settings})
    manager = ActionManager(action_configs=configs)
    settings["start_hotkey"].append("F9")
    configs.clear()
    action = manager.action_configs["pose"]
    assert isinstance(action, WindowKeyActionConfig)
    assert action.keyword == " (Pose) "
    assert action.window_title == " カメラ位置確認 "
    assert action.start_hotkey == action.stop_hotkey == ("CTRL", "SHIFT", "R")
    assert action.start_lead_sec == 0
    assert action.stop_delay_sec == 0.5
    assert manager.action_configs["other"] == action
    with pytest.raises(FrozenInstanceError):
        action.keyword = "changed"
    with pytest.raises(TypeError):
        manager.action_configs["new"] = action
    with pytest.raises(KeyError):
        manager.get("pose")


@pytest.mark.parametrize("color", ["orange", "cyan", "lightgreen"])
def test_global_actions_and_legacy_settings(color, settings):
    document = {
        "ble": {name: {"ble_names": [name], "stop_delay_sec": i}
                for i, name in enumerate(["orange", "cyan", "lightgreen"])},
        "log": {"make_events_json": True},
        "excel": {"read_extra_encoding": "shift_jis"},
        "actions": {"pose": settings},
    }
    config = _build_timer_config(document, color)
    manager = ActionManager(parse_action_configs(config["actions"]))
    assert config["ble_names"] == [color]
    assert config["stop_delay_sec"] == document["ble"][color]["stop_delay_sec"]
    assert config["make_events_json"] is True
    assert config["read_extra_encoding"] == "shift_jis"
    assert manager.action_configs["pose"].window_title == "カメラ位置確認"


def test_legacy_config_without_actions():
    config = _build_timer_config({"ble": {"orange": {"ble_names": ["GoPro"]}}}, "orange")
    assert config["ble_names"] == ["GoPro"]
    assert not ActionManager(parse_action_configs(config["actions"])).action_configs
    assert not ActionManager().action_configs


@pytest.mark.parametrize("field, value", [
    ("type", "command"), ("type", None), ("window_match", "exact"),
    ("keyword", ""), ("keyword", 12), ("window_title", "  "),
    ("window_title", []), ("start_hotkey", "F9"), ("start_hotkey", []),
    ("start_hotkey", [""]), ("stop_hotkey", [False]), ("stop_hotkey", [["F9"]]),
])
def test_invalid_fields_include_path(settings, field, value):
    settings[field] = value
    with pytest.raises(ValueError, match="actions.pose"):
        parse_action_configs({"pose": settings})


@pytest.mark.parametrize("field", ["start_lead_sec", "stop_delay_sec"])
@pytest.mark.parametrize("value", [-1, True, "5", None, float("inf"), float("nan")])
def test_invalid_seconds(settings, field, value):
    settings[field] = value
    with pytest.raises(ValueError, match=f"actions.pose.{field}"):
        parse_action_configs({"pose": settings})


@pytest.mark.parametrize("field", ["type", "keyword", "start_lead_sec", "stop_delay_sec", "window_title", "start_hotkey", "stop_hotkey"])
def test_required_fields(settings, field):
    del settings[field]
    with pytest.raises(ValueError, match=f"actions.pose.{field}"):
        parse_action_configs({"pose": settings})


@pytest.mark.parametrize("actions", [None, [], "bad", {"pose": []}, {"": {}}])
def test_invalid_tables(actions):
    with pytest.raises(ValueError):
        parse_action_configs(actions)


def test_generated_config_is_disabled_and_preserves_existing_config(tmp_path):
    generated = tmp_path / "config.toml"
    make_events_json(generated)
    text = generated.read_text(encoding="utf-8")
    assert "actions.pose_streamer" in text
    assert "actions" not in tomllib.loads(text)
    example = "\n".join(line[2:] for line in text.splitlines() if line.startswith("# "))
    example = example[example.index("[actions.pose_streamer]"):]
    configs = parse_action_configs(tomllib.loads(example)["actions"])
    assert configs["pose_streamer"].start_hotkey == ("F9",)
    generated.write_text("# existing user config", encoding="utf-8")
    make_events_json(generated)
    assert generated.read_text() == "# existing user config"


def test_app_passes_parsed_global_settings_to_manager(settings, monkeypatch):
    from unittest.mock import Mock

    from timeline_kun import app_timer

    class SettingsReceived(Exception):
        pass

    received = {}

    def capture_manager(*, action_configs):
        received.update(action_configs)
        # Stop construction before creating widgets or any external action.
        raise SettingsReceived

    monkeypatch.setattr(app_timer.ttk.Frame, "__init__", lambda *args: None)
    monkeypatch.setattr(app_timer.ttk, "Style", Mock())
    monkeypatch.setattr(app_timer.sound, "AudioPlayer", Mock())
    monkeypatch.setattr(app_timer, "ActionManager", capture_manager)
    config = _build_timer_config({"actions": {"pose": settings}}, "cyan")
    with pytest.raises(SettingsReceived):
        app_timer.App(Mock(), "unused.csv", toml_dict=config)
    assert received["pose"] == parse_action_configs({"pose": settings})["pose"]
