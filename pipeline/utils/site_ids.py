"""One site, several spellings — the canonical `site_id` matcher.

The two databases are joined by a `site_url` STRING (`.claude/skills.md` §3), and nothing
enforces which spelling of a site gets written. In practice four appear:

    premierstaff.com                 <- sites.site_url, what every view resolves a slug to
    sc-domain:premierstaff.com       <- Search Console domain properties
    https://premierstaff.com/        <- Search Console URL-prefix properties, and whatever a
    https://premierstaff.com            connector was handed the day it ran

Five services each carried their own two-line copy of this helper, and every copy knew only the
`sc-domain:` prefix. So a project registered as `premierstaff.com` could not see the 16
`ai_keyword_data` rows written under `https://premierstaff.com/` — the AI Optimization page
rendered empty over data that was already in the database. `saved_keywords` was split across the
two spellings the same way (24 rows / 16 rows).

The fix is one matcher, used everywhere, that expands a site_id into every spelling it could
have been stored under. This is deliberately a READ-side widening, not a data migration: it
makes existing rows reachable without rewriting anyone's history. New writes should still go
through `sites.site_url`.

`www.x.com` and `x.com` are NOT merged — Search Console treats them as different properties, and
silently unioning them would attribute one host's traffic to the other.
"""
from urllib.parse import urlsplit

SC_DOMAIN_PREFIX = "sc-domain:"


def canonical_domain(site_id: str | None) -> str:
    """The bare host for a site_id in any of its spellings. `""` when there is nothing to match.

    Any path is dropped: the join key identifies a SITE, and `sites.site_url` never carries one.
    """
    raw = (site_id or "").strip().lower()
    if not raw:
        return ""
    if raw.startswith(SC_DOMAIN_PREFIX):
        raw = raw[len(SC_DOMAIN_PREFIX):]
    if "//" in raw:
        # urlsplit only populates .netloc when a scheme is present, which is exactly the case
        # this branch guards; a bare "example.com/path" would otherwise land entirely in .path.
        raw = urlsplit(raw).netloc or raw
    raw = raw.split("/", 1)[0]
    return raw.strip("/").strip()


def resolve_site_ids(site_id: str | None) -> list[str]:
    """Every spelling `site_id` could be stored under, for `Column.site_id.in_(...)`.

    The exact input is always first so an exact match is never reordered away. Returns `[]` for
    an empty input — `.in_([])` matches nothing, which is the honest answer, whereas `.in_([""])`
    would be a silent miss that reads like "this site has no data".
    """
    given = (site_id or "").strip()
    if not given:
        return []

    domain = canonical_domain(given)
    if not domain:
        return [given]

    candidates = [
        given,
        domain,
        f"{SC_DOMAIN_PREFIX}{domain}",
        f"https://{domain}/",
        f"https://{domain}",
        f"http://{domain}/",
        f"http://{domain}",
    ]

    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out
