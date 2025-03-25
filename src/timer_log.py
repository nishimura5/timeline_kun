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
                f.write("datetime,start,member,title\n")
        self.log_ok = True

    def add_log(self, now, dt, title, member):
        if self.log_ok is False:
            return
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        dt_str = time_format.timedelta_to_str(dt)

        with open(self.file_path, "a") as f:
            f.write(f"{now_str},{dt_str},{member},{title}\n")
        self.log_ok = False

    def skip_log(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.file_path, "a") as f:
            f.write(f"{now_str},0:00:00,---,skip\n")
        self.log_ok = False
