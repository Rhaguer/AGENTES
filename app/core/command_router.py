from __future__ import annotations
import re, unicodedata
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from app.core.config import settings
from app.core.errors import AppError
from app.core.models import CommandResolution


def normalize(text):
    text=unicodedata.normalize('NFD',text.lower())
    text=''.join(c for c in text if unicodedata.category(c)!='Mn')
    return re.sub(r'\s+',' ',text).strip()

class IntentClassifier:
    patterns={
      'mail_unread':[r'correos? (sin leer|no leidos?|nuevos?|pendientes?)',r'(revisa|ver|muestra|muestreme|tengo).*correos?',r'emails? pendientes?'],
      'calendar_list':[r'(agenda|calendario|reuniones?|eventos?).*(hoy|manana)',r'(que|cuales).*reuniones?'],
      'teams_chats':[r'teams.*chats?',r'mensajes?.*teams'],
      'tasks_pending':[r'tareas?.*pendientes?'],
      'system_health':[r'(salud|estado).*(pc|sistema|equipo)',r'(cpu|ram|disco).*estado'],
      'github_repos':[r'repositorios?.*github',r'github.*repositorios?'],
      'security_posture':[r'(seguridad|postura de seguridad|auditoria de seguridad)'],
    }
    def classify(self,text):
        t=normalize(text)
        for intent,pats in self.patterns.items():
            for p in pats:
                if re.search(p,t):return intent,0.92
        if any(w in t for w in ('correo','email','gmail','outlook')):return 'mail_unread',0.72
        raise AppError('COMMAND_NOT_RECOGNIZED','No se pudo resolver el comando de forma determinística',400)

class EntityExtractor:
    def extract(self,text,intent):
        t=normalize(text);e={}
        if intent=='mail_unread':e['source']='google' if ('gmail' in t or 'google' in t) else 'microsoft';e['limit']=20
        elif intent=='calendar_list':
            e['source']='google' if ('google' in t or 'gmail' in t) else 'microsoft'
            tz=ZoneInfo(settings.timezone);now=datetime.now(tz);day=(now+timedelta(days=1)).date() if 'manana' in t else now.date()
            start=datetime.combine(day,datetime.min.time(),tzinfo=tz);e.update(start=start.isoformat(),end=(start+timedelta(days=1)).isoformat(),limit=50)
        return e

class AgentResolver:
    mapping={'mail_unread':'mail','calendar_list':'calendar','teams_chats':'meeting','tasks_pending':'task','system_health':'monitoring','github_repos':'development','security_posture':'security'}
    def resolve(self,intent):return self.mapping[intent]

class ActionResolver:
    mapping={'mail_unread':'list_unread','calendar_list':'list_events','teams_chats':'list_chats','tasks_pending':'list_tasks','system_health':'system_health','github_repos':'github_repos','security_posture':'security_posture'}
    def resolve(self,intent):return self.mapping[intent]

class CommandRouter:
    def __init__(self):self.intent=IntentClassifier();self.entities=EntityExtractor();self.agents=AgentResolver();self.actions=ActionResolver()
    def route(self,text):
        intent,confidence=self.intent.classify(text);entities=self.entities.extract(text,intent)
        if intent=='tasks_pending':entities={'status':'pending'}
        return CommandResolution(intent=intent,agent=self.agents.resolve(intent),action=self.actions.resolve(intent),entities=entities,confidence=confidence)
