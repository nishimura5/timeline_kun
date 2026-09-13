from datetime import timedelta
from unittest.mock import Mock

import pytest

from timeline_kun.actions import ActionManager
from timeline_kun.actions.config import WindowKeyActionConfig
from timeline_kun.actions.timeline import ActionTimeline
from timeline_kun.actions import window_key


def config(**changes):
    values = dict(keyword="(pose)", start_lead_sec=5, stop_delay_sec=2,
                  window_title="Recorder", start_hotkey=("F9",), stop_hotkey=("F10",))
    values.update(changes)
    return WindowKeyActionConfig(**values)


def stage(start, end, instruction=""):
    return dict(start_dt=timedelta(seconds=start), end_dt=timedelta(seconds=end),
                instruction=instruction)


def setup_timeline(stages, configs=None):
    manager = ActionManager(configs or {"pose": config()})
    actions = {}
    for name in manager.action_configs:
        actions[name] = Mock()
        actions[name].start.return_value = True
        actions[name].stop.return_value = True
        manager.register(name, actions[name])
    now = [0]
    report = Mock()
    timeline = ActionTimeline(manager, stages, report, clock=lambda: now[0])
    return timeline, actions, now, report


def test_lead_contiguous_stages_delay_and_reentry():
    timeline, actions, now, _ = setup_timeline([
        stage(0, 10), stage(10, 20, "(pose)"), stage(20, 30, "(pose)"),
        stage(30, 40), stage(40, 50, "(pose)"),
    ])
    action = actions["pose"]
    timeline.update(4.99)
    action.start.assert_not_called()
    timeline.update(5)
    timeline.update(10)
    timeline.update(20)
    timeline.update(29.99)
    action.start.assert_called_once()
    timeline.update(30)
    now[0] = 1.99
    timeline.update(31.99)
    action.stop.assert_not_called()
    now[0] = 2
    timeline.update(32)
    action.stop.assert_called_once()
    timeline.update(35)
    assert action.start.call_count == 2


def test_reentry_cancels_pending_stop_and_shutdown_is_immediate():
    timeline, actions, now, _ = setup_timeline(
        [stage(0, 2, "(pose)"), stage(2, 3), stage(3, 8, "(pose)")],
        {"pose": config(start_lead_sec=0, stop_delay_sec=5)},
    )
    timeline.update(0)
    timeline.update(2)
    now[0] = 1
    timeline.update(3)
    now[0] = 10
    timeline.update(4)
    actions["pose"].start.assert_called_once()
    actions["pose"].stop.assert_not_called()
    timeline.stop_all()
    timeline.stop_all()
    actions["pose"].stop.assert_called_once()
    timeline.update(0)
    assert actions["pose"].start.call_count == 2


def test_pending_stop_is_flushed_on_reset():
    timeline, actions, now, _ = setup_timeline([stage(0, 2, "(pose)"), stage(2, 8)])
    timeline.update(0)
    timeline.update(2)
    timeline.stop_all()
    actions["pose"].stop.assert_called_once()
    now[0] = 100
    timeline.update(3)
    actions["pose"].stop.assert_called_once()


def test_actions_are_independent_and_failures_do_not_stop_other_actions():
    timeline, actions, _, report = setup_timeline(
        [stage(0, 10, "(pose)"), stage(10, 20, "(other)")],
        {"one": config(), "two": config(keyword="(other)", start_lead_sec=0)},
    )
    actions["one"].start.side_effect = RuntimeError("input error")
    timeline.update(0)
    timeline.update(1)
    actions["one"].start.assert_called_once()
    assert report.call_args.args == ("one", "start", False, "input error")
    timeline.update(10)
    actions["two"].start.assert_called_once()
    timeline.stop_all()
    actions["one"].stop.assert_not_called()
    actions["two"].stop.assert_called_once()


def test_skip_uses_timeline_time_but_delay_uses_real_time():
    timeline, actions, now, _ = setup_timeline([
        stage(0, 100), stage(100, 110, "(pose)"), stage(110, 200),
    ])
    timeline.update(0)
    timeline.update(96)
    actions["pose"].start.assert_called_once()
    timeline.update(115)
    timeline.update(190)
    actions["pose"].stop.assert_not_called()
    now[0] = 2
    timeline.update(192)
    actions["pose"].stop.assert_called_once()


def test_overlap_of_lead_windows_does_not_toggle_action():
    timeline, actions, _, _ = setup_timeline([
        stage(0, 10, "(pose)"), stage(10, 12), stage(12, 20, "(pose)"),
    ])
    for elapsed in (0, 9, 10, 11, 12, 19):
        timeline.update(elapsed)
    actions["pose"].start.assert_called_once()
    actions["pose"].stop.assert_not_called()


@pytest.mark.parametrize("operation, keys", [("start", (0x78,)), ("stop", (0x79,))])
def test_window_action_finds_focuses_then_sends(monkeypatch, operation, keys):
    lookup = Mock(return_value=123)
    backend = Mock()
    monkeypatch.setattr(window_key, "find_window", lookup)
    monkeypatch.setattr(window_key, "WindowsKeyboard", Mock(return_value=backend))
    action = window_key.WindowKeyAction(config())
    assert getattr(action, operation)()
    lookup.assert_called_once_with("Recorder")
    assert backend.mock_calls == [("focus", (123,), {}), ("send", (123, keys), {})]


@pytest.mark.parametrize("failure", ["missing", "focus", "input", "key"])
def test_window_failure_reports_reason_without_sending_to_wrong_window(monkeypatch, failure):
    monkeypatch.setattr(window_key, "find_window", Mock(return_value=None if failure == "missing" else 123))
    backend = Mock()
    monkeypatch.setattr(window_key, "WindowsKeyboard", Mock(return_value=backend))
    if failure == "focus":
        backend.focus.side_effect = OSError("Could not focus")
    if failure == "input":
        backend.send.side_effect = OSError("SendInput failed")
    action = window_key.WindowKeyAction(config(start_hotkey=("INVALID",) if failure == "key" else ("F9",)))
    assert not action.start()
    assert action.get_status() != "Idle"
    if failure != "input":
        backend.send.assert_not_called()


def test_explicit_registration_does_not_touch_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    lookup = Mock(side_effect=AssertionError("No lookup during registration"))
    monkeypatch.setattr(window_key, "find_window", lookup)
    manager = ActionManager({"pose": config()})
    manager.register_configured()
    assert isinstance(manager.get("pose"), window_key.WindowKeyAction)
    lookup.assert_not_called()


@pytest.mark.parametrize("key, value", [("CTRL", 0x11), ("shift", 0x10), ("R", 0x52),
                                       ("F9", 0x78), ("F24", 0x87), ("0", 0x30)])
def test_supported_keys(key, value):
    assert window_key.virtual_key(key) == value


@pytest.mark.skipif(__import__("sys").platform != "win32", reason="Windows ABI")
def test_send_input_layout_order_and_partial_failure_cleanup():
    import ctypes
    keyboard = window_key.WindowsKeyboard()
    assert ctypes.sizeof(keyboard.Input) == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)
    keyboard.api = Mock()
    keyboard.api.GetForegroundWindow.return_value = 123
    batches = []

    def send(count, events, size):
        batches.append([(e.ki.wVk, e.ki.dwFlags) for e in events])
        return count

    keyboard.api.SendInput.side_effect = send
    keyboard.send(123, (0x11, 0x10, 0x52))
    assert batches == [[(0x11, 0), (0x10, 0), (0x52, 0),
                        (0x52, 2), (0x10, 2), (0x11, 2)]]
    keyboard.api.SendInput.side_effect = lambda count, events, size: (send(count, events, size) and 2)
    with pytest.raises(OSError, match="SendInput failed"):
        keyboard.send(123, (0x11, 0x10, 0x52))
    assert batches[-1] == [(0x10, 2), (0x11, 2)]
    keyboard.api.GetForegroundWindow.return_value = 456
    keyboard.api.SendInput.reset_mock()
    with pytest.raises(OSError, match="lost focus"):
        keyboard.send(123, (0x78,))
    keyboard.api.SendInput.assert_not_called()


def test_action_log_records_failures(tmp_path):
    import json
    from timeline_kun.timer_log import ActionLog

    log = ActionLog(str(tmp_path / "schedule.csv"))
    log.add_log("pose", "start", False, "Window not found")
    record = json.loads((tmp_path / "log/schedule_actions.jsonl").read_text(encoding="utf-8"))
    assert record["action"] == "pose"
    assert record["success"] is False
    assert record["detail"] == "Window not found"
