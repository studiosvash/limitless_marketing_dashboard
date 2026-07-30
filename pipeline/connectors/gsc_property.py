"""Shared Search Console property resolution for the GSC connectors (gsc, gsc_keywords,
gsc_pages).

Why this exists: add_site defaults gsc_property to the bare domain (e.g. "eventstaff.com").
The Search Console API interprets a bare domain as the URL-prefix property
"http://eventstaff.com" and returns 403 — even when the connected Google account actually
owns the domain property "sc-domain:eventstaff.com". Every connector therefore resolves the
stored value against the account's real property list before querying, repairs the Site row
when a match is found, and raises one clear, actionable error when the account has no access
at all (instead of three cryptic 403s).
"""
import logging
from urllib.parse import urlparse

from googleapiclient.discovery import build

from pipeline.utils.auth import get_google_credentials
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)


def _bare_domain(value: str) -> str:
    """'sc-domain:x.com' / 'https://www.x.com/' / 'x.com' -> 'x.com'."""
    v = (value or "").strip().lower()
    if v.startswith("sc-domain:"):
        v = v[len("sc-domain:"):]
    if "://" in v:
        v = urlparse(v).netloc
    return v.strip("/").removeprefix("www.")


def list_verified_properties(service=None) -> set[str]:
    """Property URLs the connected Google account can actually query."""
    if service is None:
        creds = get_google_credentials()
        service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    entries = service.sites().list().execute().get("siteEntry", [])
    return {
        e["siteUrl"] for e in entries
        if e.get("permissionLevel") != "siteUnverifiedUser"
    }


def resolve_gsc_property(site_id: str, stored: str, service=None) -> str:
    """Return a property URL the account can query for `stored`, repairing the Site row
    when the stored value was wrong. Raises ValueError with an actionable message when the
    account has no Search Console access to the domain at all.

    If the account's property list can't be fetched (transient API error), returns `stored`
    unchanged — the query itself will then produce its own error.
    """
    try:
        allowed = list_verified_properties(service)
    except Exception as e:
        logger.warning(f"[gsc_property] sites.list() failed, using stored value as-is: {e}")
        return stored

    if stored in allowed:
        return stored

    domain = _bare_domain(stored)
    candidates = [
        f"sc-domain:{domain}",
        f"https://{domain}/", f"https://www.{domain}/",
        f"http://{domain}/", f"http://www.{domain}/",
    ]
    match = next((c for c in candidates if c in allowed), None)
    if match is None:
        properties_list = ", ".join(sorted(allowed)) or "none"
        raise ValueError(
            f"Your Google account has no Search Console access to '{domain}'. "
            f"Verify the property in Search Console (search.google.com/search-console), "
            f"or set the exact property URL in Settings -> General -> gsc_property. "
            f"Properties this account can query: {properties_list}"
        )

    logger.info(f"[gsc_property] Repaired gsc_property for {site_id!r}: {stored!r} -> {match!r}")
    _persist_repair(site_id, match)
    return match


def _persist_repair(site_id: str, resolved: str) -> None:
    """Store the resolved property on the Site row so future syncs (and the other two GSC
    connectors) query it directly. Best-effort — resolution still works if this fails."""
    from pipeline.services.site_service import get_site
    try:
        with get_session() as session:
            site = get_site(session, site_id)
            if site is not None and site.gsc_property != resolved:
                site.gsc_property = resolved
                session.commit()
    except Exception as e:
        logger.warning(f"[gsc_property] could not persist repaired property: {e}")
