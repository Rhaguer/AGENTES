from __future__ import annotations
import uuid
from datetime import datetime,timezone
from app.core import store
from app.core.context import ExecutionContext
from app.core.models import AgentRequest,Role,RiskLevel
from app.core.audit import audit

class AutomationService:
    def __init__(self):self.scheduler=None;self.orchestrator=None
    def bind(self,orchestrator):self.orchestrator=orchestrator
    def start(self):
        if self.scheduler:return True
        try:from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError:return False
        self.scheduler=BackgroundScheduler(timezone='UTC');self.scheduler.start();self.reload();return True
    def stop(self):
        if self.scheduler:self.scheduler.shutdown(wait=False);self.scheduler=None
    def _trigger(self,spec):
        if spec.startswith('interval:'):
            minutes=max(1,int(spec.split(':',1)[1]));return ('interval',{'minutes':minutes})
        if spec.startswith('cron:'):
            from apscheduler.triggers.cron import CronTrigger
            expr=spec.split(':',1)[1].strip();return (CronTrigger.from_crontab(expr,timezone='UTC'),{})
        raise ValueError('schedule must be interval:<minutes> or cron:<5-part-expression>')
    def reload(self):
        if not self.scheduler:return
        for job in list(self.scheduler.get_jobs()):
            if job.id.startswith('automation-'):self.scheduler.remove_job(job.id)
        for item in store.list_automations():
            if not item['enabled']:continue
            trigger,kwargs=self._trigger(item['schedule'])
            if isinstance(trigger,str):job=self.scheduler.add_job(self.fire,trigger,args=[item['id']],id=f"automation-{item['id']}",replace_existing=True,max_instances=1,coalesce=True,**kwargs)
            else:job=self.scheduler.add_job(self.fire,trigger,args=[item['id']],id=f"automation-{item['id']}",replace_existing=True,max_instances=1,coalesce=True)
            store.update_automation_schedule(item['id'],next_run=job.next_run_time.isoformat() if job.next_run_time else None,status='SCHEDULED')
    def fire(self,aid):
        item=store.get_automation(aid)
        if not item or not item['enabled'] or not self.orchestrator:return
        agent=self.orchestrator.agents.get(item['agent'])
        if not agent:return
        risk=agent.risk_for(item['action'])
        if risk not in {RiskLevel.READ,RiskLevel.PREPARE}:
            store.update_automation_schedule(aid,last_run=datetime.now(timezone.utc).isoformat(),status='BLOCKED');return
        hid=store.automation_history_start(aid);ctx=ExecutionContext(correlation_id=f'automation-{aid}-{uuid.uuid4()}',actor='automation-service',role=Role.OPERATOR)
        try:
            result=self.orchestrator.dispatch(item['agent'],AgentRequest(action=item['action'],payload=item['parameters']),ctx);status='SUCCESS' if result.success else 'ERROR';msg=result.message;audit_id=result.audit_id
        except Exception as exc:status='ERROR';msg=str(exc)[:1000];audit_id=None
        store.automation_history_finish(hid,status,msg,audit_id);store.update_automation_schedule(aid,last_run=datetime.now(timezone.utc).isoformat(),status=status)
        job=self.scheduler.get_job(f'automation-{aid}') if self.scheduler else None
        if job:store.update_automation_schedule(aid,next_run=job.next_run_time.isoformat() if job.next_run_time else None)
        audit({'type':'automation_run','automation_id':aid,'agent':item['agent'],'action':item['action'],'ok':status=='SUCCESS','correlation_id':ctx.correlation_id})
automation_service=AutomationService()
