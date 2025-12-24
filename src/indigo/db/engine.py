from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from indigo.config.settings import Settings


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    # database_url example: sqlite:///./.indigo_data/indigo.db
    if not database_url.startswith("sqlite:///"):
        return

    sqlite_path = database_url.replace("sqlite:///", "", 1)
    p = Path(sqlite_path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)


def create_db_engine(settings: Settings):
    """
    Create a SQLAlchemy engine.
    For SQLite, we enable WAL mode (recommended for concurrent readers).
    """
    _ensure_sqlite_parent_dir(settings.database_url)

    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        # SQLite: needed when using threads (Flask + background services)
        connect_args["check_same_thread"] = False

    engine = create_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    if settings.database_url.startswith("sqlite") and settings.sqlite_wal:
        # Enable WAL + some sane defaults
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA synchronous=NORMAL;"))
            conn.execute(text("PRAGMA foreign_keys=ON;"))
            conn.commit()

    return engine


def create_session_factory(engine):
    """
    Session factory. Services and API should use sessions from here.
    """
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
