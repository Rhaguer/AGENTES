from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.core import store
from app.services.reminders import reminder_service

class ReminderAgent(BaseAgent):
    id='reminder';name='ReminderAgent';display_name='Reminder Agent';description='Recordatorios persistentes y programados.';integration='local';capabilities=['listar recordatorios','crear recordatorio']
    ACTION_RISKS={'list_reminders':RiskLevel.READ,'create_reminder':RiskLevel.WRITE}
    def handle(self,r,ctx):
        if r.action=='list_reminders':return {'reminders':store.list_reminders(r.payload.get('status'))}
        if r.action=='create_reminder':return {'id':reminder_service.schedule(r.payload['text'],r.payload['run_at'],ctx.actor,r.payload.get('priority','MEDIUM'))}
        raise ValueError('Unsupported action')
