"""Tests for the `domain_checks` connector.

The six probes (SSL, sitemap.xml, robots.txt, HTTP/2, www redirect, llms.txt) used to be a
side effect buried in `sync_engine._run_post_sync`. Making them a connector is what lets the
Domain Checks card refresh itself for ~4 seconds instead of buying a 20-30 minute Site Audit
crawl — and it is also what gives them a SyncLog row, so a failed probe is visible instead of
silently indistinguishable from a successful one.

Nothing here touches the network: `probe_domain_checks` is patched in every test.
"""
from unittest.mock import patch

from django.test import TestCase

from apps.sync.models import SyncLog
from pipeline.connectors.domain_checks import DomainChecksConnector

SITE_URL = "sc-domain:fusehealth.com"

CHECKS = [
    {"label": "SSL certificate", "detail": "Valid", "ok": True},
    {"label": "Sitemap.xml", "detail": "/sitemap.xml", "ok": True},
    {"label": "Robots.txt", "detail": "12 rules", "ok": True},
    {"label": "HTTP/2", "detail": "Protocol support", "ok": True},
    {"label": "WWW redirect", "detail": "Unified", "ok": True},
    {"label": "llms.txt", "detail": "Missing", "ok": False},
]


class DomainChecksConnectorTests(TestCase):
    def test_sync_stores_the_probe_results_and_reports_the_count(self):
        from apps.dashboard.services.site_audit_service import stored_domain_checks

        with patch("apps.dashboard.services.site_audit_service.probe_domain_checks",
                   return_value=CHECKS):
            result = DomainChecksConnector().sync(site_id=SITE_URL)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["records_written"], 6)
        self.assertEqual(stored_domain_checks(SITE_URL), CHECKS)

    def test_sync_writes_a_synclog_row(self):
        """Without this row the connector has no step in the refresh checklist -- which is
        precisely the invisibility the old post-sync side effect had."""
        with patch("apps.dashboard.services.site_audit_service.probe_domain_checks",
                   return_value=CHECKS):
            DomainChecksConnector().sync(site_id=SITE_URL)

        log = SyncLog.objects.get(connector="domain_checks", site_url=SITE_URL)
        self.assertEqual(log.status, "success")
        self.assertEqual(log.records_written, 6)
        self.assertIsNotNone(log.last_synced)

    def test_a_failed_probe_is_reported_as_an_error_not_a_silent_success(self):
        with patch("apps.dashboard.services.site_audit_service.probe_domain_checks",
                   side_effect=RuntimeError("DNS lookup failed")):
            result = DomainChecksConnector().sync(site_id=SITE_URL)

        self.assertEqual(result["status"], "error")
        self.assertIn("DNS lookup failed", result["error"])
        log = SyncLog.objects.get(connector="domain_checks", site_url=SITE_URL)
        self.assertEqual(log.status, "error")

    def test_an_empty_probe_result_never_blanks_previously_stored_checks(self):
        """`stored_domain_checks` cannot tell "probed, found nothing" from "never probed", and
        the SPA renders the latter as the "No domain checks recorded yet" empty state. A run
        that came back with nothing must not send a populated card back to that screen."""
        from apps.dashboard.services.site_audit_service import stored_domain_checks

        with patch("apps.dashboard.services.site_audit_service.probe_domain_checks",
                   return_value=CHECKS):
            DomainChecksConnector().sync(site_id=SITE_URL)
        with patch("apps.dashboard.services.site_audit_service.probe_domain_checks",
                   return_value=[]):
            result = DomainChecksConnector().sync(site_id=SITE_URL)

        self.assertEqual(result["records_written"], 0)
        self.assertEqual(stored_domain_checks(SITE_URL), CHECKS)

    def test_the_connector_is_reachable_through_the_engine_registry(self):
        """PAGE_CONNECTORS naming a connector the factory cannot build is a silent skip, which
        would make the domain_checks scope a no-op that still reports success."""
        from pipeline.services.sync_engine import _get_connector

        connector = _get_connector("domain_checks")
        self.assertIsNotNone(connector)
        self.assertEqual(connector.name, "domain_checks")
