import re
from datetime import datetime,timedelta,timezone
from app.core.models import AgentRequest

class DeterministicCommandRouter:
    def route(self,text,approved=False):
        t=text.strip().lower()
        if 'correo' in t and ('no leído' in t or 'no leido' in t or 'nuevos' in t):
            source='google' if 'gmail' in t else 'microsoft'
            return 'mail',AgentRequest(action='list_unread',payload={'source':source,'limit':20},approved=approved)
        if ('salud' in t or 'estado' in t) and ('pc' in t or 'sistema' in t or 'equipo' in t):
            return 'monitoring',AgentRequest(action='system_health',approved=approved)
        if 'tareas' in t and ('pendiente' in t or 'pendientes' in t):
            return 'task',AgentRequest(action='list_tasks',payload={'status':'pending'},approved=approved)
        if 'repositorios' in t and 'github' in t:
            return 'development',AgentRequest(action='github_repos',approved=approved)
        raise ValueError('Comando natural no reconocido por el router determinístico. Usa la API /agents/{agent}/execute para acciones explícitas.')
