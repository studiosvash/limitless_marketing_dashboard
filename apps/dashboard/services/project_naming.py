"""Duplicate-project naming checks — advisory only.

WHY THIS IS A WARNING AND NOT A CONSTRAINT. One domain can legitimately be registered as
several projects, one per city (`add_site(allow_duplicate=True)`), and those siblings want
related names. Nothing in this codebase has ever checked `site_name` for uniqueness, and adding
a hard rule would break a supported workflow.

What is worth saying out loud is the two shapes that actually cost the user something:

  * TWO PROJECTS ON ONE DOMAIN WITH THE SAME NAME. The project switcher, the workspace header
    and every export identify a project by its name, so two identically-named rows are
    indistinguishable in the UI. That matters more here than it would elsewhere, because the
    failures that happen on a duplicated domain — a settings save landing on the wrong sibling,
    a location edit blanking a page — are precisely the ones the user then cannot attribute to
    the right project.

  * TWO PROJECTS ON ONE DOMAIN IN THE SAME LOCATION. Those share `site_id` *and* the location
    filter every ranking read applies, so they read the same `keyword_rankings` rows and will
    report identical numbers under two different names for as long as they both exist. This is
    the shape that produced six Premierstaff projects with byte-identical figures.

The caller decides what to do with either. This function returns findings and a sentence; it
does not return a verdict, and it never raises — a naming hint must not be the reason a save
cannot proceed.
"""
import logging

logger = logging.getLogger(__name__)

_EMPTY = {"name": [], "location": [], "warning": ""}


def _fold(value) -> str:
    """Case- and whitespace-folded comparison key. Empty string never matches anything."""
    return (value or "").strip().casefold()


def find_project_name_conflicts(site_url: str, site_name: str,
                                location: str | None = None,
                                exclude_site_pk: int | None = None) -> dict:
    """Other projects on the SAME normalised domain that clash with this name or location.

    Returns::

        {"name":     [{"site_pk", "slug", "site_name", "location"}, …],
         "location": [{"site_pk", "slug", "site_name", "location"}, …],
         "warning":  "one sentence, or '' when there is nothing to say"}

    `site_url` is matched through `pipeline.utils.site_ids.normalize_domain` — the one
    registration rule (skills.md §3) — so `https://www.x.com/` and `x.com` are one domain and
    a different domain with the same project name is not a conflict.

    `exclude_site_pk` is the project being edited; without it a project always collides with
    itself. Pass the pk the view already resolved, never a `site_url` lookup: several projects
    share one `site_url` and `.first()` on it is its own documented bug (skills.md §9).
    """
    name_key = _fold(site_name)
    loc_key = _fold(location)
    if not name_key and not loc_key:
        return {"name": [], "location": [], "warning": ""}

    try:
        from sqlalchemy import select

        from pipeline.db.schema import Site
        from pipeline.utils.db_connection import get_session
        from pipeline.utils.site_ids import normalize_domain

        domain = normalize_domain(site_url)
        if not domain:
            return {"name": [], "location": [], "warning": ""}

        name_hits, loc_hits = [], []
        with get_session() as session:
            rows = session.execute(
                select(Site.id, Site.slug, Site.site_name, Site.site_url, Site.location)
            ).all()

        for row in rows:
            if exclude_site_pk is not None and row.id == exclude_site_pk:
                continue
            if normalize_domain(row.site_url) != domain:
                continue
            hit = {"site_pk": row.id, "slug": row.slug, "site_name": row.site_name,
                   "location": row.location}
            if name_key and _fold(row.site_name) == name_key:
                name_hits.append(hit)
            # Reported separately, not as an "else": one sibling can be both, and the two
            # findings have different consequences and different fixes.
            if loc_key and _fold(row.location) == loc_key:
                loc_hits.append(hit)

        return {"name": name_hits, "location": loc_hits,
                "warning": _warning(domain, site_name, location, name_hits, loc_hits)}
    except Exception as e:
        logger.error(f"find_project_name_conflicts error: {e}", exc_info=True)
        # A safe empty shape, per skills.md rule 6. Silence here means "no warning to show",
        # which is the correct degradation: the check is advisory, so failing it must not
        # invent a conflict OR stop the caller.
        return {"name": [], "location": [], "warning": ""}


def _warning(domain: str, site_name: str, location, name_hits: list, loc_hits: list) -> str:
    """One sentence per finding, naming the siblings so the user can go and look."""
    parts = []
    if name_hits:
        others = ", ".join(f"{h['site_name']!r} ({h['location'] or 'no location'})"
                           for h in name_hits[:5])
        parts.append(
            f"{len(name_hits)} other project on {domain} is already called "
            f"{(site_name or '').strip()!r} — {others}. "
            if len(name_hits) == 1 else
            f"{len(name_hits)} other projects on {domain} are already called "
            f"{(site_name or '').strip()!r} — {others}. "
        )
        parts.append("The switcher, the workspace header and every export identify a project "
                     "by its name, so they will be indistinguishable. ")
    if loc_hits:
        others = ", ".join(f"{h['site_name']!r}" for h in loc_hits[:5])
        parts.append(
            f"{others} already track{'s' if len(loc_hits) == 1 else ''} {domain} in "
            f"{(location or '').strip()!r}, so both projects read the same rankings and will "
            f"report the same numbers under two names. "
        )
    if not parts:
        return ""
    parts.append("This is allowed — several projects per domain is a supported setup — but "
                 "it is worth a distinct name.")
    return "".join(parts)
