from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
class DevOpsAgent(BaseAgent):
    name='DevOpsAgent'
    ACTION_RISKS={'check_services':RiskLevel.READ}
    def handle(self,r):

        import psutil
        if r.action=='check_services':
            names=[p.info for p in psutil.process_iter(['pid','name'])]
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Procesos obtenidos.',data={'processes':names[:500]})

        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')

