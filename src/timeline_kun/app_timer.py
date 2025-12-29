import argparse
import datetime
import os
import sys
import tkinter as tk
import tomllib
from tkinter import ttk

from . import (
    file_loader,
    gui_ble_button,
    icon_data,
    sound,
    time_format,
    timer_log,
    trigger,
)


class App(ttk.Frame):
    INTERMISSION = "Intermission"

    def __init__(
        self,
        master,
        file_path,
        start_index=0,
        is_hmmss=True,
        sound_file_name="countdown3_orange.wav",
        toml_dict={},
    ):
        super().__init__(master)
        master.title("Timer")
        self.sound_file_name = sound_file_name
        self.hmmss = is_hmmss
        self.master = master

        self.ap = sound.AudioPlayer()
        self.ap.load_audio(sound_file_name)

        self.trigger_device = trigger.Trigger(offset_sec=5)

        # header
        head_frame = ttk.Frame(self.master)
        head_frame.pack(fill=tk.X, pady=10, padx=10)

        title_frame = ttk.Frame(head_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.X)
        clock_frame = ttk.Frame(head_frame)
        clock_frame.pack(side=tk.RIGHT, fill=tk.X)

        self.title_label = ttk.Label(title_frame, text="", font=("Helvetica", 28))
        self.title_label.pack(anchor=tk.W)

        self.main_clock_label = ttk.Label(clock_frame, font=("Helvetica", 12))
        self.main_clock_label.pack(anchor=tk.E, pady=1)
        self.count_up_label = ttk.Label(clock_frame, font=("Helvetica", 18))
        self.count_up_label.pack(anchor=tk.E)

        # stage
        center_frame = ttk.Frame(self.master)
        center_frame.pack(fill=tk.BOTH, expand=True)
        self.current_stage_label = ttk.Label(center_frame, style="Small.TLabel")
        self.current_stage_label.grid(row=0, column=0, sticky=tk.S)
        self.current_instruction_label = ttk.Label(center_frame, font=("Helvetica", 18))
        self.current_instruction_label.grid(row=1, column=0, sticky=tk.N)
        center_frame.columnconfigure(0, weight=1)
        center_frame.rowconfigure(0, weight=1)
        center_frame.rowconfigure(1, weight=1)

        # footer
        buttons_frame = ttk.Frame(self.master)
        buttons_frame.pack(pady=(10, 5), side=tk.BOTTOM, fill=tk.BOTH, anchor=tk.S)

        # progress
        progress_frame = ttk.Frame(buttons_frame)
        progress_frame.pack(pady=10, fill=tk.X)
        window_width = self.winfo_screenwidth()
        self.progress_bar = ttk.Progressbar(
            progress_frame, orient=tk.HORIZONTAL, length=window_width
        )
        self.progress_bar.pack()
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 100

        # next stage
        next_frame = ttk.Frame(buttons_frame)
        next_frame.pack(padx=10, pady=(0, 15), fill=tk.X)
        self.next_stage_label = ttk.Label(next_frame, font=("Helvetica", 18))
        self.next_stage_label.pack(side=tk.LEFT, anchor=tk.E)

        self.remaining_time_label = ttk.Label(next_frame, font=("Helvetica", 18))
        self.remaining_time_label.pack(padx=(15, 0), side=tk.LEFT, anchor=tk.E)

        self.start_btn = ttk.Button(buttons_frame, text="Start", command=self.start)
        self.start_btn.pack(padx=12, side=tk.LEFT)
        self.start_btn["state"] = "disabled"

        self.sound_test_btn = ttk.Button(
            buttons_frame,
            text="Sound test",
            command=lambda: self.ap.play_sound(self.sound_file_name),
        )
        self.sound_test_btn.pack(padx=12, side=tk.LEFT)

        self.reset_btn = ttk.Button(buttons_frame, text="Reset", command=self.reset_all)
        self.reset_btn.pack(padx=12, side=tk.LEFT)
        self.reset_btn["state"] = "disabled"

        switch_label_size_button = ttk.Button(
            buttons_frame, text="Label size", command=self.switch_label_size
        )
        switch_label_size_button.pack(padx=12, side=tk.LEFT)

        skip_btn = ttk.Button(buttons_frame, text="Skip", command=self.skip)
        skip_btn.pack(padx=12, side=tk.LEFT)

        ble_names = toml_dict.get("ble_names", [])
        if len(ble_names) > 0:
            self.enable_ble = True
            self.stop_delay_sec = toml_dict.get("stop_delay_sec", 2)
            self.ble_manager = gui_ble_button.BleButtonManager(
                buttons_frame,
                self.master,
                self.trigger_device,
                ble_names,
                self.stop_delay_sec,
            )
        else:
            self.enable_ble = False

        # close event
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.stage_list = []
        self.now_stage = 0
        self.is_running = False
        self.update_clock()
        self.ring_done = False
        self.is_skip = False
        self.disp_time = datetime.timedelta(seconds=0)

        print(f"Timeline CSV file path: {file_path}")
        self.csv_path = file_path

        # Make events.tsv
        self.bids_log = timer_log.BIDSLog(self.csv_path)
        make_events_json = toml_dict.get("make_events_json", False)
        if make_events_json:
            self.bids_log.make_events_json()

        fall_back_encoding = toml_dict.get("read_extra_encoding", "utf-8-sig")
        self.load_file(start_index, fallback_encoding=fall_back_encoding)

    def update_clock(self):
        now = datetime.datetime.now()
        self.main_clock_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.after(100, self.update_clock)

        # If the timer is stopped, reset the timer
        if self.is_running is False:
            self.count_up_label.config(text="00:00:00")
            self.now_stage = 0
            self.progress_bar.config(value=0)
            self.reset_time = datetime.datetime.now()
            self.total_skip_time = datetime.timedelta(seconds=0)
            self.is_skip = False
            if self.enable_ble:
                self.ble_manager.update_ble_status()
            return
        # cnt_up: internal time counter
        # self.disp_time: time used for display and log
        cnt_up = now - self.reset_time
        self.disp_time = cnt_up - self.total_skip_time
        self.count_up_label.config(
            text=time_format.timedelta_to_str(self.disp_time, self.hmmss)
        )

        current_stage = self.stage_list[self.now_stage]
        current_start_dt = current_stage["start_dt"]
        current_end_dt = current_stage["end_dt"]
        # stage change if end time is reached
        if cnt_up > current_end_dt:
            self.now_stage += 1
            if self.now_stage < len(self.stage_list):
                print(
                    f"stage change {self.now_stage} (/{len(self.stage_list)}) {cnt_up}"
                )
                current_stage = self.stage_list[self.now_stage]
                current_start_dt = current_stage["start_dt"]
                current_end_dt = current_stage["end_dt"]
                self.bids_log.add_task_log()
                if cnt_up < current_start_dt:
                    msg = f"{self.INTERMISSION}({current_stage['start_dt']}-{current_stage['end_dt']})"
                    self.bids_log.set_task_log(self.INTERMISSION)
                else:
                    msg = f"{current_stage['title']}({current_stage['start_dt']}-{current_stage['end_dt']})"
                    self.bids_log.set_task_log(current_stage["title"])
        #                self.tlog.add_log(self.disp_time, msg)

        # If the last stage is reached, stop the timer
        if self.now_stage >= len(self.stage_list):
            self.current_stage_label.config(text="End")
            self.current_instruction_label.config(text="")
            self.next_stage_label.config(text="---")
            self.remaining_time_label.config(text="")
            self.is_running = False
            self.bids_log.add_task_log()
            self.bids_log.add_control_log("session_end")
            self.trigger_device.trigger_out("End")
            return

        self.current_stage_label.config(text=current_stage["title"])
        self.title_label.config(text=current_stage["member"])
        self.update_next_stage_label(end_text="End")
        self.update_instruction_label(current_stage, current_start_dt, current_end_dt)

        remaining_dt = self.calc_remaining_time_next(cnt_up, current_end_dt)
        self.sound(remaining_dt, offset_sec=3)
        # BLE
        if self.enable_ble:
            self.trigger(self.now_stage, remaining_dt)
            self.ble_manager.update_ble_status()

        self.update_remaining_time_label(remaining_dt)
        self.update_progress_bar(cnt_up, current_end_dt)
        self.update_skip(remaining_dt, offset_sec=4)

    def update_instruction_label(self, current_stage, start_dt, end_dt):
        # Display instruction if it exists, otherwise display start and end time
        if current_stage["instruction"]:
            self.current_instruction_label.config(text=current_stage["instruction"])
        else:
            start_str = time_format.timedelta_to_str(start_dt, self.hmmss)
            end_str = time_format.timedelta_to_str(end_dt, self.hmmss)
            self.current_instruction_label.config(text=f"{start_str} - {end_str}")

    def calc_remaining_time_next(self, cnt_up, next_dt):
        if next_dt < cnt_up:
            remaining_dt = datetime.timedelta(seconds=0)
        else:
            remaining_dt = next_dt - cnt_up + datetime.timedelta(seconds=1)
        return remaining_dt

    def sound(self, remaining_dt, offset_sec=3):
        if remaining_dt.seconds == offset_sec and not self.ring_done:
            self.ap.play_sound(self.sound_file_name)
            self.ring_done = True
        if remaining_dt.seconds < offset_sec:
            self.ring_done = False

    def trigger(self, now_stage, remaining_dt):
        is_start_trigger = False
        next_stage = now_stage + 1
        if next_stage > len(self.stage_list):
            return

        if next_stage == len(self.stage_list):
            next_stage_instruction = "End"
        else:
            next_stage_instruction = self.stage_list[next_stage]["instruction"]
        current_stage_instruction = self.stage_list[now_stage]["instruction"]
        # Trigger in before X seconds of next stage
        if remaining_dt < datetime.timedelta(seconds=self.trigger_device.offset_sec):
            is_start_trigger = self.trigger_device.trigger_in(next_stage_instruction)
        else:
            # for 1st stage
            is_start_trigger = self.trigger_device.trigger_in(current_stage_instruction)
            # Trigger out when leaving current stage
            is_stop_trigger = self.trigger_device.trigger_out(current_stage_instruction)

        if is_start_trigger:
            #            self.tlog.add_log(self.disp_time, "recording start triggered")
            self.bids_log.add_control_log("video_record_start")

    def update_progress_bar(self, cnt_up, next_dt):
        duration_dt = self.stage_list[self.now_stage]["duration"]
        progress = cnt_up - next_dt
        val = 100 + progress / duration_dt * 100
        self.progress_bar.config(value=val)

    def update_next_stage_label(self, end_text="End"):
        if self.now_stage + 1 < len(self.stage_list):
            self.next_stage_label["text"] = self.stage_list[self.now_stage + 1]["title"]
        else:
            self.next_stage_label["text"] = end_text

    def update_remaining_time_label(self, remaining_dt):
        if remaining_dt <= datetime.timedelta(seconds=0):
            self.remaining_time_label.config(text="")
        else:
            self.remaining_time_label.config(
                text=time_format.timedelta_to_str(remaining_dt, self.hmmss)
            )

    def update_skip(self, remaining_dt, offset_sec=4):
        if self.is_skip:
            # prevent over skip
            if remaining_dt > datetime.timedelta(seconds=offset_sec):
                skip_time = remaining_dt - datetime.timedelta(seconds=offset_sec)
                self.reset_time -= skip_time
                self.total_skip_time += skip_time
                #                self.tlog.skip_log(self.disp_time)
                self.bids_log.add_control_log("task_skip")
            self.is_skip = False

    def reset_all(self):
        self.is_running = False
        #        self.tlog.reset_log(self.disp_time)
        self.start_btn.config(state="normal")
        self.sound_test_btn.config(state="normal")
        self.reset_btn.config(state="disabled")
        self.current_stage_label.config(text="")
        self.current_instruction_label.config(text="")
        self.next_stage_label.config(text=self.stage_list[0]["title"])
        self.remaining_time_label.config(text="")

        # BLE stop
        self.trigger_device.trigger_out("")

        # for close log
        self.disp_time = datetime.timedelta(seconds=0)

    def start(self):
        #        self.tlog.start_log()
        self.bids_log.mark_start_time(datetime.datetime.now())
        self.start_btn.config(state="disabled")
        self.sound_test_btn.config(state="disabled")
        self.reset_btn.config(state="normal")
        if self.enable_ble:
            self.ble_manager.set_disabled()
        self.is_running = True

        # initial event log
        current_stage = self.stage_list[0]
        msg = f"{current_stage['title']}({current_stage['start_dt']}-{current_stage['end_dt']})"
        #        self.tlog.add_log(self.disp_time, msg)
        self.bids_log.set_task_log(current_stage["title"])

    def skip(self):
        self.is_skip = True

    def switch_label_size(self):
        if self.current_stage_label["style"] == "Small.TLabel":
            self.current_stage_label["style"] = "Large.TLabel"
        elif self.current_stage_label["style"] == "Large.TLabel":
            self.current_stage_label["style"] = "Tiny.TLabel"
        else:
            self.current_stage_label["style"] = "Small.TLabel"

    def load_file(self, start_index, fallback_encoding="utf-8-sig"):
        fl = file_loader.FileLoader(self.INTERMISSION, fallback_encoding=fallback_encoding)
        fl.load_file_for_timer(start_index, self.csv_path)

        self.stage_list = fl.get_stage_list()

        self.title_label.config(text=self.stage_list[0]["member"])
        self.next_stage_label.config(text=self.stage_list[0]["title"])
        self.now_stage = 0
        self.is_running = False
        self.start_btn["state"] = "normal"

        for i, stage in enumerate(self.stage_list):
            print(
                f"{i}: {stage['title']}({stage['start_dt']}-{stage['end_dt']}) {stage['instruction']}"
            )

    def _on_closing(self):
        self.trigger_device.trigger_out("")
        #        self.tlog.close_log(self.disp_time)
        self.master.quit()
        self.master.destroy()


def main(
    file_path=None, fg_color: str = "orange", start_index: int = 0, hmmss: str = "hmmss"
):
    bg_color = "#202020"
    color_and_sound = {
        "orange": "countdown3_orange.wav",
        "cyan": "countdown3_cyan.wav",
        "lightgreen": "countdown3_lightgreen.wav",
    }

    root = tk.Tk()
    root.geometry("900x420+0+0")
    root.configure(background=bg_color)
    root.tk.call("wm", "iconphoto", root._w, tk.PhotoImage(data=icon_data.icon_data))
    s = ttk.Style(root)
    s.theme_use("default")
    s.configure("TFrame", background=bg_color)
    s.configure("TLabel", foreground=fg_color, background=bg_color)
    s.configure(
        "Tiny.TLabel", foreground=fg_color, background=bg_color, font=("Helvetica", 36)
    )
    s.configure(
        "Small.TLabel", foreground=fg_color, background=bg_color, font=("Helvetica", 48)
    )
    s.configure(
        "Large.TLabel", foreground=fg_color, background=bg_color, font=("Helvetica", 64)
    )
    s.configure("TButton", foreground=fg_color, background=bg_color, relief="flat")
    s.map("TButton", background=[("active", "#203030")], relief=[("active", "flat")])
    s.configure(
        "Horizontal.TProgressbar",
        troughcolor=bg_color,
        troughrelief="flat",
        background=fg_color,
        borderwidth=0,
        thickness=5,
    )
    s.map(
        "Horizontal.TProgressbar",
        troughcolor=[("active", bg_color), ("!active", bg_color)],
    )

    if hmmss == "hmmss":
        is_hmmss = True
    else:
        is_hmmss = False

    # Load toml config
    if getattr(sys, "frozen", False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(__file__)
    ble_file_name = os.path.join(current_dir, "config.toml")
    with open(ble_file_name, "rb") as f:
        toml = tomllib.load(f)
    # Construct toml_dict for App
    ble_conf = toml.get("ble", {}).get(fg_color, {})
    log_conf = toml.get("log", {})
    excel_conf = toml.get("excel", {})
    toml_dict = {**ble_conf, **log_conf, **excel_conf}

    print(f"TOML config: {toml_dict}")

    app = App(
        root,
        file_path,
        start_index,
        is_hmmss,
        sound_file_name=color_and_sound[fg_color],
        toml_dict=toml_dict,
    )
    app.mainloop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Timeline-kun Timer: manage timed tasks with GUI."
    )
    parser.add_argument(
        "--file_path",
        type=str,
        required=True,
        help="Path to the CSV file containing task definitions (required).",
    )
    parser.add_argument(
        "--fg_color",
        type=str,
        default="orange",
        choices=["orange", "cyan", "lightgreen"],
        help="Foreground color for text and theme (default: orange).",
    )
    parser.add_argument(
        "--start_index",
        type=int,
        default=0,
        help="Index of the task to start from (default: 0). Must be an integer.",
    )
    parser.add_argument(
        "--hmmss",
        type=str,
        default="hmmss",
        choices=["hmmss", "mmss"],
        help="Display format for time (default: hmmss). 'hmmss' for 1:23:45, 'mmss' for 83:45.",
    )
    return parser


def cli(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return main(args.file_path, args.fg_color, args.start_index, args.hmmss)


if __name__ == "__main__":
    cli()
