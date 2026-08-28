from __future__ import annotations
from fastapi import APIRouter,Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.core import store
from app.runtime import orchestrator
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.connectors.github import GitHubConnector
from app.services.health import platform_health

router=APIRouter(tags=['UI']);templates=Jinja2Templates(directory='app/templates')
NAV=[('dashboard','/','Dashboard','DB'),('agents','/ui/agents','Agentes','AG'),('integrations','/ui/integrations','Integraciones','IN'),('automations','/ui/automations','Automatizaciones','AU'),('tasks','/ui/tasks','Tareas','TA'),('monitoring','/ui/monitoring','Monitoreo','MO'),('audit','/ui/audit','Auditoría','AD'),('settings','/ui/settings','Configuración','CF')]

def ctx(request,page,title):return {'request':request,'page':page,'title':title,'app_name':settings.app_name,'version':'2.0.0','nav':NAV}

def render(request,page,title,template):return templates.TemplateResponse(request=request,name=template,context=ctx(request,page,title))

@router.get('/',response_class=HTMLResponse,include_in_schema=False)
def dashboard(request:Request):return render(request,'dashboard','Dashboard','dashboard.html')
@router.get('/ui/agents',response_class=HTMLResponse,include_in_schema=False)
def agents_page(request:Request):return render(request,'agents','Agentes','agents.html')
@router.get('/ui/integrations',response_class=HTMLResponse,include_in_schema=False)
def integrations_page(request:Request):return render(request,'integrations','Integraciones','integrations.html')
@router.get('/ui/automations',response_class=HTMLResponse,include_in_schema=False)
def automations_page(request:Request):return render(request,'automations','Automatizaciones','automations.html')
@router.get('/ui/tasks',response_class=HTMLResponse,include_in_schema=False)
def tasks_page(request:Request):return render(request,'tasks','Tareas y recordatorios','tasks.html')
@router.get('/ui/monitoring',response_class=HTMLResponse,include_in_schema=False)
def monitoring_page(request:Request):return render(request,'monitoring','Monitoreo','monitoring.html')
@router.get('/ui/audit',response_class=HTMLResponse,include_in_schema=False)
def audit_page(request:Request):return render(request,'audit','Auditoría','audit.html')
@router.get('/ui/settings',response_class=HTMLResponse,include_in_schema=False)
def settings_page(request:Request):return render(request,'settings','Configuración','settings.html')

@router.get('/api/ui/dashboard/summary',include_in_schema=False)
def dashboard_summary():
    catalog=orchestrator.catalog();health=platform_health(orchestrator);aud=store.list_audit(50)
    return {'metrics':{'agents_total':len(catalog),'agents_active':sum(1 for a in catalog if a.status=='ONLINE'),'integrations_connected':sum(1 for x in (health.microsoft,health.google,health.github) if x=='connected'),'recent_errors':sum(1 for x in aud if x['status']=='ERROR'),'tasks_pending':len(store.list_tasks('pending')),'automations_enabled':sum(1 for x in store.list_automations() if x['enabled'])},'agents':[a.model_dump(mode='json') for a in catalog],'health':health.model_dump(),'recent_audit':aud[:8]}

@router.get('/api/ui/settings',include_in_schema=False)
def settings_view():
    return {'app_name':settings.app_name,'version':'2.0.0','environment':settings.app_env,'host':settings.app_host,'port':settings.app_port,'timezone':settings.timezone,'default_role':settings.default_role,'approval_ttl_seconds':settings.approval_ttl_seconds,'approval_separation':settings.approval_require_different_actor,'rate_limits':{'auth':settings.rate_auth_per_minute,'command':settings.rate_command_per_minute,'agent':settings.rate_agent_per_minute,'write':settings.rate_write_per_minute},'swagger':'/docs','openapi':'/openapi.json','api':'/api/v1'}
