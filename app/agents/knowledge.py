from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
class KnowledgeAgent(BaseAgent):
    name='KnowledgeAgent'
    ACTION_RISKS={'search_files':RiskLevel.READ}
    def handle(self,r):

        from pathlib import Path
        if r.action=='search_files':
            p=Path(r.payload.get('path','.')).resolve(); q=r.payload['query'].lower(); found=[]
            for f in p.rglob('*'):
                if f.is_file() and f.suffix.lower() in {'.md','.txt','.py','.js','.ts','.json','.yaml','.yml'}:
                    try:
                        txt=f.read_text(encoding='utf-8',errors='ignore')[:2_000_000]
                        if q in txt.lower(): found.append(str(f.relative_to(p)))
                    except Exception: pass
                if len(found)>=200: break
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(found)} archivos coincidentes.',data={'files':found})

        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')

