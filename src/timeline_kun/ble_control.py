# ble_control.py
import asyncio
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from bleak import BleakClient, BleakScanner

Result = Tuple[str, int, str]
CommandHandler = Callable[[Optional[Any]], Awaitable[Result]]


@dataclass(frozen=True)
class BleData:
    COMMAND_UUID: str = "b5f90072-aa8d-11e3-9046-0002a5d5c51b"
    SETTING_UUID: str = "b5f90074-aa8d-11e3-9046-0002a5d5c51b"
    RESPONSE_UUID: str = "b5f90075-aa8d-11e3-9046-0002a5d5c51b"

    START_RECORDING: bytearray = field(
        default_factory=lambda: bytearray([0x03, 0x01, 0x01, 0x01])
    )
    STOP_RECORDING: bytearray = field(
        default_factory=lambda: bytearray([0x03, 0x01, 0x01, 0x00])
    )
    KEEP_ALIVE: bytearray = field(
        default_factory=lambda: bytearray([0x03, 0x5B, 0x01, 0x42])
    )

    KEEP_ALIVE_ID: int = 0x5B
    OK: int = 0x00
    RESP_PREFIX: int = 0x02


BLE = BleData()


@dataclass
class BLEMessage:
    raw: bytes
    msg_type: int
    msg_id: int
    status: int
    payload: bytes

    @classmethod
    def parse(cls, data: bytearray) -> Optional["BLEMessage"]:
        b = bytes(data)
        if len(b) < 3:
            return None
        return cls(raw=b, msg_type=b[0], msg_id=b[1], status=b[2], payload=b[3:])


NotifyHandler = Callable[[int, bytearray], Awaitable[None]]


class NotifyCenter:
    """デバイス単位の通知集約"""

    def __init__(self) -> None:
        self._queues: Dict[int, asyncio.Queue[BLEMessage]] = {}
        self._handler: Optional[NotifyHandler] = None

    def _queue_for(self, msg_id: int) -> asyncio.Queue[BLEMessage]:
        q = self._queues.get(msg_id)
        if q is None:
            q = asyncio.Queue(maxsize=16)
            self._queues[msg_id] = q
        return q

    def get_handler(self) -> NotifyHandler:
        if self._handler is None:

            async def handler(sender: int, data: bytearray) -> None:
                msg = BLEMessage.parse(data)
                if msg is None:
                    return
                await self._safe_put(self._queue_for(msg.msg_id), msg)

            self._handler = handler
        return self._handler

    async def _safe_put(self, q: asyncio.Queue, item: BLEMessage) -> None:
        try:
            q.put_nowait(item)
        except asyncio.QueueFull:
            try:
                _ = q.get_nowait()
            except asyncio.QueueEmpty:
                pass
            await q.put(item)

    async def wait_for(self, msg_id: int, timeout: float) -> Optional[BLEMessage]:
        q = self._queue_for(msg_id)
        try:
            return await asyncio.wait_for(q.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def clear(self, msg_id: Optional[int] = None) -> None:
        if msg_id is None:
            for q in self._queues.values():
                self._drain(q)
        else:
            q = self._queues.get(msg_id)
            if q:
                self._drain(q)

    @staticmethod
    def _drain(q: asyncio.Queue) -> None:
        try:
            while True:
                q.get_nowait()
        except asyncio.QueueEmpty:
            return


class DeviceSession:
    def __init__(self, address: str) -> None:
        self.address = address
        self.client = BleakClient(address)
        self.center = NotifyCenter()
        self.last_alive: bool = False

    async def connect_and_listen(self) -> bool:
        if not self.client.is_connected:
            print(f"connecting {self.address}")
            await self.client.connect()
        await self.client.start_notify(BLE.RESPONSE_UUID, self.center.get_handler())
        return True

    async def ensure_connected(self) -> bool:
        if self.client.is_connected:
            return True
        try:
            await self.connect_and_listen()
            print(f"reconnected {self.address}")
            return True
        except Exception as e:
            print(f"reconnect failed {self.address} {e}")
            return False

    async def write_command(self, uuid: str, payload: bytearray) -> bool:
        if not await self.ensure_connected():
            return False
        try:
            await self.client.write_gatt_char(uuid, payload, response=True)
            return True
        except Exception as e:
            print(f"write failed {self.address} {e}")
            return False

    async def keep_alive_roundtrip(self, timeout: float = 3.0) -> bool:
        self.center.clear(BLE.KEEP_ALIVE_ID)
        if not await self.write_command(BLE.SETTING_UUID, BLE.KEEP_ALIVE):
            self.last_alive = False
            return False
        msg = await self.center.wait_for(BLE.KEEP_ALIVE_ID, timeout=timeout)
        if msg and msg.status != BLE.OK:
            print(msg)
        ok = bool(msg and msg.msg_type == BLE.RESP_PREFIX and msg.status == BLE.OK)
        self.last_alive = ok
        return ok


class BleManager:
    def __init__(
        self, target_device_names: List[str], keep_alive_sec: float = 3.0
    ) -> None:
        self.target_device_names = target_device_names
        self.sessions: List[DeviceSession] = []
        self.keep_alive_sec = keep_alive_sec
        self._keep_task: Optional[asyncio.Task] = None
        self._running = False
        self.is_recording = False

    async def discover_and_connect(self) -> int:
        devices = await BleakScanner.discover(timeout=10)
        names = set(n for n in self.target_device_names if n)
        addrs: List[str] = []
        for d in devices:
            if d.name and d.name in names:
                print(f"found {d.name} {d.address}")
                addrs.append(d.address)

        self.sessions = [DeviceSession(addr) for addr in addrs]
        ok = 0
        for s in self.sessions:
            try:
                await s.connect_and_listen()
                ok += 1
            except Exception as e:
                print(f"connect failed {s.address} {e}")

        if ok:
            self.start_keep_alive_loop()
        return ok

    def start_keep_alive_loop(self) -> None:
        if self._keep_task is None or self._keep_task.done():
            self._running = True
            self._keep_task = asyncio.create_task(self._keep_loop())

    def stop_keep_alive_loop(self) -> None:
        self._running = False
        if self._keep_task:
            self._keep_task.cancel()

    async def _keep_loop(self) -> None:
        while self._running:
            await self.send_keep_alive_all()
            try:
                await asyncio.sleep(self.keep_alive_sec)
            except asyncio.CancelledError:
                break

    async def send_keep_alive_all(self) -> int:
        ok_cnt = 0
        for s in list(self.sessions):
            alive = await s.keep_alive_roundtrip(timeout=3.0)
            if not alive:
                # 再接続のチャンスをここで与える
                if await s.ensure_connected():
                    alive = await s.keep_alive_roundtrip(timeout=3.0)
            if alive:
                ok_cnt += 1
        #        print(f"keep alive {ok} of {len(self.sessions)}")
        if ok_cnt < len(self.sessions):
            print(f"[!] keep alive ok {ok_cnt} of {len(self.sessions)}")
        return ok_cnt

    async def start_recording_all(self) -> int:
        cnt = 0
        for s in self.sessions:
            if await s.write_command(BLE.COMMAND_UUID, BLE.START_RECORDING):
                cnt += 1
        self.is_recording = cnt > 0
        return cnt

    async def stop_recording_all(self) -> int:
        cnt = 0
        for s in self.sessions:
            if await s.write_command(BLE.COMMAND_UUID, BLE.STOP_RECORDING):
                cnt += 1
        self.is_recording = False if cnt > 0 else self.is_recording
        return cnt


class BleThread:
    """スレッドはキュー処理だけに限定"""

    def __init__(self) -> None:
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False
        self.command_q: "queue.Queue[Tuple[str, Optional[Any]]]" = queue.Queue()
        self.result_q: "queue.Queue[Result]" = queue.Queue()
        self.manager: Optional[BleManager] = None
        self.target_device_names: List[str] = [""]
        self._handlers: Dict[str, CommandHandler] = {
            "connect": self._h_connect,
            "record_start": self._h_start,
            "record_stop": self._h_stop,
            "status": self._h_status,
        }

    def set_target_device_names(self, names: List[str]) -> None:
        self.target_device_names = names

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        self.command_q.put(("__stop__", None))
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def execute_command(
        self, command: str, data: Optional[Any] = None, timeout: int = 30
    ) -> Result:
        if not self.running:
            return (command, 0, "thread not running")
        self.command_q.put((command, data))
        try:
            return self.result_q.get(timeout=timeout)
        except queue.Empty:
            return (command, 0, "timeout")

    def _run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.manager = BleManager(self.target_device_names, keep_alive_sec=3.0)
            self.loop.run_until_complete(self._loop())
        finally:
            if self.loop:
                self.loop.close()

    async def _loop(self) -> None:
        assert self.manager is not None
        while self.running:
            try:
                cmd, data = self.command_q.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue

            if cmd == "__stop__":
                self.manager.stop_keep_alive_loop()
                break

            handler = self._handlers.get(cmd)
            if handler is None:
                self.result_q.put((cmd, 0, "unknown"))
                continue
            try:
                res = await handler(data)
            except Exception as e:
                res = (cmd, 0, f"error {e}")
            self.result_q.put(res)

    # handlers
    async def _h_connect(self, _: Optional[Any]) -> Result:
        assert self.manager is not None
        self.manager.target_device_names = self.target_device_names
        ok = await self.manager.discover_and_connect()
        return ("connect", ok, "success" if ok else "failed")

    async def _h_start(self, _: Optional[Any]) -> Result:
        assert self.manager is not None
        ok = await self.manager.start_recording_all()
        return ("record_start", ok, "success" if ok else "failed")

    async def _h_stop(self, _: Optional[Any]) -> Result:
        assert self.manager is not None
        ok = await self.manager.stop_recording_all()
        return ("record_stop", ok, "success" if ok else "failed")

    async def _h_status(self, _: Optional[Any]) -> Result:
        assert self.manager is not None
        total = len(self.manager.sessions)
        alive_cnt = sum(1 for s in self.manager.sessions if s.last_alive)
        state = "recording" if self.manager.is_recording else "idle"
        return ("status", alive_cnt, f"{alive_cnt}/{total} {state}")
