from __future__ import annotations
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV = os.getenv('APP_ENV', 'development').strip().lower() or 'development'
ENV_FILE = Path(f'config/{ENV}.env')

class Settings(BaseSettings):
    app_name: str = 'HAGUER Agent Platform'
    app_env: str = ENV
    app_host: str = '127.0.0.1'
    app_port: int = 8000
    api_version: str = 'v1'
    timezone: str = 'America/Santiago'
    debug: bool = True

    database_path: str = 'data/agent_platform.sqlite3'
    log_file: str = 'logs/platform.jsonl'
    secret_key_file: str = 'data/.platform.key'

    default_role: str = 'ADMIN'
    default_actor: str = 'local-user'
    approval_ttl_seconds: int = 300
    approval_require_different_actor: bool = False

    cors_origins: str = 'http://127.0.0.1:8000,http://localhost:8000'
    trusted_hosts: str = '127.0.0.1,localhost'

    rate_auth_per_minute: int = 5
    rate_command_per_minute: int = 30
    rate_agent_per_minute: int = 60
    rate_write_per_minute: int = 10

    provider_timeout_seconds: float = 20.0
    provider_max_retries: int = 3
    provider_backoff_seconds: float = 0.6
    circuit_failure_threshold: int = 4
    circuit_recovery_seconds: int = 45

    ms_client_id: str | None = None
    ms_tenant_id: str | None = None
    ms_enable_teams_channels: bool = False
    ms_scopes: str = 'User.Read Mail.Read Mail.Send Calendars.ReadWrite Chat.Read Team.ReadBasic.All Channel.ReadBasic.All'

    google_credentials_file: str = 'secrets/google_credentials.json'
    google_redirect_uri: str = 'http://127.0.0.1:8000/auth/google/callback'

    github_token: str | None = None
    github_api_version: str = '2022-11-28'

    model_config = SettingsConfigDict(
        env_file=('.env', str(ENV_FILE)),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(',') if x.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [x.strip() for x in self.trusted_hosts.split(',') if x.strip()]

settings = Settings()
