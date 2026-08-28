from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector

class MailAgent(BaseAgent):
    id='mail';name='MailAgent';display_name='Mail Agent';description='Gestiona correo de Outlook y Gmail con controles de autorización.';integration='microsoft/google';requires_auth=True;capabilities=['correo no leído','envío de correo','extracción de compromisos']
    ACTION_RISKS={'list_unread':RiskLevel.READ,'send_email':RiskLevel.WRITE,'extract_commitments':RiskLevel.READ}
    ACTION_DESCRIPTIONS={'list_unread':'Lista correos no leídos.','send_email':'Envía un correo real.','extract_commitments':'Extrae compromisos desde texto proporcionado.'}
    def _connector(self,src):return GoogleWorkspaceConnector() if src in {'google','gmail'} else MicrosoftGraphConnector()
    def handle(self,r,ctx):
        src=r.payload.get('source','microsoft').lower();c=self._connector(src)
        if r.action=='list_unread':
            data=c.unread_mail(r.payload.get('limit',20));return {'source':src,'messages':data,'count':len(data)}
        if r.action=='send_email':return {'source':src,'result':c.send_mail(r.payload['to'],r.payload['subject'],r.payload['body'])}
        if r.action=='extract_commitments':
            text=r.payload.get('text','');keys=('debo','debe','enviar','revisar','agendar','confirmar','entregar','pendiente')
            items=[x.strip() for x in text.splitlines() if any(k in x.lower() for k in keys)];return {'items':items}
        raise ValueError('Unsupported action')
