from __future__ import annotations
import json, uuid
from app.core import store
from app.core.utils import utcnow_iso, redact

class AuditService:
    def record(self, *, actor, agent, action, risk_level, target, parameters_hash, approval_id, status, duration_ms, result=None, error_code=None, correlation_id=''):
        audit_id=str(uuid.uuid4())
        if result is not None:
            if not isinstance(result,str):result=json.dumps(redact(result),ensure_ascii=False,default=str)
            result=result[:10000]
        row={'audit_id':audit_id,'timestamp':utcnow_iso(),'actor':actor,'agent':agent,'action':action,'risk_level':str(risk_level),
             'target':target or '','parameters_hash':parameters_hash,'approval_id':approval_id,'status':status,'duration_ms':int(duration_ms),
             'result':result,'error_code':error_code,'correlation_id':correlation_id or ''}
        store.insert_audit(row);return audit_id

audit_service=AuditService()

def audit(event: dict):
    # Compatibility helper for non-agent services.
    return audit_service.record(actor=event.get('actor','system'),agent=event.get('agent',event.get('type','system')),
        action=event.get('action',event.get('type','event')),risk_level=event.get('risk','READ'),target=event.get('target',''),
        parameters_hash=event.get('parameters_hash',''),approval_id=event.get('approval_id'),status='SUCCESS' if event.get('ok',True) else 'ERROR',
        duration_ms=event.get('duration_ms',0),result=event,error_code=event.get('error_code'),correlation_id=event.get('correlation_id','system'))
