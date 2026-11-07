"""Action configuration editor shared by source and frozen previewers."""

import os
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import tomlkit

from .actions.config import parse_action_configs
from .actions.window import WINDOWS_ONLY_MESSAGE, find_window
from .actions.window_key import virtual_key


def parse_hotkey(text):
    keys = [key.strip().upper() for key in text.split("+")]
    for key in keys:
        virtual_key(key)
    return keys


def save_actions(path, actions):
    """Preserve unrelated settings and comments; replace the file atomically."""
    parse_action_configs(actions)
    path = Path(path)
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["actions"] = actions
    content = tomlkit.dumps(document)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False) as stream:
            temporary = stream.name
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


class ActionSettingsDialog(tk.Toplevel):
    def __init__(self, master, config_path, on_save):
        super().__init__(master)
        self.title("Action setting")
        self.transient(master)
        self.resizable(False, False)
        self.config_path = config_path
        self.on_save = on_save
        self.checked_titles = set()
        self.editors = {}
        try:
            document = tomlkit.parse(Path(config_path).read_text(encoding="utf-8"))
            actions = document.get("actions", {}).unwrap() if "actions" in document else {}
            parse_action_configs(actions)
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Action setting", str(exc), parent=self)
            self.destroy()
            return

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(padx=12, pady=12, fill="both", expand=True)
        for name, values in actions.items():
            self.add_editor(name, values)
        if not actions:
            self.add_action()
        buttons = ttk.Frame(self)
        buttons.pack(padx=12, pady=(0, 12), fill="x")
        ttk.Button(buttons, text="Add action", command=self.add_action).pack(side="left")
        ttk.Button(buttons, text="Remove action", command=self.remove_action).pack(side="left", padx=5)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", command=self.save).pack(side="right", padx=5)
        self.grab_set()

    def add_action(self):
        index = 1
        while f"action_{index}" in self.editors:
            index += 1
        self.add_editor(f"action_{index}", {})

    def remove_action(self):
        selected = self.notebook.select()
        for name, (frame, _) in list(self.editors.items()):
            if str(frame) == selected:
                self.notebook.forget(frame)
                frame.destroy()
                del self.editors[name]
                break

    def add_editor(self, name, values):
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text=name)
        self.notebook.select(frame)
        variables = {}
        defaults = {"type": "window_key", "keyword": "", "start_lead_sec": 5,
                    "stop_delay_sec": 2, "window_title": "",
                    "start_hotkey": ["F9"], "stop_hotkey": ["F10"]}
        for row, (field, default) in enumerate(defaults.items()):
            value = values.get(field, default)
            ttk.Label(frame, text=field).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
            if field in ("start_lead_sec", "stop_delay_sec"):
                lower, upper = (3, 5) if field == "start_lead_sec" else (2, 5)
                var = tk.IntVar(frame, value=round(max(lower, min(upper, value))))
                widget = tk.Scale(frame, from_=lower, to=upper, resolution=1,
                                  orient="horizontal", variable=var, length=240)
            else:
                var = tk.StringVar(frame, value="+".join(value) if isinstance(value, list) else value)
                widget = (ttk.Combobox(frame, textvariable=var, values=["window_key"], state="readonly")
                          if field == "type" else ttk.Entry(frame, textvariable=var, width=34))
            variables[field] = var
            widget.grid(row=row, column=1, sticky="ew", pady=6)
            if field == "window_title":
                ttk.Button(frame, text="Check Window",
                           command=lambda v=var: self.check_window(v.get())).grid(row=row, column=2, padx=(8, 0))
        ttk.Label(frame, text="Hotkey example: F9 / Ctrl+Shift+R").grid(row=7, column=1, sticky="w", pady=6)
        self.editors[name] = (frame, variables)

    def check_window(self, title):
        if not title.strip():
            messagebox.showerror("Check Window", "Enter window_title.", parent=self)
            return
        try:
            if sys.platform != "win32":
                messagebox.showinfo("Check Window", WINDOWS_ONLY_MESSAGE, parent=self)
                self.checked_titles.add(title)
                return
            found = find_window(title) is not None
            report = messagebox.showinfo if found else messagebox.showwarning
            report("Check Window", f"{title!r}: {'Found' if found else 'Not found'}", parent=self)
            self.checked_titles.add(title)
        except OSError as exc:
            messagebox.showerror("Check Window", str(exc), parent=self)

    def save(self):
        try:
            actions = {}
            for name, (_, variables) in self.editors.items():
                values = {field: var.get() for field, var in variables.items()}
                for field in ("start_hotkey", "stop_hotkey"):
                    values[field] = parse_hotkey(values[field])
                actions[name] = values
            save_actions(self.config_path, actions)
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Action setting", str(exc), parent=self)
            return
        self.on_save(actions, self.checked_titles)
        self.destroy()
