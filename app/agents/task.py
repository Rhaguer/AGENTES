from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.core import store

class TaskAgent(BaseAgent):
    id='task';name='TaskAgent';display_name='Task Agent';description='Gestiona tareas persistentes con prioridad, responsable e historial.';integration='local';capabilities=['listar tareas','crear tarea','completar tarea','historial']
    ACTION_RISKS={'list_tasks':RiskLevel.READ,'create_task':RiskLevel.WRITE,'complete_task':RiskLevel.WRITE,'task_history':RiskLevel.READ}
    def handle(self,r,ctx):
        if r.action=='list_tasks':return {'tasks':store.list_tasks(r.payload.get('status'))}
        if r.action=='create_task':
            tid=store.create_task(r.payload['title'],ctx.actor,r.payload.get('priority','MEDIUM'),r.payload.get('due_at'),r.payload.get('assigned_to'),r.payload.get('source','agent'),r.payload.get('source_id'));return {'id':tid}
        if r.action=='complete_task':return {'completed':store.complete_task(int(r.payload['id']),ctx.actor)}
        if r.action=='task_history':return {'history':store.task_history(int(r.payload['id']))}
        raise ValueError('Unsupported action')
