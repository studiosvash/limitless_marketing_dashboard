"""`DELETE /api/projects/<slug>/keywords` — untracking one keyword (P11).

`saved_keyword_service.delete_saved_keyword` was written, documented and correct, and had
ZERO callers and no route. The only way to untrack a keyword was the bulk `PUT`, i.e. re-sending
the entire list minus one — through the Edit Project modal, which is also where a location
change and a duplicate-name clash live. Removing one keyword meant opening a modal that rewrites
five other fields.

`saved_keywords` is the table that decides DataForSEO spend, so removing a row is exactly the
kind of thing a user should be able to do directly.
"""
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase
from sqlalchemy import select

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import SavedKeyword, Site, init_db
from pipeline.utils.db_connection import get_session

LOC = "United States - Washington, DC"


class KeywordDeleteTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff DC",
                             slug="staff-dc", location=LOC, is_active=1))
            session.add(Site(site_url="premierstaff.com", site_name="Premierstaff NY",
                             slug="staff-ny", location="United States - New York",
                             is_active=1))
            for kw in ("event staffing", "brand ambassadors"):
                session.add(SavedKeyword(site_id="premierstaff.com", site_pk=1, keyword=kw,
                                         location=LOC))
            # The sibling project tracks the same phrase, in its own market.
            session.add(SavedKeyword(site_id="premierstaff.com", site_pk=2,
                                     keyword="event staffing",
                                     location="United States - New York"))

        user = get_user_model().objects.create_user("deluser", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def _tracked(self, site_pk):
        with get_session() as session:
            return sorted(session.execute(
                select(SavedKeyword.keyword).where(SavedKeyword.site_pk == site_pk)
            ).scalars().all())

    def _delete(self, slug, body):
        return self.client_auth.delete(f"/api/projects/{slug}/keywords", body, format="json")

    def test_it_removes_the_keyword(self):
        resp = self._delete("staff-dc", {"keyword": "event staffing"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(resp.json()["deleted"], True)
        self.assertEqual(self._tracked(1), ["brand ambassadors"])

    def test_it_leaves_the_sibling_projects_copy_alone(self):
        """`saved_keywords` is keyed by project; two projects may track one phrase."""
        self._delete("staff-dc", {"keyword": "event staffing"})
        self.assertEqual(self._tracked(2), ["event staffing"])

    def test_it_is_idempotent(self):
        self._delete("staff-dc", {"keyword": "event staffing"})
        resp = self._delete("staff-dc", {"keyword": "event staffing"})
        self.assertEqual(resp.status_code, 200,
                         "the SPA fires these in parallel; a second call is not an error")
        self.assertEqual(resp.json()["deleted"], False,
                         "but it reports honestly that there was nothing to remove")

    def test_a_missing_keyword_is_a_400(self):
        resp = self._delete("staff-dc", {})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.json())
        self.assertEqual(self._tracked(1), ["brand ambassadors", "event staffing"])

    def test_a_blank_keyword_is_a_400(self):
        self.assertEqual(self._delete("staff-dc", {"keyword": "   "}).status_code, 400)

    def test_unknown_slug_is_404(self):
        self.assertEqual(self._delete("nope", {"keyword": "x"}).status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().delete("/api/projects/staff-dc/keywords",
                                  {"keyword": "event staffing"}, format="json")
        self.assertEqual(resp.status_code, 401,
                         "without @login_not_required this would be a 302 to the login page")
