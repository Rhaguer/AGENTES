from fastapi.testclient import TestClient
from app.main import app

def test_calendar_write_requires_approval():
    with TestClient(app) as c:
        r=c.post('/api/v1/agents/calendar/execute',json={'action':'create_event','payload':{'source':'microsoft','subject':'x','start':'2026-01-01T10:00:00','end':'2026-01-01T11:00:00'},'approved':True})
        assert r.status_code==403
        assert r.json()['error']['code']=='APPROVAL_REQUIRED'
