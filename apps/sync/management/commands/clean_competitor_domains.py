"""Repair `tracked_competitors` rows that were stored as URLs or as the project's own domain.

`_bare()` used to strip the scheme and a trailing slash but not the PATH, so a pasted URL was
stored whole — `premierstaff.com/event-staffing-agency-las-vegas` became a "competitor domain",
and a project's own landing pages turned up listed as its rivals in Share of Voice.

`_bare()` is fixed, so nothing new lands in this shape. Rows already written keep it until this
runs.

Dry-run by default, like `normalize_site_urls`: it prints exactly what it would do and changes
nothing until `--apply`.

Three outcomes per row:
  * normalises to a real domain, and that domain is not already tracked by the same project
    -> UPDATE it in place;
  * normalises to a domain the project ALREADY tracks -> DELETE the duplicate, because the
    unique key is (site_pk, competitor_domain) and the good row is already there;
  * normalises to the project's OWN domain -> DELETE it. A site is not its own competitor, and
    every read filters it out anyway, so the row is dead weight that reads as a mistake.
"""
from django.core.management.base import BaseCommand
from sqlalchemy import delete, select, update

from pipeline.db.schema import Site, TrackedCompetitor
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import normalize_domain


class Command(BaseCommand):
    help = "Normalise tracked_competitors rows stored as URLs. Dry-run unless --apply."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Actually write the changes (default is a dry run).")

    def handle(self, *args, **options):
        apply = options["apply"]

        with get_session() as session:
            own_by_pk = {
                site_pk: normalize_domain(site_url or "")
                for site_pk, site_url in session.execute(select(Site.id, Site.site_url)).all()
            }
            rows = session.execute(
                select(TrackedCompetitor.id, TrackedCompetitor.site_pk,
                       TrackedCompetitor.site_id, TrackedCompetitor.competitor_domain)
            ).all()

            # What each project already holds, so a normalisation that collides with a good
            # row deletes instead of violating (site_pk, competitor_domain).
            held: dict = {}
            for _id, site_pk, _site_id, domain in rows:
                held.setdefault(site_pk, set()).add(domain)

            fixed = dupes = self_refs = 0
            for row_id, site_pk, site_id, domain in rows:
                clean = normalize_domain(domain or "")
                if clean == domain:
                    continue

                if not clean:
                    self.stdout.write(f"  SKIP  #{row_id} {domain!r} -> normalises to nothing")
                    continue

                if clean == own_by_pk.get(site_pk):
                    self_refs += 1
                    self.stdout.write(
                        self.style.WARNING(f"  DELETE #{row_id} {domain!r} — this is project "
                                           f"#{site_pk}'s own domain, not a competitor"))
                    if apply:
                        session.execute(delete(TrackedCompetitor)
                                        .where(TrackedCompetitor.id == row_id))
                    continue

                if clean in held.get(site_pk, set()):
                    dupes += 1
                    self.stdout.write(
                        self.style.WARNING(f"  DELETE #{row_id} {domain!r} — project #{site_pk} "
                                           f"already tracks {clean!r}"))
                    if apply:
                        session.execute(delete(TrackedCompetitor)
                                        .where(TrackedCompetitor.id == row_id))
                    continue

                fixed += 1
                self.stdout.write(f"  UPDATE #{row_id} {domain!r} -> {clean!r}")
                if apply:
                    session.execute(update(TrackedCompetitor)
                                    .where(TrackedCompetitor.id == row_id)
                                    .values(competitor_domain=clean))
                held.setdefault(site_pk, set()).add(clean)

            if apply:
                session.commit()

        total = fixed + dupes + self_refs
        summary = (f"{total} row(s) affected — {fixed} normalised, {dupes} duplicate(s) removed, "
                   f"{self_refs} self-reference(s) removed")
        if apply:
            self.stdout.write(self.style.SUCCESS(f"Applied: {summary}"))
        elif total:
            self.stdout.write(self.style.WARNING(
                f"Dry run: {summary}. Re-run with --apply to write."))
        else:
            self.stdout.write(self.style.SUCCESS("Nothing to clean — every row is already a bare domain."))
