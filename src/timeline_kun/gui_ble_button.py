import threading
import tkinter as tk
from tkinter import ttk


class BleButtonManager:
    """Manages the BLE button and status display."""

    def __init__(
        self, parent_frame, master_window, trigger_device, ble_names, stop_delay_sec=2
    ):
        """
        Args:
            parent_frame: Parent frame where the button and label are placed
            master_window: Main window used to schedule UI updates
            trigger_device: Trigger instance used for BLE control
        """
        self.master_window = master_window
        self.trigger_device = trigger_device
        self.stop_delay_sec = stop_delay_sec
        self.trigger_device.set_delay_sec(self.stop_delay_sec)

        # Create BLE UI elements
        self.ble_frame = ttk.Frame(parent_frame)
        self.ble_frame.pack(side=tk.RIGHT)

        self.ble_btn = ttk.Button(
            self.ble_frame, text="BLE Connect", command=self.connect_ble
        )
        self.ble_btn.pack(padx=0, side=tk.LEFT)

        self.ble_status_label = ttk.Label(self.ble_frame)
        self.ble_status_label.pack(padx=12, side=tk.LEFT)

        self.default_fg_color = self.ble_status_label.cget("foreground")

        if ble_names and len(ble_names) > 0:
            self.trigger_device.set_device_names(ble_names)
            dev_names = ", ".join(self.trigger_device.target_device_names)
            self.trigger_device.set_status(dev_names)
        else:
            self.trigger_device.set_status("No devices configured")
            self.ble_btn.config(state="disabled")
            self.ble_status_label.config(foreground="gray")

    def connect_ble(self):
        """Start BLE connection"""
        self.set_disabled()
        self.trigger_device.set_status("Connecting...")

        def connect_thread():
            try:
                self.trigger_device.ble_connect()
                self.master_window.after(0, self._on_ble_connect_complete)
            except Exception as e:
                print(f"BLE connection error: {e}")
                self.master_window.after(0, self._on_ble_connect_error)

        thread = threading.Thread(target=connect_thread, daemon=True)
        thread.start()

    def set_disabled(self):
        self.ble_btn.config(state="disabled")

    def set_enabled(self):
        self.ble_btn.config(state="normal")

    def _on_ble_connect_complete(self):
        """Called on the main thread when BLE connection completes."""
        self.ble_btn.config(state="normal")
        self.ble_status_label.config(text=self.trigger_device.get_status())

    def _on_ble_connect_error(self):
        """Called on the main thread when a BLE connection error occurs."""
        self.ble_btn.config(state="normal")
        self.trigger_device.set_status("Connection Error")

    def update_ble_status(self):
        """Update the BLE status label."""
        status = self.trigger_device.update_status()
        self.ble_status_label.config(text=status)
