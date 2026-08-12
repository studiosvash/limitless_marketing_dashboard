from rest_framework import serializers


class ProjectSerializer(serializers.Serializer):
    """Shapes a pipeline.db.schema.Site row to HANDOFF_SPEC.md's project object:
    {id, domain, name, vertical, location}. `id` is the slug (matches the frontend
    fixtures' convention, e.g. 'fusehealth'), not the internal integer PK."""
    id = serializers.CharField(source="slug")
    domain = serializers.SerializerMethodField()
    name = serializers.CharField(source="site_name")
    vertical = serializers.CharField(allow_null=True)
    location = serializers.CharField(allow_null=True)
    tracked_keywords_count = serializers.SerializerMethodField()
    avg_position = serializers.SerializerMethodField()
    visibility = serializers.SerializerMethodField()
    improved_count = serializers.SerializerMethodField()
    declined_count = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()

    def get_domain(self, site) -> str:
        from pipeline.services.site_service import _bare_domain
        return _bare_domain(site.site_url)

    def _pos_summary(self, site) -> dict:
        if hasattr(site, "_pos_summary_cache"):
            return site._pos_summary_cache
        try:
            from pipeline.utils.keywords import load_tracked_keywords
            # Scoped to THIS project by its primary key — several projects can share one
            # site_url, and an unscoped list gives a new project its siblings' keywords, so its
            # card in the project switcher advertises a tracked count it does not have.
            project_location = (getattr(site, "location", "") or "").strip() or None
            tracked_kws = load_tracked_keywords(site.site_url, location=project_location,
                                                site_pk=getattr(site, "id", None))
            if not tracked_kws:
                summary = {"tracked": 0, "avg_pos": 0.0, "visibility": None, "improved": 0, "declined": 0, "last_updated": "No sync yet"}
                site._pos_summary_cache = summary
                return summary

            from datetime import date, timedelta
            from apps.dashboard.services.overview_service import range_to_period_dates
            from apps.dashboard.services.shared_queries import _get_ranking_distribution, _get_position_changes

            # Scope to THIS project's tracking location. These three numbers are the project
            # list's "keywords / up / down" columns, and several projects can share one
            # site_url (one per city) -- unscoped, every city row rendered the union of all of
            # them, which is why six Premierstaff projects showed an identical 22 / 6 / 7.
            location = (getattr(site, "location", "") or "").strip() or None
            project_pk = getattr(site, "id", None)

            # THE SAME WINDOW THE POSITIONING PAGE RENDERS. This used to be built from
            # `date.today() - 28` — wall-clock, with no reference to when the project was
            # actually measured — while `ProjectPositionsView` anchors on
            # `latest_ranking_anchor` (the newest keyword_rankings row + 1 day, so the
            # `anchor - 1` arithmetic lands the window END exactly on the measurement).
            #
            # The two disagreed the moment a project fell behind: with its last sync 40 days
            # ago, the wall-clock window contained no measurement at all, so the list row
            # reported "—" (which means NEVER CAPTURED) beside a workspace showing a real
            # score for the same project. Anchoring both on the measurement makes the list and
            # the workspace two views of one number instead of two numbers.
            #
            # THE SAME RANGE, TOO. This used to hardcode "28d" while ProjectPositionsView
            # honours the `range` query param, so selecting 7d or 90d moved the workspace's
            # "Your visibility" figure and left this row's Visibility column on its 28-day
            # reading — one project, two percentages, neither labelled with its window. The
            # view now passes the caller's range through `context`; 28d stays the default so a
            # caller that only wants the project list is unchanged.
            #
            # 28d, not 30d: the SPA's default range is '28d', matching Search Console's own
            # windows — see OverviewQuerySerializer.
            #
            # Imported lazily: apps.api.views imports this module at import time, so a
            # module-level `from apps.api.views import latest_ranking_anchor` would cycle.
            from apps.api.views import latest_ranking_anchor
            anchor = latest_ranking_anchor(site.site_url, location)
            latest = (anchor - timedelta(days=1)) if anchor else None
            range_key = (self.context.get("range") or "28d") if self.context else "28d"
            curr_start, curr_end, prev_start, prev_end = range_to_period_dates(
                range_key, anchor or date.today())

            dist = _get_ranking_distribution(site.site_url, curr_start, curr_end,
                                             location=location, site_pk=project_pk)
            changes = _get_position_changes(site.site_url, curr_start, curr_end,
                                            prev_start, prev_end, location=location,
                                            site_pk=project_pk)

            if latest:
                days_ago = (date.today() - latest).days
                if days_ago == 0:
                    updated_str = "Today"
                elif days_ago == 1:
                    updated_str = "Yesterday"
                else:
                    updated_str = f"{days_ago} days ago"
            else:
                updated_str = "No sync yet"

            summary = {
                "tracked": dist.get("total", len(tracked_kws)),
                "avg_pos": dist.get("avg_position", 0.0),
                # Semrush-style CTR-weighted score from _get_ranking_distribution. None means
                # "never captured" (renders as —); 0.0 means "captured, ranks nowhere".
                "visibility": dist.get("visibility"),
                "improved": changes.get("improved_count", 0),
                "declined": changes.get("declined_count", 0),
                "last_updated": updated_str,
            }
            site._pos_summary_cache = summary
            return summary
        except Exception as e:
            import logging; logging.getLogger(__name__).error(f"ProjectSerializer _pos_summary error: {e}", exc_info=True)
            summary = {"tracked": 0, "avg_pos": 0.0, "visibility": None, "improved": 0, "declined": 0, "last_updated": "No sync yet"}
            site._pos_summary_cache = summary
            return summary

    def get_tracked_keywords_count(self, site) -> int:
        return self._pos_summary(site)["tracked"]

    def get_avg_position(self, site) -> float:
        return self._pos_summary(site)["avg_pos"]

    def get_visibility(self, site) -> float | None:
        return self._pos_summary(site)["visibility"]

    def get_improved_count(self, site) -> int:
        return self._pos_summary(site)["improved"]

    def get_declined_count(self, site) -> int:
        return self._pos_summary(site)["declined"]

    def get_last_updated(self, site) -> str:
        return self._pos_summary(site)["last_updated"]


class ProjectCreateSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    vertical = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    # Collected by the Add-domain modal's Connections step. All optional — a site can be added
    # with none of them (the modal's explicit "Skip for now") and configured later in Settings.
    # Previously the popover collected only domain+name, so add_site() always stored
    # gsc_property=domain (which Search Console reads as a URL-prefix property, not the
    # sc-domain: property most accounts actually own) and ga4_property_id=None — the direct
    # cause of a new site's GA4-backed pages staying empty until someone visited Settings.
    gsc_property = serializers.CharField(max_length=255, required=False, allow_blank=True)
    ga4_property_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    dataforseo_target_domain = serializers.CharField(max_length=255, required=False, allow_blank=True)
    # Set only by the Position Tracking wizard, to register the same domain as a second,
    # independent tracking project. Every other creation path leaves this False, so add_site()
    # keeps rejecting a plain re-add of an already-registered domain there.
    allow_duplicate = serializers.BooleanField(required=False, default=False)


class OverviewQuerySerializer(serializers.Serializer):
    # 28d, matching Search Console's own window choices — see range_to_period_dates for why.
    # "30d" stays accepted so a cached SPA build or bookmarked URL keeps working; it resolves
    # to the same 28-day window rather than a second, slightly different one.
    range = serializers.ChoiceField(choices=["7d", "28d", "30d", "90d"], required=False, default="28d")
