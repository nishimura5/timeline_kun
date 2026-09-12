from .. import ble_control


class GoProAction:
    """GoPro operations and display status, backed by the existing BLE worker."""

    def __init__(self, device_names=None) -> None:
        self.ble_thread = ble_control.BleThread()
        self.target_device_names = []
        self.connection_status = "Idle"
        self.set_device_names(list(device_names or []))

    def connect(self) -> bool:
        self.ble_thread.start()
        _, ok_count, msg = self.ble_thread.execute_command(
            "connect", None, timeout=30
        )
        if ok_count == len(self.target_device_names):
            self.connection_status = "Connected"
        else:
            self.connection_status = (
                f"Failed ({ok_count}/{len(self.target_device_names)})"
            )
            print(f"BLE connect failed: {msg}")

        return self.connection_status == "Connected"

    def set_device_names(self, names):
        self.target_device_names = names
        self.ble_thread.set_target_device_names(names)

    def start(self) -> bool:
        _, success, _ = self.ble_thread.execute_command(
            "record_start", None, timeout=3
        )
        self.connection_status = "Recording" if success else "Failed to start"
        return bool(success)

    def stop(self) -> bool:
        _, success, _ = self.ble_thread.execute_command(
            "record_stop", None, timeout=5
        )
        self.connection_status = "Connected" if success else "Failed to stop"
        return bool(success)

    def set_status(self, status: str) -> None:
        self.connection_status = status

    def get_status(self) -> str:
        return self.connection_status

    def update_status(self) -> str:
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
