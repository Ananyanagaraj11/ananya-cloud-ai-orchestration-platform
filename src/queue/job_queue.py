"""In-memory/redis-compatible queue stub for local and Render demos."""

import json
from collections import deque

_queue: deque[str] = deque()


class JobQueue:
    def enqueue(self, payload: dict) -> str:
        job_id = payload.get("run_id", "unknown")
        _queue.append(json.dumps(payload))
        return job_id

    def dequeue(self) -> dict | None:
        if not _queue:
            return None
        return json.loads(_queue.popleft())

    def depth(self) -> int:
        return len(_queue)
