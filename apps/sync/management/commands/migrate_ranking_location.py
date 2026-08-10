"""Carry one project's measured ranking history across to a new tracking location.

WHY THIS EXISTS. `sites.location` is not a label — it is a filter. Every positioning read
narrows to the project's CURRENT location (`shared_queries._location_clause`) and every ranking
row carries the location it was measured in, because two projects on one domain can track two
different cities and the rows would otherwise merge into one set of numbers.

The consequence is that editing a project's location makes 100% of its measured history
unreadable in one click. Rankings Overview goes blank, the whole tracked list drops into "Newly
Added Keywords — Not Tracked Yet", and the next sync re-buys every keyword from DataForSEO. The
rows are not lost: they are still there under the old string, and changing the location back
restores them exactly. The Edit Project modal now says so before it saves.

This command is the deliberate other option — move the history to the new market and keep it —
and it is dry-run by default, like `normalize_site_urls`.

    python manage.py migrate_ranking_location staff-dc \
        --from "United States - New York" --to "United States - Washington, DC"
    python manage.py migrate_ranking_location staff-dc --from "..." --to "..." --apply

WHAT IT TOUCHES
    keyword_rankings             your measured positions
    competitor_keyword_rankings  the competitor grid's cells

Both, together. The Positioning page reads both on `location`, so moving one and not the other
leaves the page half-migrated: your column populated and every competitor cell an em dash.

WHAT IT DOES NOT TOUCH
    saved_keywords — the tracked list is scoped by `site_pk` alone (see
    `saved_keyword_service.project_scope`); `location` on those rows identifies nothing and is
    already ignored when a project is in hand. Moving it would change no read.

TWO REFUSALS, both because the analytics rows do not record which project wrote them:

  * A COLLISION — a row already exists for the same (date, site_id, keyword[, competitor],
    NEW location). It is skipped and reported, never overwritten. The two rows are different
    facts about different SERPs on the same day; destroying a real measurement of the new
    market to make room for an older one from another city is not a migration.
  * A SIBLING still tracking the OLD location. The rows are keyed by `site_id`, which every
    project on the domain shares, so moving them would take the sibling's measurements with
    them — blanking the sibling's page exactly the way this command exists to undo.

Idempotent: a second run finds nothing at the old location and says so.
"""
from django.core.management.base import BaseCommand, CommandError
from sqlalchemy import select, update

from pipeline.db.schema import (
    CompetitorKeywordRanking, KeywordRanking, Site,
    ensure_ranking_location_columns, ensure_ranking_location_keys,
)
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import resolve_site_ids


class Command(BaseCommand):
    help = ("Move a project's keyword_rankings and competitor_keyword_rankings rows from one "
            "tracking location to another. Dry run unless --apply is given.")

    def add_arguments(self, parser):
        parser.add_argument("slug", help="The project's slug, as it appears in the URL.")
        parser.add_argument("--from", dest="from_location", required=True,
                            help="The location the rows were measured under.")
        parser.add_argument("--to", dest="to_location", required=True,
                            help="The location to move them to — normally the project's "
                                 "current sites.location.")
        parser.add_argument("--apply", action="store_true",
                            help="Actually write the changes. Without this the command only "
                                 "prints the plan.")

    def handle(self, *args, **options):
        slug = options["slug"]
        old = options["from_location"]
        new = options["to_location"]
        apply_changes = options["apply"]

        if old == new:
            raise CommandError("--from and --to are the same location; nothing to migrate.")

        with get_session() as session:
            # Legacy databases predate the `location` column and its unique key; both the
            # SELECTs and the UPDATEs below would fail without this.
            ensure_ranking_location_columns(session)
            ensure_ranking_location_keys(session)

            site = session.execute(
                select(Site).where(Site.slug == slug)
            ).scalars().first()
            if site is None:
                raise CommandError(f"No project with slug {slug!r}.")

            site_ids = resolve_site_ids(site.site_url)

            siblings = session.execute(
                select(Site.id, Site.slug, Site.site_name)
                .where(Site.site_url == site.site_url, Site.id != site.id,
                       Site.location == old)
            ).all()
            if siblings:
                names = ", ".join(f"#{s.id} {s.slug!r}" for s in siblings)
                raise CommandError(
                    f"Refusing to run: {len(siblings)} other project(s) on {site.site_url} "
                    f"still track {old!r} — {names}. The ranking rows are keyed on site_id, "
                    f"which every project on this domain shares, so moving them would take "
                    f"those projects' measurements with them and blank their pages. Point "
                    f"them somewhere else first, or leave this history where it is."
                )

            self.stdout.write(self.style.MIGRATE_HEADING(
                f"Project {site.slug!r} (site #{site.id}, {site.site_url}) — "
                f"{old!r} -> {new!r}"
            ))
            if site.location != new:
                self.stdout.write(self.style.WARNING(
                    f"  note: this project's stored location is {site.location!r}, not "
                    f"{new!r}. The migrated rows will only be readable once it matches."
                ))

            plans = [
                self._plan(session, KeywordRanking, site_ids, old, new,
                           ("date", "keyword"), "keyword_rankings"),
                self._plan(session, CompetitorKeywordRanking, site_ids, old, new,
                           ("date", "keyword", "competitor_domain"),
                           "competitor_keyword_rankings"),
            ]

            movable = sum(len(p["move"]) for p in plans)
            skipped = sum(len(p["skip"]) for p in plans)

            if not movable and not skipped:
                self.stdout.write(self.style.SUCCESS(
                    f"No rows found at {old!r} for this project. Nothing to do."
                ))
                return

            for plan in plans:
                self.stdout.write(
                    f"  {plan['label']}: {len(plan['move'])} row(s) to move, "
                    f"{len(plan['skip'])} to skip"
                )
                # Bounded so a large collision set does not bury the summary.
                for key in plan["skip"][:20]:
                    self.stdout.write(self.style.WARNING(
                        f"    skip  {key} — a row already exists at {new!r}"
                    ))
                if len(plan["skip"]) > 20:
                    self.stdout.write(f"    … and {len(plan['skip']) - 20} more skipped")

            if not apply_changes:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING(
                    "Dry run — nothing written. Re-run with --apply to make these changes."
                ))
                return

            written = 0
            for plan in plans:
                for row_id in plan["move"]:
                    session.execute(
                        update(plan["model"])
                        .where(plan["model"].id == row_id)
                        .values(location=new)
                    )
                    written += 1

        self.stdout.write(self.style.SUCCESS(
            f"Moved {written} row(s) to {new!r}; {skipped} left at {old!r} because a row "
            f"already existed for them in the new market."
        ))

    def _plan(self, session, model, site_ids, old, new, key_cols, label) -> dict:
        """Split this table's old-location rows into (movable ids, colliding key strings)."""
        occupied = {
            tuple(getattr(r, c) for c in key_cols)
            for r in session.execute(
                select(*[getattr(model, c) for c in key_cols])
                .where(model.site_id.in_(site_ids), model.location == new)
            ).all()
        }
        move, skip = [], []
        rows = session.execute(
            select(model.id, *[getattr(model, c) for c in key_cols])
            .where(model.site_id.in_(site_ids), model.location == old)
        ).all()
        for row in rows:
            key = tuple(getattr(row, c) for c in key_cols)
            if key in occupied:
                skip.append(" / ".join(str(k) for k in key))
            else:
                move.append(row.id)
                # A duplicate inside the moving set would collide with itself once the first
                # one lands, so claim the key as we go.
                occupied.add(key)
        return {"model": model, "label": label, "move": move, "skip": skip}
