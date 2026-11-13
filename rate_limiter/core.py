import collections
import queue
import time
from threading import Lock, Event
from typing import Any, Optional

class RateLimitedQueue:
    def __init__(self, max_ops: int = 5, time_window: float = 1.0):
        if max_ops <= 0:
            raise ValueError("max_ops must be greater than 0")
        if time_window <= 0:
            raise ValueError("time_window must be greater than 0")
        
        self.max_ops = max_ops
        self.time_window = time_window
        self._queue = queue.Queue()
        self._window = collections.deque(maxlen=max_ops * 2)  # Pre-allocate
        self._lock = Lock()
        self._ready = Event()
        self._ready.set()

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        self._queue.put(item, block=block, timeout=timeout)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        item = self._queue.get(block=block, timeout=timeout)

        with self._lock:
            now = time.monotonic()

            # Evict expired timestamps
            while self._window and (now - self._window[0] >= self.time_window):
                self._window.popleft()

            if len(self._window) >= self.max_ops:
                sleep_time = max(0, self.time_window - (now - self._window[0]))
                if sleep_time > 0:
                    self._ready.clear()
                    self._ready.wait(timeout=sleep_time)
                self._window.popleft()

            self._window.append(now)
            self._ready.set()

        return item

    def qsize(self) -> int:
        return self._queue.qsize()