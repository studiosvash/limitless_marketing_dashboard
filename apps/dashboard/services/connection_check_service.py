"""apps/dashboard/services/connection_check_service.py — "is this integration actually working?"

One service, four consumers:
  * the Add-domain modal's "Check all connections" button (before a site is created)
  * Settings -> Connections' "Test connection" button (after credentials are edited)
  * `manage.py check_connections` (operator CLI)
  * `start_sync_run`'s pre-flight warnings (the cheap, no-network half only)

WHY THIS EXISTS. Before it, credential problems were only discoverable by starting a 20-30
minute sync and reading the wreckage afterwards:
  * GA4 had no access check at all -- only `if not property_id`. A wrong-but-present id saved
    cleanly and failed mid-sync.
  * DataForSEO had no check of any kind. Bad credentials made every DataForSEO connector fail
    to construct, `_get_connector` returned None, and the run still reported SUCCESS.
  * The add-site flow collected no credentials, so a new domain was created with
    `gsc_property` = the bare domain (which Search Console reads as `http://domain`, not the
    `sc-domain:` property the account owns) and `ga4_property_id` = NULL.

TWO LEVELS, DELIBERATELY SEPARATE:
  * `credential_presence()` -- no network, safe to call on every request. Answers "is it
    configured?"
  * `check_connections()` -- live API calls. Answers "does it work?" Only ever called because
    a human pressed a button or ran the command, which is why it does not violate the
    "no external API in a page-data endpoint" contract (same category as /api/research).

Per the service convention: nothing here raises. Every probe is wrapped and reports a failure
as data, because the entire point is to survive the failures it is describing.
"""
import logging
import os

logger = logging.getLogger(__name__)

# ── State vocabulary ────────────────────────────────────────────────────────────
# "ok"      the integration was exercised and worked
# "fail"    it was exercised and did not work -- the detail says why
# "absent"  not configured at all. Not a failure: skipping GA4 is a legitimate choice.
# "unknown" configured, but cannot be verified without spending real money or minutes
#           (PageSpeed). Reported honestly rather than guessed either way.
STATE_OK, STATE_FAIL, STATE_ABSENT, STATE_UNKNOWN = "ok", "fail", "absent", "unknown"

# Which credential family each connector needs before it can do anything at all.
# Used to turn "GA4 is not configured" into "these 1 of 14 connectors will be skipped",
# which is a fact the user can act on, unlike a blanket refusal.
CONNECTOR_REQUIREMENTS: dict[str, str] = {
    "gsc": "gsc",
    "gsc_keywords": "gsc",
    "gsc_pages": "gsc",
    "url_inspection": "gsc",
    "ga4": "ga4",
    "pagespeed": "pagespeed",
    "sitemap": "sitemap",
    "dataforseo_serp": "dataforseo",
    "dataforseo_keywords": "dataforseo",
    "dataforseo_backlinks": "dataforseo",
    "dataforseo_labs_competitors": "dataforseo",
    "dataforseo_serp_competitors": "dataforseo",
    "dataforseo_onpage": "dataforseo",
    "dataforseo_opportunities": "dataforseo",
    "dataforseo_ai_keywords": "dataforseo",
    "google_ads": "google_ads",
    "google_ads_search_terms": "google_ads",
    "meta": "meta",
}

FAMILY_LABELS = {
    "gsc": "Google Search Console",
    "ga4": "Google Analytics 4",
    "dataforseo": "DataForSEO",
    "pagespeed": "PageSpeed Insights",
    "sitemap": "Sitemap",
    "google_ads": "Google Ads",
    "meta": "Meta Ads",
    "openai": "OpenAI",
}


# ── Level 1: presence (no network) ──────────────────────────────────────────────

def credential_presence(site_id: str | None = None) -> dict[str, bool]:
    """Which credential families are configured. No network calls — safe on any request path.

    `gsc`/`ga4` are per-site (they live on the Site row); everything else is process-wide env.
    A missing Site row makes the per-site families False rather than raising, so this is safe
    to call before a site exists (the Add-domain modal does exactly that).
    """
    google_oauth = all(os.getenv(k) for k in
                       ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"))

    ga4_configured = False
    gsc_configured = False
    if site_id:
        try:
            from pipeline.services.site_service import get_site
            from pipeline.utils.db_connection import get_session
            with get_session() as session:
                site = get_site(session, site_id)
                if site is not None:
                    ga4_configured = bool(site.ga4_property_id)
                    gsc_configured = bool(site.gsc_property)
        except Exception:
            logger.error("[connection_check] could not read Site row for presence check",
                         exc_info=True)

    return {
        # GSC/GA4 need BOTH the shared OAuth identity and this site's own property.
        "gsc": google_oauth and gsc_configured,
        "ga4": google_oauth and ga4_configured,
        "dataforseo": bool(os.getenv("DATAFORSEO_LOGIN") and os.getenv("DATAFORSEO_PASSWORD")),
        "pagespeed": bool(os.getenv("GOOGLE_API_KEY")),
        "sitemap": bool(os.getenv("FRAMER_SITEMAP_URL")),
        "google_ads": google_oauth and bool(os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")),
        "meta": bool(os.getenv("META_ACCESS_TOKEN")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }


def missing_requirements(site_id: str, connectors: list[str]) -> dict[str, list[str]]:
    """family -> the connectors in `connectors` that cannot run without it.

    Only families that are actually MISSING appear. Connectors with no entry in
    CONNECTOR_REQUIREMENTS are assumed to need nothing and are never reported.
    """
    present = credential_presence(site_id)
    out: dict[str, list[str]] = {}
    for name in connectors:
        family = CONNECTOR_REQUIREMENTS.get(name)
        if not family or present.get(family, True):
            continue
        out.setdefault(family, []).append(name)
    return out


def requirement_warnings(site_id: str, connectors: list[str]) -> list[str]:
    """Human-readable pre-flight warnings for a sync about to start.

    These are WARNINGS, not errors, and that distinction is the whole point. The previous
    behaviour refused the entire run with a 400 when GA4 was unset -- which meant a brand-new
    domain (no GA4 property yet, by definition) could not sync ANYTHING, including the 9
    connectors that never touch GA4. It even blocked the Backlinks refresh, which needs
    neither GSC nor GA4. Now the run proceeds, the unusable connectors are skipped, and the
    user is told exactly which ones and how to fix it.
    """
    warnings = []
    for family, blocked in sorted(missing_requirements(site_id, connectors).items()):
        label = FAMILY_LABELS.get(family, family)
        where = ("Settings → Connections" if family in ("gsc", "ga4")
                 else "the server environment (.env)")
        warnings.append(
            f"{label} is not configured, so {len(blocked)} step(s) will be skipped "
            f"({', '.join(blocked)}). Set it in {where}, then refresh again."
        )
    return warnings


# ── Level 2: live probes ────────────────────────────────────────────────────────

def _check(cid, state, detail, **extra):
    return {"id": cid, "label": FAMILY_LABELS.get(cid, cid),
            "state": state, "detail": detail, **extra}


def _check_gsc(domain: str, gsc_property: str | None) -> dict:
    """Resolve the property against the account's real verified list.

    Also returns `options` — every property this account can query — because the single most
    useful thing to show someone whose GSC check failed is the list of what they COULD have
    picked. The Add-domain modal renders it as a dropdown so the value cannot be mistyped.
    """
    try:
        from pipeline.connectors.gsc_property import list_verified_properties
        options = sorted(list_verified_properties())
    except Exception as exc:
        return _check("gsc", STATE_FAIL,
                      f"Could not read the Search Console property list: {exc}", options=[])

    if not options:
        return _check("gsc", STATE_FAIL,
                      "The connected Google account has no verified Search Console properties.",
                      options=[])

    candidate = (gsc_property or "").strip() or domain
    try:
        # resolve_gsc_property persists a repair onto the Site row. Passing the domain as
        # site_id is safe: for a site that does not exist yet get_site finds nothing and the
        # repair is a no-op, and for one that does it is the correct key.
        from pipeline.connectors.gsc_property import resolve_gsc_property
        resolved = resolve_gsc_property(domain, candidate)
    except ValueError as exc:
        return _check("gsc", STATE_FAIL, str(exc), options=options)
    except Exception as exc:
        return _check("gsc", STATE_FAIL, f"Search Console check failed: {exc}", options=options)

    return _check("gsc", STATE_OK, f"Verified property: {resolved}",
                  options=options, resolved=resolved)


def _check_ga4(ga4_property_id: str | None) -> dict:
    if not (ga4_property_id or "").strip():
        return _check("ga4", STATE_ABSENT,
                      "No GA4 property set. Analytics-based pages will stay empty.")
    from pipeline.connectors.ga4 import normalise_property_id, probe_property
    ok, detail = probe_property(ga4_property_id)
    return _check("ga4", STATE_OK if ok else STATE_FAIL, detail,
                  resolved=normalise_property_id(ga4_property_id))


def _check_dataforseo(target: str | None) -> dict:
    from pipeline.connectors.dataforseo_probe import credentials_present, probe_credentials
    if not credentials_present():
        return _check("dataforseo", STATE_ABSENT,
                      "DataForSEO credentials are not set. Keyword, competitor, backlink and "
                      "on-page data will stay empty.")
    ok, detail = probe_credentials()
    if ok and target:
        detail = f"{detail} Target domain: {target}."
    return _check("dataforseo", STATE_OK if ok else STATE_FAIL, detail)


def _check_pagespeed() -> dict:
    """Presence only, and labelled as such.

    A real PageSpeed probe means a full Lighthouse run: ~20-60 seconds and a genuine quota
    hit, for one bit of information. Claiming "ok" from a present key would be a guess, so the
    state is `unknown` and the detail says why.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        return _check("pagespeed", STATE_ABSENT,
                      "GOOGLE_API_KEY is not set — PageSpeed scores will stay empty.")
    return _check("pagespeed", STATE_UNKNOWN,
                  "GOOGLE_API_KEY is set. Not probed: a PageSpeed check is a full Lighthouse "
                  "run and would cost real quota and ~30s.")


def _check_openai() -> dict:
    """`/v1/models` is a free authenticated GET — the one LLM check that costs nothing."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return _check("openai", STATE_ABSENT,
                      "OPENAI_API_KEY is not set — the AI overview summary will be "
                      "unavailable. (Prompt runs and the Answer Inspector go through "
                      "DataForSEO, not this key.)")
    try:
        import requests
        resp = requests.get("https://api.openai.com/v1/models",
                            headers={"Authorization": f"Bearer {key}"}, timeout=15)
    except Exception as exc:
        return _check("openai", STATE_FAIL, f"Could not reach OpenAI: {exc}")
    if resp.status_code == 401:
        return _check("openai", STATE_FAIL, "OpenAI rejected the API key (401).")
    if resp.status_code != 200:
        return _check("openai", STATE_FAIL, f"OpenAI returned HTTP {resp.status_code}.")
    return _check("openai", STATE_OK, "API key valid.")


def _check_google_ads() -> dict:
    missing = [k for k in ("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID")
               if not os.getenv(k)]
    if missing:
        return _check("google_ads", STATE_ABSENT,
                      f"Not configured ({', '.join(missing)} unset) — the Ads pages will stay "
                      f"in their setup state.")
    return _check("google_ads", STATE_UNKNOWN,
                  "Credentials are set. Not probed: the Ads API has no free validation call.")


def test_google_ads_credential(fields: dict) -> dict:
    """Live-probe a typed-in (not necessarily saved) Google Ads credential.
    fields: {developer_token, customer_id, login_customer_id?}
    """
    from pipeline.connectors.google_ads import probe_credential
    developer_token = (fields.get("developer_token") or "").strip()
    customer_id = (fields.get("customer_id") or "").replace("-", "").strip()
    login_customer_id = (fields.get("login_customer_id") or "").replace("-", "").strip() or None
    if not developer_token or not customer_id:
        return {"ok": False, "detail": "Developer Token and Customer ID are both required."}
    ok, detail = probe_credential(developer_token, customer_id, login_customer_id)
    return {"ok": ok, "detail": detail}


def test_meta_ads_credential(fields: dict) -> dict:
    """Live-probe a typed-in (not necessarily saved) Meta Ads credential.
    fields: {access_token, ad_account_id}
    """
    from pipeline.connectors.meta import probe_credential
    access_token = (fields.get("access_token") or "").strip()
    ad_account_id = (fields.get("ad_account_id") or "").strip()
    if not access_token or not ad_account_id:
        return {"ok": False, "detail": "Access Token and Ad Account ID are both required."}
    ok, detail = probe_credential(access_token, ad_account_id)
    return {"ok": ok, "detail": detail}


def check_connections(domain: str, gsc_property: str | None = None,
                      ga4_property_id: str | None = None,
                      dataforseo_target: str | None = None,
                      include_optional: bool = True) -> dict:
    """Live-probe every integration for `domain`. Returns {ok, checks[]}.

    `ok` covers only the three integrations the dashboard's core pages depend on -- GSC, GA4
    and DataForSEO -- and only counts a hard `fail`. An `absent` integration does NOT make
    `ok` false: choosing to skip GA4 is a legitimate decision the Add-domain modal explicitly
    offers, and treating it as a failure would make "Skip for now" look broken.
    """
    checks = [
        _check_gsc(domain, gsc_property),
        _check_ga4(ga4_property_id),
        _check_dataforseo(dataforseo_target),
    ]
    if include_optional:
        checks += [_check_pagespeed(), _check_openai(), _check_google_ads()]

    core = {"gsc", "ga4", "dataforseo"}
    ok = not any(c["state"] == STATE_FAIL for c in checks if c["id"] in core)
    return {"ok": ok, "checks": checks}
