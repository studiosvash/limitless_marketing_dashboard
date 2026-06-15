from datetime import date, timedelta
from sqlalchemy import delete
from pipeline.utils.db_connection import get_session
from pipeline.db.schema import Anomaly
from pipeline.services.anomaly_service import AnomalyDetector, _daily_seo_totals

SITE = "sc-domain:fusehealth.com"
LAST_DATA = date(2026, 6, 2)
GSC_LAG_DAYS = 3                      # GSC finalizes ~2-3 days late; don't judge those
END = LAST_DATA - timedelta(days=GSC_LAG_DAYS)
DAYS_BACK = 30

# Clear prior (noisy) anomalies for this site before re-detecting
with get_session() as session:
    session.execute(delete(Anomaly).where(Anomaly.site_id == SITE))
    session.commit()

found = []
with get_session() as session:
    det = AnomalyDetector(session, site_id=SITE)
    for i in range(DAYS_BACK):
        d = END - timedelta(days=i)
        found.extend(det.detect_all(d, site_id=SITE))
    session.commit()

print(f"\nTotal REAL anomalies detected (lag-excluded, data-days only): {len(found)}")
for a in sorted(found, key=lambda x: str(x['date']), reverse=True):
    print(f"  {a['date']}  {a['metric_type']:18} actual={a['actual_value']:.2f} base={a['baseline_value']:.2f} dev={a['deviation_pct']}% [{a['severity']}]")

# VERIFY: independently re-derive the daily total for each flagged day
if found:
    print("\n--- VERIFY (independent recompute of daily totals) ---")
    seen = set()
    with get_session() as session:
        for a in found:
            if a["date"] in seen:
                continue
            seen.add(a["date"])
            t = _daily_seo_totals(session, a["date"], a["date"], SITE).get(a["date"])
            print(f"  {a['date']}: clicks={t['clicks']:.0f} impr={t['impressions']:.0f} ctr={t['ctr']:.3f} pos={t['avg_position']:.1f}")
