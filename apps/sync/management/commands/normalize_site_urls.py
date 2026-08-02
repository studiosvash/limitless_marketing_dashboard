"""One-off, idempotent migration: rewrite `sites.site_url` to its normalised domain.

WHY: `sites.site_url` is the string that joins the two databases (`.claude/skills.md` §3), and
until 2026-08-02 nothing normalised it. `add_site`'s duplicate guard stripped the scheme and the
`sc-domain:` prefix but not a leading `www.`, so the same site could be registered twice —
`premierstaff.com` AND `www.premierstaff.com` — as two projects with two slugs, two sync budgets
and two halves of one site's history. `pipeline/utils/site_ids.normalize_domain()` is now the one
registration rule and `add_site` stores its output; this command brings rows created before that
into line.

WHAT IT TOUCHES: only `site_url` columns, and only where the normalised form differs.

    fusehealth.db (SQLAlchemy)  sites.site_url
    django_internal.db (ORM)    SyncLog, RefreshRun, Insight, AITarget, AIPromptList,
                                AIPrompt, ProjectSettings

The Django-side rows MUST move with the site row. They are keyed on the same string, so renaming
`sites.site_url` alone would orphan the project's settings blob, its acknowledged alerts, its ads
overrides and its whole sync history — the UI would report a configured, freshly-synced project
as never-synced and unconfigured.

WHAT IT DOES NOT TOUCH: the analytics tables in fusehealth.db (`seo_daily`, `keyword_rankings`,
…). Their `site_id` values stay exactly as written. `resolve_site_ids()` expands a project's
domain to both the www and non-www spellings, so those rows remain readable without rewriting
anyone's measurement history. Rewriting millions of analytics rows to gain nothing is the riskier
option, not the safer one.

`sites.slug` is also left alone: it is the public project id in every URL, in the SPA's
`fh_selected_project` localStorage key, and in whatever the team has bookmarked. Renaming it
would break those for a cosmetic gain.

SAFETY: dry run by default. It prints the exact plan and changes nothing until `--apply`.
Collisions (two projects that normalise to the same domain) are reported and REFUSED — merging
two real projects into one is a judgement call about which name, slug, credentials and settings
survive, and this command will not make it for you.

    python manage.py normalize_site_urls            # show the plan
    python manage.py normalize_site_urls --apply    # do it

Idempotent: a second run finds nothing to do.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from sqlalchemy import select

from pipeline.db.schema import Site
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import normalize_domain

# Every Django model keyed on the site_url string. Kept explicit rather than discovered by
# introspection so adding a model to the list is a deliberate, reviewable act.
DJANGO_MODELS = [
    ("apps.sync.models", "SyncLog"),
    ("apps.sync.models", "RefreshRun"),
    ("apps.dashboard.models", "Insight"),
    ("apps.dashboard.models", "AITarget"),
    ("apps.dashboard.models", "AIPromptList"),
    ("apps.dashboard.models", "AIPrompt"),
    ("apps.dashboard.models", "ProjectSettings"),
]


def _load_models():
    from importlib import import_module
    return [(name, getattr(import_module(mod), name)) for mod, name in DJANGO_MODELS]


class Command(BaseCommand):
    help = "Rewrite sites.site_url (and every site_url-keyed Django row) to its normalised domain."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true",
            help="Actually write the changes. Without this the command only prints the plan.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        with get_session() as session:
            sites = session.execute(select(Site).order_by(Site.id)).scalars().all()
            plan = []
            for site in sites:
                new_url = normalize_domain(site.site_url)
                if not new_url:
                    self.stdout.write(self.style.WARNING(
                        f"  skip  site #{site.id}: {site.site_url!r} has no readable domain"
                    ))
                    continue
                if new_url != site.site_url:
                    plan.append((site.id, site.slug, site.site_url, new_url))

            if not plan:
                self.stdout.write(self.style.SUCCESS(
                    f"All {len(sites)} site_url value(s) are already normalised. Nothing to do."
                ))
                return

            # A collision means two SEPARATE project rows describe one site. Renaming both would
            # hit the unique constraint on sites.site_url (and on AITarget/ProjectSettings), so
            # refuse before writing anything rather than fail halfway through.
            targets: dict[str, list[str]] = {}
            for site in sites:
                key = normalize_domain(site.site_url)
                if key:
                    targets.setdefault(key, []).append(f"#{site.id} {site.site_url!r}")
            collisions = {k: v for k, v in targets.items() if len(v) > 1}

            self.stdout.write(self.style.MIGRATE_HEADING("Planned site_url rewrites:"))
            for site_id, slug, old, new in plan:
                self.stdout.write(f"  site #{site_id} ({slug}):  {old}  ->  {new}")

            if collisions:
                self.stdout.write("")
                self.stdout.write(self.style.ERROR("REFUSING TO RUN — duplicate projects found:"))
                for domain, rows in collisions.items():
                    self.stdout.write(f"  {domain}: {', '.join(rows)}")
                self.stdout.write(
                    "\nThese are two projects for one site. Decide which one keeps the history, "
                    "then delete the other in Settings (or `delete_site`) and re-run. This "
                    "command will not pick for you — the loser's settings, acknowledged alerts "
                    "and ads overrides would be discarded silently."
                )
                return

            if not apply:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING(
                    "Dry run — nothing written. Re-run with --apply to make these changes."
                ))
                self._preview_django_rows(plan)
                return

            # Django rows first: if that transaction fails, the analytics row is untouched and
            # the two databases still agree. The reverse order would leave the site renamed with
            # its settings and sync history stranded under the old key.
            self._move_django_rows(plan)

            for site_id, _slug, _old, new in plan:
                site = session.get(Site, site_id)
                site.site_url = new

        self.stdout.write(self.style.SUCCESS(f"Normalised {len(plan)} site_url value(s)."))

    def _preview_django_rows(self, plan):
        self.stdout.write("")
        self.stdout.write("Django rows that would move with them:")
        for name, model in _load_models():
            for _site_id, _slug, old, new in plan:
                count = model.objects.filter(site_url=old).count()
                if count:
                    self.stdout.write(f"  {name}: {count} row(s)  {old} -> {new}")

    @transaction.atomic
    def _move_django_rows(self, plan):
        for name, model in _load_models():
            for _site_id, _slug, old, new in plan:
                moved = model.objects.filter(site_url=old).update(site_url=new)
                if moved:
                    self.stdout.write(f"  {name}: moved {moved} row(s)  {old} -> {new}")
