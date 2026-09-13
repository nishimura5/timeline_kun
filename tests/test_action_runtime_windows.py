"""Opt-in real Windows test: TIMELINE_KUN_GUI_TEST=1 python -m pytest ..."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import Mock
from uuid import uuid4

import pytest


@pytest.mark.skipif(sys.platform != "win32" or os.environ.get("TIMELINE_KUN_GUI_TEST") != "1",
                    reason="Requires an interactive Windows desktop and explicit opt-in")
def test_timer_drives_real_window_without_ble(tmp_path, monkeypatch):
    import tkinter as tk
    from timeline_kun import app_timer

    title = "timeline_kun automated test " + uuid4().hex
    state_path = tmp_path / "window.json"
    target_path = tmp_path / "target.py"
    target_path.write_text("""
import json
from pathlib import Path
import sys
import tkinter as tk
root = tk.Tk()
root.title(sys.argv[1])
state = "Idle"
def write():
    Path(sys.argv[2]).write_text(json.dumps(dict(state=state, focused=root.focus_get() is not None)))
def change(value):
    global state
    state = value
    write()
root.bind("<F9>", lambda e: change("Recording"))
root.bind("<F10>", lambda e: change("Stopped"))
root.bind("<FocusIn>", lambda e: root.after_idle(write))
root.bind("<FocusOut>", lambda e: root.after_idle(write))
root.after(50, write)
root.mainloop()
""", encoding="utf-8")
    target = subprocess.Popen([sys.executable, str(target_path), title, str(state_path)],
                              creationflags=subprocess.CREATE_NO_WINDOW)
    root = None
    try:
        deadline = time.monotonic() + 5
        while not state_path.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert state_path.exists(), "Test window did not start"
        csv = tmp_path / "schedule.csv"
        csv.write_text(
            "title,member,start,duration,fixed,instruction\n"
            "Wait,,,0:00:02,duration,\n"
            "Record,,,0:00:01,duration,(pose)\n"
            "Tail,,,0:00:02,duration,\n", encoding="utf-8")
        monkeypatch.setattr(app_timer.sound, "AudioPlayer", Mock())
        root = tk.Tk()
        root.geometry("900x420+40+40")
        app = app_timer.App(root, str(csv), toml_dict={"actions": {"pose": {
            "type": "window_key", "keyword": "(pose)",
            "start_lead_sec": 0.5, "stop_delay_sec": 0.2,
            "window_title": title, "start_hotkey": ["F9"], "stop_hotkey": ["F10"],
        }}})
        assert not app.enable_ble
        root.update()
        def pump(seconds):
            until = time.monotonic() + seconds
            while time.monotonic() < until:
                root.update()
                time.sleep(0.01)

        def read():
            return json.loads(state_path.read_text())

        def click_start():
            # Supply real input to the test Timer, as a user clicking Start would.
            # This grants the timer foreground rights without forcing other apps.
            from timeline_kun.actions.window_key import WindowsKeyboard
            keyboard = WindowsKeyboard()
            root.attributes("-topmost", True)
            pump(0.1)
            x = app.start_btn.winfo_rootx() + app.start_btn.winfo_width() // 2
            y = app.start_btn.winfo_rooty() + app.start_btn.winfo_height() // 2
            api = keyboard.api
            events = (keyboard.Input * 3)()
            events[0].mi.dx = round((x - api.GetSystemMetrics(76)) * 65535 / (api.GetSystemMetrics(78) - 1))
            events[0].mi.dy = round((y - api.GetSystemMetrics(77)) * 65535 / (api.GetSystemMetrics(79) - 1))
            events[0].mi.dwFlags = 0xC001  # MOVE | ABSOLUTE | VIRTUALDESK
            events[1].mi.dwFlags = 2  # LEFTDOWN
            events[2].mi.dwFlags = 4  # LEFTUP
            assert api.SendInput(1, events, keyboard.ctypes.sizeof(keyboard.Input)) == 1
            pump(0.05)
            clicks = (keyboard.Input * 2)(events[1], events[2])
            assert api.SendInput(2, clicks, keyboard.ctypes.sizeof(keyboard.Input)) == 2
            pump(0.1)
            root.attributes("-topmost", False)
            assert app.is_running

        click_start()

        pump(1.8)
        assert read() == {"state": "Recording", "focused": True}
        pump(1.7)
        assert read()["state"] == "Stopped"
        pump(1.8)
        assert not app.is_running
        results = [json.loads(line) for line in Path(app.action_log.file_path).read_text().splitlines()]
        assert [(r["operation"], r["success"]) for r in results] == [("start", True), ("stop", True)]

        # Reset during a recording must send the stop key immediately.
        app.reset_all()
        root.focus_force()
        root.update()
        app.start()
        pump(1.8)
        assert read()["state"] == "Recording"
        app.reset_all()
        pump(0.1)
        assert read()["state"] == "Stopped"

        # Starting inside a matching first stage and closing stops immediately.
        from timeline_kun.actions.timeline import ActionTimeline
        from datetime import timedelta
        app.action_timeline = ActionTimeline(app.action_manager, [{
            "start_dt": timedelta(), "end_dt": timedelta(seconds=20),
            "instruction": "(pose)",
        }], report=app.action_log.add_log)
        root.focus_force()
        root.update()
        app.start()
        pump(0.1)
        assert read()["state"] == "Recording"
        pump(5.2)
        assert not app.is_running
        assert read()["state"] == "Stopped"
        app.reset_all()
        root.focus_force()
        root.update()
        app.start()
        pump(0.1)
        assert read()["state"] == "Recording"
        app._on_closing()
        root = None
        time.sleep(0.1)
        assert read()["state"] == "Stopped"
    finally:
        if root is not None:
            root.destroy()
        target.terminate()
        target.wait(timeout=5)
