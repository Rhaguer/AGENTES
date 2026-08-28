import re
from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.connectors.microsoft_graph import MicrosoftGraphConnector

class MeetingAgent(BaseAgent):
    id='meeting';name='MeetingAgent';display_name='Teams Agent';description='Consulta Teams, chats, equipos, canales y extrae acciones de reuniones.';integration='microsoft';requires_auth=True;capabilities=['chats Teams','equipos','canales','acciones de reunión']
    ACTION_RISKS={'list_chats':RiskLevel.READ,'chat_messages':RiskLevel.READ,'list_teams':RiskLevel.READ,'list_channels':RiskLevel.READ,'channel_messages':RiskLevel.READ,'extract_actions':RiskLevel.READ}
    def handle(self,r,ctx):
        c=MicrosoftGraphConnector()
        if r.action=='list_chats':data=c.chats(r.payload.get('limit',30))
        elif r.action=='chat_messages':data=c.chat_messages(r.payload['chat_id'],r.payload.get('limit',50))
        elif r.action=='list_teams':data=c.joined_teams()
        elif r.action=='list_channels':data=c.channels(r.payload['team_id'])
        elif r.action=='channel_messages':data=c.channel_messages(r.payload['team_id'],r.payload['channel_id'],r.payload.get('limit',50))
        elif r.action=='extract_actions':
            rg=re.compile(r'(?i)\b(pendiente|acuerdo|debe|enviar|revisar|validar|confirmar|agendar|coordinar|entregar)\b');data=[x.strip(' -•\t') for x in r.payload.get('text','').splitlines() if rg.search(x)]
        else:raise ValueError('Unsupported action')
        return {'items':data,'count':len(data)}
