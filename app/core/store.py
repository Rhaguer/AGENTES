from __future__ import annotations
import json, sqlite3, uuid
from pathlib import Path
from typing import Any
from app.core.config import settings
from app.core.utils import utcnow_iso

DB = Path(settings.database_path)
DB.parent.mkdir(parents=True, exist_ok=True)

def connect():
    c = sqlite3.connect(DB, timeout=20, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init_db():
    with connect() as c:
        c.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS tasks(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          priority TEXT NOT NULL DEFAULT 'MEDIUM',
          due_at TEXT,
          status TEXT NOT NULL DEFAULT 'pending',
          source TEXT,
          source_id TEXT,
          created_by TEXT NOT NULL,
          assigned_to TEXT,
          completed_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS task_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          task_id INTEGER NOT NULL,
          event TEXT NOT NULL,
          actor TEXT NOT NULL,
          detail TEXT,
          timestamp TEXT NOT NULL,
          FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS reminders(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          text TEXT NOT NULL,
          priority TEXT NOT NULL DEFAULT 'MEDIUM',
          run_at TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          created_by TEXT NOT NULL,
          fired_at TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals(
          approval_id TEXT PRIMARY KEY,
          requester TEXT NOT NULL,
          approver TEXT,
          agent TEXT NOT NULL,
          action TEXT NOT NULL,
          risk_level TEXT NOT NULL,
          target TEXT NOT NULL,
          parameters_hash TEXT NOT NULL,
          token_hash TEXT,
          status TEXT NOT NULL DEFAULT 'pending',
          created_at TEXT NOT NULL,
          approved_at TEXT,
          expires_at TEXT NOT NULL,
          used_at TEXT,
          rejected_at TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_events(
          audit_id TEXT PRIMARY KEY,
          timestamp TEXT NOT NULL,
          actor TEXT NOT NULL,
          agent TEXT NOT NULL,
          action TEXT NOT NULL,
          risk_level TEXT NOT NULL,
          target TEXT NOT NULL,
          parameters_hash TEXT NOT NULL,
          approval_id TEXT,
          status TEXT NOT NULL,
          duration_ms INTEGER NOT NULL DEFAULT 0,
          result TEXT,
          error_code TEXT,
          correlation_id TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_audit_corr ON audit_events(correlation_id);
        CREATE INDEX IF NOT EXISTS idx_audit_agent_action ON audit_events(agent,action);
        CREATE TABLE IF NOT EXISTS automations(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          agent TEXT NOT NULL,
          action TEXT NOT NULL,
          parameters_json TEXT NOT NULL DEFAULT '{}',
          schedule TEXT NOT NULL,
          enabled INTEGER NOT NULL DEFAULT 1,
          status TEXT NOT NULL DEFAULT 'IDLE',
          last_run TEXT,
          next_run TEXT,
          created_by TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS automation_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          automation_id INTEGER NOT NULL,
          started_at TEXT NOT NULL,
          completed_at TEXT,
          status TEXT NOT NULL,
          message TEXT,
          audit_id TEXT,
          FOREIGN KEY(automation_id) REFERENCES automations(id) ON DELETE CASCADE
        );
        ''')
        _ensure_column(c, 'tasks', 'priority', "TEXT NOT NULL DEFAULT 'MEDIUM'")
        _ensure_column(c, 'tasks', 'created_by', "TEXT NOT NULL DEFAULT 'local-user'")
        _ensure_column(c, 'tasks', 'assigned_to', 'TEXT')
        _ensure_column(c, 'tasks', 'completed_at', 'TEXT')
        _ensure_column(c, 'tasks', 'updated_at', "TEXT NOT NULL DEFAULT ''")
        _ensure_column(c, 'reminders', 'priority', "TEXT NOT NULL DEFAULT 'MEDIUM'")
        _ensure_column(c, 'reminders', 'created_by', "TEXT NOT NULL DEFAULT 'local-user'")
        _ensure_column(c, 'reminders', 'fired_at', 'TEXT')

def _ensure_column(c, table, column, definition):
    cols = {r['name'] for r in c.execute(f'PRAGMA table_info({table})').fetchall()}
    if column not in cols:
        c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')

def database_health() -> bool:
    try:
        with connect() as c:
            row = c.execute('PRAGMA integrity_check').fetchone()
            return bool(row and row[0] == 'ok')
    except Exception:
        return False

def create_task(title, actor, priority='MEDIUM', due_at=None, assigned_to=None, source='ui', source_id=None):
    now = utcnow_iso()
    with connect() as c:
        cur = c.execute('''INSERT INTO tasks(title,priority,due_at,status,source,source_id,created_by,assigned_to,created_at,updated_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?)''',
                        (title, priority, due_at, 'pending', source, source_id, actor, assigned_to, now, now))
        tid = cur.lastrowid
        c.execute('INSERT INTO task_history(task_id,event,actor,detail,timestamp) VALUES(?,?,?,?,?)',
                  (tid,'created',actor,json.dumps({'priority':priority,'assigned_to':assigned_to},ensure_ascii=False),now))
        return tid

def list_tasks(status=None):
    with connect() as c:
        q='SELECT * FROM tasks'; args=[]
        if status: q+=' WHERE status=?'; args.append(status)
        q+=' ORDER BY id DESC'
        return [dict(r) for r in c.execute(q,args).fetchall()]

def complete_task(task_id, actor):
    now=utcnow_iso()
    with connect() as c:
        cur=c.execute("UPDATE tasks SET status='completed',completed_at=?,updated_at=? WHERE id=? AND status!='completed'",(now,now,task_id))
        if cur.rowcount:
            c.execute('INSERT INTO task_history(task_id,event,actor,timestamp) VALUES(?,?,?,?)',(task_id,'completed',actor,now))
        return cur.rowcount == 1

def task_history(task_id):
    with connect() as c: return [dict(r) for r in c.execute('SELECT * FROM task_history WHERE task_id=? ORDER BY id',(task_id,)).fetchall()]

def create_reminder(text, run_at, actor, priority='MEDIUM'):
    with connect() as c:
        cur=c.execute('INSERT INTO reminders(text,priority,run_at,status,created_by,created_at) VALUES(?,?,?,?,?,?)',
                      (text,priority,run_at,'pending',actor,utcnow_iso()))
        return cur.lastrowid

def list_reminders(status=None):
    with connect() as c:
        q='SELECT * FROM reminders'; args=[]
        if status:q+=' WHERE status=?';args.append(status)
        q+=' ORDER BY run_at'
        return [dict(r) for r in c.execute(q,args).fetchall()]

def mark_reminder_fired(reminder_id):
    with connect() as c: c.execute("UPDATE reminders SET status='fired',fired_at=? WHERE id=?",(utcnow_iso(),reminder_id))

def insert_approval(row: dict):
    with connect() as c:
        c.execute('''INSERT INTO approvals(approval_id,requester,agent,action,risk_level,target,parameters_hash,status,created_at,expires_at)
                     VALUES(:approval_id,:requester,:agent,:action,:risk_level,:target,:parameters_hash,:status,:created_at,:expires_at)''',row)

def get_approval(approval_id):
    with connect() as c:
        row=c.execute('SELECT * FROM approvals WHERE approval_id=?',(approval_id,)).fetchone()
        return dict(row) if row else None

def update_approval(approval_id, **fields):
    if not fields:return False
    cols=', '.join(f'{k}=?' for k in fields); vals=list(fields.values())+[approval_id]
    with connect() as c:
        cur=c.execute(f'UPDATE approvals SET {cols} WHERE approval_id=?',vals)
        return cur.rowcount==1

def insert_audit(row: dict):
    with connect() as c:
        c.execute('''INSERT INTO audit_events(audit_id,timestamp,actor,agent,action,risk_level,target,parameters_hash,approval_id,status,duration_ms,result,error_code,correlation_id)
                     VALUES(:audit_id,:timestamp,:actor,:agent,:action,:risk_level,:target,:parameters_hash,:approval_id,:status,:duration_ms,:result,:error_code,:correlation_id)''',row)

def get_audit(audit_id):
    with connect() as c:
        r=c.execute('SELECT * FROM audit_events WHERE audit_id=?',(audit_id,)).fetchone(); return dict(r) if r else None

def list_audit(limit=100, actor=None, agent=None, action=None, risk_level=None, status=None, correlation_id=None, date_from=None, date_to=None):
    where=[]; args=[]
    for col,val in [('actor',actor),('agent',agent),('action',action),('risk_level',risk_level),('status',status),('correlation_id',correlation_id)]:
        if val: where.append(f'{col}=?'); args.append(val)
    if date_from: where.append('timestamp>=?');args.append(date_from)
    if date_to: where.append('timestamp<=?');args.append(date_to)
    q='SELECT * FROM audit_events'+((' WHERE '+' AND '.join(where)) if where else '')+' ORDER BY timestamp DESC LIMIT ?';args.append(max(1,min(int(limit),1000)))
    with connect() as c:return [dict(r) for r in c.execute(q,args).fetchall()]

def last_execution_for(agent_name):
    with connect() as c:
        r=c.execute('SELECT timestamp FROM audit_events WHERE agent=? ORDER BY timestamp DESC LIMIT 1',(agent_name,)).fetchone()
        return r['timestamp'] if r else None

def create_automation(name,agent,action,parameters,schedule,enabled,actor):
    now=utcnow_iso()
    with connect() as c:
        cur=c.execute('''INSERT INTO automations(name,agent,action,parameters_json,schedule,enabled,status,created_by,created_at,updated_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?)''',(name,agent,action,json.dumps(parameters,ensure_ascii=False),schedule,1 if enabled else 0,'IDLE',actor,now,now))
        return cur.lastrowid

def _automation_row(r):
    x=dict(r);x['enabled']=bool(x['enabled'])
    try:x['parameters']=json.loads(x.pop('parameters_json'))
    except Exception:x['parameters']={};x.pop('parameters_json',None)
    return x

def list_automations():
    with connect() as c:return [_automation_row(r) for r in c.execute('SELECT * FROM automations ORDER BY id DESC').fetchall()]

def get_automation(aid):
    with connect() as c:r=c.execute('SELECT * FROM automations WHERE id=?',(aid,)).fetchone();return _automation_row(r) if r else None

def set_automation_enabled(aid,enabled):
    with connect() as c:return c.execute('UPDATE automations SET enabled=?,updated_at=? WHERE id=?',(1 if enabled else 0,utcnow_iso(),aid)).rowcount==1

def delete_automation(aid):
    with connect() as c:return c.execute('DELETE FROM automations WHERE id=?',(aid,)).rowcount==1

def update_automation_schedule(aid, *, last_run=None, next_run=None, status=None):
    fields={'updated_at':utcnow_iso()}
    if last_run is not None:fields['last_run']=last_run
    if next_run is not None:fields['next_run']=next_run
    if status is not None:fields['status']=status
    cols=', '.join(f'{k}=?' for k in fields);args=list(fields.values())+[aid]
    with connect() as c:c.execute(f'UPDATE automations SET {cols} WHERE id=?',args)

def automation_history_start(aid):
    with connect() as c:
        cur=c.execute('INSERT INTO automation_history(automation_id,started_at,status) VALUES(?,?,?)',(aid,utcnow_iso(),'RUNNING'));return cur.lastrowid

def automation_history_finish(hid,status,message,audit_id=None):
    with connect() as c:c.execute('UPDATE automation_history SET completed_at=?,status=?,message=?,audit_id=? WHERE id=?',(utcnow_iso(),status,str(message)[:2000],audit_id,hid))

def list_automation_history(aid=None,limit=100):
    with connect() as c:
        if aid:rows=c.execute('SELECT * FROM automation_history WHERE automation_id=? ORDER BY id DESC LIMIT ?',(aid,limit)).fetchall()
        else:rows=c.execute('SELECT * FROM automation_history ORDER BY id DESC LIMIT ?',(limit,)).fetchall()
        return [dict(r) for r in rows]
