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


def _is_offsite_channel(channel: str) -> bool:
    """This page's own definition of "off-site": referral, social and video traffic GA4
    attributes to another site or platform sending you visitors -- not search-engine, direct
    or paid traffic. Matched on GA4's `sessionDefaultChannelGroup` name (a substring check,
    because custom channel groupings vary the exact string -- "Social"/"Organic Social" and
    "Video"/"Organic Video" both occur in practice).

    Excludes "Organic Search" specifically even though it also contains "Organic" -- that is
    on-site SEO (driven by your own ranking), and the one thing this page explicitly is not.
    Excludes any "Paid *" channel for the same reason a paid campaign isn't earned/off-site
    just because its name also contains "Social" or "Video".

    Single source of truth for every off-site figure on this page (channel-mix flags, KPI
    totals, the trend chart, revenue) so none of them can drift apart on what counts.
    """
    ch = channel or ""
    is_offsite_name = ("Organic" in ch or "Referral" in ch or "Social" in ch or "Video" in ch)
    return is_offsite_name and ch != "Organic Search" and "Paid" not in ch


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
        "engagementRate": eng["engagementRate"] if eng["engagementRate"] is not None else 0.0,
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
        d = by_date.setdefault(str(r.date), {"sessions": 0, "engaged": 0, "conversions": 0})
        if not _is_offsite_channel(r.channel):
            continue
        d["sessions"] += int(r.sessions or 0)
        d["engaged"] += int(r.engaged_sessions or 0)
        d["conversions"] += int(r.conversions or 0)

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
        })
    return out


def query_offsite_landing_pages_raw(site_id: str, start, end) -> list[dict]:
    site_ids = _resolve_site_ids(site_id)
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    SEODaily.landing_page.label("url"),
                    func.sum(SEODaily.sessions).label("sessions"),
                    func.avg(SEODaily.engagement_rate).label("engagement_rate"),
                    func.sum(SEODaily.conversions).label("conversions"),
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
            "engagedRate": round(float(r.engagement_rate or 0.0), 4),
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
    
    # Map sources to referring domains if possible
    source_map = {r["source"].replace("www.", ""): r for r in traffic_sources if "Referral" in r["channel"] or "Social" in r["channel"]}
    
    for rd in ref_domains[:20]:
        domain = rd["domain"].replace("www.", "")
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

    # Social mapping
    def get_social_metrics(domain_keyword: str):
        matches = [r for r in traffic_sources if domain_keyword in r["source"]]
        sess = sum(r["sessions"] for r in matches)
        eng = sum(r["engaged_sessions"] for r in matches)
        conv = sum(r["conversions"] for r in matches)
        rev = sum(r["revenue"] for r in matches)
        return sess, eng, conv, rev

    li_sess, li_eng, li_conv, li_rev = get_social_metrics("linkedin")
    rd_sess, rd_eng, rd_conv, rd_rev = get_social_metrics("reddit")
    yt_sess, yt_eng, yt_conv, yt_rev = get_social_metrics("youtube")
    tw_sess, tw_eng, tw_conv, tw_rev = get_social_metrics("t.co")

    # Platform impressions are ALWAYS None. GA4 measures sessions that arrived from
    # a source; it cannot see how many times a post was shown on LinkedIn, Reddit,
    # YouTube or X. Those counts only exist in each platform's own API, and no
    # platform connector is wired yet — so there is no impression data for any
    # platform, connected toggle or not. The previous `sessions * 12 / 8 / 5 / 4`
    # multipliers were invented out of thin air. None makes the SPA render "—" with
    # a "connector needed" caption, which is the truth.
    social = [
        {"platform": "LinkedIn", "source": "linkedin.com", "channel": "Social", "connected": li_conn, "impressions": None, "sessions": li_sess, **_engagement(li_eng, li_sess), "keyEvents": li_conv, "revenue": li_rev},
        {"platform": "Reddit", "source": "reddit.com", "channel": "Social", "connected": reddit_conn, "impressions": None, "sessions": rd_sess, **_engagement(rd_eng, rd_sess), "keyEvents": rd_conv, "revenue": rd_rev},
        {"platform": "YouTube", "source": "youtube.com", "channel": "Video", "connected": yt_conn, "impressions": None, "sessions": yt_sess, **_engagement(yt_eng, yt_sess), "keyEvents": yt_conv, "revenue": yt_rev},
        {"platform": "X / Twitter", "source": "t.co", "channel": "Social", "connected": x_conn, "impressions": None, "sessions": tw_sess, **_engagement(tw_eng, tw_sess), "keyEvents": tw_conv, "revenue": tw_rev},
    ]

    _ga4_at, _ga4_status = _last_ga4_sync(site_id)

    return {
        "totals": totals,
        "prev": prev,
        "trend": trend,
        "channels": channels,
        "referrers": referrers,
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
