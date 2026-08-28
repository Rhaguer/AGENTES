import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import os
os.environ.setdefault('APP_ENV','testing')
import pytest
from app.core import store

@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db=tmp_path/'test.sqlite3';monkeypatch.setattr(store,'DB',db);store.init_db();yield db
