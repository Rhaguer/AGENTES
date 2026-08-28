from fastapi.testclient import TestClient
from app.main import app

def test_task_approval_audit_flow():
    with TestClient(app) as c:
        p={'title':'E2E','priority':'HIGH','source':'e2e'}
        q=c.post('/api/v1/approvals/request',json={'agent':'task','action':'create_task','payload':p}).json()
        d=c.post(f"/api/v1/approvals/{q['approval_id']}/decision",json={'decision':'approve'}).json()
        x=c.post('/api/v1/agents/task/execute',json={'action':'create_task','payload':p,'approval_id':q['approval_id'],'approval_token':d['approval_token']})
        assert x.status_code==200
        audit_id=x.json()['audit_id'];a=c.get(f'/api/v1/audit/{audit_id}')
        assert a.status_code==200 and a.json()['action']=='create_task'
