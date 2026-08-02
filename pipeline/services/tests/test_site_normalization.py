"""One domain, one project — `add_site` must not accept the same site twice.

The bug, reported 2026-08-02 with a screenshot of the project switcher: adding
`premierstaff.com` and then `www.premierstaff.com` produced TWO projects. `add_site`'s duplicate
guard compared `_bare_domain()`, which stripped `https://`, `http://`, `sc-domain:` and a
trailing slash — but not a leading `www.`. Two projects meant two slugs, two sync budgets, two
halves of one site's history, and a switcher that offered the user a choice between them with no
way to tell which was real.

`sites.site_url` is the string that joins the two databases (`.claude/skills.md` §3), so the fix
has to land at the single point of registration: normalise on the way in, and compare the
normalised form.
"""
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from sqlalchemy import select

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.services.site_service import add_site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


SPELLINGS = [
    "https://premierstaff.com",
    "http://premierstaff.com",
    "https://www.premierstaff.com",
    "http://www.premierstaff.com",
    "premierstaff.com",
    "www.premierstaff.com",
]


def _new_analytics_db(test_case):
    db_connection._SessionFactory = None
    test_case.addCleanup(setattr, db_connection, "_SessionFactory", None)
    db_path = str(Path(tempfile.mkdtemp()) / "fusehealth.db")
    init_db(get_engine(db_path))
    ctx = override_settings(ANALYTICS_DB_PATH=db_path)
    ctx.enable()
    test_case.addCleanup(ctx.disable)


class AddSiteNormalisesTheDomainTests(TestCase):
    def setUp(self):
        _new_analytics_db(self)

    def test_every_spelling_is_stored_as_the_same_bare_domain(self):
        for raw in SPELLINGS:
            with self.subTest(raw=raw):
                _new_analytics_db(self)
                add_site(site_url=raw)
                with get_session() as session:
                    site = session.execute(select(Site)).scalars().one()
                    self.assertEqual(site.site_url, "premierstaff.com")

    def test_a_second_spelling_of_the_same_site_is_refused(self):
        add_site(site_url="premierstaff.com")
        for raw in SPELLINGS:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError) as ctx:
                    add_site(site_url=raw)
                self.assertIn("already exists", str(ctx.exception))

        with get_session() as session:
            self.assertEqual(len(session.execute(select(Site)).scalars().all()), 1)

    def test_www_first_then_bare_is_refused_too(self):
        # The reported order: the www spelling was added first.
        add_site(site_url="www.premierstaff.com")
        with self.assertRaises(ValueError):
            add_site(site_url="https://premierstaff.com/")

    def test_an_existing_row_stored_with_www_still_blocks_the_bare_form(self):
        # A project registered before this rule existed keeps its `www.` site_url until
        # `manage.py normalize_site_urls` runs. It must still be recognised as the same site.
        with get_session() as session:
            session.add(Site(site_url="www.eventstaff.com", site_name="Event Staff",
                             slug="event-staff", is_active=1))
        with self.assertRaises(ValueError) as ctx:
            add_site(site_url="eventstaff.com")
        self.assertIn("www.eventstaff.com", str(ctx.exception))

    def test_a_genuinely_different_subdomain_is_a_different_site(self):
        # Only `www.` is folded away. blog.x.com is a real, separate host.
        add_site(site_url="premierstaff.com")
        add_site(site_url="blog.premierstaff.com")
        with get_session() as session:
            urls = {s.site_url for s in session.execute(select(Site)).scalars().all()}
        self.assertEqual(urls, {"premierstaff.com", "blog.premierstaff.com"})

    def test_dataforseo_target_is_normalised_but_gsc_property_is_left_alone(self):
        # dataforseo_target_domain is a bare domain by contract. gsc_property is a Search
        # Console property identifier — the account may genuinely own the www URL-prefix
        # property, so normalising it would break the very lookup it exists for.
        add_site(
            site_url="https://www.premierstaff.com/",
            gsc_property="https://www.premierstaff.com/",
            dataforseo_target_domain="https://www.premierstaff.com/",
        )
        with get_session() as session:
            site = session.execute(select(Site)).scalars().one()
        self.assertEqual(site.site_url, "premierstaff.com")
        self.assertEqual(site.dataforseo_target_domain, "premierstaff.com")
        self.assertEqual(site.gsc_property, "https://www.premierstaff.com/")

    def test_input_with_no_readable_domain_is_refused_not_stored_empty(self):
        # An empty join key would match nothing and read as "this site has no data".
        for raw in ["", "   ", "https://", "sc-domain:"]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    add_site(site_url=raw)
