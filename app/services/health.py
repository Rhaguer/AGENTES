from __future__ import annotations
import time
from app.core import store
from app.core.models import HealthResponse
from app.core.utils import utcnow_iso
from app.connectors.microsoft_graph import MicrosoftGraphConnector
from app.connectors.google_workspace import GoogleWorkspaceConnector
from app.connectors.github import GitHubConnector

STARTED=time.time()

def integration_state(c):
    if not c.configured():return 'not_configured'
    return 'connected' if c.authenticated() else 'disconnected'

def platform_health(orchestrator):
    db='healthy' if store.database_health() else 'unhealthy'
    ms=integration_state(MicrosoftGraphConnector());google=integration_state(GoogleWorkspaceConnector());gh=integration_state(GitHubConnector())
    agents={x.id:('online' if x.health=='healthy' else 'degraded') for x in orchestrator.catalog()}
    overall='healthy' if db=='healthy' else 'degraded'
    errors=sum(1 for x in store.list_audit(100) if x['status']=='ERROR')
    return HealthResponse(status=overall,api='healthy',database=db,microsoft=ms,google=google,github=gh,agents=agents,uptime_seconds=round(time.time()-STARTED,2),recent_errors=errors,timestamp=utcnow_iso())
