import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_FILE=Path('logs/audit.jsonl')
AUDIT_FILE.parent.mkdir(parents=True,exist_ok=True)

def audit(event: dict):
    safe={k:v for k,v in event.items() if k.lower() not in {'token','access_token','refresh_token','authorization','secret','client_secret'}}
    row={'ts': datetime.now(timezone.utc).isoformat(), **safe}
    with AUDIT_FILE.open('a',encoding='utf-8') as f:
        f.write(json.dumps(row,ensure_ascii=False,default=str)+'\n')
