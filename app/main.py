from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request,Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core import store
from app.core.errors import AppError,app_error_handler,validation_error_handler,unhandled_error_handler
from app.core.middleware import CorrelationIdentityMiddleware,RateLimitMiddleware
from app.core.models import *
from app.core.context import ExecutionContext,correlation_id_var,actor_var,role_var
from app.api.v1 import router as v1_router,execute_agent,COMMON
from app.runtime import orchestrator,command_router
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.connectors.github import GitHubConnector
from app.services.automations import automation_service
from app.services.reminders import reminder_service
from app.services.health import platform_health
from app.ui.router import router as ui_router

@asynccontextmanager
async def lifespan(app):
    store.init_db();automation_service.bind(orchestrator);reminder_service.start();automation_service.start();yield;automation_service.stop();reminder_service.stop()

app=FastAPI(title=settings.app_name,version='2.0.0',description='HAGUER Agent Platform. Dashboard operativo en /. Swagger técnico en /docs.',lifespan=lifespan)
app.add_exception_handler(AppError,app_error_handler);app.add_exception_handler(RequestValidationError,validation_error_handler);app.add_exception_handler(Exception,unhandled_error_handler)
app.add_middleware(CorrelationIdentityMiddleware);app.add_middleware(RateLimitMiddleware)
_hosts=settings.trusted_host_list or ['*']
if settings.app_env in {'development','testing'} and 'testserver' not in _hosts:_hosts.append('testserver')
app.add_middleware(TrustedHostMiddleware,allowed_hosts=_hosts)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Content-Type','X-Correlation-ID','X-Actor','X-Role'])
app.mount('/static',StaticFiles(directory='app/static'),name='static');app.include_router(ui_router);app.include_router(v1_router)

# OAuth/Auth endpoints
@app.post('/auth/microsoft/device-login',responses=COMMON,tags=['Authentication'])
def microsoft_login():return MicrosoftGraphConnector().start_device_login()
@app.get('/auth/microsoft/device-login/status/{job_id}',responses=COMMON,tags=['Authentication'])
def microsoft_login_status(job_id:str):return MicrosoftGraphConnector().device_login_status(job_id)
@app.get('/auth/microsoft/me',responses=COMMON,tags=['Authentication'])
def microsoft_me():return MicrosoftGraphConnector().me()
@app.post('/auth/microsoft/disconnect',responses=COMMON,tags=['Authentication'])
def microsoft_disconnect():return MicrosoftGraphConnector().disconnect()

@app.post('/auth/google/login',responses=COMMON,tags=['Authentication'])
def google_login():return GoogleWorkspaceConnector().start_login()
@app.get('/auth/google/callback',response_class=HTMLResponse,include_in_schema=False)
def google_callback(state:str,code:str):
    GoogleWorkspaceConnector().finish_login(state,code)
    return '<!doctype html><html><body style="font-family:Segoe UI;background:#20242a;color:#eef;padding:40px"><h2>Google conectado correctamente</h2><p>Puedes cerrar esta pestaña y volver a HAGUER Agent Platform.</p></body></html>'
@app.get('/auth/google/me',responses=COMMON,tags=['Authentication'])
def google_me():return GoogleWorkspaceConnector().me()
@app.post('/auth/google/disconnect',responses=COMMON,tags=['Authentication'])
def google_disconnect():return GoogleWorkspaceConnector().disconnect()

@app.post('/auth/github/connect',responses=COMMON,tags=['Authentication'])
def github_connect():return GitHubConnector().connect()
@app.get('/auth/github/me',responses=COMMON,tags=['Authentication'])
def github_me():return GitHubConnector().me()
@app.post('/auth/github/disconnect',responses=COMMON,tags=['Authentication'])
def github_disconnect():return GitHubConnector().disconnect()

# Compatibility aliases. New integrations should use /api/v1/*.
@app.get('/version',response_model=VersionResponse,responses=COMMON,tags=['Compatibility'])
def version_compat():return VersionResponse(application='HAGUER Agent Platform',version='2.0.0',api_version='v1')
@app.get('/agents',response_model=AgentRegistryResponse,responses=COMMON,tags=['Compatibility'])
def agents_compat():
    items=orchestrator.catalog();return AgentRegistryResponse(agents=items,count=len(items))
@app.get('/agents/{agent_name}/health',response_model=AgentHealthResponse,responses=COMMON,tags=['Compatibility'])
def agent_health_compat(agent_name:str):return AgentHealthResponse(**orchestrator.agent_health(agent_name))
@app.post('/agents/{agent_name}/execute',response_model=AgentExecutionResponse,responses=COMMON,tags=['Compatibility'])
def execute_compat(agent_name:str,request:AgentRequest):return execute_agent(agent_name,request)
@app.post('/command',response_model=CommandResponse,responses=COMMON,tags=['Compatibility'])
def command_compat(request:CommandRequest):
    resolution=command_router.route(request.text);execution=execute_agent(resolution.agent,AgentRequest(action=resolution.action,payload=resolution.entities,approval_id=request.approval_id,approval_token=request.approval_token));return CommandResponse(success=execution.success,resolution=resolution,execution=execution)
@app.get('/integrations/status',response_model=IntegrationsResponse,responses=COMMON,tags=['Compatibility'])
def integrations_compat():return IntegrationsResponse(integrations=[MicrosoftGraphConnector().status(),GoogleWorkspaceConnector().status(),GitHubConnector().status()])
@app.get('/health',response_model=HealthResponse,responses=COMMON,tags=['Compatibility'])
def health_compat():return platform_health(orchestrator)
@app.get('/audit',response_model=AuditListResponse,responses=COMMON,tags=['Compatibility'])
def audit_compat(limit:int=100):
    rows=store.list_audit(limit);return AuditListResponse(events=[AuditEntry(**r) for r in rows],count=len(rows))
@app.get('/audit/{audit_id}',response_model=AuditEntry,responses=COMMON,tags=['Compatibility'])
def audit_get_compat(audit_id:str):
    row=store.get_audit(audit_id)
    if not row:raise AppError('AUDIT_NOT_FOUND','Audit entry not found',404)
    return AuditEntry(**row)
