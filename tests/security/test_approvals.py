from fastapi.testclient import TestClient
from app.main import app

def approve(c,agent,action,payload):
    r=c.post('/api/v1/approvals/request',json={'agent':agent,'action':action,'payload':payload});assert r.status_code==200;aid=r.json()['approval_id']
    d=c.post(f'/api/v1/approvals/{aid}/decision',json={'decision':'approve'});assert d.status_code==200;return aid,d.json()['approval_token']

def test_approved_true_is_not_authorization():
    with TestClient(app) as c:
        r=c.post('/api/v1/agents/task/execute',json={'action':'create_task','payload':{'title':'x'},'approved':True})
        assert r.status_code==403 and r.json()['error']['code']=='APPROVAL_REQUIRED'

def test_write_without_approval_rejected():
    with TestClient(app) as c:
        r=c.post('/api/v1/agents/task/execute',json={'action':'create_task','payload':{'title':'x'}})
        assert r.status_code==403

def test_approval_single_use():
    with TestClient(app) as c:
        p={'title':'x','priority':'MEDIUM','source':'test'};aid,tok=approve(c,'task','create_task',p)
        b={'action':'create_task','payload':p,'approval_id':aid,'approval_token':tok}
        assert c.post('/api/v1/agents/task/execute',json=b).status_code==200
        r=c.post('/api/v1/agents/task/execute',json=b);assert r.status_code==409 and r.json()['error']['code']=='APPROVAL_ALREADY_USED'

def test_approval_scope_mismatch():
    with TestClient(app) as c:
        p={'title':'x','priority':'MEDIUM','source':'test'};aid,tok=approve(c,'task','create_task',p)
        changed={'title':'y','priority':'MEDIUM','source':'test'}
        r=c.post('/api/v1/agents/task/execute',json={'action':'create_task','payload':changed,'approval_id':aid,'approval_token':tok})
        assert r.status_code==403 and r.json()['error']['code']=='APPROVAL_SCOPE_MISMATCH'

def test_read_only_cannot_prepare():
    with TestClient(app) as c:
        r=c.post('/api/v1/agents/followup/execute',headers={'X-Role':'READ_ONLY'},json={'action':'prepare_followup','payload':{}})
        assert r.status_code==403 and r.json()['error']['code']=='RBAC_FORBIDDEN'

def test_unknown_agent_and_action():
    with TestClient(app) as c:
        assert c.post('/api/v1/agents/nope/execute',json={'action':'x','payload':{}}).status_code==404
        assert c.post('/api/v1/agents/task/execute',json={'action':'nope','payload':{}}).status_code==404
