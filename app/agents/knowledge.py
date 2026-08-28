from pathlib import Path
from app.agents.base import BaseAgent
from app.core.models import RiskLevel
class KnowledgeAgent(BaseAgent):
    id='knowledge';name='KnowledgeAgent';display_name='Knowledge Agent';description='Búsqueda textual local limitada a un workspace explícito.';integration='local';capabilities=['text search']
    ACTION_RISKS={'search':RiskLevel.READ}
    def handle(self,r,ctx):
        root=Path(r.payload.get('path','.')).resolve();q=r.payload['query'].lower();hits=[]
        for p in root.rglob('*'):
            if not p.is_file() or p.stat().st_size>3_000_000:continue
            try:text=p.read_text(encoding='utf-8',errors='ignore')
            except Exception:continue
            if q in text.lower():hits.append(str(p))
            if len(hits)>=100:break
        return {'matches':hits}
