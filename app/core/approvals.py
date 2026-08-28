from __future__ import annotations
import hashlib, secrets, uuid
from datetime import datetime, timedelta, timezone
from app.core import store
from app.core.config import settings
from app.core.errors import AppError
from app.core.models import RiskLevel, Role
from app.core.security import ROLE_LEVEL
from app.core.utils import stable_hash, utcnow_iso

class ApprovalService:
    def request(self, *, requester, role, agent, action, risk_level:RiskLevel, target, payload):
        if risk_level not in {RiskLevel.WRITE,RiskLevel.DANGEROUS}:
            raise AppError('APPROVAL_NOT_REQUIRED','Approval is only valid for WRITE or DANGEROUS actions',400)
        aid=str(uuid.uuid4());expires=(datetime.now(timezone.utc)+timedelta(seconds=settings.approval_ttl_seconds)).isoformat()
        store.insert_approval({'approval_id':aid,'requester':requester,'agent':agent,'action':action,'risk_level':risk_level.value,
            'target':target or '','parameters_hash':stable_hash(payload),'status':'pending','created_at':utcnow_iso(),'expires_at':expires})
        return aid,expires

    def decide(self, approval_id, *, approver, role:Role, decision:str):
        row=store.get_approval(approval_id)
        if not row:raise AppError('APPROVAL_NOT_FOUND','Approval request not found',404)
        if row['status']!='pending':raise AppError('APPROVAL_INVALID_STATE',f"Approval is {row['status']}",409)
        if datetime.fromisoformat(row['expires_at']) < datetime.now(timezone.utc):
            store.update_approval(approval_id,status='expired');raise AppError('APPROVAL_EXPIRED','Approval request expired',409)
        risk=RiskLevel(row['risk_level'])
        required=Role.ADMIN if risk==RiskLevel.DANGEROUS else Role.OPERATOR
        if ROLE_LEVEL[role] < ROLE_LEVEL[required]:raise AppError('APPROVAL_FORBIDDEN',f'{required.value} or higher required to approve',403)
        if settings.approval_require_different_actor and approver==row['requester']:
            raise AppError('APPROVAL_SEPARATION_REQUIRED','Requester cannot approve own action in this environment',403)
        if decision=='reject':
            store.update_approval(approval_id,status='rejected',approver=approver,rejected_at=utcnow_iso());return None,row['expires_at']
        token=secrets.token_urlsafe(32);token_hash=hashlib.sha256(token.encode()).hexdigest()
        store.update_approval(approval_id,status='approved',approver=approver,approved_at=utcnow_iso(),token_hash=token_hash)
        return token,row['expires_at']

    def consume(self, *, approval_id, token, actor, agent, action, risk_level:RiskLevel, target, payload):
        if not approval_id or not token:raise AppError('APPROVAL_REQUIRED','This action requires an approved one-time authorization',403)
        row=store.get_approval(approval_id)
        if not row:raise AppError('APPROVAL_NOT_FOUND','Approval request not found',403)
        if row['used_at'] or row['status']=='used':raise AppError('APPROVAL_ALREADY_USED','Approval is single-use and was already consumed',409)
        if row['status']!='approved':raise AppError('APPROVAL_NOT_APPROVED',f"Approval is {row['status']}",403)
        if datetime.fromisoformat(row['expires_at']) < datetime.now(timezone.utc):
            store.update_approval(approval_id,status='expired');raise AppError('APPROVAL_EXPIRED','Approval expired',401)
        if row['requester']!=actor:raise AppError('APPROVAL_ACTOR_MISMATCH','Approval belongs to another actor',403)
        expected=(row['agent'],row['action'],row['risk_level'],row['target'],row['parameters_hash'])
        actual=(agent,action,risk_level.value,target or '',stable_hash(payload))
        if expected!=actual:raise AppError('APPROVAL_SCOPE_MISMATCH','Approval does not match action/resource/parameters',403)
        if not secrets.compare_digest(row.get('token_hash') or '',hashlib.sha256(token.encode()).hexdigest()):
            raise AppError('APPROVAL_TOKEN_INVALID','Approval token invalid',403)
        store.update_approval(approval_id,status='used',used_at=utcnow_iso())
        return row

approval_service=ApprovalService()
