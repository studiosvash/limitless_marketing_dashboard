"""Off-site SEO page — comprehensive multi-source calculations deriving traffic channels,
referrers, social share, and top landing pages across real GA4 SEODaily and Backlinks data."""
import logging
from sqlalchemy import func, select

from pipeline.db.schema import SEODaily, GA4TrafficSourceDaily
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import resolve_site_ids
from apps.dashboard.services.backlinks_service import query_referring_domains_raw

logger = logging.getLogger(__name__)


def _resolve_site_ids(site_id: str) -> list[str]:
    """Every spelling this site's analytics rows may be keyed under — see
    `pipeline/utils/site_ids.py` for why the `sc-domain:` prefix alone was not enough."""
    return resolve_site_ids(site_id)


# --- platform attribution -------------------------------------------------
# GA4's `sessionSource` is a HOST ("m.reddit.com", "lnkd.in", "t.co"), so which platform sent a
# session is a host question and must be answered host-wise. It used to be answered with a naked
# substring test, `if domain_keyword in row["source"]`, and every consequence of that was wrong
# in a way that looked plausible on screen:
#
#   "t.co" in "reddit.com"    -> True   Reddit's entire referral volume was added to X / Twitter
#   "t.co" in "hubspot.com"   -> True   ... as was HubSpot's, and blogspot.com's, and any *t.com
#   "t.co" in "twitter.com"   -> False  ... while X's own domain matched nothing
#   "linkedin" in "lnkd.in"   -> False  LinkedIn's own shortener, which carries most of the
#                                       click-throughs from a LinkedIn post, went nowhere
#   "youtube" in "youtu.be"   -> False  same gap for YouTube
#
# One map, matched with a dot boundary. `source == d or source.endswith("." + d)` accepts
# `m.reddit.com` and refuses `hubspot.com`, and first-match-wins means a source can never be
# counted under two platforms.
#
# Extending this is the supported way to add a platform: add its hosts here and every surface
# that attributes traffic (social table, LinkedIn spotlight) picks it up.
PLATFORM_DOMAINS: dict[str, set[str]] = {
    "linkedin": {"linkedin.com", "lnkd.in"},
    "x": {"t.co", "twitter.com", "x.com"},
    "youtube": {"youtube.com", "youtu.be"},
    "reddit": {"reddit.com", "redd.it"},
}

# Display name per platform key, so the table, the spotlight and the connector flags cannot
# drift apart on what a platform is called.
PLATFORM_LABELS: dict[str, str] = {
    "linkedin": "LinkedIn",
    "reddit": "Reddit",
    "youtube": "YouTube",
    "x": "X / Twitter",
}


def normalise_source(source: str | None) -> str:
    """GA4's source string reduced to a comparable host: lowercased, `www.` stripped.

    `.replace("www.", "")` (what the referrer map used) removes the substring ANYWHERE, so
    `wwww.example.com` and `myww.wwww` mangle. Only a leading label is a `www` prefix.
    """
    s = (source or "").strip().lower().rstrip(".")
    if s.startswith("www."):
        s = s[4:]
    return s


def platform_for_source(source: str | None) -> str | None:
    """The platform key a GA4 `sessionSource` belongs to, or None when it is not one of ours.

    Host-wise with a dot boundary — see PLATFORM_DOMAINS. Returns at most one platform for any
    input, so no session can be double-counted. A bare non-host source (`google`, `(direct)`,
    `newsletter`, or the literal word `linkedin`) is NOT a platform host and matches nothing;
    it is a real off-site source and shows up in the social table under its own name.
    """
    src = normalise_source(source)
    if not src:
        return None
    for platform, domains in PLATFORM_DOMAINS.items():
        for d in domains:
            if src == d or src.endswith("." + d):
                return platform
    return None


# The channels this page is about, named explicitly.
#
# These are GA4's own `sessionDefaultChannelGroup` values for earned off-site traffic: another
# site linked to you (Referral), or someone posted about you on a social/video platform
# (Organic Social, Organic Video). Everything else GA4 can report is deliberately absent —
# Organic Search is on-site SEO, Direct is not attributable to anyone, and every Paid * channel
# is bought rather than earned.
#
# To add a channel (a custom channel grouping that emits bare "Social"/"Video", say), add the
# exact string here. That is the whole extension mechanism, and it changes every figure on the
# page at once — KPI totals, the trend, the channel mix, the social table, the referrer map —
# which is the point of there being one list.
#
# Ordered, not a set: the trend chart stacks its bands in this order, so "which channel is the
# base of the stack" is decided here alongside "which channels count" rather than in the SPA.
OFFSITE_CHANNELS: tuple[str, ...] = (
    "Referral",
    "Organic Social",
    "Organic Video",
)
_OFFSITE_CHANNEL_SET = frozenset(OFFSITE_CHANNELS)


def _is_offsite_channel(channel: str) -> bool:
    """Is this GA4 channel group off-site traffic? Membership of OFFSITE_CHANNELS, nothing else.

    This was a substring test -- `("Organic" in ch or "Referral" in ch or "Social" in ch or
    "Video" in ch) and ch != "Organic Search" and "Paid" not in ch` -- which is a guess at a
    definition rather than a definition, and it was wrong in both directions:

      * It ADMITTED `Organic Shopping`, a standard GA4 channel for shopping-surface listings,
        purely because the name contains "Organic". Those sessions were counted in the
        "off-site sessions" KPI and in the channel mix as earned off-site traffic.
      * A channel is off-site or not on its own merits; extending the substring list to cover
        Affiliates or Email would have meant more substrings that could match the next channel
        Google names.

    An allow-list can only ever count what someone deliberately put in it.
    """
    return (channel or "").strip() in _OFFSITE_CHANNEL_SET


# --- revenue --------------------------------------------------------------
# Revenue exists in exactly one place: ga4_traffic_source_daily.revenue, written
# from GA4's `totalRevenue` metric. seo_daily has no revenue column, so the
# SEODaily-based aggregates below cannot derive it and must read it from here.
# When GA4 reports no revenue (a property with no ecommerce/revenue events) the
# honest answer is 0.0 — never a per-conversion estimate.

def _engagement(engaged: int, sessions: int) -> dict:
    """The two engagement-rate keys, or `None` for both when there is nothing to divide by.

    An engagement rate over zero sessions is **undefined**, not zero: "0% of visitors
    engaged" asserts that visitors arrived and none engaged, which is a measurement nobody
    took. Every one of these used to be `... if sessions > 0 else 0`, so a backlink domain
    that drove no traffic and a platform with no connector both reported a confident 0.0%
    next to genuinely-measured rows. `None` renders as an em dash instead — the same
    convention `impressions` and `users` already use on this page.

    `engagedRate` is the 0-1 fraction the SPA multiplies by 100; `engagementRate` is the
    percentage. Both are returned together so they can never disagree about whether the
    number exists."""
    if sessions <= 0:
        return {"engagedRate": None, "engagementRate": None}
    return {
        "engagedRate": round(engaged / sessions, 3),
        "engagementRate": round(engaged / sessions * 100, 1),
    }


def _revenue_total_raw(site_ids: list[str], start, end) -> float:
    """Real GA4 revenue attributed to off-site channels for the whole period, or 0.0 when GA4
    reported none. Grouped by channel (rather than a flat SUM) so `_is_offsite_channel` can
    filter out Organic Search / Direct / Paid revenue before it's totalled -- this is "Off-
    site SEO"'s Attributed Revenue card, not the site's whole revenue."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    GA4TrafficSourceDaily.channel,
                    func.sum(GA4TrafficSourceDaily.revenue).label("revenue"),
                )
                .where(
                    GA4TrafficSourceDaily.site_id.in_(site_ids),
                    GA4TrafficSourceDaily.date >= start,
                    GA4TrafficSourceDaily.date <= end,
                )
                .group_by(GA4TrafficSourceDaily.channel)
            ).all()
            total = sum(float(r.revenue or 0.0) for r in rows if _is_offsite_channel(r.channel))
            return round(total, 2)
    except Exception as e:
        logger.error(f"_revenue_total_raw error: {e}", exc_info=True)
        return 0.0


def _revenue_by_date_raw(site_ids: list[str], start, end) -> dict:
    """Real GA4 revenue per day, off-site channels only (see `_revenue_total_raw`), keyed by
    ISO date string. Missing day -> no revenue."""
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    GA4TrafficSourceDaily.date,
                    GA4TrafficSourceDaily.channel,
                    func.sum(GA4TrafficSourceDaily.revenue).label("revenue"),
                )
                .where(
                    GA4TrafficSourceDaily.site_id.in_(site_ids),
                    GA4TrafficSourceDaily.date >= start,
                    GA4TrafficSourceDaily.date <= end,
                )
                .group_by(GA4TrafficSourceDaily.date, GA4TrafficSourceDaily.channel)
            ).all()
            out: dict = {}
            for r in rows:
                if not _is_offsite_channel(r.channel):
                    continue
                key = str(r.date)
                out[key] = round(out.get(key, 0.0) + float(r.revenue or 0.0), 2)
            return out
    except Exception as e:
        logger.error(f"_revenue_by_date_raw error: {e}", exc_info=True)
        return {}


def query_offsite_totals_raw(site_id: str, start, end) -> dict:
    """Off-site totals: sessions/engagement/key events attributed to off-site channels only
    (Referral, Organic Social, Social, Organic Video, Video -- see `_is_offsite_channel`), not
    the whole site.

    Sourced from `ga4_traffic_source_daily`, which carries GA4's channel dimension --
    `seo_daily` (used elsewhere on this page for landing pages, which have no channel of
    their own) has none, so it cannot answer an off-site-only question. This used to sum
    `seo_daily.sessions`, i.e. every session on the site including Organic Search, Direct and
    Paid -- so the "Off-site sessions" KPI was really "total site sessions" mislabeled.

    `users` has no equivalent here: `ga4_traffic_source_daily` has no per-channel user count,
    and there is no honest way to attribute a site-wide user total to "off-site" alone, so it
    is None rather than the same whole-site number under a new label.
    """
    site_ids = _resolve_site_ids(site_id)
    sessions = engaged = conversions = 0
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    GA4TrafficSourceDaily.channel,
                    func.sum(GA4TrafficSourceDaily.sessions).label("sessions"),
                    func.sum(GA4TrafficSourceDaily.engaged_sessions).label("engaged_sessions"),
                    func.sum(GA4TrafficSourceDaily.conversions).label("conversions"),
                )
                .where(
                    GA4TrafficSourceDaily.site_id.in_(site_ids),
                    GA4TrafficSourceDaily.date >= start,
                    GA4TrafficSourceDaily.date <= end,
                )
                .group_by(GA4TrafficSourceDaily.channel)
            ).all()
        for r in rows:
            if not _is_offsite_channel(r.channel):
                continue
            sessions += int(r.sessions or 0)
            engaged += int(r.engaged_sessions or 0)
            conversions += int(r.conversions or 0)
    except Exception as e:
        logger.error(f"query_offsite_totals_raw error: {e}", exc_info=True)

    ref_domains = len(query_referring_domains_raw(site_id))
    eng = _engagement(engaged, sessions)
    return {
        "sessions": sessions,
        "users": None,
        # None when there were no sessions to divide by, NOT 0.0. This one key used to
        # re-coerce _engagement's honest None back to zero on the way out, so the headline
        # "Engagement rate" card printed a confident 0% for a project GA4 has never measured
        # -- next to four other cards on the same row that show a dash for the same state.
        "engagementRate": eng["engagementRate"],
        "engagedSessions": engaged,
        "keyEvents": conversions,
        # Real GA4 totalRevenue attributed to off-site channels, not conversions x an
        # invented average order value, and not the site's whole revenue.
        "revenue": _revenue_total_raw(site_ids, start, end),
        "referringDomains": ref_domains,
    }


def query_offsite_trend_raw(site_id: str, start, end) -> list[dict]:
    """Per-day off-site sessions/engagement/key events -- same off-site channel filter as
    `query_offsite_totals_raw`, so the trend line and the KPI card can never disagree about
    what is being measured (see `_is_offsite_channel`).

    Grouped by (date, channel): a day is kept in the output as soon as GA4 reported ANY
    channel for it, with its off-site sum defaulting to 0 when every channel that day was
    Organic Search/Direct/Paid. Filtering rows first and only THEN grouping by date would
    silently drop that day from the x-axis instead of showing a real zero -- the chart plots
    points by array index, not by date, so a missing day would compress the timeline rather
    than show a gap.
    """
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    GA4TrafficSourceDaily.date,
                    GA4TrafficSourceDaily.channel,
                    func.sum(GA4TrafficSourceDaily.sessions).label("sessions"),
                    func.sum(GA4TrafficSourceDaily.engaged_sessions).label("engaged_sessions"),
                    func.sum(GA4TrafficSourceDaily.conversions).label("conversions"),
                )
                .where(
                    GA4TrafficSourceDaily.site_id.in_(site_ids),
                    GA4TrafficSourceDaily.date >= start,
                    GA4TrafficSourceDaily.date <= end,
                )
                .group_by(GA4TrafficSourceDaily.date, GA4TrafficSourceDaily.channel)
            ).all()
    except Exception as e:
        logger.error(f"query_offsite_trend_raw error: {e}", exc_info=True)
        return []

    by_date: dict = {}
    for r in rows:
        d = by_date.setdefault(str(r.date), {
            "sessions": 0, "engaged": 0, "conversions": 0,
            # Zero-filled for EVERY off-site channel, on every day, so the stacked chart has
            # one stable band set across the whole x-axis. A per-day key set would make a band
            # appear and vanish mid-series, which reads as data changing shape rather than a
            # channel going quiet.
            "channels": {ch: 0 for ch in OFFSITE_CHANNELS},
        })
        if not _is_offsite_channel(r.channel):
            continue
        sessions = int(r.sessions or 0)
        d["sessions"] += sessions
        d["engaged"] += int(r.engaged_sessions or 0)
        d["conversions"] += int(r.conversions or 0)
        # The query has always grouped by (date, channel); the channel was summed away one
        # line later and thrown out. Keeping it costs nothing and is the whole stacked chart.
        d["channels"][r.channel.strip()] += sessions

    # Real GA4 totalRevenue per day, off-site channels only; days GA4 reported none stay 0.0.
    revenue_by_date = _revenue_by_date_raw(site_ids, start, end)

    out = []
    for date_str in sorted(by_date):
        d = by_date[date_str]
        out.append({
            "date": date_str,
            "sessions": d["sessions"],
            "engagedSessions": d["engaged"],
            "keyEvents": d["conversions"],
            "revenue": revenue_by_date.get(date_str, 0.0),
            # Per-channel sessions for the stacked area. Always sums to `sessions` above --
            # the bands and the total are the same measurement drawn twice.
            "channels": d["channels"],
        })
    return out


def query_offsite_landing_pages_raw(site_id: str, start, end) -> list[dict]:
    """The site's most-visited pages over the period — ALL traffic, not off-site traffic.

    Two things this cannot be, despite what its name and the heading above it used to claim:

      1. **It is not channel-scoped.** `seo_daily` has no channel column; GA4 writes it from a
         date x country x device x pagePath report that carries no channel dimension at all.
         So this list includes Organic Search and Direct visits, and there is no filter that
         could remove them. It sat under the heading "Where off-site traffic lands / Pages that
         referral & social visitors enter on", which described a measurement nobody took. A
         genuinely off-site landing-page table needs a NEW GA4 report on
         `landingPage` x `sessionDefaultChannelGroup` — a new dimension pair and a new table,
         not a filter over this one.

      2. **These are not entrances.** The column is called `landing_page`, but `ga4.py` fills
         it from the `pagePath` dimension, i.e. every page a session VIEWED, not the page it
         entered on. `pageviews` (GA4 `screenPageViews`) is therefore the metric that is
         actually additive at this grain and is returned alongside `sessions` — one visit that
         viewed three pages contributes a session to three rows here, which is the same
         non-additivity that made `ga4_daily_totals` a separate report.

    Ordered by sessions so the ranking is unchanged; both numbers ship so the UI can label
    what it shows.
    """
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page.label("url"),
                    func.sum(SEODaily.sessions).label("sessions"),
                    # Stored by every GA4 sync since the connector was written, read by
                    # nothing until now.
                    func.sum(SEODaily.pageviews).label("pageviews"),
                    # Session-weighted: engagement rate is a ratio, and AVG() over this
                    # page's (date, country, device) rows let a 2-session cell count as much
                    # as a 900-session one — measured at 77.6% shown vs 72.3% real across a
                    # 28-day window. Divided by the same SUM(sessions) selected above.
                    func.sum(SEODaily.engagement_rate * SEODaily.sessions).label("weighted_engagement"),
                    func.sum(SEODaily.conversions).label("conversions"),
                    # Stored by every GA4 sync and read by nothing until 2026-08-03.
                    # bounce_rate is a ratio -> session-weighted like engagement above.
                    # new_users IS additive: GA4 counts a user as new exactly once, on the
                    # row where their first session started, so a per-page sum is sound.
                    func.sum(SEODaily.bounce_rate * SEODaily.sessions).label("weighted_bounce"),
                    func.sum(SEODaily.new_users).label("new_users"),
                )
                .where(
                    SEODaily.site_id.in_(site_ids),
                    SEODaily.date >= start,
                    SEODaily.date <= end,
                    SEODaily.landing_page.isnot(None),
                )
                .group_by(SEODaily.landing_page)
                .order_by(func.sum(SEODaily.sessions).desc())
                .limit(50)
            ).all()
    except Exception as e:
        logger.error(f"query_offsite_landing_pages_raw error: {e}", exc_info=True)
        return []

    return [
        {
            "url": r.url,
            # seo_daily has no channel dimension, so the channel that drove each
            # landing page is genuinely unknown. Hard-coding "Organic Search"
            # labelled every page — including referral and social entries — with a
            # source we never measured. Empty string = "we don't know"; the SPA
            # renders it as a dash.
            "topSource": "",
            "sessions": int(r.sessions or 0),
            "pageviews": int(r.pageviews or 0),
            "engagedRate": round(float(r.weighted_engagement or 0.0) / r.sessions, 4)
                           if r.sessions else 0.0,
            "bounceRate": round(float(r.weighted_bounce or 0.0) / r.sessions, 4)
                          if r.sessions else 0.0,
            "newUsers": int(r.new_users or 0),
            "keyEvents": int(r.conversions or 0),
        }
        for r in rows
    ]


def query_traffic_sources_raw(site_id: str, start, end) -> list[dict]:
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    GA4TrafficSourceDaily.channel,
                    GA4TrafficSourceDaily.source,
                    func.sum(GA4TrafficSourceDaily.sessions).label("sessions"),
                    func.sum(GA4TrafficSourceDaily.engaged_sessions).label("engaged_sessions"),
                    func.sum(GA4TrafficSourceDaily.conversions).label("conversions"),
                    func.sum(GA4TrafficSourceDaily.revenue).label("revenue"),
                )
                .where(
                    GA4TrafficSourceDaily.site_id.in_(site_ids),
                    GA4TrafficSourceDaily.date >= start,
                    GA4TrafficSourceDaily.date <= end,
                )
                .group_by(GA4TrafficSourceDaily.channel, GA4TrafficSourceDaily.source)
            ).all()
            return [
                {
                    "channel": r.channel,
                    "source": r.source,
                    "sessions": int(r.sessions or 0),
                    "engaged_sessions": int(r.engaged_sessions or 0),
                    "conversions": int(r.conversions or 0),
                    "revenue": float(r.revenue or 0.0),
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"query_traffic_sources_raw error: {e}", exc_info=True)
        return []

def _last_ga4_sync(site_id: str) -> tuple:
    """`(iso_timestamp_or_None, last_run_status)` for this site's `ga4` connector.

    Every number on the Off-site page comes from GA4, so this is the honest "as of" for the
    whole screen.

    Why a status is returned alongside the date, rather than just filtering to successful runs:
    `SyncLog` is UNIQUE on `(connector, site_url)` -- exactly ONE row per pair, rewritten in
    place by each run. So `status` describes the LATEST attempt, and the table has no memory of
    when the last *successful* one was. Filtering `status="success"` would therefore report
    "never synced" for a project that has synced fine for months and merely failed this
    morning, which is worse than the bug being fixed.

    Instead: report the real `last_synced` date, and hand the status back so the caller can say
    "as of <date> — last refresh failed". Both facts, neither invented.
    """
    try:
        from apps.sync.models import SyncLog
        row = (
            SyncLog.objects.filter(site_url=site_id, connector="ga4")
            .values("last_synced", "status")
            .first()
        )
        if not row or not row["last_synced"]:
            return (None, row["status"] if row else "never")
        return (row["last_synced"].isoformat(), row["status"] or "never")
    except Exception as exc:
        logger.error(f"_last_ga4_sync failed for {site_id!r}: {exc}", exc_info=True)
        return (None, "never")


# How many rows the social table shows. LinkedIn is pinned into the first slot, so this is
# 1 pinned + (SOCIAL_TABLE_LIMIT - 1) real sources by session volume.
SOCIAL_TABLE_LIMIT = 8


def build_social_rows(offsite_sources: list[dict], limit: int = SOCIAL_TABLE_LIMIT) -> list[dict]:
    """The social & video table: the sources GA4 actually measured, biggest first.

    This was a FIXED four-row roster — LinkedIn, Reddit, YouTube, X / Twitter — rendered
    whether or not GA4 had ever seen them, and it discarded every other source. Both halves of
    that were wrong at once: a project whose off-site traffic came from Hacker News, a Substack
    and a forum saw four rows of zeroes and none of its real traffic, while four platforms it
    has no presence on were listed as though they were the ones being reported on.

    Sources belonging to one platform are merged (linkedin.com + lnkd.in are one LinkedIn row);
    everything else appears under its own host, which is also where the sources that match no
    platform finally become visible.

    LinkedIn stays pinned in the first slot even at zero sessions. It is not a fabrication —
    the number is a real measured zero — and the LinkedIn spotlight card beside this table
    reads its row by name, so the two would otherwise disagree about whether LinkedIn exists.

    `impressions` is None on every row, always. GA4 sees sessions that ARRIVED from a source;
    it cannot see how many times a post was shown on the platform. That count exists only in
    each platform's own API and no platform connector is wired, so there is no impression data
    for any row. The `sessions * 12 / 8 / 5 / 4` multipliers this replaced were invented.
    Likewise `connected`: no platform connector is registered in the sync engine, so it is
    False everywhere — see the block above its use in build_offsite_response.
    """
    groups: dict[str, dict] = {}
    for r in offsite_sources:
        host = normalise_source(r["source"])
        if not host:
            continue
        platform = platform_for_source(host)
        key = platform or host
        g = groups.setdefault(key, {
            "label": PLATFORM_LABELS.get(platform, host) if platform else host,
            "hosts": set(), "channels": {},
            "sessions": 0, "engaged": 0, "conversions": 0, "revenue": 0.0,
        })
        g["hosts"].add(host)
        g["channels"][r["channel"]] = g["channels"].get(r["channel"], 0) + r["sessions"]
        g["sessions"] += r["sessions"]
        g["engaged"] += r["engaged_sessions"]
        g["conversions"] += r["conversions"]
        g["revenue"] = round(g["revenue"] + r["revenue"], 2)

    # An empty LinkedIn group so the pin has something to pin. Its zeroes are measured: GA4
    # reported no LinkedIn sessions in this window.
    groups.setdefault("linkedin", {
        "label": PLATFORM_LABELS["linkedin"], "hosts": set(), "channels": {},
        "sessions": 0, "engaged": 0, "conversions": 0, "revenue": 0.0,
    })

    def to_row(g: dict) -> dict:
        # Channels listed biggest-first rather than reduced to one: a source genuinely can
        # arrive under two, and picking a winner would hide the other.
        channels = sorted(g["channels"], key=lambda c: -g["channels"][c])
        return {
            "platform": g["label"],
            "source": ", ".join(sorted(g["hosts"])),
            "channel": " · ".join(channels),
            "connected": False,
            "impressions": None,
            "sessions": g["sessions"],
            **_engagement(g["engaged"], g["sessions"]),
            "keyEvents": g["conversions"],
            "revenue": g["revenue"],
        }

    pinned = to_row(groups.pop("linkedin"))
    if not pinned["source"]:
        # No LinkedIn host was measured at all; still name the platform the row is about.
        pinned["source"] = "linkedin.com"
    rest = sorted(groups.values(), key=lambda g: (-g["sessions"], g["label"]))
    return [pinned] + [to_row(g) for g in rest[: max(0, limit - 1)]]


def build_offsite_response(site_id: str, curr_start, curr_end, prev_start, prev_end) -> dict:
    """API-shaped Off-site SEO response across all tabs and charts."""
    totals = query_offsite_totals_raw(site_id, curr_start, curr_end)
    prev = query_offsite_totals_raw(site_id, prev_start, prev_end)
    trend = query_offsite_trend_raw(site_id, curr_start, curr_end)
    landing_pages = query_offsite_landing_pages_raw(site_id, curr_start, curr_end)
    traffic_sources = query_traffic_sources_raw(site_id, curr_start, curr_end)

    # Real channel aggregation from GA4
    channel_agg = {}
    for r in traffic_sources:
        ch = r["channel"]
        if ch not in channel_agg:
            channel_agg[ch] = {"sessions": 0, "engaged": 0, "conversions": 0}
        channel_agg[ch]["sessions"] += r["sessions"]
        channel_agg[ch]["engaged"] += r["engaged_sessions"]
        channel_agg[ch]["conversions"] += r["conversions"]

    # `pct` is each channel's share of ALL channels shown in this same list -- `totals`
    # above is off-site sessions only (see query_offsite_totals_raw), which would make an
    # on-site channel like Organic Search read as >100% of a smaller denominator.
    tot_sessions = max(1, sum(d["sessions"] for d in channel_agg.values()))

    channels = []
    for ch, data in channel_agg.items():
        sess = data["sessions"]
        er = _engagement(data["engaged"], sess)["engagementRate"]
        channels.append({
            "channel": ch,
            "sessions": sess,
            "pct": round(sess / tot_sessions * 100),
            "engagementRate": er,
            "keyEvents": data["conversions"],
            "offsite": _is_offsite_channel(ch)
        })
        
    # No placeholder row when ga4_traffic_source_daily is empty: an "Organic Search
    # / 0 sessions" row is a channel we never measured. An empty list is the honest
    # shape and the SPA already renders the channel mix as blank.

    # Real referrers session mapping
    ref_domains = query_referring_domains_raw(site_id)
    referrers = []
    
    # Every off-site session GA4 attributed to a source, summed PER SOURCE across channels.
    #
    # This was a dict comprehension, `{r["source"]...: r for r in traffic_sources if "Referral"
    # in r["channel"] or "Social" in r["channel"]}`, and it lost data two ways at once:
    #
    #   - Organic Video was not in the filter, so a youtube.com referring domain reported 0
    #     sessions on a page that measured them one section further up.
    #   - A dict comprehension keeps the LAST value for a repeated key. One source under two
    #     channels is normal in GA4 (linkedin.com appears under Referral AND Organic Social),
    #     so whichever row the comprehension saw last silently DISCARDED the other channel's
    #     sessions, key events and revenue.
    #
    # Summing across channels fixes both, and the filter is now the page's single off-site
    # definition rather than a second, differently-worded copy of it.
    source_map: dict[str, dict] = {}
    for r in traffic_sources:
        if not _is_offsite_channel(r["channel"]):
            continue
        agg = source_map.setdefault(normalise_source(r["source"]), {
            "sessions": 0, "engaged_sessions": 0, "conversions": 0, "revenue": 0.0,
        })
        agg["sessions"] += r["sessions"]
        agg["engaged_sessions"] += r["engaged_sessions"]
        agg["conversions"] += r["conversions"]
        agg["revenue"] = round(agg["revenue"] + r["revenue"], 2)

    # Two kinds of link, both real, told apart instead of left as a 0 in a column: a link that
    # drove measured GA4 sessions this period, and a link that exists but drove none. Counted
    # over EVERY linking domain, not just the 20 rows below, because the "Referring domains"
    # KPI counts them all too and these two numbers sit next to each other.
    driving = sum(1 for rd in ref_domains
                  if (source_map.get(normalise_source(rd["domain"])) or {}).get("sessions", 0) > 0)
    referrer_split = {
        "total": len(ref_domains),
        "driving": driving,
        "linkOnly": len(ref_domains) - driving,
    }

    for rd in ref_domains[:20]:
        domain = normalise_source(rd["domain"])
        match = source_map.get(domain)

        # If no match in real GA4 data, it's 0 (since it didn't drive traffic)
        # But we still list it because it's a backlink
        share = match["sessions"] if match else 0
        engaged = match["engaged_sessions"] if match else 0
        convs = match["conversions"] if match else 0
        rev = match["revenue"] if match else 0.0

        referrers.append({
            "domain": rd["domain"],
            "authorityScore": rd["rank"],
            "sessions": share,
            # "This link sent us people" vs "this link exists". Both are facts the row already
            # held; only one of them was legible.
            "drivesTraffic": share > 0,
            # ga4_traffic_source_daily has no user count, so per-referrer users is
            # unknown. It used to be set to `sessions` and commented "# estimate" —
            # a fabricated number. null says "not measured".
            "users": None,
            # None, not 0.0 — this is the common case here, not an edge one: a referring
            # domain is listed because it LINKS to us, and most of them drive no measured
            # GA4 sessions at all. See _engagement().
            "engagementRate": _engagement(engaged, share)["engagementRate"],
            "keyEvents": convs,
            # Real GA4 totalRevenue attributed to this source, or 0.0 when GA4
            # reported none / the domain drove no measured sessions.
            "revenue": rev,
        })

    # `connected` used to be read from ProjectSettings.data["platformConnectors"] — a boolean
    # the user flipped on the Settings page with a "Connect" button that authenticated nothing.
    # It made this page announce "Connector live · impressions + click-throughs" for a platform
    # whose impressions are None and whose connector does not run, which is the fabrication this
    # module exists to avoid. No platform connector is wired into the sync engine (neither
    # pipeline/connectors/linkedin.py nor meta.py is listed in PAGE_CONNECTORS/ALL_CONNECTORS,
    # and Reddit/YouTube/X have no module at all), so the honest value is False for all of them
    # — including on projects that still have a stale `true` stored from the old toggle, which
    # the now-inert Settings row can no longer clear.
    #
    # Flip these to a real per-connector check (a SyncLog row, as the Ads cards do) at the same
    # time as the connector is registered — not before.
    li_conn = reddit_conn = yt_conn = x_conn = False

    # Social mapping — off-site channels only.
    #
    # The social table and the LinkedIn spotlight used to scan EVERY traffic-source row with no
    # channel filter, while the KPIs, the trend and the channel mix all exclude paid traffic via
    # _is_offsite_channel. So a Paid Social campaign on linkedin.com was counted here and nowhere
    # else, and the table could report more sessions than the "Off-site sessions" KPI printed
    # directly above it — the same page disagreeing with itself about what off-site means.
    offsite_sources = [r for r in traffic_sources if _is_offsite_channel(r["channel"])]

    social = build_social_rows(offsite_sources)

    _ga4_at, _ga4_status = _last_ga4_sync(site_id)

    return {
        "totals": totals,
        "prev": prev,
        "trend": trend,
        "channels": channels,
        "referrers": referrers,
        # "Links driving traffic" vs "links only", counted over every linking domain — the
        # difference used to be expressed as a 0 in the sessions column and nothing else.
        "referrerSplit": referrer_split,
        "social": social,
        "landingPages": landing_pages,
        # All False, for the reason given above the li_conn/reddit_conn block.
        "connectors": {
            "linkedin": li_conn, "reddit": reddit_conn, "youtube": yt_conn,
            "x": x_conn, "facebook": False, "instagram": False,
        },
        # `lastUpdated` used to be `totals["engagementRate"]` -- the engagement-rate PERCENTAGE
        # under a key the frontend renders as a timestamp. Now it is the real last successful
        # `ga4` sync for this site (GA4 is what feeds every number on this page), or None when
        # GA4 has never synced. `None` is the honest answer; the banner prints "never synced"
        # rather than inventing a date.
        #
        # Deliberately NOT returned: `cadence` and `ga4_tokens_used`/`ga4_tokens_limit`. The
        # frontend read all three and none has ever existed here, so the banner rendered the
        # literal "undefined · undefined / 0 GA4 tokens". GA4 API token quota is not tracked
        # anywhere in this codebase, so there is no real number to show -- the fix is to stop
        # claiming one, not to invent a counter.
        "syncMeta": {"state": "ready", "lastUpdated": _ga4_at, "lastStatus": _ga4_status},
    }
