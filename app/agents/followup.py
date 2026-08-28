from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.core import store
class FollowUpAgent(BaseAgent):
    id='followup';name='FollowUpAgent';display_name='Follow-up Agent';description='Consolida tareas y recordatorios pendientes para seguimiento.';integration='local';capabilities=['pendientes','seguimiento']
    ACTION_RISKS={'find_pending':RiskLevel.READ,'prepare_followup':RiskLevel.PREPARE}
    def handle(self,r,ctx):
        if r.action=='find_pending':return {'tasks':store.list_tasks('pending'),'reminders':store.list_reminders('pending')}
        if r.action=='prepare_followup':return {'prepared':True,'target':r.payload.get('target'),'message':r.payload.get('message','')}
        raise ValueError('Unsupported action')
