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
import logging

from sqlalchemy import (
    Column, String, Float, Integer, Date, DateTime, Text,
    UniqueConstraint, Index, inspect, text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

Base = declarative_base()

# The location a row belongs to when nothing more specific is known. Matches `Site.location`'s
# and `SavedKeyword.location`'s existing default, and it is the honest backfill value for rows
# captured before location became part of their identity: every one of those was fetched with a
# hardcoded `location_name="United States"`, so labelling them "United States" records what
# actually happened rather than guessing.
DEFAULT_LOCATION = "United States"

# `saved_keywords.site_pk` for a row whose `site_id` matches no `sites` row at all — an old
# site_url spelling (see pipeline/utils/site_ids). 0, not NULL: the column is part of a unique
# key and Postgres does not treat NULL = NULL as a conflict, so a nullable key column would
# bypass ON CONFLICT and duplicate the row on every save (skills.md §9).
UNOWNED_SITE_PK = 0


class Site(Base):
    """Registry of tracked domains; source of truth for per-domain credentials."""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # NOT unique: Position Tracking's wizard allows registering the same domain as a second,
    # independent project (add_site(..., allow_duplicate=True)) so a team can run two tracking
    # configurations against one site. Every other creation path (topbar "+", Settings) still
    # blocks duplicates at the add_site() level -- this column-level constraint would block
    # both, so the guard has to live in application code instead. See ensure_site_url_not_unique
    # below for reconciling a database created before this change.
    site_url = Column(String(255), nullable=False, index=True)
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
    # STILL A STORED PREFERENCE, NOT A SYNC PARAMETER — for these three. Both SERP connectors
    # post language_name="English" and device="desktop" as literals and read neither column.
    # Recording what the user chose is honest; claiming it changes what gets fetched would not
    # be. See ensure_site_columns() below for how an existing database acquires them.
    #
    # `location` (declared above) IS a sync parameter as of 2026-08-06 and is no longer
    # covered by the paragraph above: both SERP connectors resolve it per project via
    # `site_service.resolve_tracking_location` and send it as `location_name`, and every row
    # they write is stamped with it. Until then they posted a literal "United States", so a
    # project configured for Las Vegas was measured against the national SERP — see
    # KeywordRanking.location for the full account of what that broke.
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
    # The tracking location this rank was MEASURED IN — part of the identity of the row, not a
    # label on it. A position is meaningless without it: "event staffing" sits at #25 nationally
    # and somewhere else entirely in a Las Vegas SERP.
    #
    # This column is also what separates two PROJECTS that track the same domain. Position
    # Tracking's wizard registers the same domain repeatedly (add_site(allow_duplicate=True)),
    # so "Premierstaff NY" and "Premierstaff Las Vegas" are distinct `sites` rows with distinct
    # slugs but the SAME site_url — and site_url is the analytics join key. Before this column
    # existed the unique key was (date, site_id, keyword), so every city project wrote to and
    # read from ONE set of rows: six projects showed one identical dataset (same visibility %,
    # same keyword count, same up/down counts), which is exactly the bug this fixes.
    #
    # Two projects on the same domain AND the same location still share rows, deliberately —
    # they are tracking the identical thing, so one fetch serving both is correct, not a
    # collision.
    #
    # Stored in the SPA's display form ("United States - Las Vegas, NV"), the same form
    # `sites.location` holds; the DataForSEO wire form is produced at the connector edge by
    # `normalize_location_name`. Keeping one form in the database means a read filter can
    # compare against `sites.location` directly.
    location = Column(String(255), nullable=False, index=True, default=DEFAULT_LOCATION)
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

    # THE DATE A RANK CONNECTOR ACTUALLY LOOKED. Written only by connectors that inspect a
    # SERP — `dataforseo_serp` and `gsc_keywords` — and never by `dataforseo_keywords`, which
    # only prices a keyword.
    #
    # It exists because `position IS NULL` means two completely different things and this table
    # could not tell them apart:
    #
    #   "nobody has ever checked this keyword"        -> genuinely unmeasured
    #   "checked, and the domain is not in the top 30" -> a real, measured result
    #
    # Both wrote `position: NULL`, so the Positioning page filed a keyword the user had just
    # paid to measure back into "Newly Added Keywords — Not Tracked Yet", under copy reading
    # "no captured position yet" — telling them the refresh they had watched succeed had not
    # happened. `keywords_needing_backfill` had the same problem and had to guess from
    # `position IS NOT NULL OR impressions > 0`, which re-bought every genuinely-unranked
    # keyword on every incremental sync.
    #
    # NULL therefore means "never rank-checked", and that is now a fact rather than an
    # inference. Rows written before this column existed are NULL — honest, since nothing
    # recorded whether they were checked; the next sync stamps them.
    rank_checked_at = Column(Date, nullable=True)

    __table_args__ = (
        # `location` joined this key on 2026-08-06 — see the column comment. The constraint was
        # RENAMED at the same time on purpose: the name is how `ensure_ranking_location_keys()`
        # tells a reconciled database from one still carrying the 3-column key.
        UniqueConstraint("date", "site_id", "keyword", "location",
                         name="uq_keyword_date_site_loc"),
        Index("ix_keyword_site_date", "site_id", "date"),
        Index("ix_keyword_site_loc_date", "site_id", "location", "date"),
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
    # Same role as KeywordRanking.location — the SERP this position was read from. Without it
    # the NY project's competitor grid and the Las Vegas project's would overwrite each other.
    location = Column(String(255), nullable=False, index=True, default=DEFAULT_LOCATION)
    position = Column(Integer, nullable=True)        # rank_absolute; NULL = not in captured depth
    url = Column(Text, nullable=True)                # the competitor's ranking URL
    last_fetched = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("date", "site_id", "keyword", "competitor_domain", "location",
                         name="uq_comp_kw_rank_loc"),
        Index("ix_comp_kw_rank_site_date", "site_id", "date"),
        Index("ix_comp_kw_rank_site_loc_date", "site_id", "location", "date"),
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
    # The owning PROJECT, exactly as on SavedKeyword and for the same reason: one domain can be
    # registered as several projects (`add_site(allow_duplicate=True)`), so `site_id` cannot
    # identify whose override this is. Keyed on `site_id` alone, one project's competitor edit
    # DELETED every sibling's list and the grid read back whichever set happened to be stored.
    # `UNOWNED_SITE_PK` (0) is the pre-migration value `_backfill_tracked_competitor_projects`
    # replaces; a DEFAULT is required because the column is part of a unique key.
    site_pk = Column(Integer, nullable=False, index=True, default=UNOWNED_SITE_PK,
                     server_default=str(UNOWNED_SITE_PK))
    competitor_domain = Column(String(255), nullable=False, index=True)
    added_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        # RENAMED from uq_tracked_competitor_site: `_swap_unique_constraint` uses the name to
        # decide whether a database has been reconciled onto the per-project key.
        UniqueConstraint("site_pk", "competitor_domain", name="uq_tracked_competitor_project"),
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
    ranks for, discovered from GSC). PROJECT-scoped (see `site_pk`), shared by the team.
    """
    __tablename__ = "saved_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")

    # THE OWNING PROJECT — `sites.id`, and the only column that identifies one.
    #
    # `site_id` cannot: Position Tracking registers one domain as several projects
    # (`add_site(allow_duplicate=True)`), and every one of them carries the same `site_url`. A
    # read keyed on `site_id` alone therefore hands a brand-new project every keyword its
    # siblings already track — which is exactly what put 28 keywords the user had never chosen
    # into a freshly created project's "Newly Added Keywords" card on the Positioning page.
    #
    # `location` was the first attempt at a discriminator (2026-08-06) and is NOT one. It is a
    # tracking preference, not an identity: nothing stops two projects on a domain from tracking
    # the same market, and the wizard defaults every project to "United States", so the common
    # case is siblings that share it. It stays as the market a keyword's metrics were researched
    # in — see `location` below — and is no longer asked to say who owns the row.
    #
    # `UNOWNED_SITE_PK` (0) means no project could be resolved for the row's `site_id`. Those
    # rows are deliberately invisible to every project and are reported by
    # `manage.py adopt_orphan_saved_keywords`.
    site_pk = Column(Integer, nullable=False, index=True, default=UNOWNED_SITE_PK,
                     server_default=str(UNOWNED_SITE_PK))

    keyword = Column(Text, nullable=False, index=True)
    location = Column(String(255), nullable=False, default="United States")
    search_volume = Column(Integer, nullable=True)
    keyword_difficulty = Column(Float, nullable=True)
    cpc = Column(Float, nullable=True)
    competition = Column(String(50), nullable=True)        # competition_level label (LOW/MEDIUM/HIGH)
    intent = Column(String(100), nullable=True)
    serp_features = Column(Text, nullable=True)            # comma-joined serp_item_types
    saved_at = Column(DateTime, server_default=func.now())

    # `site_pk` is PREPENDED to the old (site_id, keyword, location) key rather than replacing
    # part of it. That is deliberate and the reason the migration is safe: adding a column to a
    # unique key can only SPLIT existing groups, never merge two rows onto one key, so no
    # existing row can collide when the constraint is swapped. Dropping `location` from the key
    # could have, and a rebuild that raises IntegrityError halfway is not a migration.
    __table_args__ = (
        UniqueConstraint("site_pk", "site_id", "keyword", "location",
                         name="uq_saved_keyword_project_kw_loc"),
        Index("ix_saved_keyword_site", "site_id"),
    )


class KeywordListEntry(Base):
    """One keyword's membership in one named research list — site-scoped and shared.

    Lists used to live only in the browser (`localStorage['fh_keyword_lists']`): invisible to
    the team, gone on a cache clear, and — the reason this table exists — invisible to the
    backend, so the Keywords page's portfolio KPIs could not include them. The portfolio is
    defined as *every keyword saved for this site anywhere* (position tracking ∪ lists,
    deduplicated), so the lists had to become data the server holds.

    Distinct from `saved_keywords` (the position-TRACKING list, which drives paid per-keyword
    connector spend) on purpose: putting a keyword in a research list must never enrol it in
    metered SERP tracking as a side effect. The metric columns are a snapshot of what the
    Keyword Explorer knew when the keyword was sent to the list — research provenance, not
    synced state; keywords added by bare name legitimately carry NULLs.
    """
    __tablename__ = "keyword_list_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    list_name = Column(String(255), nullable=False)
    keyword = Column(Text, nullable=False)
    search_volume = Column(Integer, nullable=True)
    keyword_difficulty = Column(Float, nullable=True)
    cpc = Column(Float, nullable=True)
    intent = Column(String(100), nullable=True)
    added_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "list_name", "keyword", name="uq_kw_list_entry"),
        Index("ix_kw_list_entries_site", "site_id"),
    )


# ─────────────────────────────────────────────
# Prediction & intelligence layer
# ─────────────────────────────────────────────
# Removed 2026-08-03: `MetricForecast` and `RiskSignal` sat here for months with no writer,
# no reader and no UI — schema for a prediction service that was never built. Phantom
# entities cost real review time (every audit has to re-establish that they're empty) and
# invite code that reads a table nothing fills. Restore them from git history WITH the
# service that writes them, not before. `KeywordOpportunity` stays: positioning_service
# genuinely computes and reads it.


class KeywordOpportunity(Base):
    """Scored 'what to target next' keywords. Upsert latest snapshot per (site, keyword)."""
    __tablename__ = "keyword_opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True)
    # The owning PROJECT — same reason as SavedKeyword and TrackedCompetitor. Scored from THIS
    # project's tracked list, so keying on the domain meant two projects sharing one domain
    # deleted each other's rows on every page render (persist runs on a GET) and the upsert
    # silently overwrote a sibling's score for any keyword both track.
    site_pk = Column(Integer, nullable=False, index=True, default=UNOWNED_SITE_PK,
                     server_default=str(UNOWNED_SITE_PK))
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
        # RENAMED from uq_opportunity_site_keyword: the name is how `_swap_unique_constraint`
        # detects a database already moved onto the per-project key.
        UniqueConstraint("site_pk", "keyword", name="uq_opportunity_project_keyword"),
        Index("ix_opportunity_site_score", "site_id", "opportunity_score"),
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

# `keyword_rankings.location` / `competitor_keyword_rankings.location` — see the column comments
# on KeywordRanking. A DEFAULT is given (unlike the nullable measurements above) because these
# columns are NOT NULL and part of a unique key: an existing row must land on a real value in the
# same ALTER, and "United States" is what those rows were genuinely fetched with.
_KEYWORD_RANKINGS_ADDED_COLUMNS = (
    ("location", "VARCHAR(255)", DEFAULT_LOCATION),
    # No DEFAULT: a row written before this column existed has a genuinely unknown check
    # history, and backfilling a date would assert a measurement that may never have happened.
    # See the column comment on KeywordRanking.rank_checked_at.
    ("rank_checked_at", "DATE", None),
)
_COMPETITOR_KEYWORD_RANKINGS_ADDED_COLUMNS = (
    ("location", "VARCHAR(255)", DEFAULT_LOCATION),
)

# (table, old constraint name, new constraint name, new column tuple) for the 2026-08-06
# location key change. `ensure_ranking_location_keys` uses the NAME to decide whether a database
# has been reconciled, which is why the new constraints were given new names rather than
# redefining the old ones in place.
_RANKING_LOCATION_KEYS = (
    ("keyword_rankings", "uq_keyword_date_site", "uq_keyword_date_site_loc",
     ("date", "site_id", "keyword", "location")),
    ("competitor_keyword_rankings", "uq_comp_kw_rank", "uq_comp_kw_rank_loc",
     ("date", "site_id", "keyword", "competitor_domain", "location")),
)

# `saved_keywords.site_pk` — the owning project. See the column comment on SavedKeyword for why
# neither `site_id` nor `location` can identify one. A DEFAULT is given (unlike the nullable
# measurements above) because the column is part of a unique key: an existing row has to land on
# a real value in the same ALTER, and `UNOWNED_SITE_PK` is the honest "not resolved yet" value
# that `_backfill_saved_keyword_projects` then replaces with a real project id.
_SAVED_KEYWORDS_ADDED_COLUMNS = (
    ("site_pk", "INTEGER", UNOWNED_SITE_PK),
)

_SAVED_KEYWORD_PROJECT_KEY = (
    "saved_keywords", "uq_saved_keyword_site_kw_loc", "uq_saved_keyword_project_kw_loc",
    ("site_pk", "site_id", "keyword", "location"),
)

# `tracked_competitors.site_pk` — same migration shape as saved_keywords above, same reason: the
# competitor override set belongs to a PROJECT, and keying it on the domain let one project's
# edit replace its siblings'. See the column comment on TrackedCompetitor.
_TRACKED_COMPETITORS_ADDED_COLUMNS = (
    ("site_pk", "INTEGER", UNOWNED_SITE_PK),
)

_TRACKED_COMPETITOR_PROJECT_KEY = (
    "tracked_competitors", "uq_tracked_competitor_site", "uq_tracked_competitor_project",
    ("site_pk", "competitor_domain"),
)

# `keyword_opportunities.site_pk` — same shape again. NO backfill counterpart: unlike
# saved_keywords (a list a user chose) these rows are a recomputed cache of the current answer,
# so legacy unowned rows are simply dropped by the next persist for their domain rather than
# guessed into an owner.
_KEYWORD_OPPORTUNITIES_ADDED_COLUMNS = (
    ("site_pk", "INTEGER", UNOWNED_SITE_PK),
)

_KEYWORD_OPPORTUNITY_PROJECT_KEY = (
    "keyword_opportunities", "uq_opportunity_site_keyword", "uq_opportunity_project_keyword",
    ("site_pk", "keyword"),
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


def ensure_ranking_location_columns(session_or_engine) -> list[str]:
    """Add `location` to the two ranking tables on an existing database. Idempotent.

    Must run BEFORE `ensure_ranking_location_keys`, which builds a unique constraint over that
    column. `init_db` orders them correctly.
    """
    added = _run_alter(session_or_engine, "keyword_rankings",
                       _KEYWORD_RANKINGS_ADDED_COLUMNS)
    added += _run_alter(session_or_engine, "competitor_keyword_rankings",
                        _COMPETITOR_KEYWORD_RANKINGS_ADDED_COLUMNS)
    return added


def _swap_unique_constraint(conn, table: str, old_name: str, new_name: str,
                            new_columns: tuple) -> bool:
    """Replace `table`'s old unique constraint with one that also covers `location`.

    Returns True if a swap actually happened.

    Why this cannot be left to `create_all`: it only ever creates MISSING TABLES and never
    alters an existing table's constraints. And the swap is not cosmetic — while the old
    3-column key is still in force, two projects tracking the same domain in different cities
    collide on (date, site_id, keyword) and the second one's upsert OVERWRITES the first's
    row instead of adding its own. The location column alone fixes nothing without this.

    The two backends need different SQL, for a real reason rather than a stylistic one:

      * PostgreSQL (what production runs) supports `DROP CONSTRAINT` / `ADD CONSTRAINT`
        directly, so the swap is two statements against the live table and the 215k existing
        rows are never copied.
      * SQLite compiles a table-level UNIQUE into an internal `sqlite_autoindex_*` that
        `DROP INDEX` refuses to touch, so the only way to change it is the documented
        rebuild: create the new table, copy the rows, swap the names. Acceptable here because
        every SQLite database in this project is a dev or test one — production is Postgres.
    """
    inspector = inspect(conn)
    if not inspector.has_table(table):
        return False  # brand-new database: create_all() already built the current definition

    names = {c.get("name") for c in inspector.get_unique_constraints(table)}
    names |= {i.get("name") for i in inspector.get_indexes(table) if i.get("unique")}
    if new_name in names:
        return False                      # already reconciled
    if old_name not in names:
        # Neither name present. Do not invent a constraint on a table whose shape this function
        # does not recognise — say so and leave it alone.
        logger.warning(
            "[schema] %s carries neither %r nor %r; leaving its unique key untouched.",
            table, old_name, new_name,
        )
        return False

    cols = ", ".join(f'"{c}"' for c in new_columns)
    if conn.dialect.name == "sqlite":
        _rebuild_sqlite_table(conn, table)
    else:
        conn.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT "{old_name}"'))
        conn.execute(text(
            f'ALTER TABLE {table} ADD CONSTRAINT "{new_name}" UNIQUE ({cols})'
        ))
    return True


def _rebuild_sqlite_table(conn, table: str) -> None:
    """Rebuild one SQLite table from its current model definition, preserving its rows.

    SQLite cannot alter a table-level UNIQUE in place (see `_swap_unique_constraint`). Only the
    columns present in BOTH the old table and the model are copied, named explicitly — a
    bare `INSERT INTO ... SELECT *` would depend on column ORDER matching, which is exactly the
    assumption that turns a schema migration into silently transposed data.
    """
    model_table = Base.metadata.tables[table]
    old_cols = {c["name"] for c in inspect(conn).get_columns(table)}
    shared = [c.name for c in model_table.columns if c.name in old_cols]
    cols = ", ".join(f'"{c}"' for c in shared)
    tmp = f"{table}__pre_key_swap"

    conn.execute(text(f"ALTER TABLE {table} RENAME TO {tmp}"))
    model_table.create(bind=conn)
    conn.execute(text(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM {tmp}"))
    conn.execute(text(f"DROP TABLE {tmp}"))


def ensure_ranking_location_keys(session_or_engine) -> list[str]:
    """Move both ranking tables onto their location-aware unique keys. Idempotent.

    Returns the tables actually reconciled, so a caller can log a real event.
    """
    def _do(conn) -> list[str]:
        changed = []
        for table, old_name, new_name, cols in _RANKING_LOCATION_KEYS:
            try:
                if _swap_unique_constraint(conn, table, old_name, new_name, cols):
                    changed.append(table)
            except Exception:
                # Never take a sync or a page load down over this. A database left on the old
                # key still reads and writes; it just cannot separate two city projects, which
                # is the pre-existing behaviour rather than a new failure.
                logger.error("[schema] could not swap the unique key on %s", table,
                             exc_info=True)
        return changed

    if isinstance(session_or_engine, Session):
        return _do(session_or_engine.connection())
    with session_or_engine.begin() as conn:
        return _do(conn)


def _backfill_saved_keyword_projects(conn) -> int:
    """Give every unowned `saved_keywords` row the project id it belongs to. Returns the count.

    Runs once per database, between the ALTER that adds `site_pk` and the constraint swap that
    puts it in the unique key. Every row written before the column existed defaulted to
    `UNOWNED_SITE_PK`, and a row nobody owns is invisible to every project — so leaving them
    unresolved would blank out keyword lists that users really did choose and that the rank
    connectors are really being billed for.

    THE OWNERSHIP RULE, and why it is the only defensible one:

      * candidates are the projects whose domain matches the row's `site_id`, expanded through
        `resolve_site_ids` so a row filed under `https://x.com/` still reaches the project
        registered as `x.com` (skills.md §3);
      * among them, a project whose `location` equals the row's wins — that pairing is what the
        previous scoping scheme wrote, so honouring it preserves whatever separation the
        location-based read had actually achieved;
      * otherwise the OLDEST project on the domain takes it. That is the project that existed
        when the row was written, which is the same rule `adopt_orphan_saved_keywords` already
        applies, and guessing at a newer sibling would hand one team's keywords to another.

    A row whose `site_id` matches no project at all keeps `UNOWNED_SITE_PK`. Re-keying
    measurement history is `normalize_site_urls`' job; inventing an owner here could file one
    site's keywords under a different site.
    """
    from collections import defaultdict

    from pipeline.utils.site_ids import resolve_site_ids

    inspector = inspect(conn)
    if not inspector.has_table("saved_keywords") or not inspector.has_table("sites"):
        return 0

    sites = conn.execute(text("SELECT id, site_url, location FROM sites ORDER BY id")).fetchall()
    if not sites:
        return 0

    owners: dict[str, list] = defaultdict(list)   # spelling -> [(id, location)], oldest first
    for site_pk, site_url, location in sites:
        for spelling in resolve_site_ids(site_url or ""):
            owners[spelling].append((site_pk, (location or "").strip()))

    rows = conn.execute(text(
        "SELECT id, site_id, location FROM saved_keywords "
        "WHERE site_pk IS NULL OR site_pk = :unowned"
    ), {"unowned": UNOWNED_SITE_PK}).fetchall()

    updated = 0
    for row_id, site_id, location in rows:
        candidates = owners.get(site_id or "")
        if not candidates:
            continue                              # orphaned spelling — left for normalize_site_urls
        wanted = (location or "").strip()
        target = next((pk for pk, loc in candidates if loc == wanted), candidates[0][0])
        conn.execute(text("UPDATE saved_keywords SET site_pk = :pk WHERE id = :id"),
                     {"pk": target, "id": row_id})
        updated += 1
    return updated


def ensure_saved_keyword_project(session_or_engine) -> bool:
    """Move `saved_keywords` onto its per-PROJECT key: add `site_pk`, fill it, key on it.

    Idempotent, and safe to call on every read path — it inspects first and issues nothing once
    the database is reconciled. That matters because `init_db()` is a management-command entry
    point, not something the web process runs at boot: without a lazy caller, a deployed
    database would never acquire the column and every `select(SavedKeyword)` would fail with
    "no such column" (the same window `ensure_page_speed_columns` documents).

    Returns True if this call changed anything.

    Never raises. A database left on the old key still reads and writes; it just cannot separate
    two projects on one domain, which is the pre-existing behaviour rather than a new failure.
    """
    def _do(conn) -> bool:
        changed = False
        try:
            changed = bool(_alter_missing_columns(conn, "saved_keywords",
                                                  _SAVED_KEYWORDS_ADDED_COLUMNS))
            if _backfill_saved_keyword_projects(conn):
                changed = True
            table, old_name, new_name, cols = _SAVED_KEYWORD_PROJECT_KEY
            if _swap_unique_constraint(conn, table, old_name, new_name, cols):
                changed = True
        except Exception:
            logger.error("[schema] could not move saved_keywords onto its per-project key",
                         exc_info=True)
        return changed

    if isinstance(session_or_engine, Session):
        return _do(session_or_engine.connection())
    with session_or_engine.begin() as conn:
        return _do(conn)


def _backfill_tracked_competitor_projects(conn) -> int:
    """Give every unowned `tracked_competitors` row its owning project id. Returns the count.

    Runs once per database, between the ALTER that adds `site_pk` and the constraint swap that
    puts it in the unique key — the same sequence `_backfill_saved_keyword_projects` documents.

    THE OWNERSHIP RULE: the OLDEST project on the row's domain takes it, with the domain matched
    through `resolve_site_ids` so a row filed under `https://x.com/` still reaches the project
    registered as `x.com` (skills.md §3). There is no location tiebreak here because this table
    has no location column — and unlike saved_keywords there is nothing else to disambiguate
    with, so the oldest project (the one that existed when the row was written, and whose edits
    were landing on it under the old key anyway) is the only defensible owner.

    A row whose `site_id` matches no project keeps `UNOWNED_SITE_PK`: inventing an owner could
    hand one site's competitor set to another.
    """
    from collections import defaultdict

    from pipeline.utils.site_ids import resolve_site_ids

    inspector = inspect(conn)
    if not inspector.has_table("tracked_competitors") or not inspector.has_table("sites"):
        return 0

    sites = conn.execute(text("SELECT id, site_url FROM sites ORDER BY id")).fetchall()
    if not sites:
        return 0

    owners: dict[str, int] = {}                   # spelling -> oldest project id
    for site_pk, site_url in sites:
        for spelling in resolve_site_ids(site_url or ""):
            owners.setdefault(spelling, site_pk)  # ORDER BY id, so the first seen is the oldest

    rows = conn.execute(text(
        "SELECT id, site_id FROM tracked_competitors "
        "WHERE site_pk IS NULL OR site_pk = :unowned"
    ), {"unowned": UNOWNED_SITE_PK}).fetchall()

    updated = 0
    for row_id, site_id in rows:
        target = owners.get(site_id or "")
        if target is None:
            continue                              # orphaned spelling — left alone deliberately
        conn.execute(text("UPDATE tracked_competitors SET site_pk = :pk WHERE id = :id"),
                     {"pk": target, "id": row_id})
        updated += 1
    return updated


def ensure_tracked_competitor_project(session_or_engine) -> bool:
    """Move `tracked_competitors` onto its per-PROJECT key: add `site_pk`, fill it, key on it.

    Idempotent and safe on every read path — it inspects first and issues nothing once the
    database is reconciled. Called lazily from `competitor_service` for the same reason
    `ensure_saved_keyword_project` is: `init_db()` is a management-command entry point, so a
    deployed database would otherwise never acquire the column and every `select(...)` naming
    it would fail with "no such column".

    Returns True if this call changed anything. Never raises: a database left on the old key
    still reads and writes, it just cannot separate two projects on one domain — the
    pre-existing behaviour rather than a new failure.
    """
    def _do(conn) -> bool:
        changed = False
        try:
            changed = bool(_alter_missing_columns(conn, "tracked_competitors",
                                                  _TRACKED_COMPETITORS_ADDED_COLUMNS))
            if _backfill_tracked_competitor_projects(conn):
                changed = True
            table, old_name, new_name, cols = _TRACKED_COMPETITOR_PROJECT_KEY
            if _swap_unique_constraint(conn, table, old_name, new_name, cols):
                changed = True
        except Exception:
            logger.error("[schema] could not move tracked_competitors onto its per-project key",
                         exc_info=True)
        return changed

    if isinstance(session_or_engine, Session):
        return _do(session_or_engine.connection())
    with session_or_engine.begin() as conn:
        return _do(conn)


def ensure_keyword_opportunity_project(session_or_engine) -> bool:
    """Move `keyword_opportunities` onto its per-PROJECT key: add `site_pk`, key on it.

    Idempotent, never raises, safe on every read path — same contract as
    `ensure_saved_keyword_project` / `ensure_tracked_competitor_project`.

    Deliberately has NO backfill step. These rows are a recomputed snapshot of "what to target
    next", not a list anyone chose, so an unowned legacy row is worth nothing to guess at: the
    next `persist_keyword_opportunities` for that domain drops it and writes the project's own
    scored answer in its place.
    """
    def _do(conn) -> bool:
        changed = False
        try:
            changed = bool(_alter_missing_columns(conn, "keyword_opportunities",
                                                  _KEYWORD_OPPORTUNITIES_ADDED_COLUMNS))
            table, old_name, new_name, cols = _KEYWORD_OPPORTUNITY_PROJECT_KEY
            if _swap_unique_constraint(conn, table, old_name, new_name, cols):
                changed = True
        except Exception:
            logger.error("[schema] could not move keyword_opportunities onto its project key",
                         exc_info=True)
        return changed

    if isinstance(session_or_engine, Session):
        return _do(session_or_engine.connection())
    with session_or_engine.begin() as conn:
        return _do(conn)


def ensure_site_url_not_unique(session_or_engine) -> bool:
    """Drop the UNIQUE index on `sites.site_url` if a pre-existing database still has one.

    `Site.site_url` used to be declared `unique=True`; a database created before that was
    removed still carries the resulting unique index (Column(unique=True, index=True) compiles
    to one unique Index, not a separate UniqueConstraint -- confirmed via `PRAGMA index_list`
    on SQLite), and `create_all()` never alters an existing table's constraints. This inspects
    for that index on either backend and replaces it with a plain (non-unique) index of the same
    name, so Position Tracking can register a duplicate domain (add_site(allow_duplicate=True))
    without an IntegrityError. Idempotent: a database already reconciled has no unique index left
    to find, so a repeat call issues nothing.

    Returns True if a unique index was found and replaced.
    """
    def _do(conn) -> bool:
        inspector = inspect(conn)
        if not inspector.has_table("sites"):
            return False
        changed = False
        for idx in inspector.get_indexes("sites"):
            if idx.get("unique") and idx.get("column_names") == ["site_url"]:
                name = idx["name"]
                conn.execute(text(f'DROP INDEX "{name}"'))
                conn.execute(text(f'CREATE INDEX "{name}" ON sites (site_url)'))
                changed = True
        return changed

    if isinstance(session_or_engine, Session):
        return _do(session_or_engine.connection())
    with session_or_engine.begin() as conn:
        return _do(conn)


def init_db(engine: Engine) -> None:
    """Create all analytics tables if they don't exist, then reconcile columns added later.

    Safe to call repeatedly. The reconcile steps are what make this usable as a migration entry
    point on an existing database: create_all cannot add a column, the ensure_* helpers can.
    """
    Base.metadata.create_all(engine)
    ensure_site_columns(engine)
    ensure_page_speed_columns(engine)
    ensure_backlinks_columns(engine)
    ensure_site_url_not_unique(engine)
    # Order matters: the column has to exist before a unique key can be built over it.
    ensure_ranking_location_columns(engine)
    ensure_ranking_location_keys(engine)
    # Same shape, one step each: add site_pk, backfill it, then key on it.
    ensure_saved_keyword_project(engine)
    ensure_tracked_competitor_project(engine)
    ensure_keyword_opportunity_project(engine)
