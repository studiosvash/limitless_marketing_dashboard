"""Keywords page data — raw calculator (shared by the old Django view and the new DRF API
view) built on the existing keyword-intelligence pandas pipeline (health score, intent/KD
distribution, action-bucket segments). See
docs/superpowers/specs/2026-07-10-phaseB2-keywords-design.md for the all_keywords/prevPos fix."""

from datetime import date

import pandas as pd
from sqlalchemy import func, select

from pipeline.db.schema import KeywordRanking
from pipeline.utils.db_connection import get_session


def get_keyword_intelligence_raw(site_id: str, curr_start: date, curr_end: date,
                                  prev_start: date, prev_end: date) -> dict:
    """Keyword health score and action buckets. Identical to the pre-extraction
    _get_keyword_intelligence, except all_keywords is now built from `merged` (carries
    prev_position/pos_change on every row) instead of `df` (current period only) — the old
    version silently omitted prevPos for any keyword outside the top-15-per-segment lists."""
    try:
        with get_session() as session:
            def get_kw_df(start, end):
                rows = session.execute(
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
                    )
                    .where(KeywordRanking.site_id == site_id, KeywordRanking.date >= start, KeywordRanking.date <= end)
                    .group_by(KeywordRanking.keyword)
                ).all()
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
                    "all_keywords": [],
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
                "all_keywords": df_to_dicts(merged.sort_values("clicks", ascending=False).head(200)),
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"get_keyword_intelligence_raw error: {e}", exc_info=True)
        return {
            "health_score": 0, "health_label": "Error", "health_color": "#ef4444",
            "total_tracked": 0, "total_volume": 0, "avg_position": 0, "total_clicks": 0,
            "intent_distribution": {"informational": 0, "commercial": 0, "transactional": 0, "navigational": 0},
            "kd_easy": 0, "kd_medium": 0, "kd_hard": 0,
            "quick_wins": [], "striking": [], "declining": [], "low_ctr": [], "all_keywords": []
        }
