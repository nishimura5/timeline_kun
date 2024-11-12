import os
import subprocess
import sys


def play_sound(sound_name):
    if getattr(sys, "frozen", False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(__file__)
    sound_path = os.path.join(current_dir, "sound", sound_name)
    # no window
    subprocess.Popen(
        [
            "powershell",
            "-c",
            f"(New-Object Media.SoundPlayer '{sound_path}').PlaySync();",
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
