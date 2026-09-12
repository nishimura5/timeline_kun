import os


def make_events_json(tar_path):
    toml_content = """flush = false
flush_width = 36
flush_height = 36

[ble.orange]
ble_names = []
stop_delay_sec = 2

[ble.cyan]
ble_names = []
stop_delay_sec = 2

[ble.lightgreen]
ble_names = []
stop_delay_sec = 2

[log]
make_events_json = true

[excel]
#read_extra_encoding = "your_encoding"

# Generic action settings are global (independent of timer color).
# Settings only: window key execution is not implemented yet.
# Uncomment the whole example to load its settings; disabled by default.
# [actions.pose_streamer]
# type = "window_key"
# keyword = "(pose_recording)"
# start_lead_sec = 5
# stop_delay_sec = 2
# window_title = "カメラ位置確認"
# start_hotkey = ["F9"]
# stop_hotkey = ["F10"]

"""

    if os.path.exists(tar_path):
        return
    with open(tar_path, "w", encoding="utf-8") as f:
        f.write(toml_content)
