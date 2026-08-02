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

`www.x.com` and `x.com` ARE merged, as of 2026-08-02. This reverses the original decision, so
the reasoning on both sides is worth keeping:

  Against merging — Search Console models `https://www.x.com/` and `https://x.com/` as two
  separate URL-prefix properties, so a site that genuinely serves different content on the two
  hosts would have one host's traffic attributed to the other.

  For merging (what actually happened) — the registry let the same site be added twice, once as
  `premierstaff.com` and once as `www.premierstaff.com`. Two projects, two slugs, two sync
  budgets, two halves of one site's history, and a project switcher that offered the user a
  choice between them with no way to tell which was "the real one". Nobody in this product runs
  the two hosts as different sites; every real domain here redirects one to the other.

`normalize_domain()` is now the single registration rule — `add_site` stores its output as
`sites.site_url` and dedupes on it, so both spellings resolve to one project. `resolve_site_ids`
expands to BOTH hosts so analytics rows written under either spelling before the rule existed
stay reachable.

`canonical_domain()` deliberately still keeps `www.` — it answers "which host is this string?",
which is the right question when comparing a third-party URL against a property list. Use
`normalize_domain()` when the question is "which site is this?".
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
        netloc = urlsplit(raw).netloc
        if netloc:
            raw = netloc
        elif "://" in raw:
            # A scheme with no authority — "https://" on its own. There is no host here. The
            # `or raw` fallback this replaces returned "https:", which normalised to the
            # domain-shaped string "https" and would have been stored as a site_url.
            return ""
        # else: protocol-relative or a doubled slash in a path; the split below handles it.
    raw = raw.split("/", 1)[0]
    return raw.strip("/").strip()


def normalize_domain(site_id: str | None) -> str:
    """The ONE registration form of a domain, whatever spelling the user typed.

    All six of these are the same site and all normalise to `premierstaff.com`:

        https://premierstaff.com        http://premierstaff.com        premierstaff.com
        https://www.premierstaff.com    http://www.premierstaff.com    www.premierstaff.com

    …as do `sc-domain:premierstaff.com`, a trailing slash, a path, a port, a trailing dot and
    any capitalisation. `add_site` stores this and dedupes on it, so a site cannot be registered
    twice under two spellings. Returns `""` when there is no host to read, which callers must
    treat as invalid input rather than as a domain.
    """
    host = canonical_domain(site_id)
    if not host:
        return ""
    host = host.rsplit("@", 1)[-1]   # drop any user:pass@ left in a netloc
    host = host.split(":", 1)[0]     # drop :port
    host = host.rstrip(".")          # "example.com." is the fully-qualified same host
    if host.startswith("www."):
        host = host[4:]
    return host


def resolve_site_ids(site_id: str | None) -> list[str]:
    """Every spelling `site_id` could be stored under, for `Column.site_id.in_(...)`.

    The exact input is always first so an exact match is never reordered away. Returns `[]` for
    an empty input — `.in_([])` matches nothing, which is the honest answer, whereas `.in_([""])`
    would be a silent miss that reads like "this site has no data".

    Covers both the www and non-www host (see the module docstring): a project registered as
    `premierstaff.com` must still find the rows a connector wrote under
    `https://www.premierstaff.com/` before `normalize_domain` existed.
    """
    given = (site_id or "").strip()
    if not given:
        return []

    domain = canonical_domain(given)
    if not domain:
        return [given]

    bare = normalize_domain(given) or domain
    hosts = [bare, f"www.{bare}", domain]

    candidates = [given]
    seen_hosts: set[str] = set()
    for host in hosts:
        if not host or host in seen_hosts:
            continue
        seen_hosts.add(host)
        candidates += [
            host,
            f"{SC_DOMAIN_PREFIX}{host}",
            f"https://{host}/",
            f"https://{host}",
            f"http://{host}/",
            f"http://{host}",
        ]

    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out
