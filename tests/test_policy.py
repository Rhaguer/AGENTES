from app.agents.calendar import CalendarAgent
from app.core.models import AgentRequest

def test_calendar_write_requires_approval():
    r=CalendarAgent().execute(AgentRequest(action='create_event',payload={},approved=False))
    assert r.ok is False
    assert r.requires_approval is True
