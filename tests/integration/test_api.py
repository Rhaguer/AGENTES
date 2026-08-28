from fastapi.testclient import TestClient
from app.main import app

def test_ui_and_swagger():
    with TestClient(app) as c:
        for path in ['/','/ui/agents','/ui/integrations','/ui/automations','/ui/tasks','/ui/monitoring','/ui/audit','/ui/settings','/docs','/openapi.json']:
            assert c.get(path).status_code==200

def test_version_and_catalog():
    with TestClient(app) as c:
        v=c.get('/api/v1/version');assert v.status_code==200 and v.json()['version']=='2.0.0'
        a=c.get('/api/v1/agents');assert a.status_code==200 and a.json()['count']==14

def test_missing_credentials_are_not_500():
    with TestClient(app) as c:
        assert c.get('/auth/microsoft/me').status_code in {401,503}
        assert c.get('/auth/github/me').status_code in {401,503}
