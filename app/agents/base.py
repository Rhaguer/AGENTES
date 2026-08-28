from abc import ABC,abstractmethod
from app.core.models import AgentRequest,AgentResult,RiskLevel
from app.core.security import PolicyEngine
from app.core.config import settings
from app.core.audit import audit

class BaseAgent(ABC):
    name='BaseAgent'; ACTION_RISKS={}
    def __init__(self): self.policy=PolicyEngine(settings.require_approval_for_writes)
    def risk_for(self,action): return self.ACTION_RISKS.get(action,RiskLevel.PREPARE)
    def execute(self,request:AgentRequest):
        risk=self.risk_for(request.action)
        allowed,reason=self.policy.authorize(risk,request.approved)
        if not allowed:
            r=AgentResult(agent=self.name,action=request.action,ok=False,message=reason,requires_approval=(risk==RiskLevel.WRITE))
            audit({'agent':self.name,'action':request.action,'risk':risk.value,'ok':False,'reason':reason})
            return r
        try: r=self.handle(request)
        except Exception as e: r=AgentResult(agent=self.name,action=request.action,ok=False,message=str(e))
        audit({'agent':self.name,'action':request.action,'risk':risk.value,'ok':r.ok,'message':r.message})
        return r
    @abstractmethod
    def handle(self,request): ...
