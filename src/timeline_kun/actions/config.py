"""Validated action settings, independent of timer colors and runtime actions."""

import math
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ActionConfig:
    keyword: str
    start_lead_sec: float
    stop_delay_sec: float


@dataclass(frozen=True)
class WindowKeyActionConfig(ActionConfig):
    window_title: str
    start_hotkey: tuple[str, ...]
    stop_hotkey: tuple[str, ...]
    type: Literal["window_key"] = "window_key"


def parse_action_configs(actions: object) -> dict[str, ActionConfig]:
    """Parse the [actions] table without creating or executing external actions.

    All fields are required. Unknown types/fields fail explicitly rather than
    silently accepting misspelled or unsupported settings.
    """
    if not isinstance(actions, dict):
        raise ValueError("Config value 'actions' must be a table")
    configs: dict[str, ActionConfig] = {}
    for name, values in actions.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Action ID must be a non-empty string")
        path = f"actions.{name}"
        if not isinstance(values, dict):
            raise ValueError(f"Config value '{path}' must be a table")
        if values.get("type") != "window_key":
            raise ValueError(f"Config value '{path}.type' must be 'window_key'")
        fields = {
            "type", "keyword", "start_lead_sec", "stop_delay_sec",
            "window_title", "start_hotkey", "stop_hotkey",
        }
        unknown = values.keys() - fields
        if unknown:
            raise ValueError(f"Unknown config field in '{path}': {', '.join(sorted(unknown))}")

        def string(key):
            value = values.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Config value '{path}.{key}' must be a non-empty string")
            return value

        def seconds(key):
            value = values.get(key)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
                or (isinstance(value, float) and not math.isfinite(value))
            ):
                raise ValueError(f"Config value '{path}.{key}' must be finite non-negative seconds")
            return value

        def hotkey(key):
            value = values.get(key)
            if (
                not isinstance(value, list)
                or not value
                or any(not isinstance(key, str) or not key.strip() for key in value)
            ):
                raise ValueError(f"Config value '{path}.{key}' must be a non-empty string array")
            return tuple(value)

        configs[name] = WindowKeyActionConfig(
            keyword=string("keyword"),
            start_lead_sec=seconds("start_lead_sec"),
            stop_delay_sec=seconds("stop_delay_sec"),
            window_title=string("window_title"),
            start_hotkey=hotkey("start_hotkey"),
            stop_hotkey=hotkey("stop_hotkey"),
        )
    return configs
