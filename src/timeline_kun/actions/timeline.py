"""Configured actions driven by timer ticks, without background stop threads."""

import logging
import time
from dataclasses import dataclass, field


@dataclass
class ActionState:
    intervals: list = field(default_factory=list)
    entered: bool = False
    active: bool = False
    stop_at: float | None = None


class ActionTimeline:
    def __init__(self, manager, stages, report=None, clock=time.monotonic):
        self.manager = manager
        self.report = report
        self.clock = clock
        self.states = {}
        for name, config in manager.action_configs.items():
            state = ActionState()
            for stage in stages:
                if config.keyword not in stage["instruction"]:
                    continue
                start = stage["start_dt"].total_seconds() - config.start_lead_sec
                end = stage["end_dt"].total_seconds()
                if state.intervals and start <= state.intervals[-1][1]:
                    previous_start, previous_end = state.intervals[-1]
                    state.intervals[-1] = (previous_start, max(previous_end, end))
                else:
                    state.intervals.append((start, end))
            self.states[name] = state

    def _execute(self, name, operation):
        try:
            success = bool(getattr(self.manager, operation)(name))
            detail = self.manager.get_status(name)
        except Exception as exc:
            success, detail = False, str(exc)
        logging.getLogger(__name__).log(
            logging.INFO if success else logging.ERROR,
            "Action %s %s: %s (%s)", name, operation, success, detail,
        )
        if self.report:
            try:
                self.report(name, operation, success, detail)
            except Exception:
                logging.getLogger(__name__).exception("Could not write action log")
        return success

    def update(self, elapsed):
        now = self.clock()
        for name, state in self.states.items():
            wanted = any(start <= elapsed < end for start, end in state.intervals)
            if wanted:
                state.stop_at = None
                if not state.entered and not state.active:
                    state.active = self._execute(name, "start")
                state.entered = True
            else:
                if state.entered and state.active:
                    state.stop_at = now + self.manager.action_configs[name].stop_delay_sec
                state.entered = False
                if state.stop_at is not None and now >= state.stop_at:
                    self._execute(name, "stop")
                    state.active = False
                    state.stop_at = None

    def stop_all(self):
        for name, state in self.states.items():
            if state.active:
                self._execute(name, "stop")
            state.active = state.entered = False
            state.stop_at = None
