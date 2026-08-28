import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB = Path('data/agent_platform.sqlite3')
DB.parent.mkdir(parents=True, exist_ok=True)

def connect():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    return c

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def init_db():
    with connect() as c:
        c.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS tasks(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          due_at TEXT,
          status TEXT NOT NULL DEFAULT 'pending',
          source TEXT,
          source_id TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reminders(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          text TEXT NOT NULL,
          run_at TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          action TEXT NOT NULL,
          payload TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS automations(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          agent TEXT NOT NULL,
          action TEXT NOT NULL,
          payload_json TEXT NOT NULL DEFAULT '{}',
          interval_minutes INTEGER NOT NULL DEFAULT 60,
          enabled INTEGER NOT NULL DEFAULT 1,
          last_run_at TEXT,
          last_status TEXT,
          last_message TEXT,
          created_at TEXT NOT NULL
        );
        ''')

def create_task(title, due_at=None, source=None, source_id=None):
    with connect() as c:
        cur = c.execute(
            'INSERT INTO tasks(title,due_at,source,source_id,created_at) VALUES(?,?,?,?,?)',
            (title, due_at, source, source_id, now_iso())
        )
        return cur.lastrowid

def list_tasks(status=None):
    with connect() as c:
        if status:
            rows=c.execute('SELECT * FROM tasks WHERE status=? ORDER BY id DESC',(status,)).fetchall()
        else:
            rows=c.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
    return [dict(r) for r in rows]

def complete_task(task_id):
    with connect() as c:
        cur=c.execute("UPDATE tasks SET status='completed' WHERE id=?",(task_id,))
        return cur.rowcount == 1

def create_reminder(text, run_at):
    with connect() as c:
        cur=c.execute('INSERT INTO reminders(text,run_at,created_at) VALUES(?,?,?)',(text,run_at,now_iso()))
        return cur.lastrowid

def list_reminders(status=None):
    with connect() as c:
        if status:
            rows=c.execute('SELECT * FROM reminders WHERE status=? ORDER BY run_at',(status,)).fetchall()
        else:
            rows=c.execute('SELECT * FROM reminders ORDER BY run_at').fetchall()
    return [dict(r) for r in rows]

def mark_reminder_fired(reminder_id):
    with connect() as c:
        c.execute("UPDATE reminders SET status='fired' WHERE id=?",(reminder_id,))

def create_automation(name, agent, action, payload, interval_minutes, enabled=True):
    payload_json=json.dumps(payload or {}, ensure_ascii=False)
    interval_minutes=max(1,int(interval_minutes))
    with connect() as c:
        cur=c.execute('''
          INSERT INTO automations(name,agent,action,payload_json,interval_minutes,enabled,created_at)
          VALUES(?,?,?,?,?,?,?)
        ''',(name,agent,action,payload_json,interval_minutes,1 if enabled else 0,now_iso()))
        return cur.lastrowid

def list_automations():
    with connect() as c:
        rows=c.execute('SELECT * FROM automations ORDER BY id DESC').fetchall()
    out=[]
    for row in rows:
        item=dict(row)
        raw=item.pop('payload_json','{}')
        try: item['payload']=json.loads(raw)
        except Exception: item['payload']={}
        item['enabled']=bool(item['enabled'])
        out.append(item)
    return out

def get_automation(automation_id):
    with connect() as c:
        row=c.execute('SELECT * FROM automations WHERE id=?',(automation_id,)).fetchone()
    if not row: return None
    item=dict(row)
    raw=item.pop('payload_json','{}')
    try: item['payload']=json.loads(raw)
    except Exception: item['payload']={}
    item['enabled']=bool(item['enabled'])
    return item

def set_automation_enabled(automation_id, enabled):
    with connect() as c:
        cur=c.execute('UPDATE automations SET enabled=? WHERE id=?',(1 if enabled else 0,automation_id))
        return cur.rowcount == 1

def delete_automation(automation_id):
    with connect() as c:
        cur=c.execute('DELETE FROM automations WHERE id=?',(automation_id,))
        return cur.rowcount == 1

def update_automation_run(automation_id, ok, message):
    with connect() as c:
        c.execute('''UPDATE automations SET last_run_at=?,last_status=?,last_message=? WHERE id=?''',
                  (now_iso(),'ok' if ok else 'error',str(message)[:1000],automation_id))
