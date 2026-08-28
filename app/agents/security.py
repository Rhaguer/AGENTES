from pathlib import Path
import re
from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
class SecurityAgent(BaseAgent):
    name='SecurityAgent'
    ACTION_RISKS={'scan_secrets':RiskLevel.READ,'security_posture':RiskLevel.READ}
    def handle(self,r):
        if r.action=='security_posture':
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Controles activos.',data={'write_approval':True,'dangerous_blocked':True,'audit_log':'logs/audit.jsonl','secret_source':'.env'})
        if r.action=='scan_secrets':
            base=Path(r.payload.get('path','.')).resolve(); findings=[]
            pat=re.compile(r'(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["\']?([^"\'\s]{8,})')
            allowed={'.py','.js','.ts','.json','.yml','.yaml','.env','.toml','.ini','.md','.txt'}
            for p in base.rglob('*'):
                if not p.is_file() or p.suffix.lower() not in allowed or '.git' in p.parts: continue
                try: txt=p.read_text(encoding='utf-8',errors='ignore')[:2_000_000]
                except Exception: continue
                for i,line in enumerate(txt.splitlines(),1):
                    if pat.search(line): findings.append({'file':str(p.relative_to(base)),'line':i,'type':'possible_secret'})
                    if len(findings)>=200: break
                if len(findings)>=200: break
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(findings)} posibles secretos.',data={'findings':findings})
        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
