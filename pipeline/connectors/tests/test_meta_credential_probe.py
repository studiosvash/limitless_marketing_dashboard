"""probe_credential -- the live-probe function backing the Settings 'Test connection'
button for Meta Ads. Network is always mocked here."""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from pipeline.connectors.meta import probe_credential


class ProbeCredentialTests(TestCase):
    @patch("pipeline.connectors.meta.requests.get")
    def test_ok_when_graph_api_returns_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"name": "Acme Ads"})
        ok, detail = probe_credential("tok123", "act_999")
        self.assertTrue(ok)
        self.assertIn("Acme Ads", detail)

    @patch("pipeline.connectors.meta.requests.get")
    def test_fail_when_graph_api_rejects(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=400, json=lambda: {"error": {"message": "Invalid OAuth access token"}},
        )
        ok, detail = probe_credential("bad-tok", "act_999")
        self.assertFalse(ok)
        self.assertIn("Invalid OAuth access token", detail)

    @patch(
        "pipeline.connectors.meta.requests.get",
        side_effect=Exception(
            "connection failed to https://graph.facebook.com/v18.0/act_999"
            "?fields=name&access_token=SECRET123"
        ),
    )
    def test_fail_when_network_error(self, mock_get):
        ok, detail = probe_credential("SECRET123", "act_999")
        self.assertFalse(ok)
        # The detail string must never carry the token (or any other raw exception
        # text) -- it is both returned to the browser and persisted unencrypted via
        # record_test_result. Only the exception type name is surfaced.
        self.assertNotIn("SECRET123", detail)
        self.assertIn("Exception", detail)
