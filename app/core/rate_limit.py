from __future__ import annotations
import time
from collections import defaultdict,deque
from threading import Lock
from app.core.config import settings
from app.core.errors import AppError

class ActionRateLimiter:
    def __init__(self):self.data=defaultdict(deque);self.lock=Lock()
    def check_write(self,actor):
        now=time.time();key=('write',actor)
        with self.lock:
            q=self.data[key]
            while q and q[0]<=now-60:q.popleft()
            if len(q)>=settings.rate_write_per_minute:raise AppError('WRITE_RATE_LIMIT_EXCEEDED','Too many WRITE/DANGEROUS actions',429)
            q.append(now)
action_rate_limiter=ActionRateLimiter()
