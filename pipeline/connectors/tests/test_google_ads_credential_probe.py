"""probe_credential -- the live-probe function backing the Settings 'Test connection'
button for Google Ads. Network is always mocked here; see test_ads_connector_credentials.py
for the constructor override/fallback behaviour."""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from pipeline.connectors.google_ads import probe_credential


class ProbeCredentialTests(TestCase):
    @patch("google.ads.googleads.client.GoogleAdsClient")
    def test_ok_when_search_succeeds(self, mock_client_cls):
        mock_service = MagicMock()
        mock_service.search.return_value = iter([MagicMock()])
        mock_client_cls.load_from_dict.return_value.get_service.return_value = mock_service

        ok, detail = probe_credential("dev-token", "1234567890")
        self.assertTrue(ok)
        self.assertIn("1234567890", detail)

    @patch("google.ads.googleads.client.GoogleAdsClient")
    def test_fail_when_sdk_raises(self, mock_client_cls):
        mock_client_cls.load_from_dict.side_effect = Exception("401 Unauthenticated")

        ok, detail = probe_credential("bad-token", "1234567890")
        self.assertFalse(ok)
        self.assertIn("401 Unauthenticated", detail)
