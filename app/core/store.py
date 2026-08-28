import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB=Path('data/agent_platform.sqlite3')
DB.parent.mkdir(parents=True,exist_ok=True)

def connect():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.executescript("""
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
        """)

def now_iso(): return datetime.now(timezone.utc).isoformat()

def create_task(title,due_at=None,source=None,source_id=None):
    with connect() as c:
        cur=c.execute('INSERT INTO tasks(title,due_at,source,source_id,created_at) VALUES(?,?,?,?,?)',
                      (title,due_at,source,source_id,now_iso()))
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

def create_reminder(text,run_at):
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
