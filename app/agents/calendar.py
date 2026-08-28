from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.core.config import settings

class CalendarAgent(BaseAgent):
    name='CalendarAgent'
    ACTION_RISKS={'list_events':RiskLevel.READ,'create_event':RiskLevel.WRITE}
    def handle(self,r):
        src=r.payload.get('source','microsoft').lower()
        c=GoogleWorkspaceConnector() if src in {'google','gmail'} else MicrosoftGraphConnector()
        if r.action=='list_events':
            data=c.calendar_events(r.payload['start'],r.payload['end'],r.payload.get('limit',50))
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(data)} eventos obtenidos.',data={'source':src,'events':data})
        if r.action=='create_event':
            attendees=r.payload.get('attendees',[])
            if src in {'google','gmail'}:
                ev=c.create_event(r.payload['subject'],r.payload['start'],r.payload['end'],r.payload.get('timezone',settings.timezone),attendees,r.payload.get('body',''))
            else:
                ev=c.create_event(r.payload['subject'],r.payload['start'],r.payload['end'],r.payload.get('timezone',settings.timezone),attendees,r.payload.get('body',''))
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Evento creado.',data={'source':src,'event':ev})
        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
