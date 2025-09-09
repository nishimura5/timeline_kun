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


class BleThread:
    def __init__(self):
        self.thread = None
        self.loop = None
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = False
        self.ble_control = None
        self.last_keep_alive = 0
        self.keep_alive_interval = 10.0  # 10秒間隔
        self.target_device_names = [""]
        self.connection_status = "Disconnected"

    def set_target_device_names(self, names):
        self.target_device_names = names

    def start(self):
        if self.thread is None or not self.thread.is_alive():
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
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.ble_control = BleControl(self.target_device_names)
            self.loop.run_until_complete(self._command_loop())
        except Exception as e:
            print(f"BLE thread error: {e}")
        finally:
            if self.loop:
                self.loop.close()

    async def _command_loop(self):
        if not self.ble_control:
            return

        while self.running:
            try:
                command, data = self.command_queue.get_nowait()
            except queue.Empty:
                await self._check_keep_alive()
                await asyncio.sleep(0.1)
                continue

            print(f"BLE command: {command}, {data}")
            if command == "connect":
                result = await self.ble_control.connect()
                self.result_queue.put(("connect", result, "success?"))
                # 接続成功時にkeep_alive開始のタイマーをセット
                if result:
                    self.last_keep_alive = time.time()
            elif command == "disconnect":
                await self.ble_control.disconnect()
                self.result_queue.put(("disconnect", True, "success?"))
                # end keep_alive
                self.last_keep_alive = 0
                break
            elif command == "record_start":
                result = await self.ble_control.start_recording()
                self.result_queue.put(("record_start", result, "success?"))
            elif command == "record_stop":
                result = await self.ble_control.stop_recording()
                self.result_queue.put(("record_stop", result, "success?"))
            elif command == "keep_alive":
                await self.ble_control.send_keep_alive()
            else:
                print(f"Unknown command: {command}")

    async def _check_keep_alive(self):
        """keep_aliveが必要かチェックして送信"""
        current_time = time.time()

        if (
            self.ble_control
            and self.ble_control.is_connected()
            and self.last_keep_alive > 0
            and current_time - self.last_keep_alive >= self.keep_alive_interval
        ):
            await self.ble_control.send_keep_alive()
            self.last_keep_alive = current_time

    def execute_command(self, command, data=None, timeout=30):
        if not self.running:
            return (command, False, "Thread not running")

        self.command_queue.put((command, data))

        try:
            result = self.result_queue.get(timeout=timeout)
            return result
        except queue.Empty:
            return (command, False, "No response")


class BleControl:
    def __init__(self, target_device_names):
        self.active = False
        self.client_list = []
        self.device_list = []
        self.is_recording = False
        self.target_device_names = target_device_names
        # 各clientごとにnotification用のイベント・データ・状態を管理
        self._notify_events = {}  # client.address: asyncio.Event
        self._notify_data = {}    # client.address: bytes
        self._notify_setup = {}   # client.address: bool

    def load_config(self, config_path):
        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = f.read()
            self.active = True

    async def connect(self):
        print("Scanning for BLE devices...")
        await self.discover_device()
        if len(self.device_list) == 0:
            print("No device to connect")
            return False

        try:
            for device in self.device_list:
                print(f"Attempting to connect to {device.name} ({device.address})")
                self.client_list.append(BleakClient(device.address))
                await self.client_list[-1].connect()

            # 接続後にnotificationをセットアップ
            await self._setup_notifications()

            print("Connected and notifications set up")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    async def discover_device(self):
        self.device_list = []
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name and device.name in self.target_device_names:
                self.device_list.append(device)
                print(f"Found BLE device: {device.name}, {device.address}")
        if len(self.device_list) == 0:
            print(f"Target device '{self.target_device_names}' not found")

    def is_connected(self):
        connected_count = 0
        for client in self.client_list:
            if client.is_connected:
                connected_count += 1
        return connected_count == len(self.client_list) and connected_count > 0

    async def disconnect(self):
        if self.is_connected() and self.client_list:
            if self.is_recording:
                await self.stop_recording()

            try:
                for client in self.client_list:
                    addr = client.address
                    if self._notify_setup.get(addr, False):
                        await client.stop_notify(BleData.RESPONSE_UUID)
                        self._notify_setup[addr] = False
                    await client.disconnect()
            except Exception as e:
                print(f"Disconnect error: {e}")

        self.client_list = []
        self.device_list = []
        self.is_recording = False
        self._notify_events.clear()
        self._notify_data.clear()
        self._notify_setup.clear()
        print("Disconnected")

    async def start_recording(self):
        if not self.is_connected():
            print("Not connected")
            return False

        for client in self.client_list:
            await client.write_gatt_char(
                BleData.COMMAND_UUID, BleData.START_RECORDING, response=True
            )
        self.is_recording = True
        print("Started recording")
        return True

    async def stop_recording(self):
        if not self.is_connected():
            print("Not connected")
            return False
        for client in self.client_list:
            await client.write_gatt_char(
                BleData.COMMAND_UUID, BleData.STOP_RECORDING, response=True
            )
        self.is_recording = False
        print("Stopped recording")
        return True

    async def send_keep_alive(self):
        if not self.is_connected():
            print("Not connected - cannot send keep alive")
            return False

        try:
            # 各clientごとにイベント・データを初期化
            for client in self.client_list:
                addr = client.address
                self._notify_events[addr] = asyncio.Event()
                self._notify_data[addr] = None

            for client in self.client_list:
                await client.write_gatt_char(
                    BleData.SETTING_UUID, BleData.KEEP_ALIVE, response=True
                )
            print("Sent keep alive command...")

            # 各clientからの応答を待つ
            all_ok = True
            for client in self.client_list:
                addr = client.address
                try:
                    await asyncio.wait_for(self._notify_events[addr].wait(), timeout=3.0)
                    if self._notify_data[addr]:
                        print(f"[{addr}] Keep alive response: {self._notify_data[addr]}")
                    else:
                        print(f"[{addr}] No response data received")
                        all_ok = False
                except Exception as e:
                    print(f"[{addr}] Keep alive response timeout: {e}")
                    all_ok = False
            return all_ok
        except Exception as e:
            print(f"Failed to send keep alive: {e}")
            return False

    async def _setup_notifications(self):
        if not self.is_connected():
            return False

        try:
            for client in self.client_list:
                addr = client.address
                # clientごとにハンドラをラップ
                async def handler(sender, data, addr=addr):
                    self._notify_data[addr] = data
                    if self._notify_events.get(addr):
                        self._notify_events[addr].set()
                await client.start_notify(
                    BleData.RESPONSE_UUID, handler
                )
                self._notify_setup[addr] = True
            print("Notifications set up successfully")
            return True
        except Exception as e:
            print(f"Failed to set up notifications: {e}")
            for client in self.client_list:
                addr = client.address
                self._notify_setup[addr] = False
            return False

