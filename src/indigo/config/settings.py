from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv_file(path: Path) -> None:
    """
    Minimal .env loader (no dependency).
    - ignores blank lines and comments (# ...)
    - supports KEY=VALUE (VALUE may be quoted)
    - does NOT override existing environment variables
    """
    if not path.exists():
        return

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        k, v = line.split("=", 1)
        key = k.strip()
        val = v.strip()

        # strip surrounding quotes
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]

        # don't override already-set env vars
        os.environ.setdefault(key, val)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    return int(v)


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    return float(v)


def _env_csv_ints(name: str, default: list[int]) -> list[int]:
    v = os.getenv(name)
    if v is None or not v.strip():
        return default

    # tolerate formats like "1,2,3" or "[1,2,3]"
    cleaned = v.strip().strip("[](){}")
    return [int(x.strip()) for x in cleaned.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    # Core toggles (keep stable for deployment)
    ENABLE_API: bool
    ENABLE_UI: bool

    # Mode
    SIMULATION_MODE: bool

    # API
    API_HOST: str
    API_PORT: int

    # Polling
    POLL_HZ: float

    # Addresses
    LANE_ADDRS: tuple[int, ...]
    UTILITY_ADDR: int

    # Storage/logging
    INDIGO_DATA_DIR: Path
    LOG_DIR: Path
    LOG_LEVEL: str

    # Database
    DATABASE_URL: str
    SQLITE_WAL: bool

    @staticmethod
    def load() -> Settings:
        """
        Loads settings from:
          1) OS env vars
          2) .env file (if present) for missing vars only
        """
        _load_dotenv_file(Path(".env"))

        data_dir = Path(os.getenv("INDIGO_DATA_DIR", ".indigo_data")).resolve()
        log_dir = Path(os.getenv("INDIGO_LOG_DIR", str(data_dir / "logs"))).resolve()

        lane_addrs = tuple(_env_csv_ints("LANE_ADDRS", [1, 2, 3, 4, 5, 6, 7, 8, 9]))

        # Default DB path under INDIGO_DATA_DIR if not specified
        default_db = f"sqlite:///{(data_dir / 'indigo.db').as_posix()}"

        return Settings(
            ENABLE_API=_env_bool("ENABLE_API", True),
            ENABLE_UI=_env_bool("ENABLE_UI", False),
            SIMULATION_MODE=_env_bool("SIMULATION_MODE", True),
            API_HOST=os.getenv("API_HOST", "127.0.0.1"),
            API_PORT=_env_int("API_PORT", 5000),
            POLL_HZ=_env_float("POLL_HZ", 2.0),
            LANE_ADDRS=lane_addrs,
            UTILITY_ADDR=_env_int("UTILITY_ADDR", 9),
            INDIGO_DATA_DIR=data_dir,
            LOG_DIR=log_dir,
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            DATABASE_URL=os.getenv("DATABASE_URL", default_db),
            SQLITE_WAL=_env_bool("SQLITE_WAL", True),
        )


_SETTINGS: Settings | None = None


def get_settings() -> Settings:
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = Settings.load()
    return _SETTINGS
