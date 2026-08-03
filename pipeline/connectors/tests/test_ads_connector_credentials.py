"""DB-saved credentials override .env, and .env is still the fallback when nothing is
saved for a site. See docs/superpowers/specs/2026-08-03-ads-credentials-design.md."""
import os
from unittest.mock import patch

from django.test import TestCase

from pipeline.connectors.google_ads import GoogleAdsConnector
from pipeline.connectors.meta import MetaConnector


class GoogleAdsCredentialOverrideTests(TestCase):
    @patch.dict(os.environ, {
        "GOOGLE_ADS_CUSTOMER_ID": "1112223333", "GOOGLE_ADS_DEVELOPER_TOKEN": "env-token",
    })
    def test_falls_back_to_env_when_no_override_given(self):
        conn = GoogleAdsConnector()
        self.assertEqual(conn.developer_token, "env-token")
        self.assertEqual(conn.customer_id, "1112223333")

    @patch.dict(os.environ, {
        "GOOGLE_ADS_CUSTOMER_ID": "1112223333", "GOOGLE_ADS_DEVELOPER_TOKEN": "env-token",
    })
    def test_db_credentials_override_env(self):
        conn = GoogleAdsConnector(credentials={
            "developer_token": "db-token", "customer_id": "999-888-7777",
        })
        self.assertEqual(conn.developer_token, "db-token")
        self.assertEqual(conn.customer_id, "9998887777")  # dashes stripped, same as env path

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_when_neither_db_nor_env_has_credentials(self):
        with self.assertRaises(ValueError):
            GoogleAdsConnector()


class MetaCredentialOverrideTests(TestCase):
    @patch.dict(os.environ, {"META_ACCESS_TOKEN": "env-tok", "META_AD_ACCOUNT_ID": "act_env"})
    def test_falls_back_to_env_when_no_override_given(self):
        conn = MetaConnector()
        self.assertEqual(conn.access_token, "env-tok")

    @patch.dict(os.environ, {"META_ACCESS_TOKEN": "env-tok", "META_AD_ACCOUNT_ID": "act_env"})
    def test_db_credentials_override_env(self):
        conn = MetaConnector(credentials={"access_token": "db-tok", "ad_account_id": "act_db"})
        self.assertEqual(conn.access_token, "db-tok")
        self.assertEqual(conn.ad_account_id, "act_db")
