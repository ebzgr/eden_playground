"""Application configuration via environment variables."""

import shutil
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent
# SQLite needs a writable directory for WAL/journal files. Project trees on
# fuseblk (common in this workspace) often reject those writes at runtime.
_DEFAULT_DB_PATH = Path("/tmp/eden_playground.db")


def _bootstrap_database_file() -> Path:
    """Use /tmp for the live DB; copy repo playground.db once if present."""
    if _DEFAULT_DB_PATH.exists():
        return _DEFAULT_DB_PATH
    repo_db = _REPO_ROOT / "playground.db"
    if repo_db.exists():
        try:
            shutil.copy2(repo_db, _DEFAULT_DB_PATH)
        except OSError:
            pass
    return _DEFAULT_DB_PATH


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Eden Playground"
    debug: bool = False

    database_url: str = Field(
        default_factory=lambda: f"sqlite+aiosqlite:///{_bootstrap_database_file()}"
    )

    server_salt: str = "change-me-in-production-use-env-var"
    return_code_cookie: str = "return_code"
    return_code_max_age_days: int = 365

    admin_auth_enabled: bool = False
    admin_username: str = "admin"
    admin_password: str = "admin"

    worlds_content_dir: Path = Path(__file__).resolve().parent / "worlds_content"

    event_flush_max_batch: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
