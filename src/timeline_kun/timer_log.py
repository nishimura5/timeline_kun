import os
from datetime import datetime

from . import time_format


class TimerLog:
    def __init__(self, csv_file_path):
        tar_dir = os.path.dirname(csv_file_path)
        tar_name = os.path.basename(csv_file_path).split(".")[0]
        today = datetime.now().strftime("%Y-%m-%d")
        self.file_path = os.path.join(tar_dir, f"log_{today}_{tar_name}.csv")
        if os.path.exists(self.file_path) is False:
            with open(self.file_path, "w") as f:
                f.write("datetime,displaytime,message\n")

    def add_log(self, display_time, message):
        dt_str = time_format.timedelta_to_str(display_time)
        self._write_log(dt_str, message)

    def start_log(self):
        print("start")
        self._write_log("0:00:00", "====== start ======")

    def skip_log(self, display_time):
        print("skip")
        dt_str = time_format.timedelta_to_str(display_time)
        self._write_log(dt_str, "skip")

    def reset_log(self, display_time):
        print("reset")
        dt_str = time_format.timedelta_to_str(display_time)
        self._write_log(dt_str, "reset")

    def close_log(self, display_time):
        print("close")
        dt_str = time_format.timedelta_to_str(display_time)
        self._write_log(dt_str, "close")

    def end_log(self, display_time):
        print("end")
        dt_str = time_format.timedelta_to_str(display_time)
        self._write_log(dt_str, "end")

    def _write_log(self, display_time, message):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(self.file_path, "a") as f:
            f.write(f"{now_str},{display_time},{message}\n")


class BIDSLog:
    CONTROL_LOGS = [
        "video_record_start",
        "task_skip",
        "session_start",
        "session_end",
    ]

    def __init__(self, csv_file_path):
        # BIDS events.tsv format
        tar_dir = os.path.dirname(csv_file_path)
        tar_name = os.path.basename(csv_file_path).split(".")[0]
        today = datetime.now().strftime("%Y-%m-%d")
        self.file_path = os.path.join(tar_dir, f"events_{today}_{tar_name}.tsv")
        if os.path.exists(self.file_path) is False:
            with open(self.file_path, "w") as f:
                f.write("onset\tduration\ttrial_type\n")

        self.task_name = None
        self.task_start_dt = None

    def _write_log(self, onset, duration, trial_type):
        with open(self.file_path, "a") as f:
            f.write(f"{onset:<.1f}\t{duration:<.1f}\t{trial_type}\n")

    def mark_start_time(self, start_time):
        self.session_start_time = start_time

    def add_control_log(self, trial_type):
        if trial_type not in self.CONTROL_LOGS:
            raise ValueError(f"Invalid control log type: {trial_type}")
        onset = (datetime.now() - self.session_start_time).total_seconds()
        duration = 0.0
        self._write_log(onset, duration, trial_type)

    def set_task_log(self, task_name: str):
        self.task_start_time = datetime.now()
        self.task_name = task_name

    def add_task_log(self):
        onset = (self.task_start_time - self.session_start_time).total_seconds()
        duration = (datetime.now() - self.task_start_time).total_seconds()
        self._write_log(onset, duration, self.task_name)
