from __future__ import annotations
import json, logging
from pathlib import Path
from app.core.config import settings
from app.core.utils import redact, utcnow_iso

LOG_PATH=Path(settings.log_file);LOG_PATH.parent.mkdir(parents=True,exist_ok=True)
logger=logging.getLogger('haguer');logger.setLevel(logging.INFO)

def log_event(level='INFO', **fields):
    payload=redact({'timestamp':utcnow_iso(),'level':level,**fields})
    line=json.dumps(payload,ensure_ascii=False,default=str)
    with LOG_PATH.open('a',encoding='utf-8') as f:f.write(line+'\n')
    getattr(logger,level.lower(),logger.info)(line)
