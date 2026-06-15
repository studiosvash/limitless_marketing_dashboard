"""
pipeline/services/anomaly_service.py — Anomaly detection engine.

Detects unusual patterns in metrics by comparing against 12-week baseline.
Called by pipeline tasks after daily syncs. Anomaly acknowledgment is handled
by Django views directly via the Anomaly SQLAlchemy table.
"""

from datetime import date, timedelta
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from pipeline.db.schema import SEODaily, AdMetricDaily, Anomaly
from pipeline.db.writer import upsert_anomaly as _upsert_anomaly
from pipeline.utils.db_connection import get_session
from pipeline.utils.logger import get_logger

logger = get_logger("anomaly_service")


def _daily_seo_totals(session, start_date: date, end_date: date, site_id: str = "") -> dict:
    """Aggregate seo_daily into one row PER DAY (it is stored per
    country×device×page, ~90 rows/day). Returns {date: {clicks, impressions,
    ctr, avg_position}}. ctr and avg_position are impression-weighted so a
    long-tail dimension row can't skew the daily figure.

    This is the unit anomaly detection must compare on — comparing a single
    raw dimension row against a multi-dimension average is meaningless.
    """
    q = select(
        SEODaily.date.label("d"),
        func.sum(SEODaily.clicks).label("clicks"),
        func.sum(SEODaily.impressions).label("impressions"),
        func.sum(SEODaily.avg_position * SEODaily.impressions).label("pos_weighted"),
    ).where(SEODaily.date.between(start_date, end_date)).group_by(SEODaily.date)
    if site_id:
        q = q.where(SEODaily.site_id == site_id)

    out: dict = {}
    for row in session.execute(q).all():
        clicks = float(row.clicks or 0)
        impressions = float(row.impressions or 0)
        out[row.d] = {
            "clicks": clicks,
            "impressions": impressions,
            "ctr": (clicks / impressions) if impressions else 0.0,
            "avg_position": (float(row.pos_weighted or 0) / impressions) if impressions else 0.0,
        }
    return out


def _get_rolling_average_seo(session, end_date: date, weeks: int = 12, site_id: str = "") -> dict:
    """Mean of each DAILY metric over the trailing `weeks` window, excluding the
    most recent 7 days (so a current spike doesn't dilute its own baseline)."""
    start_date = end_date - timedelta(days=(weeks * 7 + 7))
    daily = _daily_seo_totals(session, start_date, end_date - timedelta(days=7), site_id)
    # Only average over days that actually reported data. GSC data is sparse
    # here — including 0-impression (no-data) days would drag the baseline to
    # nonsense and manufacture false anomalies.
    daily = {d: v for d, v in daily.items() if v["impressions"] > 0}
    if not daily:
        return {"baseline_clicks": 0, "baseline_impressions": 0, "baseline_ctr": 0, "baseline_avg_position": 0}

    n = len(daily)
    return {
        "baseline_clicks": sum(d["clicks"] for d in daily.values()) / n,
        "baseline_impressions": sum(d["impressions"] for d in daily.values()) / n,
        "baseline_ctr": sum(d["ctr"] for d in daily.values()) / n,
        "baseline_avg_position": sum(d["avg_position"] for d in daily.values()) / n,
    }


def _get_rolling_average_ads(session, end_date: date, weeks: int = 12, site_id: str = "") -> dict:
    from sqlalchemy import select, func
    start_date = end_date - timedelta(days=(weeks * 7 + 7))
    q = select(
        func.avg(AdMetricDaily.spend).label("avg_spend"),
        func.avg(AdMetricDaily.clicks).label("avg_clicks"),
        func.avg(AdMetricDaily.impressions).label("avg_impressions"),
        func.avg(AdMetricDaily.conversions).label("avg_conversions"),
    ).where(AdMetricDaily.date.between(start_date, end_date - timedelta(days=7)))
    if site_id:
        q = q.where(AdMetricDaily.site_id == site_id)
    result = session.execute(q).one()
    return {
        "baseline_spend": float(result.avg_spend or 0),
        "baseline_clicks": float(result.avg_clicks or 0),
        "baseline_impressions": float(result.avg_impressions or 0),
        "baseline_conversions": float(result.avg_conversions or 0),
    }


class AnomalyDetector:
    """Detects metric anomalies against 12-week rolling baseline."""

    ANOMALY_THRESHOLD_PCT = 35  # Flag only meaningful swings (was 20 — too noisy on low-volume data)
    SEVERITY_THRESHOLDS = {
        "low": 35,      # 35-50% = low
        "medium": 50,   # 50-75% = medium
        "high": 75,     # >75% = high
    }

    # A % swing on tiny numbers isn't a story. Require a minimum absolute change
    # too, so "2 clicks vs 8" or "23 impressions vs 49" don't spam the alerts.
    MIN_ABS_CHANGE = {
        "clicks": 10,        # at least 10 clicks of movement
        "impressions": 100,  # at least 100 impressions of movement
        "ctr": 0.05,         # at least 5 percentage points of CTR
        "avg_position": 5,   # at least 5 ranking positions
        "spend": 50,
        "conversions": 5,
    }

    def __init__(self, session: Session, site_id: str = ""):
        self.session = session
        self.site_id = site_id

    def detect_all(self, check_date: date, site_id: str = "") -> list[dict]:
        """
        Scan all metrics for given date against 12-week baseline.
        Returns list of result dicts from upserted anomaly records.
        """
        effective_site_id = site_id or self.site_id
        anomalies = []

        # SEO metrics to check — VOLUME ONLY.
        # CTR and avg_position are deliberately excluded from daily anomaly
        # detection: at this traffic level the impression-weighted daily figure
        # is dominated by which page happened to get impressions that day
        # (mix-shift), not by real change. CTR is surfaced at period level on the
        # Overview, and position per-keyword on the Positioning page — both of
        # which compare like-for-like and are actually meaningful.
        seo_metrics = [
            ("seo_clicks", "clicks"),
            ("seo_impressions", "impressions"),
        ]

        for metric_type, field_name in seo_metrics:
            result = self._check_seo_metric(metric_type, field_name, check_date, effective_site_id)
            if result:
                anomalies.append(result)

        # Ad metrics to check
        ad_metrics = [
            ("ad_spend", "spend"),
            ("ad_clicks", "clicks"),
            ("ad_impressions", "impressions"),
            ("ad_conversions", "conversions"),
        ]

        for metric_type, field_name in ad_metrics:
            result = self._check_ad_metric(metric_type, field_name, check_date, effective_site_id)
            if result:
                anomalies.append(result)

        logger.info(f"[anomaly] Detected {len(anomalies)} anomalies on {check_date} for site={effective_site_id!r}")
        return anomalies

    def _check_seo_metric(
        self,
        metric_type: str,
        field_name: str,
        check_date: date,
        site_id: str = "",
    ) -> Optional[dict]:
        """
        Check single SEO metric for anomaly.
        Returns anomaly dict if deviation exceeds threshold, else None.
        """
        # Aggregate the day across all country×device×page rows into one daily
        # total, then compare that against the daily baseline.
        day_totals = _daily_seo_totals(self.session, check_date, check_date, self.site_id)
        day = day_totals.get(check_date)
        if not day:
            return None

        # A day with no impressions means GSC reported nothing for it (sparse /
        # not-yet-finalized data), NOT a real-world drop. Skip it so we never
        # flag a phantom "-100%" anomaly.
        if day["impressions"] <= 0:
            return None

        current_value = day.get(field_name)
        if current_value is None:
            return None

        # Get 12-week baseline (exclude current week)
        baseline = _get_rolling_average_seo(self.session, check_date, weeks=12, site_id=self.site_id)

        baseline_key = f"baseline_{field_name}"
        baseline_value = baseline.get(baseline_key, 0)

        if baseline_value == 0:
            return None

        deviation_pct = abs((current_value - baseline_value) / baseline_value) * 100

        if deviation_pct < self.ANOMALY_THRESHOLD_PCT:
            return None

        # Magnitude gate: ignore big-% swings that are tiny in absolute terms.
        min_abs = self.MIN_ABS_CHANGE.get(field_name, 0)
        if abs(current_value - baseline_value) < min_abs:
            return None

        severity = self._get_severity(deviation_pct)
        description = (
            f"{metric_type}: {current_value:.2f} vs baseline {baseline_value:.2f} "
            f"({deviation_pct:.1f}% deviation)"
        )

        record = {
            "date": check_date,
            "site_id": site_id or "",
            "metric_type": metric_type,
            "actual_value": float(current_value),
            "baseline_value": float(baseline_value),
            "deviation_pct": round(deviation_pct, 2),
            "severity": severity,
            "description": description,
            "is_acknowledged": 0,
        }
        _upsert_anomaly(self.session, [record])
        return record

    def _check_ad_metric(
        self,
        metric_type: str,
        field_name: str,
        check_date: date,
        site_id: str = "",
    ) -> Optional[dict]:
        """
        Check single ad metric for anomaly across all platforms.
        """
        total = self.session.execute(
            select(func.sum(getattr(AdMetricDaily, field_name))).where(
                AdMetricDaily.date == check_date,
                AdMetricDaily.site_id == (self.site_id or ""),
            )
        ).scalar()

        if total is None:
            return None

        current_value = total

        baseline = _get_rolling_average_ads(self.session, check_date, weeks=12, site_id=self.site_id)
        baseline_key = f"baseline_{field_name}"
        baseline_value = baseline.get(baseline_key, 0)

        if baseline_value == 0:
            return None

        deviation_pct = abs((current_value - baseline_value) / baseline_value) * 100

        if deviation_pct < self.ANOMALY_THRESHOLD_PCT:
            return None

        # Magnitude gate: ignore big-% swings that are tiny in absolute terms.
        min_abs = self.MIN_ABS_CHANGE.get(field_name, 0)
        if abs(current_value - baseline_value) < min_abs:
            return None

        severity = self._get_severity(deviation_pct)
        description = (
            f"{metric_type}: {current_value:.2f} vs baseline {baseline_value:.2f} "
            f"({deviation_pct:.1f}% deviation)"
        )

        record = {
            "date": check_date,
            "site_id": site_id or "",
            "metric_type": metric_type,
            "actual_value": float(current_value),
            "baseline_value": float(baseline_value),
            "deviation_pct": round(deviation_pct, 2),
            "severity": severity,
            "description": description,
            "is_acknowledged": 0,
        }
        _upsert_anomaly(self.session, [record])
        return record

    @staticmethod
    def _get_severity(deviation_pct: float) -> str:
        """Determine severity based on deviation %."""
        if deviation_pct >= 75:
            return "high"
        elif deviation_pct >= 50:
            return "medium"
        else:
            return "low"


# GSC finalizes data ~2-3 days late; the trailing days are incomplete, not
# anomalous. Never judge inside this window.
GSC_LAG_DAYS = 3
# How far back to (re)scan on each sync.
ANOMALY_LOOKBACK_DAYS = 30


def detect_recent_anomalies(site_id: str) -> int:
    """Re-detect SEO anomalies for the trailing window and persist them.

    Driver used by the sync engine. Determines the latest reported day from the
    data itself, skips the GSC reporting-lag window, clears the site's previous
    anomalies (so resolved ones don't linger), and rewrites the current set.
    Returns the number of anomalies written.
    """
    from sqlalchemy import delete

    with get_session() as session:
        latest = session.execute(
            select(func.max(SEODaily.date)).where(SEODaily.site_id == site_id)
        ).scalar()
        if not latest:
            return 0

        end = latest - timedelta(days=GSC_LAG_DAYS)

        # Clear prior anomalies for this site before re-detecting.
        session.execute(delete(Anomaly).where(Anomaly.site_id == site_id))

        detector = AnomalyDetector(session, site_id=site_id)
        written = 0
        for i in range(ANOMALY_LOOKBACK_DAYS):
            written += len(detector.detect_all(end - timedelta(days=i), site_id=site_id))
        session.commit()
        return written
