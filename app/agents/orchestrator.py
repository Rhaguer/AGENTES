from __future__ import annotations
import time
from app.core.models import AgentRequest,AgentExecutionResponse,AgentInfo,AgentActionInfo,RiskLevel
from app.core.context import ExecutionContext
from app.core.security import PolicyEngine
from app.core.approvals import approval_service
from app.core.audit import audit_service
from app.core.errors import AppError
from app.core.utils import stable_hash
from app.core.structured_logging import log_event
from app.core import store
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.connectors.github import GitHubConnector
from app.agents.mail import MailAgent
from app.agents.calendar import CalendarAgent
from app.agents.meeting import MeetingAgent
from app.agents.task import TaskAgent
from app.agents.reminder import ReminderAgent
from app.agents.followup import FollowUpAgent
from app.agents.development import DevelopmentAgent
from app.agents.devops import DevOpsAgent
from app.agents.security import SecurityAgent
from app.agents.database import DatabaseAgent
from app.agents.documentation import DocumentationAgent
from app.agents.monitoring import MonitoringAgent
from app.agents.knowledge import KnowledgeAgent

class OrchestratorAgent:
    id='orchestrator';name='OrchestratorAgent';display_name='Orchestrator';version='2.0.0'
    def __init__(self):
        self.policy=PolicyEngine()
        self.agents={a.id:a for a in [MailAgent(),CalendarAgent(),MeetingAgent(),TaskAgent(),ReminderAgent(),FollowUpAgent(),DevelopmentAgent(),DevOpsAgent(),SecurityAgent(),DatabaseAgent(),DocumentationAgent(),MonitoringAgent(),KnowledgeAgent()]}
    def _integration_auth(self,agent):
        if not agent.requires_auth:return None
        if agent.integration=='microsoft':return MicrosoftGraphConnector().authenticated()
        if agent.integration=='microsoft/google':return MicrosoftGraphConnector().authenticated() or GoogleWorkspaceConnector().authenticated()
        return None
    def _health(self,agent):
        if agent.requires_auth:
            return 'healthy' if self._integration_auth(agent) else 'disconnected'
        return 'healthy'
    def catalog(self):
        out=[]
        for key,a in self.agents.items():
            out.append(AgentInfo(id=key,name=a.name,display_name=a.display_name,description=a.description,status='ONLINE' if self._health(a)=='healthy' else 'DEGRADED',version=a.version,capabilities=list(a.capabilities),actions=[AgentActionInfo(name=n,risk_level=r,description=a.ACTION_DESCRIPTIONS.get(n,'')) for n,r in a.ACTION_RISKS.items()],integration=a.integration,health=self._health(a),last_execution=store.last_execution_for(a.name),requires_auth=a.requires_auth))
        out.insert(0,AgentInfo(id='orchestrator',name=self.name,display_name=self.display_name,description='Detecta intención, resuelve agente/acción, aplica permisos, aprobación y auditoría.',status='ONLINE',version=self.version,capabilities=['routing','policy','approval','audit'],actions=[],integration='core',health='healthy',last_execution=store.last_execution_for(self.name),requires_auth=False))
        return out
    def agent_health(self,name):
        if name=='orchestrator':return {'agent':'orchestrator','status':'healthy','integration':'core','requires_auth':False,'authenticated':None,'last_execution':store.last_execution_for(self.name)}
        a=self.agents.get(name)
        if not a:raise AppError('AGENT_NOT_FOUND','Agent not found',404)
        auth=self._integration_auth(a)
        return {'agent':name,'status':self._health(a),'integration':a.integration,'requires_auth':a.requires_auth,'authenticated':auth,'last_execution':store.last_execution_for(a.name)}
    def dispatch(self,name,request:AgentRequest,context:ExecutionContext):
        a=self.agents.get(name)
        if not a:raise AppError('AGENT_NOT_FOUND','Agent not found',404)
        risk=a.risk_for(request.action)
        if risk is None:raise AppError('ACTION_NOT_FOUND','Action not registered for agent',404)
        self.policy.check_rbac(context.role,risk,request.action)
        target=a.target_for(request);ph=stable_hash(request.payload)
        if self.policy.requires_approval(risk):
            if not request.approval_id or not request.approval_token:
                raise AppError('APPROVAL_REQUIRED','This action requires a one-time approval',403,{'agent':name,'action':request.action,'risk_level':risk.value,'target':target})
            approval_service.consume(approval_id=request.approval_id,token=request.approval_token,actor=context.actor,agent=name,action=request.action,risk_level=risk,target=target,payload=request.payload)
        started=time.perf_counter();status='SUCCESS';error_code=None;data={};message='Operation completed'
        try:
            data=a.handle(request,context) or {}
            if isinstance(data,dict) and data.get('returncode') not in (None,0):status='ERROR';message='Operation returned a non-zero status'
        except AppError as exc:
            status='ERROR';error_code=exc.code;message=exc.message
            aid=audit_service.record(actor=context.actor,agent=a.name,action=request.action,risk_level=risk.value,target=target,parameters_hash=ph,approval_id=request.approval_id,status=status,duration_ms=int((time.perf_counter()-started)*1000),result=None,error_code=error_code,correlation_id=context.correlation_id)
            raise
        except Exception as exc:
            status='ERROR';error_code='AGENT_EXECUTION_ERROR';message=str(exc)[:500]
            aid=audit_service.record(actor=context.actor,agent=a.name,action=request.action,risk_level=risk.value,target=target,parameters_hash=ph,approval_id=request.approval_id,status=status,duration_ms=int((time.perf_counter()-started)*1000),result={'message':message},error_code=error_code,correlation_id=context.correlation_id)
            raise AppError(error_code,message,424) from exc
        duration=int((time.perf_counter()-started)*1000)
        aid=audit_service.record(actor=context.actor,agent=a.name,action=request.action,risk_level=risk.value,target=target,parameters_hash=ph,approval_id=request.approval_id,status=status,duration_ms=duration,result=data,error_code=error_code,correlation_id=context.correlation_id)
        log_event(correlation_id=context.correlation_id,actor=context.actor,agent=a.name,action=request.action,provider=a.integration,risk_level=risk.value,duration_ms=duration,status=status,error_code=error_code)
        return AgentExecutionResponse(success=status=='SUCCESS',agent=a.name,action=request.action,risk_level=risk,message=message,data=data,audit_id=aid,correlation_id=context.correlation_id)
