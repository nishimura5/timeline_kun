import ctypes
from unittest.mock import Mock

import pytest

from timeline_kun import app_previewer
from timeline_kun.actions import window


def test_previewer_starts_unchecked_and_retains_actions(monkeypatch):
    class StopBeforeWidgets(Exception):
        pass

    monkeypatch.setattr(app_previewer.ttk.Frame, "__init__", lambda *args: None)
    monkeypatch.setattr(app_previewer.tk, "Menu", Mock(side_effect=StopBeforeWidgets))
    app = app_previewer.App.__new__(app_previewer.App)
    actions = {"pose": {"type": "window_key"}}
    with pytest.raises(StopBeforeWidgets):
        app.__init__(Mock(), toml_dict={"actions": actions})
    assert app.window_check_performed is False
    assert app.actions_config == actions


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(app_previewer.sys, "platform", "win32")
    app = app_previewer.App.__new__(app_previewer.App)
    app.actions_config = {
        name: {
            "type": "window_key", "keyword": "(recording)",
            "start_lead_sec": 0, "stop_delay_sec": 0,
            "window_title": title, "start_hotkey": ["F9"], "stop_hotkey": ["F10"],
        }
        for name, title in [("one", "カメラ位置確認"), ("two", "Recorder")]
    }
    app.window_check_performed = False
    monkeypatch.setattr(app_previewer, "messagebox", Mock())
    return app


@pytest.mark.parametrize("handles", [(1, 2), (1, None), (None, None)])
def test_check_reports_each_action_without_csv(app, monkeypatch, handles):
    lookup = Mock(side_effect=handles)
    monkeypatch.setattr(app_previewer, "find_window", lookup)
    app.actions_config["other"] = {"type": "http"}
    app.check_windows()
    assert app.window_check_performed
    assert [call.args[0] for call in lookup.call_args_list] == ["カメラ位置確認", "Recorder"]
    dialogs = app_previewer.messagebox
    report = dialogs.showinfo if all(handles) else dialogs.showwarning
    text = report.call_args.args[1]
    for name, title, handle in zip(["one", "two"], ["カメラ位置確認", "Recorder"], handles):
        assert f"{name} | {title!r} | {'Found' if handle else 'Not found'}" in text
    if all(handles):
        assert "All target windows found" in text


@pytest.mark.parametrize("actions", [{}, {"other": {"type": "http"}}])
def test_no_window_actions(app, monkeypatch, actions):
    app.actions_config = actions
    lookup = Mock()
    monkeypatch.setattr(app_previewer, "find_window", lookup)
    app.check_windows()
    lookup.assert_not_called()
    assert app.window_check_performed
    assert "No window_key actions" in app_previewer.messagebox.showinfo.call_args.args[1]


def test_unavailable_check_is_reported(app, monkeypatch):
    monkeypatch.setattr(app_previewer, "find_window", Mock(side_effect=OSError("Unavailable")))
    app.check_windows()
    assert app.window_check_performed
    assert "Unavailable" in app_previewer.messagebox.showerror.call_args.args[1]


@pytest.mark.parametrize("checked, proceed", [(False, False), (False, True), (True, False)])
def test_timer_warning_and_launch(app, monkeypatch, checked, proceed):
    app.window_check_performed = checked
    app.stage_list = [{"has_error": False}]
    app.time_format_combobox = Mock(get=Mock(return_value="h:mm:ss"))
    app.timer_color_combobox = Mock(get=Mock(return_value="cyan"))
    app.csv_path = "schedule.csv"
    app.start_index = 2
    app_previewer.messagebox.askyesno.return_value = proceed
    monkeypatch.setattr(app_previewer.sys, "frozen", False, raising=False)
    monkeypatch.setattr(app_previewer.importlib.util, "find_spec", Mock(return_value=object()))
    launch = Mock()
    monkeypatch.setattr(app_previewer.subprocess, "Popen", launch)
    app.open_timer()
    assert app_previewer.messagebox.askyesno.call_count == (0 if checked else 1)
    if checked or proceed:
        launch.assert_called_once_with([
            app_previewer.sys.executable, "-m", "timeline_kun.app_timer",
            "--file_path", "schedule.csv", "--fg_color", "cyan",
            "--start_index", "2", "--hmmss", "hmmss",
        ])
    else:
        launch.assert_not_called()


@pytest.mark.parametrize("target, expected", [
    ("カメラ位置確認", 2), ("Recorder", 4), ("recorder", None),
    (" Recorder ", None), ("カメラ", None),
])
def test_lookup_matches_exact_title(monkeypatch, target, expected):
    # Fake only the read APIs; activation/input calls would fail this test.
    titles = {1: "カメラ位置確認 - extra", 2: "カメラ位置確認", 3: "RECORDER", 4: "Recorder"}

    def enum_windows(callback, param):
        for hwnd in titles:
            if not callback(hwnd, param):
                return False
        return True

    def get_text(hwnd, buffer, size):
        buffer.value = titles[hwnd]
        return len(buffer.value)

    api = Mock(spec=["EnumWindows", "GetWindowTextLengthW", "GetWindowTextW"])
    api.EnumWindows.side_effect = enum_windows
    api.GetWindowTextLengthW.side_effect = lambda hwnd: len(titles[hwnd])
    api.GetWindowTextW.side_effect = get_text
    monkeypatch.setattr(window.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "WinDLL", Mock(return_value=api), raising=False)
    monkeypatch.setattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE, raising=False)
    assert window.find_window(target) == expected


@pytest.mark.parametrize("platform", ["darwin", "linux"])
def test_non_windows_lookup_is_explicit(monkeypatch, platform):
    monkeypatch.setattr(window.sys, "platform", platform)
    with pytest.raises(OSError, match="supported on Windows only"):
        window.find_window("Recorder")


@pytest.mark.parametrize("platform", ["darwin", "linux"])
def test_non_windows_check_skips_lookup_and_allows_timer(app, monkeypatch, platform):
    monkeypatch.setattr(app_previewer.sys, "platform", platform)
    lookup = Mock(side_effect=AssertionError("Must not search windows"))
    monkeypatch.setattr(app_previewer, "find_window", lookup)
    app.check_windows()
    lookup.assert_not_called()
    app_previewer.messagebox.showinfo.assert_called_once_with(
        "Check Windows", "WindowKey actions are supported on Windows only."
    )
    assert app.window_check_performed
    app.stage_list = [{"has_error": False}]
    app.time_format_combobox = Mock(get=Mock(return_value="mm:ss"))
    app.timer_color_combobox = Mock(get=Mock(return_value="orange"))
    app.csv_path = "schedule.csv"
    app.start_index = 0
    monkeypatch.setattr(app_previewer.sys, "frozen", False, raising=False)
    monkeypatch.setattr(app_previewer.importlib.util, "find_spec", Mock(return_value=object()))
    launch = Mock()
    monkeypatch.setattr(app_previewer.subprocess, "Popen", launch)
    app.open_timer()
    app_previewer.messagebox.askyesno.assert_not_called()
    launch.assert_called_once()


@pytest.mark.parametrize("platform", ["darwin", "linux"])
def test_non_windows_action_requests_fail_without_execution(app, monkeypatch, platform):
    from timeline_kun.actions import ActionManager
    from timeline_kun.actions.config import parse_action_configs

    monkeypatch.setattr(window.sys, "platform", platform)
    manager = ActionManager(parse_action_configs(app.actions_config))
    runtime = Mock()
    manager.register("one", runtime)
    for operation in (manager.connect, manager.start, manager.stop):
        assert operation("one") is False
        assert operation("two") is False
    assert manager.get_status("one") == window.WINDOWS_ONLY_MESSAGE
    assert manager.update_status("two") == window.WINDOWS_ONLY_MESSAGE
    assert not runtime.mock_calls
    manager.register("gopro", runtime)
    manager.start("gopro")
    runtime.start.assert_called_once()
    with pytest.raises(KeyError):
        manager.start("unknown")
