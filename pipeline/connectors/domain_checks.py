"""
pipeline/connectors/domain_checks.py — Domain Checks Connector.

Probes the site itself (no third-party API, no credentials, no metered call) for the six
facts the Site Audit page's "Domain Checks" card shows:

    SSL certificate · sitemap.xml · robots.txt · HTTP/2 · www redirect · llms.txt

WHY THIS IS A CONNECTOR
-----------------------
The probes used to run only as a side effect inside `sync_engine._run_post_sync`, gated on
`_AUDIT_SNAPSHOT_INPUTS` (url_inspection / pagespeed / dataforseo_onpage). That had two costs:

  * **The card's own button could not be cheap.** "Run a Crawl Now" in the Domain Checks empty
    state had to fire scope='audit' — four connectors, 20-30 minutes, including the
    long-polling and metered DataForSEO OnPage crawl — to record six local HTTP requests that
    take about four seconds together.
  * **It was invisible.** A side effect writes no SyncLog row, so it had no step in the refresh
    checklist, no duration, no record count, and a failed probe looked exactly like a
    successful one.

As a connector it is a normal step like every other: `BaseConnector.sync` writes the
running/success/error SyncLog row, the SPA's checklist renders it, and it can be scoped on its
own (`domain_checks`) or run as part of `audit` and `all`.

Writes to: mutation state (`domainChecksCache`), via
`apps.dashboard.services.site_audit_service.store_domain_checks`. Nothing in the analytics DB —
these are six booleans about the domain, not time series, so `_write_records` ignores its
session argument.
"""

from typing import Optional

from pipeline.connectors.base import BaseConnector


class DomainChecksConnector(BaseConnector):
    name = "domain_checks"

    def fetch(self, site_id: Optional[str] = None, **kwargs) -> list[dict]:
        """Six parallel probes against the site. Raises if the probe machinery fails.

        The import is local and deliberately late: this connector lives in `pipeline/` but the
        probe helpers are a Django app service, and importing `apps.*` at module scope would
        make the connector registry depend on Django app loading. `_run_post_sync` already
        imported this module the same way.
        """
        from apps.dashboard.services.site_audit_service import probe_domain_checks
        return probe_domain_checks(site_id or "")

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Store the probe results as this project's domain-check state.

        `session` is the analytics SQLAlchemy session BaseConnector opens for every connector;
        it is unused here because domain checks are project state, not analytics rows.
        """
        from apps.dashboard.services.site_audit_service import store_domain_checks
        return store_domain_checks(site_id or "", records)
