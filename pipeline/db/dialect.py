"""
pipeline/db/dialect.py — the single place that answers "which database is this?".

The analytics layer has to run on two backends at once: SQLite (dev, and every
test in the suite, which drives temp .db files) and PostgreSQL (production, where
the analytics tables live in the same database as Django's). Two differences
cannot be papered over by SQLAlchemy Core:

  * `on_conflict_do_update` lives on the *dialect-specific* insert construct.
    `sqlalchemy.dialects.sqlite.insert` emits `ON CONFLICT ... DO UPDATE` that
    only the SQLite driver accepts; Postgres needs its own. The two constructs
    expose the same `.on_conflict_do_update(index_elements=..., set_=...)` and
    `stmt.excluded.<col>` API in SQLAlchemy 2.x, so swapping the constructor is
    the whole port.
  * SQLite caps a statement at ~999 bound parameters, which is why every writer
    inserts in batches of 40–80 rows. Postgres allows 65535, so holding it to
    the SQLite ceiling would mean ~20x more round-trips than necessary.

The answer is derived from the live connection rather than from a setting,
because a caller can hold a session against a temp SQLite file even when
settings point at Postgres (that is exactly what the test suite does).
"""

from sqlalchemy.dialects.postgresql import insert as _pg_insert
from sqlalchemy.dialects.sqlite import insert as _sqlite_insert

# SQLite's ~999-bound-parameter ceiling, expressed as rows; callers pass the value
# their table's column count has always been tuned for.
SQLITE_DEFAULT_BATCH = 60
# Postgres allows 65535 parameters per statement; 1000 rows stays well inside it
# even for the widest analytics table (~20 columns → ~20k parameters).
POSTGRES_MAX_BATCH = 1000


def _bind(session_or_bind):
    """Accept a Session, Engine or Connection and return something with .dialect.

    Callers pass whatever they already have in hand — writers hold a Session,
    `ensure_tables` holds a bind — and should not have to care which.
    """
    get_bind = getattr(session_or_bind, "get_bind", None)
    if get_bind is not None:
        return get_bind()
    return session_or_bind


def dialect_name(session_or_bind) -> str:
    """Return the SQLAlchemy dialect name: 'sqlite' or 'postgresql'."""
    return _bind(session_or_bind).dialect.name


def is_postgres(session_or_bind) -> bool:
    return dialect_name(session_or_bind) == "postgresql"


def upsert_insert(session_or_bind):
    """Return the `insert` constructor whose on_conflict_do_update this backend understands."""
    return _pg_insert if is_postgres(session_or_bind) else _sqlite_insert


def max_batch_size(session_or_bind, sqlite_batch: int = SQLITE_DEFAULT_BATCH) -> int:
    """Rows per insert statement for this backend.

    `sqlite_batch` preserves each writer's existing, hand-tuned SQLite batch size
    so the SQLite path keeps issuing byte-identical statements; only Postgres
    gets the larger batch.
    """
    return POSTGRES_MAX_BATCH if is_postgres(session_or_bind) else sqlite_batch
