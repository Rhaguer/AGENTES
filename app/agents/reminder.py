from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
from app.core import store
from app.services.reminders import reminder_service

class ReminderAgent(BaseAgent):
    name='ReminderAgent'
    ACTION_RISKS={'list_reminders':RiskLevel.READ,'create_reminder':RiskLevel.WRITE}
    def handle(self,r):
        if r.action=='list_reminders':
            data=store.list_reminders(r.payload.get('status'))
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(data)} recordatorios.',data={'reminders':data})
        if r.action=='create_reminder':
            rid=reminder_service.schedule(r.payload['text'],r.payload['run_at'])
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Recordatorio programado.',data={'id':rid})
        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
