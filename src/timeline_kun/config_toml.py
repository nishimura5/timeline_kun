import os


def make_events_json(tar_path):
    toml_content = """[ble.orange]
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

"""

    if os.path.exists(tar_path):
        return
    with open(tar_path, "w") as f:
        f.write(toml_content)
