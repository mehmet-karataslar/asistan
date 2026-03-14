from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable


@dataclass
class ScheduledTask:
    description: str
    delay_seconds: int


class TaskScheduler:
    def __init__(self, logger: Callable[[str], None]) -> None:
        self.logger = logger
        self._timers: list[threading.Timer] = []

    def schedule(self, delay_seconds: int, description: str, callback: Callable[[], None]) -> None:
        timer = threading.Timer(delay_seconds, callback)
        timer.daemon = True
        timer.start()
        self._timers.append(timer)
        self.logger(f"Zamanlandi: {description} ({delay_seconds} sn sonra)")

    def cancel_all(self) -> None:
        for timer in self._timers:
            timer.cancel()
        self._timers.clear()
