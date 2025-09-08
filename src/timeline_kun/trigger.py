from . import ble_control


class Trigger:
    def __init__(self, offset_sec=5):
        self.triggered_in = False
        self.offset_sec = offset_sec
        self.keyword = "(recording)"
        self.ble_thread = ble_control.BleThread()

    def ble_connect(self):
        self.ble_thread.start()
        result = self.ble_thread.execute_command("connect", None, timeout=30)
        command, success, msg = result
        if success:
            print("BLE connected")
        else:
            print(f"BLE connect failed: {msg}")

    def set_keyword(self, keyword):
        self.keyword = keyword

    def trigger_in(self, title):
        if self.keyword in title and self.triggered_in is False:
            self.triggered_in = True
            self.ble_thread.execute_command("record_start", None, timeout=3)

    def trigger_out(self, title):
        if self.keyword not in title and self.triggered_in is True:
            self.triggered_in = False
            self.ble_thread.execute_command("record_stop", None, timeout=3)

    def trigger_end(self):
        if self.triggered_in is True:
            self.triggered_in = False
            self.ble_thread.execute_command("disconnect", None, timeout=3)

    def get_triggered(self):
        return self.triggered_in
