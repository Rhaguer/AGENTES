from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

def test_commit_approval_cannot_delete_branch():
    with TestClient(app) as c:
        p={'path':'.','message':'x'}
        q=c.post('/api/v1/approvals/request',json={'agent':'development','action':'commit','payload':p}).json()
        d=c.post(f"/api/v1/approvals/{q['approval_id']}/decision",json={'decision':'approve'}).json()
        r=c.post('/api/v1/agents/development/execute',json={'action':'delete_branch','payload':{'owner':'x','repo':'y','branch':'z'},'approval_id':q['approval_id'],'approval_token':d['approval_token']})
        assert r.status_code==403 and r.json()['error']['code']=='APPROVAL_SCOPE_MISMATCH'

def test_rate_limit_429(monkeypatch):
    monkeypatch.setattr(settings,'rate_command_per_minute',1)
    from app.core.middleware import RateLimitMiddleware
    with TestClient(app) as c:
        a=c.post('/command',json={'text':'revisa mis correos'})
        b=c.post('/command',json={'text':'revisa mis correos'})
        assert b.status_code==429
