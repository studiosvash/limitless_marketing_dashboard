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


class GA4ResolveSiblingProjectTests(TestCase):
    """One domain registered as several projects (18 premierstaff.com city projects) is ONE
    GA4 property: the traffic is the domain's, whichever city project the run belongs to.

    Live server, 2026-09-01: the property was stored on exactly one of the 18 rows (Denver),
    `_resolve_site` looked the domain up by site_url and got the first sibling -- blank -- so
    every scheduled organic run since 5 Aug ended "No GA4 property configured" while the
    property sat one row over. Resolution order: the run's own project row, then any sibling
    on the same domain that has a property. Never another domain (see the env-fallback bug
    the class above pins).
    """

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
            blank = Site(site_url="shared.com", slug="shared-charlotte", is_active=1,
                         ga4_property_id=None)
            holder = Site(site_url="shared.com", slug="shared-denver", is_active=1,
                          ga4_property_id="318744602")
            other = Site(site_url="other.com", slug="other", is_active=1,
                         ga4_property_id="777777777")
            session.add_all([blank, holder, other])
            session.flush()
            self.blank_pk, self.holder_pk = blank.id, holder.id

    def _connector(self, site_pk=None):
        connector = GA4Connector()
        connector._default_property_id = "999999999"  # env default must never leak in
        connector.site_pk = site_pk                    # what sync_engine attaches per run
        return connector

    def test_the_runs_own_project_row_wins_when_it_has_a_property(self):
        self.assertEqual(self._connector(self.holder_pk)._resolve_site("shared.com"),
                         ("shared.com", "318744602"))

    def test_a_blank_project_row_borrows_a_siblings_property_on_the_same_domain(self):
        self.assertEqual(self._connector(self.blank_pk)._resolve_site("shared.com"),
                         ("shared.com", "318744602"))

    def test_a_domain_lookup_with_no_project_borrows_a_sibling_too(self):
        """The legacy path (no site_pk on the run) used to stop at whichever row came first."""
        self.assertEqual(self._connector()._resolve_site("shared.com"),
                         ("shared.com", "318744602"))

    def test_a_property_is_never_borrowed_from_another_domain(self):
        with get_session() as session:
            session.add(Site(site_url="lonely.com", slug="lonely", is_active=1,
                             ga4_property_id=None))
        self.assertEqual(self._connector()._resolve_site("lonely.com"), ("lonely.com", ""))
