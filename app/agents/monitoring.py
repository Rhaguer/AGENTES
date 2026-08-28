import socket,time,psutil
from pathlib import Path
from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.core import store

class MonitoringAgent(BaseAgent):
    id='monitoring';name='MonitoringAgent';display_name='Monitoring Agent';description='Monitorea CPU, RAM, disco, procesos, red y base de datos.';integration='local';capabilities=['salud sistema','TCP','DB']
    ACTION_RISKS={'system_health':RiskLevel.READ,'tcp_check':RiskLevel.READ,'database_health':RiskLevel.READ}
    def handle(self,r,ctx):
        if r.action=='system_health':
            vm=psutil.virtual_memory();root=Path.cwd().anchor or '/';du=psutil.disk_usage(root)
            return {'cpu_percent':psutil.cpu_percent(interval=.2),'memory_percent':vm.percent,'memory_total':vm.total,'memory_available':vm.available,'disk_percent':du.percent,'disk_total':du.total,'disk_free':du.free,'process_count':len(psutil.pids()),'boot_time':psutil.boot_time()}
        if r.action=='database_health':return {'healthy':store.database_health()}
        if r.action=='tcp_check':
            host=r.payload['host'];port=int(r.payload['port']);started=time.perf_counter()
            try:
                with socket.create_connection((host,port),timeout=min(float(r.payload.get('timeout',3)),10)):ok=True
            except OSError:ok=False
            return {'host':host,'port':port,'reachable':ok,'latency_ms':round((time.perf_counter()-started)*1000,2)}
        raise ValueError('Unsupported action')
