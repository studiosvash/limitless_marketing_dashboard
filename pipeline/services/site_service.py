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
from pipeline.db.schema import Site

load_dotenv()
logger = get_logger("site_service")


def _bare_domain(value: str) -> str:
    if not value:
        return ""
    return (
        value.replace("https://", "")
        .replace("http://", "")
        .replace("sc-domain:", "")
        .rstrip("/")
    )


def _slugify(value: str) -> str:
    """Lowercase, alnum + hyphens only, matching the project 'id' shape the frontend
    fixtures already use (e.g. 'fusehealth', 'limitless')."""
    value = _bare_domain(value) or value
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def slugify_unique(session, base: str) -> str:
    """Return a slug derived from `base` that doesn't collide with an existing Site.slug.
    Appends -2, -3, ... on collision."""
    root = _slugify(base)
    candidate = root
    n = 2
    while session.execute(select(Site).where(Site.slug == candidate)).scalars().first():
        candidate = f"{root}-{n}"
        n += 1
    return candidate


def list_sites(active_only: bool = True) -> list[Site]:
    with get_session() as session:
        q = select(Site).order_by(Site.site_url)
        if active_only:
            q = q.where(Site.is_active == 1)
        rows = session.execute(q).scalars().all()
        session.expunge_all()
        return list(rows)


def get_site(session, site_id: Optional[str] = None) -> Optional[Site]:
    if site_id:
        site = session.execute(
            select(Site).where(Site.site_url == site_id)
        ).scalars().first()
        if site:
            return site
        logger.warning(f"[site_service] site_id={site_id!r} not found, falling back to first active")
    return session.execute(
        select(Site).where(Site.is_active == 1).order_by(Site.id)
    ).scalars().first()


def get_default_site_id() -> str:
    with get_session() as session:
        site = session.execute(
            select(Site).where(Site.is_active == 1).order_by(Site.id)
        ).scalars().first()
        if site:
            return site.site_url
    return os.getenv("GSC_SITE_URL", "")


def get_active_site_ids() -> list[str]:
    return [s.site_url for s in list_sites(active_only=True)]


def sync_primary_site_from_env() -> None:
    gsc = os.getenv("GSC_SITE_URL", "").strip()
    if not gsc:
        return
    ga4 = os.getenv("GA4_PROPERTY_ID", "").strip() or None
    df_target = _bare_domain(os.getenv("DATAFORSEO_TARGET_DOMAIN", "").strip() or gsc) or None
    with get_session() as session:
        site = session.execute(
            select(Site).where(Site.site_url == gsc)
        ).scalars().first()
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
                site_url=gsc,
                site_name=_bare_domain(gsc) or gsc,
                gsc_property=gsc,
                ga4_property_id=ga4,
                dataforseo_target_domain=df_target,
                is_active=1,
            ))
            logger.info(f"[site_service] Created primary site from .env: {gsc}")


def add_site(site_url, site_name=None, gsc_property=None, ga4_property_id=None,
             dataforseo_target_domain=None, vertical=None, location="United States") -> int:
    site_url = (site_url or "").strip()
    if not site_url:
        raise ValueError("site_url is required")
    with get_session() as session:
        existing = session.execute(select(Site).where(Site.site_url == site_url)).scalars().first()
        if existing:
            raise ValueError(f"Site already exists: {site_url}")
        name = site_name or _bare_domain(site_url) or site_url
        site = Site(
            site_url=site_url,
            site_name=name,
            slug=slugify_unique(session, name),
            vertical=vertical,
            location=location,
            gsc_property=gsc_property or site_url,
            ga4_property_id=ga4_property_id or None,
            dataforseo_target_domain=_bare_domain(dataforseo_target_domain or site_url),
            is_active=1,
        )
        session.add(site)
        session.flush()
        new_id = site.id
        logger.info(f"[site_service] Added site #{new_id}: {site_url}")
        return new_id


def update_site(site_id_pk: int, **fields) -> None:
    allowed = {"site_name", "gsc_property", "ga4_property_id", "dataforseo_target_domain",
               "is_active", "vertical", "location"}
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"Cannot update fields: {bad}. Allowed: {allowed}")
    if "dataforseo_target_domain" in fields:
        fields["dataforseo_target_domain"] = _bare_domain(fields["dataforseo_target_domain"])
    with get_session() as session:
        site = session.get(Site, site_id_pk)
        if not site:
            raise ValueError(f"Site #{site_id_pk} not found")
        for k, v in fields.items():
            setattr(site, k, v)
        logger.info(f"[site_service] Updated site #{site_id_pk}: {list(fields)}")


def delete_site(site_id_pk: int, hard: bool = False) -> None:
    with get_session() as session:
        site = session.get(Site, site_id_pk)
        if not site:
            raise ValueError(f"Site #{site_id_pk} not found")
        if hard:
            session.delete(site)
            logger.info(f"[site_service] Hard-deleted site #{site_id_pk}: {site.site_url}")
        else:
            site.is_active = 0
            logger.info(f"[site_service] Soft-deleted site #{site_id_pk}: {site.site_url}")
