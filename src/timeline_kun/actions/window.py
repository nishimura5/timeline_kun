"""Side-effect-free window lookup shared by preflight and runtime actions."""

import sys


WINDOWS_ONLY_MESSAGE = "WindowKey actions are supported on Windows only."


class UnsupportedWindowKeyAction:
    """Non-Windows fallback: report unsupported without operating on windows."""

    def connect(self) -> bool:
        return False

    def start(self) -> bool:
        return False

    def stop(self) -> bool:
        return False

    def get_status(self) -> str:
        return WINDOWS_ONLY_MESSAGE

    def update_status(self) -> str:
        return self.get_status()


def find_window(window_title: str) -> int | None:
    """Return the first top-level HWND with an exactly matching title.

    Matching preserves case and whitespace. No window is activated or modified.
    """
    if sys.platform != "win32":
        raise OSError(WINDOWS_ONLY_MESSAGE)

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    found = None

    @callback_type
    def visit(hwnd, _):
        nonlocal found
        length = user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, len(title))
        if title.value == window_title:
            found = hwnd
            return False
        return True

    if not user32.EnumWindows(visit, 0) and found is None:
        raise ctypes.WinError(ctypes.get_last_error())
    return found
