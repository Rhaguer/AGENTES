from __future__ import annotations
import time, uuid
from collections import defaultdict, deque
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import settings
from app.core.context import actor_var, correlation_id_var, role_var
from app.core.models import Role
from app.core.errors import error_body
from app.core.structured_logging import log_event

class CorrelationIdentityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        cid=request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        actor=request.headers.get('X-Actor') or settings.default_actor
        role_raw=(request.headers.get('X-Role') or settings.default_role).upper()
        try:role=Role(role_raw)
        except ValueError:role=Role.READ_ONLY
        tok1=correlation_id_var.set(cid);tok2=actor_var.set(actor);tok3=role_var.set(role)
        started=time.perf_counter()
        try:
            response=await call_next(request)
            response.headers['X-Correlation-ID']=cid
            log_event(correlation_id=cid,actor=actor,method=request.method,path=request.url.path,status=response.status_code,duration_ms=int((time.perf_counter()-started)*1000))
            return response
        finally:
            correlation_id_var.reset(tok1);actor_var.reset(tok2);role_var.reset(tok3)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app);self.buckets=defaultdict(deque)
    def limit_for(self,path):
        if path.startswith('/auth/'):return settings.rate_auth_per_minute
        if path.endswith('/command') or path=='/command':return settings.rate_command_per_minute
        if '/agents/' in path and path.endswith('/execute'):return settings.rate_agent_per_minute
        return None
    async def dispatch(self,request,call_next):
        limit=self.limit_for(request.url.path)
        if limit:
            host=request.client.host if request.client else 'local';key=(host,request.url.path)
            now=time.time();q=self.buckets[key]
            while q and q[0] <= now-60:q.popleft()
            if len(q)>=limit:
                return JSONResponse(status_code=429,content=error_body('RATE_LIMIT_EXCEEDED','Too many requests'))
            q.append(now)
        return await call_next(request)
