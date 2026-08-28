from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.models import AgentRequest, CommandRequest
from app.core.store import init_db
from app.runtime import orchestrator, command_router
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.connectors.github import GitHubConnector
from app.services.reminders import reminder_service
from app.services.automations import automation_service
from app.ui.router import router as ui_router, integration_status

@asynccontextmanager
async def lifespan(app):
    init_db()
    automation_service.bind(orchestrator)
    reminder_service.start()
    automation_service.start()
    yield
    automation_service.stop()
    reminder_service.stop()

app=FastAPI(
    title=settings.app_name,
    version='1.1.0',
    description='API técnica de HAGUER Agent Platform. Dashboard en /. Swagger permanece en /docs.',
    lifespan=lifespan,
)
app.mount('/static',StaticFiles(directory='app/static'),name='static')
app.include_router(ui_router)

@app.get('/agents')
def agents(): return orchestrator.catalog()

@app.post('/agents/{agent_name}/execute')
def execute(agent_name:str,request:AgentRequest): return orchestrator.dispatch(agent_name,request)

@app.post('/command')
def command(request:CommandRequest):
    try:
        name,ar=command_router.route(request.text,request.approved)
        return orchestrator.dispatch(name,ar)
    except ValueError as exc:
        raise HTTPException(400,str(exc))

@app.get('/integrations/status')
def integrations(): return integration_status()

@app.post('/auth/microsoft/device-login')
def microsoft_login(): return MicrosoftGraphConnector().start_device_login()

@app.get('/auth/microsoft/device-login/status/{job_id}')
def microsoft_login_status(job_id:str): return MicrosoftGraphConnector().device_login_status(job_id)

@app.post('/auth/google/login')
def google_login(): return GoogleWorkspaceConnector().login()

@app.get('/auth/microsoft/me')
def microsoft_me(): return MicrosoftGraphConnector().me()

@app.get('/auth/google/me')
def google_me(): return GoogleWorkspaceConnector().me()

@app.get('/auth/github/me')
def github_me(): return GitHubConnector().me()
