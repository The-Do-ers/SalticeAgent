class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

class QueueTimeoutError(asyncio.TimeoutError):
    """Exception raised when queue operation times out."""
    pass