from __future__ import annotations
from app.core.models import RiskLevel, Role
from app.core.errors import AppError

ROLE_LEVEL={Role.READ_ONLY:0,Role.USER:1,Role.OPERATOR:2,Role.ADMIN:3}
USER_WRITE_ACTIONS={'create_task','complete_task','create_reminder','create_event','send_email'}

class PolicyEngine:
    def check_rbac(self, role:Role, risk:RiskLevel, action:str):
        if risk==RiskLevel.READ:return
        if risk==RiskLevel.PREPARE and ROLE_LEVEL[role] < ROLE_LEVEL[Role.USER]:
            raise AppError('RBAC_FORBIDDEN','READ_ONLY role cannot execute PREPARE actions',403)
        if risk==RiskLevel.WRITE:
            if role==Role.USER and action in USER_WRITE_ACTIONS:return
            if ROLE_LEVEL[role] < ROLE_LEVEL[Role.OPERATOR]:raise AppError('RBAC_FORBIDDEN','Insufficient role for WRITE action',403)
        if risk==RiskLevel.DANGEROUS and role!=Role.ADMIN:
            raise AppError('RBAC_FORBIDDEN','DANGEROUS actions require ADMIN role',403)

    def requires_approval(self,risk:RiskLevel)->bool:
        return risk in {RiskLevel.WRITE,RiskLevel.DANGEROUS}
