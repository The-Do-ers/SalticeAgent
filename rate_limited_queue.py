import time
import threading
from collections import deque


class RateLimitedQueue:
    """
    A rate-limited queue that allows at most `max_ops_per_second` operations per second.
    
    Uses a sliding window approach to track operation timestamps.
    Thread-safe via a lock.
    """

    def __init__(self, max_ops_per_second: int = 5):
        if max_ops_per_second <= 0:
            raise ValueError("max_ops_per_second must be positive")
        self.max_ops = max_ops_per_second
        self._timestamps = deque()  # timestamps of recent operations
        self._lock = threading.Lock()

    def _wait_if_needed(self):
        """Block until an operation slot is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                # Remove timestamps older than 1 second
                window_start = now - 1.0
                while self._timestamps and self._timestamps[0] <= window_start:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.max_ops:
                    # Slot available
                    self._timestamps.append(now)
                    return

                # Need to wait until the oldest timestamp in window expires
                oldest = self._timestamps[0]
                sleep_time = oldest + 1.0 - now

            # Sleep outside the lock to allow other threads to proceed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def enqueue(self, item):
        """Add an item to the queue, respecting the rate limit."""
        self._wait_if_needed()
        # In a real queue, we'd store the item here.
        # For this implementation, we track the operation.
        return True

    def dequeue(self):
        """Remove and return an item from the queue, respecting the rate limit."""
        self._wait_if_needed()
        return None  # Placeholder for actual queue item

    def peek(self):
        """Look at the front item without removing it, respecting the rate limit."""
        self._wait_if_needed()
        return None

    def size(self):
        """Return the number of items in the queue (no rate limit for read-only)."""
        return 0

    def is_empty(self):
        """Check if queue is empty (no rate limit for read-only)."""
        return True


class RateLimitedQueueFull(RateLimitedQueue):
    """
    Extended version that actually stores items in a deque.
    """

    def __init__(self, max_ops_per_second: int = 5, max_size: int = 100):
        super().__init__(max_ops_per_second)
        self._items = deque()
        self._max_size = max_size

    def enqueue(self, item):
        self._wait_if_needed()
        with self._lock:
            if len(self._items) >= self._max_size:
                raise OverflowError("Queue is full")
            self._items.append(item)
        return True

    def dequeue(self):
        self._wait_if_needed()
        with self._lock:
            if not self._items:
                return None
            return self._items.popleft()

    def peek(self):
        self._wait_if_needed()
        with self._lock:
            if self._items:
                return self._items[0]
            return None

    def size(self):
        with self._lock:
            return len(self._items)

    def is_empty(self):
        with self._lock:
            return len(self._items) == 0
