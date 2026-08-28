from __future__ import annotations
import random,time
from dataclasses import dataclass
from threading import Lock
from app.core.config import settings
from app.core.errors import ProviderRateLimitError, ProviderUnavailableError, AppError

@dataclass
class BreakerState:
    failures:int=0
    opened_at:float|None=None

class CircuitBreaker:
    def __init__(self):self.states={};self.lock=Lock()
    def before(self,key):
        with self.lock:
            s=self.states.setdefault(key,BreakerState())
            if s.opened_at is not None:
                if time.time()-s.opened_at < settings.circuit_recovery_seconds:raise ProviderUnavailableError(key,'Circuit breaker is open')
                s.opened_at=None;s.failures=0
    def success(self,key):
        with self.lock:self.states[key]=BreakerState()
    def failure(self,key):
        with self.lock:
            s=self.states.setdefault(key,BreakerState());s.failures+=1
            if s.failures>=settings.circuit_failure_threshold:s.opened_at=time.time()

breaker=CircuitBreaker()

def retry_call(provider, fn):
    breaker.before(provider);last=None
    for attempt in range(settings.provider_max_retries):
        try:
            out=fn();breaker.success(provider);return out
        except ProviderRateLimitError:
            breaker.failure(provider);raise
        except AppError:
            raise
        except Exception as exc:
            last=exc;breaker.failure(provider)
            if attempt+1>=settings.provider_max_retries:break
            time.sleep(settings.provider_backoff_seconds*(2**attempt)+random.random()*0.15)
    if isinstance(last,ProviderUnavailableError):raise last
    raise ProviderUnavailableError(provider,str(last)[:500] if last else 'Provider unavailable')
