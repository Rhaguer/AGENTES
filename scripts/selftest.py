import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.store import init_db
from app.agents.orchestrator import OrchestratorAgent
from app.core.models import AgentRequest
init_db(); o=OrchestratorAgent()
r=o.dispatch('monitoring',AgentRequest(action='system_health'))
assert r.ok
r=o.dispatch('calendar',AgentRequest(action='create_event',payload={},approved=False))
assert not r.ok and r.requires_approval
print('SELFTEST OK')
