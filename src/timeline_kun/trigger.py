import threading
import time

from . import ble_control


class Trigger:
    """録画トリガーの公開インターフェースは変更しない。
    set_device_names と set_keyword と set_delay_sec
    ble_connect と trigger_in と trigger_out
    get_triggered と set_status と get_status
    """

    def __init__(self, offset_sec: int = 5) -> None:
        self.triggered_in = False
        self.offset_sec = offset_sec
        self.keyword = "(recording)"
        self.ble_thread = ble_control.BleThread()
        self.target_device_names = []
        self.connection_status = "Idle"
        self.delay_sec = 1

    def ble_connect(self) -> None:
        self.ble_thread.start()
        command, ok_count, msg = self.ble_thread.execute_command(
            "connect", None, timeout=30
        )
        if ok_count == len(self.target_device_names):
            self.connection_status = "Connected"
        else:
            self.connection_status = (
                f"Failed ({ok_count}/{len(self.target_device_names)})"
            )
            print(f"BLE connect failed: {msg}")

    def set_device_names(self, names):
        self.target_device_names = names
        self.ble_thread.set_target_device_names(names)

    def set_keyword(self, keyword):
        self.keyword = keyword

    def set_delay_sec(self, delay_sec):
        self.delay_sec = delay_sec

    def trigger_in(self, title):
        if self.keyword in title and self.triggered_in is False:
            self.triggered_in = True
            command, success, msg = self.ble_thread.execute_command(
                "record_start", None, timeout=3
            )
            if success:
                self.connection_status = "Recording"
                return True
            self.connection_status = "Failed to start"
        return False

    def trigger_out(self, title):
        if self.keyword not in title and self.triggered_in is True:
            print("trigger out")
            self.triggered_in = False
            threading.Thread(target=self._delayed_stop, daemon=True).start()
            return True
        return False

    def _delayed_stop(self):
        time.sleep(self.delay_sec)
        command, success, msg = self.ble_thread.execute_command(
            "record_stop", None, timeout=5
        )
        if success:
            self.connection_status = "Connected"
        else:
            self.connection_status = "Failed to stop"

    def get_triggered(self):
        return self.triggered_in

    def set_status(self, status):
        self.connection_status = status

    def get_status(self):
        return self.connection_status

    def update_status(self):
        cmd, alive_cnt, msg = self.ble_thread.execute_command("status", None, timeout=3)
        if cmd != "status":
            return self.connection_status
        try:
            ratio, state = msg.split(maxsplit=1)
            alive_str, total_str = ratio.split("/")
            total = int(total_str)
        except Exception:
            return self.connection_status

        if total == 0:
            # 未接続またはデバイス未検出
            return self.connection_status

        if alive_cnt == 0:
            self.connection_status = "Disconnected"
        elif alive_cnt < total:
            self.connection_status = f"KeepAlive Failed ({alive_cnt}/{total})"
        else:
            if state.startswith("recording"):
                self.connection_status = "Recording..."
            else:
                self.connection_status = "Connected"
        return self.connection_status
