"""One-off, idempotent repair: give every tracked keyword back to a real project.

WHY THIS EXISTS
---------------
`saved_keywords` is a per-PROJECT list, and `saved_keywords.site_pk` (the owning `sites.id`) is
what identifies the project — Position Tracking registers one domain as several projects
(`add_site(allow_duplicate=True)`) and they all share `site_id`, so nothing else can tell them
apart. `ensure_saved_keyword_project()` fills that column in on every existing database the
first time it runs, matching each row to a project by domain and, where it can, by location.

Rows it cannot resolve are left at `UNOWNED_SITE_PK` and are invisible to every project:

  * a keyword written under a `site_id` spelling no project uses any more
    (`https://premierstaff.com/` vs `premierstaff.com`), and
  * a keyword whose project has since been deleted.

The keywords were really chosen by a real user and are still being paid for by the rank
connectors, so deleting them is wrong; they just need to be pointed at a project that exists.

WHAT IT DOES
------------
An unowned row whose domain still resolves to a live project is ADOPTED BY THE OLDEST PROJECT
on that domain — the one that existed when the row was written, which is the only defensible
owner. `resolve_site_ids` expands each project's domain to every spelling its rows may be keyed
under, so a project registered as `premierstaff.com` reclaims `https://premierstaff.com/` rows.

Rows whose domain matches no project at all are REPORTED, NOT MOVED: re-keying measurement
history is `normalize_site_urls`' job, and guessing here could hand one site's keywords to
another.

A row that would collide with an existing (site_pk, site_id, keyword, location) row is deleted
rather than duplicated — the destination already tracks that keyword, so the adoption is a no-op
for it.

SAFETY: dry run by default; prints the plan and changes nothing until `--apply`.

    python manage.py adopt_orphan_saved_keywords            # show the plan
    python manage.py adopt_orphan_saved_keywords --apply    # do it

Idempotent: a second run finds nothing to do.
"""
from collections import defaultdict

from django.core.management.base import BaseCommand
from sqlalchemy import select

from pipeline.db.schema import SavedKeyword, Site, ensure_saved_keyword_project
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import resolve_site_ids


class Command(BaseCommand):
    help = "Re-home tracked keywords that belong to no project. Dry run unless --apply."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Write the changes. Without it, only the plan is printed.")

    def handle(self, *args, **options):
        apply = options["apply"]

        with get_session() as session:
            # The column has to exist (and be backfilled) before anything below can read it.
            ensure_saved_keyword_project(session)

            sites = session.execute(select(Site).order_by(Site.id)).scalars().all()
            live_pks = {s.id for s in sites}
            # site_url spelling -> the projects that read it, oldest first.
            owners: dict[str, list] = defaultdict(list)
            for site in sites:
                for spelling in resolve_site_ids(site.site_url):
                    owners[spelling].append(site)

            rows = session.execute(select(SavedKeyword)).scalars().all()

            moves, unowned, already_ok = [], [], 0
            for row in rows:
                if row.site_pk and row.site_pk in live_pks:
                    already_ok += 1
                    continue
                # site_pk is 0 (never resolved) or points at a project that no longer exists.
                projects = owners.get(row.site_id)
                if not projects:
                    unowned.append(row)
                    continue
                moves.append((row, projects[0]))     # oldest project on the domain

            # A move that lands on a row the destination already holds would violate
            # (site_pk, site_id, keyword, location). Resolve it here rather than at write time.
            existing = {(r.site_pk, r.site_id, (r.keyword or "").lower(),
                         (r.location or "").strip()) for r in rows}
            real_moves, collisions = [], []
            for row, target in moves:
                dest = (target.id, row.site_id, (row.keyword or "").lower(),
                        (row.location or "").strip())
                if dest in existing:
                    collisions.append((row, target))
                else:
                    existing.add(dest)
                    real_moves.append((row, target))

            self.stdout.write(f"saved_keywords rows: {len(rows)}")
            self.stdout.write(f"  already owned by a live project : {already_ok}")
            self.stdout.write(f"  to adopt                        : {len(real_moves)}")
            self.stdout.write(f"  duplicate at destination        : {len(collisions)} (will be deleted)")
            self.stdout.write(f"  domain matches no project       : {len(unowned)} (left alone)")

            if real_moves:
                self.stdout.write("\nPlanned adoptions:")
                by_target = defaultdict(list)
                for row, target in real_moves:
                    by_target[(target.slug, target.location)].append(row)
                for (slug, loc), grouped in sorted(by_target.items()):
                    self.stdout.write(f"  -> {slug!r} ({loc!r}): {len(grouped)} keyword(s)")
                    for row in grouped[:8]:
                        self.stdout.write(f"       {row.keyword!r}  (was project #{row.site_pk})")
                    if len(grouped) > 8:
                        self.stdout.write(f"       … and {len(grouped) - 8} more")

            if unowned:
                self.stdout.write("\nsite_id values no project uses — run normalize_site_urls, "
                                  "or re-track these from the Keyword Explorer:")
                counts = defaultdict(int)
                for row in unowned:
                    counts[row.site_id] += 1
                for sid, n in sorted(counts.items()):
                    self.stdout.write(f"  {sid!r}: {n} keyword(s)")

            if not real_moves and not collisions:
                self.stdout.write(self.style.SUCCESS("\nNothing to do."))
                return

            if not apply:
                self.stdout.write(self.style.WARNING(
                    "\nDry run — nothing written. Re-run with --apply to make these changes."))
                return

            for row, target in real_moves:
                row.site_pk = target.id
            for row, _target in collisions:
                session.delete(row)
            session.commit()

            self.stdout.write(self.style.SUCCESS(
                f"\nAdopted {len(real_moves)} keyword(s); removed {len(collisions)} duplicate(s)."))
