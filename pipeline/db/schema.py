"""
pipeline/db/schema.py — SQLAlchemy table definitions for the analytics DB (fusehealth.db).

Source of truth for the analytics schema. Run init_db(engine) to create all tables.
Managed by SQLAlchemy, NOT the Django ORM. Internal/operational state (users, sync
log, refresh runs, insights) lives in Django's django_internal.db instead.

Refinements vs. the Streamlit MVP schema:
  * No data_source columns — demo data is purged and fake data is forbidden, so the
    value was always 'real' (dead column).
  * site_id added to anomalies and comparative_metrics (the platform is per-website).
  * technical_issues has a real upsert key (site_id, url, issue_type) so re-syncs
    update instead of duplicating.
  * users / sync_log / refresh_jobs / insights removed — re-homed to Django.
  * site_id columns hold the site's URL string (= Site.site_url), intentionally NOT an
    integer FK to sites.id. It is the cross-DB join key shared with Django models.
"""
from sqlalchemy import (
    Column, String, Float, Integer, Date, DateTime, Text,
    UniqueConstraint, Index, inspect, text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Site(Base):
    """Registry of tracked domains; source of truth for per-domain credentials."""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_url = Column(String(255), nullable=False, unique=True, index=True)
    site_name = Column(String(255), nullable=True)
    slug = Column(String(100), nullable=True, unique=True, index=True)
    vertical = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True, default="United States")
    gsc_property = Column(String(255), nullable=True)
    ga4_property_id = Column(String(100), nullable=True)
    dataforseo_target_domain = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # --- Tracking preferences (added 2026-07) ---------------------------------------------
    # The three fields Position Tracking's "Tracking area" wizard step and its Edit modal
    # have always collected. Before this they had nowhere to go: the wizard's finish handler
    # never sent them, `sites` had no column for them, and the workspace header printed a
    # hardcoded "Desktop" no matter what the user picked. They are stored here so the header
    # can report the user's actual choice.
    #
    # THEY ARE A STORED PREFERENCE, NOT YET A SYNC PARAMETER. Both SERP connectors
    # (dataforseo_serp.py and dataforseo_serp_competitors.py) still post
    # location_name="United States", language_name="English", device="desktop" as literals,
    # and neither reads this row. Recording what the user chose is honest; claiming it
    # changes what gets fetched would not be. See ensure_site_columns() below for how an
    # existing database acquires these columns.
    search_engine = Column(String(50), nullable=True, default="Google")
    device = Column(String(50), nullable=True, default="Desktop")
    language = Column(String(100), nullable=True, default="English")


class SEODaily(Base):
    """Blended GSC + GA4 daily metrics per site/page/dimensions."""
    __tablename__ = "seo_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    avg_position = Column(Float, default=0.0)
    sessions = Column(Integer, default=0)
    pageviews = Column(Integer, default=0)
    bounce_rate = Column(Float, default=0.0)
    conversions = Column(Integer, default=0)
    users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    country = Column(String(100), nullable=True, index=True)
    device = Column(String(50), nullable=True, index=True)
    landing_page = Column(Text, nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "country", "device", "landing_page",
                         name="uq_seo_daily_date_site_dimensions"),
        Index("ix_seo_daily_site_date", "site_id", "date"),
    )


class SEODailyTotal(Base):
    """The unfiltered per-day Search Console figures — one row per (site, date).

    Why this exists alongside `seo_daily`: that table is stored at
    (date, country, device, page) grain, and Google drops rows below its privacy threshold
    from a dimension-grouped response while still counting them in the unfiltered total. The
    finer the slice, the more it drops, so summing `seo_daily` cannot reproduce what the
    Search Console UI shows. Measured on premierstaff.com for 2026-07-13: the 4-dimension
    breakdown held 55 of 135 clicks (41%) and 9,921 of 12,761 impressions (78%).

    A second, cheap `dimensions=["date"]` call has no such loss — verified equal to the
    no-dimension total on every window tested (135/135, 455/455, 2652/2652, 10594/10594).
    Those figures land here and are what every headline KPI reads, so the dashboard matches
    Search Console exactly. `seo_daily` stays as the drill-down source (top pages, countries,
    devices), where a breakdown that is internally consistent matters more than a total that
    ties out.

    `ctr` and `avg_position` are stored as Google reported them for the day rather than
    recomputed, so a single day needs no arithmetic at all. Across several days, CTR must be
    re-derived as SUM(clicks)/SUM(impressions) and position as the impression-weighted mean —
    averaging the stored per-day values would be wrong. See `query_gsc_totals`.
    """
    __tablename__ = "seo_daily_totals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    avg_position = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("date", "site_id", name="uq_seo_daily_totals_date_site"),
        Index("ix_seo_daily_totals_site_date", "site_id", "date"),
    )


class GA4TrafficSourceDaily(Base):
    """GA4 Traffic by sessionDefaultChannelGroup and sessionSource."""
    __tablename__ = "ga4_traffic_source_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True)
    channel = Column(String(100), nullable=False, index=True)
    source = Column(String(200), nullable=False, index=True)
    sessions = Column(Integer, default=0)
    engaged_sessions = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "channel", "source",
                         name="uq_ga4_traffic_source_date_site_channel_source"),
        Index("ix_ga4_traffic_source_site_date", "site_id", "date"),
    )


class GA4DailyTotal(Base):
    """Session-scoped GA4 figures at (site, date, country) grain — the GA4 counterpart of
    `SEODailyTotal`, and it exists for the same measured reason.

    GA4 sessions are not additive across `pagePath`: one visit that viewed three pages is one
    session but three rows, so summing the (date, country, device, page) breakdown in
    `seo_daily` overstates sessions — measured at 158% of what the GA4 UI reports
    (21,077 vs 13,333 over 2026-06-01..07-27). Grouped by date alone the API returned 13,067
    — within 2% of the UI figure, the residue being GA4's own "(other)" bucketing.

    Country is in the grain rather than a separate table because a session has exactly one
    country, so sessions stay additive when countries are summed — one table serves both the
    headline total (sum over countries) and the top-locations card (group by country), which
    previously summed the page breakdown and inflated every country by its page count.

    `users` is stored as GA4 reported it for that (date, country) and MUST NOT be summed
    across dates or countries — unique users are not additive along either axis (a returning
    visitor is one user in the window, two in the sum). Anything needing a window-level user
    count has to ask GA4 for that window; until then surfaces show None, never a sum.
    """
    __tablename__ = "ga4_daily_totals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=False, default="(not set)")
    sessions = Column(Integer, default=0)
    pageviews = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    users = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "country", name="uq_ga4_daily_totals_date_site_country"),
        Index("ix_ga4_daily_totals_site_date", "site_id", "date"),
    )


class KeywordRanking(Base):
    """Daily keyword rankings: GSC engagement + DataForSEO market data."""
    __tablename__ = "keyword_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    # Text, not String(500). A search query has no 500-character limit, and real GSC data
    # proves it: 115 rows here hold queries up to 1440 chars -- people pasting long
    # AI-assistant-style prompts into Google ("i am a 25-34 year old event planner, ...")
    # and long `-filetype:` operator strings. SQLite is dynamically typed and stored them
    # happily; PostgreSQL enforces the declared width and aborted the 2026-07-27 migration
    # with StringDataRightTruncation partway through this table.
    #
    # Every `keyword` column in this file was widened at the same time (competitor_keyword_
    # rankings, ai_keyword_data, saved_keywords, keyword_opportunities, and
    # ad_search_terms.matched_keyword) -- they hold the same kind of value, so each was the
    # same crash waiting for its turn. Truncating to fit would have silently corrupted real
    # queries, which this codebase does not do.
    keyword = Column(Text, nullable=False, index=True)
    position = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    clicks = Column(Integer, nullable=True, default=0)
    impressions = Column(Integer, nullable=True, default=0)
    ctr = Column(Float, nullable=True, default=0.0)
    search_volume = Column(Integer, nullable=True)
    keyword_difficulty = Column(Float, nullable=True)
    cpc = Column(Float, nullable=True)
    intent = Column(String(100), nullable=True, index=True)
    trend = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "keyword", name="uq_keyword_date_site"),
        Index("ix_keyword_site_date", "site_id", "date"),
    )


class Page(Base):
    """Page inventory from CMS sources, enriched with GSC metrics."""
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    url = Column(Text, nullable=False, index=True)
    cms_type = Column(String(50), nullable=True)
    title = Column(Text, nullable=True)
    sessions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    issues = Column(Text, nullable=True)
    author = Column(String(200), nullable=True, index=True)
    meta_title = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    publish_date = Column(Date, nullable=True, index=True)
    last_modified = Column(Date, nullable=True)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "url", name="uq_pages_site_url"),
    )


class AdMetricDaily(Base):
    """Daily paid-ad metrics across platforms (google|meta|linkedin)."""
    __tablename__ = "ad_metrics_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    platform = Column(String(50), nullable=False, index=True)
    campaign = Column(String(500), nullable=True)
    campaign_id = Column(String(100), nullable=True)
    spend = Column(Float, default=0.0)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    roas = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "platform", "campaign",
                         name="uq_ad_metrics_date_site_platform_campaign"),
        Index("ix_ad_metrics_site_date", "site_id", "date"),
    )


class Backlink(Base):
    """Backlinks from DataForSEO Backlinks API."""
    __tablename__ = "backlinks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    referring_domain = Column(String(500), nullable=False, index=True)
    target_url = Column(Text, nullable=False)
    anchor = Column(Text, nullable=True)
    status = Column(String(20), default="live")
    dofollow = Column(Integer, default=1)
    # The referring DOMAIN's authority (DataForSEO `domain_from_rank`), 0-1000. Was populated
    # from `rank` -- a different, per-BACKLINK score -- which is why unrelated domains showed
    # identical values here; see ensure_backlinks_columns() for the added columns below.
    domain_rank = Column(Integer, nullable=True)
    first_seen = Column(Date, nullable=True)
    last_seen = Column(Date, nullable=True)
    # The exact page that carries the link (DataForSEO `url_from`). Without this the Backlinks
    # table could only show the referring DOMAIN, never a link to the actual page.
    url_from = Column(Text, nullable=True)
    # The referring PAGE's own authority (DataForSEO `page_from_rank`), 0-1000 -- distinct from
    # `domain_rank` above, which is domain-wide.
    page_from_rank = Column(Integer, nullable=True)
    # Per-backlink spam score (DataForSEO `backlink_spam_score`), 0-100.
    spam_score = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("site_id", "referring_domain", "target_url", name="uq_backlink_site"),
    )


class BacklinksSnapshot(Base):
    """One stored Backlinks-page payload per site (DB-first cache of the DataForSEO Backlinks
    aggregates: summary, referring domains, anchors, new/lost history). The page reads the
    latest snapshot; a Refresh re-fetches and overwrites it. Stored as a JSON blob because the
    data is display-only (never cross-queried), which keeps this to one table instead of four."""
    __tablename__ = "backlinks_snapshot"

    site_id = Column(String(255), primary_key=True, default="")
    fetched_at = Column(DateTime, nullable=False)
    payload = Column(Text, nullable=False)  # JSON string of the SPA Backlinks `data` shape


class CompetitorVisibility(Base):
    """Competitor domain search visibility over time."""
    __tablename__ = "competitor_visibility"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    competitor_domain = Column(String(255), nullable=False, index=True)
    visibility_pct = Column(Float, nullable=True)
    shared_keywords = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "competitor_domain", name="uq_competitor_date_site_domain"),
    )


class CompetitorDomain(Base):
    """Auto-discovered competitor domains from DataForSEO Labs."""
    __tablename__ = "competitor_domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    competitor_domain = Column(String(255), nullable=False, index=True)
    intersections = Column(Integer, default=0)
    full_domain_metrics_organic_count = Column(Integer, default=0)
    avg_position = Column(Float, nullable=True)
    median_position = Column(Float, nullable=True)
    etv = Column(Float, nullable=True)
    last_fetched = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "competitor_domain", name="uq_competitor_domain_site"),
    )


class TechnicalIssue(Base):
    """On-page technical SEO issues from DataForSEO On-Page API."""
    __tablename__ = "technical_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    url = Column(Text, nullable=False, index=True)
    issue_type = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    detected_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "url", "issue_type", name="uq_technical_issue_site_url_type"),
    )


class PageSpeed(Base):
    """PageSpeed Insights / Lighthouse scores + Core Web Vitals per URL."""
    __tablename__ = "page_speed"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    url = Column(Text, nullable=False, index=True)
    strategy = Column(String(20), nullable=False)
    performance_score = Column(Integer, nullable=True)
    seo_score = Column(Integer, nullable=True)
    accessibility_score = Column(Integer, nullable=True)
    best_practices_score = Column(Integer, nullable=True)
    lcp_ms = Column(Float, nullable=True)
    cls = Column(Float, nullable=True)
    inp_ms = Column(Float, nullable=True)
    fcp_ms = Column(Float, nullable=True)
    ttfb_ms = Column(Float, nullable=True)
    si_ms = Column(Float, nullable=True)
    # --- Total Blocking Time (added 2026-07) ------------------------------------------------
    # Lighthouse returns `audits["total-blocking-time"].numericValue` (milliseconds) on EVERY
    # PSI run. It had nowhere to go, so the Site Audit page's TBT tile had no source.
    #
    # `lighthouse_audits` is NOT a substitute and was never one: that blob stores only the
    # audits that FAILED (`score < 1 or savings > 0`), so on the live database TBT was present
    # for 4 of 75 mobile rows — and only for pages that scored badly. A p75 over that subset is
    # a p75 of "the slow pages", not of the site.
    #
    # `inp_ms` is NOT a substitute either: INP is a different metric (a field metric a lab
    # Lighthouse run never returns), and it is NULL on all 150 stored rows.
    tbt_ms = Column(Float, nullable=True)
    lighthouse_audits = Column(Text, nullable=True)
    last_checked = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "url", "strategy", name="uq_pagespeed_site_url_strategy"),
    )


class IndexingStatus(Base):
    """URL Inspection API results per URL."""
    __tablename__ = "indexing_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    url = Column(Text, nullable=False, index=True)
    verdict = Column(String(20), nullable=True)
    coverage_state = Column(String(100), nullable=True)
    indexing_state = Column(String(50), nullable=True)
    last_crawl_time = Column(DateTime, nullable=True)
    crawl_status = Column(String(50), nullable=True)
    robots_txt_state = Column(String(50), nullable=True)
    mobile_usability = Column(String(20), nullable=True)
    rich_results_status = Column(String(50), nullable=True)
    last_checked = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "url", name="uq_indexing_site_url"),
    )


class SEOAggregate(Base):
    """Pre-rolled SEO + GA4 metrics per (site, period_type, period_start)."""
    __tablename__ = "seo_aggregates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    period_type = Column(String(10), nullable=False, index=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    avg_position = Column(Float, default=0.0)
    sessions = Column(Integer, default=0)
    pageviews = Column(Integer, default=0)
    users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    returning_users = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    rebuilt_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "period_type", "period_start", name="uq_seo_aggregate_site_period"),
    )


class AISummary(Base):
    """Weekly AI-generated intelligence summary (per site)."""
    __tablename__ = "ai_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    summary_text = Column(Text, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())
    model_used = Column(String(100), nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("week_start", "site_id", name="uq_ai_summary_week_site"),
    )


class Anomaly(Base):
    """Detected unusual patterns in metrics (reactive: what already changed)."""
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    metric_type = Column(String(50), nullable=False, index=True)
    actual_value = Column(Float, nullable=False)
    baseline_value = Column(Float, nullable=False)
    deviation_pct = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    is_acknowledged = Column(Integer, default=0)
    detected_at = Column(DateTime, server_default=func.now(), index=True)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "metric_type", name="uq_anomaly_date_site_metric"),
    )


class ComparativeMetrics(Base):
    """Week-over-week / month-over-month comparative analysis (per site)."""
    __tablename__ = "comparative_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    metric_type = Column(String(50), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)
    current_week_value = Column(Float, nullable=False)
    previous_week_value = Column(Float, nullable=False)
    wow_change_pct = Column(Float, nullable=True)
    mom_change_pct = Column(Float, nullable=True)
    four_week_avg = Column(Float, nullable=True)
    twelve_week_avg = Column(Float, nullable=True)
    trend_direction = Column(String(20), nullable=True)
    data_freshness = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "metric_type", "week_start", name="uq_comparative_site_metric_week"),
    )


# ─────────────────────────────────────────────
# Competitor rank tracking + AI keyword data (additive — 2026-06-15)
# New capabilities; do not alter the existing competitor/keyword tables above.
# ─────────────────────────────────────────────


class CompetitorKeywordRanking(Base):
    """
    Per-keyword competitor positions captured from the live SERP — the data
    behind the SEMrush-style Positioning grid (your rank vs each competitor's,
    tracked over time). Mirrors KeywordRanking so the same date-over-date diff
    logic applies. Your own domain lives in keyword_rankings; this table holds
    the competitor domains (and may also hold your own for a uniform query).
    """
    __tablename__ = "competitor_keyword_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    keyword = Column(Text, nullable=False, index=True)
    competitor_domain = Column(String(255), nullable=False, index=True)
    position = Column(Integer, nullable=True)        # rank_absolute; NULL = not in captured depth
    url = Column(Text, nullable=True)                # the competitor's ranking URL
    last_fetched = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("date", "site_id", "keyword", "competitor_domain",
                         name="uq_comp_kw_rank"),
        Index("ix_comp_kw_rank_site_date", "site_id", "date"),
    )


class TrackedCompetitor(Base):
    """
    The competitor domains a site explicitly tracks as grid columns. When empty
    for a site, the grid auto-seeds from competitor_domains (top by intersections).
    This is the editable override layer; the auto-discovery table is untouched.
    """
    __tablename__ = "tracked_competitors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    competitor_domain = Column(String(255), nullable=False, index=True)
    added_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "competitor_domain", name="uq_tracked_competitor_site"),
    )


class AIKeywordData(Base):
    """
    AI-search keyword data from DataForSEO's AI Optimization API — how often
    people ask AI-style questions related to the site's tracked keywords. A
    research input surfaced on the Keywords page, not a daily rank tracker.
    """
    __tablename__ = "ai_keyword_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    keyword = Column(Text, nullable=False, index=True)
    ai_search_volume = Column(Integer, nullable=True)        # current AI search volume rate
    prev_ai_search_volume = Column(Integer, nullable=True)   # previous month (for trend arrow)
    search_volume = Column(Integer, nullable=True)           # classic volume, enriched for context
    intent = Column(String(100), nullable=True, index=True)
    trend = Column(Text, nullable=True)                      # JSON: 12-month ai_monthly_searches array
    last_fetched = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("date", "site_id", "keyword", name="uq_ai_keyword_date_site"),
        Index("ix_ai_keyword_site_date", "site_id", "date"),
    )


class LLMMentionMetric(Base):
    """Weekly LLM-mention aggregate for one subject on one platform.

    Written by `dataforseo_llm_mentions` from DataForSEO's LLM Mentions API. One row per
    (site, week, subject domain, platform). `subject_type` distinguishes the project itself
    from the competitors it tracks from domains merely DISCOVERED in the same answers -- the
    grain is identical, so one table serves both the Share-of-Voice list and the
    "Domains Dominating AI Answers" list, and "which new domain is rising?" stays a
    single-table query.

    Weekly rather than daily because the API returns current state with no history: the
    snapshot IS the history, and it cannot be backfilled later.
    """
    __tablename__ = "llm_mention_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    week_start = Column(Date, nullable=False, index=True)   # Monday of the ISO week, UTC
    subject_domain = Column(String(255), nullable=False, index=True)
    subject_type = Column(String(20), nullable=False, default="discovered")  # you|competitor|discovered
    platform = Column(String(20), nullable=False, default="google")          # google|chat_gpt
    mentions = Column(Integer, nullable=False, default=0)
    ai_search_volume = Column(Integer, nullable=False, default=0)
    last_fetched = Column(DateTime, server_default=func.now())

    # Every conflict-target column is NOT NULL on purpose: Postgres does not treat NULL = NULL
    # as a conflict, so a null key would bypass ON CONFLICT and duplicate on every sync.
    __table_args__ = (
        UniqueConstraint("site_id", "week_start", "subject_domain", "platform",
                         name="uq_llm_mention_week"),
        Index("ix_llm_mention_site_week", "site_id", "week_start"),
    )


class LLMCitedPage(Base):
    """One of the project's own URLs that AI answers cited, in a given week.

    Only URLs on the project's own host are stored. The API's top_pages response also returns
    co-occurring pages from OTHER domains (a call for driphydration.com returns perfectb.com
    URLs), which would be wrong under a heading that says "Your Most-Cited Pages".
    """
    __tablename__ = "llm_cited_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    week_start = Column(Date, nullable=False, index=True)
    url = Column(Text, nullable=False, index=True)
    mentions = Column(Integer, nullable=False, default=0)
    ai_search_volume = Column(Integer, nullable=False, default=0)
    platforms = Column(Text, nullable=True)   # JSON list, e.g. ["google", "chat_gpt"]
    last_fetched = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "week_start", "url", name="uq_llm_cited_page_week"),
        Index("ix_llm_cited_page_site_week", "site_id", "week_start"),
    )


class SavedKeyword(Base):
    """
    The site's TRACKED keyword list — keywords an admin explicitly bookmarked from the
    Keyword Explorer ("Track"). This is the dashboard-managed source of truth that the paid
    per-keyword connectors read (SERP position tracking, AI keyword volume) via
    pipeline.utils.keywords.load_tracked_keywords, so the admin controls the tracking list —
    and therefore the API spend — entirely from the UI, with no file to edit.

    Distinct from keyword_rankings, which is the *synced result* data (what the site actually
    ranks for, discovered from GSC). Site-scoped, shared by the team.
    """
    __tablename__ = "saved_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    keyword = Column(Text, nullable=False, index=True)
    location = Column(String(255), nullable=False, default="United States")
    search_volume = Column(Integer, nullable=True)
    keyword_difficulty = Column(Float, nullable=True)
    cpc = Column(Float, nullable=True)
    competition = Column(String(50), nullable=True)        # competition_level label (LOW/MEDIUM/HIGH)
    intent = Column(String(100), nullable=True)
    serp_features = Column(Text, nullable=True)            # comma-joined serp_item_types
    saved_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "keyword", "location", name="uq_saved_keyword_site_kw_loc"),
        Index("ix_saved_keyword_site", "site_id"),
    )


# ─────────────────────────────────────────────
# Prediction & intelligence layer
# Not filled by any API — a prediction service reads the raw/aggregate tables,
# computes, and writes here. This is what makes FuseHealth a prediction platform.
# ─────────────────────────────────────────────


class MetricForecast(Base):
    """
    Predicted future value of a metric with a confidence band. actual_value and
    error_pct are backfilled once target_date passes, so the platform self-tracks
    how accurate its forecasts were.
    """
    __tablename__ = "metric_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)   # clicks|impressions|sessions|avg_position|...
    period_type = Column(String(10), nullable=False)   # daily|weekly|monthly
    target_date = Column(Date, nullable=False)
    predicted_value = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    actual_value = Column(Float, nullable=True)         # backfilled when target_date arrives
    error_pct = Column(Float, nullable=True)            # |actual - predicted| / actual
    generated_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "metric_type", "period_type", "target_date", "model_name",
                         name="uq_forecast_site_metric_period_date_model"),
        Index("ix_forecast_site_metric_date", "site_id", "metric_type", "target_date"),
    )


class KeywordOpportunity(Base):
    """Scored 'what to target next' keywords. Upsert latest snapshot per (site, keyword)."""
    __tablename__ = "keyword_opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    keyword = Column(Text, nullable=False)
    current_position = Column(Integer, nullable=True)
    search_volume = Column(Integer, nullable=True)
    keyword_difficulty = Column(Float, nullable=True)
    cpc = Column(Float, nullable=True)
    opportunity_score = Column(Float, nullable=False, default=0.0)   # 0-100
    opportunity_type = Column(String(50), nullable=True)            # quick_win|striking_distance|content_gap|rising
    estimated_traffic_gain = Column(Float, nullable=True)
    rationale = Column(Text, nullable=True)
    computed_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "keyword", name="uq_opportunity_site_keyword"),
        Index("ix_opportunity_site_score", "site_id", "opportunity_score"),
    )


class RiskSignal(Base):
    """
    Proactive early warnings & opportunities at entity level (what's coming) —
    complements Anomaly (what already changed).
    """
    __tablename__ = "risk_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)   # ranking_drop_risk|traffic_decline|indexing_risk|opportunity
    entity_type = Column(String(20), nullable=False)   # page|keyword|site
    entity_ref = Column(Text, nullable=False)          # URL or keyword
    severity = Column(String(20), nullable=True)       # low|medium|high
    confidence = Column(Float, nullable=True)          # 0-1
    predicted_impact = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    status = Column(String(20), default="open", index=True)  # open|acknowledged|resolved
    detected_at = Column(DateTime, server_default=func.now())
    expires_at = Column(Date, nullable=True)

    __table_args__ = (
        Index("ix_risk_site_status", "site_id", "status"),
        Index("ix_risk_signal_type", "signal_type"),
    )


# ─────────────────────────────────────────────
# History & cost tables (2026-07)
# Added because four screens were fully built over data that was never stored:
# Site Audit's Compare/Progress tabs, Ads' Search Terms and Attribution tabs, and
# Settings' cost figures. Each of those previously rendered fabricated or empty data.
# ─────────────────────────────────────────────


class AuditSnapshot(Base):
    """One row per completed Site Audit crawl — the history the Compare Crawls and Progress
    sub-tabs read. Those tabs were fully built but permanently empty because nothing recorded
    a crawl's outcome; `build_site_audit_response` returned `snapshots: []` unconditionally.

    `by_check` is a JSON map of {issue_type: count} so Compare Crawls can diff per check
    without a second table. Keyed on the DATE, not a timestamp: two crawls on the same day
    overwrite rather than producing a misleading double point on the trend line.
    """
    __tablename__ = "audit_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    captured_at = Column(Date, nullable=False, index=True)
    score = Column(Integer, nullable=True)
    errors = Column(Integer, default=0)
    warnings = Column(Integer, default=0)
    notices = Column(Integer, default=0)
    pages_crawled = Column(Integer, default=0)
    by_check = Column(Text, nullable=True)          # JSON: {issue_type: count}
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "captured_at", name="uq_audit_snapshot_site_date"),
        Index("ix_audit_snapshot_site_date", "site_id", "captured_at"),
    )


class AdSearchTerm(Base):
    """Google Ads `search_term_view` rows — the real queries that triggered an ad.

    The Search Terms page (filters, bulk negatives, promote-to-organic) was fully built against
    a response key that was hardcoded to `[]` because no table existed. The negative-keyword and
    promote endpoints already work; they simply had nothing to act on.
    """
    __tablename__ = "ad_search_terms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    term = Column(String(500), nullable=False, index=True)
    matched_keyword = Column(Text, nullable=True)
    match_type = Column(String(20), nullable=True)      # exact | phrase | broad
    campaign = Column(String(500), nullable=True)
    campaign_id = Column(String(100), nullable=True, index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    conversions = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "term", "campaign_id",
                         name="uq_ad_search_term_date_site_term_campaign"),
        Index("ix_ad_search_term_site_date", "site_id", "date"),
    )


class GA4CampaignDaily(Base):
    """GA4 key events and revenue broken down by campaign — the GA4 half of the Attribution
    comparison. Google Ads reports its own last-click attribution; GA4 attributes across all
    channels, so the two never agree. Showing them side by side is the whole point of that page,
    and it needs both halves stored per campaign, which nothing did before.
    """
    __tablename__ = "ga4_campaign_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    campaign = Column(String(500), nullable=False, index=True)
    sessions = Column(Integer, default=0)
    key_events = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("date", "site_id", "campaign",
                         name="uq_ga4_campaign_date_site_campaign"),
        Index("ix_ga4_campaign_site_date", "site_id", "date"),
    )


class ConnectorCost(Base):
    """What each connector run actually cost. Every DataForSEO response already carries a real
    `task.cost` and every one of them was being discarded, which is why Settings' Usage & Budget
    tab could only show honest zeros and the budget cap could not be enforced.

    One row per (connector, run). `units` is whatever the connector meters — keywords looked up,
    pages crawled — so cost-per-unit is derivable without a second table.
    """
    __tablename__ = "connector_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    connector = Column(String(100), nullable=False, index=True)
    run_at = Column(DateTime, nullable=False, index=True)
    cost = Column(Float, default=0.0)
    units = Column(Integer, nullable=True)
    currency = Column(String(10), default="USD")
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_connector_cost_site_run", "site_id", "run_at"),
    )


class PageCrawlMeta(Base):
    """Per-page link and content counts measured by the DataForSEO OnPage crawl.

    `/v3/on_page/pages` returns these on every crawled page and the connector threw the whole
    `items[].meta` object away, keeping only `items[].checks`. That is why the Site Audit page
    had no honest source for in-links, internal links or word count — and why a previous
    version faked them from `performance_score * 0.4` and `fcp_ms * 1.5`.

    WHY A SEPARATE TABLE RATHER THAN COLUMNS ON `pages`:
      * `pages` is the GSC/CMS *inventory* (2 144 rows on the live DB), written by `gsc_pages`,
        `sitemap` and the CMS connectors. The OnPage crawl covers a different, smaller URL set,
        so upserting into `pages` would silently inject crawl-discovered URLs into the
        inventory that `pagespeed._get_top_pages` and the Pages page both sample from.
      * These are crawl-scoped measurements with their own freshness (`crawled_at`), not
        inventory attributes. Keeping them apart means "we have not crawled this page" is
        representable as a missing row instead of four NULL columns that read as zeros.
      * No writer coupling: `upsert_pages` derives its update set from the incoming record's
        keys, so a shared table would work, but two connectors owning disjoint column groups
        of one row is exactly the coupling the one-concern-per-file rule exists to avoid.

    Nullable everywhere on purpose: OnPage omits a field it could not measure, and a missing
    measurement must stay NULL so the payload can report None rather than a fabricated 0.
    """
    __tablename__ = "page_crawl_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    url = Column(Text, nullable=False, index=True)
    internal_links_count = Column(Integer, nullable=True)   # meta.internal_links_count
    external_links_count = Column(Integer, nullable=True)   # meta.external_links_count
    inbound_links_count = Column(Integer, nullable=True)    # meta.inbound_links_count
    word_count = Column(Integer, nullable=True)             # meta.content.plain_text_word_count
    crawled_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "url", name="uq_page_crawl_meta_site_url"),
    )


# ─────────────────────────────────────────────
# Columns added to an ALREADY-SHIPPED table
# ─────────────────────────────────────────────
#
# `Base.metadata.create_all` only creates MISSING TABLES. It will never add a column to a
# table that already exists, so every column added to `sites` after the first release needs
# an explicit ALTER against live databases.
#
# WHY THIS IS NOT A COPY OF apps/sync/management/commands/add_project_fields.py: that command
# guards each ALTER with `PRAGMA table_info(sites)`, which is SQLite-only syntax — Postgres
# rejects it as a syntax error, so the command cannot even be run there, and this project now
# supports both backends (config/settings/base.py picks Postgres when POSTGRES_DB is set).
# `sqlalchemy.inspect()` asks the same question through whichever dialect is connected, and
# `ALTER TABLE t ADD COLUMN c <type> DEFAULT '<v>'` is accepted verbatim by SQLite 3.2+ and
# PostgreSQL 11+, backfilling existing rows with the default in that one statement on both.
#
# (name, SQL type, default) — every value below is a module constant. Nothing user-supplied
# is ever interpolated into the DDL string. `default=None` emits no DEFAULT clause, which is
# what a nullable measurement wants: an existing row that was never measured must read NULL,
# never a backfilled number that would look like a real reading.
_SITES_ADDED_COLUMNS = (
    ("search_engine", "VARCHAR(50)", "Google"),
    ("device", "VARCHAR(50)", "Desktop"),
    ("language", "VARCHAR(100)", "English"),
)

# `page_speed.tbt_ms` — see the PageSpeed model for why this is a real column and not a value
# dug out of the `lighthouse_audits` blob.
_PAGE_SPEED_ADDED_COLUMNS = (
    ("tbt_ms", "FLOAT", None),
)

# `backlinks.url_from` / `page_from_rank` / `spam_score` — DataForSEO returns all three on
# every backlink row (see pipeline/connectors/dataforseo_backlinks.py), but the original table
# had no columns for them, so they were fetched and then discarded. Nullable, no default: a
# backlink synced before this migration has genuinely unknown values, not zero.
_BACKLINKS_ADDED_COLUMNS = (
    ("url_from", "TEXT", None),
    ("page_from_rank", "INTEGER", None),
    ("spam_score", "INTEGER", None),
)


def _alter_missing_columns(conn, table: str, specs) -> list[str]:
    """Add each missing column of `table` on the given Connection. Returns the names added.

    `sqlalchemy.inspect()` asks "does this column exist?" through whichever dialect is
    connected, unlike the SQLite-only `PRAGMA table_info` the legacy management command uses,
    and `ALTER TABLE t ADD COLUMN c <type> [DEFAULT '<v>']` is accepted verbatim by SQLite 3.2+
    and PostgreSQL 11+.
    """
    inspector = inspect(conn)
    if not inspector.has_table(table):
        return []  # brand-new database: create_all() has already built it in full
    existing = {c["name"] for c in inspector.get_columns(table)}
    added = []
    for name, sql_type, default in specs:
        if name in existing:
            continue
        suffix = "" if default is None else f" DEFAULT '{default}'"
        conn.execute(text(f"""ALTER TABLE {table} ADD COLUMN "{name}" {sql_type}{suffix}"""))
        added.append(name)
    return added


def _run_alter(session_or_engine, table: str, specs) -> list[str]:
    """Apply `_alter_missing_columns` to a Session (joining its transaction) or an Engine."""
    if isinstance(session_or_engine, Session):
        return _alter_missing_columns(session_or_engine.connection(), table, specs)
    with session_or_engine.begin() as conn:
        return _alter_missing_columns(conn, table, specs)


def ensure_site_columns(session_or_engine) -> list[str]:
    """Bring an existing `sites` table up to date with the Site model. Idempotent.

    Safe to call on every backend and on a database that is already current (it inspects
    first and issues nothing when there is nothing to add). Accepts a Session (uses its
    connection, so the ALTER joins the caller's transaction) or an Engine.

    Returns the list of column names actually added, so callers can log a real event
    instead of announcing work that did not happen.
    """
    return _run_alter(session_or_engine, "sites", _SITES_ADDED_COLUMNS)


def ensure_page_speed_columns(session_or_engine) -> list[str]:
    """Bring an existing `page_speed` table up to date with the PageSpeed model. Idempotent.

    Same contract as `ensure_site_columns`, and needed for the same reason: SQLAlchemy selects
    every mapped column, so the FIRST `select(PageSpeed)` against a database created before
    `tbt_ms` existed fails with "no such column" — the read breaks before any write does.

    Callers: `init_db` (the migration entry point), `writer.upsert_page_speed` (every sync) and
    `site_audit_service` (every Site Audit page load). Stated limit, exactly as
    `site_service._ensure_columns` states its own: a process whose very first PageSpeed query
    comes from somewhere else — `overview_service`, `technical_issues_service` — still hits the
    missing column until one of those three paths has run once. Any `init_db()` call closes
    that window deterministically on both backends.
    """
    return _run_alter(session_or_engine, "page_speed", _PAGE_SPEED_ADDED_COLUMNS)


def ensure_backlinks_columns(session_or_engine) -> list[str]:
    """Bring an existing `backlinks` table up to date with the Backlink model. Idempotent.

    Same contract as `ensure_site_columns`/`ensure_page_speed_columns`: `select(Backlink)`
    against a database created before `url_from`/`page_from_rank`/`spam_score` existed fails
    with "no such column" otherwise.
    """
    return _run_alter(session_or_engine, "backlinks", _BACKLINKS_ADDED_COLUMNS)


def init_db(engine: Engine) -> None:
    """Create all analytics tables if they don't exist, then reconcile columns added later.

    Safe to call repeatedly. The reconcile steps are what make this usable as a migration entry
    point on an existing database: create_all cannot add a column, the ensure_* helpers can.
    """
    Base.metadata.create_all(engine)
    ensure_site_columns(engine)
    ensure_page_speed_columns(engine)
    ensure_backlinks_columns(engine)
