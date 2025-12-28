import datetime
import re
import sys
import tkinter as tk
from tkinter import ttk
from typing import Literal

from . import time_format, timetable_to_csv

IS_DARWIN = sys.platform.startswith("darwin")
ValidateMode = Literal["none", "focus", "focusin", "focusout", "key", "all"]


class Tree(ttk.Frame):
    """
    End column is not displayed in the tree.
    If you set the end time, csv file will have the end column.
    """

    def __init__(self, master, columns: list):
        super().__init__(master)
        cols = [col["name"] for col in columns]
        self.tree = ttk.Treeview(
            self, columns=cols, show="headings", selectmode="browse"
        )
        for column in columns:
            self.tree.heading(column["name"], text=column["name"])
            self.tree.column(column["name"], width=column["width"])
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree["displaycolumns"] = (
            "title",
            "member",
            "start",
            "duration",
            "fixed",
            "instruction",
        )
        if not IS_DARWIN:
            self.tree.bind("<Button-3>", self._right_click_tree)
        else:
            self.tree.bind("<Button-2>", self._right_click_tree)

        self.menu = tk.Menu(self, tearoff=0)
        self.stage_list = []
        self.write_encoding = "utf-8"

    def set_stages(self, stages):
        self.tree.delete(*self.tree.get_children())
        for i, stage in enumerate(stages):
            self.tree.insert(
                "",
                "end",
                values=[
                    stage["title"],
                    stage["member"],
                    time_format.str_to_time_str(stage["start_sec"]),
                    time_format.str_to_time_str(stage["end_sec"]),
                    time_format.str_to_time_str(stage["duration_sec"]),
                    stage["fixed"],
                    stage["instruction"],
                ],
            )
        self.stage_list = stages

    def add_menu(self, label, command):
        self.menu.add_command(label=label, command=command)

    def set_write_encoding(self, encoding):
        self.write_encoding = encoding

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

    def edit(self, prev_end_sec):
        """Only one row can be edited at once"""
        selected = self.tree.selection()
        if len(selected) == 0 or len(selected) > 1:
            return False
        default_row = self.tree.item(selected)["values"]

        x = self.winfo_rootx()
        y = self.winfo_rooty()
        dialog = TimelineTreeDialog(self, x, y)
        dialog.set_row_contents(default_row)

        idx = self.get_selected_index()
        start = time_format.timedelta_to_str(self.stage_list[idx]["start_dt"])
        end = time_format.timedelta_to_str(self.stage_list[idx]["end_dt"])
        dialog.set_current_time_range(start, end)
        dialog.set_prev_sec(prev_end_sec)
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
            values[2] = dialog.selected_start
            values[3] = dialog.selected_end
            values[4] = dialog.selected_duration
            if dialog.selected_instruction != "":
                values[6] = dialog.selected_instruction
            elif (
                dialog.selected_instruction == " " or dialog.selected_instruction == ""
            ):
                values[6] = ""

            self.tree.item(item, values=values)
        return True

    def insert(self):
        selected = self.tree.selection()
        if len(selected) != 1:
            return False

        item = selected[0]
        idx = self.tree.index(item)
        if idx == 0:
            start_dt = datetime.timedelta(seconds=0)
        else:
            start_dt = self.stage_list[idx - 1]["end_dt"]

        new_row = {
            "title": "New event",
            "member": "",
            "start_dt": start_dt,
            "end_dt": start_dt,
            "duration": datetime.timedelta(seconds=60),
            "start_sec": "",
            "end_sec": "",
            "duration_sec": "1:00",
            "fixed": "duration",
            "instruction": "",
        }
        item = selected[0]
        idx = self.tree.index(item)
        self.stage_list.insert(idx, new_row)
        self.set_stages(self.stage_list)
        return True

    def remove(self):
        """Only one row can be removed at once"""
        selected = self.tree.selection()
        if len(selected) != 1:
            return False

        item = selected[0]

        # update start and end time below all removed item
        idx = self.tree.index(item)
        self.stage_list.pop(idx)
        self.set_stages(self.stage_list)
        return True

    def tree_to_csv_file(self, file_path):
        end_col_num = 3
        timetable_to_csv.move_to_backup_folder(file_path)
        ends = [
            self.tree.item(item)["values"][end_col_num]
            for item in self.tree.get_children()
        ]

        if ends.count("") == len(ends):
            header = "title,member,start,duration,fixed,instruction"
            no_end = True
        else:
            header = "title,member,start,end,duration,fixed,instruction"
            no_end = False

        with open(file_path, "w", encoding=self.write_encoding) as f:
            f.write(header + "\n")
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                if no_end:
                    values.pop(end_col_num)
                line = ",".join(str(val) for val in values)
                f.write(line + "\n")

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.stage_list = []


class TimelineTreeDialog(tk.Frame):
    def __init__(self, master, x, y):
        super().__init__(master)
        dialog = tk.Toplevel(master)
        dialog.focus_set()
        dialog.title("Timeline row")
        dialog.geometry(f"+{x + 500}+{y}")
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
        self.msg_label = ttk.Label(tar_frame, text="")
        self.msg_label.pack(pady=5, side=tk.TOP, anchor=tk.W)

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

    def set_prev_sec(self, prev_end_sec):
        self.prev_end_sec = prev_end_sec

    def on_fixed_selected(self, event=None):
        self._update()
        # when start is set, entry should be current start time
        current_start = self.current_time_range_label.start_label.cget("text")
        current_start_sec = time_format.str_to_seconds(current_start)
        self.start_entry.set_seconds(current_start_sec)

    def _update(self):
        fixed_code = self.fixed_combobox.get()
        if fixed_code == "duration":
            self.start_entry.set_seconds("")
            self.end_entry.set_seconds("")
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
            self.msg_label.config(text="No time entry", foreground="red")
            return False

        duration = self.duration_entry.get_seconds()
        start = self.start_entry.get_seconds()
        end = self.end_entry.get_seconds()

        validate_result = True
        # basic validation
        if fixed == "start":
            if start == 0 and self.prev_end_sec != 0:
                error_msg = '"Start" should be set.'
                validate_result = False
            elif duration > 0 and end > 0:
                error_msg = '"Duration" or "End" (or both) should be blank.'
                validate_result = False
            elif start >= end and end > 0:
                error_msg = '"Start" should be smaller than "End".'
                validate_result = False
            else:
                error_msg = "OK"
                validate_result = True
        elif fixed == "duration":
            if duration == 0:
                error_msg = '"Duration" should be set.'
                validate_result = False
            else:
                error_msg = "OK"
                validate_result = True

        print(error_msg)
        if validate_result is False:
            self.msg_label.config(text=error_msg, foreground="red")
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

        if start_sec > end_sec:
            print("start > end")
            return False
        return True


class TimeEntry(ttk.Frame):
    def __init__(self, master, label_text: str):
        super().__init__(master)

        label = ttk.Label(self, text=label_text)
        label.pack(side=tk.LEFT)
        self._focusin_value = ""
        self._validate_mode: ValidateMode = "focusout"

        vcmd = (self.register(self._validate), "%P")
        invcmd = (self.register(self._invalid), "%P")
        self.time_entry = ttk.Entry(
            self,
            width=7,
            validate="focusout",
            validatecommand=vcmd,
            invalidcommand=invcmd,
        )
        self.time_entry.pack(side=tk.LEFT)
        self.time_entry.bind("<FocusIn>", self._on_focus_in)

    def set_time(self, time_str):
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, time_str)

    def get_time(self):
        return self.time_entry.get()

    def set_seconds(self, seconds):
        if seconds == "":
            self.set_time("")
            return
        time_str = time_format.str_to_time_str(seconds)
        self.set_time(time_str)

    def get_seconds(self):
        time_str = self.time_entry.get()
        if time_str == "":
            return 0
        return time_format.str_to_seconds(time_str)

    def get_status(self):
        status = self.time_entry.cget("state")
        return status

    def enabled(self):
        self.time_entry.config(state="normal")

    def disabled(self):
        self.time_entry.config(state="disabled")

    def is_blank(self):
        return self.time_entry.get() == ""

    def _validate(self, text: str) -> bool:
        if text is None:
            return False

        text = text.strip()
        if text == "":
            return True

        # Only digits and ":" allowed
        if not re.fullmatch(r"[0-9:]+", text):
            return False

        # At most two colons
        if text.count(":") > 2:
            return False

        parts = text.split(":")

        # Helper: validate a 0-59 field (minute/second) with partial typing support
        def valid_0_59_field(field: str) -> bool:
            if field == "":
                return True  # allow partial like "1:" or "1:2:"
            if not field.isdigit():
                return False
            if len(field) > 2:
                return False
            if len(field) == 2 and int(field) > 59:
                return False
            return True  # len==1 is always allowed while typing

        # 1-colon: M:SS  (M can be any length >=1 once completed)
        if len(parts) == 2:
            m, s = parts

            # minutes part: allow partial typing ("" only allowed if user starts with ":"; optional)
            if m != "" and not m.isdigit():
                return False

            # seconds must be 0-59 once 2 digits are present; <=2 digits always
            return valid_0_59_field(s)

        # 2-colon: H:MM:SS
        if len(parts) == 3:
            h, m, s = parts

            # hours part: any non-negative integer, allow partial ("" while typing)
            if h != "" and not h.isdigit():
                return False

            # minutes/seconds are 0-59 fields
            if not valid_0_59_field(m):
                return False
            if not valid_0_59_field(s):
                return False

            return True

        return text.isdigit()

    def _invalid(self, text):
        # revert to previous value
        self.time_entry.config(validate="none")
        try:
            self.time_entry.delete(0, tk.END)
            self.time_entry.insert(0, self._focusin_value)
        finally:
            self.time_entry.config(validate=self._validate_mode)

        self.time_entry.after_idle(self.time_entry.focus_set)

    def _on_focus_in(self, event):
        self._focusin_value = self.time_entry.get()


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
