from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
from app.core import store

class TaskAgent(BaseAgent):
    name='TaskAgent'
    ACTION_RISKS={'list_tasks':RiskLevel.READ,'create_task':RiskLevel.WRITE,'complete_task':RiskLevel.WRITE}
    def handle(self,r):
        if r.action=='list_tasks':
            data=store.list_tasks(r.payload.get('status'))
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(data)} tareas.',data={'tasks':data})
        if r.action=='create_task':
            tid=store.create_task(r.payload['title'],r.payload.get('due_at'),r.payload.get('source'),r.payload.get('source_id'))
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Tarea creada.',data={'id':tid})
        if r.action=='complete_task':
            ok=store.complete_task(int(r.payload['id']))
            return AgentResult(agent=self.name,action=r.action,ok=ok,message='Tarea completada.' if ok else 'Tarea no encontrada.')
        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
