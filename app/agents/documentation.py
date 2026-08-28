from pathlib import Path
from app.agents.base import BaseAgent
from app.core.models import RiskLevel
class DocumentationAgent(BaseAgent):
    id='documentation';name='DocumentationAgent';display_name='Documentation Agent';description='Inventario y preparación de documentación técnica.';integration='local';capabilities=['inspect docs','generate markdown']
    ACTION_RISKS={'inspect_docs':RiskLevel.READ,'generate_readme':RiskLevel.PREPARE,'write_docs':RiskLevel.WRITE}
    def handle(self,r,ctx):
        root=Path(r.payload.get('path','.')).resolve()
        if r.action=='inspect_docs':return {'documents':[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {'.md','.txt','.rst'}][:500]}
        if r.action=='generate_readme':return {'content':f"# {r.payload.get('title','Proyecto')}\n\nDocumento preparado por DocumentationAgent.\n"}
        if r.action=='write_docs':
            p=(root/r.payload['relative_path']).resolve()
            if root not in p.parents and p!=root:raise ValueError('Path escapes workspace')
            p.parent.mkdir(parents=True,exist_ok=True);p.write_text(r.payload['content'],encoding='utf-8');return {'path':str(p)}
        raise ValueError('Unsupported action')
