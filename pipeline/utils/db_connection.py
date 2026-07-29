"""
pipeline/utils/db_connection.py — SQLAlchemy session factory for the analytics DB.

Resolves the analytics DB from Django settings when available, falling back to
env vars and finally to the bundled SQLite file. Exposes get_session() context
manager — same interface used by all connectors.
"""
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from pipeline.db.engine import get_engine
from pipeline.utils.logger import get_logger

logger = get_logger("db")

_SessionFactory = None
_factory_lock = threading.Lock()


def _get_db_url() -> str:
    """
    Resolve the analytics DB to a full SQLAlchemy URL.

    Order, most specific first:
      1. settings.ANALYTICS_DB_URL  — production; a complete URL (Postgres).
      2. env ANALYTICS_DB_URL       — same, outside Django (standalone pipeline runs).
      3. settings.ANALYTICS_DB_PATH — a filesystem path; this is what the entire
         test suite drives via override_settings, so it must keep working.
      4. env ANALYTICS_DB_PATH
      5. the bundled data/fusehealth.db

    The URL settings are checked for truthiness, not existence: config/settings
    defines ANALYTICS_DB_URL = None in the no-Postgres branch, and that must fall
    through to the SQLite path rather than being taken as "configured".
    """
    settings = _django_settings()

    if settings is not None and getattr(settings, "ANALYTICS_DB_URL", None):
        return str(settings.ANALYTICS_DB_URL)

    env_url = os.getenv("ANALYTICS_DB_URL")
    if env_url:
        return env_url

    if settings is not None and hasattr(settings, "ANALYTICS_DB_PATH"):
        return _as_sqlite_url(settings.ANALYTICS_DB_PATH)

    env_path = os.getenv("ANALYTICS_DB_PATH")
    if env_path:
        return _as_sqlite_url(env_path)

    # Default: fusehealth/data/fusehealth.db (3 levels up from pipeline/utils/)
    return _as_sqlite_url(Path(__file__).parent.parent.parent / "data" / "fusehealth.db")


def _django_settings():
    """Django's settings, or None when the pipeline runs standalone (no Django).

    Accessing settings raises if DJANGO_SETTINGS_MODULE is unset — the pipeline is
    deliberately runnable on its own, so that is a fallback signal, not an error.
    """
    try:
        from django.conf import settings
        if not settings.configured:
            return None
    except Exception:
        return None
    return settings


def _get_db_path() -> str:
    """Back-compat alias — the resolved value is now a URL, not a bare path.

    Kept because callers and older docs reference this name.
    """
    return _get_db_url()


def _as_sqlite_url(path) -> str:
    return f"sqlite:///{path}"


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
                db_url = _get_db_url()
                engine = get_engine(db_url)
                # PRAGMAs are SQLite syntax — issuing them on Postgres is a hard
                # error on every new connection. WAL/synchronous are also
                # meaningless for an in-memory DB, which is why :memory: was
                # always excluded.
                if engine.dialect.name == "sqlite" and not db_url.endswith(":memory:"):
                    event.listen(engine, "connect", _configure_sqlite)
                _SessionFactory = sessionmaker(engine, expire_on_commit=False)
                logger.info(f"[db] Analytics DB: {_safe_url(db_url)}")
    return _SessionFactory


def _safe_url(db_url: str) -> str:
    """Mask the password before logging — a Postgres DSN carries credentials."""
    try:
        return make_url(db_url).render_as_string(hide_password=True)
    except Exception:
        return db_url


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
