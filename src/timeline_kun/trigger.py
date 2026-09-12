import threading
import time

from .actions import ActionManager


class Trigger:
    """Start a named action on keyword entry and stop it after keyword exit."""

    def __init__(
        self,
        action_manager: ActionManager,
        action_name: str,
        keyword: str,
        offset_sec: int = 5,
        delay_sec: float = 1,
    ) -> None:
        # Fail early for an invalid binding, before the timeline starts.
        action_manager.get(action_name)
        self.action_manager = action_manager
        self.action_name = action_name
        self.triggered_in = False
        self.offset_sec = offset_sec
        self.keyword = keyword
        self.delay_sec = delay_sec

    def set_keyword(self, keyword):
        self.keyword = keyword

    def set_delay_sec(self, delay_sec):
        self.delay_sec = delay_sec

    def trigger_in(self, title):
        if self.keyword in title and self.triggered_in is False:
            self.triggered_in = True
            return self.action_manager.start(self.action_name)
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
        self.action_manager.stop(self.action_name)

    def get_triggered(self):
        return self.triggered_in
