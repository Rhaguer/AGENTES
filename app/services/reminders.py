from datetime import datetime
from app.core import store
from app.core.audit import audit

class ReminderService:
    def __init__(self): self.scheduler=None
    def start(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError:
            return False
        self.scheduler=BackgroundScheduler()
        self.scheduler.start()
        self.reload_pending()
        return True
    def stop(self):
        if self.scheduler: self.scheduler.shutdown(wait=False)
    def reload_pending(self):
        if not self.scheduler: return
        for r in store.list_reminders('pending'):
            try:
                dt=datetime.fromisoformat(r['run_at'])
                if dt > datetime.now(dt.tzinfo):
                    self.scheduler.add_job(self.fire,'date',run_date=dt,args=[r['id'],r['text']],id=f"reminder-{r['id']}",replace_existing=True)
            except Exception as e:
                audit({'type':'reminder_schedule_error','id':r['id'],'error':str(e)})
    def schedule(self,text,run_at):
        rid=store.create_reminder(text,run_at)
        self.reload_pending()
        return rid
    def fire(self,rid,text):
        # Always auditable; on Windows also attempts a native toast.
        audit({'type':'reminder_fired','id':rid,'text':text})
        try:
            from winotify import Notification
            Notification(app_id='HAGUER Agent Platform',title='Recordatorio',msg=text).show()
        except Exception:
            print(f'[RECORDATORIO] {text}',flush=True)
        store.mark_reminder_fired(rid)

reminder_service=ReminderService()
