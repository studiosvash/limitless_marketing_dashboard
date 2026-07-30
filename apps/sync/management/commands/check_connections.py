"""Probe every external integration and print what actually works.

    python manage.py check_connections              # every active site
    python manage.py check_connections fusehealth   # one site by slug
    python manage.py check_connections --core-only  # skip PageSpeed / OpenAI / Google Ads

Answers "are all the APIs working?" with evidence instead of inference. Before this, the only
way to find out was to start a 20-30 minute sync and read the wreckage: a connector whose
credentials are missing fails to construct, `sync_engine._get_connector` returns None, and the
run is still reported as SUCCESS with no SyncLog row at all -- so a completely dead integration
looked identical to one that had simply never been asked to run.

Exit code 1 if any CORE integration (GSC / GA4 / DataForSEO) reports a hard failure for any
site, so this is usable as a post-deploy smoke check. An `absent` integration is NOT a failure:
choosing not to connect GA4 for a site is legitimate.
"""
from django.core.management.base import BaseCommand

from apps.dashboard.services.connection_check_service import (
    STATE_ABSENT, STATE_FAIL, STATE_OK, STATE_UNKNOWN, check_connections,
)

MARK = {STATE_OK: "OK   ", STATE_FAIL: "FAIL ", STATE_ABSENT: "-    ", STATE_UNKNOWN: "?    "}


class Command(BaseCommand):
    help = "Live-probe GSC, GA4, DataForSEO (and optionally PageSpeed/OpenAI/Google Ads) per site."

    def add_arguments(self, parser):
        parser.add_argument("slug", nargs="?", help="Check only this site (Site.slug).")
        parser.add_argument("--core-only", action="store_true",
                            help="Only GSC, GA4 and DataForSEO.")

    def handle(self, *args, **options):
        from pipeline.services.site_service import list_sites

        sites = list_sites(active_only=True)
        if options["slug"]:
            sites = [s for s in sites if s.slug == options["slug"]]
            if not sites:
                self.stderr.write(self.style.ERROR(f"No active site with slug {options['slug']!r}."))
                return

        if not sites:
            self.stdout.write("No active sites to check.")
            return

        any_fail = False
        for site in sites:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"{site.site_name or site.slug}  ({site.site_url})"
            ))
            result = check_connections(
                domain=site.site_url,
                gsc_property=site.gsc_property,
                ga4_property_id=site.ga4_property_id,
                dataforseo_target=site.dataforseo_target_domain,
                include_optional=not options["core_only"],
            )
            for c in result["checks"]:
                style = {
                    STATE_OK: self.style.SUCCESS,
                    STATE_FAIL: self.style.ERROR,
                }.get(c["state"], self.style.WARNING)
                self.stdout.write(
                    f"  {style(MARK.get(c['state'], '?    '))} {c['label']:<24} {c['detail']}"
                )
                if c["id"] == "gsc" and c["state"] == STATE_FAIL and c.get("options"):
                    self.stdout.write("        Properties this account CAN query:")
                    for opt in c["options"]:
                        self.stdout.write(f"          · {opt}")
            if not result["ok"]:
                any_fail = True

        self.stdout.write("")
        self.stdout.write("Legend: OK = probed and working · FAIL = probed and broken · "
                          "- = not configured · ? = configured, not probed (no free check)")
        if any_fail:
            # Raising SystemExit rather than CommandError: this is a check result, not a usage
            # error, so it should not print a traceback-style message.
            self.stderr.write(self.style.ERROR(
                "\nOne or more core integrations (GSC / GA4 / DataForSEO) are FAILING."
            ))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("No core integration is failing."))
