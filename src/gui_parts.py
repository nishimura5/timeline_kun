import tkinter as tk
from tkinter import ttk


class Combobox(ttk.Frame):
    def __init__(self, master, label: str, values: list, width=5, current=0):
        super().__init__(master)
        self.frame = ttk.Frame(master)
        caption = ttk.Label(self.frame, text=label)
        caption.pack(side=tk.LEFT, padx=(0, 1))
        self.combobox = ttk.Combobox(self.frame, state="readonly", width=width)
        self.combobox["values"] = values
        self.combobox.current(current)
        self.combobox.pack(side=tk.LEFT)
        self.current_value = None

    def pack_horizontal(self, anchor=tk.E, padx=0, pady=0, side=tk.LEFT):
        self.frame.pack(side=side, anchor=anchor, padx=padx, pady=pady)

    def set_selected_bind(self, func):
        self.combobox.bind("<<ComboboxSelected>>", func)

    def get(self):
        """Get selected value of the combo box"""
        self.current_value = self.combobox.get()
        return self.combobox.get()

    def get_current_value(self):
        """Get the selected value when get() was called"""
        return self.current_value

    def get_values(self):
        return self.combobox["values"]

    def set(self, value=None):
        """Set value to the combo box"""
        if value is None:
            self.combobox.current(0)
        else:
            self.combobox.set(value)

    def set_values(self, values):
        self.combobox["values"] = values
        self.combobox.current(0)

    def set_state(self, state):
        self.combobox["state"] = state
