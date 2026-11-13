import asyncio
import time
from typing import Any, Optional

class RateLimitedQueue:
    def __init__(self, max_ops: int = 5, time_window: float = 1.0, maxsize: Optional[int] = None):
        if max_ops <= 0 or time_window <= 0:
            raise ValueError("max_ops and time_window must be positive values.")
        
        self.max_ops = float(max_ops)
        self.fill_rate = max_ops / time_window
        self.tokens = float(max_ops)
        self.last_refill = time.perf_counter()

        self._queue = asyncio.Queue(maxsize=maxsize)
        self._lock = asyncio.Lock()

    async def put(self, item: Any) -> None:
        await self._queue.put(item)

    async def _consume_token(self) -> None:
        async with self._lock:
            now = time.perf_counter()
            elapsed = now - self.last_refill
            self.last_refill = now

            self.tokens = min(self.max_ops, self.tokens + elapsed * self.fill_rate)

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return

            required_tokens = 1.0 - self.tokens
            wait_time = required_tokens / self.fill_rate
            await asyncio.sleep(wait_time)

    async def get(self) -> Any:
        item = await self._queue.get()
        await self._consume_token()
        self._queue.task_done()
        return item

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()