from fastapi.testclient import TestClient
from app.main import app

def test_invalid_input_422_and_health():
    with TestClient(app) as c:
        r=c.post('/api/v1/command',json={'text':''});assert r.status_code==422 and r.json()['error']['code']=='VALIDATION_ERROR'
        h=c.get('/api/v1/health');assert h.status_code==200 and h.json()['api']=='healthy'
