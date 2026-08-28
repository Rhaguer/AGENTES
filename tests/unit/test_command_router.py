import pytest
from app.core.command_router import CommandRouter

@pytest.mark.parametrize('text',["revisa mis correos","muéstrame emails pendientes","tengo correos sin leer","ver correo nuevo"])
def test_mail_synonyms(text):
    r=CommandRouter().route(text)
    assert r.agent=='mail' and r.action=='list_unread'

def test_calendar_tomorrow():
    r=CommandRouter().route('muéstrame mis reuniones mañana')
    assert r.agent=='calendar' and r.action=='list_events'
