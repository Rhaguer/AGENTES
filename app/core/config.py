from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'HAGUER Agent Platform REAL'
    app_env: str = 'development'
    app_host: str = '127.0.0.1'
    app_port: int = 8000
    require_approval_for_writes: bool = True
    timezone: str = 'America/Santiago'

    ms_client_id: str | None = None
    ms_tenant_id: str = 'organizations'
    ms_enable_teams_channels: bool = False

    google_credentials_file: str = 'secrets/google_credentials.json'
    google_token_file: str = 'data/google_token.json'

    github_token: str | None = None
    github_api_version: str = '2026-03-10'
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @property
    def data_dir(self) -> Path:
        p=Path('data'); p.mkdir(exist_ok=True); return p

settings=Settings()
