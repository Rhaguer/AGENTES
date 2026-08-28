from __future__ import annotations
import os, subprocess
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

class EncryptedStore:
    def __init__(self):
        self.key_path=Path(settings.secret_key_file)
        self.key_path.parent.mkdir(parents=True,exist_ok=True)
        self._key=self._load_or_create_key()
        self.fernet=Fernet(self._key)

    def _load_or_create_key(self):
        env=os.getenv('HAGUER_MASTER_KEY')
        if env:return env.encode('utf-8')
        if self.key_path.exists():return self.key_path.read_bytes().strip()
        key=Fernet.generate_key();self.key_path.write_bytes(key);self._tighten(self.key_path);return key

    def write_text(self,path,text):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(self.fernet.encrypt(text.encode('utf-8')))
        self._tighten(p)

    def read_text(self,path):
        p=Path(path)
        if not p.exists():return None
        try:return self.fernet.decrypt(p.read_bytes()).decode('utf-8')
        except InvalidToken:return None

    def _tighten(self,p):
        try:os.chmod(p,0o600)
        except OSError:pass
        if os.name=='nt':
            user=os.environ.get('USERNAME');domain=os.environ.get('USERDOMAIN')
            principal=f'{domain}\\{user}' if domain and user else user
            if principal:
                try:subprocess.run(['icacls',str(p),'/inheritance:r','/grant:r',f'{principal}:(F)'],capture_output=True,timeout=10,check=False)
                except Exception:pass
    def delete(self,path):
        p=Path(path)
        if p.exists():p.unlink()

secret_store=EncryptedStore()
