"""Keywords page data — raw calculator (shared by the old Django view and the new DRF API
view) built on the existing keyword-intelligence pandas pipeline (health score, intent/KD
distribution, action-bucket segments). See
.claude/api-reference.md for the all_keywords/prevPos fix."""

import json
from datetime import date

import pandas as pd
from sqlalchemy import func, select

from pipeline.db.schema import KeywordRanking
from pipeline.utils.db_connection import get_session


def kw_id(row: dict) -> str:
    return row["keyword"]


def _parse_trend(raw) -> list:
    """keyword_rankings.trend holds a JSON list of 12 monthly volumes, oldest→newest,
    written by the DataForSEO keywords connector. [] (not None) when never synced — the
    SPA's sparkline treats an empty list as "no line", which is the honest render."""
    if not raw:
        return []
    try:
        vals = json.loads(raw) if isinstance(raw, str) else raw
        return [int(v or 0) for v in vals][-12:] if isinstance(vals, list) else []
    except (ValueError, TypeError):
        return []


def to_api_keyword(row: dict, extras: dict | None = None) -> dict:
    """`extras`: per-keyword annotations from saved_keywords (serp_features, competition) —
    research-time facts the sync tables don't carry. Passed in by build_keywords_response;
    {} for callers that don't have them."""
    extra = (extras or {}).get((row.get("keyword") or "").lower(), {})
    return {
        "id": kw_id(row),
        "kw": row["keyword"],
        "intent": row.get("intent"),
        "pos": row.get("position"),
        "prevPos": row.get("prev_position"),
        "volume": row.get("search_volume"),
        "kd": row.get("keyword_difficulty"),
        "cpc": row.get("cpc"),
        "clicks": row.get("clicks"),
        "impressions": row.get("impressions"),
        "ctr": row.get("ctr"),
        "url": row.get("url"),
        # Row's own trend when the window caught it, else the window-independent one from
        # extras — see query_saved_keyword_extras for why both paths exist.
        "monthly": _parse_trend(row.get("trend") or extra.get("trend")),
        "source": "sync",    # every currently-tracked keyword comes from the sync pipeline
        "serpFeatures": extra.get("serp_features") or [],
        "competition": extra.get("competition"),
    }


def get_keyword_intelligence_raw(site_id: str, curr_start: date, curr_end: date,
                                  prev_start: date, prev_end: date, tracked_only: bool = False) -> dict:
    """Keyword health score and action buckets. Identical to the pre-extraction
    _get_keyword_intelligence, except all_keywords is now built from `merged` (carries
    prev_position/pos_change on every row) instead of `df` (current period only) — the old
    version silently omitted prevPos for any keyword outside the top-15-per-segment lists."""
    try:
        tracked_lower = None
        if tracked_only:
            from pipeline.utils.keywords import load_tracked_keywords
            tracked_kws = load_tracked_keywords(site_id)
            if not tracked_kws:
                return {
                    "health_score": 0, "health_label": "No Data", "health_color": "#94a3b8",
                    "total_tracked": 0, "total_volume": 0, "avg_position": 0, "total_clicks": 0,
                    "intent_distribution": {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0},
                    "kd_easy": 0, "kd_medium": 0, "kd_hard": 0,
                    "quick_wins": [], "striking": [], "declining": [], "low_ctr": [],
                    "all_keywords": [], "full_keywords": [],
                }
            tracked_lower = [k.lower() for k in tracked_kws]

        with get_session() as session:
            def get_kw_df(start, end):
                stmt = (
                    select(
                        KeywordRanking.keyword,
                        func.avg(KeywordRanking.position).label("position"),
                        func.sum(KeywordRanking.clicks).label("clicks"),
                        func.sum(KeywordRanking.impressions).label("impressions"),
                        func.max(KeywordRanking.search_volume).label("search_volume"),
                        func.max(KeywordRanking.keyword_difficulty).label("keyword_difficulty"),
                        func.max(KeywordRanking.cpc).label("cpc"),
                        func.max(KeywordRanking.intent).label("intent"),
                        func.max(KeywordRanking.url).label("url"),
                        # JSON text; MAX just picks the non-null one — every row for a
                        # keyword carries the same series from the same connector run.
                        func.max(KeywordRanking.trend).label("trend"),
                    )
                    .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= start, KeywordRanking.date <= end)
                )
                if tracked_lower is not None:
                    stmt = stmt.where(func.lower(KeywordRanking.keyword).in_(tracked_lower))
                rows = session.execute(stmt.group_by(KeywordRanking.keyword)).all()
                if not rows:
                    return pd.DataFrame()
                df = pd.DataFrame([dict(r._mapping) for r in rows])
                df["ctr"] = (df["clicks"] / df["impressions"] * 100).fillna(0)
                return df

            df = get_kw_df(curr_start, curr_end)
            prev_df = get_kw_df(prev_start, prev_end)

            if df.empty:
                return {
                    "health_score": 0, "health_label": "No Data", "health_color": "#94a3b8",
                    "total_tracked": 0, "total_volume": 0, "avg_position": 0, "total_clicks": 0,
                    "intent_distribution": {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0},
                    "kd_easy": 0, "kd_medium": 0, "kd_hard": 0,
                    "quick_wins": [], "striking": [], "declining": [], "low_ctr": [],
                    "all_keywords": [], "full_keywords": [],
                }

            with_clicks = df[df["clicks"] > 0]
            top10 = df[df["position"] <= 10]
            p1_ratio = len(top10) / len(df) if len(df) > 0 else 0
            click_ratio = len(with_clicks) / len(df) if len(df) > 0 else 0
            health_score = int((p1_ratio * 0.6 + click_ratio * 0.4) * 100)

            if health_score >= 70:
                health_color, health_label = "#10b981", "Excellent"
            elif health_score >= 40:
                health_color, health_label = "#f59e0b", "Needs Work"
            else:
                health_color, health_label = "#ef4444", "Critical"

            if not prev_df.empty and "position" in prev_df.columns:
                merged = df.merge(
                    prev_df[["keyword", "position"]].rename(columns={"position": "prev_position"}),
                    on="keyword", how="left"
                )
                merged["pos_change"] = merged["prev_position"] - merged["position"]
            else:
                merged = df.copy()
                merged["prev_position"] = None
                merged["pos_change"] = None

            quick_wins = merged[
                (merged["position"] >= 4) & (merged["position"] <= 10) & (merged["clicks"] > 0)
            ].sort_values("clicks", ascending=False).head(15)

            striking = merged[
                (merged["position"] >= 11) & (merged["position"] <= 20)
            ].sort_values(["impressions", "position"], ascending=[False, True]).head(15)

            if "pos_change" in merged.columns and merged["pos_change"].notna().any():
                declining = merged[merged["pos_change"] <= -3].sort_values("pos_change").head(15)
            else:
                declining = pd.DataFrame()

            low_ctr = merged[
                (merged["position"] <= 20) & (merged["impressions"] >= 50) & (merged["ctr"] < 2.0)
            ].sort_values("impressions", ascending=False).head(15)

            # all_keywords must be a superset of every segment's members: the segments below
            # sort by their own criteria (impressions, pos_change, ...) rather than clicks, so
            # a keyword can qualify for e.g. `striking` while falling outside the top-200-by-
            # clicks slice. Dropping it here would leave a segment ID with no matching entry in
            # `keywords[]` (see build_keywords_response), which the frontend surfaces as a tab
            # whose row count doesn't match its rendered rows. Union the top-200-by-clicks slice
            # (preserves the existing cap/ordering for the general table) with every segment
            # member, then dedupe and re-sort by clicks descending.
            top_by_clicks = merged.sort_values("clicks", ascending=False).head(200)
            segment_frames = [f for f in (quick_wins, striking, declining, low_ctr) if not f.empty]
            if segment_frames:
                all_keywords_df = (
                    pd.concat([top_by_clicks, *segment_frames], ignore_index=True)
                    .drop_duplicates(subset="keyword")
                    .sort_values("clicks", ascending=False)
                )
            else:
                all_keywords_df = top_by_clicks

            def df_to_dicts(data_df):
                if data_df.empty:
                    return []
                # .astype(object) first: plain `.where(pd.notna(df), None)` on a float64
                # column silently reverts the None back to NaN (pandas can't hold None in a
                # float dtype), which would leave prev_position as NaN instead of a real None
                # for keywords with no previous-period row. Casting to object dtype first lets
                # the None actually stick, so JSON/dict consumers see null, not NaN.
                return data_df.astype(object).where(pd.notna(data_df), None).to_dict('records')

            intent_counts = {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0}
            if "intent" in df.columns:
                for val in df["intent"].dropna():
                    key = str(val).lower().strip()
                    if key in intent_counts:
                        intent_counts[key] += 1
                    elif "info" in key:
                        intent_counts["informational"] += 1
                    elif "comm" in key:
                        intent_counts["commercial"] += 1
                    elif "trans" in key:
                        intent_counts["transactional"] += 1
                    elif "nav" in key:
                        intent_counts["navigational"] += 1

            kd_easy = kd_medium = kd_hard = 0
            if "keyword_difficulty" in df.columns:
                kd_vals = df["keyword_difficulty"].dropna()
                kd_easy = int((kd_vals < 30).sum())
                kd_medium = int(((kd_vals >= 30) & (kd_vals < 60)).sum())
                kd_hard = int((kd_vals >= 60).sum())

            total_volume = int(df["search_volume"].dropna().sum()) if "search_volume" in df.columns else 0
            avg_position = round(df["position"].mean(), 1) if "position" in df.columns and not df["position"].isna().all() else 0
            total_clicks = int(df["clicks"].sum()) if "clicks" in df.columns else 0

            return {
                "health_score": health_score,
                "health_label": health_label,
                "health_color": health_color,
                "total_tracked": len(df),
                "total_volume": total_volume,
                "avg_position": avg_position,
                "total_clicks": total_clicks,
                "intent_distribution": intent_counts,
                "kd_easy": kd_easy,
                "kd_medium": kd_medium,
                "kd_hard": kd_hard,
                "quick_wins": df_to_dicts(quick_wins),
                "striking": df_to_dicts(striking),
                "declining": df_to_dicts(declining),
                "low_ctr": df_to_dicts(low_ctr),
                "all_keywords": df_to_dicts(all_keywords_df),
                "full_keywords": df_to_dicts(merged.sort_values("clicks", ascending=False)),
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"get_keyword_intelligence_raw error: {e}", exc_info=True)
        return {
            "health_score": 0, "health_label": "Error", "health_color": "#ef4444",
            "total_tracked": 0, "total_volume": 0, "avg_position": 0, "total_clicks": 0,
            "intent_distribution": {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0},
            "kd_easy": 0, "kd_medium": 0, "kd_hard": 0,
            "quick_wins": [], "striking": [], "declining": [], "low_ctr": [], "all_keywords": [], "full_keywords": []
        }


def query_saved_keyword_extras(site_id: str) -> dict:
    """{lower(keyword): {"serp_features": [...], "competition": "LOW"|...}} from
    saved_keywords — research-time facts the Explorer captured that the sync tables never
    carry. They were stored on every Track click and then read by nothing; the tracked
    table showed a keyword's SERP features in the research view and dropped them the
    moment it was tracked (found in the 2026-08-03 surfacing audit)."""
    from pipeline.db.schema import SavedKeyword
    try:
        with get_session() as session:
            rows = session.execute(
                select(SavedKeyword.keyword, SavedKeyword.serp_features, SavedKeyword.competition)
                .where(SavedKeyword.site_id == site_id)
            ).all()
    except Exception:
        import logging; logging.getLogger(__name__).error("query_saved_keyword_extras failed", exc_info=True)
        return {}
    out = {}
    for kw, serp, competition in rows:
        feats = [s.strip() for s in serp.split(",") if s.strip()] if isinstance(serp, str) else (serp or [])
        out[(kw or "").lower()] = {"serp_features": feats, "competition": competition}

    # 12-month trend, window-INDEPENDENT on purpose: the sync stamps it on the row for the
    # day the sync ran, which is routinely outside the page's date window (the window is
    # anchored to the last GSC data date, which trails a just-run keyword sync). It is a
    # research attribute of the keyword, not a time series — reading it only through the
    # window left the sparkline empty right after the very sync that fetched it.
    try:
        with get_session() as session:
            for kw, trend in session.execute(
                select(KeywordRanking.keyword, func.max(KeywordRanking.trend))
                .where(KeywordRanking.site_id == site_id, KeywordRanking.trend.isnot(None))
                .group_by(KeywordRanking.keyword)
            ):
                out.setdefault((kw or "").lower(), {})["trend"] = trend
    except Exception:
        import logging; logging.getLogger(__name__).error("trend map failed", exc_info=True)
    return out


def get_keyword_lists_raw(site_id: str) -> list[dict]:
    """The site's research lists, in the shape the SPA holds them:
    [{"id", "name", "keywords": [{"kw", "volume", "kd", "cpc", "intent"}]}]. `id` is the
    list name — names are unique per site by construction (one row per (site, list, kw))."""
    from pipeline.db.schema import KeywordListEntry
    from pipeline.db.writer import ensure_tables
    try:
        with get_session() as session:
            ensure_tables(session, KeywordListEntry)
            rows = session.execute(
                select(KeywordListEntry.list_name, KeywordListEntry.keyword,
                       KeywordListEntry.search_volume, KeywordListEntry.keyword_difficulty,
                       KeywordListEntry.cpc, KeywordListEntry.intent)
                .where(KeywordListEntry.site_id == site_id)
                .order_by(KeywordListEntry.list_name, KeywordListEntry.id)
            ).all()
    except Exception:
        import logging; logging.getLogger(__name__).error("get_keyword_lists_raw failed", exc_info=True)
        return []

    lists: dict[str, list] = {}
    for name, kw, vol, kd, cpc, intent in rows:
        lists.setdefault(name, []).append(
            {"kw": kw, "volume": vol, "kd": kd, "cpc": cpc, "intent": intent})
    return [{"id": name, "name": name, "keywords": kws} for name, kws in lists.items()]


def _bucket_intent(value, counts: dict) -> None:
    key = str(value or "").lower().strip()
    if key in counts:
        counts[key] += 1
    elif "info" in key:
        counts["informational"] += 1
    elif "comm" in key:
        counts["commercial"] += 1
    elif "trans" in key:
        counts["transactional"] += 1
    elif "nav" in key:
        counts["navigational"] += 1


def query_keyword_portfolio_raw(site_id: str) -> dict:
    """Portfolio-wide KPI inputs over EVERY keyword saved for this site — the position-
    tracking list (`saved_keywords`) ∪ every research list (`keyword_list_entries`) —
    deduplicated case-insensitively across all of them.

    Scope decided by the product owner (2026-08-03): "Total keywords / Total volume /
    intent / difficulty should represent not just keywords tracked in position tracking but
    overall keywords saved in lists; repeats across lists must not be double-counted."
    Average position is deliberately NOT here — a list keyword has no measured position, so
    that KPI stays tracked-only.

    Per-keyword metrics prefer `keyword_rankings` (synced, freshest) over the saved/list
    snapshot taken when the keyword was filed. A keyword nowhere synced keeps its snapshot
    values; one with no known volume anywhere contributes 0 volume but still counts as a
    keyword — membership is the fact being counted, metrics are best-known.
    """
    from pipeline.db.schema import KeywordListEntry, SavedKeyword
    from pipeline.db.writer import ensure_tables

    portfolio: dict[str, dict] = {}   # lower(kw) -> {volume, kd, intent, rank}
    RANK_LIST, RANK_SAVED, RANK_SYNCED = 0, 1, 2

    def _absorb(kw, volume, kd, intent, rank):
        key = (kw or "").strip().lower()
        if not key:
            return
        cur = portfolio.setdefault(key, {"volume": None, "kd": None, "intent": None, "rank": -1})
        # Per-field: a higher-priority source wins; a lower one only fills gaps.
        for field, val in (("volume", volume), ("kd", kd), ("intent", intent)):
            if val is None or (isinstance(val, str) and not val.strip()):
                continue
            if rank >= cur["rank"] or cur[field] is None:
                cur[field] = val
        cur["rank"] = max(cur["rank"], rank)

    try:
        with get_session() as session:
            ensure_tables(session, KeywordListEntry)
            for kw, vol, kd, intent in session.execute(
                select(KeywordListEntry.keyword, KeywordListEntry.search_volume,
                       KeywordListEntry.keyword_difficulty, KeywordListEntry.intent)
                .where(KeywordListEntry.site_id == site_id)
            ):
                _absorb(kw, vol, kd, intent, RANK_LIST)

            for kw, vol, kd, intent in session.execute(
                select(SavedKeyword.keyword, SavedKeyword.search_volume,
                       SavedKeyword.keyword_difficulty, SavedKeyword.intent)
                .where(SavedKeyword.site_id == site_id)
            ):
                _absorb(kw, vol, kd, intent, RANK_SAVED)

            if portfolio:
                # Synced metrics for exactly the portfolio's members. No date filter:
                # volume/KD/intent are research attributes, not a time series — the newest
                # non-null ever synced is the best-known value.
                for kw, vol, kd, intent in session.execute(
                    select(KeywordRanking.keyword,
                           func.max(KeywordRanking.search_volume),
                           func.max(KeywordRanking.keyword_difficulty),
                           func.max(KeywordRanking.intent))
                    .where(KeywordRanking.site_id == site_id,
                           func.lower(KeywordRanking.keyword).in_(list(portfolio.keys())))
                    .group_by(KeywordRanking.keyword)
                ):
                    _absorb(kw, vol, kd, intent, RANK_SYNCED)
    except Exception:
        import logging; logging.getLogger(__name__).error("query_keyword_portfolio_raw failed", exc_info=True)
        return {"total": 0, "total_volume": 0,
                "intents": {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0},
                "difficulty": {"easy": 0, "medium": 0, "hard": 0}}

    intents = {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0}
    easy = medium = hard = 0
    total_volume = 0
    for m in portfolio.values():
        total_volume += int(m["volume"] or 0)
        if m["intent"]:
            _bucket_intent(m["intent"], intents)
        if m["kd"] is not None:
            kd = float(m["kd"])
            if kd < 30:
                easy += 1
            elif kd < 60:
                medium += 1
            else:
                hard += 1

    return {"total": len(portfolio), "total_volume": total_volume,
            "intents": intents, "difficulty": {"easy": easy, "medium": medium, "hard": hard}}


def build_keywords_response(site_id: str, curr_start: date, curr_end: date,
                             prev_start: date, prev_end: date) -> dict:
    """HANDOFF_SPEC.md `keywords` view shape — verified against the real fixture's
    keywordsView() in Limitless marketing dashboard2/app/api.js. See
    .claude/api-reference.md for the field mapping."""
    intel = get_keyword_intelligence_raw(site_id, curr_start, curr_end, prev_start, prev_end, tracked_only=True)

    # Portfolio scope (owner decision, 2026-08-03): total / volume / intent / difficulty
    # cover every keyword saved anywhere for this site (tracked ∪ lists, deduplicated).
    # avg_pos and total_clicks stay tracked-only — only tracked keywords have measured
    # positions and click attribution. A site with nothing saved falls back to the synced-
    # rankings figures so its page is not blanked by the scope change.
    portfolio = query_keyword_portfolio_raw(site_id)
    has_portfolio = portfolio["total"] > 0
    extras = query_saved_keyword_extras(site_id)

    return {
        "kpis": {
            "total": portfolio["total"] if has_portfolio else intel["total_tracked"],
            "avg_pos": intel["avg_position"],
            "total_volume": portfolio["total_volume"] if has_portfolio else intel["total_volume"],
            "total_clicks": intel["total_clicks"],
        },
        "intents": portfolio["intents"] if has_portfolio else intel["intent_distribution"],
        "difficulty": portfolio["difficulty"] if has_portfolio
                      else {"easy": intel["kd_easy"], "medium": intel["kd_medium"], "hard": intel["kd_hard"]},
        "segments": {
            "quick_wins": [kw_id(r) for r in intel["quick_wins"]],
            "striking": [kw_id(r) for r in intel["striking"]],
            "declining": [kw_id(r) for r in intel["declining"]],
            "low_ctr": [kw_id(r) for r in intel["low_ctr"]],
        },
        "keywords": [to_api_keyword(r, extras) for r in intel["all_keywords"]],
        "lists": get_keyword_lists_raw(site_id),
    }
