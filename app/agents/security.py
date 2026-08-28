import re
from pathlib import Path
from app.agents.base import BaseAgent
from app.core.models import RiskLevel
class SecurityAgent(BaseAgent):
    id='security';name='SecurityAgent';display_name='Security Agent';description='Búsqueda defensiva de secretos y controles básicos de postura.';integration='local';capabilities=['secret scan','security posture']
    ACTION_RISKS={'scan_secrets':RiskLevel.READ,'security_posture':RiskLevel.READ,'prepare_hardening':RiskLevel.PREPARE,'apply_hardening':RiskLevel.WRITE}
    def handle(self,r,ctx):
        if r.action=='security_posture':return {'controls':['approval-service','RBAC','audit-db','correlation-id','rate-limit','encrypted-tokens'],'status':'enabled'}
        if r.action=='scan_secrets':
            root=Path(r.payload.get('path','.')).resolve();patterns=[re.compile(r'(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["\']?[^\s"\']{8,}')];hits=[]
            for p in root.rglob('*'):
                if not p.is_file() or p.stat().st_size>2_000_000 or any(x in p.parts for x in ('.git','.venv','node_modules')):continue
                try:text=p.read_text(encoding='utf-8',errors='ignore')
                except Exception:continue
                for i,line in enumerate(text.splitlines(),1):
                    if any(rx.search(line) for rx in patterns):hits.append({'file':str(p),'line':i,'match':'potential-secret'})
                    if len(hits)>=250:return {'hits':hits,'truncated':True}
            return {'hits':hits,'truncated':False}
        if r.action=='prepare_hardening':return {'plan':r.payload,'prepared':True}
        if r.action=='apply_hardening':return {'applied':False,'message':'No hardening adapter configured for this target.'}
        raise ValueError('Unsupported action')
