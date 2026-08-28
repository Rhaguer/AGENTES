from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
class DocumentationAgent(BaseAgent):
    name='DocumentationAgent'
    ACTION_RISKS={'inspect_docs':RiskLevel.READ}
    def handle(self,r):

        from pathlib import Path
        if r.action=='inspect_docs':
            p=Path(r.payload.get('path','.')).resolve(); docs=[str(x.relative_to(p)) for x in p.rglob('*') if x.is_file() and x.suffix.lower() in {'.md','.txt','.pdf','.docx'}][:500]
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(docs)} documentos encontrados.',data={'documents':docs})

        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')

