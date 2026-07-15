"""Fetch DataForSEO Backlinks aggregates for a project and store the page snapshot.

Usage:
    python manage.py refresh_backlinks <slug> [--target domain.com]

This is the Backlinks page's Refresh path: it calls DataForSEO (metered) and overwrites the
stored snapshot the API reads. `--target` overrides the domain queried (defaults to the site's
own domain, falling back to DATAFORSEO_TARGET_DOMAIN).
"""
import os

from django.core.management.base import BaseCommand, CommandError
from sqlalchemy import select

from pipeline.db.schema import Site
from pipeline.services.backlinks_service import refresh_backlinks, _clean_domain
from pipeline.utils.db_connection import get_session


class Command(BaseCommand):
    help = "Fetch DataForSEO backlinks aggregates and cache the Backlinks-page snapshot."

    def add_arguments(self, parser):
        parser.add_argument("slug", help="Project slug (e.g. 'fusehealth')")
        parser.add_argument("--target", default=None, help="Domain to query (defaults to the site's domain)")

    def handle(self, *args, **opts):
        slug = opts["slug"]
        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
            if not site:
                raise CommandError(f"No project with slug '{slug}'")
            site_url = site.site_url

        target = opts["target"] or _clean_domain(site_url) or os.getenv("DATAFORSEO_TARGET_DOMAIN", "")
        if not target:
            raise CommandError("Could not resolve a target domain; pass --target.")

        self.stdout.write(f"Fetching backlinks for {target} …")
        payload = refresh_backlinks(site_url, target)
        s = payload["summary"]
        self.stdout.write(self.style.SUCCESS(
            f"Saved snapshot for {slug}: AS {s['authorityScore']}, "
            f"{s['refDomains']} referring domains, {s['backlinks']} backlinks."
        ))
