"""
SQLAlchemy engine/session factory for the analytics DB.

Pure SQLAlchemy — no Django import — so the pipeline stays reusable and testable
on its own. Code inside Django passes settings.ANALYTICS_DB_URL (or, when no
Postgres is configured, the SQLite file at settings.ANALYTICS_DB_PATH); tests
pass ':memory:' or a temp file path.
"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def get_engine(db_path_or_url: str) -> Engine:
    """
    Create a SQLAlchemy engine for the analytics DB.

    Accepts either form, because both are live at once:
      * a bare filesystem path (or ':memory:') — the historical SQLite contract
        that every test and management command still passes;
      * a full SQLAlchemy URL such as
        'postgresql+psycopg://user:pw@host:5432/db' — production.

    A URL is anything containing '://'. Bare paths get their parent directories
    created so first-run on a fresh checkout does not fail.
    """
    value = str(db_path_or_url)

    if "://" in value:
        if value.startswith("postgresql"):
            # Pooling matters only for a networked server: pre_ping discards
            # connections the server closed while the worker sat idle between
            # syncs, which is otherwise a guaranteed first-query failure.
            return create_engine(
                value,
                future=True,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
        return create_engine(value, future=True)

    if value != ":memory:":
        Path(value).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{value}", future=True)


def get_sessionmaker(db_path_or_url: str) -> sessionmaker:
    """
    Return a sessionmaker bound to a fresh engine for db_path_or_url.

    Creates a NEW engine on every call — call this ONCE at startup and reuse the
    returned sessionmaker. Calling it per-request would open a new connection pool
    each time. Note: each call with ':memory:' yields a SEPARATE in-memory database.
    """
    return sessionmaker(bind=get_engine(db_path_or_url), future=True)
