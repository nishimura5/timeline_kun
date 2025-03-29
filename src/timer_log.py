import os
from datetime import datetime

import time_format


class TimerLog:
    def __init__(self, csv_file_path):
        tar_dir = os.path.dirname(csv_file_path)
        tar_name = os.path.basename(csv_file_path).split(".")[0]
        today = datetime.now().strftime("%Y-%m-%d")
        self.file_path = os.path.join(tar_dir, f"log_{today}_{tar_name}.csv")
        if os.path.exists(self.file_path) is False:
            with open(self.file_path, "w") as f:
                f.write("datetime,displaytime,message\n")
        self.log_ok = True

    def add_log(self, now, display_time, message):
        if self.log_ok is False:
            return
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_str = time_format.timedelta_to_str(display_time)

        with open(self.file_path, "a") as f:
            f.write(f"{now_str},{dt_str},{message}\n")
        self.log_ok = False

    def start_log(self):
        self._write_log("0:00:00", "start")
        self.log_ok = True

    def skip_log(self, display_time):
        dt_str = time_format.timedelta_to_str(display_time)
        self._write_log(dt_str, "skip")
        self.log_ok = False

    def reset_log(self, display_time):
        dt_str = time_format.timedelta_to_str(display_time)
        self._write_log(dt_str, "reset")
        self.log_ok = False

    def _write_log(self, display_time, message):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.file_path, "a") as f:
            f.write(f"{now_str},{display_time},{message}\n")
        self.log_ok = False
