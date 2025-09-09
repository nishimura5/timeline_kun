import asyncio
import os
import queue
import threading
import time

from bleak import BleakClient, BleakScanner


class BleData:
    # GoPro GATT UUID
    COMMAND_UUID = "b5f90072-aa8d-11e3-9046-0002a5d5c51b"
    SETTING_UUID = "b5f90074-aa8d-11e3-9046-0002a5d5c51b"
    RESPONSE_UUID = "b5f90075-aa8d-11e3-9046-0002a5d5c51b"

    # control commands for GoPro
    START_RECORDING = bytearray([0x03, 0x01, 0x01, 0x01])
    STOP_RECORDING = bytearray([0x03, 0x01, 0x01, 0x00])
    KEEP_ALIVE = bytearray([0x03, 0x5B, 0x01, 0x42])

    KEEP_ALIVE_ID = 0x5B
    OK = 0x00


class BleThread:
    def __init__(self):
        self.thread = None
        self.loop = None
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = False
        self.ble_control = None
        self.last_keep_alive = 0
        self.keep_alive_interval = 10.0
        self.target_device_names = [""]

    def set_target_device_names(self, names):
        self.target_device_names = names

    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._run_thread, daemon=True)
            self.thread.start()

    def stop(self):
        if self.running:
            self.running = False
            self.command_queue.put(("stop", None))
            if self.thread and self.thread.is_alive():
                self.thread.join()

    def _run_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.ble_control = BleControl(self.target_device_names)
        self.loop.run_until_complete(self._command_loop())
        if self.loop:
            self.loop.close()

    async def _command_loop(self):
        while self.running:
            try:
                command, data = self.command_queue.get_nowait()
            except queue.Empty:
                await self._check_keep_alive()
                await asyncio.sleep(0.1)
                continue

            result = await self._execute_command(command, data)
            self.result_queue.put(result)

            if command in ["disconnect", "stop"]:
                break

    async def _execute_command(self, command, data):
        command_map = {
            "connect": self.ble_control.connect,
            "disconnect": self.ble_control.disconnect,
            "record_start": self.ble_control.start_recording,
            "record_stop": self.ble_control.stop_recording,
        }

        if command in command_map:
            ok_count = await command_map[command]()
            print(
                f"Executed command: {command}, result: {ok_count}, time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}, PID: {os.getpid()}"
            )
            if command == "connect" and ok_count:
                self.last_keep_alive = time.time()
            elif command == "disconnect":
                self.last_keep_alive = 0
            return (command, ok_count, "success" if ok_count else "failed")

        return (command, 0, "unknown command")

    async def _check_keep_alive(self):
        current_time = time.time()
        if (
            self.ble_control
            and self.ble_control.is_connected()
            and self.last_keep_alive > 0
            and current_time - self.last_keep_alive >= self.keep_alive_interval
        ):
            ok_count = await self.ble_control.send_keep_alive()
            if ok_count < len(self.ble_control.client_list):
                print(
                    f"Keep-alive failed for {len(self.ble_control.client_list) - ok_count} devices"
                )
            self.last_keep_alive = current_time

    def execute_command(self, command, data=None, timeout=30):
        if not self.running:
            return (command, False, "Thread not running")

        self.command_queue.put((command, data))
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return (command, False, "No response")


class BleControl:
    def __init__(self, target_device_names):
        self.client_list = []
        self.device_list = []
        self.is_recording = False
        self.target_device_names = target_device_names
        self._notify_events = {}
        self._notify_data = {}

    async def connect(self):
        if len(self.client_list) == len(self.target_device_names):
            return len(self.client_list)
        ok_count = await self.discover_device()
        if ok_count < len(self.target_device_names):
            return ok_count

        try:
            for device in self.device_list:
                client = BleakClient(device.address)
                await client.connect()
                self.client_list.append(client)

            await self._setup_notifications()
            ok_count = await self.send_keep_alive()
            return ok_count
        except Exception:
            return 0

    async def discover_device(self):
        self.device_list = []
        devices = await BleakScanner.discover()

        for device in devices:
            if device.name and device.name in self.target_device_names:
                self.device_list.append(device)

        return len(self.device_list)

    def is_connected(self):
        return len(self.client_list) > 0 and all(
            client.is_connected for client in self.client_list
        )

    async def disconnect(self):
        success_code = len(self.client_list)
        if not self.is_connected():
            return success_code

        if self.is_recording:
            await self.stop_recording()

        for client in self.client_list:
            try:
                await client.stop_notify(BleData.RESPONSE_UUID)
                await client.disconnect()
            except Exception:
                print("Error during BLE disconnect")
                pass

        self.client_list.clear()
        self.device_list.clear()
        self.is_recording = False
        self._notify_events.clear()
        self._notify_data.clear()
        return success_code

    async def start_recording(self):
        return await self._send_command_to_all(
            BleData.COMMAND_UUID, BleData.START_RECORDING, set_recording=True
        )

    async def stop_recording(self):
        return await self._send_command_to_all(
            BleData.COMMAND_UUID, BleData.STOP_RECORDING, set_recording=False
        )

    async def _send_command_to_all(self, uuid, command, set_recording=None):
        ok_count = 0
        if not self.is_connected():
            return 0

        try:
            for client in self.client_list:
                await client.write_gatt_char(uuid, command, response=True)
                ok_count += 1

            if set_recording is not None:
                self.is_recording = set_recording
            return ok_count
        except Exception:
            return 0

    async def send_keep_alive(self):
        ok_count = 0
        if not self.is_connected():
            return 0

        # イベントとデータを初期化
        for client in self.client_list:
            addr = client.address
            self._notify_events[addr] = asyncio.Event()
            self._notify_data[addr] = None

        try:
            for client in self.client_list:
                await client.write_gatt_char(
                    BleData.SETTING_UUID, BleData.KEEP_ALIVE, response=True
                )

            ok_count = await self._wait_for_responses()
            return ok_count
        except Exception:
            return 0

    async def _wait_for_responses(self, timeout=3.0):
        ok_count = 0
        for client in self.client_list:
            addr = client.address
            try:
                await asyncio.wait_for(
                    self._notify_events[addr].wait(), timeout=timeout
                )
                data = self._notify_data.get(addr)

                if self._is_keep_alive_ok(data):
                    ok_count += 1

            except Exception:
                pass

        return ok_count

    def _is_keep_alive_ok(self, data):
        if not data:
            return False

        b = bytes(data)
        return (
            len(b) >= 3
            and b[0] == 0x02
            and b[1] == BleData.KEEP_ALIVE_ID
            and b[2] == BleData.OK
        )

    async def _setup_notifications(self):
        for client in self.client_list:
            addr = client.address

            async def handler(sender, data, addr=addr):
                self._notify_data[addr] = data
                if addr in self._notify_events:
                    self._notify_events[addr].set()

            await client.start_notify(BleData.RESPONSE_UUID, handler)

        return True
