from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class RiskLevel(str, Enum):
    READ = 'READ'
    PREPARE = 'PREPARE'
    WRITE = 'WRITE'
    DANGEROUS = 'DANGEROUS'

class Role(str, Enum):
    READ_ONLY = 'READ_ONLY'
    USER = 'USER'
    OPERATOR = 'OPERATOR'
    ADMIN = 'ADMIN'

class APIErrorDetail(BaseModel):
    code: str
    message: str
    correlation_id: str
    details: dict[str, Any] = Field(default_factory=dict)

class APIError(BaseModel):
    success: bool = False
    error: APIErrorDetail

class AgentRequest(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    approval_id: str | None = None
    approval_token: str | None = None

class AgentExecutionResponse(BaseModel):
    success: bool
    agent: str
    action: str
    risk_level: RiskLevel
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    audit_id: str | None = None
    correlation_id: str
    requires_approval: bool = False
    approval_request: dict[str, Any] | None = None

class AgentActionInfo(BaseModel):
    name: str
    risk_level: RiskLevel
    description: str = ''

class AgentInfo(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    status: str
    version: str
    capabilities: list[str]
    actions: list[AgentActionInfo]
    integration: str | None = None
    health: str
    last_execution: str | None = None
    requires_auth: bool = False

class AgentRegistryResponse(BaseModel):
    success: bool = True
    agents: list[AgentInfo]
    count: int

class CommandRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    approval_id: str | None = None
    approval_token: str | None = None

class CommandResolution(BaseModel):
    intent: str
    agent: str
    action: str
    entities: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)

class CommandResponse(BaseModel):
    success: bool
    resolution: CommandResolution
    execution: AgentExecutionResponse

class IntegrationStatus(BaseModel):
    provider: str
    configured: bool
    authenticated: bool
    available: bool
    status: str
    last_check: str
    capabilities: list[str]
    message: str | None = None

class IntegrationsResponse(BaseModel):
    success: bool = True
    integrations: list[IntegrationStatus]

class HealthResponse(BaseModel):
    status: str
    api: str
    database: str
    microsoft: str
    google: str
    github: str
    agents: dict[str, str]
    uptime_seconds: float
    recent_errors: int = 0
    timestamp: str

class ApprovalRequestCreate(BaseModel):
    agent: str
    action: str
    target: str = ''
    payload: dict[str, Any] = Field(default_factory=dict)

class ApprovalRequestResponse(BaseModel):
    approval_id: str
    status: str
    risk_level: RiskLevel
    expires_at: str
    message: str

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern='^(approve|reject)$')

class ApprovalDecisionResponse(BaseModel):
    approval_id: str
    status: str
    approval_token: str | None = None
    expires_at: str | None = None

class AuditEntry(BaseModel):
    audit_id: str
    timestamp: str
    actor: str
    agent: str
    action: str
    risk_level: str
    target: str
    parameters_hash: str
    approval_id: str | None = None
    status: str
    duration_ms: int
    result: str | None = None
    error_code: str | None = None
    correlation_id: str

class AuditListResponse(BaseModel):
    success: bool = True
    events: list[AuditEntry]
    count: int

class VersionResponse(BaseModel):
    application: str
    version: str
    api_version: str

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    priority: str = Field(default='MEDIUM', pattern='^(LOW|MEDIUM|HIGH|CRITICAL)$')
    due_at: str | None = None
    assigned_to: str | None = None
    source: str = 'ui'

class ReminderCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    run_at: str
    priority: str = Field(default='MEDIUM', pattern='^(LOW|MEDIUM|HIGH|CRITICAL)$')

class AutomationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    agent: str
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    schedule: str = Field(description='interval:<minutes> or cron:<5-part-expression>')
    enabled: bool = True

class AutomationToggle(BaseModel):
    enabled: bool

class AgentHealthResponse(BaseModel):
    agent: str
    status: str
    integration: str | None = None
    requires_auth: bool
    authenticated: bool | None = None
    last_execution: str | None = None
    message: str | None = None
