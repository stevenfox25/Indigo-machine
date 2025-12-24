from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from indigo.config.settings import Settings, get_settings
from indigo.db.orm.tables import Base


def build_engine(settings: Settings):
    engine = create_engine(
        settings.DATABASE_URL,
        future=True,
        connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    )

    # Optional WAL mode for SQLite (recommended on SBC)
    if settings.DATABASE_URL.startswith("sqlite") and settings.SQLITE_WAL:
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")

    return engine


def init_db(settings: Settings) -> sessionmaker:
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


_SESSION_FACTORY: sessionmaker | None = None


def get_session_factory() -> sessionmaker:
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = init_db(get_settings())
    return _SESSION_FACTORY
