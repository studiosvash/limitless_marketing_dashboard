"""
pipeline/utils/db_connection.py — SQLAlchemy session factory for the analytics DB.

Gets the DB path from Django settings when available, falls back to env var.
Exposes get_session() context manager — same interface used by all connectors.
"""
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from pipeline.db.engine import get_engine
from pipeline.utils.logger import get_logger

logger = get_logger("db")

_SessionFactory = None
_factory_lock = threading.Lock()


def _get_db_path() -> str:
    try:
        from django.conf import settings
        if hasattr(settings, "ANALYTICS_DB_PATH"):
            return settings.ANALYTICS_DB_PATH
    except Exception:
        pass
    env_path = os.getenv("ANALYTICS_DB_PATH")
    if env_path:
        return env_path
    # Default: fusehealth/data/fusehealth.db (3 levels up from pipeline/utils/)
    return str(Path(__file__).parent.parent.parent / "data" / "fusehealth.db")


def _configure_sqlite(dbapi_conn, connection_record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


def _get_session_factory() -> sessionmaker:
    global _SessionFactory
    if _SessionFactory is None:
        with _factory_lock:
            if _SessionFactory is None:
                db_path = _get_db_path()
                engine = get_engine(db_path)
                if str(db_path) != ":memory:":
                    event.listen(engine, "connect", _configure_sqlite)
                _SessionFactory = sessionmaker(engine, expire_on_commit=False)
                logger.info(f"[db] Analytics DB: {db_path}")
    return _SessionFactory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"[db] Session error — rolled back: {exc}")
        raise
    finally:
        session.close()
