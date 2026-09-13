"""Windows foreground activation and keyboard input for configured actions."""

import sys
import time

from .window import WINDOWS_ONLY_MESSAGE, find_window


def virtual_key(name):
    keys = {
        "CTRL": 0x11, "CONTROL": 0x11, "SHIFT": 0x10, "ALT": 0x12,
        "WIN": 0x5B, "ENTER": 0x0D, "RETURN": 0x0D, "TAB": 0x09,
        "ESC": 0x1B, "ESCAPE": 0x1B, "SPACE": 0x20, "BACKSPACE": 0x08,
        "DELETE": 0x2E, "INSERT": 0x2D, "HOME": 0x24, "END": 0x23,
        "PAGEUP": 0x21, "PAGEDOWN": 0x22, "LEFT": 0x25, "UP": 0x26,
        "RIGHT": 0x27, "DOWN": 0x28,
    }
    key = name.upper()
    if key in keys:
        return keys[key]
    if len(key) == 1 and ("A" <= key <= "Z" or "0" <= key <= "9"):
        return ord(key)
    if key.startswith("F") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        return 0x70 + int(key[1:]) - 1
    raise ValueError(f"Unsupported hotkey: {name!r}")


class WindowsKeyboard:
    def __init__(self):
        if sys.platform != "win32":
            raise OSError(WINDOWS_ONLY_MESSAGE)
        import ctypes
        from ctypes import wintypes as w

        class KeyboardInput(ctypes.Structure):
            _fields_ = [("wVk", w.WORD), ("wScan", w.WORD),
                        ("dwFlags", w.DWORD), ("time", w.DWORD),
                        ("dwExtraInfo", ctypes.c_size_t)]

        class MouseInput(ctypes.Structure):
            _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD),
                        ("dwFlags", w.DWORD), ("time", w.DWORD),
                        ("dwExtraInfo", ctypes.c_size_t)]

        class InputUnion(ctypes.Union):
            _fields_ = [("ki", KeyboardInput), ("mi", MouseInput)]

        class Input(ctypes.Structure):
            _anonymous_ = ("data",)
            _fields_ = [("type", w.DWORD), ("data", InputUnion)]

        self.ctypes, self.Input, self.KeyboardInput = ctypes, Input, KeyboardInput
        self.api = ctypes.WinDLL("user32", use_last_error=True)
        signatures = {
            "IsIconic": ([w.HWND], w.BOOL),
            "ShowWindowAsync": ([w.HWND, ctypes.c_int], w.BOOL),
            "SetForegroundWindow": ([w.HWND], w.BOOL),
            "GetForegroundWindow": ([], w.HWND),
            "SendInput": ([w.UINT, ctypes.POINTER(Input), ctypes.c_int], w.UINT),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result

    def focus(self, hwnd):
        if self.api.IsIconic(hwnd):
            self.api.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
        self.api.SetForegroundWindow(hwnd)
        # Activation in another process is asynchronous.
        for _ in range(30):
            if self.api.GetForegroundWindow() == hwnd:
                return
            time.sleep(0.01)
        raise OSError(f"Could not focus target window (target={hwnd}, foreground={self.api.GetForegroundWindow()})")

    def send(self, hwnd, keys):
        if self.api.GetForegroundWindow() != hwnd:
            raise OSError("Target window lost focus before key input")

        def event(key, up=False):
            extended = key in {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
                               0x28, 0x2D, 0x2E, 0x5B}
            return self.Input(type=1, ki=self.KeyboardInput(
                wVk=key, dwFlags=int(extended) | (2 if up else 0)))

        events = [event(key) for key in keys]
        events.extend(event(key, True) for key in reversed(keys))
        batch = (self.Input * len(events))(*events)
        sent = self.api.SendInput(len(batch), batch, self.ctypes.sizeof(self.Input))
        if sent != len(batch):
            # Release only keys whose down event was actually inserted.
            down = list(keys[:min(sent, len(keys))])
            released = max(0, sent - len(keys))
            if released:
                down = down[:-released]
            if down:
                cleanup = (self.Input * len(down))(*(event(k, True) for k in reversed(down)))
                self.api.SendInput(len(cleanup), cleanup, self.ctypes.sizeof(self.Input))
            raise OSError(f"SendInput failed ({sent}/{len(batch)} events inserted)")


class WindowKeyAction:
    def __init__(self, config):
        self.config = config
        self.status = "Idle"

    def connect(self):
        try:
            found = find_window(self.config.window_title)
            self.status = "Found" if found else "Window not found"
            return bool(found)
        except Exception as exc:
            self.status = str(exc)
            return False

    def _send(self, hotkey, status):
        try:
            keys = tuple(virtual_key(key) for key in hotkey)
            if len(set(keys)) != len(keys):
                raise ValueError("Hotkey contains duplicate keys")
            hwnd = find_window(self.config.window_title)
            if hwnd is None:
                raise OSError(f"Window not found: {self.config.window_title!r}")
            keyboard = WindowsKeyboard()
            keyboard.focus(hwnd)
            keyboard.send(hwnd, keys)
            self.status = status
            return True
        except Exception as exc:
            self.status = str(exc)
            return False

    def start(self):
        return self._send(self.config.start_hotkey, "Start keys sent")

    def stop(self):
        return self._send(self.config.stop_hotkey, "Stop keys sent")

    def get_status(self):
        return self.status

    def update_status(self):
        return self.get_status()
