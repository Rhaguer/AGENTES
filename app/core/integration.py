from __future__ import annotations
from abc import ABC,abstractmethod
from app.core.models import IntegrationStatus
from app.core.utils import utcnow_iso

class IntegrationConnector(ABC):
    provider='unknown';capabilities=[]
    @abstractmethod
    def configured(self)->bool:...
    @abstractmethod
    def authenticated(self)->bool:...
    def status(self)->IntegrationStatus:
        configured=self.configured()
        if not configured:
            return IntegrationStatus(provider=self.provider,configured=False,authenticated=False,available=False,status='NOT_CONFIGURED',last_check=utcnow_iso(),capabilities=list(self.capabilities))
        try:
            authenticated=self.authenticated();status='CONNECTED' if authenticated else 'DISCONNECTED'
            return IntegrationStatus(provider=self.provider,configured=True,authenticated=authenticated,available=True,status=status,last_check=utcnow_iso(),capabilities=list(self.capabilities))
        except Exception as exc:
            return IntegrationStatus(provider=self.provider,configured=True,authenticated=False,available=False,status='ERROR',last_check=utcnow_iso(),capabilities=list(self.capabilities),message=str(exc)[:300])
