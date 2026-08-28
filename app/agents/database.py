from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.core import store
class DatabaseAgent(BaseAgent):
    id='database';name='DatabaseAgent';display_name='Database Agent';description='Valida integridad y salud de la base de datos local.';integration='local';capabilities=['integrity check','schema inspection']
    ACTION_RISKS={'healthcheck':RiskLevel.READ,'inspect_schema':RiskLevel.READ,'backup':RiskLevel.WRITE,'restore':RiskLevel.DANGEROUS}
    def handle(self,r,ctx):
        if r.action=='healthcheck':return {'healthy':store.database_health(),'database':str(store.DB.name)}
        if r.action=='inspect_schema':
            with store.connect() as c:return {'tables':[x['name'] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]}
        if r.action=='backup':
            import shutil
            target=r.payload['target'];shutil.copy2(store.DB,target);return {'backup':target}
        if r.action=='restore':return {'restored':False,'message':'Restore is intentionally not automatic. Use a maintenance window and validated backup procedure.'}
        raise ValueError('Unsupported action')
