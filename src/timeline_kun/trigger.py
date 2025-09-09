from . import ble_control


class Trigger:
    def __init__(self, offset_sec=5):
        self.triggered_in = False
        self.offset_sec = offset_sec
        self.keyword = "(recording)"
        self.ble_thread = ble_control.BleThread()
        self.target_device_names = []
        self.connection_status = "Disconnected"

    def ble_connect(self):
        self.ble_thread.start()
        result = self.ble_thread.execute_command("connect", None, timeout=30)
        command, ok_count, msg = result
        if ok_count == len(self.target_device_names):
            self.connection_status = "Connected"
        else:
            self.connection_status = f"Connect Failed ({ok_count}/{len(self.target_device_names)})"
            print(f"BLE connect failed: {msg}")

    def set_device_names(self, names):
        self.target_device_names = names
        self.ble_thread.set_target_device_names(names)

    def set_keyword(self, keyword):
        self.keyword = keyword

    def trigger_in(self, title):
        if self.keyword in title and self.triggered_in is False:
            self.triggered_in = True
            result = self.ble_thread.execute_command("record_start", None, timeout=3)
            command, success, msg = result
            if success:
                self.connection_status = "Recording"

    def trigger_out(self, title):
        if self.keyword not in title and self.triggered_in is True:
            self.triggered_in = False
            result = self.ble_thread.execute_command("record_stop", None, timeout=3)
            command, success, msg = result
            if success:
                self.connection_status = "Connected"

    def get_triggered(self):
        return self.triggered_in

    def get_status(self):
        return self.connection_status
