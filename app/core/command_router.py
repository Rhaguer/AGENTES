import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.models import AgentRequest


class DeterministicCommandRouter:
    """Router de lenguaje natural acotado y verificable.

    No intenta adivinar intenciones fuera de patrones explícitos. Para acciones
    complejas o ambiguas se debe usar el ejecutor visual o Swagger.
    """

    def _calendar_window(self, text: str):
        tz = ZoneInfo(settings.timezone)
        now = datetime.now(tz)
        if 'mañana' in text or 'manana' in text:
            day = (now + timedelta(days=1)).date()
        else:
            day = now.date()
        start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
        end = start + timedelta(days=1)
        return start.isoformat(), end.isoformat()

    def route(self, text, approved=False):
        raw = text.strip()
        t = raw.lower()

        if 'correo' in t or 'gmail' in t or 'outlook' in t:
            if any(x in t for x in ('no leído', 'no leido', 'no leídos', 'no leidos', 'nuevos', 'pendientes')):
                source = 'google' if ('gmail' in t or 'google' in t) else 'microsoft'
                return 'mail', AgentRequest(
                    action='list_unread',
                    payload={'source': source, 'limit': 20},
                    approved=approved,
                )

        if any(x in t for x in ('reuniones', 'eventos', 'calendario', 'agenda')) and any(x in t for x in ('hoy', 'mañana', 'manana')):
            source = 'google' if ('google' in t or 'gmail' in t) else 'microsoft'
            start, end = self._calendar_window(t)
            return 'calendar', AgentRequest(
                action='list_events',
                payload={'source': source, 'start': start, 'end': end, 'limit': 50},
                approved=approved,
            )

        if 'teams' in t and ('chat' in t or 'chats' in t):
            return 'meeting', AgentRequest(action='list_chats', payload={'limit': 30}, approved=approved)

        if 'teams' in t and any(x in t for x in ('equipos', 'teams disponibles', 'mis equipos')):
            return 'meeting', AgentRequest(action='list_teams', payload={}, approved=approved)

        if any(x in t for x in ('salud', 'estado')) and any(x in t for x in ('pc', 'sistema', 'equipo')):
            return 'monitoring', AgentRequest(action='system_health', approved=approved)

        if 'tareas' in t and ('pendiente' in t or 'pendientes' in t):
            return 'task', AgentRequest(action='list_tasks', payload={'status': 'pending'}, approved=approved)

        if 'recordatorios' in t and ('pendiente' in t or 'pendientes' in t):
            return 'reminder', AgentRequest(action='list_reminders', payload={'status': 'pending'}, approved=approved)

        if 'repositorios' in t and 'github' in t:
            return 'development', AgentRequest(action='github_repos', payload={'limit': 50}, approved=approved)

        if any(x in t for x in ('seguridad', 'postura de seguridad', 'controles de seguridad')):
            return 'security', AgentRequest(action='security_posture', payload={}, approved=approved)

        if any(x in t for x in ('procesos', 'servicios')) and any(x in t for x in ('pc', 'sistema', 'windows', 'equipo')):
            return 'devops', AgentRequest(action='check_services', payload={}, approved=approved)

        raise ValueError(
            'Comando natural no reconocido por el router determinístico. '
            'Usa /ui/agents o Swagger /docs para seleccionar explícitamente agente, acción y payload.'
        )
