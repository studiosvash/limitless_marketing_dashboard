# Phase D — AI Optimization Implementation Plan

Branch: `phase-d-ai-optimization` (based on `phase-c4-ads`)
Design spec: `docs/superpowers/specs/2026-07-13-phaseD-ai-optimization-design.md` — read it
first for the full mutation contract and real-vs-honest-empty mapping.

## Global constraints (apply to every task)

- **No fake data, ever.** `mentions`/`gap` on `aiKeywords[]` rows are ALWAYS `0`/`false` — do
  not derive them from `AIKeywordData` fields that look plausible (there is no real signal for
  "does this keyword mention us" in that table; inventing one would be exactly the fabrication
  this project forbids).
- These are genuinely new Django ORM models (`apps/dashboard/models.py`, `django_internal.db`)
  — NOT SQLAlchemy analytics tables. Follow the existing `Insight` model's pattern exactly:
  plain `site_url` CharField (no FK across databases), no `Meta.app_label` surprises.
- Test-class hygiene: every new test class must define its own `setUp()` and inherit directly
  from `TestCase`/`APITestCase` — never inherit a sibling test class.
- Run the full suite (`python manage.py test`) after each task and report the pass count.

---

## Task 1: Django models — `AITarget`, `AIPromptList`, `AIPrompt`

Add to `apps/dashboard/models.py`:

```python
class AITarget(models.Model):
    """AI Optimization tracked brand/competitors — one row per project. First-party app
    state (which brand/competitors/aliases to watch for in AI-answer-engine mentions), not
    analytics data -- same site_url-string-keyed pattern as Insight."""
    site_url = models.CharField(max_length=255, unique=True, db_index=True)
    brand = models.CharField(max_length=255, blank=True, default="")
    aliases = models.JSONField(default=list)
    competitors = models.JSONField(default=list)
    setup_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AIPromptList(models.Model):
    site_url = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class AIPrompt(models.Model):
    site_url = models.CharField(max_length=255, db_index=True)
    list = models.ForeignKey(AIPromptList, null=True, blank=True, on_delete=models.SET_NULL, related_name="prompts")
    text = models.TextField()
    tracked_models = models.JSONField(default=list)  # which LLMs this prompt WOULD check once
                                                       # 'run' exists -- persisted preference,
                                                       # never a live/fabricated check result
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
```

Run `python manage.py makemigrations dashboard` and commit the generated migration file.

**Tests** (new file `apps/dashboard/tests/test_ai_models.py` or extend an existing dashboard
model test file if one exists — check first): basic create/uniqueness (`AITarget.site_url` is
unique — assert a second create for the same `site_url` raises `IntegrityError`), `AIPrompt`
list FK nullability (a prompt with no list is valid), default `JSONField` values are real empty
lists (`[]`), not `None`.

Report DONE with commit hash and test count after this task.

---

## Task 2: `ai_service.py` — real `aiKeywords` reshape + `build_ai_response`

Create `apps/dashboard/services/ai_service.py`:

```python
"""AI Optimization page (Phase D) — real reshape of AIKeywordData plus first-party
targets/lists/prompts persistence (Django ORM), plus honest empty/zero placeholders for
everything requiring the LLM Mentions/Responses/scraper infrastructure that doesn't exist
anywhere in this codebase. See docs/superpowers/specs/2026-07-13-phaseD-ai-optimization-design.md."""
import json
import logging
from datetime import date, timedelta

from sqlalchemy import func, select

from apps.dashboard.models import AITarget, AIPromptList, AIPrompt
from pipeline.db.schema import AIKeywordData
from pipeline.utils.db_connection import get_session

logger = logging.getLogger(__name__)

MENTION_PLATFORMS = [
    {"id": "chatgpt", "label": "ChatGPT", "color": "#10a37f"},
    {"id": "claude", "label": "Claude", "color": "#d97757"},
    {"id": "gemini", "label": "Gemini", "color": "#4285f4"},
    {"id": "perplexity", "label": "Perplexity", "color": "#20808d"},
]


def query_ai_keywords_raw(site_id: str) -> list[dict]:
    """Real reshape of AIKeywordData for the latest captured snapshot date -- same
    "latest date per site" query pattern as the old MVP's apps/dashboard/views.py
    _get_ai_keywords (reused deliberately, not reinvented: AIKeywordData rows are captured
    as one full snapshot per sync date, so "latest date" is the correct notion of current
    state, not a per-keyword max-date dedup). mentions/gap are ALWAYS 0/False -- no LLM
    Mentions data exists to derive them from; never fabricate a signal."""
    try:
        with get_session() as session:
            latest = session.execute(
                select(func.max(AIKeywordData.date)).where(AIKeywordData.site_id == site_id)
            ).scalar()
            if latest is None:
                return []
            rows = session.execute(
                select(AIKeywordData)
                .where(AIKeywordData.site_id == site_id, AIKeywordData.date == latest)
            ).scalars().all()
    except Exception as e:
        logger.error(f"query_ai_keywords_raw error: {e}", exc_info=True)
        return []

    out = []
    for r in rows:
        ai_vol = r.ai_search_volume or 0
        g_vol = r.search_volume or 0
        try:
            trend = json.loads(r.trend) if r.trend else []
        except (ValueError, TypeError):
            trend = []
        if len(trend) < 12:
            trend = trend + [0] * (12 - len(trend))
        out.append({
            "kw": r.keyword,
            "aiVolume": ai_vol,
            "gVolume": g_vol,
            "ratio": round(ai_vol / g_vol * 100) if g_vol else 0,
            "intent": r.intent or "",
            "trend": trend[-12:],
            "mentions": 0,   # honest -- no LLM Mentions data exists
            "gap": False,    # honest -- no LLM Mentions data exists
        })
    return out


def _target_dict(t: "AITarget | None") -> dict:
    if t is None:
        return {"brand": "", "aliases": [], "competitors": []}
    return {"brand": t.brand, "aliases": t.aliases, "competitors": t.competitors}


def build_ai_response(site_id: str) -> dict:
    """API-shaped AI Optimization response. Real: targets/lists/prompts/setupDone (first-party
    ORM data), aiKeywords (real AIKeywordData reshape). Honest empty/zero: everything requiring
    LLM Mentions/Responses/scraper infra that doesn't exist -- sov/trend/topPages/topDomains/
    prompts[].results/suggestions/history/budget/costs/next_run."""
    target = AITarget.objects.filter(site_url=site_id).first()
    lists = list(AIPromptList.objects.filter(site_url=site_id).values("id", "name"))
    prompts_qs = AIPrompt.objects.filter(site_url=site_id).select_related(None)
    prompts = [
        {"id": p.id, "text": p.text, "listId": p.list_id, "models": p.tracked_models, "results": []}
        for p in prompts_qs
    ]

    return {
        "setupDone": bool(target and target.setup_done),
        "targets": _target_dict(target),
        "budget": {"cap": 0, "spent": 0, "weekly_est": 0},
        "costs": {"model": None, "inspect": None},
        "next_run": None,
        "mentionPlatforms": MENTION_PLATFORMS,
        "llmPlatforms": [p["id"] for p in MENTION_PLATFORMS],
        "sov": {"you": 0, "delta": 0, "rows": []},
        "kpis": {"mentions": 0, "impressions": 0, "cited_pages": 0, "prompt_coverage": {"cited": 0, "total": len(prompts)}},
        "trend": [],
        "topPages": [],
        "topDomains": [],
        "lists": lists,
        "prompts": prompts,
        "suggestions": [],
        "aiKeywords": query_ai_keywords_raw(site_id),
        "history": [],
    }
```

**Note on `suggestions[]`:** the wizard's 3rd step ("starter prompts") expects candidate prompt
suggestions to pick from. Real suggestion generation (from the tracked keyword portfolio, e.g.
templated off `KeywordRanking`) is a reasonable, real, NOT-fabricated feature (deriving prompt
text from real tracked keywords, not inventing data) — but scope it OUT of this task unless
trivial; an honest empty `suggestions: []` just means the wizard's step 3 shows no pre-filled
options, which is honest, not broken (the SPA's "custom prompts" textarea still works — verify
this in Task 4). Note this decision in your task report either way.

**Tests** (new file `apps/dashboard/services/tests/test_ai_service.py`):
- `query_ai_keywords_raw`: seed 2 `AIKeywordData` rows for different keywords on the SAME
  (latest) date (one with a full 12-element `trend` JSON array, one with `trend=None`) — assert
  both are reshaped correctly, the null-trend row gets a real 12-zero list (not a crash, not
  `None`). Seed an OLDER-dated row for a third keyword — assert it's excluded (proving the
  query scopes to the latest snapshot date only, not all history). Assert `mentions` and `gap`
  are ALWAYS `0`/`False` regardless of the row's other values — this is the test that enforces
  the no-fabrication contract for this function, do not skip it. Empty-DB case returns `[]`.
- `build_ai_response`: with no `AITarget` row at all, assert `setupDone is False` and
  `targets == {"brand": "", "aliases": [], "competitors": []}` (not a crash, not `None`). With
  a real `AITarget(setup_done=True)`, assert `setupDone is True` and `targets` reflects it.
  Seed `AIPromptList`/`AIPrompt` rows, assert they appear in `lists`/`prompts`. Exact-equality-
  assert every honest-empty/zero field (`sov`, `trend`, `topPages`, `topDomains`, `suggestions`,
  `history`, `budget`, `costs`, `next_run`).

Report DONE with commit hash and test count after this task.

---

## Task 3: `GET`/`POST /api/projects/<slug>/ai...` endpoints

In `apps/api/views.py`, add:

```python
from apps.dashboard.models import AITarget, AIPromptList, AIPrompt
from apps.dashboard.services.ai_service import build_ai_response

@method_decorator(login_not_required, name="dispatch")
class ProjectAIView(APIView):
    def get(self, request, slug):
        site_id = resolve_project_or_404(slug).site_url
        return Response(build_ai_response(site_id))


@method_decorator(login_not_required, name="dispatch")
class ProjectAIActionView(APIView):
    def post(self, request, slug, action):
        site_id = resolve_project_or_404(slug).site_url
        handler = getattr(self, f"_handle_{action.replace('-', '_')}", None)
        if handler is None:
            return Response({"detail": f"Unknown or not-yet-available action: {action}"}, status=400)
        return handler(request, site_id)

    def _handle_setup(self, request, site_id):
        data = request.data
        target, _ = AITarget.objects.update_or_create(
            site_url=site_id,
            defaults={
                "brand": data.get("brand", ""),
                "aliases": data.get("aliases", []),
                "competitors": data.get("competitors", []),
                "setup_done": True,
            },
        )
        for text in data.get("prompts", []):
            if text and text.strip():
                AIPrompt.objects.create(site_url=site_id, text=text.strip())
        return Response({})

    def _handle_targets(self, request, site_id):
        data = request.data
        AITarget.objects.update_or_create(
            site_url=site_id,
            defaults={"brand": data.get("brand", ""), "aliases": data.get("aliases", []), "competitors": data.get("competitors", [])},
        )
        return Response({})

    def _handle_prompts(self, request, site_id):
        data = request.data
        list_id = data.get("listId")
        texts = [t.strip() for t in data.get("texts", []) if t and t.strip()]
        created = [AIPrompt(site_url=site_id, list_id=list_id, text=t) for t in texts]
        AIPrompt.objects.bulk_create(created)
        return Response({"added": len(created)})

    def _handle_prompts_remove(self, request, site_id):
        AIPrompt.objects.filter(site_url=site_id, id=request.data.get("id")).delete()
        return Response({})

    def _handle_prompts_config(self, request, site_id):
        AIPrompt.objects.filter(site_url=site_id, id=request.data.get("id")).update(
            tracked_models=request.data.get("models", [])
        )
        return Response({})

    def _handle_lists(self, request, site_id):
        data = request.data
        op = data.get("op")
        if op == "create":
            obj = AIPromptList.objects.create(site_url=site_id, name=data.get("name", "Untitled"))
            return Response({"id": obj.id})
        if op == "rename":
            AIPromptList.objects.filter(site_url=site_id, id=data.get("id")).update(name=data.get("name", ""))
            return Response({})
        if op == "delete":
            AIPromptList.objects.filter(site_url=site_id, id=data.get("id")).delete()
            return Response({})
        return Response({"detail": f"Unknown list op: {op}"}, status=400)
```

In `apps/api/urls.py`, add BOTH routes (action must come after the more specific GET route in
Django's URL resolution — verify no conflict with the existing pattern, e.g. check whether
`slug:slug` also greedily matches sub-paths; test both routes work independently):
```python
path("projects/<slug:slug>/ai", views.ProjectAIView.as_view(), name="project-ai"),
path("projects/<slug:slug>/ai/<str:action>", views.ProjectAIActionView.as_view(), name="project-ai-action"),
```

**Tests** (new file `apps/api/tests/test_ai.py`):
- `GET`: real-data case (seed `AITarget`+`AIPromptList`+`AIPrompt`, assert response reflects
  them), empty-DB case (assert honest `setupDone: false`/empty shape, not a crash), 404 unknown
  slug, 401 unauthenticated.
- `POST .../ai/setup`: assert `AITarget` created with `setup_done=True` and the right
  brand/aliases/competitors, assert prompts created. Call `GET` again afterward in the same
  test and assert the change is reflected (proves the mutation persists, not just returns 200).
- `POST .../ai/targets`: assert an existing target is updated, not duplicated (call twice,
  assert `AITarget.objects.filter(site_url=...).count() == 1`).
- `POST .../ai/prompts`: assert `{"added": N}` matches the real count created, assert list
  scoping works (`listId` set correctly).
- `POST .../ai/prompts-remove`: assert the specific prompt is gone, others survive.
- `POST .../ai/lists` with `op="create"`: assert the returned `id` is a real, usable FK (create
  a prompt with that `listId` afterward, assert it links correctly).
- `POST .../ai/run` / `.../ai/inspect` (or any unhandled action): assert a clean 400, not a 500
  or an unhandled crash.
- 401/404 coverage on at least one mutation endpoint (auth is shared middleware, but confirm
  it's not accidentally bypassed for POST).

After this task: update `.claude/FILE_INDEX.md` and `.claude/checklist.md` (add a "PHASE D — AI
Optimization" section, mirroring Phase C's sections — include the "genuinely new mutation
endpoints, first Phase D/E feature to need them" framing from the design spec).

Report DONE with commit hash and final full-suite test count after this task.

---

## Task 4: SPA fidelity fix — crash guard + remove the false "Live" claim

**Three independent, narrow fixes in `static/spa/index.html`** (a third was added after Task 2's
review found `query_ai_keywords_raw` now honestly returns `ratio: None` — not a fabricated `0%`
— when there's no Google-volume denominator to compare against; see `ai_service.py`'s current
code and commit `fbed14e` for why):

0. **`aiKeywords[]` row `ratio` null-guard** (`static/spa/index.html:5894-5895`, inside the
   `aiv.kwRows = rows.map(...)` block): `ratioLabel: r.ratio + '%'` renders the literal string
   `"null%"` when `r.ratio` is `None` (JS `null`); `ratioStyle`'s `r.ratio >= 30` comparison is
   safe (evaluates to `false` for `null`, no crash) but the label itself is wrong. Fix:
   ```js
   ratioLabel: r.ratio == null ? '—' : r.ratio + '%',
   ```
   Verify the segment-filter counts (`heavy: allRows.filter(r => r.ratio >= 30).length`, line
   ~5824) and the KPI computation (`allRows.filter(r => r.ratio >= 30).length`, line ~5817)
   still behave sensibly with `ratio: null` rows mixed in — `null >= 30` is `false`, so these
   rows are correctly excluded from "AI-heavy," not crashed on. No other fix needed there.

**Two more independent, narrow fixes in `static/spa/index.html`:**

1. **Crash fix** (line ~5627, verify exact line at implementation — search `d.trend[0].date`):
   `aiv.trendFrom = d.trend[0].date; aiv.trendTo = d.trend[d.trend.length - 1].date;` crashes
   when `trend` is honestly `[]`. Guard with a length check, e.g.:
   ```js
   aiv.trendFrom = d.trend.length ? d.trend[0].date : '';
   aiv.trendTo = d.trend.length ? d.trend[d.trend.length - 1].date : '';
   ```
   Also independently verify (don't just trust the design spec) whether anything else in the
   `if (tab === 'ai')` block — the wizard-prefill path (`~5488-5548`), the visibility sub-tab
   (`~5587-5640`), prompts/explorer (`~5642-5903`), inspector (`~5905-5931`), history
   (`~5933-5945`) — has a similar unguarded chain against an honestly-empty array/object from
   Task 2/3's real response shape. Fix any you find, using the same "guard, don't fabricate"
   principle; report every fix you make.

2. **Remove the false "Live" claim** (`static/spa/index.html:455`, in the Keywords tab's
   Keyword Explorer card header — verify exact line, this is a DIFFERENT tab from AI
   Optimization): a hardcoded `<span>...</span>Live</span> Keyword Explorer`-style badge with
   **zero data binding**. Since Keyword Explorer's real endpoint (`POST /api/research`) is
   explicitly out of scope this phase (per the design spec), this claim is flatly false the
   moment the SPA talks to the real backend instead of its fixture/demo mode. This is NOT a
   "gate on real data" fix like C3/C4's — there's no real endpoint to gate on. Remove the "Live"
   badge, or replace it with an honest label (e.g. nothing, or a muted "Beta"/no badge at all —
   use judgment on what reads cleanly; do not invent a new false claim in its place).

**Verification** (no new automated test — JS-only, no JS test harness, same limitation noted in
every prior phase's review):
- Manually trace: with `data.trend = []`, `data.targets = {"brand":"","aliases":[],"competitors":[]}`,
  `data.setupDone = false` (the real payload from Task 2/3), confirm the wizard renders without
  crashing and the dashboard branch (force `setupDone: true` mentally, or test via a seeded
  `AITarget`) doesn't crash on the trend fix.
- Confirm `<sc-if>`/`<sc-for>` tag-balance count is unchanged (unless you added a guard that
  needs one — report exactly what changed).
- Run the full Python test suite once more to confirm it's unaffected (SPA-only change).

Report DONE with commit hash after this task. This is the last task of Phase D — after this,
dispatch the final whole-branch review.
