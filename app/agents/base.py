from __future__ import annotations
from abc import ABC,abstractmethod
from app.core.models import AgentRequest,RiskLevel

class BaseAgent(ABC):
    id='base';name='BaseAgent';display_name='Base Agent';description='';version='2.0.0';integration=None;requires_auth=False;capabilities=[];ACTION_RISKS={};ACTION_DESCRIPTIONS={}
    def risk_for(self,action):return self.ACTION_RISKS.get(action)
    def target_for(self,request:AgentRequest):
        p=request.payload
        return str(p.get('path') or p.get('repo') or p.get('id') or p.get('source') or p.get('target') or '')
    @abstractmethod
    def handle(self,request,context):...
