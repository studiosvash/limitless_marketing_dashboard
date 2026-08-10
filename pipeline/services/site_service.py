"""
pipeline/services/site_service.py — Multi-domain registry CRUD + lookup helpers.

Provides read/write access to the `sites` table. All Django views and pipeline
connectors that need to resolve a site_url → Site row should go through this module.
"""
import os
import re
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import select

from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger
from pipeline.utils.site_ids import normalize_domain
from pipeline.db.schema import Site

load_dotenv()
logger = get_logger("site_service")

# Databases whose `sites` table has already been reconciled with the Site model in this
# process, keyed by connection URL so a test's temp SQLite file never inherits another's
# result. See _ensure_columns below.
_COLUMNS_ENSURED: set[str] = set()


def _ensure_columns(session) -> None:
    """Reconcile the `sites` table with the Site model once per process, per database.

    WHY HERE: columns added to `sites` after release (search_engine/device/language) do not
    exist in a database created before them, and SQLAlchemy selects every mapped column — so
    the FIRST `select(Site)` against an un-upgraded database fails, not the first write.
    Running the reconcile from this module means the ordinary boot path repairs itself: the
    SPA's first call is `GET /api/projects` -> list_sites() -> here, which lands before any
    slug-scoped view resolves a Site.

    LIMIT, stated plainly: this covers callers that go through site_service or through
    init_db(). A process that reaches `select(Site)` by another route first (e.g.
    apps/api/views.resolve_project_or_404, which builds its own query) would still hit the
    missing column. Running `python manage.py add_project_fields` on SQLite, or any command
    that calls init_db(), closes that window deterministically; on Postgres, init_db() is the
    entry point (add_project_fields' own PRAGMA guard is SQLite-only).

    Never raises: a failure here must not turn a page into a 500 when the columns are in fact
    already present, which is the case for every database created after this change.
    """
    try:
        key = str(session.get_bind().engine.url)
    except Exception:  # noqa: BLE001 - a bind we cannot name is still worth reconciling once
        key = "<unknown>"
    if key in _COLUMNS_ENSURED:
        return
    _COLUMNS_ENSURED.add(key)
    try:
        from pipeline.db.schema import ensure_site_columns, ensure_site_url_not_unique
        added = ensure_site_columns(session)
        if added:
            logger.info(f"[site_service] Added missing sites column(s): {', '.join(added)}")
        if ensure_site_url_not_unique(session):
            logger.info("[site_service] Dropped legacy unique index on sites.site_url")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[site_service] Could not reconcile sites columns: {exc}")


def _bare_domain(value: str) -> str:
    """The registration form of a domain — delegates to `site_ids.normalize_domain`.

    This used to be three `str.replace` calls and an `.rstrip("/")`, which stripped the scheme
    and the `sc-domain:` prefix but NOT a leading `www.`. So `add_site`'s duplicate guard (which
    compares this function's output) saw `www.premierstaff.com` and `premierstaff.com` as two
    different sites and happily registered both: two projects, two slugs, two sync budgets, and
    a project switcher offering the user a choice between two halves of one site's history.
    `normalize_domain` strips `www.` too, and also handles a path, a port, a trailing dot and
    an uppercase scheme that the old substring replaces missed. See pipeline/utils/site_ids.py.
    """
    return normalize_domain(value)


def _slugify(value: str) -> str:
    """Lowercase, alnum + hyphens only, matching the project 'id' shape the frontend
    fixtures already use (e.g. 'fusehealth', 'limitless')."""
    value = _bare_domain(value) or value
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def slugify_unique(session, base: str) -> str:
    """Return a slug derived from `base` that doesn't collide with an existing Site.slug.
    Appends -2, -3, ... on collision."""
    from pipeline.db.schema import Site  # local import: avoids a circular import at module load

    root = _slugify(base)
    candidate = root
    n = 2
    while session.execute(select(Site).where(Site.slug == candidate)).scalars().first():
        candidate = f"{root}-{n}"
        n += 1
    return candidate


def list_sites(active_only: bool = True) -> list[Site]:
    with get_session() as session:
        _ensure_columns(session)
        q = select(Site).order_by(Site.site_url)
        if active_only:
            q = q.where(Site.is_active == 1)
        rows = session.execute(q).scalars().all()
        session.expunge_all()
        return list(rows)


def get_site(session, site_id: Optional[str] = None) -> Optional[Site]:
    """The `sites` row for `site_id`, or None when it names no site.

    An UNKNOWN site_id returns None. It used to fall back to "the first active site", which is
    the same shape as the `.env` GA4_PROPERTY_ID fallback that once wrote 6 654 rows of one
    site's data under another site's id: a connector handed an id it could not resolve was
    given a STRANGER'S row and went on to use that row's site_url as its write key and its
    credentials as its target. Every caller already guards for a missing row and has its own
    explicit default, so failing to resolve now degrades to that caller's own fallback instead
    of silently borrowing another project's identity.

    Called with NO site_id at all, it still returns the first active site — that is a different
    question ("the default site"), and `get_default_site_id` depends on it.

    Note this can only ever answer "a site on this domain": when several projects share one
    `site_url` it returns the first. Anything needing one specific project must use
    `get_site_by_pk`.
    """
    _ensure_columns(session)
    if site_id:
        site = session.execute(
            select(Site).where(Site.site_url == site_id)
        ).scalars().first()
        if not site:
            logger.warning(
                "[site_service] site_id=%r matches no site — returning None rather than "
                "another site's row", site_id,
            )
        return site
    return session.execute(
        select(Site).where(Site.is_active == 1).order_by(Site.id)
    ).scalars().first()


def get_site_by_pk(session, site_pk: Optional[int]) -> Optional[Site]:
    """The exact `sites` row, by primary key. None when `site_pk` is falsy or unknown.

    Distinct from `get_site()`, which looks up by `site_url` and CANNOT identify a project when
    several share a domain — it returns the first match. Anything that needs one project's own
    settings (its tracking location, above all) has to come through here.
    """
    if not site_pk:
        return None
    _ensure_columns(session)
    return session.execute(select(Site).where(Site.id == site_pk)).scalars().first()


def resolve_tracking_location(site_pk: Optional[int] = None,
                              site_id: Optional[str] = None) -> str:
    """The location a sync should query SERPs in, for THIS project.

    Resolution order, and why:

      1. `site_pk` — the project that actually triggered the run. The only source that is
         correct when several projects track one domain in different cities.
      2. `site_id` — the domain. Right for the scheduled per-domain sync and for older runs
         with no pk recorded; ambiguous (first match wins) when siblings exist, which is why
         it is the fallback and not the primary.
      3. `DEFAULT_LOCATION` — a project with a blank location field. That is the real stored
         value for projects created before the wizard collected one, and "United States" is
         what those were being fetched with regardless.

    Always returns a non-empty string in the SPA's display form; the DataForSEO wire form is
    produced separately by `normalize_location_name`.
    """
    from pipeline.db.schema import DEFAULT_LOCATION

    try:
        with get_session() as session:
            site = get_site_by_pk(session, site_pk)
            if site is None and site_id:
                site = get_site(session, site_id)
            location = (getattr(site, "location", "") or "").strip() if site else ""
    except Exception:
        logger.error("[site_service] could not resolve tracking location for "
                     "site_pk=%r site_id=%r", site_pk, site_id, exc_info=True)
        return DEFAULT_LOCATION
    return location or DEFAULT_LOCATION


def get_default_site_id() -> str:
    with get_session() as session:
        _ensure_columns(session)
        site = session.execute(
            select(Site).where(Site.is_active == 1).order_by(Site.id)
        ).scalars().first()
        if site:
            return site.site_url
    return os.getenv("GSC_SITE_URL", "")


def get_active_site_ids() -> list[str]:
    return [s.site_url for s in list_sites(active_only=True)]


def sync_primary_site_from_env() -> None:
    """Upsert the site named by GSC_SITE_URL in .env.

    Matches on the NORMALISED domain, not on the raw env string. `GSC_SITE_URL` is a Search
    Console property (`sc-domain:x.com`, `https://www.x.com/`), and add_site now stores
    `sites.site_url` normalised — so an equality test against the raw value would miss the row
    this created and insert a second project for the same site, which is exactly the duplication
    add_site was fixed to prevent. The raw property string still goes to `gsc_property`, which
    is where a property identifier belongs.
    """
    gsc = os.getenv("GSC_SITE_URL", "").strip()
    if not gsc:
        return
    domain = _bare_domain(gsc)
    if not domain:
        return
    ga4 = os.getenv("GA4_PROPERTY_ID", "").strip() or None
    df_target = _bare_domain(os.getenv("DATAFORSEO_TARGET_DOMAIN", "").strip() or gsc) or None
    with get_session() as session:
        _ensure_columns(session)
        site = next(
            (s for s in session.execute(select(Site)).scalars().all()
             if _bare_domain(s.site_url) == domain),
            None,
        )
        if site:
            changed = (
                site.gsc_property != gsc
                or site.ga4_property_id != ga4
                or site.dataforseo_target_domain != df_target
                or site.is_active != 1
            )
            site.gsc_property = gsc
            site.ga4_property_id = ga4
            site.dataforseo_target_domain = df_target
            site.is_active = 1
            if changed:
                logger.info(f"[site_service] Synced primary site from .env: {gsc}")
        else:
            session.add(Site(
                site_url=domain,
                site_name=domain,
                slug=slugify_unique(session, domain),
                gsc_property=gsc,
                ga4_property_id=ga4,
                dataforseo_target_domain=df_target,
                is_active=1,
            ))
            logger.info(f"[site_service] Created primary site from .env: {domain} (property {gsc})")


def add_site(site_url, site_name=None, gsc_property=None, ga4_property_id=None,
             dataforseo_target_domain=None, vertical=None, location="United States",
             search_engine="Google", device="Desktop", language="English",
             allow_duplicate=False) -> int:
    """Register a new site. Returns the new row's integer primary key.

    `site_url` is accepted in any spelling and STORED NORMALISED — `https://www.x.com/`,
    `http://x.com`, `sc-domain:x.com` and `x.com` all become `x.com`. That normalised string is
    the cross-database join key (`.claude/skills.md` §3), so normalising at the single point of
    registration is what keeps one site from becoming two projects. The duplicate check below
    compares the same normalised form, which is the fix for the bug where `premierstaff.com` and
    `www.premierstaff.com` were both accepted as new sites.

    `gsc_property` is NOT normalised: it is a Search Console property identifier, and the
    account may genuinely own `https://www.x.com/` rather than the domain property. Left unset
    it defaults to the bare domain, which gsc_property.resolve_gsc_property() then matches
    against the account's real property list (including the www URL-prefix forms) and repairs.

    search_engine/device/language are the Position Tracking wizard's "Tracking area" choices.
    Their defaults match the wizard's own pre-selected options, so a caller that does not pass
    them stores what the wizard would have shown rather than NULL. They are a recorded
    preference only — see the note on Site in pipeline/db/schema.py.

    `allow_duplicate` skips the duplicate-domain check below. Only the Position Tracking
    wizard passes this — it lets a team register the same domain twice to run two independent
    tracking configurations (different keyword lists, tracking-area settings) against one site.
    Every other creation path (topbar "+", Settings) leaves this False, so a plain re-add of an
    already-registered domain is still rejected there.
    """
    raw_url = (site_url or "").strip()
    if not raw_url:
        raise ValueError("site_url is required")
    domain = _bare_domain(raw_url)
    if not domain:
        # Honest failure beats storing an empty join key that silently matches nothing.
        raise ValueError(f"Could not read a domain from {raw_url!r}")
    with get_session() as session:
        _ensure_columns(session)
        if not allow_duplicate:
            existing_sites = session.execute(select(Site)).scalars().all()
            for s in existing_sites:
                if _bare_domain(s.site_url) == domain:
                    raise ValueError(f"Site already exists: {s.site_url}")
        name = site_name or domain
        site = Site(
            site_url=domain,
            site_name=name,
            slug=slugify_unique(session, name),
            vertical=vertical,
            location=location,
            gsc_property=gsc_property or domain,
            ga4_property_id=ga4_property_id or None,
            dataforseo_target_domain=_bare_domain(dataforseo_target_domain or domain),
            is_active=1,
            search_engine=search_engine or "Google",
            device=device or "Desktop",
            language=language or "English",
        )
        session.add(site)
        session.flush()
        new_id = site.id
        if domain != raw_url:
            logger.info(f"[site_service] Normalised {raw_url!r} -> {domain!r}")
        logger.info(f"[site_service] Added site #{new_id}: {domain}")
        return new_id


def update_site(site_id_pk: int, **fields) -> None:
    # Whitelist, not a blanket setattr: an unknown key must fail loudly rather than be
    # written onto the ORM object and silently dropped. search_engine/device/language were
    # added here at the same time as the columns, so the Edit Project modal can actually
    # persist the three fields it has always collected.
    allowed = {"site_name", "gsc_property", "ga4_property_id", "dataforseo_target_domain",
               "is_active", "vertical", "location",
               "search_engine", "device", "language"}
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"Cannot update fields: {bad}. Allowed: {allowed}")
    if "dataforseo_target_domain" in fields:
        fields["dataforseo_target_domain"] = _bare_domain(fields["dataforseo_target_domain"])
    with get_session() as session:
        _ensure_columns(session)
        site = session.get(Site, site_id_pk)
        if not site:
            raise ValueError(f"Site #{site_id_pk} not found")
        for k, v in fields.items():
            setattr(site, k, v)
        logger.info(f"[site_service] Updated site #{site_id_pk}: {list(fields)}")


def delete_site(site_id_pk: int, hard: bool = False) -> None:
    with get_session() as session:
        _ensure_columns(session)
        site = session.get(Site, site_id_pk)
        if not site:
            raise ValueError(f"Site #{site_id_pk} not found")
        if hard:
            session.delete(site)
            logger.info(f"[site_service] Hard-deleted site #{site_id_pk}: {site.site_url}")
        else:
            site.is_active = 0
            logger.info(f"[site_service] Soft-deleted site #{site_id_pk}: {site.site_url}")
