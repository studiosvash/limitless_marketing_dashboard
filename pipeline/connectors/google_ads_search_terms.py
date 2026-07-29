"""
pipeline/connectors/google_ads_search_terms.py — Google Ads `search_term_view` connector.

Fetches: the real user queries that triggered an ad, per campaign per day.
Writes to: ad_search_terms table (see pipeline/db/schema.py::AdSearchTerm).

Why a sibling file instead of more code inside google_ads.py
------------------------------------------------------------
`search_term_view` is a different GAQL resource with a different grain (query × campaign ×
day, thousands of rows) and a different failure mode from `campaign` (it is subject to its
own reporting restrictions — Google withholds terms below its privacy threshold, and the
resource can 403 independently of campaign reporting). Keeping it separate means:

  * one BaseConnector = one table = one SyncLog row, matching every other connector here.
    A search-term failure records itself as a search-term failure instead of marking the
    campaign-spend sync — the thing the Ads KPIs depend on — as failed.
  * `GoogleAdsConnector.fetch()` keeps returning `list[dict]` for ad_metrics_daily. Folding
    a second table in would have meant switching it to a dict payload, changing an existing
    connector's contract for the benefit of a new one.
  * the sync engine can schedule the two at different cadences later (search terms are far
    heavier than campaign totals) without a flag.

Auth is NOT duplicated: this class subclasses GoogleAdsConnector, so it inherits the exact
same `__init__` credential validation and the exact same `_build_service()` client. With
`GOOGLE_ADS_*` unset, `__init__` raises and the sync engine's connector factory returns
None → the run records a clean skip, exactly as it already does for `google_ads`.
"""

from datetime import date
from typing import Optional

from pipeline.connectors.google_ads import GoogleAdsConnector
from pipeline.db.writer import upsert_ad_search_terms
from pipeline.utils.date_helpers import days_ago, iso
from pipeline.utils.retry import with_retry

# Google reports the *search term's* match type against the keyword it matched. NEAR_EXACT /
# NEAR_PHRASE are Google's own "close variant" of EXACT / PHRASE and are shown as such in the
# Google Ads UI, so they normalise onto the three values the SPA's match-type filter offers.
# Anything else (RSA_HEADLINE, UNKNOWN, UNSPECIFIED, future values) is passed through
# lowercased rather than being forced into one of the three — a real label the user can see
# beats a guessed one.
_MATCH_TYPE_MAP = {
    "EXACT": "exact",
    "NEAR_EXACT": "exact",
    "PHRASE": "phrase",
    "NEAR_PHRASE": "phrase",
    "BROAD": "broad",
}


class GoogleAdsSearchTermsConnector(GoogleAdsConnector):
    name = "google_ads_search_terms"

    @staticmethod
    def _match_type(raw) -> Optional[str]:
        if raw is None:
            return None
        # proto-plus enums stringify as e.g. "SearchTermMatchType.PHRASE"; .name is present
        # on the enum, and a plain str is already the value.
        token = getattr(raw, "name", None) or str(raw).rsplit(".", 1)[-1]
        token = token.strip().upper()
        if not token or token in ("UNSPECIFIED", "UNKNOWN"):
            return None
        return _MATCH_TYPE_MAP.get(token, token.lower())

    @with_retry(max_retries=3, base_delay=5.0)
    def fetch(self, site_id: Optional[str] = None, days: int = 90) -> list[dict]:
        """Fetch search-term rows for the past N days.

        Returns a list of dicts shaped for the ad_search_terms table.
        """
        service = self._build_service()

        start_date = iso(days_ago(days))
        end_date = iso(days_ago(1))

        # segments.keyword.info.text = the keyword the query matched (the SPA's
        # "matchedKeyword" column). cost_micros = USD × 1,000,000.
        # No campaign.status filter: a query that wasted spend on a since-paused campaign is
        # exactly the row the Search Terms page exists to surface, and dropping it would
        # understate wasted spend for the period.
        query = f"""
            SELECT
                search_term_view.search_term,
                segments.keyword.info.text,
                segments.search_term_match_type,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                segments.date
            FROM search_term_view
            WHERE
                segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY segments.date DESC, metrics.cost_micros DESC
        """

        self.logger.info(
            f"[{self.name}] Querying search_term_view {start_date} → {end_date}"
        )
        response = service.search(customer_id=self.customer_id, query=query)

        records = []
        for row in response:
            term = (row.search_term_view.search_term or "").strip()
            if not term:
                # Google withholds low-volume queries; those rows carry no term at all and
                # there is nothing honest to display for them.
                continue

            records.append({
                "date": date.fromisoformat(row.segments.date),
                "term": term,
                "matched_keyword": (row.segments.keyword.info.text or "") or None,
                "match_type": self._match_type(row.segments.search_term_match_type),
                "campaign": row.campaign.name,
                "campaign_id": str(row.campaign.id) if row.campaign.id else None,
                "impressions": int(row.metrics.impressions),
                "clicks": int(row.metrics.clicks),
                "cost": round(row.metrics.cost_micros / 1_000_000, 4),
                "conversions": float(row.metrics.conversions),
            })

        self.logger.info(f"[{self.name}] Fetched {len(records)} search-term-day records")
        return records

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        return upsert_ad_search_terms(session, records, site_id=site_id)


if __name__ == "__main__":
    connector = GoogleAdsSearchTermsConnector()
    rows = connector.fetch(days=30)
    print(f"Fetched {len(rows)} Google Ads search-term records")
    if rows:
        print(f"Sample: {rows[0]}")
