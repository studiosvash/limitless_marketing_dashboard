# Phase E — Settings Implementation Plan

Branch: `phase-e-settings` (based on `phase-d-ai-optimization`)
Design spec: `docs/superpowers/specs/2026-07-13-phaseE-settings-design.md` — read it first.

## Global constraints (apply to every task)

- **No fake data, ever** — and this phase has a sharper version of that rule: several fields
  (`workspace.plan/mrr/seats`, `security.twofa/sso`, `platformConnectors.linkedin`) were
  FABRICATED in the original SPA fixture. Returning honest `""`/`0`/`false`/`null` for these is
  not just "incomplete," it's correcting an active fabrication — do not accidentally reintroduce
  the fixture's specific fake values as "reasonable defaults."
- **Verify every SPA request/response shape against `static/spa/index.html`'s actual code
  yourself before writing code** — do not trust this plan's shape sketches as gospel. Phase D's
  final review found two real bugs (a Critical data-loss bug, an Important blank-label bug)
  that survived four rounds of review because implementations were built against a *documented*
  shape that had quietly diverged from the SPA's *actual* `aiPost`/render code. Grep the exact
  line, read the exact request-building/response-reading code, before implementing.
- Test-class hygiene: every new test class defines its own `setUp()`, inherits directly from
  `TestCase`/`APITestCase` — never a sibling test class.
- Run the full suite (`python manage.py test`) after each task, report the pass count.

---

## Task 1: `ProjectSettings` model

Add to `apps/dashboard/models.py`:

```python
def _empty_dict():
    return {}


class ProjectSettings(models.Model):
    """Blob store for Settings groups with no dedicated relational need (workspace,
    notifications, aiConfig, dataPrefs, syncConfig, platformConnectors, budget.cap/.enforce,
    alertRules, crawl) -- see design spec for why these are a single JSONField rather than
    one model each. Genuine persistence (saves survive reload); several groups are honestly
    disclosed as not yet wired to any downstream system."""
    site_url = models.CharField(max_length=255, unique=True, db_index=True)
    data = models.JSONField(default=_empty_dict)
    updated_at = models.DateTimeField(auto_now=True)
```

Run `makemigrations dashboard`, check the migration file in.

**Tests** (`apps/dashboard/tests/test_settings_models.py`): `site_url` uniqueness
(`IntegrityError` on duplicate, wrapped in `transaction.atomic()`), default `data` is a real
empty dict (not `None`) on an unspecified create.

Report DONE with commit hash and test count.

---

## Task 2: `settings_service.py`

**Before writing this task's code**, independently re-verify these exact field/shape claims
against the live SPA source (per the Global Constraints above) — grep `static/spa/index.html`
for each of: the Connections sub-tab's `connectors[]` row template fields, the Team sub-tab's
row fields, and the full list of top-level keys read in the Settings computed-values block
(`settingsView`/`renderVals`'s Settings branch — search `st.gen`/`st.team`/`st.conn` etc.). Do
not assume the shapes below are exactly right — they are a starting sketch from research, not
verified against a diff of the current worktree's SPA copy at implementation time.

Create `apps/dashboard/services/settings_service.py`:

```python
"""Settings page (Phase E) -- real reshape of Site credentials/competitors (existing
pipeline.services.site_service/competitor_service), SyncLog connector status, and the app's
real Django users, plus a genuinely-persisted JSON blob for every settings group with no
dedicated relational need. See docs/superpowers/specs/2026-07-13-phaseE-settings-design.md."""
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
# workspace/billing/2FA numbers. Verify these keys against the SPA's actual reads before
# finalizing (see note above).
DEFAULT_SETTINGS_BLOB = {
    "workspace": {"name": "", "timezone": "America/Chicago", "week_start": "Monday", "owner_email": ""},
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
    """Real reshape of the app's actual (exactly 3, fixed) Django users -- no invite/multi-
    seat concept exists, so this is read-only. email is honestly blank (seed_users creates
    users with no email), last_active is Django's own real last_login."""
    profiles = UserProfile.objects.select_related("user").all()
    return [
        {"id": p.user.id, "name": p.user.username, "email": p.user.email or "",
         "role": p.role, "status": "active",
         "last_active": p.user.last_login.date().isoformat() if p.user.last_login else None}
        for p in profiles
    ]


def _get_or_create_blob(site_id: str) -> ProjectSettings:
    obj, _ = ProjectSettings.objects.get_or_create(site_url=site_id, defaults={"data": {}})
    return obj


def build_settings_response(site_id: str) -> dict:
    """API-shaped Settings response. Real: project/credentials/connectors/team. Genuinely
    persisted (not fabricated, not a crash-avoidance sentinel): everything in
    DEFAULT_SETTINGS_BLOB, merged with whatever's actually been saved."""
    with get_session() as session:
        site = session.execute(select(Site).where(Site.site_url == site_id)).scalars().first()

    project = {
        "id": site.id if site else None,
        "domain": site.site_url if site else site_id,
        "name": site.site_name if site else "",
        "vertical": (site.vertical or "") if site else "",
        "location": (site.location or "") if site else "",
        "competitors": get_tracked_competitors(site_id),
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
        **blob,
    }


def apply_settings_update(site_id: str, body: dict) -> dict:
    """Routes a PUT body's top-level key(s) to the right backing store. Returns
    {"ok": True} on success, or {"error": "..."} for keys this phase explicitly does not
    persist (team, security) -- callers must turn the latter into a 400, never a silent 200."""
    if "team" in body or "security" in body:
        return {"error": "not_yet_available"}

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

    if "project" in body and isinstance(body["project"], dict) and "competitors" in body["project"]:
        set_tracked_competitors(site_id, body["project"]["competitors"])

    blob_obj = _get_or_create_blob(site_id)
    data = dict(blob_obj.data)
    if "budgetCap" in body:
        data.setdefault("budget", dict(DEFAULT_SETTINGS_BLOB["budget"]))
        data["budget"] = {**data["budget"], "cap": body["budgetCap"]}
    if "budgetEnforce" in body:
        data.setdefault("budget", dict(DEFAULT_SETTINGS_BLOB["budget"]))
        data["budget"] = {**data["budget"], "enforce": body["budgetEnforce"]}
    for key in ("workspace", "notifications", "aiConfig", "dataPrefs", "syncConfig",
                "platformConnectors", "alertRules", "crawl"):
        if key in body:
            data[key] = body[key]
    blob_obj.data = data
    blob_obj.save(update_fields=["data", "updated_at"])

    return {"ok": True}
```

**Tests** (`apps/dashboard/services/tests/test_settings_service.py`):
- `query_connectors_raw`: seed 2 `SyncLog` rows (one `ok`, one `error` with a message), assert
  both reshape correctly including the error message; empty case returns `[]`.
- `query_team_raw`: assert it reflects the REAL seeded users (founder/seo/ads) with their real
  roles, not a fabricated list; assert `email` is honestly `""` when unset; assert `last_active`
  is `None` (not a crash) for a user who's never logged in.
- `build_settings_response`: no-`ProjectSettings`-row case returns `DEFAULT_SETTINGS_BLOB`'s
  exact values merged with real `project`/`credentials`/`connectors`/`team` — exact-equality
  assert the blob fields are NOT the fixture's fabricated workspace/2FA/connector values.
  With a real saved blob (partial — e.g. only `notifications` ever saved), assert the OTHER
  keys still get honest defaults (proves the merge-with-defaults logic, not just "return
  whatever's saved").
- `apply_settings_update`: `credentials` update reflects on next `build_settings_response`
  call (real persistence, not just a 200). `budgetCap`/`budgetEnforce` merge into `budget`
  without clobbering `budget.quotas`. A second call with only `notifications` doesn't erase
  a `workspace` value saved in a prior call (proves per-key merge, not blob overwrite). `team`
  and `security` both return `{"error": "not_yet_available"}`, never persisting anything.

Report DONE with commit hash and test count.

---

## Task 3: `GET`/`PUT /api/projects/<slug>/settings`

In `apps/api/views.py`:

```python
from apps.dashboard.services.settings_service import build_settings_response, apply_settings_update

@method_decorator(login_not_required, name="dispatch")
class ProjectSettingsView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_settings_response(site_id))

    def put(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        result = apply_settings_update(site_id, request.data)
        if "error" in result:
            return Response({"detail": result["error"]}, status=400)
        return Response(build_settings_response(site_id))
```

In `apps/api/urls.py`:
```python
path("projects/<slug:slug>/settings", views.ProjectSettingsView.as_view(), name="project-settings"),
```

**Tests** (`apps/api/tests/test_settings.py`):
- `GET`: real-data case (seed `SyncLog`, assert `connectors` reflects it; assert `team`
  reflects the real seeded users), fresh-project case (no `ProjectSettings` row yet — assert
  honest defaults, not a crash), 404 unknown slug, 401 unauthenticated.
- `PUT credentials`: call, then GET again in the same test, assert the change persisted.
- `PUT budgetCap` then `PUT notifications`: assert the second call didn't erase the first's
  effect (per-key merge, not blob overwrite) — verify via a GET after both.
- `PUT team` / `PUT security`: assert clean `400`, and assert nothing was persisted (no
  `ProjectSettings` row mutated in a way that reflects the attempted change).
- 401/404 on the PUT route too.

After this task: update `.claude/FILE_INDEX.md` and `.claude/checklist.md` (add a "PHASE E —
Settings" section mirroring Phase D's, including this phase's own scope-cut rationale).

Report DONE with commit hash and full-suite test count.

---

## Task 4: SPA fidelity check

Per the design spec's "SPA fidelity check" note: independently re-trace the ENTIRE Settings
computed-values block (`static/spa/index.html`, grep `tab === 'settings'` / `st.gen` / `st.team`
/ etc.) against the ACTUAL shape `build_settings_response`/`apply_settings_update` now produce
— not against this plan's shape sketches, which were written from research and may have drifted.
For every sub-tab (General/Team/Connections/Automation/Usage & Budget/Alerts & Rules/AI
Summaries/Security & Data):
- Confirm every `data.*` dereference gets a real value of the right type (this phase's design
  bet is "no whole-tab guard needed because every key is real" — verify that bet holds, the
  same way C3's did and C4's Ads phase's did, by tracing, not assuming).
- Confirm the exact PUT request body each save button sends matches what
  `apply_settings_update` reads (the Phase D lesson: diff against the real `post`/`put` call
  site, e.g. `saveWs`/`saveNotif`/`saveAi`/`saveData`/`editSyncCfg`/`togletoggle`/`setBudgetCap`
  — read every one, not just a sample).
- Fix the hardcoded "All healthy" Connections header (`index.html:2896`-ish, verify exact line)
  to reflect real connector status (any `error`/`never`-status row → don't claim "All healthy").
- For `team`/`security`'s explicit-400 mutations: confirm the SPA's `.catch(() => {})` pattern
  on these calls means a 400 fails silently with no error toast (matching Ads/AI's precedent for
  out-of-scope actions) rather than surfacing a broken-looking error — if it currently shows a
  raw error, note this for the reviewer but do not treat it as blocking (matches the established
  precedent from C4/D for not-yet-implemented actions).
- Report every fix made, with exact line numbers, the same rigor as Phase D's Task 4.

Run the full suite once more (SPA-only change, should be unaffected). Update the checklist with
a Task 4 section. This is the last task — after this, dispatch the final whole-branch review.
