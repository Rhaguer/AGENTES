from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
class FollowUpAgent(BaseAgent):
    name='FollowUpAgent'
    ACTION_RISKS={'find_pending_tasks':RiskLevel.READ}
    def handle(self,r):

        from app.core import store
        if r.action=='find_pending_tasks':
            data=store.list_tasks('pending')
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(data)} tareas pendientes.',data={'tasks':data})

        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')

