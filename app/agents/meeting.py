import re
from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
from app.connectors.microsoft_graph import MicrosoftGraphConnector

class MeetingAgent(BaseAgent):
    name='MeetingAgent'
    ACTION_RISKS={'list_chats':RiskLevel.READ,'chat_messages':RiskLevel.READ,'list_teams':RiskLevel.READ,'list_channels':RiskLevel.READ,'channel_messages':RiskLevel.READ,'extract_actions':RiskLevel.READ}
    def handle(self,r):
        c=MicrosoftGraphConnector()
        if r.action=='list_chats': data=c.chats(r.payload.get('limit',30))
        elif r.action=='chat_messages': data=c.chat_messages(r.payload['chat_id'],r.payload.get('limit',50))
        elif r.action=='list_teams': data=c.joined_teams()
        elif r.action=='list_channels': data=c.channels(r.payload['team_id'])
        elif r.action=='channel_messages': data=c.channel_messages(r.payload['team_id'],r.payload['channel_id'],r.payload.get('limit',50))
        elif r.action=='extract_actions':
            text=r.payload.get('text','')
            lines=[x.strip(' -•\t') for x in text.splitlines() if x.strip()]
            keys=re.compile(r'(?i)\b(pendiente|acuerdo|debe|enviar|revisar|validar|confirmar|agendar|coordinar|entregar)\b')
            data=[x for x in lines if keys.search(x)]
        else: return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
        return AgentResult(agent=self.name,action=r.action,ok=True,message='Operación de reunión/Teams completada.',data={'items':data})
