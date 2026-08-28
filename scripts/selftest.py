from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.store import init_db
from app.agents.orchestrator import OrchestratorAgent
from app.core.models import AgentRequest


def main():
    init_db()
    o = OrchestratorAgent()
    assert len(o.agents) == 13

    health = o.dispatch('monitoring', AgentRequest(action='system_health'))
    assert health.ok

    blocked = o.dispatch(
        'task',
        AgentRequest(action='create_task', payload={'title': 'prueba'}, approved=False),
    )
    assert not blocked.ok and blocked.requires_approval

    assert Path('app/templates/dashboard.html').exists()
    assert Path('app/static/css/agents.css').exists()
    assert Path('app/static/js/app.js').exists()

    from app.main import app
    routes = {getattr(route, 'path', None) for route in app.routes}
    required = {
        '/', '/ui/agents', '/ui/integrations', '/ui/automations', '/ui/tasks',
        '/ui/monitoring', '/ui/audit', '/ui/settings', '/docs', '/agents'
    }
    assert required.issubset(routes), required - routes
    print('SELFTEST OK')


if __name__ == '__main__':
    main()
