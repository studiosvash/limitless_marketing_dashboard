"""GA4 property resolution — regression for the cross-site fallback bug.

2026-07-15: a newly added site (eventstaff.com) had no ga4_property_id, and _resolve_site
fell back to the .env GA4_PROPERTY_ID — which belongs to the PRIMARY site — silently writing
6,654 of the primary site's GA4 rows under the new site's id. A Site row without its own
property must resolve to "" so fetch() fails loudly instead of fetching someone else's data.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from pipeline.connectors.ga4 import GA4Connector
from pipeline.db.engine import get_engine
from pipeline.db.schema import Site, init_db
from pipeline.utils.db_connection import get_session


class GA4ResolveSiteTests(TestCase):
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
            session.add(Site(site_url="primary.com", slug="primary", is_active=1,
                             ga4_property_id="111111111"))
            session.add(Site(site_url="newsite.com", slug="newsite", is_active=1,
                             ga4_property_id=None))

    def test_site_with_own_property_resolves_it(self):
        connector = GA4Connector()
        connector._default_property_id = "999999999"  # env default must be ignored
        self.assertEqual(connector._resolve_site("primary.com"), ("primary.com", "111111111"))

    def test_site_without_property_never_falls_back_to_env(self):
        connector = GA4Connector()
        connector._default_property_id = "999999999"  # the primary site's env property
        site_url, prop = connector._resolve_site("newsite.com")
        self.assertEqual(site_url, "newsite.com")
        self.assertEqual(prop, "")  # "" -> fetch() raises a clear error, writes nothing
