"""apps/api/tests/test_ads_credentials.py -- POST /api/projects/<slug>/ads-credentials/test."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection

SITE_URL = "sc-domain:fusehealth.com"


def _bootstrap(test_case):
    """Same recipe as test_settings.py's _bootstrap_settings_test_env -- kept as its own
    copy per this project's test-file convention (see that file's docstring)."""
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)

    with get_session() as session:
        session.add(Site(site_url=SITE_URL, site_name="FuseHealth",
                          slug="fusehealth", is_active=1))

    user = get_user_model().objects.create_user("founder1", password="x")
    token = Token.objects.get(user=user)
    client_auth = APIClient()
    client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client_auth


class AdsCredentialTestEndpointTests(APITestCase):
    def setUp(self):
        self.client_auth = _bootstrap(self)

    @patch("apps.dashboard.services.connection_check_service.test_meta_ads_credential",
          return_value={"ok": True, "detail": "Verified"})
    def test_tests_typed_in_fields_without_saving(self, mock_test):
        resp = self.client_auth.post("/api/projects/fusehealth/ads-credentials/test", {
            "platform": "meta_ads", "access_token": "tok", "ad_account_id": "act_999",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "detail": "Verified"})
        mock_test.assert_called_once()

    def test_use_saved_with_nothing_saved_reports_ok_false(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ads-credentials/test", {
            "platform": "google_ads", "useSaved": True,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["ok"])

    def test_invalid_platform_is_a_400(self):
        resp = self.client_auth.post("/api/projects/fusehealth/ads-credentials/test", {
            "platform": "tiktok_ads",
        })
        self.assertEqual(resp.status_code, 400)
