from __future__ import annotations
import os,sys
os.environ.setdefault('APP_ENV','testing')
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
from fastapi.testclient import TestClient
from app.main import app

REQUIRED=['/','/ui/agents','/ui/integrations','/ui/automations','/ui/tasks','/ui/monitoring','/ui/audit','/ui/settings','/docs','/openapi.json','/api/v1/version','/api/v1/agents','/api/v1/health','/version','/agents','/health']

def main():
    failures=[]
    with TestClient(app) as c:
        for path in REQUIRED:
            r=c.get(path)
            if r.status_code!=200:failures.append((path,r.status_code,r.text[:200]))
        ms=c.get('/auth/microsoft/me')
        if ms.status_code==500:failures.append(('microsoft missing credentials',500,ms.text[:200]))
        write=c.post('/api/v1/agents/task/execute',json={'action':'create_task','payload':{'title':'selftest'},'approved':True})
        if write.status_code!=403:failures.append(('approved:true bypass',write.status_code,write.text[:200]))
    if failures:
        print('SELFTEST FAILED')
        for x in failures:print(x)
        raise SystemExit(1)
    print('SELFTEST OK')
    print('Dashboard, Swagger, API v1, compatibilidad y controles de aprobación: OK')
if __name__=='__main__':main()
