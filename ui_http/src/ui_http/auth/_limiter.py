"""Process-wide, bounded, atomic rolling windows over trusted socket peers."""

import math
import time
from collections import deque
from threading import Lock


class RateLimiter:
    def __init__(self, capacity: int = 10000) -> None:
        self.capacity = capacity
        self._buckets: dict[tuple[str, str], deque[float]] = {}
        self._lock = Lock()

    def reserve(self, operation: str, peer: str) -> int | None:
        window, limit = (300, 1) if operation == "register" else (60, 5)
        with self._lock:
            now = time.monotonic()
            # Capacity is bounded, so cleanup also has a bounded cost.
            for key in list(self._buckets):
                duration = 300 if key[0] == "register" else 60
                timestamps = self._buckets[key]
                while timestamps and timestamps[0] <= now - duration:
                    timestamps.popleft()
                if not timestamps:
                    del self._buckets[key]
            key = operation, peer
            bucket = self._buckets.get(key)
            if bucket is None:
                if len(self._buckets) >= self.capacity:
                    return max(
                        1,
                        math.ceil(
                            min(
                                timestamps[0] + (300 if name == "register" else 60) - now
                                for (name, _), timestamps in self._buckets.items()
                            )
                        ),
                    )
                bucket = self._buckets[key] = deque()
            if len(bucket) >= limit:
                return max(1, math.ceil(bucket[0] + window - now))
            bucket.append(now)
            return None


limiter = RateLimiter()
