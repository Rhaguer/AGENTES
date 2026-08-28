from __future__ import annotations
from fastapi import APIRouter,Request,Query
from fastapi.responses import HTMLResponse
from app.core.context import ExecutionContext,correlation_id_var,actor_var,role_var
from app.core.models import *
from app.core.errors import AppError
from app.core.approvals import approval_service
from app.core.rate_limit import action_rate_limiter
from app.core import store
from app.core.audit import audit
from app.runtime import orchestrator,command_router
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.connectors.github import GitHubConnector
from app.services.health import platform_health
from app.services.automations import automation_service
from app.services.reminders import reminder_service

router=APIRouter(prefix='/api/v1',tags=['API v1'])
COMMON={400:{'model':APIError},401:{'model':APIError},403:{'model':APIError},404:{'model':APIError},409:{'model':APIError},422:{'model':APIError},424:{'model':APIError},429:{'model':APIError},500:{'model':APIError},503:{'model':APIError}}

def ctx():return ExecutionContext(correlation_id=correlation_id_var.get(),actor=actor_var.get(),role=role_var.get())

def execute_agent(agent_name,request):
    a=orchestrator.agents.get(agent_name)
    if not a:raise AppError('AGENT_NOT_FOUND','Agent not found',404)
    risk=a.risk_for(request.action)
    if risk is None:raise AppError('ACTION_NOT_FOUND','Action not registered for agent',404)
    if risk in {RiskLevel.WRITE,RiskLevel.DANGEROUS}:action_rate_limiter.check_write(actor_var.get())
    return orchestrator.dispatch(agent_name,request,ctx())

@router.get('/version',response_model=VersionResponse,responses=COMMON)
def version():return VersionResponse(application='HAGUER Agent Platform',version='2.0.0',api_version='v1')

@router.get('/agents',response_model=AgentRegistryResponse,responses=COMMON)
def agents():
    items=orchestrator.catalog();return AgentRegistryResponse(agents=items,count=len(items))

@router.get('/agents/{agent_name}/health',response_model=AgentHealthResponse,responses=COMMON)
def agent_health(agent_name:str):return AgentHealthResponse(**orchestrator.agent_health(agent_name))

@router.post('/agents/{agent_name}/execute',response_model=AgentExecutionResponse,responses=COMMON)
def agent_execute(agent_name:str,request:AgentRequest):return execute_agent(agent_name,request)

@router.post('/command',response_model=CommandResponse,responses=COMMON)
def command(request:CommandRequest):
    resolution=command_router.route(request.text)
    ar=AgentRequest(action=resolution.action,payload=resolution.entities,approval_id=request.approval_id,approval_token=request.approval_token)
    execution=execute_agent(resolution.agent,ar)
    return CommandResponse(success=execution.success,resolution=resolution,execution=execution)

@router.post('/approvals/request',response_model=ApprovalRequestResponse,responses=COMMON)
def request_approval(item:ApprovalRequestCreate):
    agent=orchestrator.agents.get(item.agent)
    if not agent:raise AppError('AGENT_NOT_FOUND','Agent not found',404)
    risk=agent.risk_for(item.action)
    if risk is None:raise AppError('ACTION_NOT_FOUND','Action not registered for agent',404)
    orchestrator.policy.check_rbac(role_var.get(),risk,item.action)
    aid,expires=approval_service.request(requester=actor_var.get(),role=role_var.get(),agent=item.agent,action=item.action,risk_level=risk,target=item.target or agent.target_for(AgentRequest(action=item.action,payload=item.payload)),payload=item.payload)
    return ApprovalRequestResponse(approval_id=aid,status='pending',risk_level=risk,expires_at=expires,message='Approval request created')

@router.post('/approvals/{approval_id}/decision',response_model=ApprovalDecisionResponse,responses=COMMON)
def approval_decision(approval_id:str,item:ApprovalDecisionRequest):
    token,expires=approval_service.decide(approval_id,approver=actor_var.get(),role=role_var.get(),decision=item.decision)
    return ApprovalDecisionResponse(approval_id=approval_id,status='approved' if item.decision=='approve' else 'rejected',approval_token=token,expires_at=expires)

@router.get('/integrations',response_model=IntegrationsResponse,responses=COMMON)
def integrations():
    connectors=[MicrosoftGraphConnector(),GoogleWorkspaceConnector(),GitHubConnector()]
    return IntegrationsResponse(integrations=[c.status() for c in connectors])

@router.get('/health',response_model=HealthResponse,responses=COMMON)
def health():return platform_health(orchestrator)

@router.get('/audit',response_model=AuditListResponse,responses=COMMON)
def audit_list(limit:int=Query(100,ge=1,le=1000),actor:str|None=None,agent:str|None=None,action:str|None=None,risk_level:str|None=None,status:str|None=None,correlation_id:str|None=None,date_from:str|None=None,date_to:str|None=None):
    rows=store.list_audit(limit,actor,agent,action,risk_level,status,correlation_id,date_from,date_to);return AuditListResponse(events=[AuditEntry(**r) for r in rows],count=len(rows))

@router.get('/audit/{audit_id}',response_model=AuditEntry,responses=COMMON)
def audit_get(audit_id:str):
    row=store.get_audit(audit_id)
    if not row:raise AppError('AUDIT_NOT_FOUND','Audit entry not found',404)
    return AuditEntry(**row)

@router.get('/tasks',responses=COMMON)
def tasks(status:str|None=None):return {'success':True,'tasks':store.list_tasks(status)}

@router.post('/tasks/approval',response_model=ApprovalRequestResponse,responses=COMMON)
def task_approval(item:TaskCreate):
    return request_approval(ApprovalRequestCreate(agent='task',action='create_task',payload=item.model_dump()))

@router.get('/reminders',responses=COMMON)
def reminders(status:str|None=None):return {'success':True,'reminders':store.list_reminders(status)}

@router.get('/automations',responses=COMMON)
def automations():return {'success':True,'automations':store.list_automations(),'history':store.list_automation_history(limit=50)}

@router.post('/automations',responses={201:{'description':'Created'},**COMMON},status_code=201)
def create_automation(item:AutomationCreate):
    agent=orchestrator.agents.get(item.agent)
    if not agent:raise AppError('AGENT_NOT_FOUND','Agent not found',404)
    risk=agent.risk_for(item.action)
    if risk is None:raise AppError('ACTION_NOT_FOUND','Action not found',404)
    if risk not in {RiskLevel.READ,RiskLevel.PREPARE}:raise AppError('AUTOMATION_RISK_FORBIDDEN','Automations can only execute READ or PREPARE actions',403)
    aid=store.create_automation(item.name,item.agent,item.action,item.parameters,item.schedule,item.enabled,actor_var.get());audit({'actor':actor_var.get(),'agent':'Platform','action':'automation_create','risk':'WRITE','target':str(aid),'ok':True,'correlation_id':correlation_id_var.get()});automation_service.reload();return {'success':True,'id':aid}

@router.patch('/automations/{automation_id}',responses=COMMON)
def toggle_automation(automation_id:int,item:AutomationToggle):
    if not store.set_automation_enabled(automation_id,item.enabled):raise AppError('AUTOMATION_NOT_FOUND','Automation not found',404)
    audit({'actor':actor_var.get(),'agent':'Platform','action':'automation_toggle','risk':'WRITE','target':str(automation_id),'ok':True,'correlation_id':correlation_id_var.get()});automation_service.reload();return {'success':True}

@router.delete('/automations/{automation_id}',responses=COMMON)
def delete_automation(automation_id:int):
    if not store.delete_automation(automation_id):raise AppError('AUTOMATION_NOT_FOUND','Automation not found',404)
    audit({'actor':actor_var.get(),'agent':'Platform','action':'automation_delete','risk':'WRITE','target':str(automation_id),'ok':True,'correlation_id':correlation_id_var.get()});automation_service.reload();return {'success':True}
