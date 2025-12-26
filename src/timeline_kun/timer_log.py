import os
from datetime import datetime

from . import events_json, time_format


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
        "session_end",
    ]

    def __init__(self, csv_file_path):
        # BIDS events.tsv format
        tar_dir = os.path.dirname(csv_file_path)
        tar_name = os.path.basename(csv_file_path).split(".")[0]

        self.output_dir = os.path.join(tar_dir, "log")
        os.makedirs(self.output_dir, exist_ok=True)

        self.events_path = os.path.join(self.output_dir, f"{tar_name}_")

        # scans.tsv file
        self.scans_path = os.path.join(self.output_dir, f"{tar_name}_scans.tsv")
        if os.path.exists(self.scans_path) is False:
            with open(self.scans_path, "w") as f:
                f.write("filename\tacq_time\n")

        self.task_name = None
        self.task_start_dt = None

    def _write_log(self, onset, duration, trial_type):
        with open(self.file_path, "a") as f:
            f.write(f"{onset:<.1f}\t{duration:<.1f}\t{trial_type}\n")

    def make_events_json(self):
        prefix = self.file_path.rsplit("_events.tsv", 1)[0]
        events_json.make_events_json(prefix)

    def _write_scans_log(self, filename, acq_time):
        with open(self.scans_path, "a") as f:
            f.write(f"{filename}\t{acq_time}\n")

    def mark_start_time(self, start_time):
        self.session_start_time = start_time

        # events.tsv file
        for i in range(100):
            if os.path.exists(self.events_path + f"{i:0>2}_events.tsv") is False:
                self.file_path = self.events_path + f"{i:0>2}_events.tsv"
                break
        with open(self.file_path, "w") as f:
            f.write("onset\tduration\ttrial_type\n")

        with open(self.scans_path, "a") as f:
            f.write(
                f"{os.path.basename(self.file_path)}\t{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\n"
            )

    def add_control_log(self, trial_type):
        if trial_type not in self.CONTROL_LOGS:
            raise ValueError(f"Invalid control log type: {trial_type}")
        onset = (datetime.now() - self.session_start_time).total_seconds()
        duration = 0.0
        self._write_log(onset, duration, trial_type)
        # for MP4 file in Cameras
        if trial_type == "video_record_start":
            self._write_scans_log(
                "Unknown", datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            )

    def set_task_log(self, task_name: str):
        self.task_start_time = datetime.now()
        self.task_name = task_name

    def add_task_log(self):
        onset = (self.task_start_time - self.session_start_time).total_seconds()
        duration = (datetime.now() - self.task_start_time).total_seconds()
        self._write_log(onset, duration, self.task_name)
