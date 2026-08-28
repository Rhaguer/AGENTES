from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import psutil
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.core import store
from app.core.audit import audit
from app.core.config import settings
from app.core.models import AgentRequest
from app.runtime import orchestrator
from app.services.automations import automation_service
from app.connectors.microsoft_graph import TOKEN_CACHE

router=APIRouter()
templates=Jinja2Templates(directory='app/templates')

NAV=[
 ('dashboard','/','Dashboard','DB'),('agents','/ui/agents','Agentes','AG'),
 ('integrations','/ui/integrations','Integraciones','IN'),('automations','/ui/automations','Automatizaciones','AU'),
 ('tasks','/ui/tasks','Tareas','TA'),('monitoring','/ui/monitoring','Monitoreo','MO'),
 ('audit','/ui/audit','Auditoría','AD'),('settings','/ui/settings','Configuración','CF'),
]

META={
 'orchestrator':('Orchestrator','Coordina, enruta y controla el trabajo entre agentes.','Core'),
 'mail':('Mail Agent','Outlook y Gmail: correo no leído y envío con aprobación.','Productividad'),
 'calendar':('Calendar Agent','Google Calendar y Outlook Calendar.','Productividad'),
 'meeting':('Teams Agent','Chats, equipos, canales, mensajes y reuniones de Teams.','Productividad'),
 'task':('Task Agent','Tareas persistentes y seguimiento de estados.','Productividad'),
 'reminder':('Reminder Agent','Recordatorios persistentes ejecutados por scheduler.','Productividad'),
 'followup':('Follow-up Agent','Seguimiento de pendientes y compromisos.','Productividad'),
 'development':('Development Agent','Git, GitHub, repositorios, tests y workflows.','Ingeniería'),
 'devops':('DevOps Agent','Procesos y servicios del sistema.','Ingeniería'),
 'security':('Security Agent','Auditoría, secretos y postura de seguridad.','Control'),
 'database':('Database Agent','Integridad y validaciones de bases de datos.','Ingeniería'),
 'documentation':('Documentation Agent','Inventario y control de documentación técnica.','Ingeniería'),
 'monitoring':('Monitoring Agent','CPU, RAM, disco, red y salud del equipo.','Control'),
 'knowledge':('Knowledge Agent','Búsqueda local de conocimiento técnico.','Ingeniería'),
}

class TaskCreate(BaseModel):
    title:str
    due_at:str|None=None
    source:str|None='ui'

class ReminderCreate(BaseModel):
    text:str
    run_at:str

class AutomationCreate(BaseModel):
    name:str
    agent:str
    action:str
    payload:dict[str,Any]=Field(default_factory=dict)
    interval_minutes:int=60
    enabled:bool=True

class AutomationToggle(BaseModel):
    enabled:bool


def ctx(request,page,title):
    return {'request':request,'page':page,'title':title,'app_name':settings.app_name,
            'version':'1.1.0','nav':NAV}

@router.get('/',response_class=HTMLResponse)
def dashboard(request:Request): return templates.TemplateResponse('dashboard.html',ctx(request,'dashboard','Dashboard'))
@router.get('/ui/agents',response_class=HTMLResponse)
def agents_page(request:Request): return templates.TemplateResponse('agents.html',ctx(request,'agents','Agentes'))
@router.get('/ui/integrations',response_class=HTMLResponse)
def integrations_page(request:Request): return templates.TemplateResponse('integrations.html',ctx(request,'integrations','Integraciones'))
@router.get('/ui/automations',response_class=HTMLResponse)
def automations_page(request:Request): return templates.TemplateResponse('automations.html',ctx(request,'automations','Automatizaciones'))
@router.get('/ui/tasks',response_class=HTMLResponse)
def tasks_page(request:Request): return templates.TemplateResponse('tasks.html',ctx(request,'tasks','Tareas y recordatorios'))
@router.get('/ui/monitoring',response_class=HTMLResponse)
def monitoring_page(request:Request): return templates.TemplateResponse('monitoring.html',ctx(request,'monitoring','Monitoreo'))
@router.get('/ui/audit',response_class=HTMLResponse)
def audit_page(request:Request): return templates.TemplateResponse('audit.html',ctx(request,'audit','Auditoría'))
@router.get('/ui/settings',response_class=HTMLResponse)
def settings_page(request:Request): return templates.TemplateResponse('settings.html',ctx(request,'settings','Configuración'))

def integration_status():
    gc=Path(settings.google_credentials_file); gt=Path(settings.google_token_file)
    return {
      'microsoft':{'configured':bool(settings.ms_client_id),'authenticated_cache':TOKEN_CACHE.exists(),
                   'teams_channels_enabled':settings.ms_enable_teams_channels},
      'google':{'configured':gc.exists(),'authenticated_cache':gt.exists(),
                'credentials_file':settings.google_credentials_file},
      'github':{'configured':bool(settings.github_token)},
      'local':{'configured':True},
    }

def read_audit(limit=100):
    p=Path('logs/audit.jsonl')
    if not p.exists(): return []
    limit=max(1,min(int(limit),1000)); rows=[]
    for line in reversed(p.read_text(encoding='utf-8',errors='ignore').splitlines()[-limit:]):
        try:
            item=json.loads(line)
            for key in list(item):
                if key.lower() in {'token','access_token','refresh_token','authorization','secret','client_secret'}:
                    item[key]='[REDACTED]'
            rows.append(item)
        except Exception: pass
    return rows

def agent_status(key,integrations):
    if key=='meeting':
        return 'online' if integrations['microsoft']['authenticated_cache'] else 'offline'
    if key in {'mail','calendar'}:
        return 'online' if (integrations['microsoft']['authenticated_cache'] or integrations['google']['authenticated_cache']) else 'warning'
    if key=='development':
        return 'online' if integrations['github']['configured'] else 'warning'
    return 'online'

@router.get('/api/dashboard/summary')
def dashboard_summary():
    catalog=orchestrator.catalog(); integrations=integration_status(); audit_rows=read_audit(200)
    agents=[{'key':'orchestrator','label':META['orchestrator'][0],'description':META['orchestrator'][1],
             'category':META['orchestrator'][2],'status':'online','actions':{'command':'PREPARE'}}]
    for key,info in catalog.items():
        label,desc,cat=META.get(key,(info['agent'],'','Agente'))
        agents.append({'key':key,'label':label,'description':desc,'category':cat,
                       'status':agent_status(key,integrations),'actions':info.get('actions',{})})
    active=sum(1 for a in agents if a['status']=='online')
    configured=sum(1 for k in ('microsoft','google','github') if integrations[k]['configured'])
    errors=sum(1 for x in audit_rows if x.get('ok') is False or x.get('status')=='error')
    return {'metrics':{'agents_total':len(agents),'agents_active':active,'integrations_configured':configured,
                       'recent_errors':errors,'tasks_pending':len(store.list_tasks('pending')),
                       'automations_enabled':sum(1 for x in store.list_automations() if x['enabled'])},
            'agents':agents,'integrations':integrations,'recent_audit':audit_rows[:8]}

@router.get('/api/agents/meta')
def api_agents_meta():
    out=[]
    for key,info in orchestrator.catalog().items():
        label,desc,cat=META.get(key,(info['agent'],'','Agente'))
        out.append({'key':key,'label':label,'description':desc,'category':cat,
                    'agent':info['agent'],'actions':info['actions']})
    return {'agents':out}

@router.get('/api/integrations')
def api_integrations(): return integration_status()

@router.get('/api/tasks')
def api_tasks(status:str|None=None): return {'tasks':store.list_tasks(status)}

@router.post('/api/tasks')
def api_create_task(item:TaskCreate):
    if not item.title.strip(): raise HTTPException(400,'El título es obligatorio.')
    result=orchestrator.dispatch('task',AgentRequest(action='create_task',
        payload={'title':item.title.strip(),'due_at':item.due_at,'source':item.source},approved=True))
    if not result.ok: raise HTTPException(400,result.message)
    return result

@router.patch('/api/tasks/{task_id}/complete')
def api_complete_task(task_id:int):
    result=orchestrator.dispatch('task',AgentRequest(action='complete_task',payload={'id':task_id},approved=True))
    if not result.ok: raise HTTPException(404,result.message)
    return result

@router.get('/api/reminders')
def api_reminders(status:str|None=None): return {'reminders':store.list_reminders(status)}

@router.post('/api/reminders')
def api_create_reminder(item:ReminderCreate):
    result=orchestrator.dispatch('reminder',AgentRequest(action='create_reminder',
        payload={'text':item.text.strip(),'run_at':item.run_at},approved=True))
    if not result.ok: raise HTTPException(400,result.message)
    return result

@router.get('/api/automations')
def api_automations(): return {'automations':store.list_automations()}

@router.post('/api/automations')
def api_create_automation(item:AutomationCreate):
    catalog=orchestrator.catalog()
    if item.agent not in catalog: raise HTTPException(400,'Agente no registrado.')
    risks=catalog[item.agent]['actions']
    if item.action not in risks: raise HTTPException(400,'Acción no registrada para ese agente.')
    if risks[item.action] in {'WRITE','DANGEROUS'}:
        raise HTTPException(400,'Una automatización programada solo puede usar READ/PREPARE. WRITE requiere aprobación interactiva.')
    aid=store.create_automation(item.name.strip() or f'{item.agent}:{item.action}',item.agent,item.action,
                                item.payload,max(1,item.interval_minutes),item.enabled)
    audit({'type':'automation_created','automation_id':aid,'agent':item.agent,'action':item.action,'ok':True})
    automation_service.reload()
    return {'ok':True,'id':aid}

@router.patch('/api/automations/{automation_id}/toggle')
def api_toggle_automation(automation_id:int,item:AutomationToggle):
    if not store.set_automation_enabled(automation_id,item.enabled): raise HTTPException(404,'Automatización no encontrada.')
    audit({'type':'automation_toggled','automation_id':automation_id,'enabled':item.enabled,'ok':True})
    automation_service.reload(); return {'ok':True}

@router.delete('/api/automations/{automation_id}')
def api_delete_automation(automation_id:int):
    if not store.delete_automation(automation_id): raise HTTPException(404,'Automatización no encontrada.')
    audit({'type':'automation_deleted','automation_id':automation_id,'ok':True})
    automation_service.reload(); return {'ok':True}

@router.get('/api/monitoring')
def api_monitoring():
    vm=psutil.virtual_memory(); root=Path.cwd().anchor or '/'; disk=psutil.disk_usage(root)
    return {'cpu_percent':psutil.cpu_percent(interval=.2),'memory_percent':vm.percent,
            'memory_total':vm.total,'memory_available':vm.available,
            'disk_percent':disk.percent,'disk_total':disk.total,'disk_free':disk.free,
            'process_count':len(psutil.pids()),'boot_time':psutil.boot_time()}

@router.get('/api/audit')
def api_audit(limit:int=100): return {'events':read_audit(limit)}

@router.get('/api/settings')
def api_settings():
    return {'app_name':settings.app_name,'app_env':settings.app_env,'host':settings.app_host,'port':settings.app_port,
            'timezone':settings.timezone,'require_approval_for_writes':settings.require_approval_for_writes,
            'microsoft_tenant':settings.ms_tenant_id,'teams_channels_enabled':settings.ms_enable_teams_channels,
            'google_credentials_file':settings.google_credentials_file,'google_token_file':settings.google_token_file,
            'database':str(store.DB),'audit_file':'logs/audit.jsonl','swagger':'/docs','openapi':'/openapi.json'}
