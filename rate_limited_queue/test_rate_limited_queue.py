import asyncio
import pytest
from .core import RateLimitedQueue
from .exceptions import RateLimitError

@pytest.mark.asyncio
async def test_put_and_get():
    queue = RateLimitedQueue()
    await queue.put(1)
    item = await queue.get()
    assert item == 1

@pytest.mark.asyncio
async def test_rate_limiting():
    queue = RateLimitedQueue(max_ops=2, time_window=1.0)
    await queue.put(1)
    await queue.put(2)
    with pytest.raises(RateLimitError):
        await queue.put(3)

@pytest.mark.asyncio
async def test_task_done_and_join():
    queue = RateLimitedQueue()
    await queue.put(1)
    await queue.put(2)
    await queue.get()
    await queue.get()
    await queue.join()
