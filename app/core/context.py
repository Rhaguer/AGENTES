from __future__ import annotations
from contextvars import ContextVar
from dataclasses import dataclass
from app.core.models import Role

correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')
actor_var: ContextVar[str] = ContextVar('actor', default='local-user')
role_var: ContextVar[Role] = ContextVar('role', default=Role.READ_ONLY)

@dataclass(slots=True)
class ExecutionContext:
    correlation_id: str
    actor: str
    role: Role
