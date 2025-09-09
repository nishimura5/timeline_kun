import os
import sys
import threading
import tkinter as tk
from tkinter import ttk


class BleButtonManager:
    """BLEボタンとステータス表示を管理するクラス"""

    def __init__(self, parent_frame, master_window, trigger_device, ble_file_name):
        """
        Args:
            parent_frame: ボタンとラベルを配置する親フレーム
            master_window: UIの更新をスケジュールするためのメインウィンドウ
            trigger_device: BLE制御用のTriggerインスタンス
        """
        self.master_window = master_window
        self.trigger_device = trigger_device

        # BLE UI要素を作成
        self.ble_frame = ttk.Frame(parent_frame)
        self.ble_frame.pack(side=tk.RIGHT)

        self.ble_btn = ttk.Button(
            self.ble_frame, text="BLE Connect", command=self.connect_ble
        )
        self.ble_btn.pack(padx=12, side=tk.LEFT)

        self.ble_status_label = ttk.Label(self.ble_frame, text="Disconnected")
        self.ble_status_label.pack(padx=12, side=tk.LEFT)

        self.load_ble_name(ble_file_name)

    def load_ble_name(self, ble_file_name):
        if getattr(sys, "frozen", False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(__file__)

        ble_file_path = os.path.join(current_dir, ble_file_name)
        try:
            with open(ble_file_path, "r", encoding="utf-8") as f:
                device_names = [line.strip() for line in f.readlines()]
            device_names = [name for name in device_names if name]
            print(f"Loaded BLE device names: {device_names}")
            self.trigger_device.set_device_names(device_names)
        except Exception as e:
            print(f"Error loading BLE device names: {e}")
        dev_names = ", ".join(self.trigger_device.target_device_names)
        self.ble_status_label.config(text=dev_names if dev_names else "No Devices")

    def connect_ble(self):
        """BLE接続を開始"""
        # ボタンを無効化して、接続中の表示に変更
        self.set_disabled()
        self.ble_status_label.config(text="Connecting...")

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
        """BLE接続完了時にメインスレッドで呼ばれる"""
        self.ble_btn.config(state="normal")
        self.update_ble_status()

    def _on_ble_connect_error(self):
        """BLE接続エラー時にメインスレッドで呼ばれる"""
        self.ble_btn.config(state="normal")
        self.ble_status_label.config(text="Connect Failed")

    def update_ble_status(self):
        """BLEステータスラベルを更新"""
        self.ble_status_label.config(text=self.trigger_device.get_status())
