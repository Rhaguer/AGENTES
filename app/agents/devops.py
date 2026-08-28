import psutil
from app.agents.base import BaseAgent
from app.core.models import RiskLevel
class DevOpsAgent(BaseAgent):
    id='devops';name='DevOpsAgent';display_name='DevOps Agent';description='Inspección de procesos y preparación controlada de operaciones DevOps.';integration='local';capabilities=['procesos','servicios','preparación despliegue']
    ACTION_RISKS={'check_services':RiskLevel.READ,'prepare_deploy':RiskLevel.PREPARE,'deploy':RiskLevel.WRITE,'rollback':RiskLevel.WRITE}
    def handle(self,r,ctx):
        if r.action=='check_services':
            items=[]
            for p in psutil.process_iter(['pid','name','status']):
                try:items.append(p.info)
                except Exception:pass
            return {'processes':items[:300],'count':len(items)}
        if r.action=='prepare_deploy':return {'plan':r.payload,'prepared':True}
        if r.action in {'deploy','rollback'}:return {'executed':False,'message':'No deployment adapter configured. Define an explicit deployment command/provider before production use.'}
        raise ValueError('Unsupported action')
