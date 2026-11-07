import tomllib
from unittest.mock import Mock

import pytest

from timeline_kun.action_settings import ActionSettingsDialog, parse_hotkey, save_actions


def settings():
    return dict(type="window_key", keyword="(recording)", start_lead_sec=5,
                stop_delay_sec=2, window_title='Camera "one"',
                start_hotkey=["F9"], stop_hotkey=["F10"])


def test_save_preserves_other_settings_and_replaces_actions(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('# Keep this comment\nflush = false\n[ble.orange]\nble_names = ["camera"]\n', encoding="utf-8")
    save_actions(path, {"pose": settings()})
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    assert document["actions"] == {"pose": settings()}
    assert document["ble"]["orange"]["ble_names"] == ["camera"]
    assert document["flush"] is False
    assert "# Keep this comment" in path.read_text(encoding="utf-8")
    save_actions(path, {})
    assert tomllib.loads(path.read_text(encoding="utf-8"))["actions"] == {}


def test_invalid_action_does_not_change_file(tmp_path):
    path = tmp_path / "config.toml"
    original = "flush = false\n"
    path.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError):
        save_actions(path, {"pose": {**settings(), "keyword": ""}})
    assert path.read_text(encoding="utf-8") == original


def test_hotkey_input():
    assert parse_hotkey(" Ctrl + Shift + r ") == ["CTRL", "SHIFT", "R"]
    for invalid in ("", "Ctrl+", "F25", "unknown"):
        with pytest.raises(ValueError):
            parse_hotkey(invalid)


def test_editor_saves_and_reloads_values(tmp_path):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk display is unavailable")
    root.withdraw()
    try:
        path = tmp_path / "config.toml"
        path.write_text("flush = false\n", encoding="utf-8")
        saved = Mock()
        dialog = ActionSettingsDialog(root, path, saved)
        _, variables = dialog.editors["action_1"]
        assert variables["start_hotkey"].get() == "F9"
        assert variables["stop_hotkey"].get() == "F10"
        variables["keyword"].set("(recording)")
        variables["window_title"].set("Camera")
        variables["start_lead_sec"].set(3)
        variables["stop_delay_sec"].set(5)
        variables["start_hotkey"].set("Ctrl+R")
        dialog.save()
        saved.assert_called_once()
        expected = saved.call_args.args[0]
        assert tomllib.loads(path.read_text(encoding="utf-8"))["actions"] == expected
        reopened = ActionSettingsDialog(root, path, Mock())
        _, variables = reopened.editors["action_1"]
        assert variables["start_hotkey"].get() == "CTRL+R"
        assert variables["start_lead_sec"].get() == 3
        assert variables["stop_delay_sec"].get() == 5
        reopened.destroy()
    finally:
        root.destroy()
