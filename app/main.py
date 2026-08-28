from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.core.models import AgentRequest,CommandRequest
from app.core.store import init_db
from app.agents.orchestrator import OrchestratorAgent
from app.core.command_router import DeterministicCommandRouter
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.connectors.github import GitHubConnector
from app.services.reminders import reminder_service

@asynccontextmanager
async def lifespan(app):
    init_db(); reminder_service.start(); yield; reminder_service.stop()

app=FastAPI(title=settings.app_name,version='1.0.0',lifespan=lifespan)
o=OrchestratorAgent(); router=DeterministicCommandRouter()

@app.get('/',response_class=HTMLResponse)
def home():
    return """<!doctype html><html><head><meta charset="utf-8"><title>HAGUER Agent Platform</title>
<style>body{font-family:Segoe UI,Arial;max-width:1000px;margin:40px auto;padding:0 20px}code{background:#eee;padding:2px 5px}.ok{color:#176b2c}</style></head><body>
<h1>HAGUER Agent Platform REAL</h1><p class="ok">API activa.</p><p>Swagger: <a href="/docs">/docs</a></p>
<p>Agentes: <a href="/agents">/agents</a> · Estado: <a href="/integrations/status">/integrations/status</a></p>
<p>Microsoft login: POST <code>/auth/microsoft/device-login</code> · Google login: POST <code>/auth/google/login</code></p>
</body></html>"""

@app.get('/agents')
def agents(): return o.catalog()

@app.post('/agents/{agent_name}/execute')
def execute(agent_name:str,request:AgentRequest): return o.dispatch(agent_name,request)

@app.post('/command')
def command(request:CommandRequest):
    try: name,ar=router.route(request.text,request.approved); return o.dispatch(name,ar)
    except ValueError as e: raise HTTPException(400,str(e))

@app.get('/integrations/status')
def integrations():
    ms={'configured':bool(settings.ms_client_id),'teams_channels_enabled':settings.ms_enable_teams_channels}
    google={'credentials_file':settings.google_credentials_file,'token_file':settings.google_token_file}
    github={'configured':bool(settings.github_token)}
    return {'microsoft':ms,'google':google,'github':github}

@app.post('/auth/microsoft/device-login')
def microsoft_login(): return MicrosoftGraphConnector().login_device_code()

@app.post('/auth/google/login')
def google_login(): return GoogleWorkspaceConnector().login()

@app.get('/auth/microsoft/me')
def microsoft_me(): return MicrosoftGraphConnector().me()

@app.get('/auth/github/me')
def github_me(): return GitHubConnector().me()
