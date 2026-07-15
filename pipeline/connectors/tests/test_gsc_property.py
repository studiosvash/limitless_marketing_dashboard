"""GSC property auto-match (gsc_property.py) — regression for the eventstaff.com 403s.

add_site stores gsc_property as a bare domain ("eventstaff.com"); the GSC API reads that as
the URL-prefix property "http://eventstaff.com" and 403s even though the account owns
"sc-domain:eventstaff.com". resolve_gsc_property must match the stored value against the
account's real property list, repair the Site row, and raise ONE actionable error when the
account truly has no access.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from pipeline.connectors.gsc_property import resolve_gsc_property
from pipeline.db.engine import get_engine
from pipeline.db.schema import Site, init_db
from pipeline.utils.db_connection import get_session


class FakeService:
    """Stands in for the searchconsole discovery client: sites().list().execute()."""

    def __init__(self, site_urls):
        self._entries = [{"siteUrl": u, "permissionLevel": "siteOwner"} for u in site_urls]

    def sites(self):
        return self

    def list(self):
        return self

    def execute(self):
        return {"siteEntry": self._entries}


class ResolveGscPropertyTests(TestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        with get_session() as session:
            session.add(Site(site_url="eventstaff.com", slug="eventstaff", is_active=1,
                             gsc_property="eventstaff.com"))

    def test_exact_stored_match_is_returned_unchanged(self):
        service = FakeService(["sc-domain:fusehealth.com"])
        self.assertEqual(
            resolve_gsc_property("x", "sc-domain:fusehealth.com", service),
            "sc-domain:fusehealth.com",
        )

    def test_bare_domain_matches_domain_property_and_repairs_site_row(self):
        service = FakeService(["sc-domain:eventstaff.com", "https://eventstaff.com/"])
        resolved = resolve_gsc_property("eventstaff.com", "eventstaff.com", service)
        self.assertEqual(resolved, "sc-domain:eventstaff.com")

        with get_session() as session:
            site = session.query(Site).filter_by(site_url="eventstaff.com").one()
            self.assertEqual(site.gsc_property, "sc-domain:eventstaff.com")

    def test_bare_domain_falls_back_to_url_prefix_property(self):
        service = FakeService(["https://eventstaff.com/"])
        self.assertEqual(
            resolve_gsc_property("eventstaff.com", "eventstaff.com", service),
            "https://eventstaff.com/",
        )

    def test_no_access_raises_actionable_error(self):
        service = FakeService(["sc-domain:fusehealth.com"])
        with self.assertRaises(ValueError) as ctx:
            resolve_gsc_property("eventstaff.com", "eventstaff.com", service)
        self.assertIn("no Search Console access to 'eventstaff.com'", str(ctx.exception))
        self.assertIn("sc-domain:fusehealth.com", str(ctx.exception))
