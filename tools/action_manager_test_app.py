"""Standalone window for manually checking ActionManager window_key actions."""

import tkinter as tk


def main():
    root = tk.Tk()
    root.title("timeline_kun action manager test")

    status = tk.Label(root, text="Idle")
    status.pack(padx=24, pady=12)
    focus = tk.Label(root, text="Not focused")
    focus.pack(pady=6)
    tk.Label(root, text="F9: Recording\nF10: Stopped").pack(padx=24, pady=12)

    def update_focus():
        focus.config(text="Focused" if root.focus_get() is not None else "Not focused")

    # Check after focus events settle, including the initial window mapping.
    root.bind("<FocusIn>", lambda event: root.after_idle(update_focus))
    root.bind("<FocusOut>", lambda event: root.after_idle(update_focus))
    root.bind("<F9>", lambda event: status.config(text="Recording"))
    root.bind("<F10>", lambda event: status.config(text="Stopped"))
    root.after_idle(update_focus)
    root.mainloop()


if __name__ == "__main__":
    main()
