from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
class DatabaseAgent(BaseAgent):
    name='DatabaseAgent'
    ACTION_RISKS={'sqlite_integrity':RiskLevel.READ}
    def handle(self,r):

        import sqlite3
        if r.action=='sqlite_integrity':
            db=r.payload['path']
            with sqlite3.connect(db) as c: result=c.execute('PRAGMA integrity_check').fetchone()[0]
            return AgentResult(agent=self.name,action=r.action,ok=(result=='ok'),message='Integridad SQLite verificada.',data={'result':result})

        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')

