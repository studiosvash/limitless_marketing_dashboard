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
    UniqueConstraint, Index,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Site(Base):
    """Registry of tracked domains; source of truth for per-domain credentials."""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_url = Column(String(255), nullable=False, unique=True, index=True)
    site_name = Column(String(255), nullable=True)
    gsc_property = Column(String(255), nullable=True)
    ga4_property_id = Column(String(100), nullable=True)
    dataforseo_target_domain = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, server_default=func.now())


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


class KeywordRanking(Base):
    """Daily keyword rankings: GSC engagement + DataForSEO market data."""
    __tablename__ = "keyword_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    keyword = Column(String(500), nullable=False, index=True)
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
    domain_rank = Column(Integer, nullable=True)
    first_seen = Column(Date, nullable=True)
    last_seen = Column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("site_id", "referring_domain", "target_url", name="uq_backlink_site"),
    )


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
    keyword = Column(String(500), nullable=False, index=True)
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
    keyword = Column(String(500), nullable=False, index=True)
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
    keyword = Column(String(500), nullable=False)
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


def init_db(engine: Engine) -> None:
    """Create all analytics tables if they don't exist. Safe to call repeatedly."""
    Base.metadata.create_all(engine)
