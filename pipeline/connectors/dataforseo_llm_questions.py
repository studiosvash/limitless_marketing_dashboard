"""
pipeline/connectors/dataforseo_llm_questions.py — which AI questions does this URL turn up in?

One question this answers, for a domain or for a single page: when somebody asks an answer
engine something, does OUR page get pulled into the reply — and if so, which questions.

Endpoint: POST /v3/ai_optimization/llm_mentions/search/live

WHAT THE ENDPOINT REALLY RETURNS (verified live against premierstaff.com, 2026-08-11 — 62
questions on chat_gpt alone), one row per question:

    question            the prompt the engine was asked, verbatim
    answer              the reply the user saw
    ai_search_volume    how often that question is asked
    monthly_searches    12 months of it
    first/last_response_at   how long it has been answering that way
    fan_out_queries     the sub-searches the engine ran internally
    sources[]           pages it CITED in the answer
    search_results[]    pages it RETRIEVED but did not necessarily cite

CITED IS NOT THE SAME AS SEEN, and this module will not flatten them. On the live account
every premierstaff.com page appeared in `search_results` and NONE in `sources`: the engine is
finding the pages and quoting somebody else. That gap is the most actionable thing the
endpoint says, and a single "mentioned" flag would erase it.

TWO CONSTRAINTS, both found by calling the API rather than reading about it:

  * `target[].domain` REJECTS a path. `premierstaff.com/blog/x` returns 40501 "must be a valid
    domain like 'example.com'". So a page-level answer comes from querying the DOMAIN and
    filtering on the URL here — which is also cheaper, since one call then answers for every
    page on that domain.
  * the endpoint's own filter list carries platform, location, language, ai_search_volume, the
    two timestamps and model_name — and NO url field. The local filter is not a shortcut; it
    is the only way.

COST: metered per returned row, like every Labs call. One request per platform. The caller
books it through `record_cost` and is gated by `ensure_budget` before it ever gets here.
"""
import os
from urllib.parse import urlsplit, urlunsplit

import requests
from dotenv import load_dotenv

from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.utils.logger import get_logger
from pipeline.utils.retry import with_retry
from pipeline.utils.site_ids import normalize_domain

load_dotenv()

logger = get_logger("dataforseo_llm_questions")

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
SEARCH_ENDPOINT = f"{DATAFORSEO_BASE}/ai_optimization/llm_mentions/search/live"

# The two platforms this endpoint covers. Claude and Perplexity are NOT available from it at
# any price — same limitation llm_mentions_service documents for the mentions endpoints.
PLATFORMS = ("chat_gpt", "google")

DEFAULT_LIMIT = 100


def domain_of(target: str) -> str:
    """The bare host of whatever the user typed. `normalize_domain` is the one canonicaliser."""
    return normalize_domain(str(target or ""))


def _canonical_url(url: str) -> str:
    """A URL reduced to the part that identifies the page.

    Every URL the engine returns carries `?utm_source=chatgpt.com`, and a trailing slash comes
    and goes between the two lists — so comparing raw strings would report a page as absent
    from its own question.
    """
    raw = str(url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    host = (parts.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = (parts.path or "").rstrip("/")
    # Query and fragment dropped entirely: no page on this product's sites is identified by
    # one, and every value seen in the wild is tracking.
    return urlunsplit((parts.scheme or "https", host, path, "", ""))


def url_matches(candidate: str, wanted: str) -> bool:
    """Is `candidate` the same page as `wanted`, ignoring tracking and trailing slashes?"""
    a, b = _canonical_url(candidate), _canonical_url(wanted)
    return bool(a) and a == b


def _our_hit(links, our_domain: str):
    """The first link in `links` that belongs to us, canonicalised. None when none do."""
    for link in links or []:
        if not isinstance(link, dict):
            continue
        url = link.get("url")
        host = normalize_domain(link.get("domain") or url or "")
        if host and host == our_domain and url:
            return _canonical_url(url)
    return None


def parse_questions(payload: dict, target: str, page_url: str = "") -> list[dict]:
    """Rows for the questions where our domain (or one exact page) turns up.

    A question in which we appear nowhere is dropped rather than returned with empty flags —
    the caller is asking "where do we show up", and a list padded with places we do not is a
    worse answer than a short one.

    Never raises: a malformed envelope yields [].
    """
    our_domain = domain_of(target)
    if not our_domain:
        return []

    try:
        result = ((payload or {}).get("tasks") or [{}])[0].get("result") or []
        items = (result[0] or {}).get("items") or [] if result else []
    except (AttributeError, IndexError, TypeError):
        return []

    rows: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cited_url = _our_hit(item.get("sources"), our_domain)
        seen_url = _our_hit(item.get("search_results"), our_domain)
        our_url = cited_url or seen_url
        if not our_url:
            continue                       # this question is not about us
        if page_url and not url_matches(our_url, page_url):
            continue

        volume = item.get("ai_search_volume")
        rows.append({
            "question": item.get("question") or "",
            "answer": item.get("answer") or "",
            "platform": item.get("platform") or "",
            "model_name": item.get("model_name") or "",
            "our_url": our_url,
            # Kept apart deliberately — see the module docstring.
            "cited": cited_url is not None,
            "retrieved": seen_url is not None,
            # None, not 0: "we were not told" and "nobody asks this" are different facts.
            "ai_search_volume": int(volume) if isinstance(volume, (int, float)) else None,
            "monthly_searches": item.get("monthly_searches") or {},
            "first_response_at": item.get("first_response_at"),
            "last_response_at": item.get("last_response_at"),
            "fan_out_queries": item.get("fan_out_queries") or [],
            # Who the engine cited instead of us — the competitive read on this question.
            "cited_domains": [
                normalize_domain(s.get("domain") or s.get("url") or "")
                for s in (item.get("sources") or []) if isinstance(s, dict)
            ],
        })

    # Most-asked first; unknown volume sorts last rather than as a zero.
    rows.sort(key=lambda r: (r["ai_search_volume"] is None, -(r["ai_search_volume"] or 0)))
    return rows


@with_retry(max_retries=2, base_delay=3.0)
def _post(payload: list, login: str, password: str) -> dict:
    response = requests.post(SEARCH_ENDPOINT, json=payload, auth=(login, password), timeout=120)
    response.raise_for_status()
    return response.json()


def fetch_llm_questions(target: str, page_url: str = "", platforms=PLATFORMS,
                        location_name: str = "United States", language_code: str = "en",
                        limit: int = DEFAULT_LIMIT, site_id: str = "") -> dict:
    """{status, rows, total, platforms, cost} — the questions this URL turns up in.

    `target` may be a domain OR a deep URL; the domain is extracted for the request and the
    full URL, when it has a path, additionally filters the rows. That is the whole page-level
    story: one call per platform, filtered locally.
    """
    login, password = os.getenv("DATAFORSEO_LOGIN"), os.getenv("DATAFORSEO_PASSWORD")
    if not login or not password:
        return {"status": "setup", "rows": [], "total": 0, "cost": 0.0,
                "error": "DataForSEO credentials are not configured."}

    our_domain = domain_of(target)
    if not our_domain:
        return {"status": "error", "rows": [], "total": 0, "cost": 0.0,
                "error": f"{target!r} is not a domain or URL."}

    # A path only filters when the user actually gave one; a bare domain means "everything".
    wanted_page = target if urlsplit(
        target if "://" in str(target) else "https://" + str(target)).path.strip("/") else ""

    rows: list[dict] = []
    cost = 0.0
    failed: list[str] = []
    for platform in platforms:
        payload = [{
            "target": [{"domain": our_domain, "search_scope": ["any"]}],
            "platform": platform,
            "location_name": location_name,
            "language_code": language_code,
            "limit": limit,
            "order_by": ["ai_search_volume,desc"],
        }]
        try:
            data = _post(payload, login, password)
        except Exception as exc:
            # One platform failing must not lose the other's answers.
            logger.error(f"[llm_questions] {platform} search failed: {exc}")
            failed.append(platform)
            continue
        rows.extend(parse_questions(data, our_domain, page_url=page_url or wanted_page))
        cost += extract_cost(data)

    if cost:
        record_cost("dataforseo_llm_questions", site_id, cost, units=len(rows),
                    notes=f"llm_mentions/search for {our_domain}")

    rows.sort(key=lambda r: (r["ai_search_volume"] is None, -(r["ai_search_volume"] or 0)))

    if failed and not rows:
        return {"status": "error", "rows": [], "total": 0, "cost": cost,
                "error": f"DataForSEO did not answer for: {', '.join(failed)}."}

    return {
        "status": "ok",
        "rows": rows,
        "total": len(rows),
        "domain": our_domain,
        "page": wanted_page or None,
        "platforms": [p for p in platforms if p not in failed],
        "partial": failed or None,
        "cost": cost,
    }
