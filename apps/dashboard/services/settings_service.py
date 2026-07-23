"""Settings page (Phase E) -- real reshape of Site credentials/competitors (existing
pipeline.services.site_service/competitor_service), SyncLog connector status, and the app's
real Django users, plus a genuinely-persisted JSON blob for every settings group with no
dedicated relational need. See docs/superpowers/specs/2026-07-13-phaseE-settings-design.md.

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
     invention of this file. No real cost/quota-tracking or cron/scheduler infrastructure
     exists to back these with real numbers (same rationale as `budget.quotas` below), so
     they are honest zeros/nulls here, never the mock's fabricated per-keyword cost formulas
     or fixed $75 "plan budget."
  2. `team[].initials` is dereferenced directly (`{{ m.initials }}`, index.html:2864) rather
     than computed from `m.name` in the render code -- the plan's query_team_raw sketch omits
     it entirely, which would render the literal string "undefined" in every team avatar.
     Added here as a real (non-fabricated) derivation from each user's own username.

Both are additive, honestly-computed GET-only fields -- neither is ever written by a PUT
(no SPA call site sends `usage` or `sync` in a settings PUT body), so neither participates in
DEFAULT_SETTINGS_BLOB's merge-with-saved-blob logic below.
"""
import logging

from sqlalchemy import select

from apps.accounts.models import UserProfile
from apps.dashboard.models import ProjectSettings
from apps.sync.models import SyncLog
from pipeline.db.schema import Site
from pipeline.services.competitor_service import get_tracked_competitors, set_tracked_competitors
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
    "alertRules": [
        {"id": "pos_drop", "label": "Keyword position drops by", "threshold": 3, "unit": "positions", "on": True},
        {"id": "lost_backlink", "label": "Backlink lost from domain rank >=", "threshold": 40, "unit": "", "on": True},
        {"id": "traffic_anomaly", "label": "Clicks deviate from 28-day mean by", "threshold": 30, "unit": "%", "on": True},
        {"id": "audit_errors", "label": "Crawl finds new errors >=", "threshold": 1, "unit": "errors", "on": True},
    ],
    "crawl": {"maxPages": 500, "frequency": "monthly", "jsRendering": False,
              "respectRobots": True, "excludedPaths": ""},
    "security": {"twofa": False, "sso": False, "session_timeout": "30d", "sessions": [], "tokens": []},
}

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


def query_connectors_raw(site_id: str) -> list[dict]:
    """Real reshape of SyncLog rows -- one per connector, honest status/last_sync/records."""
    rows = SyncLog.objects.filter(site_url=site_id)
    return [
        {"name": r.connector, "status": r.status, "records": r.records_written,
         "last_sync": r.last_synced.isoformat() if r.last_synced else None,
         "error": r.error_message}
        for r in rows
    ]


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
        elif role in ("Owner", "Viewer"):
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
    """Honest 'next scheduled run' summary for the Automation sub-tab header
    (`data.sync.next_run`/`.day`/`.last_run`, dereferenced unguarded at index.html:6424).
    No cron/scheduler infrastructure exists anywhere in this codebase to compute a real next
    run or its day-of-week, so `next_run`/`day` are honestly None -- never a fabricated
    schedule. `last_run` IS real: the most recent SyncLog.last_synced across every connector
    for this site, if any connector has ever actually run."""
    latest = (
        SyncLog.objects.filter(site_url=site_id, last_synced__isnull=False)
        .order_by("-last_synced")
        .values_list("last_synced", flat=True)
        .first()
    )
    return {
        "next_run": None,
        "day": None,
        "last_run": latest.isoformat() if latest else None,
    }


def _usage_raw(sync_config: dict, budget_cap) -> dict:
    """Honest usage/cost summary for the Usage & Budget sub-tab (`data.usage`, dereferenced
    unguarded at index.html:6314 as `const u = data.usage;`). No real cost-tracking or
    spend-counter infrastructure exists anywhere in this codebase (same rationale as
    `budget.quotas` in DEFAULT_SETTINGS_BLOB) -- every module's cost estimate is honestly
    `None` with a disclosing note, never the SPA's own (now-stale) mock backend's fabricated
    per-keyword/per-page dollar formulas. `cadence` mirrors this site's real, currently-
    configured syncConfig value (not a hardcoded label) and `budget` mirrors the user's own
    configured `budget.cap` (not a fabricated fixed monthly plan allowance), so the progress
    bar reflects a real, user-set number instead of an invented one."""
    items = [
        {
            "module": label,
            "cadence": _CADENCE_LABELS.get(sync_config.get(key), sync_config.get(key) or ""),
            "est": None,
            "note": "Cost tracking not available yet",
        }
        for label, key in _USAGE_MODULES
    ]
    return {
        "budget": budget_cap,
        "currency": "USD",
        "month_to_date": 0,
        "est_monthly": 0,
        "items": items,
    }


def build_settings_response(site_id: str) -> dict:
    """API-shaped Settings response. Real: project/credentials/connectors/team/sync.last_run.
    Genuinely persisted (not fabricated, not a crash-avoidance sentinel): everything in
    DEFAULT_SETTINGS_BLOB, merged with whatever's actually been saved. Honest zero/null (no
    backing infrastructure exists yet): usage.*, sync.next_run/day, budget.quotas."""
    with get_session() as session:
        site = session.execute(select(Site).where(Site.site_url == site_id)).scalars().first()

    from pipeline.services.saved_keyword_service import list_saved_keywords
    project = {
        "id": site.id if site else None,
        "domain": site.site_url if site else site_id,
        "name": site.site_name if site else "",
        "vertical": (site.vertical or "") if site else "",
        "location": (site.location or "") if site else "",
        "competitors": get_tracked_competitors(site_id),
        "tracked_keywords": [k["keyword"] for k in list_saved_keywords(site_id)],
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

    return {
        "project": project,
        "credentials": credentials,
        "connectors": query_connectors_raw(site_id),
        "team": query_team_raw(),
        "invitations": query_invitations_raw(),
        "sync": _sync_summary_raw(site_id),
        "usage": _usage_raw(blob["syncConfig"], blob["budget"]["cap"]),
        **blob,
    }


def apply_settings_update(site_id: str, body: dict) -> dict:
    """Routes a PUT body's top-level key(s) to the right backing store. Returns
    {"ok": True} on success, or {"error": "..."} for keys explicitly not persisted."""
    if "security" in body:
        return {"error": "not_yet_available"}

    if "team" in body and isinstance(body["team"], list):
        for member in body["team"]:
            uid = member.get("id")
            role = member.get("role")
            if uid and role in ("Admin", "Analyst"):
                UserProfile.objects.filter(user_id=uid).exclude(role="Owner").update(role=role)

    if "credentials" in body:
        with get_session() as session:
            site = session.execute(select(Site).where(Site.site_url == site_id)).scalars().first()
        if site:
            update_site(
                site.id,
                gsc_property=body["credentials"].get("gsc_property") or None,
                ga4_property_id=body["credentials"].get("ga4_property_id") or None,
                dataforseo_target_domain=body["credentials"].get("dataforseo_target_domain") or None,
            )

    if "project" in body and isinstance(body["project"], dict):
        proj = body["project"]
        if "competitors" in proj:
            set_tracked_competitors(site_id, proj["competitors"])
        
        update_kwargs = {}
        if "name" in proj:
            update_kwargs["site_name"] = proj["name"]
        if "location" in proj:
            update_kwargs["location"] = proj["location"]
            
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
    blob_obj.data = data
    blob_obj.save(update_fields=["data", "updated_at"])

    return {"ok": True}
