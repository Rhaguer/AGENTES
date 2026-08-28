from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    READ='READ'
    PREPARE='PREPARE'
    WRITE='WRITE'
    DANGEROUS='DANGEROUS'

class AgentRequest(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False

class AgentResult(BaseModel):
    agent: str
    action: str
    ok: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False

class CommandRequest(BaseModel):
    text: str
    approved: bool = False
