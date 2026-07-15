"""One-off, idempotent migration: adds vertical/location/slug columns to the
SQLAlchemy-managed `sites` table (Django migrations don't cover fusehealth.db —
see .claude/DATABASE.md) and backfills slug for any existing rows that don't have one.

Safe to run multiple times: each ALTER TABLE is guarded by a PRAGMA table_info check,
and slug backfill only touches rows where slug IS NULL.
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from sqlalchemy import select, text

from pipeline.db.engine import get_engine
from pipeline.db.schema import Site, init_db
from pipeline.services.site_service import slugify_unique
from pipeline.utils.db_connection import get_session


class Command(BaseCommand):
    help = "Add vertical/location/slug columns to sites and backfill slug for existing rows."

    def handle(self, *args, **options):
        # Ensure the database and tables are initialized
        db_path = settings.ANALYTICS_DB_PATH
        engine = get_engine(db_path)
        init_db(engine)

        with get_session() as session:
            conn = session.connection()
            existing_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(sites)"))}

            for col_name, ddl in [
                ("vertical", "ALTER TABLE sites ADD COLUMN vertical VARCHAR(255)"),
                ("location", "ALTER TABLE sites ADD COLUMN location VARCHAR(255) DEFAULT 'United States'"),
                ("slug", "ALTER TABLE sites ADD COLUMN slug VARCHAR(100)"),
            ]:
                if col_name not in existing_cols:
                    conn.execute(text(ddl))
                    self.stdout.write(f"Added column: sites.{col_name}")
                else:
                    self.stdout.write(f"Column already present, skipping: sites.{col_name}")

            rows = session.execute(select(Site).where(Site.slug.is_(None))).scalars().all()
            for site in rows:
                site.slug = slugify_unique(session, site.site_name or site.site_url)
                if site.location is None:
                    site.location = "United States"
                self.stdout.write(f"Backfilled slug for site #{site.id}: {site.slug}")
            if not rows:
                self.stdout.write("No rows needed a slug backfill.")

        self.stdout.write(self.style.SUCCESS("add_project_fields complete."))
