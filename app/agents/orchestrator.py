from app.core.models import AgentResult
from app.agents.mail import MailAgent
from app.agents.calendar import CalendarAgent
from app.agents.meeting import MeetingAgent
from app.agents.task import TaskAgent
from app.agents.reminder import ReminderAgent
from app.agents.followup import FollowUpAgent
from app.agents.development import DevelopmentAgent
from app.agents.devops import DevOpsAgent
from app.agents.security import SecurityAgent
from app.agents.database import DatabaseAgent
from app.agents.documentation import DocumentationAgent
from app.agents.monitoring import MonitoringAgent
from app.agents.knowledge import KnowledgeAgent

class OrchestratorAgent:
    def __init__(self):
        self.agents={'mail':MailAgent(),'calendar':CalendarAgent(),'meeting':MeetingAgent(),'task':TaskAgent(),
          'reminder':ReminderAgent(),'followup':FollowUpAgent(),'development':DevelopmentAgent(),'devops':DevOpsAgent(),
          'security':SecurityAgent(),'database':DatabaseAgent(),'documentation':DocumentationAgent(),
          'monitoring':MonitoringAgent(),'knowledge':KnowledgeAgent()}
    def dispatch(self,name,request):
        a=self.agents.get(name)
        if not a: return AgentResult(agent='OrchestratorAgent',action=request.action,ok=False,message=f'Agente no registrado: {name}')
        return a.execute(request)
    def catalog(self):
        return {k:{'agent':v.name,'actions':{a:r.value for a,r in v.ACTION_RISKS.items()}} for k,v in self.agents.items()}
