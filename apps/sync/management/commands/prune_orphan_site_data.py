"""Find — and on request delete — analytics rows filed under a site_id no Site row uses.

Every analytics table is keyed by the `Site.site_url` string. Connectors that stamped the
*Search Console property* instead of that canonical key wrote a parallel copy of the same
site's history under a second spelling: `https://premierstaff.com/` alongside
`premierstaff.com`, `fusehealth.com` alongside `sc-domain:fusehealth.com`. Nothing reads
those rows — every page resolves a site through the `sites` table first — but they are
indistinguishable from real data when anyone inspects the database by hand, and any query
that widens its filter to "either spelling" double-counts them.

Reports by default. Deleting is irreversible, so it happens only under --apply.

    python manage.py prune_orphan_site_data
    python manage.py prune_orphan_site_data --apply
"""
from django.core.management.base import BaseCommand
from sqlalchemy import func, select, text

from pipeline.db.schema import (
    Site, SEODaily, SEODailyTotal, KeywordRanking, Page, Backlink, AdMetricDaily,
)
from pipeline.utils.db_connection import get_session

# Every table whose rows belong to a site. Listed explicitly rather than walked off the
# metadata so adding a table is a deliberate decision, not something a deletion command
# picks up on its own.
SITE_KEYED = [SEODaily, SEODailyTotal, KeywordRanking, Page, Backlink, AdMetricDaily]


class Command(BaseCommand):
    help = "Report (or delete) analytics rows whose site_id matches no Site row."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Actually delete. Without it, nothing is written.")
        parser.add_argument("--only", action="append", metavar="SITE_ID",
                            help="Restrict to this site_id; repeatable. Without it, --apply "
                                 "would delete every orphan, and not every orphan is junk — "
                                 "a site removed from the sites table still has real history "
                                 "under its key. Name the keys you mean.")

    def handle(self, *args, **opts):
        apply = opts["apply"]
        only = set(opts["only"] or [])

        if apply and not only:
            self.stderr.write(self.style.ERROR(
                "Refusing to delete every orphan at once. Re-run with --only <site_id> "
                "(repeatable) naming the keys you have checked."
            ))
            return

        with get_session() as session:
            known = {r[0] for r in session.execute(select(Site.site_url)).all()}
            self.stdout.write(f"Known site keys: {sorted(known)}\n")

            total = 0
            for model in SITE_KEYED:
                table = model.__tablename__
                try:
                    counts = session.execute(
                        select(model.site_id, func.count()).group_by(model.site_id)
                    ).all()
                except Exception as exc:
                    self.stdout.write(f"{table}: skipped ({exc.__class__.__name__})")
                    continue

                orphans = [(sid, n) for sid, n in counts
                           if sid not in known and (not only or sid in only)]
                if not orphans:
                    self.stdout.write(f"{table}: clean")
                    continue

                for sid, n in sorted(orphans, key=lambda x: -x[1]):
                    total += n
                    self.stdout.write(f"{table}: {n:>8,} rows under {sid!r}")
                    if apply:
                        session.execute(
                            text(f"DELETE FROM {table} WHERE site_id = :sid"), {"sid": sid}
                        )

            if apply:
                session.commit()
                self.stdout.write(self.style.SUCCESS(f"\nDeleted {total:,} orphaned rows."))
            else:
                self.stdout.write(
                    f"\n{total:,} orphaned rows found. Re-run with --apply to delete them."
                )
