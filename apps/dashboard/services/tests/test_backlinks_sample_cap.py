"""The Backlinks response must say whether `links` is everything we hold or a truncated sample.

The page pages over `links` in the browser and prints a "showing X-Y of Z" counter. Z is the
number of rows the response carried, which equals the number of stored links only while that
number is under the cap. Above it, Z is the cap — and a counter that states it without saying
so invites the reader to take a truncated sample for the whole profile, which is the same
defect class as the old "Showing 12 of 729" line this replaced.

There is deliberately no server-side paging. Two reasons, both recorded on LINKS_LIMIT itself:
1000 rows is nothing at this scale, and `query_referring_domains_raw` rolls up the SAME
in-memory list, so paging the backend would silently shrink the referring-domain rollup with
nothing in the response to reveal it.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

import pipeline.utils.db_connection as db_connection
from pipeline.db.engine import get_engine
from pipeline.db.schema import Backlink, init_db
from pipeline.utils.db_connection import get_session

SITE = "sc-domain:example.com"


class LinksSampleCapTests(TestCase):
    def _seed(self, count):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
        init_db(get_engine(db_path))
        ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        ctx.enable()
        self.addCleanup(ctx.disable)
        with get_session() as session:
            session.add_all([
                Backlink(site_id=SITE, referring_domain="blog.com",
                         target_url="https://example.com/",
                         url_from=f"https://blog.com/post-{i}",
                         anchor=f"a{i}", status="live", dofollow=1, domain_rank=500 - i)
                for i in range(count)
            ])

    def test_a_profile_under_the_cap_is_not_reported_as_truncated(self):
        from apps.dashboard.services.backlinks_service import build_backlinks_response
        self._seed(25)
        resp = build_backlinks_response(SITE)
        self.assertEqual(len(resp["links"]), 25)
        self.assertFalse(resp["linksCapped"])
        self.assertEqual(resp["linksLimit"], 1000)

    def test_one_referring_domain_can_now_contribute_many_rows(self):
        """Under the old three-column unique key these 25 rows could not have been stored at
        all: same domain, same target, so they collapsed to one."""
        from apps.dashboard.services.backlinks_service import (
            build_backlinks_response, query_referring_domains_raw)
        self._seed(25)
        resp = build_backlinks_response(SITE)
        self.assertEqual(len({l["url_from"] for l in resp["links"]}), 25)
        rollup = query_referring_domains_raw(SITE, links=resp["links"])
        self.assertEqual(len(rollup), 1)
        self.assertEqual(rollup[0]["backlinks"], 25)

    def test_hitting_the_cap_is_reported_so_the_counter_can_say_so(self):
        from apps.dashboard.services.backlinks_service import (
            LINKS_LIMIT, build_backlinks_response)
        self._seed(LINKS_LIMIT + 5)
        resp = build_backlinks_response(SITE)
        self.assertEqual(len(resp["links"]), LINKS_LIMIT)
        self.assertTrue(resp["linksCapped"])
