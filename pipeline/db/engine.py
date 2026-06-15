"""
SQLAlchemy engine/session factory for the analytics DB (fusehealth.db).

Pure SQLAlchemy — no Django import — so the pipeline stays reusable and testable
on its own. Code inside Django passes settings.ANALYTICS_DB_PATH; tests pass
':memory:'.
"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def get_engine(db_path: str) -> Engine:
    """
    Create a SQLAlchemy engine for the SQLite analytics DB at db_path.

    db_path may be ':memory:' for tests. For file paths, parent directories are
    created so first-run on a fresh checkout does not fail.
    """
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def get_sessionmaker(db_path: str) -> sessionmaker:
    """
    Return a sessionmaker bound to a fresh engine for db_path.

    Creates a NEW engine on every call — call this ONCE at startup and reuse the
    returned sessionmaker. Calling it per-request would open a new connection pool
    each time. Note: each call with ':memory:' yields a SEPARATE in-memory database.
    """
    return sessionmaker(bind=get_engine(db_path), future=True)
