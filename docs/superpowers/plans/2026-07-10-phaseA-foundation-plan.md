# Phase A — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **EXECUTED 2026-07-15 with two client-requested enhancements to Task 7 (recorded here so the
> plan matches what shipped):**
> - **E1 — Site health is real, not `setup`.** Task 7's original `build_pillars` hardcoded
>   Site health to `state:"setup"`. Instead `overview_service.compute_site_health()` computes a
>   real composite score (GSC page coverage + indexing + PageSpeed-when-present), resilient to a
>   missing `pagespeed` table. The Site Audit module reflects the same score. Only Paid ROAS and
>   AI visibility stay `setup` (genuinely unconnected). Task 7's `test_unbuilt_pillars_report_setup_state`
>   became `test_site_health_pillar_is_real_when_page_data_exists`.
> - **E2 — the priority feed is cross-module, not `[]`.** Task 7 originally returned
>   `priority: []` ("Phase B"). Instead `overview_service.build_priority_feed()` aggregates
>   unacknowledged alerts across modules (SEO anomalies, Site Audit technical + indexing issues,
>   decision signals), severity-sorted, top 6. Heading stays "Priority feed" (user kept the name).
> - Also: Task 8 sets `baseUrl = '/'` (NOT `''` — empty is falsy in api.js's `if(config.baseUrl)`
>   fixture switch) and injects the bootstrap right after api.js (not before `</body>`) so it beats
>   the component's first fetch. DRF views carry `@login_not_required` to bypass the session
>   `LoginRequiredMiddleware` so unauth requests get DRF's 401, not a 302 redirect.

**Goal:** Stand up the DRF API foundation (token auth, project model, Overview endpoint) and
serve the approved SPA (`Limitless Marketing Dashboard v2.dc.html`) against real data — proving
the whole new architecture end-to-end on one page before Phase B ports the rest.

**Architecture:** New `apps/api` Django app exposes `/api/projects` and
`/api/projects/<slug>/overview` per `HANDOFF_SPEC.md`, authenticated with DRF
`TokenAuthentication` (subclassed to accept the `Bearer` scheme the frontend already sends).
The `sites` SQLAlchemy table becomes the project registry (gains `vertical`, `location`,
`slug` columns). Query logic already built for the old Overview page is extracted into
`apps/dashboard/services/overview_service.py` so the old Django view and the new DRF view
call the same functions — no duplicated SQL. The SPA is served at `/app/` by a Django view
that injects a small bootstrap `<script>` setting `FuseAPI.config` before the file's own
scripts run.

**Tech Stack:** Django 6.0, Django REST Framework (new dependency), SQLAlchemy 2.x (existing
analytics layer), SQLite (both DBs).

## Global Constraints

- Never call an external API from a page-rendering or API-reading view — DB-only reads (see
  `CLAUDE.md`'s core contract). This plan only reads existing DB tables; no connector calls.
- Two-database boundary holds: Django ORM owns `django_internal.db`; SQLAlchemy
  (`pipeline/db/schema.py`) owns `fusehealth.db`. No cross-DB foreign keys — `site_url` /
  `slug` are plain string join keys.
- No fake data. Any pillar/module whose source feature isn't built yet reports
  `"state": "setup"` with no invented numbers — never a placeholder value.
- Route paths have **no trailing slash** (`/api/projects`, not `/api/projects/`) — the SPA's
  `app/api.js` builds URLs by string-concatenating `config.baseUrl + path`, and the paths it
  sends never end in `/`. Defining Django routes with a trailing slash would 404 every POST
  (Django's `APPEND_SLASH` redirect only ever applies to GET).
- `FuseAPI.config.baseUrl` must be set to `''` (empty string), **not** `/api` — every call site
  in the `.dc.html` file already hardcodes the `/api/...` prefix itself (e.g.
  `FuseAPI.get('/api/projects/' + pid + '/overview', params)`); setting `baseUrl = '/api'`
  would double it to `/api/api/...`.
- The SPA sends `Authorization: Bearer <token>` (see `app/api.js:44`), not DRF's default
  `Token <token>` scheme — the auth class must be subclassed to accept `Bearer`, or every
  request 401s.
- Old Django dashboard (`apps/dashboard`, `apps/accounts`, `apps/sync` URLs) is not touched or
  removed in this phase — it keeps serving unchanged.

---

### Task 1: DRF foundation — dependency, settings, `apps/api` scaffold, smoke test

**Files:**
- Modify: `requirements.txt`
- Modify: `config/settings/base.py`
- Create: `apps/api/__init__.py`
- Create: `apps/api/apps.py`
- Create: `apps/api/authentication.py`
- Create: `apps/api/views.py`
- Create: `apps/api/urls.py`
- Modify: `config/urls.py`
- Create: `apps/api/tests/__init__.py`
- Create: `apps/api/tests/test_ping.py`

**Interfaces:**
- Produces: `apps.api.authentication.BearerTokenAuthentication` (class) — used by every
  later API view in this plan.
- Produces: `/api/ping` route, `GET` → `{"ok": true}` when authenticated, `401` otherwise —
  proves auth + routing before any real endpoint is built.

- [ ] **Step 1: Add the dependency**

Add to `requirements.txt` (after the `Django>=6.0,<6.1` line, in the web framework section):

```
djangorestframework>=3.15.0,<3.16.0
```

Run: `pip install -r requirements.txt`
Expected: `Successfully installed djangorestframework-3.15.x`

- [ ] **Step 2: Register the apps and DRF settings**

In `config/settings/base.py`, change `INSTALLED_APPS` to:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    # FuseHealth apps
    "apps.accounts",
    "apps.dashboard",
    "apps.sync",
    "apps.api",
]
```

Add after the `DATABASES` block (anywhere before the end of the file — place it right after
the `ANALYTICS_DB_PATH` line for locality with the other cross-cutting config):

```python
# --- REST API (Limitless Marketing SPA) --------------------------------------
# The frontend (`Limitless marketing dashboard2/`) sends `Authorization: Bearer <token>`
# (see app/api.js), not DRF's default `Token <token>` scheme — hence the custom auth class.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.api.authentication.BearerTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

- [ ] **Step 3: Create the `apps/api` app skeleton**

Create `apps/api/__init__.py` (empty file).

Create `apps/api/apps.py`:

```python
from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api"
    label = "api"
```

Create `apps/api/authentication.py`:

```python
"""Authentication for the Limitless Marketing SPA.

The frontend's transport (app/api.js `http()`) sends
`Authorization: Bearer <token>` — DRF's built-in TokenAuthentication expects the
keyword `Token` by default, so we override it. Everything else (token model,
lookup, expiry semantics) is stock DRF TokenAuthentication.
"""

from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    keyword = "Bearer"
```

Create `apps/api/views.py`:

```python
from rest_framework.response import Response
from rest_framework.views import APIView


class PingView(APIView):
    """Smoke-test endpoint: proves auth + routing work before any real data endpoint exists."""

    def get(self, request):
        return Response({"ok": True})
```

Create `apps/api/urls.py`:

```python
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("ping", views.PingView.as_view(), name="ping"),
]
```

- [ ] **Step 4: Wire `/api/` into the project**

In `config/urls.py`, change to:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('', include('apps.dashboard.urls')),
    path('', include('apps.sync.urls')),
    path('api/', include('apps.api.urls')),
]
```

- [ ] **Step 5: Migrate (creates the authtoken tables)**

Run: `python manage.py migrate`
Expected: output includes `Applying authtoken.0001_initial... OK` (and later authtoken
migrations) with no errors.

- [ ] **Step 6: Write the smoke test**

Create `apps/api/tests/__init__.py` (empty file).

Create `apps/api/tests/test_ping.py`:

```python
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase


class PingAuthTests(APITestCase):
    def test_unauthenticated_ping_is_401(self):
        client = APIClient()
        resp = client.get("/api/ping")
        self.assertEqual(resp.status_code, 401)

    def test_bearer_token_ping_is_200(self):
        user = get_user_model().objects.create_user("pinger", password="x")
        token = Token.objects.create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        resp = client.get("/api/ping")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True})

    def test_default_token_keyword_is_rejected(self):
        """Confirms the Bearer override is active — DRF's default `Token` keyword must NOT work,
        otherwise a future settings change could silently revert to the wrong scheme."""
        user = get_user_model().objects.create_user("pinger2", password="x")
        token = Token.objects.create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        resp = client.get("/api/ping")
        self.assertEqual(resp.status_code, 401)
```

- [ ] **Step 7: Run the tests**

Run: `python manage.py test apps.api`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 8: Commit**

```bash
git add requirements.txt config/settings/base.py config/urls.py apps/api
git commit -m "feat(api): add DRF foundation with Bearer token auth and smoke test"
```

---

### Task 2: Auto-issue a DRF token for every user

**Files:**
- Modify: `apps/accounts/models.py`
- Modify: `apps/accounts/tests.py`

**Interfaces:**
- Consumes: `apps.accounts.models.UserProfile`, the existing `ensure_profile` signal pattern.
- Produces: every `User` row always has a matching `rest_framework.authtoken.models.Token` —
  Task 8 (SPA bootstrap) reads `user.auth_token.key` and assumes it always exists.

- [ ] **Step 1: Write the failing test**

In `apps/accounts/tests.py`, add (create the file with this content if it doesn't exist yet —
check first; if `apps/accounts/tests.py` already has content, append this class):

```python
from rest_framework.authtoken.models import Token


class AutoTokenTests(TestCase):
    def test_new_user_gets_a_token(self):
        user = get_user_model().objects.create_user("newbie", password="x")
        self.assertTrue(Token.objects.filter(user=user).exists())

    def test_existing_user_keeps_the_same_token_on_resave(self):
        user = get_user_model().objects.create_user("resaved", password="x")
        original_key = Token.objects.get(user=user).key
        user.first_name = "Changed"
        user.save()
        self.assertEqual(Token.objects.get(user=user).key, original_key)
```

Add the necessary imports at the top of `apps/accounts/tests.py` if not already present:
`from django.contrib.auth import get_user_model` and `from django.test import TestCase`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.accounts.tests.AutoTokenTests`
Expected: FAIL — `Token.objects.filter(user=user).exists()` is `False` (no signal creates it yet).

- [ ] **Step 3: Add the signal**

In `apps/accounts/models.py`, add the import and a second signal receiver after the existing
`ensure_profile` function:

```python
from rest_framework.authtoken.models import Token
```

(add this import near the top, alongside the existing `django.dispatch` import)

```python
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_auth_token(sender, instance, created, **kwargs):
    """Every user gets a DRF token so the SPA can authenticate as `Authorization: Bearer <key>`
    (see apps.api.authentication.BearerTokenAuthentication). get_or_create is idempotent, so
    this is safe to run on every save, not just creation."""
    Token.objects.get_or_create(user=instance)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.accounts.tests.AutoTokenTests`
Expected: `Ran 2 tests in ...s\n\nOK`

- [ ] **Step 5: Run the full accounts test suite to check nothing broke**

Run: `python manage.py test apps.accounts`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/accounts/models.py apps/accounts/tests.py
git commit -m "feat(accounts): auto-issue a DRF Bearer token for every user"
```

---

### Task 3: Extend the project registry — `vertical`, `location`, `slug` on `Site`

**Files:**
- Modify: `pipeline/db/schema.py`
- Modify: `pipeline/services/site_service.py`
- Create: `apps/sync/management/commands/add_project_fields.py`
- Create: `pipeline/services/tests/test_site_service.py`

**Interfaces:**
- Produces: `Site.vertical: str | None`, `Site.location: str | None` (default `"United
  States"`), `Site.slug: str` (unique, indexed) — consumed by Task 4's project serializer.
- Produces: `pipeline.services.site_service.slugify_unique(session, base: str) -> str` —
  consumed by Task 4's project-create endpoint.
- Produces: `pipeline.services.site_service.add_site(..., vertical=None, location="United
  States")` — extended signature, backward compatible (new params are optional).

- [ ] **Step 1: Add the columns to the SQLAlchemy model**

In `pipeline/db/schema.py`, find the `Site` class (around line 29) and change it to:

```python
class Site(Base):
    """Registry of tracked domains; source of truth for per-domain credentials."""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_url = Column(String(255), nullable=False, unique=True, index=True)
    site_name = Column(String(255), nullable=True)
    slug = Column(String(100), nullable=True, unique=True, index=True)
    vertical = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True, default="United States")
    gsc_property = Column(String(255), nullable=True)
    ga4_property_id = Column(String(100), nullable=True)
    dataforseo_target_domain = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, server_default=func.now())
```

(`slug` is nullable at the DB level because `ALTER TABLE ... ADD COLUMN` in SQLite cannot add
a `NOT NULL` column without a default to a table with existing rows; Step 3 below backfills
every existing row's slug immediately, and Task 4's create endpoint always sets one, so it is
effectively always populated going forward.)

- [ ] **Step 2: Write the failing test for the migration command**

Create `pipeline/services/tests/__init__.py` if it doesn't already exist (empty file — check
first with a directory listing; the `pipeline/db/tests/` sibling directory already has one).

Create `pipeline/services/tests/test_site_service.py`:

```python
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings
from sqlalchemy import inspect as sa_inspect, select

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class AddProjectFieldsCommandTests(TestCase):
    def setUp(self):
        # get_session() memoizes its engine per-process (see db_connection.py) — reset it so
        # each test binds to its own temp DB instead of leaking the previous test's engine.
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)

    def test_adds_columns_and_backfills_slug(self):
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))

        # Simulate a pre-Phase-A database: a site row with no slug/vertical/location.
        # (init_db already creates the new columns since schema.py Step 1 added them — to
        # simulate the *pre-migration* state we insert directly via raw SQL, matching what a
        # real already-deployed DB looks like before this command runs.)
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO sites (site_url, site_name, is_active) VALUES (?, ?, 1)",
            ("sc-domain:fusehealth.com", "FuseHealth"),
        )
        conn.commit()
        conn.close()

        with override_settings(ANALYTICS_DB_PATH=db_path):
            db_connection._SessionFactory = None
            call_command("add_project_fields")

            with get_session() as session:
                site = session.execute(select(Site)).scalars().first()
                self.assertEqual(site.slug, "fusehealth")
                self.assertEqual(site.location, "United States")

    def test_idempotent_when_run_twice(self):
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))

        with override_settings(ANALYTICS_DB_PATH=db_path):
            db_connection._SessionFactory = None
            call_command("add_project_fields")
            call_command("add_project_fields")  # must not raise

            with get_session() as session:
                site = session.execute(select(Site)).scalars().first()
                self.assertIsNone(site)  # no sites were inserted in this test — just checking no crash
```

- [ ] **Step 2b: Run test to verify it fails**

Run: `python manage.py test pipeline.services.tests.test_site_service`
Expected: FAIL — `ModuleNotFoundError` or `CommandError: Unknown command: 'add_project_fields'`.

- [ ] **Step 3: Write the slugify helper + extend `site_service.py`**

In `pipeline/services/site_service.py`, add near the top (after `_bare_domain`):

```python
import re


def _slugify(value: str) -> str:
    """Lowercase, alnum + hyphens only, matching the project 'id' shape the frontend
    fixtures already use (e.g. 'fusehealth', 'limitless')."""
    value = _bare_domain(value) or value
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def slugify_unique(session, base: str) -> str:
    """Return a slug derived from `base` that doesn't collide with an existing Site.slug.
    Appends -2, -3, ... on collision."""
    from pipeline.db.schema import Site  # local import: avoids a circular import at module load

    root = _slugify(base)
    candidate = root
    n = 2
    while session.execute(select(Site).where(Site.slug == candidate)).scalars().first():
        candidate = f"{root}-{n}"
        n += 1
    return candidate
```

Update `add_site(...)` to accept and set the new fields — replace the existing function with:

```python
def add_site(site_url, site_name=None, gsc_property=None, ga4_property_id=None,
             dataforseo_target_domain=None, vertical=None, location="United States") -> int:
    site_url = (site_url or "").strip()
    if not site_url:
        raise ValueError("site_url is required")
    with get_session() as session:
        existing = session.execute(select(Site).where(Site.site_url == site_url)).scalars().first()
        if existing:
            raise ValueError(f"Site already exists: {site_url}")
        name = site_name or _bare_domain(site_url) or site_url
        site = Site(
            site_url=site_url,
            site_name=name,
            slug=slugify_unique(session, name),
            vertical=vertical,
            location=location,
            gsc_property=gsc_property or site_url,
            ga4_property_id=ga4_property_id or None,
            dataforseo_target_domain=_bare_domain(dataforseo_target_domain or site_url),
            is_active=1,
        )
        session.add(site)
        session.flush()
        new_id = site.id
        logger.info(f"[site_service] Added site #{new_id}: {site_url}")
        return new_id
```

Update the `allowed` set in `update_site(...)` to include the new fields:

```python
    allowed = {"site_name", "gsc_property", "ga4_property_id", "dataforseo_target_domain",
               "is_active", "vertical", "location"}
```

- [ ] **Step 4: Write the idempotent column-add + backfill management command**

Create `apps/sync/management/commands/add_project_fields.py`:

```python
"""One-off, idempotent migration: adds vertical/location/slug columns to the
SQLAlchemy-managed `sites` table (Django migrations don't cover fusehealth.db —
see .claude/DATABASE.md) and backfills slug for any existing rows that don't have one.

Safe to run multiple times: each ALTER TABLE is guarded by a PRAGMA table_info check,
and slug backfill only touches rows where slug IS NULL.
"""
from django.core.management.base import BaseCommand
from sqlalchemy import select, text

from pipeline.db.schema import Site
from pipeline.services.site_service import slugify_unique
from pipeline.utils.db_connection import get_session


class Command(BaseCommand):
    help = "Add vertical/location/slug columns to sites and backfill slug for existing rows."

    def handle(self, *args, **options):
        with get_session() as session:
            bind = session.get_bind()
            existing_cols = {row[1] for row in bind.execute(text("PRAGMA table_info(sites)"))}

            for col_name, ddl in [
                ("vertical", "ALTER TABLE sites ADD COLUMN vertical VARCHAR(255)"),
                ("location", "ALTER TABLE sites ADD COLUMN location VARCHAR(255) DEFAULT 'United States'"),
                ("slug", "ALTER TABLE sites ADD COLUMN slug VARCHAR(100)"),
            ]:
                if col_name not in existing_cols:
                    bind.execute(text(ddl))
                    self.stdout.write(f"Added column: sites.{col_name}")
                else:
                    self.stdout.write(f"Column already present, skipping: sites.{col_name}")

            rows = session.execute(select(Site).where(Site.slug.is_(None))).scalars().all()
            for site in rows:
                site.slug = slugify_unique(session, site.site_name or site.site_url)
                self.stdout.write(f"Backfilled slug for site #{site.id}: {site.slug}")
            if not rows:
                self.stdout.write("No rows needed a slug backfill.")

        self.stdout.write(self.style.SUCCESS("add_project_fields complete."))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test pipeline.services.tests.test_site_service`
Expected: `Ran 2 tests in ...s\n\nOK`

- [ ] **Step 6: Run it against the real dev database**

Run: `python manage.py add_project_fields`
Expected: output shows the three columns added (or already present) and the existing
`fusehealth.com` site backfilled with a slug (e.g. `Backfilled slug for site #1: fusehealth`).

- [ ] **Step 7: Commit**

```bash
git add pipeline/db/schema.py pipeline/services/site_service.py apps/sync/management/commands/add_project_fields.py pipeline/services/tests/
git commit -m "feat(pipeline): add vertical/location/slug to Site, backfill via idempotent command"
```

---

### Task 4: `GET /api/projects` and `POST /api/projects`

**Files:**
- Create: `apps/api/serializers.py`
- Modify: `apps/api/views.py`
- Modify: `apps/api/urls.py`
- Create: `apps/api/tests/test_projects.py`

**Interfaces:**
- Consumes: `pipeline.services.site_service.list_sites`, `slugify_unique`,
  `pipeline.db.schema.Site`, `pipeline.utils.db_connection.get_session`.
- Produces: `apps.api.serializers.ProjectSerializer` — `{id, domain, name, vertical,
  location}` shape, consumed by Task 7's overview view (for resolving `slug` → `site_url`).

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_projects.py`:

```python
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db
import pipeline.utils.db_connection as db_connection


def _auth_client(user) -> APIClient:
    token = Token.objects.get(user=user)  # created by the Task 2 signal
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


class ProjectsEndpointTests(APITestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        self.db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(self.db_path))
        self._settings_ctx = override_settings(ANALYTICS_DB_PATH=self.db_path)
        self._settings_ctx.enable()
        self.addCleanup(self._settings_ctx.disable)

        self.user = get_user_model().objects.create_user("founder1", password="x")
        self.client_auth = _auth_client(self.user)

    def test_list_projects_empty(self):
        resp = self.client_auth.get("/api/projects")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_create_then_list_project(self):
        resp = self.client_auth.post("/api/projects", {"domain": "fusehealth.com", "name": "FuseHealth"}, format="json")
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["domain"], "fusehealth.com")
        self.assertEqual(body["name"], "FuseHealth")
        self.assertEqual(body["id"], "fusehealth")

        resp = self.client_auth.get("/api/projects")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["id"], "fusehealth")

    def test_create_missing_domain_is_400(self):
        resp = self.client_auth.post("/api/projects", {"name": "No domain"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects")
        self.assertEqual(resp.status_code, 401)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_projects`
Expected: FAIL — `404` (no route yet) on every call.

- [ ] **Step 3: Write the serializer**

Create `apps/api/serializers.py`:

```python
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

    def get_domain(self, site) -> str:
        from pipeline.services.site_service import _bare_domain
        return _bare_domain(site.site_url)


class ProjectCreateSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    vertical = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
```

- [ ] **Step 4: Write the view**

In `apps/api/views.py`, add:

```python
from rest_framework import status
from sqlalchemy import select

from pipeline.services.site_service import add_site, list_sites
from pipeline.utils.db_connection import get_session
from pipeline.db.schema import Site

from .serializers import ProjectCreateSerializer, ProjectSerializer


class ProjectListCreateView(APIView):
    def get(self, request):
        sites = list_sites(active_only=True)
        return Response(ProjectSerializer(sites, many=True).data)

    def post(self, request):
        payload = ProjectCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        site_url = data["domain"].strip()
        new_id = add_site(
            site_url=site_url,
            site_name=data.get("name") or None,
            vertical=data.get("vertical") or None,
            location=data.get("location") or "United States",
        )
        with get_session() as session:
            site = session.get(Site, new_id)
            body = ProjectSerializer(site).data
        return Response(body, status=status.HTTP_201_CREATED)
```

- [ ] **Step 5: Wire the route**

In `apps/api/urls.py`, change to:

```python
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("ping", views.PingView.as_view(), name="ping"),
    path("projects", views.ProjectListCreateView.as_view(), name="projects"),
]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_projects`
Expected: `Ran 4 tests in ...s\n\nOK`

- [ ] **Step 7: Commit**

```bash
git add apps/api/serializers.py apps/api/views.py apps/api/urls.py apps/api/tests/test_projects.py
git commit -m "feat(api): add GET/POST /api/projects"
```

---

### Task 5: Extract Overview raw-data functions into `overview_service.py`

**Files:**
- Create: `apps/dashboard/services/overview_service.py`
- Modify: `apps/dashboard/views.py`
- Create: `apps/dashboard/services/tests/test_overview_service.py`

**Interfaces:**
- Produces: `get_kpi_raw(site_id, curr_start, curr_end, prev_start, prev_end) -> tuple[dict,
  dict]` (current, previous raw numeric stats — clicks/impressions/ctr/avg_position).
- Produces: `format_kpi_cards(current: dict, previous: dict) -> list[dict]` — the old
  template-formatted card shape, byte-for-byte what `_get_kpi_stats` used to return as its
  first element.
- Produces: `query_top_pages_raw(site_id, start, end, limit=10) -> list[dict]` — raw numeric
  rows (`{page, clicks, impressions, ctr}` as numbers, not formatted strings).
- Produces: `query_daily_traffic_raw(site_id, start, end) -> list[dict]` — `[{date, clicks,
  impressions}]` raw numeric rows.
- Produces: `get_ai_summary_text(site_id) -> str | None`, `parse_ai_summary(text) ->
  list[dict]` — unchanged behavior, just relocated.
- Consumed by: Task 7's `ProjectOverviewView`.

This task is a pure refactor — same behavior, new location. No new functionality yet.

- [ ] **Step 1: Write the pinning test (captures current behavior before moving code)**

Create `apps/dashboard/services/tests/__init__.py` (empty file).

Create `apps/dashboard/services/tests/test_overview_service.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.test import TestCase, override_settings
from sqlalchemy import select

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, SEODaily, AISummary
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class OverviewServiceTests(TestCase):
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
            session.add_all([
                SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                         clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                         landing_page="https://fusehealth.com/a"),
                SEODaily(date=date(2026, 7, 2), site_id="sc-domain:fusehealth.com",
                         clicks=120, impressions=1100, ctr=0.109, avg_position=7.5,
                         landing_page="https://fusehealth.com/a"),
                SEODaily(date=date(2026, 6, 1), site_id="sc-domain:fusehealth.com",
                         clicks=50, impressions=900, ctr=0.055, avg_position=9.0,
                         landing_page="https://fusehealth.com/a"),
            ])

    def test_get_kpi_raw_sums_current_period(self):
        from apps.dashboard.services.overview_service import get_kpi_raw
        current, previous = get_kpi_raw(
            "sc-domain:fusehealth.com",
            date(2026, 7, 1), date(2026, 7, 2),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        self.assertEqual(current["clicks"], 220)
        self.assertEqual(current["impressions"], 2100)
        self.assertEqual(previous["clicks"], 50)

    def test_format_kpi_cards_matches_old_shape(self):
        from apps.dashboard.services.overview_service import get_kpi_raw, format_kpi_cards
        current, previous = get_kpi_raw(
            "sc-domain:fusehealth.com",
            date(2026, 7, 1), date(2026, 7, 2),
            date(2026, 6, 1), date(2026, 6, 1),
        )
        cards = format_kpi_cards(current, previous)
        self.assertEqual(cards[0]["label"], "Clicks")
        self.assertEqual(cards[0]["value"], "220")

    def test_query_top_pages_raw_returns_numbers(self):
        from apps.dashboard.services.overview_service import query_top_pages_raw
        pages = query_top_pages_raw("sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2))
        self.assertEqual(pages[0]["clicks"], 220)
        self.assertIsInstance(pages[0]["clicks"], int)

    def test_query_daily_traffic_raw(self):
        from apps.dashboard.services.overview_service import query_daily_traffic_raw
        points = query_daily_traffic_raw("sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2))
        self.assertEqual(len(points), 2)
        self.assertEqual(points[0]["date"], "2026-07-01")
        self.assertEqual(points[0]["clicks"], 100)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_overview_service`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.dashboard.services.overview_service'`.

- [ ] **Step 3: Create the service module**

Create `apps/dashboard/services/overview_service.py`:

```python
"""Overview page data — raw calculators (shared by the old Django view and the new
DRF API view) plus the old view's presentation formatters. Query logic lives here
exactly once; each caller formats it however its output needs (see
docs/superpowers/specs/2026-07-10-limitless-migration-roadmap-and-phaseA-design.md §2.2)."""

from datetime import date

from sqlalchemy import func, select

from pipeline.db.schema import SEODaily, AISummary
from pipeline.utils.db_connection import get_session


def get_kpi_raw(site_id: str, curr_start: date, curr_end: date,
                 prev_start: date, prev_end: date) -> tuple[dict, dict]:
    """Raw current/previous period stats: clicks, impressions, ctr, avg_position."""
    with get_session() as session:
        def get_stats(start, end):
            row = session.execute(
                select(
                    func.sum(SEODaily.clicks).label("clicks"),
                    func.sum(SEODaily.impressions).label("impressions"),
                    func.avg(SEODaily.ctr).label("ctr"),
                    func.avg(SEODaily.avg_position).label("avg_position"),
                )
                .where(SEODaily.site_id == site_id, SEODaily.date >= start, SEODaily.date <= end)
            ).first()
            return {
                "clicks": row.clicks or 0,
                "impressions": row.impressions or 0,
                "ctr": row.ctr or 0.0,
                "avg_position": row.avg_position or 0.0,
            }
        return get_stats(curr_start, curr_end), get_stats(prev_start, prev_end)


def format_kpi_cards(current: dict, previous: dict) -> list[dict]:
    """Old dashboard/overview.html template shape: pre-formatted display strings."""
    def calc_delta(curr_val, prev_val):
        if not prev_val:
            return "0%", "neutral"
        delta_pct = ((curr_val - prev_val) / prev_val) * 100
        direction = "up" if delta_pct > 0 else "down" if delta_pct < 0 else "neutral"
        return f"{abs(delta_pct):.1f}%", direction

    def calc_delta_inv(curr_val, prev_val):
        if not prev_val:
            return "0%", "neutral"
        delta_pct = ((curr_val - prev_val) / prev_val) * 100
        direction = "up" if delta_pct < 0 else "down" if delta_pct > 0 else "neutral"
        return f"{abs(delta_pct):.1f}%", direction

    clicks_delta, clicks_dir = calc_delta(current["clicks"], previous["clicks"])
    impr_delta, impr_dir = calc_delta(current["impressions"], previous["impressions"])
    ctr_delta, ctr_dir = calc_delta(current["ctr"], previous["ctr"])
    pos_delta, pos_dir = calc_delta_inv(current["avg_position"], previous["avg_position"])

    return [
        {"label": "Clicks", "value": f"{int(current['clicks']):,}", "delta": clicks_delta, "delta_dir": clicks_dir},
        {"label": "Impressions", "value": f"{int(current['impressions']):,}", "delta": impr_delta, "delta_dir": impr_dir},
        {"label": "Avg. CTR", "value": f"{(current['ctr'] * 100):.2f}%", "delta": ctr_delta, "delta_dir": ctr_dir},
        {"label": "Avg. Position", "value": f"{current['avg_position']:.1f}", "delta": pos_delta, "delta_dir": pos_dir},
    ]


def query_top_pages_raw(site_id: str, start_date: date, end_date: date, limit: int = 10) -> list[dict]:
    """Raw numeric top pages by clicks. Key is `page` (matches the old template's
    variable name); Task 7 renames it to `url` for the API shape."""
    with get_session() as session:
        rows = session.execute(
            select(
                SEODaily.landing_page,
                func.sum(SEODaily.clicks).label("total_clicks"),
                func.sum(SEODaily.impressions).label("total_impressions"),
                func.avg(SEODaily.ctr).label("avg_ctr"),
            )
            .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date,
                   SEODaily.landing_page.isnot(None))
            .group_by(SEODaily.landing_page)
            .order_by(func.sum(SEODaily.clicks).desc())
            .limit(limit)
        ).all()
        return [
            {
                "page": row.landing_page or "/",
                "clicks": int(row.total_clicks or 0),
                "impressions": int(row.total_impressions or 0),
                "ctr": round((row.avg_ctr or 0) * 100, 1),
            }
            for row in rows
        ]


def query_daily_traffic_raw(site_id: str, start_date: date, end_date: date) -> list[dict]:
    """Raw [{date, clicks, impressions}] points — the API `trend[]` shape and also the
    source data for the old view's Plotly chart dict."""
    with get_session() as session:
        rows = session.execute(
            select(
                SEODaily.date,
                func.sum(SEODaily.clicks).label("total_clicks"),
                func.sum(SEODaily.impressions).label("total_impressions"),
            )
            .where(SEODaily.site_id == site_id, SEODaily.date >= start_date, SEODaily.date <= end_date)
            .group_by(SEODaily.date)
            .order_by(SEODaily.date.asc())
        ).all()
        return [
            {"date": str(r.date), "clicks": int(r.total_clicks or 0), "impressions": int(r.total_impressions or 0)}
            for r in rows
        ]


def build_traffic_chart(points: list[dict]) -> dict | None:
    """Old view's Plotly chart spec, built from query_daily_traffic_raw's output."""
    if not points:
        return None
    dates = [p["date"] for p in points]
    clicks = [p["clicks"] for p in points]
    impressions = [p["impressions"] for p in points]
    return {
        "data": [
            {"x": dates, "y": clicks, "name": "Clicks", "type": "scatter", "mode": "lines",
             "line": {"color": "#4f46e5", "width": 3, "shape": "spline"},
             "fill": "tozeroy", "fillcolor": "rgba(79,70,229,0.08)"},
            {"x": dates, "y": impressions, "name": "Impressions", "type": "scatter", "mode": "lines",
             "yaxis": "y2", "line": {"color": "#94a3b8", "width": 2, "dash": "dot", "shape": "spline"}},
        ],
        "layout": {
            "font": {"family": "Inter", "size": 12, "color": "#64748b"},
            "paper_bgcolor": "white", "plot_bgcolor": "white",
            "margin": {"l": 40, "r": 40, "t": 10, "b": 30},
            "xaxis": {"showgrid": False},
            "yaxis": {"gridcolor": "#f1f5f9", "zeroline": False},
            "yaxis2": {"overlaying": "y", "side": "right", "showgrid": False},
            "legend": {"orientation": "h", "y": 1.15, "x": 0},
            "hovermode": "x unified",
        },
        "config": {"displayModeBar": False, "responsive": True},
    }


def get_ai_summary_text(site_id: str) -> str | None:
    with get_session() as session:
        row = (
            session.execute(
                select(AISummary).where(AISummary.site_id == site_id)
                .order_by(AISummary.week_start.desc()).limit(1)
            ).scalars().first()
        )
        return row.summary_text if row and row.summary_text else None


def parse_ai_summary(text: str) -> list[dict]:
    """Turn the markdown AI summary into structured, styled sections (critical/win/info)."""
    import re
    from django.utils.html import escape, mark_safe

    if not text:
        return []

    def render_inline(s: str):
        s = escape(s.strip())
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return mark_safe(s)

    def classify(title: str) -> str:
        t = title.lower()
        if "🔴" in title or "critical" in t or "issue" in t or "fix" in t:
            return "critical"
        if "🟢" in title or "win" in t or "maintain" in t or "strength" in t:
            return "win"
        return "info"

    sections, current = [], None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        heading = re.match(r"^#{1,4}\s+(.*)$", line)
        if heading:
            title = heading.group(1).strip()
            current = {"kind": classify(title), "title": title, "items": [], "prose": []}
            sections.append(current)
            continue
        if current is None:
            current = {"kind": "info", "title": "Summary", "items": [], "prose": []}
            sections.append(current)
        item = re.match(r"^\s*(?:\d+\.|[-*])\s+(.*)$", line)
        if item:
            current["items"].append(render_inline(item.group(1)))
        else:
            current["prose"].append(render_inline(line))
    return sections
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.dashboard.services.tests.test_overview_service`
Expected: `Ran 4 tests in ...s\n\nOK`

- [ ] **Step 5: Update the old view to import from the service (delete the duplicated code)**

In `apps/dashboard/views.py`:

1. Delete the function bodies of `_get_kpi_stats`, `_get_top_pages`, `_get_traffic_chart`,
   `_get_ai_summary`, `_parse_ai_summary` (lines 58–142 and 167–297 in the current file —
   confirm exact line numbers with `grep -n "^def _get_kpi_stats\|^def _parse_ai_summary" apps/dashboard/views.py` before deleting, since Task 3/4 edits may have shifted them).
2. Add this import near the top of the file, alongside the existing `pipeline.*` imports:

```python
from apps.dashboard.services.overview_service import (
    get_kpi_raw, format_kpi_cards, query_top_pages_raw, query_daily_traffic_raw,
    build_traffic_chart, get_ai_summary_text, parse_ai_summary,
)
```

3. In the `overview(request)` view function, replace:

```python
    stats, seo_curr, seo_prev = _get_kpi_stats(site_id, curr_start, curr_end, prev_start, prev_end)
    top_pages = _get_top_pages(site_id, curr_start, curr_end)
    chart = _get_traffic_chart(site_id, curr_start, curr_end)
    ai_summary = _get_ai_summary(site_id)
    ai_summary_sections = _parse_ai_summary(ai_summary)
```

with:

```python
    seo_curr, seo_prev = get_kpi_raw(site_id, curr_start, curr_end, prev_start, prev_end)
    stats = format_kpi_cards(seo_curr, seo_prev)
    top_pages_raw = query_top_pages_raw(site_id, curr_start, curr_end)
    top_pages = [
        {"page": p["page"], "clicks": f"{p['clicks']:,}", "impressions": f"{p['impressions']:,}", "ctr": f"{p['ctr']:.1f}%"}
        for p in top_pages_raw
    ]
    chart = build_traffic_chart(query_daily_traffic_raw(site_id, curr_start, curr_end))
    ai_summary = get_ai_summary_text(site_id)
    ai_summary_sections = parse_ai_summary(ai_summary)
```

4. Any other call sites of the deleted `_get_*` functions elsewhere in `views.py` (check with
   `grep -n "_get_kpi_stats\|_get_top_pages\|_get_traffic_chart\|_get_ai_summary\|_parse_ai_summary" apps/dashboard/views.py`
   — expect none outside `overview()`, since these were overview-specific helpers) must be
   updated the same way; if any are found, apply the equivalent substitution.

- [ ] **Step 6: Verify the old Overview page still renders identically**

Run: `python manage.py test apps.dashboard`
Expected: existing dashboard tests still pass (no regressions).

Then manually: start the dev server (`python manage.py runserver`), log in, open `/` (the old
Overview page), and confirm KPI cards, chart, top pages, and AI summary render the same as
before this refactor.

- [ ] **Step 7: Commit**

```bash
git add apps/dashboard/services/overview_service.py apps/dashboard/services/tests/ apps/dashboard/views.py
git commit -m "refactor(dashboard): extract Overview query logic into overview_service.py"
```

---

### Task 6: Range-to-period-dates helper + API-shaped builders

**Files:**
- Modify: `apps/dashboard/services/overview_service.py`
- Modify: `apps/dashboard/services/tests/test_overview_service.py`

**Interfaces:**
- Produces: `range_to_period_dates(range_key: str, anchor: date) -> tuple[date, date, date,
  date]` — `range_key` is `"7d" | "30d" | "90d"`; consumed by Task 7.
- Produces: `build_kpis_api(current: dict, previous: dict) -> list[dict]` — `[{label, value,
  delta, unit}]`, numeric (not string) values, matching `HANDOFF_SPEC.md §2.1`'s `kpi` shape.
- Produces: `build_top_pages_api(site_id, start, end, limit=6) -> list[dict]` — `[{url,
  clicks, impressions, ctr}]`.

- [ ] **Step 1: Write the failing tests**

Append to `apps/dashboard/services/tests/test_overview_service.py`:

```python
class RangeAndApiShapeTests(TestCase):
    def test_range_to_period_dates_7d(self):
        from apps.dashboard.services.overview_service import range_to_period_dates
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates("7d", date(2026, 7, 10))
        self.assertEqual((curr_end - curr_start).days, 6)
        self.assertEqual(curr_end, date(2026, 7, 9))

    def test_range_to_period_dates_90d(self):
        from apps.dashboard.services.overview_service import range_to_period_dates
        curr_start, curr_end, prev_start, prev_end = range_to_period_dates("90d", date(2026, 7, 10))
        self.assertEqual((curr_end - curr_start).days, 89)

    def test_range_to_period_dates_defaults_to_30d(self):
        from apps.dashboard.services.overview_service import range_to_period_dates
        a = range_to_period_dates("garbage", date(2026, 7, 10))
        b = range_to_period_dates("30d", date(2026, 7, 10))
        self.assertEqual(a, b)

    def test_build_kpis_api_shape(self):
        from apps.dashboard.services.overview_service import build_kpis_api
        current = {"clicks": 220, "impressions": 2100, "ctr": 0.10, "avg_position": 8.0}
        previous = {"clicks": 200, "impressions": 2000, "ctr": 0.09, "avg_position": 9.0}
        kpis = build_kpis_api(current, previous)
        self.assertEqual(kpis[0], {"label": "Clicks", "value": 220, "delta": 10.0, "unit": "%"})
        self.assertEqual(kpis[3]["unit"], "pos")
        self.assertEqual(kpis[3]["value"], 8.0)

    def test_build_top_pages_api_shape(self):
        from apps.dashboard.services.overview_service import build_top_pages_api
        pages = build_top_pages_api("sc-domain:fusehealth.com", date(2026, 7, 1), date(2026, 7, 2))
        self.assertEqual(pages[0]["url"], "https://fusehealth.com/a")
        self.assertIn("ctr", pages[0])
        self.assertNotIn("page", pages[0])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_overview_service.RangeAndApiShapeTests`
Expected: FAIL — `ImportError` (functions don't exist yet).

- [ ] **Step 3: Implement**

Add to `apps/dashboard/services/overview_service.py` (add `from datetime import timedelta` to
the existing `from datetime import date` import line at the top):

```python
def range_to_period_dates(range_key: str, anchor: date) -> tuple[date, date, date, date]:
    """Maps the API's stateless `range` query param (7d/30d/90d) to
    (curr_start, curr_end, prev_start, prev_end), anchored to the latest data date.
    Unlike the old view, this never reads/writes Django session state — the API is
    stateless per HANDOFF_SPEC.md's caching model (cache key includes `range`)."""
    from pipeline.utils.period_utils import get_period_dates

    if range_key == "7d":
        return get_period_dates("weekly", 0, anchor=anchor)
    if range_key == "90d":
        custom_end = anchor - timedelta(days=1)
        custom_start = custom_end - timedelta(days=89)
        return get_period_dates("custom", 0, custom_start=custom_start, custom_end=custom_end, anchor=anchor)
    return get_period_dates("monthly", 0, anchor=anchor)  # "30d" and any unrecognized value


def build_kpis_api(current: dict, previous: dict) -> list[dict]:
    """HANDOFF_SPEC.md §2.1 kpi shape: [{label, value, delta, unit}], numeric — not the old
    view's pre-formatted display strings (see format_kpi_cards for that)."""
    from pipeline.utils.period_utils import compute_delta

    clicks_delta = compute_delta(current["clicks"], previous["clicks"])
    impr_delta = compute_delta(current["impressions"], previous["impressions"])
    ctr_delta = compute_delta(current["ctr"] * 100, previous["ctr"] * 100)
    # Avg position: lower is better, so "improvement" delta is (previous - current).
    pos_delta_val = round((previous["avg_position"] or 0) - (current["avg_position"] or 0), 1)

    return [
        {"label": "Total clicks", "value": int(current["clicks"]), "delta": clicks_delta["pct_change"], "unit": "%"},
        {"label": "Impressions", "value": int(current["impressions"]), "delta": impr_delta["pct_change"], "unit": "%"},
        {"label": "Avg. CTR", "value": round(current["ctr"] * 100, 2), "delta": ctr_delta["pct_change"], "unit": "%"},
        {"label": "Avg. position", "value": round(current["avg_position"], 1), "delta": pos_delta_val, "unit": "pos"},
    ]


def build_top_pages_api(site_id: str, start_date: date, end_date: date, limit: int = 6) -> list[dict]:
    """HANDOFF_SPEC.md overview `topPages[≤6]` shape: [{url, clicks, impressions, ctr}]."""
    raw = query_top_pages_raw(site_id, start_date, end_date, limit=limit)
    return [{"url": p["page"], "clicks": p["clicks"], "impressions": p["impressions"], "ctr": p["ctr"]} for p in raw]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_overview_service`
Expected: `Ran 9 tests in ...s\n\nOK`

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/services/overview_service.py apps/dashboard/services/tests/test_overview_service.py
git commit -m "feat(dashboard): add range_to_period_dates + API-shaped KPI/top-pages builders"
```

---

### Task 7: `GET /api/projects/<slug>/overview` — the Phase A deliverable

**Files:**
- Modify: `apps/api/serializers.py`
- Modify: `apps/api/views.py`
- Modify: `apps/api/urls.py`
- Modify: `apps/dashboard/services/overview_service.py`
- Create: `apps/api/tests/test_overview.py`

**Interfaces:**
- Consumes: everything produced by Tasks 5–6, plus `apps.dashboard.views._get_ads_overview`,
  `_get_keywords_overview`, `_get_positioning_overview`, `_get_technical_issues`,
  `_get_recent_anomalies`, `apps.dashboard.services.decision_engine.generate_signals`,
  `generate_ad_overlap_signals` (all pre-existing, unmodified — imported, not duplicated).
- Produces: `GET /api/projects/<slug>/overview?range=7d|30d|90d` → `{kpis, pillars, modules,
  priority, signals, trend, summary, topPages}` per `HANDOFF_SPEC.md §1`/`§2.2`.

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_overview.py`:

```python
import tempfile
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, SEODaily
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class OverviewEndpointTests(APITestCase):
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
            session.add(Site(site_url="sc-domain:fusehealth.com", site_name="FuseHealth",
                              slug="fusehealth", is_active=1))
            # Two rows, not one: range_to_period_dates("30d", anchor) treats `anchor` (the max
            # data date) as "today" and excludes it from the current window (yesterday =
            # anchor - 1 — pre-existing behavior in pipeline/utils/period_utils.py, not
            # introduced here). The 07-01 row is the max date and therefore intentionally
            # excluded; 06-30 is the one actually inside the current-period window.
            session.add(SEODaily(date=date(2026, 6, 30), site_id="sc-domain:fusehealth.com",
                                  clicks=100, impressions=1000, ctr=0.10, avg_position=8.0,
                                  landing_page="https://fusehealth.com/a"))
            session.add(SEODaily(date=date(2026, 7, 1), site_id="sc-domain:fusehealth.com",
                                  clicks=999, impressions=9999, ctr=0.50, avg_position=1.0,
                                  landing_page="https://fusehealth.com/a"))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_overview_returns_all_required_top_level_keys(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for key in ["kpis", "pillars", "modules", "priority", "signals", "trend", "summary", "topPages"]:
            self.assertIn(key, body, f"missing top-level key: {key}")

    def test_kpis_use_real_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        kpis = resp.json()["kpis"]
        clicks_kpi = next(k for k in kpis if k["label"] == "Total clicks")
        # 100, not 100+999=1099 — the 07-01 row is the max date, excluded from the current
        # window by design (see the comment on the seeded rows in setUp above).
        self.assertEqual(clicks_kpi["value"], 100)

    def test_unbuilt_pillars_report_setup_state_not_fake_data(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview", {"range": "30d"})
        pillars = resp.json()["pillars"]
        site_health = next(p for p in pillars if p["label"] == "Site health")
        self.assertEqual(site_health["state"], "setup")
        self.assertIsNone(site_health["value"])

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/overview")
        self.assertEqual(resp.status_code, 404)

    def test_range_defaults_to_30d(self):
        resp = self.client_auth.get("/api/projects/fusehealth/overview")
        self.assertEqual(resp.status_code, 200)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_overview`
Expected: FAIL — `404` (route doesn't exist yet).

- [ ] **Step 3: Add the pillar/module/priority/summary builders**

Add to `apps/dashboard/services/overview_service.py`:

```python
def build_pillars(site_id: str, kpis_current: dict, kpis_previous: dict, top3_count: int) -> list[dict]:
    """HANDOFF_SPEC.md §2.2 pillar shape. Site health / Paid ROAS / AI visibility report
    state='setup' — Site Audit, Ads, and AI Optimization aren't built yet (Phases C/D)."""
    clicks_delta = round(
        ((kpis_current["clicks"] - kpis_previous["clicks"]) / kpis_previous["clicks"] * 100)
        if kpis_previous["clicks"] else 0, 1,
    )
    return [
        {"label": "Organic clicks", "target": "overview", "valueKind": "num",
         "value": int(kpis_current["clicks"]), "delta": clicks_delta, "deltaUnit": "%",
         "sub": f"clicks", "state": "ok"},
        {"label": "Avg. position", "target": "positioning", "valueKind": "pos",
         "value": round(kpis_current["avg_position"], 1), "delta": None, "deltaUnit": "pos",
         "sub": f"{top3_count} keywords in top 3", "state": "ok"},
        {"label": "Site health", "target": "pages", "valueKind": "score",
         "value": None, "delta": None, "deltaUnit": "pts", "sub": "Site Audit not set up yet",
         "state": "setup"},
        {"label": "Paid ROAS", "target": "ads", "valueKind": "roas",
         "value": None, "delta": None, "deltaUnit": None, "sub": "Ads not connected yet",
         "state": "setup"},
        {"label": "AI visibility", "target": "ai", "valueKind": "pct",
         "value": None, "delta": None, "deltaUnit": "pts", "sub": "not set up yet",
         "state": "setup"},
    ]


def build_modules(seo_module_stat: str, keywords_count: int, top3_count: int,
                   avg_position: float) -> list[dict]:
    """HANDOFF_SPEC.md §2.2 module-status card shape."""
    return [
        {"label": "SEO Performance", "target": "seo", "stat": seo_module_stat, "sub": "",
         "tone": "ok"},
        {"label": "Keywords", "target": "keywords", "stat": f"{keywords_count} tracked",
         "sub": f"{top3_count} in top 3", "tone": "ok"},
        {"label": "Position Tracking", "target": "positioning", "stat": f"#{avg_position:.1f} avg",
         "sub": "", "tone": "ok"},
        {"label": "Backlinks", "target": "backlinks", "stat": "Not connected", "sub": "",
         "tone": "setup"},
        {"label": "Site Audit", "target": "pages", "stat": "Not set up", "sub": "",
         "tone": "setup"},
        {"label": "AI Optimization", "target": "ai", "stat": "Not set up",
         "sub": "Track ChatGPT, Claude, Gemini", "tone": "setup"},
        {"label": "Paid Media", "target": "ads", "stat": "Not connected", "sub": "",
         "tone": "setup"},
    ]


def build_summary_lists(ai_summary_sections: list[dict]) -> dict:
    """HANDOFF_SPEC.md summary{wins, critical, watch} — flattens the parsed AI summary
    sections (see parse_ai_summary) into complete-sentence string lists per kind."""
    out = {"wins": [], "critical": [], "watch": []}
    kind_to_key = {"win": "wins", "critical": "critical", "info": "watch"}
    for section in ai_summary_sections:
        key = kind_to_key.get(section["kind"], "watch")
        for item in section["items"]:
            out[key].append(str(item))
        for para in section["prose"]:
            out[key].append(str(para))
    return out
```

- [ ] **Step 4: Add the serializer + view + URL**

Add to `apps/api/serializers.py`:

```python
class OverviewQuerySerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=["7d", "30d", "90d"], required=False, default="30d")
```

Add to `apps/api/views.py`:

```python
from datetime import date as date_cls

from sqlalchemy import func

from apps.dashboard.services.overview_service import (
    get_kpi_raw, build_kpis_api, build_top_pages_api, query_daily_traffic_raw,
    range_to_period_dates, get_ai_summary_text, parse_ai_summary, build_summary_lists,
    build_pillars, build_modules,
)
from apps.dashboard.services.decision_engine import generate_signals, generate_ad_overlap_signals
from apps.dashboard.views import (
    _get_ads_overview, _get_keywords_overview, _get_positioning_overview,
)
from pipeline.db.schema import SEODaily

from .serializers import OverviewQuerySerializer


class ProjectOverviewView(APIView):
    def get(self, request, slug):
        with get_session() as session:
            site = session.execute(select(Site).where(Site.slug == slug)).scalars().first()
        if site is None:
            from django.http import Http404
            raise Http404(f"No project with slug '{slug}'")
        site_id = site.site_url

        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        range_key = query.validated_data["range"]

        with get_session() as session:
            anchor = session.execute(
                select(func.max(SEODaily.date)).where(SEODaily.site_id == site_id)
            ).scalar() or date_cls.today()

        curr_start, curr_end, prev_start, prev_end = range_to_period_dates(range_key, anchor)

        kpis_current, kpis_previous = get_kpi_raw(site_id, curr_start, curr_end, prev_start, prev_end)
        kpis = build_kpis_api(kpis_current, kpis_previous)
        trend = query_daily_traffic_raw(site_id, curr_start, curr_end)
        top_pages = build_top_pages_api(site_id, curr_start, curr_end)

        ads_overview, ads_curr, ads_prev = _get_ads_overview(site_id, curr_start, curr_end, prev_start, prev_end)
        signals = generate_signals(kpis_current, kpis_previous, ads_curr, ads_prev)
        signals += generate_ad_overlap_signals(site_id, curr_start, curr_end)
        signals = signals[:3]

        keywords_overview = _get_keywords_overview(site_id)
        positioning = _get_positioning_overview(site_id)
        top3_count = sum(1 for k in keywords_overview if k["position"] not in ("N/A",) and float(k["position"] or 99) <= 3)

        pillars = build_pillars(site_id, kpis_current, kpis_previous, top3_count)
        seo_stat = f"{int(kpis_current['clicks']):,} clicks"
        modules = build_modules(seo_stat, len(keywords_overview), top3_count, kpis_current["avg_position"])

        ai_summary_sections = parse_ai_summary(get_ai_summary_text(site_id))
        summary = build_summary_lists(ai_summary_sections)

        return Response({
            "kpis": kpis,
            "pillars": pillars,
            "modules": modules,
            "priority": [],  # Alerts feed is Phase B — no fake data, empty until built
            "signals": signals,
            "trend": trend,
            "summary": summary,
            "topPages": top_pages,
        })
```

Update `apps/api/urls.py`:

```python
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("ping", views.PingView.as_view(), name="ping"),
    path("projects", views.ProjectListCreateView.as_view(), name="projects"),
    path("projects/<slug:slug>/overview", views.ProjectOverviewView.as_view(), name="project-overview"),
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_overview`
Expected: `Ran 5 tests in ...s\n\nOK`

- [ ] **Step 6: Run the full test suite to check nothing broke**

Run: `python manage.py test`
Expected: all tests across `apps.accounts`, `apps.api`, `apps.dashboard`, `apps.sync`,
`pipeline` pass.

- [ ] **Step 7: Manual check against real data**

Run: `python manage.py runserver`, log in as any seeded user, then in another terminal:

```bash
curl -H "Authorization: Bearer $(python manage.py shell -c "from django.contrib.auth import get_user_model; from rest_framework.authtoken.models import Token; u = get_user_model().objects.first(); print(Token.objects.get(user=u).key)")" \
  "http://localhost:8000/api/projects/fusehealth/overview?range=30d"
```

Expected: real fusehealth.com KPI numbers matching what the old Overview page (`/`) shows for
the same period.

- [ ] **Step 8: Commit**

```bash
git add apps/dashboard/services/overview_service.py apps/api/serializers.py apps/api/views.py apps/api/urls.py apps/api/tests/test_overview.py
git commit -m "feat(api): add GET /api/projects/<slug>/overview with real data"
```

---

### Task 8: Serve the SPA at `/app/` with token bootstrap

**Files:**
- Create: `apps/dashboard/spa_views.py`
- Modify: `config/urls.py`
- Create: `static/spa/` (copy of SPA assets — see Step 1)
- Create: `apps/dashboard/tests/test_spa_views.py`

**Interfaces:**
- Produces: `GET /app/` → the SPA HTML, login-protected, with `FuseAPI.config` bootstrapped.
- Consumes: `request.user.auth_token.key` (from Task 2's signal — every user has one).

- [ ] **Step 1: Copy the SPA assets into the Django static tree**

Run (from the `fusehealth/` project root):

```bash
mkdir -p static/spa
cp "Limitless marketing dashboard2/Limitless Marketing Dashboard v2.dc.html" static/spa/index.html
cp "Limitless marketing dashboard2/support.js" static/spa/support.js
cp -r "Limitless marketing dashboard2/app" static/spa/app
cp -r "Limitless marketing dashboard2/assets" static/spa/assets
cp -r "Limitless marketing dashboard2/static/css" static/spa/css
```

Expected: `static/spa/index.html`, `static/spa/support.js`, `static/spa/app/api.js`,
`static/spa/app/fixtures.js`, `static/spa/assets/`, `static/spa/css/global.css` all present
(`ls static/spa/app` should list `api.js fixtures.js`).

In `static/spa/index.html`, fix the relative asset paths so they resolve correctly when served
from `/static/spa/` instead of the design tool's export root — open the file and update:
- `<script src="./support.js">` → `<script src="/static/spa/support.js">`
- `<script src="app/fixtures.js">` → `<script src="/static/spa/app/fixtures.js">`
- `<script src="app/api.js">` → `<script src="/static/spa/app/api.js">`

(Check for any other relative `src="assets/..."` or `href="static/css/..."` references in the
file with `grep -n 'src="[^/]|href="[^h/]' static/spa/index.html` and prefix each the same way
— `/static/spa/assets/...` and `/static/spa/css/...` respectively.)

- [ ] **Step 2: Write the failing test**

Create `apps/dashboard/tests/__init__.py` if `apps/dashboard/tests.py` exists as a single file
— check first (`ls apps/dashboard/tests.py`); if it's a file (not a package), rename it to
`apps/dashboard/tests/__init__.py` (`mkdir apps/dashboard/tests && git mv apps/dashboard/tests.py apps/dashboard/tests/__init__.py`) before adding the new test module, so
both coexist as a package.

Create `apps/dashboard/tests/test_spa_views.py`:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token


class SpaViewTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_logged_in_gets_html_with_bootstrap_script(self):
        user = get_user_model().objects.create_user("viewer", password="x")
        self.client.force_login(user)
        resp = self.client.get("/app/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/html; charset=utf-8")
        token = Token.objects.get(user=user).key
        body = resp.content.decode()
        self.assertIn(f"FuseAPI.config.authToken = '{token}'", body)
        self.assertIn("FuseAPI.config.baseUrl = ''", body)
        # The bootstrap script must come after api.js defines window.FuseAPI, and before </body>.
        self.assertLess(body.index("/static/spa/app/api.js"), body.index("FuseAPI.config.authToken"))
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.tests.test_spa_views`
Expected: FAIL — `404` (no `/app/` route yet).

- [ ] **Step 4: Write the view**

Create `apps/dashboard/spa_views.py`:

```python
"""Serves the approved Limitless Marketing SPA (static/spa/index.html) at /app/.

Deliberately does NOT run the file through Django's template engine — the file is
full of raw JS object literals (`{ id: 'x', ... }`) that would collide catastrophically
with Django's `{{ }}` / `{% %}` template syntax. Instead we read the raw bytes and do a
single targeted string replacement to inject a bootstrap <script> that configures
window.FuseAPI before the app's own code runs.
"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

_SPA_HTML_PATH = Path(settings.BASE_DIR) / "static" / "spa" / "index.html"


@login_required
def spa_index(request):
    html = _SPA_HTML_PATH.read_text(encoding="utf-8")
    token = request.user.auth_token.key
    bootstrap = (
        "<script>"
        "window.FuseAPI.config.baseUrl = '';"
        f"window.FuseAPI.config.authToken = '{token}';"
        "</script>"
    )
    # Injected right before </body> so it runs after every script tag the file itself
    # defines (including app/api.js, which creates window.FuseAPI) has already executed.
    html = html.replace("</body>", bootstrap + "</body>")
    return HttpResponse(html, content_type="text/html")
```

- [ ] **Step 5: Wire the route**

In `config/urls.py`, add the import and route:

```python
from apps.dashboard.spa_views import spa_index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('', include('apps.dashboard.urls')),
    path('', include('apps.sync.urls')),
    path('api/', include('apps.api.urls')),
    path('app/', spa_index, name='spa'),
]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python manage.py test apps.dashboard.tests.test_spa_views`
Expected: `Ran 2 tests in ...s\n\nOK`

- [ ] **Step 7: Manual browser verification**

Run: `python manage.py runserver`. In a browser:
1. Visit `http://localhost:8000/app/` while logged out → redirected to the login page.
2. Log in, then visit `http://localhost:8000/app/` again → the SPA loads (sidebar, Overview
   tab visible).
3. Open browser dev tools console, type `FuseAPI.config` → confirm `{baseUrl: "", authToken:
   "<a real token string>", ...}`.
4. Confirm the Overview tab shows real fusehealth.com numbers (not the fixture placeholder
   data) — compare against what `/` (the old Django Overview page) shows for the same period.
5. Check the Network tab: confirm requests go to `/api/projects/fusehealth/overview?range=...`
   and return `200` with real JSON (not fixture-shaped mock data).

If step 3 or 5 shows `FuseAPI` is undefined or the config wasn't applied, the injection point
needs adjusting — inspect where `<script src="/static/spa/app/api.js">` actually lands in the
rendered DOM (the file's `<helmet>`/`<x-dc>` wrapper may relocate it via `support.js`) and move
the bootstrap `<script>` in `spa_views.py` to fire after that, e.g. via a `DOMContentLoaded`
listener instead of a bare inline script, adjusting the test in Step 2 to match.

- [ ] **Step 8: Update the checklist and commit**

In `.claude/checklist.md`, add a new `## PHASE A — SPA + API Foundation ✅` section (after the
existing `PHASE 6` section) summarizing what was built: DRF foundation, Bearer token auth,
project model (`vertical`/`location`/`slug` on `Site`), `/api/projects` CRUD, `/api/projects/
<slug>/overview` with real data, SPA served at `/app/`. Mark it complete and note the old
dashboard still serves unchanged at `/`.

```bash
git add static/spa apps/dashboard/spa_views.py apps/dashboard/tests config/urls.py .claude/checklist.md
git commit -m "feat(dashboard): serve the approved SPA at /app/ with token bootstrap"
```

---

## Self-review notes (for the implementer)

- **Spec coverage:** every §2 item from the Phase A design doc (DRF app, Bearer auth, project
  model, SPA serving, Overview endpoint, verification) has a task. Settings expansion, Ads
  mutations, Backlinks/Audit/AI/Off-site, Keyword/Prompt Explorer are explicitly Phase B–D —
  not in this plan, per the design's §2.8 scope boundary.
- **Known footgun documented inline:** `pipeline.utils.db_connection.get_session()` memoizes
  its engine per-process (`_SessionFactory` global) — every test that needs an isolated
  analytics DB must reset it in `setUp`/`addCleanup`, or tests will leak state into each other.
  This pattern is spelled out in full in Tasks 3, 4, 5, 6, 7's test code — copy it exactly for
  any later phase's tests too.
- **Open item resolved:** the design doc's §3 open item on `range` vs. session `period_mode`
  was resolved in Task 6 — the API is fully stateless per-request, never touching Django
  session period state, matching `HANDOFF_SPEC.md`'s per-`(project, view, range)` caching model.
- **Open item resolved:** static-file serving strategy — Task 8 copies SPA assets into
  `static/spa/`, served via a dedicated login-protected view (not Django's generic static
  file serving, since the HTML needs per-request token injection).
