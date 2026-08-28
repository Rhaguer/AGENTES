from __future__ import annotations
from datetime import datetime,timezone
from app.core import store
from app.core.audit import audit

class ReminderService:
    def __init__(self):self.scheduler=None
    def start(self):
        if self.scheduler:return True
        try:from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError:return False
        self.scheduler=BackgroundScheduler(timezone='UTC');self.scheduler.start();self.reload_pending();return True
    def stop(self):
        if self.scheduler:self.scheduler.shutdown(wait=False);self.scheduler=None
    def reload_pending(self):
        if not self.scheduler:return
        for job in list(self.scheduler.get_jobs()):
            if job.id.startswith('reminder-'):self.scheduler.remove_job(job.id)
        for r in store.list_reminders('pending'):
            try:
                dt=datetime.fromisoformat(r['run_at']);dt=dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                if dt>datetime.now(timezone.utc):self.scheduler.add_job(self.fire,'date',run_date=dt,args=[r['id'],r['text']],id=f"reminder-{r['id']}",replace_existing=True)
            except Exception as exc:audit({'type':'reminder_schedule_error','id':r['id'],'ok':False,'error_code':'REMINDER_SCHEDULE_ERROR','error':str(exc)})
    def schedule(self,text,run_at,actor,priority='MEDIUM'):
        rid=store.create_reminder(text,run_at,actor,priority);self.reload_pending();return rid
    def fire(self,rid,text):
        audit({'type':'reminder_fired','id':rid,'text':text,'ok':True})
        try:
            from winotify import Notification
            Notification(app_id='HAGUER Agent Platform',title='Recordatorio',msg=text).show()
        except Exception:print(f'[RECORDATORIO] {text}',flush=True)
        store.mark_reminder_fired(rid)
reminder_service=ReminderService()
