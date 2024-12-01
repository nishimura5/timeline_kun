import re
import sys
import tkinter as tk
from tkinter import ttk

import time_format
import timetable_to_csv

IS_DARWIN = sys.platform.startswith("darwin")


class Tree(ttk.Frame):
    def __init__(self, master, columns: list, height: int):
        super().__init__(master)
        cols = [col["name"] for col in columns]
        self.tree = ttk.Treeview(
            self, columns=cols, height=height, show="headings", selectmode="extended"
        )
        for column in columns:
            self.tree.heading(column["name"], text=column["name"])
            self.tree.column(column["name"], width=column["width"])
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if not IS_DARWIN:
            self.tree.bind("<Button-3>", self._right_click_tree)
        else:
            self.tree.bind("<Button-2>", self._right_click_tree)

        self.menu = tk.Menu(self, tearoff=0)
        self.stage_list = []

    def set_stages(self, stages):
        self.tree.delete(*self.tree.get_children())
        for i, stage in enumerate(stages):
            self.tree.insert(
                "",
                "end",
                values=[
                    stage["title"],
                    stage["member"],
                    time_format.seconds_to_time_str(stage["start_sec"]),
                    time_format.seconds_to_time_str(stage["end_sec"]),
                    time_format.seconds_to_time_str(stage["duration_sec"]),
                    stage["fixed"],
                    stage["instruction"],
                ],
            )
        self.stage_list = stages

    def add_menu(self, label, command):
        self.menu.add_command(label=label, command=command)

    def get_selected_index(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return None
        selected = selected[0]
        return self.tree.index(selected)

    def _right_click_tree(self, event):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        self.menu.post(event.x_root, event.y_root)

    def check_csv_file_locked(self, file_path):
        if timetable_to_csv.check_file_locked(file_path) is True:
            return True
        return False

    def edit(self, prev_end_sec, next_start_sec, no_next_start, no_prev_end):
        selected = self.tree.selection()
        if len(selected) == 0:
            return False
        if len(selected) > 1:
            default_row = ["", "", "", "", "", "", ""]
        elif len(selected) == 1:
            default_row = self.tree.item(selected)["values"]

        x = self.winfo_rootx()
        y = self.winfo_rooty()
        dialog = TimelineTreeDialog(self, x, y)
        dialog.set_row_contents(default_row)

        idx = self.get_selected_index()
        start = time_format.timedelta_to_str(self.stage_list[idx]["start_dt"])
        end = time_format.timedelta_to_str(self.stage_list[idx]["end_dt"])
        dialog.set_current_time_range(start, end)
        dialog.set_valid_time_range(prev_end_sec, next_start_sec)
        dialog.set_prev_next_limt(no_prev_end, no_next_start)
        self.wait_window(dialog.dialog)

        new_title = dialog.selected_title
        new_member = dialog.selected_member
        if new_title is None:
            return False
        for item in selected:
            values = self.tree.item(item)["values"]
            if new_title != "":
                values[0] = new_title
            if new_member != "":
                values[1] = new_member
            if dialog.selected_fixed != "":
                values[5] = dialog.selected_fixed
            if dialog.selected_start != "":
                values[2] = dialog.selected_start
            if dialog.selected_end != "":
                values[3] = dialog.selected_end
            if dialog.selected_duration != "":
                values[4] = dialog.selected_duration
            if dialog.selected_instruction != "":
                values[6] = dialog.selected_instruction
            elif dialog.selected_instruction == " ":
                values[6] = ""

            self.tree.item(item, values=values)
        return True

    def remove(self):
        """Only one row can be removed at once"""
        selected = self.tree.selection()
        if len(selected) != 1:
            return False

        item = selected[0]

        # update start and end time below all removed item
        idx = self.tree.index(item)
        # offset value by selected index (end_time - start_time)
        offset = self.stage_list[idx]["end_dt"] - self.stage_list[idx]["start_dt"]
        offset_sec = offset.total_seconds()
        for i in range(idx + 1, len(self.stage_list)):
            if self.stage_list[i]["fixed"] == "duration":
                continue
            new_start_sec = (
                time_format.time_str_to_seconds(self.stage_list[i]["start_sec"])
                - offset_sec
            )
            self.stage_list[i]["start_sec"] = str(int(new_start_sec))
            current_end_sec = time_format.time_str_to_seconds(
                self.stage_list[i]["end_sec"]
            )
            if current_end_sec != 0:
                new_end_sec = (
                    time_format.time_str_to_seconds(self.stage_list[i]["end_sec"])
                    - offset_sec
                )
                self.stage_list[i]["end_sec"] = str(int(new_end_sec))
        self.stage_list.pop(idx)
        self.set_stages(self.stage_list)
        return True

    def tree_to_csv_file(self, file_path):
        timetable_to_csv.move_to_backup_folder(file_path)

        with open(file_path, "w", encoding="shift-jis") as f:
            header = "title,member,start,end,duration,fixed,instruction"
            f.write(header + "\n")
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                line = ",".join(str(val) for val in values)
                f.write(line + "\n")


class TimelineTreeDialog(tk.Frame):
    def __init__(self, master, x, y):
        super().__init__(master)
        dialog = tk.Toplevel(master)
        dialog.focus_set()
        dialog.title("Timeline row")
        dialog.geometry(f"+{x+500}+{y}")
        dialog.grab_set()

        tar_frame = ttk.Frame(dialog)
        tar_frame.pack(side=tk.TOP, padx=20, pady=(20, 0))

        title_frame = ttk.Frame(tar_frame)
        title_frame.pack(pady=5, side=tk.TOP, anchor=tk.W)
        title_label = ttk.Label(title_frame, text="Title:")
        title_label.pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, width=27)
        self.title_entry.pack(padx=(0, 30), side=tk.LEFT)

        member_label = ttk.Label(title_frame, text="Member:")
        member_label.pack(side=tk.LEFT)
        self.member_entry = ttk.Entry(title_frame, width=27)
        self.member_entry.pack(side=tk.LEFT)

        instruction_frame = ttk.Frame(tar_frame)
        instruction_frame.pack(pady=5, side=tk.TOP, anchor=tk.W)
        instruction_label = ttk.Label(instruction_frame, text="Instruction:")
        instruction_label.pack(padx=(0, 3), side=tk.LEFT)
        self.instructions_entry = ttk.Entry(instruction_frame, width=62)
        self.instructions_entry.pack(side=tk.LEFT)

        self.current_time_range_label = TimeRangeLabel(tar_frame, "Current time range:")
        self.current_time_range_label.pack(pady=5, side=tk.TOP, anchor=tk.W)
        self.valid_time_range_label = TimeRangeLabel(tar_frame, "Valid time range:")
        self.valid_time_range_label.pack(pady=5, side=tk.TOP, anchor=tk.W)

        time_frame = ttk.Frame(tar_frame)
        time_frame.pack(pady=5, side=tk.TOP, anchor=tk.W)

        fixed_frame = ttk.Frame(time_frame)
        fixed_frame.pack(padx=(0, 20), pady=5, anchor=tk.W, side=tk.LEFT)
        fixed_label = ttk.Label(fixed_frame, text="Fixed:")
        fixed_label.pack(side=tk.LEFT)
        self.fixed_combobox = ttk.Combobox(
            fixed_frame, values=["start", "duration", ""], state="readonly", width=10
        )
        self.fixed_combobox.pack(side=tk.LEFT)
        self.fixed_combobox.bind("<<ComboboxSelected>>", self.on_fixed_selected)

        self.start_entry = TimeEntry(time_frame, "Start:")
        self.start_entry.pack(padx=(0, 20), side=tk.LEFT)

        self.duration_entry = TimeEntry(time_frame, "Duration:")
        self.duration_entry.pack(padx=(0, 20), side=tk.LEFT)

        self.end_entry = TimeEntry(time_frame, "End:")
        self.end_entry.pack(side=tk.LEFT)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, pady=20)
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=(0, 5))
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT)

        self.dialog = dialog
        self.selected_title = None
        self.selected_member = None
        self.selected_duration = None
        self.selected_start = None
        self.selected_end = None
        self.selected_fixed = None

        dialog.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_row_contents(self, default_row):
        title, member, start, end, duration, fixed, instruction = default_row
        self._update_entry(self.title_entry, title)
        self._update_entry(self.member_entry, member)
        self._update_entry(self.instructions_entry, instruction)
        self.duration_entry.set_time(duration)
        self.start_entry.set_time(start)
        self.end_entry.set_time(end)
        self.fixed_combobox.set(fixed)

        self._update()

    def set_current_time_range(self, start, end):
        self.current_time_range_label.set_range(start, end)

    def set_valid_time_range(self, prev_end_sec, next_start_sec):
        self.prev_end_sec = 0 if prev_end_sec is None else prev_end_sec
        self.next_start_sec = 1000000 if next_start_sec is None else next_start_sec
        prev_end_str = time_format.seconds_to_time_str(self.prev_end_sec)
        next_start_str = time_format.seconds_to_time_str(self.next_start_sec)
        self.valid_time_range_label.set_range(prev_end_str, next_start_str)

    def set_prev_next_limt(self, no_prev_end, no_next_start):
        self.no_prev_end = no_prev_end
        self.no_next_start = no_next_start

    def on_fixed_selected(self, event=None):
        self._update()
        # when start is set, entry should be current start time
        current_start = self.current_time_range_label.start_label.cget("text")
        current_start_sec = time_format.time_str_to_seconds(current_start)
        self.start_entry.set_seconds(current_start_sec)

    def _update(self):
        fixed_code = self.fixed_combobox.get()
        if fixed_code == "duration":
            self.start_entry.set_seconds(0)
            self.end_entry.set_seconds(0)
            self.duration_entry.enabled()
            self.start_entry.disabled()
            self.end_entry.disabled()
        elif fixed_code == "start":
            self.start_entry.enabled()
            self.end_entry.enabled()
            self.duration_entry.enabled()

    def on_ok(self):
        if self._validate_time_entry() is False:
            return
        self.selected_title = self.title_entry.get()
        self.selected_member = self.member_entry.get()
        self.selected_instruction = self.instructions_entry.get()
        self.selected_duration = self.duration_entry.get_time()
        self.selected_start = self.start_entry.get_time()
        self.selected_end = self.end_entry.get_time()
        self.selected_fixed = self.fixed_combobox.get()
        self.dialog.destroy()

    def on_cancel(self):
        self.selected_title = None
        self.dialog.destroy()

    def on_close(self):
        self.selected_title = None
        self.dialog.destroy()

    def _update_entry(self, entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def _validate_time_entry(self):
        fixed = self.fixed_combobox.get()
        if fixed == "":
            return True
        time_entry_combination = [
            self.duration_entry.is_blank(),
            self.start_entry.is_blank(),
            self.end_entry.is_blank(),
        ]
        if all(time_entry_combination):
            print("no time entry")
            return True
        elif any(time_entry_combination):
            print("all time entry should be blank or filled")
            return False

        duration = int(self.duration_entry.get_seconds())
        start = int(self.start_entry.get_seconds())
        end = int(self.end_entry.get_seconds())

        validate_result = True
        # basic validation
        if fixed == "start":
            if start > 0 and (duration > 0 or end > 0):
                error_msg = "OK (0)"
                validate_result = True
            elif self.no_next_start and duration == 0 and end == 0:
                error_msg = "In case of no next start, duration or end should be set."
            elif start > 0 and duration == 0 and end == 0:
                error_msg = "OK (1)"
                validate_result = True
            elif start == 0 and self.prev_end_sec == 0:
                error_msg = "OK (first stage)"
                validate_result = True
            elif start == 0:
                error_msg = "In case of fixed start, start should be set."
                validate_result = False
            elif duration > 0 and end > 0:
                error_msg = (
                    "In case of fixed start, both duration and end should not be set."
                )
                validate_result = False
            elif start >= end and end != 0:
                error_msg = "In case of fixed start, start should be smaller than end."
                validate_result = False
            else:
                error_msg = "Invalid time entry(1)"
                validate_result = False
        elif fixed == "duration":
            if self.no_prev_end:
                error_msg = "In case of no prev end, start or end should be set."
                validate_result = False
            elif duration > 0:
                error_msg = "OK"
                validate_result = True
            else:
                error_msg = "In case of fixed duration, duration should be set."
                validate_result = False

        if validate_result is False:
            print(error_msg)
            return False
        else:
            if start == 0:
                start_sec = self.prev_end_sec
            else:
                start_sec = start
            if duration == 0 and end == 0:
                end_sec = start_sec
            elif duration > 0:
                end_sec = start_sec + duration
            else:
                end_sec = end

        # calculate end time
        if start_sec < self.prev_end_sec:
            self.valid_time_range_label.turn_red_start(True)
            return False
        elif end_sec < self.prev_end_sec:
            self.valid_time_range_label.turn_red_end(True)
            return False
        elif start_sec > self.next_start_sec:
            self.valid_time_range_label.turn_red_start(True)
            return False
        elif end_sec > self.next_start_sec:
            self.valid_time_range_label.turn_red_end(True)
            return False
        else:
            self.valid_time_range_label.turn_red_start(False)
            self.valid_time_range_label.turn_red_end(False)


class TimeEntry(ttk.Frame):
    def __init__(self, master, label_text: str):
        super().__init__(master)

        label = ttk.Label(self, text=label_text)
        label.pack(side=tk.LEFT)
        vcmd = (self.register(self._validate), "%P")
        invcmd = (self.register(self._invalid), "%P")
        self.time_entry = ttk.Entry(
            self, width=7, validatecommand=vcmd, invalidcommand=invcmd
        )
        self.time_entry.pack(side=tk.LEFT)

    def set_time(self, time_str):
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, time_str)

    def get_time(self):
        return self.time_entry.get()

    def set_seconds(self, seconds):
        if seconds == "":
            self.set_time("")
            return
        time_str = time_format.seconds_to_time_str(seconds)
        self.set_time(time_str)

    def get_seconds(self):
        time_str = self.time_entry.get()
        if time_str == "":
            return ""
        return time_format.time_str_to_seconds(time_str)

    def get_status(self):
        status = self.time_entry.cget("state")
        return status

    def enabled(self):
        self.time_entry.config(state="normal")

    def disabled(self):
        self.time_entry.config(state="disabled")

    def is_blank(self):
        return self.time_entry.get() == ""

    def _validate(self, text):
        p = r"(?:[0-5]?\d):[0-5]?\d"
        m = re.match(p, text)
        return m is not None

    def _invalid(self, text):
        self.time_entry.delete(0, tk.END)


class TimeRangeLabel(ttk.Frame):
    def __init__(self, master, label_str):
        super().__init__(master)
        title_label = ttk.Label(self, text=label_str)
        title_label.pack(side=tk.LEFT)

        self.start_label = ttk.Label(self, text="")
        self.start_label.pack(side=tk.LEFT)

        interval_label = ttk.Label(self, text="-")
        interval_label.pack(padx=5, side=tk.LEFT)

        self.end_label = ttk.Label(self, text="")
        self.end_label.pack(side=tk.LEFT)

    def set_range(self, start, end):
        self.start_label.config(text=start)
        self.end_label.config(text=end)

    def turn_red_start(self, is_red):
        if is_red:
            self.start_label.config(foreground="red")
        else:
            self.start_label.config(foreground="black")

    def turn_red_end(self, is_red):
        if is_red:
            self.end_label.config(foreground="red")
        else:
            self.end_label.config(foreground="black")
