from app.core.models import RiskLevel

class PolicyEngine:
    def __init__(self, require_approval_for_writes=True):
        self.require_approval_for_writes=require_approval_for_writes

    def authorize(self, risk: RiskLevel, approved: bool):
        if risk == RiskLevel.DANGEROUS:
            return False, 'Acción DANGEROUS bloqueada por política.'
        if risk == RiskLevel.WRITE and self.require_approval_for_writes and not approved:
            return False, 'La acción WRITE requiere aprobación explícita.'
        return True, 'Permitida'
