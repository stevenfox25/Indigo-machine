from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration. Loaded from environment (and optionally a .env file).

    Key design goals:
    - Works on dev PC and SBC
    - Defaults safe for local dev
    - Single place for feature flags (SIMULATION / ENABLE_UI)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Feature flags
    simulation: bool = True
    enable_ui: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Data storage
    indigo_data_dir: str = "./.indigo_data"

    # DB
    database_url: str = "sqlite:///./.indigo_data/indigo.db"
    sqlite_wal: bool = True

    def data_dir_path(self) -> Path:
        return Path(self.indigo_data_dir).resolve()


def get_settings() -> Settings:
    """
    Factory so we have a single import path throughout the codebase.
    """
    return Settings()
