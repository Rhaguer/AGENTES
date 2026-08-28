from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector

class MailAgent(BaseAgent):
    name='MailAgent'
    ACTION_RISKS={'list_unread':RiskLevel.READ,'send_email':RiskLevel.WRITE}
    def handle(self,r):
        src=r.payload.get('source','microsoft').lower()
        c=GoogleWorkspaceConnector() if src in {'gmail','google'} else MicrosoftGraphConnector()
        if r.action=='list_unread':
            data=c.unread_mail(r.payload.get('limit',20))
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(data)} correos no leídos obtenidos.',data={'source':src,'messages':data})
        if r.action=='send_email':
            result=c.send_mail(r.payload['to'],r.payload['subject'],r.payload['body'])
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Correo enviado.',data={'source':src,'result':result})
        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
