from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.core.config import settings

class CalendarAgent(BaseAgent):
    id='calendar';name='CalendarAgent';display_name='Calendar Agent';description='Consulta y crea eventos en Outlook Calendar y Google Calendar.';integration='microsoft/google';requires_auth=True;capabilities=['listar eventos','crear eventos','agenda']
    ACTION_RISKS={'list_events':RiskLevel.READ,'create_event':RiskLevel.WRITE}
    ACTION_DESCRIPTIONS={'list_events':'Consulta eventos en un rango.','create_event':'Crea un evento real en el calendario.'}
    def handle(self,r,ctx):
        src=r.payload.get('source','microsoft').lower();c=GoogleWorkspaceConnector() if src in {'google','gmail'} else MicrosoftGraphConnector()
        if r.action=='list_events':
            items=c.calendar_events(r.payload['start'],r.payload['end'],r.payload.get('limit',50));return {'source':src,'events':items,'count':len(items)}
        if r.action=='create_event':
            ev=c.create_event(r.payload['subject'],r.payload['start'],r.payload['end'],r.payload.get('timezone',settings.timezone),r.payload.get('attendees',[]),r.payload.get('body',''));return {'source':src,'event':ev}
        raise ValueError('Unsupported action')
