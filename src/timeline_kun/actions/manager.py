from collections.abc import Mapping
from types import MappingProxyType
from typing import Protocol

from .config import ActionConfig


class Action(Protocol):
    """Operations exposed by actions; start/stop report success as a bool."""

    def connect(self) -> bool: ...

    def start(self) -> bool: ...

    def stop(self) -> bool: ...

    def get_status(self) -> str: ...

    def update_status(self) -> str: ...


class ActionManager:
    """Registry and operation dispatch, without device-specific knowledge."""

    def __init__(self, action_configs: Mapping[str, ActionConfig] | None = None) -> None:
        # Settings are retained for future action construction, not executed.
        self.action_configs: Mapping[str, ActionConfig] = MappingProxyType(
            dict(action_configs or {})
        )
        self._actions: dict[str, Action] = {}

    def register(self, name: str, action: Action) -> None:
        if not name:
            raise ValueError("Action name must not be empty")
        if name in self._actions:
            raise ValueError(f"Action already registered: {name}")
        self._actions[name] = action

    def get(self, name: str) -> Action:
        return self._actions[name]

    def connect(self, name: str) -> bool:
        return self.get(name).connect()

    def start(self, name: str) -> bool:
        return self.get(name).start()

    def stop(self, name: str) -> bool:
        return self.get(name).stop()

    def get_status(self, name: str) -> str:
        return self.get(name).get_status()

    def update_status(self, name: str) -> str:
        return self.get(name).update_status()
