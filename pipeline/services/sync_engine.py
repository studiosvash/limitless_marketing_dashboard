"""
pipeline/services/sync_engine.py — Orchestrates connector runs for the FuseHealth sync system.

Architecture contract:
  - Pages NEVER call connectors directly. Only this engine calls connectors.
  - Views POST to /sync/all/ or /sync/page/<page>/, which launch a background thread
    that calls sync_all() or sync_page() here.
  - Progress is written to RefreshRun rows; HTMX polls GET /sync/status/ every 2s.
"""

import importlib
import logging

from pipeline.utils.logger import get_logger

logger = get_logger("sync_engine")


# ---------------------------------------------------------------------------
# Registry: page → connectors
# Only WORKING connectors or NO_CREDS_NEEDED are listed.
# BALANCE_NEGATIVE (DataForSEO) and CREDENTIALS_MISSING connectors are omitted
# and will be enabled when credentials / credits become available.
# ---------------------------------------------------------------------------

PAGE_CONNECTORS: dict[str, list[str]] = {
    "overview":    ["gsc", "ga4"],
    "seo":         ["gsc", "ga4"],
    # Ads + Backlinks connectors DO exist (google_ads.py / dataforseo_backlinks.py). They were
    # previously left empty because credentials were blocked, but that made the Refresh button
    # a silent no-op. Wire them to their real connectors so Refresh actually runs them the
    # moment credentials are valid; with no credentials the connector factory returns None and
    # the run records a clean "skipped/error" for that connector instead of silently doing
    # nothing.
    "ads":         ["google_ads", "ga4"],
    "keywords":    ["gsc_keywords", "dataforseo_ai_keywords"],
    "pages":       ["gsc_pages", "url_inspection", "pagespeed"],
    "backlinks":   ["dataforseo_backlinks"],
    "insights":    [],                    # no connectors — data entered by user
    "alerts":      ["gsc", "ga4"],        # anomaly detection runs on fresh data
    "settings":    [],                    # no data to sync
    # Positioning per-page refresh captures per-keyword competitor ranks (SEMrush-style).
    "positioning": ["gsc_keywords", "dataforseo_serp_competitors"],
    # AI visibility / AI-keyword volume refresh (DataForSEO AI Optimization API).
    "ai":          ["dataforseo_ai_keywords"],
    # Site-audit crawl (DataForSEO OnPage) -- distinct from the "pages" GSC/PageSpeed refresh.
    "audit":       ["dataforseo_onpage"],
}

ALL_CONNECTORS: list[str] = [
    "gsc",
    "ga4",
    "gsc_keywords",
    "gsc_pages",
    "url_inspection",
    "pagespeed",
    "sitemap",
]


# ---------------------------------------------------------------------------
# Connector factory
# ---------------------------------------------------------------------------

def _get_connector(name: str):
    """
    Import and instantiate a connector by name.
    Returns None if the module cannot be imported or credentials are missing.
    Lazy imports avoid circular import issues at module load time.
    """
    connector_map: dict[str, tuple[str, str]] = {
        "gsc":          ("pipeline.connectors.gsc",                   "GSCConnector"),
        "ga4":          ("pipeline.connectors.ga4",                   "GA4Connector"),
        "gsc_keywords": ("pipeline.connectors.gsc_keywords",          "GSCKeywordsConnector"),
        "gsc_pages":    ("pipeline.connectors.gsc_pages",             "GSCPagesConnector"),
        "url_inspection":("pipeline.connectors.url_inspection",       "URLInspectionConnector"),
        "pagespeed":    ("pipeline.connectors.pagespeed",             "PageSpeedConnector"),
        "sitemap":      ("pipeline.connectors.sitemap",               "SitemapConnector"),
        # DataForSEO — included in map so they can be enabled later; not in
        # PAGE_CONNECTORS or ALL_CONNECTORS until balance is positive.
        "dataforseo_keywords":         ("pipeline.connectors.dataforseo_keywords",         "DataForSEOKeywordsConnector"),
        "dataforseo_serp":             ("pipeline.connectors.dataforseo_serp",             "DataForSEOSerpConnector"),
        "dataforseo_backlinks":        ("pipeline.connectors.dataforseo_backlinks",        "DataForSEOBacklinksConnector"),
        "dataforseo_labs_competitors": ("pipeline.connectors.dataforseo_labs_competitors", "DataForSEOLabsCompetitorsConnector"),
        "dataforseo_onpage":           ("pipeline.connectors.dataforseo_onpage",           "DataForSEOOnPageConnector"),
        "dataforseo_opportunities":    ("pipeline.connectors.dataforseo_opportunities",    "DataForSEOOpportunitiesConnector"),
        # Additive 2026-06-15: per-keyword competitor rank capture + AI search keyword data.
        "dataforseo_serp_competitors": ("pipeline.connectors.dataforseo_serp_competitors", "DataForSEOSerpCompetitorsConnector"),
        "dataforseo_ai_keywords":      ("pipeline.connectors.dataforseo_ai_keywords",      "DataForSEOAIKeywordsConnector"),
        # Credentials-missing connectors — in map for future use.
        "google_ads":  ("pipeline.connectors.google_ads",  "GoogleAdsConnector"),
        "meta":        ("pipeline.connectors.meta",        "MetaConnector"),
        "linkedin":    ("pipeline.connectors.linkedin",    "LinkedInConnector"),
        "webflow":     ("pipeline.connectors.webflow",     "WebflowConnector"),
        "wordpress":   ("pipeline.connectors.wordpress",   "WordPressConnector"),
    }

    if name not in connector_map:
        logger.warning(f"[sync_engine] Unknown connector: {name!r}")
        return None

    module_path, class_name = connector_map[name]
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls()
    except (ValueError, ImportError, Exception) as exc:
        logger.warning(f"[sync_engine] Could not load connector {name!r}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Post-sync aggregate rebuild
# ---------------------------------------------------------------------------

def _run_post_sync(site_url: str, connectors_run: list[str]) -> None:
    """
    Trigger aggregate rebuild if SEO data was refreshed.
    Called silently — failures are logged but never surface to the caller.
    """
    if any(c in connectors_run for c in ("gsc", "ga4")):
        try:
            from pipeline.services.aggregate_service import rebuild_seo_aggregates
            logger.info(f"[sync_engine] Running aggregate rebuild for {site_url!r}")
            rebuild_seo_aggregates(site_url)
        except Exception as exc:
            logger.warning(f"[sync_engine] Aggregate rebuild failed for {site_url!r}: {exc}")

        # Detect anomalies on the freshly-synced SEO data (no external API).
        try:
            from pipeline.services.anomaly_service import detect_recent_anomalies
            logger.info(f"[sync_engine] Running anomaly detection for {site_url!r}")
            n = detect_recent_anomalies(site_url)
            logger.info(f"[sync_engine] Anomaly detection wrote {n} anomalies for {site_url!r}")
        except Exception as exc:
            logger.warning(f"[sync_engine] Anomaly detection failed for {site_url!r}: {exc}")

        # Derive lightweight technical issues from owned data (no external API).
        try:
            from pipeline.services.technical_issues_service import rebuild_technical_issues
            logger.info(f"[sync_engine] Rebuilding technical issues for {site_url!r}")
            n = rebuild_technical_issues(site_url)
            logger.info(f"[sync_engine] Technical issues: wrote {n} for {site_url!r}")
        except Exception as exc:
            logger.warning(f"[sync_engine] Technical issue rebuild failed for {site_url!r}: {exc}")


# ---------------------------------------------------------------------------
# sync_all
# ---------------------------------------------------------------------------

def sync_all(site_url: str, run_id: int) -> dict:
    """
    Run all active connectors for site_url.
    Updates the RefreshRun progress row after each connector completes.
    Called from a background thread by the sync view.

    Returns a summary dict: {completed, total, records_written, errors}.
    """
    from apps.sync.models import RefreshRun, RefreshStatus  # type: ignore[import]
    from django.utils import timezone  # type: ignore[import]

    connectors = list(ALL_CONNECTORS)
    total = len(connectors)
    completed = 0
    total_records = 0
    errors: list[str] = []

    logger.info(
        f"[sync_engine] sync_all started — site={site_url!r} run_id={run_id} "
        f"total_connectors={total}"
    )

    # Initialise the run row.
    RefreshRun.objects.filter(pk=run_id).update(
        total_count=total,
        status=RefreshStatus.RUNNING,
    )

    for name in connectors:
        logger.info(f"[sync_engine] [{completed + 1}/{total}] Running connector: {name!r}")
        RefreshRun.objects.filter(pk=run_id).update(current_connector=name)

        connector = _get_connector(name)
        if connector is None:
            logger.warning(f"[sync_engine] Connector {name!r} unavailable — skipping")
            completed += 1
            RefreshRun.objects.filter(pk=run_id).update(completed_count=completed)
            continue

        try:
            result = connector.sync(site_id=site_url)
        except Exception as exc:
            logger.error(f"[sync_engine] Connector {name!r} raised an exception: {exc}")
            result = {"status": "error", "records_written": 0, "error": str(exc)}

        records = result.get("records_written", 0)
        completed += 1
        total_records += records

        if result.get("status") == "error":
            error_msg = result.get("error", "unknown error")
            errors.append(f"{name}: {error_msg}")
            logger.warning(f"[sync_engine] Connector {name!r} finished with error: {error_msg}")
        else:
            logger.info(
                f"[sync_engine] Connector {name!r} OK — records_written={records}"
            )

        RefreshRun.objects.filter(pk=run_id).update(
            completed_count=completed,
            records_written=total_records,
        )

    # Mark run complete.
    final_status = RefreshStatus.ERROR if errors else RefreshStatus.SUCCESS
    RefreshRun.objects.filter(pk=run_id).update(
        status=final_status,
        current_connector=None,
        completed_count=total,
        finished_at=timezone.now(),
        error_message="; ".join(errors) if errors else None,
    )

    logger.info(
        f"[sync_engine] sync_all finished — site={site_url!r} run_id={run_id} "
        f"status={final_status} records_written={total_records} errors={len(errors)}"
    )

    # Post-sync processing (aggregate rebuild etc.).
    _run_post_sync(site_url, connectors)

    return {
        "completed": completed,
        "total": total,
        "records_written": total_records,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# sync_page
# ---------------------------------------------------------------------------

def sync_page(page: str, site_url: str, run_id: int) -> dict:
    """
    Run only the connectors relevant to `page` for site_url.
    Updates the RefreshRun progress row after each connector completes.
    Called from a background thread by the sync view.

    Returns a summary dict: {completed, total, records_written, errors}.
    """
    from apps.sync.models import RefreshRun, RefreshStatus  # type: ignore[import]
    from django.utils import timezone  # type: ignore[import]

    connector_names = PAGE_CONNECTORS.get(page, [])
    total = len(connector_names)
    completed = 0
    total_records = 0
    errors: list[str] = []

    logger.info(
        f"[sync_engine] sync_page started — page={page!r} site={site_url!r} "
        f"run_id={run_id} connectors={connector_names}"
    )

    # Pages with no connectors succeed immediately.
    if total == 0:
        logger.info(
            f"[sync_engine] sync_page — page={page!r} has no connectors; marking SUCCESS"
        )
        RefreshRun.objects.filter(pk=run_id).update(
            total_count=0,
            completed_count=0,
            status=RefreshStatus.SUCCESS,
            finished_at=timezone.now(),
        )
        return {"completed": 0, "total": 0, "records_written": 0, "errors": []}

    RefreshRun.objects.filter(pk=run_id).update(
        total_count=total,
        status=RefreshStatus.RUNNING,
    )

    for name in connector_names:
        logger.info(f"[sync_engine] [{completed + 1}/{total}] Running connector: {name!r}")
        RefreshRun.objects.filter(pk=run_id).update(current_connector=name)

        connector = _get_connector(name)
        if connector is None:
            logger.warning(f"[sync_engine] Connector {name!r} unavailable — skipping")
            completed += 1
            RefreshRun.objects.filter(pk=run_id).update(completed_count=completed)
            continue

        try:
            result = connector.sync(site_id=site_url)
        except Exception as exc:
            logger.error(f"[sync_engine] Connector {name!r} raised an exception: {exc}")
            result = {"status": "error", "records_written": 0, "error": str(exc)}

        records = result.get("records_written", 0)
        completed += 1
        total_records += records

        if result.get("status") == "error":
            error_msg = result.get("error", "unknown error")
            errors.append(f"{name}: {error_msg}")
            logger.warning(f"[sync_engine] Connector {name!r} finished with error: {error_msg}")
        else:
            logger.info(
                f"[sync_engine] Connector {name!r} OK — records_written={records}"
            )

        RefreshRun.objects.filter(pk=run_id).update(
            completed_count=completed,
            records_written=total_records,
        )

    # Mark run complete.
    final_status = RefreshStatus.ERROR if errors else RefreshStatus.SUCCESS
    RefreshRun.objects.filter(pk=run_id).update(
        status=final_status,
        current_connector=None,
        completed_count=total,
        finished_at=timezone.now(),
        error_message="; ".join(errors) if errors else None,
    )

    logger.info(
        f"[sync_engine] sync_page finished — page={page!r} site={site_url!r} "
        f"run_id={run_id} status={final_status} records_written={total_records} "
        f"errors={len(errors)}"
    )

    # Post-sync processing (aggregate rebuild etc.).
    _run_post_sync(site_url, connector_names)

    return {
        "completed": completed,
        "total": total,
        "records_written": total_records,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Public helpers (used by views)
# ---------------------------------------------------------------------------

def get_connector_names_for_page(page: str) -> list[str]:
    """Return the list of connector names active for a given page key."""
    return list(PAGE_CONNECTORS.get(page, []))


def get_all_connector_names() -> list[str]:
    """Return the full list of connector names used in sync_all."""
    return list(ALL_CONNECTORS)
