import argparse
import datetime
import tkinter as tk
from tkinter import ttk

import csv_to_timetable
import icon_data
import sound
import time_format
import timer_log


class App(ttk.Frame):
    INTERMISSION = "インターバル"

    def __init__(
        self,
        master,
        file_path,
        start_index=0,
        hmmss=True,
        sound_file_name="countdown1.wav",
    ):
        super().__init__(master)
        master.title("Timer")
        self.sound_file_name = sound_file_name
        self.hmmss = hmmss

        # header
        head_frame = ttk.Frame(master)
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
        center_frame = ttk.Frame(master)
        center_frame.pack(fill=tk.BOTH, expand=True)
        self.current_stage_label = ttk.Label(center_frame, style="Small.TLabel")
        self.current_stage_label.grid(row=0, column=0, sticky=tk.S)
        self.current_instruction_label = ttk.Label(center_frame, font=("Helvetica", 18))
        self.current_instruction_label.grid(row=1, column=0, sticky=tk.N)
        center_frame.columnconfigure(0, weight=1)
        center_frame.rowconfigure(0, weight=1)
        center_frame.rowconfigure(1, weight=1)

        # footer
        buttons_frame = ttk.Frame(master)
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
        self.start_btn.pack(padx=10, side=tk.LEFT)
        self.start_btn["state"] = "disabled"

        self.sound_test_btn = ttk.Button(
            buttons_frame,
            text="Sound test",
            command=lambda: sound.play_sound(self.sound_file_name),
        )
        self.sound_test_btn.pack(padx=10, side=tk.LEFT)

        reset_btn = ttk.Button(buttons_frame, text="Reset", command=self.reset_all)
        reset_btn.pack(padx=10, side=tk.LEFT)
        switch_label_size_button = ttk.Button(
            buttons_frame, text="Label size", command=self.switch_label_size
        )
        switch_label_size_button.pack(padx=10, side=tk.LEFT)

        self.stage_list = []
        self.now_stage = 0
        self.is_running = False
        self.update_clock()
        self.ring_done = False

        print(file_path)
        self.csv_path = file_path

        self.load_file(start_index)

    def update_clock(self):
        now = datetime.datetime.now()
        self.main_clock_label.config(text=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.after(
            200,
            self.update_clock,
        )

        # If the timer is stopped, reset the timer
        if self.is_running is False:
            self.count_up_label.config(text="00:00:00")
            self.now_stage = 0
            self.progress_bar.config(value=0)
            self.reset_time = datetime.datetime.now()
            return
        cnt_up = now - self.reset_time
        self.count_up_label.config(
            text=time_format.timedelta_to_str(cnt_up, self.hmmss)
        )

        current_stage = self.stage_list[self.now_stage]
        current_start_dt = current_stage["start_dt"]
        current_end_dt = current_stage["end_dt"]
        if cnt_up > current_end_dt:
            self.now_stage += 1
            self.timer_log.log_ok = True
            if self.now_stage + 1 < len(self.stage_list):
                current_stage = self.stage_list[self.now_stage]
                current_start_dt = current_stage["start_dt"]
                current_end_dt = current_stage["end_dt"]

        # Initial log
        if self.timer_log.log_ok is True:
            self.timer_log.add_log(
                now, current_start_dt, current_stage["title"], current_stage["member"]
            )

        if self.now_stage == 0:
            prev_end_dt = datetime.timedelta(seconds=0)
        else:
            prev_end_dt = self.stage_list[self.now_stage - 1]["end_dt"]
        if self.now_stage + 1 < len(self.stage_list):
            next_title = self.stage_list[self.now_stage + 1]["title"]

        # If the last stage is reached, stop the timer
        if self.now_stage >= len(self.stage_list):
            self.current_stage_label.config(text="End")
            self.current_instruction_label.config(text="")
            self.next_stage_label.config(text="---")
            self.remaining_time_label.config(text="")
            self.is_running = False
            self.timer_log.add_log(now, current_end_dt, "End", "---")
            return

        if cnt_up < current_start_dt:
            # Intermission
            self.current_stage_label.config(text=self.INTERMISSION)
            next_start_dt = current_start_dt
            current_start = time_format.timedelta_to_str(prev_end_dt, self.hmmss)
            current_end = time_format.timedelta_to_str(next_start_dt, self.hmmss)
            self.current_instruction_label.config(
                text=f"{current_start} - {current_end}"
            )
            self.next_stage_label.config(text=current_stage["title"])
            self.update_remaining_time_intermission(cnt_up)
            self.update_progress_intermission(cnt_up)
            self.timer_log.add_log(now, current_start_dt, "Intermission", "---")
            return
        else:
            self.current_stage_label.config(text=current_stage["title"])
            self.title_label.config(text=current_stage["member"])
            # Display instruction if it exists, otherwise display start and end time
            if current_stage["instruction"]:
                self.current_instruction_label.config(text=current_stage["instruction"])
            else:
                current_start = time_format.timedelta_to_str(
                    current_start_dt, self.hmmss
                )
                current_end = time_format.timedelta_to_str(current_end_dt, self.hmmss)
                self.current_instruction_label.config(
                    text=f"{current_start} - {current_end}"
                )
            self.timer_log.add_log(
                now, current_start_dt, current_stage["title"], current_stage["member"]
            )

        if self.now_stage + 1 < len(self.stage_list):
            # next is intermission
            next_start_dt = self.stage_list[self.now_stage + 1]["start_dt"]
            next_stage_label = (
                self.INTERMISSION if next_start_dt > current_end_dt else next_title
            )
            self.next_stage_label.config(text=next_stage_label)
        else:
            self.next_stage_label["text"] = "End"

        self.update_remaining_time_next(cnt_up, current_end_dt)
        self.update_progress_next(cnt_up, current_end_dt)

    def update_remaining_time_intermission(self, cnt_up):
        remaining = (
            self.stage_list[self.now_stage]["start_dt"]
            - cnt_up
            + datetime.timedelta(seconds=1)
        )
        self._update_remaining(remaining)

    def update_remaining_time_next(self, cnt_up, next_dt):
        if next_dt < cnt_up:
            remaining = datetime.timedelta(seconds=0)
        else:
            remaining = next_dt - cnt_up + datetime.timedelta(seconds=1)
        self._update_remaining(remaining)

    def _update_remaining(self, remaining_dt):
        if remaining_dt.seconds == 3 and not self.ring_done:
            sound.play_sound(self.sound_file_name)
            self.ring_done = True
        if remaining_dt.seconds < 3:
            self.ring_done = False
        if remaining_dt <= datetime.timedelta(seconds=0):
            self.remaining_time_label.config(text="")
        else:
            self.remaining_time_label.config(text=self._timedelta_to_str(remaining_dt))

    def update_progress_intermission(self, cnt_up):
        duration_dt = (
            self.stage_list[self.now_stage]["start_dt"]
            - self.stage_list[self.now_stage - 1]["end_dt"]
        )
        start_dt = self.stage_list[self.now_stage]["start_dt"]
        self._update_progress(cnt_up, start_dt, duration_dt)

    def update_progress_next(self, cnt_up, next_dt):
        duration_dt = self.stage_list[self.now_stage]["duration"]
        self._update_progress(cnt_up, next_dt, duration_dt)

    def _update_progress(self, cnt_up, next_dt, duration_dt):
        progress = cnt_up - next_dt
        val = 100 + progress / duration_dt * 100
        self.progress_bar.config(value=val)

    def reset_all(self):
        self.is_running = False
        self.start_btn.config(state="normal")
        self.sound_test_btn.config(state="normal")
        self.current_stage_label.config(text="")
        self.current_instruction_label.config(text="")
        self.next_stage_label.config(text=self.stage_list[0]["title"])
        self.remaining_time_label.config(text="")

    def start(self):
        self.start_btn.config(state="disabled")
        self.sound_test_btn.config(state="disabled")
        self.timer_log = timer_log.TimerLog(self.csv_path)
        self.is_running = True

    def switch_label_size(self):
        if self.current_stage_label["style"] == "Small.TLabel":
            self.current_stage_label["style"] = "Large.TLabel"
        elif self.current_stage_label["style"] == "Large.TLabel":
            self.current_stage_label["style"] = "Tiny.TLabel"
        else:
            self.current_stage_label["style"] = "Small.TLabel"

    def read_file(self, tar_path):
        try:
            with open(tar_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            print("try shift-jis")
            with open(tar_path, "r", encoding="shift-jis") as f:
                return f.read()

    def load_file(self, start_index):
        timetable_csv_str = self.read_file(self.csv_path)
        timetable = csv_to_timetable.TimeTable()
        timetable.load_csv_str(timetable_csv_str)

        self.stage_list = []
        start_row = timetable.get_timetable()[start_index]
        for i, row in enumerate(timetable.get_timetable()):
            if i < start_index:
                continue
            self.stage_list.append(
                {
                    "title": row["title"],
                    "start_dt": row["start"] - start_row["start"],
                    "end_dt": row["end"] - start_row["start"],
                    "duration": row["end"] - row["start"],
                    "member": row["member"],
                    "instruction": row["instruction"],
                }
            )
        self.title_label.config(text=timetable.time_table[0]["member"])
        self.next_stage_label.config(text=self.stage_list[0]["title"])
        self.now_stage = 0
        self.is_running = False
        self.start_btn["state"] = "normal"

    def _timedelta_to_str(self, td, include_hour=False):
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if include_hour is True:
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        else:
            return f"{minutes:02}:{seconds:02}"


def quit(root):
    root.quit()
    root.destroy()


def main(file_path=None, fg_color="orange", start_index=0, hmmss="hmmss"):
    bg_color = "#202020"
    color_and_sound = {
        "orange": "countdown3_1.wav",
        "cyan": "countdown3_2.wav",
        "lightgreen": "countdown3_3.wav",
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
        hmmss = True
    else:
        hmmss = False
    app = App(
        root, file_path, start_index, hmmss, sound_file_name=color_and_sound[fg_color]
    )
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", type=str, required=True)
    parser.add_argument("--text_color", type=str)
    parser.add_argument("--start_index", type=int)
    parser.add_argument("--hmmss", type=str)
    # arg check
    if not parser.parse_args().file_path:
        parser.error("file_path is required")

    args = parser.parse_args()
    main(args.file_path, args.text_color, args.start_index, args.hmmss)
