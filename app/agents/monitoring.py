import socket,psutil
from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
class MonitoringAgent(BaseAgent):
    name='MonitoringAgent'
    ACTION_RISKS={'system_health':RiskLevel.READ,'tcp_check':RiskLevel.READ}
    def handle(self,r):
        if r.action=='system_health':
            d={'cpu_percent':psutil.cpu_percent(interval=.25),'memory_percent':psutil.virtual_memory().percent,
               'disk_percent':psutil.disk_usage('/').percent,'boot_time':psutil.boot_time()}
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Salud del sistema obtenida.',data=d)
        if r.action=='tcp_check':
            host=r.payload['host']; port=int(r.payload['port']); timeout=min(float(r.payload.get('timeout',3)),10)
            try:
                with socket.create_connection((host,port),timeout=timeout): ok=True
            except OSError: ok=False
            return AgentResult(agent=self.name,action=r.action,ok=ok,message='Puerto accesible.' if ok else 'Puerto no accesible.',data={'host':host,'port':port})
        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
