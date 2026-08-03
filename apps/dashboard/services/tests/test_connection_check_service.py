"""The wrapper functions backing POST /api/projects/<slug>/ads-credentials/test. The
underlying live probes (pipeline.connectors.{google_ads,meta}.probe_credential) are mocked
here -- their own network behaviour is covered in pipeline/connectors/tests/."""
from unittest.mock import patch

from django.test import TestCase

from apps.dashboard.services.connection_check_service import (
    test_google_ads_credential, test_meta_ads_credential,
)


class TestGoogleAdsCredentialTests(TestCase):
    def test_missing_required_fields_short_circuits_without_a_network_call(self):
        result = test_google_ads_credential({"developer_token": ""})
        self.assertFalse(result["ok"])
        self.assertIn("required", result["detail"])

    @patch("pipeline.connectors.google_ads.probe_credential", return_value=(True, "Verified"))
    def test_delegates_to_the_live_probe(self, mock_probe):
        result = test_google_ads_credential({
            "developer_token": "tok", "customer_id": "123-456-7890",
        })
        self.assertEqual(result, {"ok": True, "detail": "Verified"})
        mock_probe.assert_called_once_with("tok", "1234567890", None)


class TestMetaAdsCredentialTests(TestCase):
    def test_missing_required_fields_short_circuits_without_a_network_call(self):
        result = test_meta_ads_credential({"access_token": "tok"})
        self.assertFalse(result["ok"])
        self.assertIn("required", result["detail"])

    @patch("pipeline.connectors.meta.probe_credential", return_value=(True, "Verified"))
    def test_delegates_to_the_live_probe(self, mock_probe):
        result = test_meta_ads_credential({
            "access_token": "tok", "ad_account_id": "act_999",
        })
        self.assertEqual(result, {"ok": True, "detail": "Verified"})
        mock_probe.assert_called_once_with("tok", "act_999")
