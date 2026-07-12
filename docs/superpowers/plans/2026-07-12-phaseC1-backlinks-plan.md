# Phase C1 — Backlinks Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the Backlinks page through `GET /api/projects/<slug>/backlinks`, built
against ONLY real, existing infrastructure (the `Backlink` table + its connector). Every
field needing a not-yet-built DataForSEO sub-endpoint connector reports `state:"setup"`.

**Architecture:** Task 1 extracts the existing `_get_backlinks_summary`/`_get_backlinks_table`
into a new service module (pure refactor, fixing a second call site in `export_csv`, same
pattern as Phase B1/B3). Task 2 builds the API-shaped response with real fields populated and
unbuilt fields honestly marked `state:"setup"`. Task 3 wires the endpoint.

**Tech Stack:** Django 6.0, DRF, SQLAlchemy 2.x.

## Global Constraints

- Never call an external API from a page-rendering or API-reading view — DB-only reads.
- Route: `GET /api/projects/<slug>/backlinks`, no trailing slash, no `range` param (matches
  `HANDOFF_SPEC.md`'s endpoint table).
- `summary`, `months`, `types`, `asBuckets`, `refDomains`, `anchors`, `gapDomains` all report
  `"state": "setup"` — NEVER fabricated numbers. `kpis`, `links`, `competitors` are real.
- `_get_backlinks_summary`/`_get_backlinks_table` have TWO call sites each to check
  (`backlinks()` view AND `export_csv`'s `"backlinks"` branch) — confirmed via grep during
  plan-writing.
- `pipeline.utils.db_connection.get_session()` memoizes its engine per-process — every test
  needing an isolated temp DB must reset `db_connection._SessionFactory = None` in
  `setUp`/`addCleanup`.
- **Test-class inheritance footgun** (hit multiple times across this project): any new test
  class must have its OWN `setUp()`, inherit `TestCase`/`APITestCase` directly, never a
  sibling test class. Verify with `-v 2` before committing that every test name appears
  exactly once.

---

### Task 1: Extract backlinks raw calculators

**Files:**
- Create: `apps/dashboard/services/backlinks_service.py`
- Modify: `apps/dashboard/views.py`
- Create: `apps/dashboard/services/tests/test_backlinks_service.py`

**Interfaces:**
- Produces: `query_backlinks_summary_raw(site_id) -> dict` — `{total, live, lost,
  unique_domains, avg_dr}`, unmodified from the existing `_get_backlinks_summary`.
- Produces: `query_backlinks_table_raw(site_id, limit=200) -> list[dict]` — `{domain,
  target_url, anchor, status, dofollow, domain_rank}` per row, unmodified from the existing
  `_get_backlinks_table`.
- Consumed by: Task 2's `build_backlinks_response`, and (via the old view/export_csv,
  rewired here) the existing `/backlinks/` page.

- [ ] **Step 1: Write the pinning tests**

Create `apps/dashboard/services/tests/test_backlinks_service.py`:

```python
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Backlink
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class BacklinksRawQueryTests(TestCase):
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
                Backlink(site_id="sc-domain:fusehealth.com", referring_domain="healthline.com",
                         target_url="https://fusehealth.com/iv-therapy", anchor="iv therapy",
                         status="live", dofollow=1, domain_rank=88),
                Backlink(site_id="sc-domain:fusehealth.com", referring_domain="spamsite.net",
                         target_url="https://fusehealth.com/", anchor="", status="lost",
                         dofollow=0, domain_rank=5),
            ])

    def test_query_backlinks_summary_raw(self):
        from apps.dashboard.services.backlinks_service import query_backlinks_summary_raw
        summary = query_backlinks_summary_raw("sc-domain:fusehealth.com")
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["live"], 1)
        self.assertEqual(summary["lost"], 1)
        self.assertEqual(summary["unique_domains"], 2)

    def test_query_backlinks_table_raw(self):
        from apps.dashboard.services.backlinks_service import query_backlinks_table_raw
        rows = query_backlinks_table_raw("sc-domain:fusehealth.com")
        self.assertEqual(len(rows), 2)
        top = next(r for r in rows if r["domain"] == "healthline.com")
        self.assertEqual(top["domain_rank"], 88)
        self.assertEqual(top["status"], "live")

    def test_query_backlinks_summary_raw_returns_zeros_on_db_error(self):
        from unittest import mock
        from apps.dashboard.services import backlinks_service
        with mock.patch.object(backlinks_service, "get_session", side_effect=RuntimeError("boom")):
            summary = backlinks_service.query_backlinks_summary_raw("x")
            self.assertEqual(summary, {"total": 0, "live": 0, "lost": 0, "unique_domains": 0, "avg_dr": 0})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_backlinks_service`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Create the service module**

Create `apps/dashboard/services/backlinks_service.py`:

```python
"""Backlinks page data — raw calculators (shared by the old Django view and the new DRF API
view), extracted unmodified from apps.dashboard.views. See
docs/superpowers/specs/2026-07-12-phaseC1-backlinks-design.md for why the rich Backlink
Analytics fields (summary/months/types/asBuckets/refDomains/anchors/gapDomains) are NOT
built here — they need 5 DataForSEO sub-endpoint connectors this codebase doesn't have yet."""

from sqlalchemy import func, select

from pipeline.db.schema import Backlink
from pipeline.utils.db_connection import get_session


def query_backlinks_summary_raw(site_id: str) -> dict:
    try:
        with get_session() as session:
            rows = session.execute(
                select(
                    func.count(Backlink.id).label("total"),
                    func.count(Backlink.id).filter(Backlink.status == 'live').label("live"),
                    func.count(Backlink.id).filter(Backlink.status == 'lost').label("lost"),
                    func.count(func.distinct(Backlink.referring_domain)).label("unique_domains"),
                    func.avg(Backlink.domain_rank).label("avg_dr")
                ).where(Backlink.site_id == site_id)
            ).first()
            if not rows:
                return {"total": 0, "live": 0, "lost": 0, "unique_domains": 0, "avg_dr": 0}
            return {
                "total": rows.total or 0,
                "live": rows.live or 0,
                "lost": rows.lost or 0,
                "unique_domains": rows.unique_domains or 0,
                "avg_dr": round(rows.avg_dr or 0, 1),
            }
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_backlinks_summary_raw error: {e}", exc_info=True)
        return {"total": 0, "live": 0, "lost": 0, "unique_domains": 0, "avg_dr": 0}


def query_backlinks_table_raw(site_id: str, limit: int = 200) -> list[dict]:
    try:
        with get_session() as session:
            rows = session.execute(
                select(Backlink)
                .where(Backlink.site_id == site_id)
                .order_by(Backlink.domain_rank.desc().nullslast())
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "domain": r.referring_domain,
                    "target_url": r.target_url,
                    "anchor": r.anchor or "—",
                    "status": r.status,
                    "dofollow": r.dofollow,
                    "domain_rank": r.domain_rank or 0,
                }
                for r in rows
            ]
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"query_backlinks_table_raw error: {e}", exc_info=True)
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_backlinks_service`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 5: Rewire both call sites**

In `apps/dashboard/views.py`:

1. Delete `_get_backlinks_summary` and `_get_backlinks_table`'s function bodies (confirm
   exact lines with `grep -n "^def _get_backlinks_summary\|^def _get_backlinks_table" apps/dashboard/views.py`).
2. Add the import:

```python
from apps.dashboard.services.backlinks_service import query_backlinks_summary_raw, query_backlinks_table_raw
```

3. In `backlinks(request)`, replace:

```python
    summary = _get_backlinks_summary(site_id)
    table = _get_backlinks_table(site_id)
```

with:

```python
    summary = query_backlinks_summary_raw(site_id)
    table = query_backlinks_table_raw(site_id)
```

4. In `export_csv`, find `elif table_name == "backlinks":` and replace
   `data = _get_backlinks_table(site_id, limit=5000)` with
   `data = query_backlinks_table_raw(site_id, limit=5000)`.

- [ ] **Step 6: Verify the old Backlinks page and CSV export still work**

Run: `python manage.py test apps.dashboard` — expected: pass.

Manually (or via test Client, per this project's established fallback when a live browser
isn't available): confirm `/backlinks/` still renders and the CSV export for `backlinks`
still produces rows in the same shape as before.

- [ ] **Step 7: Run the full suite and commit**

Run: `python manage.py test 2>&1 | tail -15` — expected: all pass.

```bash
git add apps/dashboard/services/backlinks_service.py apps/dashboard/services/tests/test_backlinks_service.py apps/dashboard/views.py
git commit -m "refactor(dashboard): extract backlinks query logic into backlinks_service.py"
```

---

### Task 2: `build_backlinks_response` — real fields + honest `state:"setup"`

**Files:**
- Modify: `apps/dashboard/services/backlinks_service.py`
- Modify: `apps/dashboard/services/tests/test_backlinks_service.py`

**Interfaces:**
- Consumes: `query_backlinks_summary_raw`, `query_backlinks_table_raw` (Task 1);
  `pipeline.services.competitor_service.get_tracked_competitors` (already used by Phase B3).
- Produces: `build_backlinks_response(site_id) -> dict` — full target shape, real
  `kpis`/`links`/`competitors`, `state:"setup"` for the rest. Consumed by Task 3.

- [ ] **Step 1: Write the failing tests**

Append to `apps/dashboard/services/tests/test_backlinks_service.py` (new class, own `setUp`
duplicating `BacklinksRawQueryTests`'s fixture — do NOT inherit from it):

```python
class BuildBacklinksResponseTests(TestCase):
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
            session.add(Backlink(site_id="sc-domain:fusehealth.com", referring_domain="healthline.com",
                                  target_url="https://fusehealth.com/iv-therapy", anchor="iv therapy",
                                  status="live", dofollow=1, domain_rank=88))

    def test_top_level_keys(self):
        from apps.dashboard.services.backlinks_service import build_backlinks_response
        body = build_backlinks_response("sc-domain:fusehealth.com")
        for key in ["kpis", "links", "summary", "months", "types", "asBuckets",
                    "refDomains", "anchors", "competitors", "gapDomains"]:
            self.assertIn(key, body)

    def test_kpis_and_links_are_real(self):
        from apps.dashboard.services.backlinks_service import build_backlinks_response
        body = build_backlinks_response("sc-domain:fusehealth.com")
        self.assertEqual(body["kpis"]["total"], 1)
        self.assertEqual(body["links"][0]["domain"], "healthline.com")

    def test_unbuilt_fields_report_setup_not_fake_data(self):
        from apps.dashboard.services.backlinks_service import build_backlinks_response
        body = build_backlinks_response("sc-domain:fusehealth.com")
        self.assertEqual(body["summary"], {"state": "setup"})
        self.assertEqual(body["months"], [])
        self.assertEqual(body["types"], [])
        self.assertEqual(body["asBuckets"], [])
        self.assertEqual(body["refDomains"], [])
        self.assertEqual(body["anchors"], [])
        self.assertEqual(body["gapDomains"], [])

    def test_competitors_uses_real_tracked_list(self):
        from unittest import mock
        from apps.dashboard.services import backlinks_service
        with mock.patch.object(backlinks_service, "get_tracked_competitors", return_value=["driphydration.com"]):
            body = backlinks_service.build_backlinks_response("sc-domain:fusehealth.com")
            self.assertEqual(body["competitors"], ["driphydration.com"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.dashboard.services.tests.test_backlinks_service.BuildBacklinksResponseTests`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

Add to `apps/dashboard/services/backlinks_service.py` (add the import at the top of the file
alongside the existing ones):

```python
from pipeline.services.competitor_service import get_tracked_competitors
```

```python
def build_backlinks_response(site_id: str) -> dict:
    """HANDOFF_SPEC.md `backlinks` view shape. Only kpis/links/competitors are real — the
    rest need DataForSEO sub-endpoint connectors this codebase doesn't have yet, so they
    honestly report state:"setup" rather than fabricated numbers. See
    docs/superpowers/specs/2026-07-12-phaseC1-backlinks-design.md."""
    summary_raw = query_backlinks_summary_raw(site_id)
    links = query_backlinks_table_raw(site_id)

    kpis = {
        "total": summary_raw["total"],
        "live": summary_raw["live"],
        "lost": summary_raw["lost"],
        "referring_domains": summary_raw["unique_domains"],
        "avg_rank": summary_raw["avg_dr"],
    }

    return {
        "kpis": kpis,
        "links": links,
        "summary": {"state": "setup"},
        "months": [],
        "types": [],
        "asBuckets": [],
        "refDomains": [],
        "anchors": [],
        "competitors": get_tracked_competitors(site_id),
        "gapDomains": [],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_backlinks_service`
Expected: all pass (3 from Task 1 + 4 new = 7).

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/services/backlinks_service.py apps/dashboard/services/tests/test_backlinks_service.py
git commit -m "feat(dashboard): add build_backlinks_response with honest setup states"
```

---

### Task 3: `GET /api/projects/<slug>/backlinks` endpoint

**Files:**
- Modify: `apps/api/views.py`
- Modify: `apps/api/urls.py`
- Create: `apps/api/tests/test_backlinks.py`

**Interfaces:**
- Consumes: `build_backlinks_response` (Task 2), `resolve_project_or_404`.
- Produces: `GET /api/projects/<slug>/backlinks` → the shape from Task 2.

- [ ] **Step 1: Write the failing tests**

Create `apps/api/tests/test_backlinks.py`:

```python
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from pipeline.db.engine import get_engine
from pipeline.db.schema import init_db, Site, Backlink
from pipeline.utils.db_connection import get_session
import pipeline.utils.db_connection as db_connection


class BacklinksEndpointTests(APITestCase):
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
            session.add(Backlink(site_id="sc-domain:fusehealth.com", referring_domain="healthline.com",
                                  target_url="https://fusehealth.com/iv-therapy", anchor="iv therapy",
                                  status="live", dofollow=1, domain_rank=88))

        user = get_user_model().objects.create_user("founder1", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_backlinks_returns_real_data_and_setup_states(self):
        resp = self.client_auth.get("/api/projects/fusehealth/backlinks")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["kpis"]["total"], 1)
        self.assertEqual(body["summary"], {"state": "setup"})

    def test_unknown_slug_is_404(self):
        resp = self.client_auth.get("/api/projects/does-not-exist/backlinks")
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        resp = APIClient().get("/api/projects/fusehealth/backlinks")
        self.assertEqual(resp.status_code, 401)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.api.tests.test_backlinks`
Expected: FAIL — `404`.

- [ ] **Step 3: Implement the view**

Add to `apps/api/views.py`:

```python
from apps.dashboard.services.backlinks_service import build_backlinks_response


@method_decorator(login_not_required, name="dispatch")
class ProjectBacklinksView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_backlinks_response(site_id))
```

- [ ] **Step 4: Wire the route**

In `apps/api/urls.py`, add:

```python
    path("projects/<slug:slug>/backlinks", views.ProjectBacklinksView.as_view(), name="project-backlinks"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_backlinks`
Expected: `Ran 3 tests in ...s\n\nOK`

- [ ] **Step 6: Run the full suite**

Run: `python manage.py test 2>&1 | tail -15`
Expected: all pass.

- [ ] **Step 7: Update the checklist and commit**

Add a "PHASE C1 — Backlinks ✅ (partial: kpis/links real, analytics suite pending DataForSEO
credentials)" note to `.claude/checklist.md`, and add `apps/dashboard/services/backlinks_service.py`
to `.claude/FILE_INDEX.md`.

```bash
git add apps/api/views.py apps/api/urls.py apps/api/tests/test_backlinks.py .claude/checklist.md .claude/FILE_INDEX.md
git commit -m "feat(api): add GET /api/projects/<slug>/backlinks"
```

## Self-review notes

- **Spec coverage:** every field has a task producing it — either real data or an honest
  `state:"setup"`/empty value, per the design's scope decision.
- **No duplication:** both call sites of the two extracted functions were found and fixed
  (Task 1, `export_csv`'s second call site).
- **Scope discipline:** this plan deliberately does NOT attempt the 5 missing DataForSEO
  sub-endpoint connectors — that's real, unvalidated integration work for a future phase once
  credentials exist, not something to guess at now.
