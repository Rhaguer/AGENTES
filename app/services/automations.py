from app.core import store
from app.core.audit import audit
from app.core.models import AgentRequest

class AutomationService:
    def __init__(self):
        self.scheduler = None
        self.orchestrator = None

    def bind(self, orchestrator):
        self.orchestrator = orchestrator

    def start(self):
        if self.scheduler:
            return True
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError:
            return False
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.reload()
        return True

    def stop(self):
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None

    def reload(self):
        if not self.scheduler:
            return
        for job in list(self.scheduler.get_jobs()):
            if job.id.startswith('automation-'):
                self.scheduler.remove_job(job.id)
        for item in store.list_automations():
            if not item['enabled']:
                continue
            self.scheduler.add_job(
                self.fire,
                'interval',
                minutes=max(1,int(item['interval_minutes'])),
                args=[item['id']],
                id=f"automation-{item['id']}",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )

    def fire(self, automation_id):
        item=store.get_automation(automation_id)
        if not item or not item['enabled'] or not self.orchestrator:
            return
        request=AgentRequest(action=item['action'],payload=item['payload'],approved=False)
        result=self.orchestrator.dispatch(item['agent'],request)
        store.update_automation_run(automation_id,result.ok,result.message)
        audit({'type':'automation_run','automation_id':automation_id,'name':item['name'],
               'agent':item['agent'],'action':item['action'],'ok':result.ok,'message':result.message})

automation_service=AutomationService()
