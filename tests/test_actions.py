from threading import Event
from unittest.mock import Mock

import pytest

from timeline_kun.actions import ActionManager
from timeline_kun.actions.gopro import GoProAction
from timeline_kun.trigger import Trigger


@pytest.fixture
def gopro(monkeypatch):
    worker = Mock()
    monkeypatch.setattr("timeline_kun.actions.gopro.ble_control.BleThread", lambda: worker)
    return GoProAction(["camera1", "camera2"]), worker


def test_named_actions_are_independent():
    manager = ActionManager()
    first, second = Mock(), Mock()
    manager.register("first", first)
    manager.register("second", second)
    for operation in ("connect", "start", "stop", "get_status", "update_status"):
        assert getattr(manager, operation)("second") is getattr(second, operation).return_value
        getattr(first, operation).assert_not_called()
    assert manager.get("first") is first
    with pytest.raises(ValueError):
        manager.register("first", second)
    with pytest.raises(ValueError):
        manager.register("", second)
    with pytest.raises(KeyError):
        manager.start("missing")


@pytest.mark.parametrize("count, expected", [(2, "Connected"), (1, "Failed (1/2)"), (0, "Failed (0/2)")])
def test_connect(gopro, count, expected):
    action, worker = gopro
    worker.execute_command.return_value = ("connect", count, "result")
    assert action.connect() is (count == 2)
    worker.set_target_device_names.assert_called_with(["camera1", "camera2"])
    worker.start.assert_called_once_with()
    worker.execute_command.assert_called_once_with("connect", None, timeout=30)
    assert action.get_status() == expected


@pytest.mark.parametrize("operation, command, timeout, count, status", [
    ("start", "record_start", 3, 1, "Recording"),
    ("start", "record_start", 3, 0, "Failed to start"),
    ("stop", "record_stop", 5, 1, "Connected"),
    ("stop", "record_stop", 5, 0, "Failed to stop"),
])
def test_recording_results(gopro, operation, command, timeout, count, status):
    action, worker = gopro
    worker.execute_command.return_value = (command, count, "result")
    assert getattr(action, operation)() is bool(count)
    worker.execute_command.assert_called_once_with(command, None, timeout=timeout)
    assert action.get_status() == status


@pytest.mark.parametrize("result, expected", [
    (("status", 2, "2/2 recording"), "Recording..."),
    (("status", 2, "2/2 idle"), "Connected"),
    (("status", 1, "1/2 idle"), "KeepAlive Failed (1/2)"),
    (("status", 0, "0/2 idle"), "Disconnected"),
    (("status", 0, "0/0 idle"), "Idle"),
    (("status", 0, "thread not running"), "Idle"),
    (("status", 0, "timeout"), "Idle"),
    (("connect", 2, "success"), "Idle"),
])
def test_status(gopro, result, expected):
    action, worker = gopro
    worker.execute_command.return_value = result
    assert action.update_status() == expected
    worker.execute_command.assert_called_once_with("status", None, timeout=3)


def test_recording_trigger_delegates_through_manager(gopro, monkeypatch):
    action, worker = gopro
    worker.execute_command.side_effect = [
        ("record_start", 2, "success"), ("record_stop", 2, "success")
    ]
    manager = ActionManager()
    manager.register("camera", action)
    trigger = Trigger(manager, "camera", "(recording)", delay_sec=2.5)
    waiting, release, stopped = Event(), Event(), Event()

    def wait(delay):
        assert delay == 2.5
        waiting.set()
        assert release.wait(2)

    original_stop = manager.stop

    def stop(name):
        original_stop(name)
        stopped.set()

    monkeypatch.setattr("timeline_kun.trigger.time.sleep", wait)
    monkeypatch.setattr(manager, "stop", stop)
    assert not trigger.trigger_in("ordinary stage")
    assert trigger.trigger_in("task (recording)")
    assert trigger.get_triggered()
    assert not trigger.trigger_in("next (recording)")
    assert not trigger.trigger_out("next (recording)")
    try:
        assert trigger.trigger_out("End")
        assert waiting.wait(2)
        assert not trigger.get_triggered()
        assert not trigger.trigger_out("")
        assert action.get_status() == "Recording"
    finally:
        release.set()
    assert stopped.wait(2)
    assert action.get_status() == "Connected"
    assert worker.execute_command.call_count == 2


def test_trigger_accepts_non_device_action_and_preserves_failed_start_state():
    manager = ActionManager()
    action = Mock()
    action.start.return_value = False
    manager.register("custom", action)
    trigger = Trigger(manager, "custom", "(custom)")
    assert not trigger.trigger_in("(custom)")
    assert trigger.get_triggered()
    assert not trigger.trigger_in("(custom)")
    action.start.assert_called_once_with()


@pytest.mark.parametrize("names, fails", [([], False), (["camera1"], False), (["camera1"], True)])
def test_ble_ui_uses_registered_action(gopro, monkeypatch, names, fails):
    from timeline_kun import gui_ble_button

    action, worker = gopro
    registry = ActionManager()
    registry.register("gopro", action)
    for widget in ("Frame", "Button", "Label"):
        monkeypatch.setattr(gui_ble_button.ttk, widget, Mock())
    # Run the background callback synchronously while retaining the after() boundary.
    monkeypatch.setattr(
        gui_ble_button.threading, "Thread",
        lambda target, daemon: Mock(start=target),
    )
    window = Mock()
    ui = gui_ble_button.BleButtonManager(Mock(), window, action, names)
    if not names:
        assert registry.get_status("gopro") == "No devices configured"
        ui.ble_btn.config.assert_called_with(state="disabled")
        return

    assert registry.get_status("gopro") == "camera1"
    if fails:
        worker.execute_command.side_effect = RuntimeError("connection failed")
    else:
        worker.execute_command.return_value = ("connect", 1, "success")
    ui.connect_ble()
    ui.ble_btn.config.assert_called_with(state="disabled")
    callback = window.after.call_args.args[1]
    callback()
    ui.ble_btn.config.assert_called_with(state="normal")
    assert registry.get_status("gopro") == ("Connection Error" if fails else "Connected")
    if not fails:
        worker.execute_command.return_value = ("status", 1, "1/1 recording")
        ui.update_ble_status()
        ui.ble_status_label.config.assert_called_with(text="Recording...")
