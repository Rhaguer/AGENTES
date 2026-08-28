from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from typing import Any

SENSITIVE_KEYS = {'password','token','access_token','refresh_token','authorization','client_secret','secret','api_key','approval_token'}

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ('[REDACTED]' if k.lower() in SENSITIVE_KEYS else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._~+\-/=]+', r'\1[REDACTED]', value)
        return value
    return value
