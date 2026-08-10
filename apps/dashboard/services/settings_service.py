"""Settings page (Phase E) -- real reshape of Site credentials/competitors (existing
pipeline.services.site_service/competitor_service), SyncLog connector status, and the app's
real Django users, plus a genuinely-persisted JSON blob for every settings group with no
dedicated relational need. See .claude/api-reference.md.

IMPORTANT -- this module's shape was corrected against the SPA's ACTUAL render code
(static/spa/index.html renderVals()'s `if (tab === 'settings')` block, ~line 6312-6494;
fetchTab()'s settings-only branch, ~line 3557-3577; and the mutation call sites `saveWs`/
`saveNotif`/`saveAi`/`saveData`/`editSyncCfg`/`togglePlatform`/`setBudgetCap`/`toggleEnforce`/
`editRule`/`saveCreds`/`togglePref`, ~line 3970-4111), NOT against the Task 2 plan's shape
sketch, which had drifted from the real SPA in two ways significant enough to crash the whole
tab on render:

  1. `data.usage` (an object with `budget`/`currency`/`month_to_date`/`est_monthly`/`items`)
     and `data.sync` (`next_run`/`day`/`last_run`) are BOTH dereferenced completely unguarded
     at the top of the Settings computed-values block (`const u = data.usage;` /
     `data.sync.next_run`), unconditionally on every render of the Settings tab regardless of
     which sub-tab is open -- neither key appears anywhere in the design spec's contract table
     or the plan's DEFAULT_SETTINGS_BLOB. Omitting them would raise a TypeError on every load
     of the Settings tab. Confirmed against the SPA's own (now-stale) mock backend
     (static/spa/app/api.js `settingsView`/`usageView`), which independently proves these two
     keys are real, required parts of the settings response shape the SPA expects -- not an
     invention of this file. `usage` is still honest zeros/nulls: no cost/quota-tracking
     infrastructure exists to back it with real numbers (same rationale as `budget.quotas`
     below), and it is never the mock's fabricated per-keyword cost formulas or fixed $75
     "plan budget." `sync` IS now real -- a scheduler exists (`manage.py run_scheduled_syncs`,
     driven hourly by the operator's OS scheduler), so `next_run`/`day` are computed from the
     configured cadence and actual RefreshRun history via apps.sync.scheduling; see
     _sync_summary_raw for the two cases where they are still legitimately None.
  2. `team[].initials` is dereferenced directly (`{{ m.initials }}`, index.html:2864) rather
     than computed from `m.name` in the render code -- the plan's query_team_raw sketch omits
     it entirely, which would render the literal string "undefined" in every team avatar.
     Added here as a real (non-fabricated) derivation from each user's own username.

Both are additive, honestly-computed GET-only fields -- neither is ever written by a PUT
(no SPA call site sends `usage` or `sync` in a settings PUT body), so neither participates in
DEFAULT_SETTINGS_BLOB's merge-with-saved-blob logic below.
"""
import calendar
import logging
from datetime import date, datetime, timezone

from sqlalchemy import select

from apps.accounts.models import UserProfile
from apps.dashboard.models import ProjectSettings
from apps.sync.models import SyncLog
from pipeline.db.schema import Site
from pipeline.services.competitor_service import get_tracked_competitors, set_tracked_competitors
from apps.dashboard.services.ads_credentials import (
    SECRET_FIELD, PLATFORM_FIELDS, PLATFORM_REQUIRED_FIELDS, decrypt_fields, encrypt_fields, mask,
)
from pipeline.services.site_service import update_site
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

# Honest static defaults for every blob-backed group -- NOT the fixture's fabricated
# workspace/billing/2FA numbers. Field names verified against the SPA's actual `st.ws`/
# `st.notif`/`st.ai`/`st.dp`/syncCfg/platConn/`data.budget`/rulesArr/crawlCfg/`sec` reads
# (static/spa/index.html:6320-6494) -- every key here is one the SPA actually dereferences.
# `prefs` is a distinct top-level group from `notifications` (confirmed via fetchTab's
# `next.prefs = Object.assign({}, data.prefs)`, index.html:3561-3564, and the mock backend's
# separate `prefs` key in static/spa/app/api.js settingsView) -- currently unreachable from any
# wired-up button in the template (togglePref's handlers `prefEmail`/`prefDigest` are defined
# but not referenced by any element), but genuinely, honestly persisted here in case that
# changes, exactly like every other blob-backed group.
DEFAULT_SETTINGS_BLOB = {
    "workspace": {"name": "", "timezone": "America/Chicago", "week_start": "Monday", "owner_email": ""},
    "prefs": {"email_alerts": False, "weekly_digest": False},
    "notifications": {"email_enabled": False, "weekly_digest": False, "digest_day": "Monday",
                       "recipients": "", "slack_enabled": False, "slack_webhook": "",
                       "quiet_start": "", "quiet_end": "", "route_high": "email",
                       "route_medium": "digest", "route_info": "none"},
    "aiConfig": {"provider": "", "model": "", "tone": "Concise", "cadence": "weekly",
                 "monthly_cap": 0, "brand_voice": ""},
    "dataPrefs": {"export_format": "CSV", "retention": "24m",
                  "report_timezone": "America/Chicago", "number_format": "1,234.56"},
    "syncConfig": {"positions": "weekly", "backlinks": "weekly", "audit": "monthly",
                   "keywords": "monthly", "ads": "12h", "ai": "weekly"},
    "platformConnectors": {"linkedin": False, "reddit": False, "youtube": False, "x": False,
                            "facebook": False, "instagram": False, "meta_ads": False},
    "budget": {"cap": 0, "enforce": False,
               "quotas": {"ga4_tokens_used": 0, "ga4_tokens_limit": 25000,
                          "ads_ops_used": 0, "ads_ops_limit": 15000,
                          "gsc_queries_used": 0, "gsc_queries_limit": 1200}},
    # Only rules that a detector actually reads belong here. `alerts_service._RULE_DETECTORS`
    # is the authority: a rule listed there governs a real query, and a rule that is not is a
    # control that appears to configure something and configures nothing.
    #
    # Removed 2026-07-27 for exactly that reason:
    #   pos_drop      -- nothing emits a per-keyword ranking alert. `alerts.js` has a `ranking`
    #                    entry in its kindMap, but no code path ever produces that kind. The
    #                    nearest real data is a `seo_avg_position` anomaly, which is a SITE-WIDE
    #                    average expressed as a percent deviation -- reading a "drops by N
    #                    positions" threshold against it would be fabrication, not a mapping.
    #   lost_backlink -- nothing anywhere detects a lost backlink.
    # Re-add either one in the same change as the detector that reads it, never before.
    #
    # `traffic_anomaly`'s label was also wrong. It said "Clicks deviate from 28-day mean by",
    # but the rule governs the WHOLE anomaly detector: every metric_type (SEO and ads), against
    # a 12-week baseline. It is the only rule mapped there, so narrowing it to clicks would
    # leave the other metric types with no control and no off switch.
    #
    # Note `anomaly_service` only writes rows above its own ANOMALY_THRESHOLD_PCT = 35, so a
    # threshold below 35 cannot surface anything extra; above 35 it genuinely filters.
    "alertRules": [
        {"id": "traffic_anomaly", "label": "Any metric deviates from its 12-week baseline by", "threshold": 35, "unit": "%", "on": True},
        {"id": "audit_errors", "label": "Crawl finds an issue affecting pages >=", "threshold": 1, "unit": "pages", "on": True},
    ],
    "crawl": {"maxPages": 500, "frequency": "monthly", "jsRendering": False,
              "respectRobots": True, "excludedPaths": ""},
    "security": {"twofa": False, "sso": False, "session_timeout": "30d", "sessions": [], "tokens": []},
}

# --- The `security` group is the one group whose fields are NOT interchangeable --------------
# Every other blob group is a plain preference: saving it changes only what the user sees next
# time. `security` mixes one plain preference with four fields that would each make the UI
# CLAIM a control that does not exist anywhere in this codebase. Persisting those four would be
# a worse lie than the blanket rejection this replaces -- a toggle that survives a reload reads
# as "two-factor auth is on", when nothing in the sign-in path would ever ask for a code.
#
#   session_timeout -> PERSISTED. A plain preference, exactly like `dataPrefs`/`prefs`: nothing
#                      consumes it yet, but saving a stored string claims nothing false. (Note
#                      no control in static/spa/src/pages/settings.html writes it today.)
#   twofa / sso     -> REFUSED. No 2FA/TOTP/SAML implementation exists (no django-otp, no SAML
#                      package in INSTALLED_APPS, nothing in the auth path reads either flag).
#                      A stored `true` would assert a security guarantee that is not real.
#   sessions        -> REFUSED. Real sessions live in django_session. A JSON array is not that,
#                      and "revoking" an entry out of it would log nobody out. Served as [] --
#                      an empty Active-sessions card is honest; a fabricated one is not.
#                      (django_session stores only session_key/expire_date/payload -- it has no
#                      device/ip/location to honestly fill the SPA's session rows with.)
#   tokens          -> REFUSED. Real API tokens are DRF authtoken rows (rest_framework.authtoken
#                      is installed and issues one real token per user). A fabricated
#                      `lm_live_xxxx` prefix stored in JSON would authenticate nothing.
#
# Refusal is deliberately change-based, not presence-based: the SPA always round-trips the whole
# `security` object (app.js toggle2fa/toggleSso/revokeSession/revokeToken/createToken all
# Object.assign over the full secDraft), so a body that merely echoes these fields back at their
# honest values is a no-op and must not block an otherwise-legitimate save. Only an attempt to
# actually CHANGE one of them is refused.
_SECURITY_PERSISTABLE = ("session_timeout",)

# The honest, unchangeable value of each unsupported field. Never persisted, always served.
_SECURITY_UNSUPPORTED = {"twofa": False, "sso": False, "sessions": [], "tokens": []}

# The wire code returned for a refused `security` write. apps/api/views.py turns this into
# `400 {"detail": <this string>}`, which is the only part of the result the view forwards, so
# this string is the entire user-facing explanation. It is deliberately still the opaque legacy
# code, not a readable sentence, because
# apps/dashboard/services/tests/test_settings_service.py's
# ApplySettingsUpdateTeamSecurityRejectedTests pins it verbatim. Replacing it with a sentence
# ("Two-factor authentication is not implemented in this app.") is a two-file change: that test,
# and static/spa/src/js/app.js's putSettings, which currently throws the message away with
# `.catch(() => {})` so no refusal reaches the user at all.
_SECURITY_REFUSED = "not_yet_available"


def _refused_security_fields(security: dict) -> list[str]:
    """The fields in a PUT's `security` object that cannot be honestly saved -- i.e. every key
    that is neither persistable nor an unsupported field left at its honest value. Empty list
    means the whole object is safe to apply."""
    refused = []
    for key, value in security.items():
        if key in _SECURITY_PERSISTABLE:
            continue
        if key in _SECURITY_UNSUPPORTED and value == _SECURITY_UNSUPPORTED[key]:
            continue  # echoed back unchanged -- a no-op, not a claim
        refused.append(key)
    return sorted(refused)

# Real cadence labels shown for each sync module -- matches the SPA's own `cadenceLabels`
# map (index.html:6350) so `usage.items[].cadence` reads as a real label, not a raw code.
_CADENCE_LABELS = {
    "12h": "Every 12 hours", "daily": "Daily", "weekly": "Weekly",
    "biweekly": "Every 2 weeks", "monthly": "Monthly", "manual": "Manual only",
}

# (display label, syncConfig key) -- the labels are exactly the SPA's own `scopeFor` map keys
# (index.html:6320) so the "run sync" button stays wired for each row.
_USAGE_MODULES = [
    ("Position tracking (SERP Standard)", "positions"),
    ("Backlinks summary + new/lost deltas", "backlinks"),
    ("Site audit crawl (OnPage)", "audit"),
    ("Keyword volume refresh (Labs)", "keywords"),
]


def _module_connector_names(scope_key: str) -> list[str]:
    """The real connector names a `_USAGE_MODULES` scope key runs.

    `connector_costs.connector` holds CONNECTOR names ("dataforseo_serp"), while
    `_USAGE_MODULES` is keyed by the SPA's SCOPE names ("positions"). Mapping the two by
    hand would be a second, silently-drifting copy of the sync registry. Instead this
    derives the mapping from the one registry that already decides which connectors a
    scope actually runs -- `PAGE_CONNECTORS`, via the same `SCOPE_ALIASES` indirection
    `start_sync_run()` uses -- so pressing "Sync now" on a row and the cost attributed to
    that row are, by construction, about the same set of connectors.

    Imported inside the function: `apps.sync.scheduling` (pulled in transitively by
    `sync_api_service`) imports DEFAULT_SETTINGS_BLOB from this module, so a module-level
    import would be circular. Same reason as `_sync_summary_raw`'s import.
    """
    try:
        from apps.dashboard.services.sync_api_service import SCOPE_ALIASES
        from pipeline.services.sync_engine import PAGE_CONNECTORS
    except Exception as exc:  # pragma: no cover - defensive; a cost read must not 500 a page
        logger.error(f"[settings] could not resolve connectors for {scope_key}: {exc}", exc_info=True)
        return []
    return list(PAGE_CONNECTORS.get(SCOPE_ALIASES.get(scope_key, scope_key), []))


def _empty_cost_window() -> dict:
    """The shape `cost_service.cost_last_90_days` returns when nothing is recorded.

    Used only if the cost read itself blows up in a way cost_service did not already
    swallow -- so `_usage_raw` still returns its full contract and Settings still renders.
    `runs: 0` is what the UI keys "never recorded" off, so this degrades to the honest
    "no measurement" state rather than to a fabricated $0.00.
    """
    today = datetime.now(timezone.utc).date()
    return {"total": 0.0, "currency": "USD", "days": 90, "start": today.isoformat(),
            "end": today.isoformat(), "runs": 0, "by_connector": []}


def _credentials_now_present(site_id: str) -> dict:
    """Which site credentials are configured RIGHT NOW, per connector family.

    Needed because SyncLog records what happened at the LAST RUN, not what is true today.
    Reading the live Site row is the only way to tell a still-broken connector from one whose
    cause the user has already fixed but which has not re-run yet.
    """
    try:
        from sqlalchemy import select as _select
        from pipeline.db.schema import Site as _Site
        with get_session() as session:
            site = session.execute(
                _select(_Site).where(_Site.site_url == site_id)
            ).scalars().first()
        if site is None:
            return {}
        return {
            "ga4": bool((site.ga4_property_id or "").strip()),
            "gsc": bool((site.gsc_property or "").strip()),
        }
    except Exception as exc:
        logger.error(f"[settings] could not read live credentials for {site_id!r}: {exc}", exc_info=True)
        return {}


# A stored error matching one of these was caused by a MISSING credential. If that credential
# is present now, the error describes a problem the user has already solved.
_MISSING_CRED_MARKERS = {
    "ga4": ("no ga4 property configured", "ga4 property id"),
    "gsc": ("no gsc property", "search console access is missing"),
}


def query_connectors_raw(site_id: str) -> list[dict]:
    """Real reshape of SyncLog rows -- one per connector, honest status/last_sync/records.

    SyncLog holds ONE row per (connector, site) describing the LAST run. That makes a stored
    error a historical fact, not a current one -- and the Data pipeline card was presenting it
    as current. A user who added their GA4 property ID in Settings kept reading
    "No GA4 property configured for <site>" indefinitely, because ga4 had not re-run since,
    so the dashboard flatly contradicted the value sitting in the form above it.

    Now: if the stored error was a missing-credential error AND that credential is present
    today, the row is reported as `stale_error` -- the run genuinely failed, but its cause is
    already fixed and a re-run is all that is needed. The error text is preserved under
    `error_was` so nothing is hidden, and `status` is NOT rewritten to "success", because no
    successful run has actually happened.
    """
    present = _credentials_now_present(site_id)
    out = []
    for r in SyncLog.objects.filter(site_url=site_id):
        err = r.error_message or ""
        low = err.lower()
        resolved = False
        for family, markers in _MISSING_CRED_MARKERS.items():
            if r.connector.startswith(family) and present.get(family) and any(m in low for m in markers):
                resolved = True
                break
        out.append({
            "name": r.connector,
            "status": "stale_error" if resolved else r.status,
            "records": r.records_written,
            "last_sync": r.last_synced.isoformat() if r.last_synced else None,
            # Preserve the stored value EXACTLY when nothing was resolved -- SyncLog.error_message
            # is None (not "") for a clean run, and callers/tests rely on that distinction.
            "error": "" if resolved else r.error_message,
            "error_was": err if resolved else "",
            "needs_rerun": resolved,
        })
    return out


# The only role values this app understands. `check_owner_admin` blocks exactly one of them
# ("Analyst"), the Settings team table renders them verbatim, and nothing else is defined —
# see .claude/skills.md §7.
LIVE_ROLES = ("Owner", "Admin", "Analyst")


def query_team_raw() -> list[dict]:
    """Real reshape of the app's actual Django users -- enforces exactly 1 Owner (the founder/first user).
    Normalizes extra owners/viewers to Admin and self-heals UserProfile rows. email is blank if unseeded,
    last_active is Django's own real last_login, initials computed from username."""
    profiles = list(UserProfile.objects.select_related("user").order_by("user__id").all())
    result = []
    owner_seen = False
    for idx, p in enumerate(profiles):
        role = p.role
        if idx == 0 or (not owner_seen and p.user.username.lower() in ("founder", "owner")):
            role = "Owner"
            owner_seen = True
        elif role == "Owner" or role not in LIVE_ROLES:
            # Three cases collapse to Admin:
            #   * a SECOND stored Owner — only one may exist, or two accounts pass
            #     check_owner_only() and the "only the Owner can…" guard means nothing;
            #   * the retired "Viewer" value;
            #   * anything outside LIVE_ROLES, which in practice means the retired
            #     founder/seo/ads vocabulary that `seed_users` wrote until it was corrected.
            #     Those rows already had Admin-level access (check_owner_admin only refuses
            #     the literal "Analyst"), so this relabels them to what they could always do
            #     rather than granting or revoking anything. Admin, not Analyst, for exactly
            #     that reason — self-healing must never silently change someone's permissions.
            role = "Admin"


        if p.role != role:
            p.role = role
            p.save(update_fields=["role"])
            
        result.append({
            "id": p.user.id, "name": p.user.username, "email": p.user.email or "",
            "role": role, "status": "active",
            "last_active": p.user.last_login.date().isoformat() if p.user.last_login else None,
            "initials": (p.user.username[:2].upper() if p.user.username else "U")
        })
    return result


def query_invitations_raw() -> list[dict]:
    """Return all pending (unaccepted) UserInvitation records."""
    from apps.accounts.models import UserInvitation
    invites = UserInvitation.objects.filter(is_accepted=False).order_by("-created_at")
    return [
        {
            "id": inv.id,
            "email": inv.email,
            "role": inv.role,
            "invited_by": inv.invited_by.username if inv.invited_by else "Owner",
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
        }
        for inv in invites
    ]


def _get_or_create_blob(site_id: str) -> ProjectSettings:
    obj, _ = ProjectSettings.objects.get_or_create(site_url=site_id, defaults={"data": {}})
    return obj


def _sync_summary_raw(site_id: str) -> dict:
    """Real 'next scheduled run' summary for the Automation sub-tab header
    (`data.sync.next_run`/`.day`/`.last_run`, dereferenced unguarded at index.html:6424).

    `next_run`/`day` used to be hardcoded None because no scheduler existed. One does now --
    `python manage.py run_scheduled_syncs`, driven hourly by the operator's OS scheduler -- so
    both are computed from the SAME cadence + run-history logic the scheduler itself uses
    (apps.sync.scheduling), which is the whole point of sharing that module: the date shown
    here is by construction the date the scheduler will act on, not a parallel guess.

    It is still None in the cases where no honest date exists, and only those:
      * every module is set to `manual` -- nothing runs automatically, so any date is invented;
      * no module has a successful run to measure a cadence from (a brand-new project). The
        scheduler treats such a module as due immediately, but nothing in the database proves
        the operator has actually installed the OS task yet, so this panel does not promise a
        date it cannot derive from real history.

    `last_run` is unchanged and still real: the most recent SyncLog.last_synced across every
    connector for this site, if any connector has ever actually run.

    Shape is unchanged (the same three keys) -- per-module detail is available from
    apps.sync.scheduling.due_modules(), which the SPA does not render.
    """
    # Imported inside the function: apps.sync.scheduling reads DEFAULT_SETTINGS_BLOB from this
    # module, so a module-level import here would be circular.
    from apps.sync.scheduling import schedule_summary

    latest = (
        SyncLog.objects.filter(site_url=site_id, last_synced__isnull=False)
        .order_by("-last_synced")
        .values_list("last_synced", flat=True)
        .first()
    )
    return {
        **schedule_summary(site_id),
        "last_run": latest.isoformat() if latest else None,
    }


def _usage_raw(site_id: str, sync_config: dict, budget_cap) -> dict:
    """Real recorded spend for the Usage & Budget sub-tab (`data.usage`, dereferenced
    unguarded at index.html:6314 as `const u = data.usage;`).

    HISTORY -- what this docstring used to say, and why it no longer holds. Every figure
    here used to be a hardcoded `0` / `None` with the note "Cost tracking not available
    yet", because nothing in the codebase recorded what an API call cost: every DataForSEO
    response carries the charge it just incurred in `tasks[].cost` and every connector
    discarded it. That is fixed. Eleven DataForSEO call sites (plus `ai_service`) now append
    a `connector_costs` row per run through `pipeline.db.writer.insert_connector_cost`, and
    `apps.dashboard.services.cost_service` reads them back. So the numbers below are no
    longer placeholders -- they are sums of charges a real, billed API response reported.

    What is a MEASUREMENT and what is a PROJECTION -- the distinction this whole panel turns
    on, because mixing them is exactly the "invented number that looks real" this codebase
    forbids:

      MEASURED (sums of billed rows, nothing extrapolated)
        window.total / window.by_connector   trailing 90 days, per connector
        month_to_date                        cost_since(first of this calendar month)
        by_month[]                           per-calendar-month totals
        items[].est / .cost_90d              the 90-day spend attributable to that module

      PROJECTED (a forecast, and labelled as one everywhere it is shown)
        est_monthly            month_to_date extended at the same daily rate to a full month
        est_monthly_basis      the sentence stating that basis; the UI must render it next
                               to the number, never the number alone
        est_monthly_is_projection   True only when there is real spend to project FROM

    "Nothing recorded" is NOT "free". A project that has never run a paid connector has
    `has_recorded_spend: False` (derived from `window.runs`, the count of spend events --
    not from the total, which is 0.0 in both the never-synced and the genuinely-free case).
    The UI renders that as an empty state, not as $0.00, and each module row whose
    connectors produced no rows carries `recorded: False` so it can say "not yet recorded"
    instead of printing a measurement it does not have.

    `cost_per_unit` stays `None` -- never 0 -- when a connector metered no units, preserving
    cost_service's deliberate distinction between "we don't know the denominator" and "it's
    free".

    `attributed` / `unattributed`: `items[]` only covers the four modules the Automation tab
    exposes. Real spend also comes from connectors no module owns (the explicit
    domain-overview / live-SERP lookups, `ai_visibility_run`, `dataforseo_opportunities`).
    Their total is reported separately rather than silently dropped, so the module rows and
    the 90-day total can be reconciled instead of appearing to disagree.

    `cadence` still mirrors this site's real configured syncConfig value, and `budget` still
    mirrors the user's own configured `budget.cap` -- neither is a fabricated plan allowance.

    Site matching is an exact `site_id` comparison (cost_service's own behaviour). That is
    correct here and does not need the `_resolve_site_ids` both-forms trick other services
    use: `connector_costs` is a 2026-07 table, always written with the same canonical
    `Site.site_url` the sync engine passes down, so no rows exist under the alternate
    prefix form.

    Never raises. cost_service already swallows and logs its own failures; the belt-and-
    braces try/except here keeps that property if a future change moves work out of it.
    """
    from apps.dashboard.services.cost_service import (
        DEFAULT_WINDOW_DAYS, cost_by_month, cost_last_90_days, cost_since,
    )

    now = datetime.now(timezone.utc)
    month_start = date(now.year, now.month, 1)

    try:
        window = cost_last_90_days(site_id, days=DEFAULT_WINDOW_DAYS)
        by_month = cost_by_month(site_id, months=3)
        month_to_date = cost_since(site_id, month_start)
    except Exception as exc:  # pragma: no cover - cost_service already swallows; see docstring
        logger.error(f"[settings] cost read failed for {site_id}: {exc}", exc_info=True)
        window, by_month, month_to_date = _empty_cost_window(), [], 0.0

    by_connector = window.get("by_connector") or []
    cost_rows = {row["connector"]: row for row in by_connector}
    has_recorded_spend = (window.get("runs") or 0) > 0

    # --- per-module attribution ------------------------------------------------------------
    items = []
    attributed_connectors: set[str] = set()
    attributed_total = 0.0
    for label, key in _USAGE_MODULES:
        connectors = _module_connector_names(key)
        rows = [cost_rows[name] for name in connectors if name in cost_rows]
        attributed_connectors.update(row["connector"] for row in rows)

        cost = round(sum(row["cost"] for row in rows), 4)
        runs = sum(row["runs"] for row in rows)
        metered = [row["units"] for row in rows if row["units"] is not None]
        units = sum(metered) if metered else None
        attributed_total += cost

        if runs:
            note = f"Measured from {runs} billed run{'' if runs == 1 else 's'} in the last {window['days']} days"
        else:
            # Not "$0.00". No billed run for these connectors means we have no measurement,
            # which is a different fact from having measured zero spend.
            note = "Not yet recorded — no billed run for this module in the window"

        items.append({
            "module": label,
            "cadence": _CADENCE_LABELS.get(sync_config.get(key), sync_config.get(key) or ""),
            # `est` is the SPA's long-standing key for this column and is kept so the shape
            # never changes under it. It no longer holds an estimate: when it is not None it
            # is the MEASURED spend for this module over the window, and the column heading
            # in static/spa/src/pages/settings.html says so.
            "est": cost if runs else None,
            "note": note,
            "recorded": bool(runs),
            "cost_90d": cost if runs else None,
            "runs": runs,
            "units": units,
            # Only meaningful when ONE connector fed this row. Two connectors under the same
            # module meter different things (SERP queries vs keywords looked up vs pages
            # crawled), so summing their units gives a denominator with no single meaning and
            # a cost-per-unit that is not a real rate. None here says exactly that; the real
            # per-connector rates are in `window.by_connector`, where each denominator has one
            # meaning. This is the same "we don't know the denominator" convention cost_service
            # uses for a connector that metered nothing.
            "cost_per_unit": (round(cost / units, 6) if units and len(rows) == 1 else None),
            "units_mixed": len(rows) > 1,
            "connectors": connectors,
        })

    unattributed = [row for row in by_connector if row["connector"] not in attributed_connectors]
    unattributed_total = round(sum(row["cost"] for row in unattributed), 4)

    # --- the one projection ----------------------------------------------------------------
    days_elapsed = now.day                                    # day 1 == one day of data so far
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    month_runs = next((m["runs"] for m in by_month if m.get("partial")), 0)

    if month_to_date > 0 and month_runs > 0:
        est_monthly = round(month_to_date / days_elapsed * days_in_month, 2)
        est_monthly_is_projection = True
        # The dollar amount is deliberately NOT restated here: it is already on screen as
        # month-to-date, and formatting it twice through two different rounding paths (Python
        # format vs JS toFixed) produced a one-cent disagreement between the two.
        est_monthly_basis = (
            f"Projection, not a measurement — the spend recorded over the first "
            f"{days_elapsed} day{'' if days_elapsed == 1 else 's'} of "
            f"{month_start.strftime('%B %Y')} ({month_runs} billed run"
            f"{'' if month_runs == 1 else 's'}), extended at that same daily rate across all "
            f"{days_in_month} days of the month."
        )
    else:
        # Rule 3: leave it 0 rather than forecast from nothing. A month with no billed run
        # gives no rate to extrapolate, and inventing one would put a fake number directly
        # beside the measured ones.
        est_monthly = 0
        est_monthly_is_projection = False
        est_monthly_basis = (
            f"No projection: nothing has been billed to this project in "
            f"{month_start.strftime('%B %Y')}, so there is no spend rate to project from."
        )

    return {
        # --- existing keys, unchanged in name and type (the SPA reads all five unguarded) ---
        "budget": budget_cap,
        "currency": window.get("currency") or "USD",
        "month_to_date": month_to_date,
        "est_monthly": est_monthly,
        "items": items,
        # --- added ---------------------------------------------------------------------------
        "est_monthly_basis": est_monthly_basis,
        "est_monthly_is_projection": est_monthly_is_projection,
        "month_start": month_start.isoformat(),
        "month_runs": month_runs,
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "has_recorded_spend": has_recorded_spend,
        "window": window,
        "by_month": by_month,
        "attributed_total": round(attributed_total, 4),
        "unattributed_total": unattributed_total,
        "unattributed": unattributed,
    }


def build_settings_response(site_id: str, site_pk: int | None = None) -> dict:
    """API-shaped Settings response. Real: project/credentials/connectors/team/sync.*
    (next_run/day now come from the real scheduler's own cadence logic, see _sync_summary_raw)
    and usage.* (measured `connector_costs` rows, read via cost_service -- see _usage_raw for
    which of its figures are measurements and which single one is a labelled projection).
    Genuinely persisted (not fabricated, not a crash-avoidance sentinel): everything in
    DEFAULT_SETTINGS_BLOB, merged with whatever's actually been saved. Honest zero/null (no
    backing infrastructure exists yet): budget.quotas -- nothing counts GA4/Ads/GSC free-tier
    API calls, so those three bars stay at their configured limits with 0 used."""
    with get_session() as session:
        # By primary key when the caller knows which project it is. `site_url` alone cannot say:
        # several projects can share one domain (add_site(allow_duplicate=True)) and this
        # returned whichever was created first, so a sibling project's Settings panel showed the
        # first project's name, vertical, location and tracking preferences.
        query = select(Site).where(Site.id == site_pk) if site_pk \
            else select(Site).where(Site.site_url == site_id)
        site = session.execute(query).scalars().first()

    from pipeline.services.saved_keyword_service import list_saved_keywords
    project = {
        "id": site.id if site else None,
        "domain": site.site_url if site else site_id,
        "name": site.site_name if site else "",
        "vertical": (site.vertical or "") if site else "",
        "location": (site.location or "") if site else "",
        # The Position Tracking wizard's "Tracking area" choices, read back from the row they
        # are now stored in. The fallbacks are the wizard's own default options, used only
        # when the column is NULL (a project created before the columns existed on a database
        # where ALTER ... DEFAULT could not backfill) or when no Site row resolves at all.
        # They are a stored preference: no connector reads them yet — see the note on Site in
        # pipeline/db/schema.py.
        "search_engine": (site.search_engine or "Google") if site else "Google",
        "device": (site.device or "Desktop") if site else "Desktop",
        "language": (site.language or "English") if site else "English",
        # This project's override set, not the domain's — same site_pk reasoning as
        # tracked_keywords below. Falls back to the resolved row's own id so a caller that
        # passed only a site_id still reads one project's columns.
        "competitors": get_tracked_competitors(
            site_id, site_pk=site_pk or (site.id if site else None)),
        # This project's tracked list, not the domain's — see the site_pk comment on
        # SavedKeyword. Falls back to the resolved row's own id so a caller that passed only a
        # site_id still gets one project's list rather than every sibling's merged together.
        "tracked_keywords": [
            k["keyword"] for k in list_saved_keywords(
                site_id, site_pk=site_pk or (site.id if site else None))
        ],
    }
    credentials = {
        "gsc_property": (site.gsc_property or "") if site else "",
        "ga4_property_id": (site.ga4_property_id or "") if site else "",
        "dataforseo_target_domain": (site.dataforseo_target_domain or "") if site else "",
    }

    blob_obj = _get_or_create_blob(site_id)
    blob = {**DEFAULT_SETTINGS_BLOB, **blob_obj.data}
    for key, defaults in DEFAULT_SETTINGS_BLOB.items():
        if isinstance(defaults, dict) and isinstance(blob.get(key), dict):
            blob[key] = {**defaults, **blob[key]}

    # apply_settings_update never writes the unsupported security fields, but a stale row from
    # before that rule, or a hand-edited JSONField, could still carry `twofa: true`. Force them
    # back to their honest values on the way out so the Security tab can never render a
    # security control as ON when nothing implements it. Shape is unchanged: same five keys.
    blob["security"] = {
        **blob["security"],
        **{k: (list(v) if isinstance(v, list) else v) for k, v in _SECURITY_UNSUPPORTED.items()},
    }

    # Masked, GET-only view of the encrypted adsCredentials sub-blob -- overwritten here,
    # same pattern as blob["security"] above, so the raw `enc` token never reaches the
    # returned dict via the **blob spread below.
    ads_credentials = {}
    stored_ads = blob.get("adsCredentials", {})
    for platform, secret_field in SECRET_FIELD.items():
        entry = stored_ads.get(platform) or {}
        token = entry.get("enc")
        masked_value = None
        if token:
            try:
                masked_value = mask(decrypt_fields(token).get(secret_field, ""))
            except Exception:
                masked_value = None
        ads_credentials[platform] = {
            "configured": bool(token and masked_value is not None),
            "masked": masked_value,
            "updated_at": entry.get("updated_at"),
            "last_test": entry.get("last_test"),
        }
    blob["adsCredentials"] = ads_credentials

    return {
        "project": project,
        "credentials": credentials,
        "connectors": query_connectors_raw(site_id),
        "team": query_team_raw(),
        "invitations": query_invitations_raw(),
        "sync": _sync_summary_raw(site_id),
        "usage": _usage_raw(site_id, blob["syncConfig"], blob["budget"]["cap"]),
        **blob,
    }


def apply_settings_update(site_id: str, body: dict) -> dict:
    """Routes a PUT body's top-level key(s) to the right backing store. Returns
    {"ok": True} on success, or {"error": "..."} for keys explicitly not persisted.

    `security` is partially supported, per-field (see _SECURITY_PERSISTABLE /
    _SECURITY_UNSUPPORTED above): `session_timeout` is saved like any other preference, while an
    attempt to change `twofa`/`sso`/`sessions`/`tokens` -- none of which this app implements --
    is refused outright rather than silently stored, and refusing aborts the WHOLE update before
    anything is written, so a mixed body never half-lands."""
    if "security" in body:
        security = body["security"]
        if not isinstance(security, dict):
            logger.warning("[settings] refused security update for %s: not an object", site_id)
            return {"error": _SECURITY_REFUSED}
        refused = _refused_security_fields(security)
        if refused:
            logger.warning(
                "[settings] refused security update for %s: %s cannot be saved -- this app "
                "implements no 2FA/SSO, and sessions/tokens live in django_session and the DRF "
                "authtoken table, not in this JSON blob",
                site_id, ", ".join(refused),
            )
            return {"error": _SECURITY_REFUSED}

    if "team" in body and isinstance(body["team"], list):
        for member in body["team"]:
            uid = member.get("id")
            role = member.get("role")
            if uid and role in ("Admin", "Analyst"):
                UserProfile.objects.filter(user_id=uid).exclude(role="Owner").update(role=role)

    if "credentials" in body:
        creds = body["credentials"]
        with get_session() as session:
            site = session.execute(select(Site).where(Site.site_url == site_id)).scalars().first()
        if site:
            # Only touch the keys the caller actually sent. This used to unconditionally pass
            # all three, so saving just GSC + GA4 (the only two fields Settings has ever shown
            # an input for) sent `dataforseo_target_domain=None`, and update_site/_bare_domain
            # turned that into "" — silently blanking a DataForSEO target on EVERY GA4/GSC save,
            # even one an operator had explicitly configured via the API or a script.
            fields = {}
            if "gsc_property" in creds:
                fields["gsc_property"] = (creds.get("gsc_property") or "").strip() or None
            if "ga4_property_id" in creds:
                # GA4's own admin UI displays "properties/123456789" and that is what people
                # paste. Every request builder does f"properties/{id}", so storing the prefixed
                # form produced "properties/properties/123456789" and an INVALID_ARGUMENT hours
                # later, well after Settings said "Saved ✓". Normalise once, here, so no save
                # path can persist the broken form.
                from pipeline.connectors.ga4 import normalise_property_id
                raw = creds.get("ga4_property_id")
                fields["ga4_property_id"] = normalise_property_id(raw) or None
            if "dataforseo_target_domain" in creds:
                fields["dataforseo_target_domain"] = (creds.get("dataforseo_target_domain") or "").strip() or None
            if fields:
                update_site(site.id, **fields)

    if "project" in body and isinstance(body["project"], dict):
        proj = body["project"]
        if "competitors" in proj:
            set_tracked_competitors(site_id, proj["competitors"])
        
        update_kwargs = {}
        if "name" in proj:
            update_kwargs["site_name"] = proj["name"]
        if "location" in proj:
            update_kwargs["location"] = proj["location"]
        # Tracking-area preferences. Blank/None is ignored rather than written, so a client
        # that omits a field (or sends "") leaves the stored choice alone instead of wiping
        # it — the Position Tracking wizard and the Edit modal each send all three, but the
        # Settings page's workspace form does not.
        for body_key, column in (("search_engine", "search_engine"),
                                 ("device", "device"),
                                 ("language", "language")):
            value = proj.get(body_key)
            if isinstance(value, str) and value.strip():
                update_kwargs[column] = value.strip()


        if update_kwargs:
            with get_session() as session:
                site = session.execute(select(Site).where(Site.site_url == site_id)).scalars().first()
            if site:
                update_site(site.id, **update_kwargs)

    blob_obj = _get_or_create_blob(site_id)
    data = dict(blob_obj.data)
    if "budgetCap" in body:
        data.setdefault("budget", dict(DEFAULT_SETTINGS_BLOB["budget"]))
        data["budget"] = {**data["budget"], "cap": body["budgetCap"]}
    if "budgetEnforce" in body:
        data.setdefault("budget", dict(DEFAULT_SETTINGS_BLOB["budget"]))
        data["budget"] = {**data["budget"], "enforce": body["budgetEnforce"]}
    for key in ("workspace", "prefs", "notifications", "aiConfig", "dataPrefs", "syncConfig",
                "platformConnectors", "alertRules", "crawl"):
        if key in body:
            data[key] = body[key]
    if "security" in body:
        # Reached only once _refused_security_fields came back empty, so this saves the
        # persistable subset (session_timeout) and never the unsupported fields -- the stored
        # blob stays free of any twofa/sso/sessions/tokens value the read path would have to
        # override. A body of nothing but echoed-back unsupported fields writes nothing.
        supported = {k: v for k, v in body["security"].items() if k in _SECURITY_PERSISTABLE}
        if supported:
            data["security"] = {**data.get("security", {}), **supported}

    if "adsCredentials" in body and isinstance(body["adsCredentials"], dict):
        # NOTE: validated here, near the end of the function -- an error return at this
        # point does NOT roll back team/credentials/project changes already applied above
        # in this same call. That matches this function's existing behaviour (only the
        # `security` block aborts the whole update up front); it is not a new gap.
        stored_ads = data.get("adsCredentials", {})
        updated_ads = dict(stored_ads)
        save_errors = []
        for platform, incoming in body["adsCredentials"].items():
            if platform not in PLATFORM_FIELDS or not isinstance(incoming, dict):
                continue
            existing_token = stored_ads.get(platform, {}).get("enc")
            try:
                merged = decrypt_fields(existing_token) if existing_token else {}
            except Exception:
                merged = {}
            for field in PLATFORM_FIELDS[platform]:
                if field in incoming:
                    value = (incoming.get(field) or "").strip()
                    # Blank means "leave the stored value alone" -- the SPA never sends a
                    # value it didn't get from the user typing into that field.
                    if value:
                        merged[field] = value
            missing = [f for f in PLATFORM_REQUIRED_FIELDS[platform] if not merged.get(f)]
            if missing:
                save_errors.append(f"{platform}: {', '.join(missing)} required")
                continue
            updated_ads[platform] = {
                **stored_ads.get(platform, {}),
                "enc": encrypt_fields(merged),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        if save_errors:
            return {"error": "Could not save Ads credentials — " + "; ".join(save_errors)}
        data["adsCredentials"] = updated_ads

    blob_obj.data = data
    blob_obj.save(update_fields=["data", "updated_at"])

    return {"ok": True}
