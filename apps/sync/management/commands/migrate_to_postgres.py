"""
One-time (but safely repeatable) migration of BOTH SQLite databases into ONE PostgreSQL
database:

  * django_internal.db   (Django ORM tables)      -> Postgres, via the Django connection
  * data/fusehealth.db   (SQLAlchemy analytics)   -> the SAME Postgres database

Why this shape
--------------
config/settings/base.py already supports the target layout: when POSTGRES_DB is set,
`DATABASES["default"]` points at Postgres AND `ANALYTICS_DB_URL` points at the same
database. So this command is run **with POSTGRES_DB set** — Django's own connection is
then already the target, and the two SQLite files are opened separately as sources.

Operator sequence:
    1. createdb / provision the Postgres database
    2. export POSTGRES_DB/USER/PASSWORD/HOST/PORT
    3. python manage.py migrate                    <- creates the Django tables
    4. python manage.py migrate_to_postgres --dry-run
    5. python manage.py migrate_to_postgres

Safety properties (all enforced below, not just claimed):
  * The two SQLite sources are opened with `file:...?mode=ro` — SQLite itself refuses any
    write. Nothing in this command issues an INSERT/UPDATE/DDL against a source.
  * Every write is `INSERT ... ON CONFLICT DO NOTHING`, so a re-run cannot duplicate rows.
  * --dry-run performs no writes at all (not even init_db's CREATE TABLE) and says so.
  * Row counts are read from the target BEFORE and AFTER each table and printed. A table is
    only reported OK when the counts actually justify it; otherwise the run exits non-zero.

Type strictness
---------------
SQLite is dynamically typed; Postgres is not. Values are coerced during the copy, driven by
the DECLARED type of each column (SQLAlchemy `Model.__table__.columns` for analytics,
`model._meta.concrete_fields` for Django) — never by a hardcoded per-table list. See
`_coerce()`.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, time as dt_time, timezone
from decimal import Decimal
from pathlib import Path

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from sqlalchemy import create_engine, inspect as sa_inspect, select, text
from sqlalchemy import types as sa_types
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from pipeline.db.engine import get_engine
from pipeline.db.schema import Base as AnalyticsBase, init_db

# Postgres accepts at most 65535 bound parameters in one statement. Batches are clamped to
# stay inside it regardless of --batch-size, so a wide table can never blow the limit.
PG_MAX_BIND_PARAMS = 60000


# ─────────────────────────────────────────────────────────────────────────────
# Django-side table plan
# ─────────────────────────────────────────────────────────────────────────────
# Ordered so foreign keys always resolve: parents before children. Primary keys are
# preserved verbatim (raw SQL, so `auto_now_add`/`auto_now` cannot silently rewrite
# created_at/updated_at the way saving through model instances would).
DJANGO_TABLE_ORDER = [
    "auth_group",
    "auth_user",
    "auth_user_groups",
    "authtoken_token",
    "django_session",
    "accounts_userprofile",
    "accounts_userinvitation",
    "dashboard_insight",
    "dashboard_aitarget",
    "dashboard_aipromptlist",
    "dashboard_aiprompt",
    "dashboard_projectsettings",
    "sync_synclog",
    "sync_refreshrun",
]

# Deliberately NOT copied, with the reason. Their source row counts are still printed so
# nothing is quietly dropped — a non-zero count on any of these is reported as a WARNING.
DJANGO_TABLES_SKIPPED = {
    "django_migrations": "target builds its own history via `manage.py migrate`",
    "django_content_type": "recreated by `migrate`; IDs are target-generated",
    "auth_permission": "recreated by `migrate`; IDs are target-generated",
    "auth_group_permissions": "references auth_permission IDs that differ in the target",
    "auth_user_user_permissions": "references auth_permission IDs that differ in the target",
    "django_admin_log": "references django_content_type IDs that differ in the target",
    "sqlite_sequence": "SQLite-internal bookkeeping, has no Postgres equivalent",
}

# Postgres column types that a plain text/str parameter cannot be assigned to without an
# explicit cast. Keyed on information_schema.columns.data_type.
PG_CAST_BY_DATA_TYPE = {"jsonb": "jsonb", "json": "json", "uuid": "uuid"}

# Per-table outcome statuses used by the final report.
OK = "ok"
DRY = "would-migrate"
ABSENT = "absent-in-source"
SKIPPED = "skipped-by-design"
MISMATCH = "MISMATCH"


class Command(BaseCommand):
    help = (
        "Migrate django_internal.db and data/fusehealth.db into one PostgreSQL database. "
        "Idempotent, read-only on the sources, and verified by before/after row counts."
    )

    # ── arguments ────────────────────────────────────────────────────────────

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what WOULD be migrated. Performs no writes and no DDL.",
        )
        parser.add_argument(
            "--only",
            choices=["django", "analytics"],
            default=None,
            help="Migrate only one side. Default: both.",
        )
        parser.add_argument(
            "--django-source",
            default=None,
            help="Path to the source django_internal.db (default: BASE_DIR/django_internal.db "
                 "or $DJANGO_INTERNAL_DB).",
        )
        parser.add_argument(
            "--analytics-source",
            default=None,
            help="Path to the source analytics SQLite DB (default: settings.ANALYTICS_DB_PATH).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=2000,
            help="Rows fetched/inserted per batch (default 2000). Tables are never loaded whole.",
        )

    # ── entry point ──────────────────────────────────────────────────────────

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        only = opts["only"]
        batch = max(1, int(opts["batch_size"]))
        pg = self._pg_settings()

        self.stdout.write("=" * 78)
        self.stdout.write("SQLite -> PostgreSQL migration")
        self.stdout.write(
            f"  target : postgresql://{pg['user'] or '<no-user>'}@{pg['host']}:{pg['port']}/{pg['db']}"
        )
        self.stdout.write(f"  mode   : {'DRY RUN (no writes)' if dry else 'LIVE'}")
        self.stdout.write(f"  scope  : {only or 'django + analytics'}")
        self.stdout.write("=" * 78)

        results: list[dict] = []
        if only in (None, "django"):
            results += self._migrate_django(opts, pg, dry, batch)
        if only in (None, "analytics"):
            results += self._migrate_analytics(opts, pg, dry, batch)

        self._report(results, dry)

    # ── configuration / guards ───────────────────────────────────────────────

    def _pg_settings(self) -> dict:
        """Read the target connection from the SAME env vars config/settings/base.py uses."""
        db = os.environ.get("POSTGRES_DB") or getattr(settings, "POSTGRES_DB", "") or ""
        if not db:
            raise CommandError(
                "POSTGRES_DB is not set - there is no target database to migrate into.\n"
                "Set the Postgres environment variables before running this command, e.g.\n"
                "    POSTGRES_DB=fusehealth\n"
                "    POSTGRES_USER=fusehealth\n"
                "    POSTGRES_PASSWORD=...\n"
                "    POSTGRES_HOST=localhost      (default: localhost)\n"
                "    POSTGRES_PORT=5432           (default: 5432)\n"
                "Then run `python manage.py migrate` against Postgres first, and re-run this "
                "command. Note the same variables also switch Django's own `default` database "
                "over to Postgres (see config/settings/base.py), which is exactly what this "
                "migration needs."
            )
        # Both layers reach Postgres through psycopg 3 (Django's backend and SQLAlchemy's
        # postgresql+psycopg dialect). Check it up front so the operator gets an install
        # hint instead of a Django ImproperlyConfigured traceback halfway through.
        try:
            import psycopg  # noqa: F401
        except ImportError as exc:
            raise CommandError(
                "The PostgreSQL driver is not installed, so nothing can connect to the "
                f"target ({exc}).\n"
                '    pip install "psycopg[binary]>=3.2"    (already in requirements.txt)'
            ) from exc

        return {
            "db": db,
            "user": os.environ.get("POSTGRES_USER") or getattr(settings, "POSTGRES_USER", "") or "",
            "password": os.environ.get("POSTGRES_PASSWORD")
            or getattr(settings, "POSTGRES_PASSWORD", "")
            or "",
            "host": os.environ.get("POSTGRES_HOST")
            or getattr(settings, "POSTGRES_HOST", "")
            or "localhost",
            "port": str(
                os.environ.get("POSTGRES_PORT")
                or getattr(settings, "POSTGRES_PORT", "")
                or "5432"
            ),
        }

    @staticmethod
    def _analytics_dsn(pg: dict) -> str:
        """SQLAlchemy DSN for the target — same construction as settings.ANALYTICS_DB_URL."""
        from urllib.parse import quote_plus

        return (
            f"postgresql+psycopg://{quote_plus(pg['user'])}:{quote_plus(pg['password'])}"
            f"@{pg['host']}:{pg['port']}/{pg['db']}"
        )

    # ── read-only source helpers ─────────────────────────────────────────────

    @staticmethod
    def _ro_uri(path: Path) -> str:
        """SQLite URI that makes the source physically read-only (writes raise)."""
        return f"file:{path.resolve().as_posix()}?mode=ro"

    def _ro_sqlite(self, path: Path) -> sqlite3.Connection:
        return sqlite3.connect(self._ro_uri(path), uri=True)

    def _ro_engine(self, path: Path) -> Engine:
        """SQLAlchemy engine over a read-only SQLite connection.

        A custom `creator` is used rather than a `sqlite:///<path>` URL because the URL form
        cannot express `mode=ro`, and because Windows paths with drive letters and spaces
        survive `sqlite3.connect(uri=True)` cleanly.
        """
        uri = self._ro_uri(path)
        return create_engine(
            "sqlite://",
            creator=lambda: sqlite3.connect(uri, uri=True),
            poolclass=NullPool,
            future=True,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Type coercion — the heart of SQLite -> Postgres strictness
    # ─────────────────────────────────────────────────────────────────────────
    # Every column is reduced to one abstract "kind" derived from its DECLARED type on the
    # target side, then `_coerce` applies that kind. Nothing is table-specific:
    #   * analytics: kind comes from the SQLAlchemy Column type object
    #   * django   : kind comes from the model field's internal type
    # None ALWAYS stays None — a NULL is never turned into 0 or "".

    @staticmethod
    def _kind_for_sa_type(coltype) -> str | None:
        """Map a declared SQLAlchemy column type to a coercion kind.

        DateTime is tested before Date on purpose: they are siblings in SQLAlchemy's
        hierarchy, but keeping the order explicit documents the intent and is robust if that
        ever changes. Integer covers SmallInteger/BigInteger via subclassing — which is why
        `Backlink.dofollow`, `Anomaly.is_acknowledged` and `Site.is_active` (declared
        Integer, but frequently written as Python bools) land on "int" and get coerced.
        """
        if isinstance(coltype, sa_types.DateTime):
            return "datetime"
        if isinstance(coltype, sa_types.Date):
            return "date"
        if isinstance(coltype, sa_types.Time):
            return "time"
        if isinstance(coltype, sa_types.Boolean):
            return "bool"
        if isinstance(coltype, sa_types.Integer):
            return "int"
        if isinstance(coltype, sa_types.Float):
            return "float"
        if isinstance(coltype, sa_types.Numeric):
            return "decimal"
        if isinstance(coltype, (sa_types.String, sa_types.Text)):
            return "text"
        return None  # pass through untouched

    _DJANGO_INT_TYPES = {
        "AutoField", "BigAutoField", "SmallAutoField",
        "IntegerField", "BigIntegerField", "SmallIntegerField",
        "PositiveIntegerField", "PositiveSmallIntegerField", "PositiveBigIntegerField",
    }

    @classmethod
    def _kind_for_django_field(cls, field) -> str | None:
        """Map a Django model field to the same coercion kinds.

        For a ForeignKey/OneToOne the relevant type is the *referenced* column's type
        (an AutoField -> int), not "ForeignKey".
        """
        target = field.target_field if (field.is_relation and field.many_to_one) else field
        internal = target.get_internal_type()
        if internal == "BooleanField":
            return "bool"          # SQLite holds 0/1; Postgres wants a real boolean
        if internal == "DateTimeField":
            return "datetime"
        if internal == "DateField":
            return "date"
        if internal == "TimeField":
            return "time"
        if internal == "FloatField":
            return "float"
        if internal == "DecimalField":
            return "decimal"
        if internal in cls._DJANGO_INT_TYPES:
            return "int"
        if internal == "JSONField":
            return None            # already JSON text in SQLite; inserted with a ::jsonb cast
        return None

    @staticmethod
    def _coerce(value, kind: str | None, *, aware: bool = False):
        """Coerce one SQLite value to what the declared Postgres column type accepts.

        `aware=True` attaches UTC to naive datetimes — used for the Django side only, where
        USE_TZ=True means the Postgres columns are `timestamptz` and SQLite stored naive UTC.
        The analytics schema declares plain `DateTime`, so it stays naive.
        """
        if value is None:
            return None            # NULL stays NULL. Never 0, never "".
        if kind is None:
            return value

        if kind == "int":
            # bool is a subclass of int, but be explicit: True -> 1. Floats such as 1.0 that
            # SQLite happily stored in an INTEGER column are rounded, not truncated.
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(round(value))
            s = str(value).strip()
            if s == "":
                return None
            try:
                return int(s)
            except ValueError:
                return int(round(float(s)))

        if kind == "float":
            return float(value)

        if kind == "decimal":
            return value if isinstance(value, Decimal) else Decimal(str(value))

        if kind == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            return str(value).strip().lower() in {"1", "t", "true", "y", "yes"}

        if kind == "date":
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            return date.fromisoformat(str(value)[:10])

        if kind == "datetime":
            dt = value
            if isinstance(dt, datetime):
                pass
            elif isinstance(dt, date):
                dt = datetime.combine(dt, dt_time.min)
            else:
                dt = Command._parse_datetime(str(value))
                if dt is None:
                    return None
            if aware and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if not aware and dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        if kind == "time":
            if isinstance(value, dt_time):
                return value
            return dt_time.fromisoformat(str(value))

        if kind == "text":
            return value if isinstance(value, str) else str(value)

        return value

    @staticmethod
    def _parse_datetime(s: str) -> datetime | None:
        """Tolerant ISO-ish parser. Django/SQLAlchemy both write ISO strings into SQLite, but
        with either a space or a 'T' separator and with or without fractional seconds."""
        s = s.strip()
        if not s:
            return None
        candidate = s[:-1] + "+00:00" if s.endswith("Z") else s
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unparseable datetime value: {s!r}")

    # ─────────────────────────────────────────────────────────────────────────
    # Django side
    # ─────────────────────────────────────────────────────────────────────────

    def _django_source_path(self, opts) -> Path:
        if opts["django_source"]:
            return Path(opts["django_source"])
        env_path = os.environ.get("DJANGO_INTERNAL_DB")
        if env_path:
            return Path(env_path)
        return Path(settings.BASE_DIR) / "django_internal.db"

    def _django_column_kinds(self) -> dict[str, dict[str, str | None]]:
        """{db_table: {column: kind}} for every concrete Django model column.

        include_auto_created=True picks up the M2M through tables (e.g. auth_user_groups).
        """
        out: dict[str, dict[str, str | None]] = {}
        for model in django_apps.get_models(include_auto_created=True):
            out[model._meta.db_table] = {
                f.column: self._kind_for_django_field(f) for f in model._meta.concrete_fields
            }
        return out

    @staticmethod
    def _django_pk_columns() -> dict[str, str]:
        return {
            m._meta.db_table: m._meta.pk.column
            for m in django_apps.get_models(include_auto_created=True)
        }

    def _migrate_django(self, opts, pg: dict, dry: bool, batch: int) -> list[dict]:
        self.stdout.write("\n=== Django tables (django_internal.db -> Postgres) ===")
        src_path = self._django_source_path(opts)
        if not src_path.exists():
            raise CommandError(f"Source Django DB not found: {src_path}")
        self.stdout.write(f"  source: {src_path}  (opened read-only)")

        # The Django `default` connection IS the target when POSTGRES_DB is set. Verify that
        # rather than assume it — if the operator set the env var after Django read settings,
        # `default` would still be SQLite and we would happily copy a DB onto itself.
        conn = connections["default"]
        engine = conn.settings_dict.get("ENGINE", "")
        name = conn.settings_dict.get("NAME", "")
        if "postgresql" not in engine or str(name) != pg["db"]:
            raise CommandError(
                "Django's `default` database is not the Postgres target.\n"
                f"  DATABASES['default'] -> ENGINE={engine!r} NAME={name!r}\n"
                f"  expected             -> postgresql / {pg['db']!r}\n"
                "Export POSTGRES_DB (and friends) BEFORE invoking manage.py so "
                "config/settings/base.py selects the Postgres branch."
            )

        sconn = self._ro_sqlite(src_path)
        try:
            src_tables = {
                r[0] for r in sconn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }

            results = [
                self._report_skipped_django(sconn, tbl, reason, src_tables)
                for tbl, reason in DJANGO_TABLES_SKIPPED.items()
            ]

            present = [t for t in DJANGO_TABLE_ORDER if t in src_tables]
            self._assert_target_tables_exist(conn, present)

            kinds = self._django_column_kinds()
            pks = self._django_pk_columns()

            if dry:
                for tbl in DJANGO_TABLE_ORDER:
                    results.append(
                        self._copy_django_table(sconn, conn, tbl, kinds, pks, src_tables,
                                                dry=True, batch=batch)
                    )
            else:
                # One transaction for the whole (small) Django side: a failure anywhere leaves
                # the target untouched and the command cleanly re-runnable.
                with transaction.atomic(using="default"):
                    for tbl in DJANGO_TABLE_ORDER:
                        results.append(
                            self._copy_django_table(sconn, conn, tbl, kinds, pks, src_tables,
                                                    dry=False, batch=batch)
                        )
            return results
        finally:
            sconn.close()

    def _report_skipped_django(self, sconn, table: str, reason: str, src_tables: set) -> dict:
        src_rows = 0
        if table in src_tables:
            src_rows = sconn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        note = reason
        if src_rows:
            note = f"{reason} - {src_rows} source row(s) NOT copied"
            self.stdout.write(self.style.WARNING(f"  {table}: skipped, {note}"))
        else:
            self.stdout.write(f"  {table}: skipped (0 source rows) - {reason}")
        return {
            "side": "django", "table": table, "source": src_rows,
            "before": None, "after": None, "status": SKIPPED, "note": note,
        }

    def _assert_target_tables_exist(self, conn, tables: list[str]) -> None:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = current_schema()"
            )
            existing = {r[0] for r in cur.fetchall()}
        missing = [t for t in tables if t not in existing]
        if missing:
            raise CommandError(
                "The target Postgres database is missing Django tables: "
                + ", ".join(missing)
                + "\nRun `python manage.py migrate` against Postgres before migrating data."
            )

    def _pg_column_types(self, conn, table: str) -> dict[str, str]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = %s",
                [table],
            )
            return {r[0]: r[1] for r in cur.fetchall()}

    def _copy_django_table(self, sconn, conn, table: str, kinds, pks,
                           src_tables: set, *, dry: bool, batch: int) -> dict:
        if table not in src_tables:
            self.stdout.write(f"  {table}: (absent in source, skipped)")
            return {"side": "django", "table": table, "source": 0, "before": None,
                    "after": None, "status": ABSENT, "note": "not present in source DB"}

        src_cols = [r[1] for r in sconn.execute(f'PRAGMA table_info("{table}")')]
        pg_types = self._pg_column_types(conn, table)
        shared = [c for c in src_cols if c in pg_types]
        dropped = [c for c in src_cols if c not in pg_types]

        src_rows = sconn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        before = self._pg_count(conn, table)

        if dry:
            self.stdout.write(
                f"  {table}: source={src_rows}  target now={before}  "
                f"would insert up to {max(0, src_rows)} row(s)"
            )
            return {"side": "django", "table": table, "source": src_rows, "before": before,
                    "after": before, "status": DRY,
                    "note": (f"columns not in target: {', '.join(dropped)}" if dropped else "")}

        col_kinds = kinds.get(table, {})
        placeholders = ", ".join(
            f"%s::{PG_CAST_BY_DATA_TYPE[pg_types[c]]}" if pg_types[c] in PG_CAST_BY_DATA_TYPE
            else "%s"
            for c in shared
        )
        collist = ", ".join(f'"{c}"' for c in shared)
        sql = f'INSERT INTO "{table}" ({collist}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

        cursor = sconn.execute(f'SELECT {collist} FROM "{table}"')
        with conn.cursor() as tcur:
            while True:
                rows = cursor.fetchmany(batch)     # streamed — never the whole table
                if not rows:
                    break
                payload = [
                    tuple(
                        self._coerce(v, col_kinds.get(c), aware=bool(settings.USE_TZ))
                        for c, v in zip(shared, row)
                    )
                    for row in rows
                ]
                tcur.executemany(sql, payload)

        self._reset_pg_sequence_django(conn, table, pks.get(table))
        after = self._pg_count(conn, table)
        return self._finish(conn_side="django", table=table, src_rows=src_rows,
                            before=before, after=after, dropped=dropped)

    @staticmethod
    def _pg_count(conn, table: str) -> int:
        with conn.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            return cur.fetchone()[0]

    def _reset_pg_sequence_django(self, conn, table: str, pk_col: str | None) -> None:
        """PKs are copied verbatim, so the identity/serial sequence must be moved past MAX(pk)
        or the very next application INSERT would raise a duplicate-key error."""
        if not pk_col:
            return
        with conn.cursor() as cur:
            cur.execute("SELECT pg_get_serial_sequence(%s, %s)", [table, pk_col])
            seq = cur.fetchone()[0]
            if not seq:
                return              # non-integer PK (e.g. django_session.session_key)
            cur.execute(
                f'SELECT setval(%s, COALESCE((SELECT MAX("{pk_col}") FROM "{table}"), 1), '
                f'(SELECT MAX("{pk_col}") FROM "{table}") IS NOT NULL)',
                [seq],
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Analytics side
    # ─────────────────────────────────────────────────────────────────────────

    def _migrate_analytics(self, opts, pg: dict, dry: bool, batch: int) -> list[dict]:
        self.stdout.write("\n=== Analytics tables (fusehealth.db -> Postgres) ===")
        src_path = Path(opts["analytics_source"] or settings.ANALYTICS_DB_PATH)
        if not src_path.exists():
            raise CommandError(f"Source analytics DB not found: {src_path}")
        self.stdout.write(f"  source: {src_path}  (opened read-only)")

        src_engine = self._ro_engine(src_path)
        try:
            # Built through pipeline.db.engine.get_engine so the target uses the same
            # pool_pre_ping/pool settings the running application will use.
            target_engine = get_engine(self._analytics_dsn(pg))
            try:
                with target_engine.connect() as probe:
                    probe.execute(text("SELECT 1"))
            except Exception as exc:
                raise CommandError(
                    f"Cannot reach the target Postgres database: {exc}\n"
                    "Check the POSTGRES_* environment variables and that the server is running. "
                    'If the driver is missing, install it with: pip install "psycopg[binary]"'
                ) from exc

            if dry:
                self.stdout.write("  (dry run: init_db() NOT called - no tables created)")
            else:
                init_db(target_engine)   # CREATE TABLE IF NOT EXISTS for all analytics tables

            src_insp = sa_inspect(src_engine)
            tgt_insp = sa_inspect(target_engine)
            src_tables = set(src_insp.get_table_names())

            results = []
            # sorted_tables == every declared Model.__table__; nothing is hardcoded here, so a
            # table added to pipeline/db/schema.py is picked up automatically. These tables have
            # no FKs between them (the join key is the site_url string), so order is irrelevant.
            for tbl in AnalyticsBase.metadata.sorted_tables:
                results.append(
                    self._copy_analytics_table(
                        src_engine, target_engine, src_insp, tgt_insp, tbl,
                        src_tables, dry=dry, batch=batch,
                    )
                )
            return results
        finally:
            src_engine.dispose()

    def _copy_analytics_table(self, src_engine, target_engine, src_insp, tgt_insp, tbl,
                              src_tables: set, *, dry: bool, batch: int) -> dict:
        name = tbl.name
        if name not in src_tables:
            self.stdout.write(f"  {name}: (absent in source, skipped)")
            return {"side": "analytics", "table": name, "source": 0, "before": None,
                    "after": None, "status": ABSENT, "note": "not present in source DB"}

        src_cols = {c["name"] for c in src_insp.get_columns(name)}
        shared = [c.name for c in tbl.columns if c.name in src_cols]
        dropped = sorted(src_cols - {c.name for c in tbl.columns})

        with src_engine.connect() as sconn:
            src_rows = sconn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar_one()

        target_exists = tgt_insp.has_table(name)
        before = 0
        if target_exists:
            with target_engine.connect() as tconn:
                before = tconn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar_one()

        if dry:
            where = "target now=%d" % before if target_exists else "target table absent"
            self.stdout.write(
                f"  {name}: source={src_rows}  {where}  would insert up to {src_rows} row(s)"
            )
            return {"side": "analytics", "table": name, "source": src_rows,
                    "before": before if target_exists else None,
                    "after": before if target_exists else None, "status": DRY,
                    "note": (f"source-only columns ignored: {', '.join(dropped)}" if dropped else "")}

        # Coercion kinds come straight from the DECLARED SQLAlchemy column types.
        kinds = {c: self._kind_for_sa_type(tbl.columns[c].type) for c in shared}
        stmt = pg_insert(tbl).on_conflict_do_nothing()   # idempotent: re-runs insert nothing

        # Clamp so one statement can never exceed Postgres' bound-parameter ceiling.
        chunk_size = max(1, min(batch, PG_MAX_BIND_PARAMS // max(1, len(shared))))

        select_stmt = select(*[tbl.columns[c] for c in shared]).select_from(tbl)
        with src_engine.connect() as sconn:
            result = sconn.execution_options(stream_results=True, yield_per=chunk_size).execute(
                select_stmt
            )
            while True:
                chunk = result.fetchmany(chunk_size)  # streamed — never the whole table
                if not chunk:
                    break
                payload = [
                    {c: self._coerce(v, kinds[c]) for c, v in zip(shared, row)}
                    for row in chunk
                ]
                with target_engine.begin() as tconn:
                    tconn.execute(stmt, payload)

        self._reset_pg_sequence_analytics(target_engine, tbl)
        with target_engine.connect() as tconn:
            after = tconn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar_one()
        return self._finish(conn_side="analytics", table=name, src_rows=src_rows,
                            before=before, after=after, dropped=dropped)

    def _reset_pg_sequence_analytics(self, target_engine, tbl) -> None:
        """Same reason as the Django side: ids are copied verbatim."""
        pk_cols = list(tbl.primary_key.columns)
        if len(pk_cols) != 1:
            return
        col = pk_cols[0].name
        with target_engine.begin() as conn:
            seq = conn.execute(
                text("SELECT pg_get_serial_sequence(:t, :c)"), {"t": tbl.name, "c": col}
            ).scalar()
            if not seq:
                return              # e.g. backlinks_snapshot.site_id (a string PK)
            conn.execute(
                text(
                    f'SELECT setval(:s, COALESCE((SELECT MAX("{col}") FROM "{tbl.name}"), 1), '
                    f'(SELECT MAX("{col}") FROM "{tbl.name}") IS NOT NULL)'
                ),
                {"s": seq},
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Verification & reporting
    # ─────────────────────────────────────────────────────────────────────────

    def _finish(self, *, conn_side: str, table: str, src_rows: int,
                before: int, after: int, dropped: list) -> dict:
        """Classify one copied table.

        The honest rule, stated so the verdict can be checked:
          * target started EMPTY  -> after MUST equal the source count. Anything less means
            source rows were lost (collided on a unique constraint or failed to insert).
          * target already had rows (a re-run, or pre-existing data) -> after must be at
            least the source count; it cannot possibly contain every source row otherwise.
        """
        inserted = after - before
        notes = []
        if dropped:
            notes.append(f"source-only columns ignored: {', '.join(dropped)}")
        if before == 0:
            status = OK if after == src_rows else MISMATCH
        else:
            status = OK if after >= src_rows else MISMATCH
        if inserted < src_rows:
            notes.append(f"{src_rows - inserted} source row(s) already present or conflicting")

        line = f"  {table}: source={src_rows}  target {before} -> {after}  (+{inserted})"
        if status == MISMATCH:
            self.stdout.write(self.style.ERROR(line + "   <-- MISMATCH"))
        else:
            self.stdout.write(line)
        for n in notes:
            self.stdout.write(f"      note: {n}")
        return {"side": conn_side, "table": table, "source": src_rows, "before": before,
                "after": after, "status": status, "note": "; ".join(notes)}

    def _report(self, results: list[dict], dry: bool) -> None:
        self.stdout.write("\n" + "=" * 78)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 78)
        self.stdout.write(
            f"  {'side':<10} {'table':<32} {'source':>9} {'before':>9} {'after':>9}  status"
        )
        for r in results:
            before = "-" if r["before"] is None else r["before"]
            after = "-" if r["after"] is None else r["after"]
            line = (
                f"  {r['side']:<10} {r['table']:<32} {r['source']:>9} "
                f"{str(before):>9} {str(after):>9}  {r['status']}"
            )
            if r["status"] == MISMATCH:
                self.stdout.write(self.style.ERROR(line))
            elif r["status"] == SKIPPED and r["source"]:
                self.stdout.write(self.style.WARNING(line))
            else:
                self.stdout.write(line)

        mismatches = [r for r in results if r["status"] == MISMATCH]
        copied = [r for r in results if r["status"] == OK]
        total_src = sum(r["source"] for r in copied)
        total_after = sum(r["after"] for r in copied)

        self.stdout.write("")
        if dry:
            would = sum(r["source"] for r in results if r["status"] == DRY)
            self.stdout.write(self.style.WARNING(
                f"DRY RUN — nothing was written. {would} row(s) across "
                f"{len([r for r in results if r['status'] == DRY])} table(s) would be migrated."
            ))
            return

        dropped_rows = [r for r in results if r["status"] == SKIPPED and r["source"]]
        for r in dropped_rows:
            self.stdout.write(self.style.WARNING(
                f"WARNING: {r['table']} had {r['source']} source row(s) that were NOT copied "
                f"({r['note']})"
            ))

        if mismatches:
            for r in mismatches:
                self.stdout.write(self.style.ERROR(
                    f"MISMATCH: {r['table']} - source {r['source']}, target ended at {r['after']}"
                ))
            raise CommandError(
                f"{len(mismatches)} table(s) did not verify. The migration is NOT complete - "
                "do not switch the application over to Postgres yet."
            )

        self.stdout.write(self.style.SUCCESS(
            f"All {len(copied)} copied table(s) verified: {total_src} source row(s), "
            f"{total_after} row(s) in the target."
        ))
