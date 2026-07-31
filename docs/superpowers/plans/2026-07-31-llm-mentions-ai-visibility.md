# LLM Mentions AI Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the AI Optimization page's hardcoded-zero top half with real DataForSEO LLM Mentions data — share of voice against tracked competitors, brand mentions, AI impressions, cited pages and dominating domains — for every project in the dashboard.

**Architecture:** A new `dataforseo_llm_mentions` connector makes at most two API calls per project per week, writes weekly snapshot rows into two new analytics tables, and a new `llm_mentions_service` reads the latest week back into the shapes the SPA already expects. The page itself never calls an API — the database stays the single source of truth.

**Tech Stack:** Django 6 + DRF, SQLAlchemy against `data/fusehealth.db` (SQLite in tests, Postgres in production), DataForSEO AI Optimization LLM Mentions API, vanilla-JS SPA.

**Spec:** `docs/superpowers/specs/2026-07-31-llm-mentions-ai-visibility-design.md`

## Global Constraints

- **Never call an external API from a page-data endpoint.** Only the connector calls DataForSEO.
- **Never fabricate a value to fill a shape.** Return empty, `null`, or a setup marker, with a comment saying why.
- **Every analytics write goes through a `pipeline/db/writer.py` upsert helper.** Never a bare INSERT.
- **`_dedupe_by_keys(records, keys)` is MANDATORY** before every multi-row `on_conflict_do_update`. Postgres raises `CardinalityViolation` and rolls back the whole batch on a duplicate conflict key; SQLite silently hides it, so the test suite cannot catch it.
- **Every conflict-target column is NOT NULL.** Postgres does not treat `NULL = NULL` as a conflict, so a null key column duplicates on every sync instead of updating.
- **Never override `BaseConnector.sync()`.** Override `fetch()` and `_write_records()` only.
- **No module-level Django imports in `pipeline/connectors/`.** Import Django models lazily inside functions.
- **Services never raise.** Catch, log with `exc_info=True`, return a safe empty shape of the right type.
- **Do not add a frontend build step, CSS framework, or component library.** The SPA uses inline styles and text inclusion deliberately.
- `week_start` is always `d - timedelta(days=d.weekday())` (Monday of the ISO week, UTC). This is the dedupe key — one definition, used everywhere.
- Real platform values are exactly `google` (displayed "AI Overviews") and `chat_gpt` (displayed "ChatGPT") — the API offers no others. One sentinel is also stored: `all`, used only for `subject_type="discovered"` rows, because `total.sources_domain` carries no platform breakdown and splitting it by a ratio would be invented data. `all` never appears in `MENTION_PLATFORMS` and never collides with a real platform row.
- Run tests with `python manage.py test <label>`.

---

### Task 1: Analytics tables and upsert helpers

**Files:**
- Modify: `pipeline/db/schema.py` (append after `class AIKeywordData`, ~line 501)
- Modify: `pipeline/db/writer.py` (append after `upsert_ai_keyword_data`, ~line 610)
- Test: `pipeline/db/tests/test_llm_mentions_writer.py` (create)

**Interfaces:**
- Consumes: `ensure_tables`, `_ensure_site_id`, `_dedupe_by_keys` from `pipeline/db/writer.py`; `upsert_insert`, `max_batch_size` from `pipeline/db/dialect.py`.
- Produces: `LLMMentionMetric`, `LLMCitedPage` models; `upsert_llm_mention_metrics(session, records, site_id=None) -> int` and `upsert_llm_cited_pages(session, records, site_id=None) -> int`.

- [ ] **Step 1: Write the failing test**

Create `pipeline/db/tests/test_llm_mentions_writer.py`:

```python
"""Weekly LLM-mention snapshots must update in place, never accumulate duplicates."""
import json
import tempfile
from datetime import date
from pathlib import Path

from django.test import SimpleTestCase
from sqlalchemy import select

from pipeline.db.schema import LLMCitedPage, LLMMentionMetric
from pipeline.db.writer import upsert_llm_cited_pages, upsert_llm_mention_metrics
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session
from pipeline.db.schema import init_db

WEEK = date(2026, 7, 27)
SITE = "fusehealth.com"


class LLMMentionsWriterTests(SimpleTestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        self.db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(self.db_path))
        from django.test import override_settings
        self._ctx = override_settings(ANALYTICS_DB_PATH=self.db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def _metric(self, domain, platform, mentions, volume, subject_type="competitor"):
        return {
            "site_id": SITE, "week_start": WEEK, "subject_domain": domain,
            "subject_type": subject_type, "platform": platform,
            "mentions": mentions, "ai_search_volume": volume,
        }

    def test_metrics_insert_then_update_in_place(self):
        with get_session() as s:
            upsert_llm_mention_metrics(s, [self._metric("driphydration.com", "google", 3632, 1617710)])
            s.commit()
        with get_session() as s:
            upsert_llm_mention_metrics(s, [self._metric("driphydration.com", "google", 4000, 1700000)])
            s.commit()
        with get_session() as s:
            rows = s.execute(select(LLMMentionMetric)).scalars().all()
        self.assertEqual(len(rows), 1, "re-sync of the same week must UPDATE, not duplicate")
        self.assertEqual(rows[0].mentions, 4000)

    def test_platforms_are_separate_rows_for_the_same_domain(self):
        with get_session() as s:
            upsert_llm_mention_metrics(s, [
                self._metric("driphydration.com", "google", 3632, 1617710),
                self._metric("driphydration.com", "chat_gpt", 1, 32),
            ])
            s.commit()
        with get_session() as s:
            rows = s.execute(select(LLMMentionMetric)).scalars().all()
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r.mentions for r in rows), 3633)

    def test_duplicate_conflict_keys_in_one_batch_are_collapsed(self):
        # Without _dedupe_by_keys this raises CardinalityViolation on Postgres and rolls
        # back the entire batch. SQLite hides it, so this test documents the contract.
        with get_session() as s:
            n = upsert_llm_mention_metrics(s, [
                self._metric("driphydration.com", "google", 10, 100),
                self._metric("driphydration.com", "google", 20, 200),
            ])
            s.commit()
        self.assertEqual(n, 1, "duplicates on the conflict key must collapse before the insert")
        with get_session() as s:
            rows = s.execute(select(LLMMentionMetric)).scalars().all()
        self.assertEqual(rows[0].mentions, 20, "last occurrence wins")

    def test_cited_pages_round_trip_platforms_as_json(self):
        with get_session() as s:
            upsert_llm_cited_pages(s, [{
                "site_id": SITE, "week_start": WEEK,
                "url": "https://fusehealth.com/locations/dallas",
                "mentions": 36, "ai_search_volume": 1627,
                "platforms": json.dumps(["google", "chat_gpt"]),
            }])
            s.commit()
        with get_session() as s:
            row = s.execute(select(LLMCitedPage)).scalars().first()
        self.assertEqual(json.loads(row.platforms), ["google", "chat_gpt"])
        self.assertEqual(row.mentions, 36)

    def test_empty_records_write_nothing(self):
        with get_session() as s:
            self.assertEqual(upsert_llm_mention_metrics(s, []), 0)
            self.assertEqual(upsert_llm_cited_pages(s, []), 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test pipeline.db.tests.test_llm_mentions_writer`
Expected: FAIL — `ImportError: cannot import name 'LLMMentionMetric' from 'pipeline.db.schema'`

- [ ] **Step 3: Add the two models**

Append to `pipeline/db/schema.py` after `class AIKeywordData` ends (~line 501):

```python
class LLMMentionMetric(Base):
    """Weekly LLM-mention aggregate for one subject on one platform.

    Written by `dataforseo_llm_mentions` from DataForSEO's LLM Mentions API. One row per
    (site, week, subject domain, platform). `subject_type` distinguishes the project itself
    from the competitors it tracks from domains merely DISCOVERED in the same answers -- the
    grain is identical, so one table serves both the Share-of-Voice list and the
    "Domains Dominating AI Answers" list, and "which new domain is rising?" stays a
    single-table query.

    Weekly rather than daily because the API returns current state with no history: the
    snapshot IS the history, and it cannot be backfilled later.
    """
    __tablename__ = "llm_mention_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    week_start = Column(Date, nullable=False, index=True)   # Monday of the ISO week, UTC
    subject_domain = Column(String(255), nullable=False, index=True)
    subject_type = Column(String(20), nullable=False, default="discovered")  # you|competitor|discovered
    platform = Column(String(20), nullable=False, default="google")          # google|chat_gpt
    mentions = Column(Integer, nullable=False, default=0)
    ai_search_volume = Column(Integer, nullable=False, default=0)
    last_fetched = Column(DateTime, server_default=func.now())

    # Every conflict-target column is NOT NULL on purpose: Postgres does not treat NULL = NULL
    # as a conflict, so a null key would bypass ON CONFLICT and duplicate on every sync.
    __table_args__ = (
        UniqueConstraint("site_id", "week_start", "subject_domain", "platform",
                         name="uq_llm_mention_week"),
        Index("ix_llm_mention_site_week", "site_id", "week_start"),
    )


class LLMCitedPage(Base):
    """One of the project's own URLs that AI answers cited, in a given week.

    Only URLs on the project's own host are stored. The API's top_pages response also returns
    co-occurring pages from OTHER domains (a call for driphydration.com returns perfectb.com
    URLs), which would be wrong under a heading that says "Your Most-Cited Pages".
    """
    __tablename__ = "llm_cited_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(255), nullable=False, index=True, default="")
    week_start = Column(Date, nullable=False, index=True)
    url = Column(Text, nullable=False, index=True)
    mentions = Column(Integer, nullable=False, default=0)
    ai_search_volume = Column(Integer, nullable=False, default=0)
    platforms = Column(Text, nullable=True)   # JSON list, e.g. ["google", "chat_gpt"]
    last_fetched = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("site_id", "week_start", "url", name="uq_llm_cited_page_week"),
        Index("ix_llm_cited_page_site_week", "site_id", "week_start"),
    )
```

Verify `Date`, `Text`, `Index`, `UniqueConstraint`, `func` are already imported at the top of `schema.py` — they are, because `AIKeywordData` uses all of them.

- [ ] **Step 4: Add the two upsert helpers**

Append to `pipeline/db/writer.py` after `upsert_ai_keyword_data` (~line 610). Add `LLMCitedPage, LLMMentionMetric` to the existing `from pipeline.db.schema import (...)` block at the top of the file.

```python
# ─────────────────────────────────────────────
# LLM Mentions (DataForSEO AI Optimization)
# ─────────────────────────────────────────────

def upsert_llm_mention_metrics(session: Session, records: list[dict],
                               site_id: Optional[str] = None) -> int:
    """Upsert weekly LLM-mention aggregates. Unique on
    (site_id, week_start, subject_domain, platform)."""
    if not records:
        return 0

    ensure_tables(session, LLMMentionMetric)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "week_start", "subject_domain", "platform")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(LLMMentionMetric).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                k: func.coalesce(stmt.excluded[k], getattr(LLMMentionMetric, k))
                for k in update_cols
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] llm_mention_metrics: upserted {total} rows")
    return total


def upsert_llm_cited_pages(session: Session, records: list[dict],
                           site_id: Optional[str] = None) -> int:
    """Upsert the project's own cited URLs for a week. Unique on (site_id, week_start, url)."""
    if not records:
        return 0

    ensure_tables(session, LLMCitedPage)
    _ensure_site_id(records, site_id)
    for r in records:
        r.setdefault("site_id", "")

    insert = upsert_insert(session)
    BATCH_SIZE = max_batch_size(session, 80)
    _upsert_keys = ("site_id", "week_start", "url")
    records = _dedupe_by_keys(records, _upsert_keys)
    update_cols = [k for k in records[0] if k not in _upsert_keys]
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(LLMCitedPage).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(_upsert_keys),
            set_={
                k: func.coalesce(stmt.excluded[k], getattr(LLMCitedPage, k))
                for k in update_cols
            },
        )
        session.execute(stmt)
        total += len(batch)
    logger.debug(f"[writer] llm_cited_pages: upserted {total} rows")
    return total
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test pipeline.db.tests.test_llm_mentions_writer`
Expected: PASS, 5 tests

- [ ] **Step 6: Commit**

```bash
git add pipeline/db/schema.py pipeline/db/writer.py pipeline/db/tests/test_llm_mentions_writer.py
git commit -m "feat(db): llm_mention_metrics + llm_cited_pages tables and upserts"
```

---

### Task 2: Connector skeleton and the weekly spend guard

The guard is built and tested **before** any HTTP code exists, because it is the control that decides how much this feature costs. "Refresh all" pressed repeatedly must not spend repeatedly.

**Files:**
- Create: `pipeline/connectors/dataforseo_llm_mentions.py`
- Test: `pipeline/connectors/tests/test_llm_mentions_guard.py` (create)

**Interfaces:**
- Consumes: `BaseConnector`, `upsert_llm_mention_metrics`, `upsert_llm_cited_pages`, `canonical_domain` from `pipeline/utils/site_ids.py`.
- Produces: `DataForSEOLLMMentionsConnector` (`name = "dataforseo_llm_mentions"`), `week_start_for(d: date) -> date`.

- [ ] **Step 1: Write the failing test**

Create `pipeline/connectors/tests/test_llm_mentions_guard.py`:

```python
"""The weekly guard is the cost control: one API call per project per week, no matter how
many times anyone presses Refresh."""
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings

from pipeline.connectors.dataforseo_llm_mentions import (
    DataForSEOLLMMentionsConnector, week_start_for,
)
from pipeline.db.schema import init_db
from pipeline.db.writer import upsert_llm_mention_metrics
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session

SITE = "fusehealth.com"


class WeekStartTests(SimpleTestCase):
    def test_monday_of_the_iso_week(self):
        self.assertEqual(week_start_for(date(2026, 7, 31)), date(2026, 7, 27))  # Friday
        self.assertEqual(week_start_for(date(2026, 7, 27)), date(2026, 7, 27))  # Monday
        self.assertEqual(week_start_for(date(2026, 8, 2)), date(2026, 7, 27))   # Sunday


@override_settings()
class WeeklyGuardTests(SimpleTestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        db_path = str(Path(tmp) / "fusehealth.db")
        init_db(get_engine(db_path))
        self._ctx = override_settings(ANALYTICS_DB_PATH=db_path)
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

        patcher = mock.patch.dict(
            "os.environ",
            {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _connector(self):
        c = DataForSEOLLMMentionsConnector()
        # Targets come from Django's AITarget; stub the lookup so this test stays about the guard.
        c._load_targets = mock.Mock(return_value=("fusehealth", ["FuseHealth"], ["driphydration.com"]))
        c._resolve_site_url = mock.Mock(return_value=SITE)
        return c

    def test_second_fetch_in_the_same_week_makes_no_http_call(self):
        week = week_start_for(date.today())
        with get_session() as s:
            upsert_llm_mention_metrics(s, [{
                "site_id": SITE, "week_start": week, "subject_domain": "fusehealth.com",
                "subject_type": "you", "platform": "google",
                "mentions": 1, "ai_search_volume": 50,
            }])
            s.commit()

        c = self._connector()
        with mock.patch.object(c, "_call_cross_aggregation") as api:
            records = c.fetch(site_id=SITE)

        api.assert_not_called()
        self.assertEqual(records, [], "an already-stored week must return no records")

    def test_first_fetch_of_a_week_does_call_the_api(self):
        c = self._connector()
        with mock.patch.object(c, "_call_cross_aggregation", return_value={}) as api, \
             mock.patch.object(c, "_call_top_pages", return_value={}):
            c.fetch(site_id=SITE)
        api.assert_called_once()

    def test_project_with_no_brand_and_no_competitors_is_skipped(self):
        c = self._connector()
        c._load_targets = mock.Mock(return_value=("", [], []))
        with mock.patch.object(c, "_call_cross_aggregation") as api:
            records = c.fetch(site_id=SITE)
        api.assert_not_called()
        self.assertEqual(records, [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test pipeline.connectors.tests.test_llm_mentions_guard`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.connectors.dataforseo_llm_mentions'`

- [ ] **Step 3: Create the connector with the guard only**

Create `pipeline/connectors/dataforseo_llm_mentions.py`:

```python
"""
pipeline/connectors/dataforseo_llm_mentions.py — AI answer-engine visibility.

Calls DataForSEO's AI Optimization **LLM Mentions** API to answer one question per project:
when people ask AI instead of Google, do we get mentioned — and who gets mentioned instead?

Endpoints (Live, instant — no task_post/task_get polling):
  POST /v3/ai_optimization/llm_mentions/cross_aggregation_metrics
  POST /v3/ai_optimization/llm_mentions/top_pages

Writes to: llm_mention_metrics, llm_cited_pages (one weekly snapshot per project).

COST
----
At most two calls per project per week. Three things keep it there:

  1. The API returns CURRENT state with no history, so a snapshot is only worth taking once a
     week. `fetch()` checks the database first and returns [] without any HTTP call when this
     week is already stored -- pressing "Refresh all" ten times in a day costs ONE call.
  2. A single cross_aggregation call covers the project AND all its competitors, because one
     `aggregation_key` accepts up to 10 entities (domain and brand-name targets together).
  3. `top_pages` is skipped entirely unless the project's own domain was mentioned at all.

`top_domains` is never called: cross_aggregation already returns the top domains in
`total.sources_domain`. `aggregation_metrics` is never called *alongside* cross_aggregation
either -- that response already carries this project's own metrics in `items[]` -- but it IS
the fallback when cross_aggregation cannot run: it needs at least 2 targets, and a project with
no competitors would otherwise get no rows at all. Either way: one metrics call per week.
"""
import json
import logging
import os
from datetime import date, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
from pipeline.db.schema import LLMMentionMetric
from pipeline.db.writer import (
    ensure_tables, upsert_llm_cited_pages, upsert_llm_mention_metrics,
)
from pipeline.utils.db_connection import get_session
from pipeline.utils.retry import with_retry
from pipeline.utils.site_ids import canonical_domain

load_dotenv()

logger = logging.getLogger(__name__)

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
CROSS_AGG_ENDPOINT = f"{DATAFORSEO_BASE}/ai_optimization/llm_mentions/cross_aggregation_metrics"
TOP_PAGES_ENDPOINT = f"{DATAFORSEO_BASE}/ai_optimization/llm_mentions/top_pages"

# The API accepts at most 10 aggregation targets; one of them is always the project itself.
MAX_COMPETITORS = 9
# Entities inside a single aggregation_key (domain + brand + aliases) are capped at 10.
MAX_ENTITIES_PER_KEY = 10
TOP_PAGES_LIMIT = 10


def week_start_for(d: date) -> date:
    """Monday of the ISO week containing `d`. The dedupe key -- one definition, used everywhere."""
    return d - timedelta(days=d.weekday())


class DataForSEOLLMMentionsConnector(BaseConnector):
    name = "dataforseo_llm_mentions"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        if not self.login or not self.password:
            raise ValueError(
                "[dataforseo_llm_mentions] Missing DATAFORSEO_LOGIN or "
                "DATAFORSEO_PASSWORD in .env."
            )
        self.auth = (self.login, self.password)
        self._run_cost = 0.0

    # ── inputs ──────────────────────────────────────────────────────────────────────────
    def _resolve_site_url(self, site_id: Optional[str]) -> str:
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            if site:
                return site.site_url
        return site_id or ""

    def _site_location(self, site_id: Optional[str]) -> str:
        from pipeline.services.site_service import get_site
        with get_session() as session:
            site = get_site(session, site_id)
            return (site.location if site and site.location else "") or "United States"

    def _load_targets(self, site_url: str) -> tuple[str, list[str], list[str]]:
        """(brand, aliases, competitors) from the project's AITarget row.

        Django models are imported lazily: `pipeline/` must stay runnable outside Django.
        """
        from apps.dashboard.models import AITarget
        target = AITarget.objects.filter(site_url=site_url).first()
        if target is None:
            return "", [], []
        return (target.brand or "").strip(), list(target.aliases or []), list(target.competitors or [])

    def _week_already_stored(self, site_url: str, week: date) -> bool:
        from sqlalchemy import func as sa_func, select
        try:
            with get_session() as session:
                ensure_tables(session, LLMMentionMetric)
                n = session.execute(
                    select(sa_func.count()).select_from(LLMMentionMetric)
                    .where(LLMMentionMetric.site_id == site_url,
                           LLMMentionMetric.week_start == week)
                ).scalar()
            return bool(n)
        except Exception:
            # A failed check must not silently re-spend; treat "unknown" as "not stored" only
            # after logging loudly, because the alternative is a page that never updates.
            logger.warning("[dataforseo_llm_mentions] week check failed for %r", site_url,
                           exc_info=True)
            return False

    # ── HTTP (implemented in Task 3) ────────────────────────────────────────────────────
    def _call_cross_aggregation(self, payload: list[dict]) -> dict:
        raise NotImplementedError

    def _call_top_pages(self, payload: list[dict]) -> dict:
        raise NotImplementedError

    # ── orchestration ───────────────────────────────────────────────────────────────────
    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        site_url = self._resolve_site_url(site_id)
        week = week_start_for(date.today())

        if self._week_already_stored(site_url, week):
            self.logger.info(
                "[dataforseo_llm_mentions] week %s already stored for %r — no API call",
                week, site_url,
            )
            return []

        brand, aliases, competitors = self._load_targets(site_url)
        if not brand and not competitors:
            self.logger.info(
                "[dataforseo_llm_mentions] %r has no brand and no competitors — nothing to "
                "measure, skipping", site_url,
            )
            return []

        self._run_cost = 0.0
        return []   # Task 3 fills this in
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test pipeline.connectors.tests.test_llm_mentions_guard`
Expected: PASS, 6 tests. `test_first_fetch_of_a_week_does_call_the_api` passes because `_call_cross_aggregation` is mocked, so `NotImplementedError` is never raised.

- [ ] **Step 5: Commit**

```bash
git add pipeline/connectors/dataforseo_llm_mentions.py pipeline/connectors/tests/test_llm_mentions_guard.py
git commit -m "feat(llm-mentions): connector skeleton with the weekly spend guard"
```

---

### Task 3: API calls and response parsing

**Files:**
- Modify: `pipeline/connectors/dataforseo_llm_mentions.py`
- Test: `pipeline/connectors/tests/test_llm_mentions_parsing.py` (create)

**Interfaces:**
- Consumes: `week_start_for`, `DataForSEOLLMMentionsConnector` from Task 2.
- Produces: records tagged `{"_table": "metrics"}` or `{"_table": "pages"}`; `_write_records` splitting on that key.

Response shapes below were captured from real calls on 2026-07-31. Two details matter and are easy to get wrong:

1. **A `group_element` omits `mentions` entirely when the value is zero** — e.g. `{"type": "group_element", "key": "chat_gpt"}` with no other keys. Always read with `.get("mentions") or 0`.
2. **`top_pages` returns co-occurring pages from OTHER domains.** A call for `driphydration.com` returned `https://www.perfectb.com/...`. Filter to the project's own host or "Your Most-Cited Pages" will list someone else's pages.

- [ ] **Step 1: Write the failing test**

Create `pipeline/connectors/tests/test_llm_mentions_parsing.py`:

```python
"""Parsing real DataForSEO LLM Mentions responses (captured 2026-07-31)."""
from datetime import date
from unittest import mock

from django.test import SimpleTestCase

from pipeline.connectors.dataforseo_llm_mentions import DataForSEOLLMMentionsConnector

WEEK = date(2026, 7, 27)
SITE = "fusehealth.com"

CROSS_AGG = {"tasks": [{"status_code": 20000, "result": [{"items": [{
    "total": {
        "platform": [
            {"type": "group_element", "key": "google", "mentions": 5785, "ai_search_volume": 2698980},
            {"type": "group_element", "key": "chat_gpt", "mentions": 115, "ai_search_volume": 2907},
        ],
        "sources_domain": [
            {"type": "group_element", "key": "driphydration.com", "mentions": 3633, "ai_search_volume": 1617742},
            {"type": "group_element", "key": "www.youtube.com", "mentions": 1916, "ai_search_volume": 962270},
        ],
    },
    "items": [
        {"key": "fusehealth.com", "platform": [
            {"type": "group_element", "key": "google", "mentions": 1, "ai_search_volume": 50},
            {"type": "group_element", "key": "chat_gpt"},          # zero -> no 'mentions' key
        ]},
        {"key": "driphydration.com", "platform": [
            {"type": "group_element", "key": "google", "mentions": 3632, "ai_search_volume": 1617710},
            {"type": "group_element", "key": "chat_gpt", "mentions": 1, "ai_search_volume": 32},
        ]},
        {"key": "restoreiv.com", "platform": [
            {"type": "group_element", "key": "google"},            # no data at all
            {"type": "group_element", "key": "chat_gpt"},
        ]},
    ],
}]}]}]}

TOP_PAGES = {"tasks": [{"status_code": 20000, "result": [{"items": [{
    "items": [
        {"key": "https://fusehealth.com/locations/dallas", "platform": [
            {"type": "group_element", "key": "google", "mentions": 36, "ai_search_volume": 1627}]},
        {"key": "https://www.perfectb.com/some-article/", "platform": [
            {"type": "group_element", "key": "google", "mentions": 171, "ai_search_volume": 138610}]},
    ],
}]}]}}


class CrossAggregationParsingTests(SimpleTestCase):
    def _connector(self):
        with mock.patch.dict("os.environ",
                             {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"}):
            return DataForSEOLLMMentionsConnector()

    def test_own_domain_is_tagged_you_and_competitors_competitor(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        by = {(r["subject_domain"], r["platform"]): r for r in recs if r["_table"] == "metrics"}
        self.assertEqual(by[("fusehealth.com", "google")]["subject_type"], "you")
        self.assertEqual(by[("driphydration.com", "google")]["subject_type"], "competitor")

    def test_missing_mentions_key_reads_as_zero_not_a_crash(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        by = {(r["subject_domain"], r["platform"]): r for r in recs if r["_table"] == "metrics"}
        self.assertEqual(by[("fusehealth.com", "chat_gpt")]["mentions"], 0)
        self.assertEqual(by[("restoreiv.com", "google")]["mentions"], 0)

    def test_zero_data_competitor_is_still_recorded(self):
        # Absence is information: restoreiv.com at 0 must appear, not vanish.
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        domains = {r["subject_domain"] for r in recs if r["_table"] == "metrics"}
        self.assertIn("restoreiv.com", domains)

    def test_discovered_domains_come_from_total_sources_domain(self):
        recs = self._connector()._parse_cross_aggregation(
            CROSS_AGG, SITE, "fusehealth.com", ["driphydration.com", "restoreiv.com"], WEEK)
        discovered = {r["subject_domain"] for r in recs
                      if r["_table"] == "metrics" and r["subject_type"] == "discovered"}
        self.assertIn("www.youtube.com", discovered)
        # A domain already tracked must NOT be duplicated as 'discovered'.
        self.assertNotIn("driphydration.com", discovered)

    def test_non_success_status_returns_no_records(self):
        bad = {"tasks": [{"status_code": 40501, "status_message": "nope", "result": []}]}
        self.assertEqual(
            self._connector()._parse_cross_aggregation(bad, SITE, "fusehealth.com", [], WEEK), [])


class TopPagesParsingTests(SimpleTestCase):
    def _connector(self):
        with mock.patch.dict("os.environ",
                             {"DATAFORSEO_LOGIN": "u", "DATAFORSEO_PASSWORD": "p"}):
            return DataForSEOLLMMentionsConnector()

    def test_only_pages_on_our_own_host_are_kept(self):
        recs = self._connector()._parse_top_pages(TOP_PAGES, SITE, "fusehealth.com", WEEK)
        urls = [r["url"] for r in recs]
        self.assertEqual(urls, ["https://fusehealth.com/locations/dallas"])

    def test_page_record_carries_mentions_volume_and_platforms(self):
        rec = self._connector()._parse_top_pages(TOP_PAGES, SITE, "fusehealth.com", WEEK)[0]
        self.assertEqual(rec["_table"], "pages")
        self.assertEqual(rec["mentions"], 36)
        self.assertEqual(rec["ai_search_volume"], 1627)
        self.assertIn("google", rec["platforms"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test pipeline.connectors.tests.test_llm_mentions_parsing`
Expected: FAIL — `AttributeError: 'DataForSEOLLMMentionsConnector' object has no attribute '_parse_cross_aggregation'`

- [ ] **Step 3: Implement the HTTP calls, parsers and writer split**

Replace the `# ── HTTP (implemented in Task 3) ──` block in `pipeline/connectors/dataforseo_llm_mentions.py` with the following, and replace the final `return []` of `fetch()`:

```python
    # ── HTTP ────────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _unwrap(data: dict) -> dict:
        """DataForSEO envelope -> the single result object holding `items`.

        Same shape every DataForSEO connector here assumes: tasks[0].result[0].
        """
        tasks = (data or {}).get("tasks") or []
        if not tasks:
            return {}
        task = tasks[0]
        if task.get("status_code") != 20000:
            logger.warning(
                "[dataforseo_llm_mentions] Non-success status: %s — %s",
                task.get("status_code"), task.get("status_message"),
            )
            return {}
        result = task.get("result") or []
        return result[0] if result else {}

    @staticmethod
    def _group_value(group: list, key: str) -> tuple[int, int]:
        """(mentions, ai_search_volume) for one key inside a group_element list.

        A group_element carries NO `mentions` key when the value is zero, so both reads are
        `or 0` rather than a plain `.get(...)` with a default.
        """
        for el in group or []:
            if el.get("key") == key:
                return int(el.get("mentions") or 0), int(el.get("ai_search_volume") or 0)
        return 0, 0

    @with_retry(max_retries=3, base_delay=5.0)
    def _call_cross_aggregation(self, payload: list[dict]) -> dict:
        resp = requests.post(CROSS_AGG_ENDPOINT, auth=self.auth, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        self._run_cost += extract_cost(data)
        return data

    @with_retry(max_retries=3, base_delay=5.0)
    def _call_top_pages(self, payload: list[dict]) -> dict:
        resp = requests.post(TOP_PAGES_ENDPOINT, auth=self.auth, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        self._run_cost += extract_cost(data)
        return data

    # ── parsing ─────────────────────────────────────────────────────────────────────────
    def _parse_cross_aggregation(self, data: dict, site_url: str, own_domain: str,
                                 competitors: list[str], week: date) -> list[dict]:
        block = self._unwrap(data)
        items = (block.get("items") or [{}])[0] if isinstance(block.get("items"), list) else {}
        if not items:
            return []

        tracked = {canonical_domain(c) for c in competitors}
        tracked.add(own_domain)
        out: list[dict] = []

        for entry in items.get("items") or []:
            domain = canonical_domain(entry.get("key"))
            if not domain:
                continue
            subject_type = "you" if domain == own_domain else "competitor"
            for platform in ("google", "chat_gpt"):
                mentions, volume = self._group_value(entry.get("platform"), platform)
                out.append({
                    "_table": "metrics", "site_id": site_url, "week_start": week,
                    "subject_domain": domain, "subject_type": subject_type,
                    "platform": platform, "mentions": mentions, "ai_search_volume": volume,
                })

        # Domains AI cites in this space that are neither us nor a tracked competitor.
        # `total.sources_domain` carries NO platform breakdown, so these rows are stored once
        # under the sentinel platform 'all'. Splitting the total across google/chat_gpt by
        # some ratio would be invented data; 'all' says exactly what is known.
        for el in (items.get("total") or {}).get("sources_domain") or []:
            domain = canonical_domain(el.get("key"))
            if not domain or domain in tracked:
                continue
            out.append({
                "_table": "metrics", "site_id": site_url, "week_start": week,
                "subject_domain": domain, "subject_type": "discovered",
                "platform": "all",
                "mentions": int(el.get("mentions") or 0),
                "ai_search_volume": int(el.get("ai_search_volume") or 0),
            })
        return out

    def _parse_top_pages(self, data: dict, site_url: str, own_domain: str,
                         week: date) -> list[dict]:
        block = self._unwrap(data)
        items = (block.get("items") or [{}])[0] if isinstance(block.get("items"), list) else {}
        if not items:
            return []

        out: list[dict] = []
        for entry in items.get("items") or []:
            url = (entry.get("key") or "").strip()
            if not url or canonical_domain(url) != own_domain:
                # top_pages returns co-occurring pages from OTHER domains (a call for
                # driphydration.com returns perfectb.com URLs). "Your Most-Cited Pages"
                # means ours.
                continue
            mentions = 0
            volume = 0
            platforms = []
            for platform in ("google", "chat_gpt"):
                m, v = self._group_value(entry.get("platform"), platform)
                mentions += m
                volume += v
                if m:
                    platforms.append(platform)
            out.append({
                "_table": "pages", "site_id": site_url, "week_start": week, "url": url,
                "mentions": mentions, "ai_search_volume": volume,
                "platforms": json.dumps(platforms),
            })
        return out

    # ── payload building ────────────────────────────────────────────────────────────────
    # NOTE: `_entities` and the cross-aggregation payload construction inside `fetch()` were
    # already added in Task 2 (its guard test needed a real call to assert against). Leave
    # them exactly as they are — Task 3 only adds the HTTP bodies, the parsers, the
    # conditional top_pages call and `_write_records`.

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """BaseConnector hands one flat list and one session; the `_table` tag on each record
        says which table it belongs to. Both writes share the transaction, so a failure in
        either rolls back the whole week rather than leaving a half-written snapshot."""
        metrics = [{k: v for k, v in r.items() if k != "_table"}
                   for r in records if r.get("_table") == "metrics"]
        pages = [{k: v for k, v in r.items() if k != "_table"}
                 for r in records if r.get("_table") == "pages"]
        written = upsert_llm_mention_metrics(session, metrics, site_id=site_id)
        written += upsert_llm_cited_pages(session, pages, site_id=site_id)
        return written
```

Then extend the tail of `fetch()`. Task 2 already builds `own_domain`, `location`, `comps` and
`targets` and calls `_call_cross_aggregation` when `len(targets) >= 2` — keep that code and wrap
it so the response is captured, parsed and cost-recorded:

```python
        self._run_cost = 0.0
        own_domain = canonical_domain(site_url)
        location = self._site_location(site_id)
        comps = [canonical_domain(c) for c in competitors if canonical_domain(c)][:MAX_COMPETITORS]

        records: list[dict] = []
        try:
            targets = [{"aggregation_key": own_domain,
                        "target": self._entities(own_domain, [brand] + aliases)}]
            for c in comps:
                targets.append({"aggregation_key": c,
                                "target": self._entities(c, [c.split(".")[0]])})

            if len(targets) >= 2:
                data = self._call_cross_aggregation([{
                    "targets": targets,
                    "location_name": location,
                    "language_code": "en",
                }])
                records.extend(
                    self._parse_cross_aggregation(data, site_url, own_domain, comps, week))
            else:
                # cross_aggregation_metrics requires at least 2 targets. With no competitors
                # there is no share of voice to compute; the service renders the "add
                # competitors" state rather than a meaningless 100%.
                self.logger.info(
                    "[dataforseo_llm_mentions] %r has no competitors — share of voice "
                    "needs at least one, recording own mentions only", site_url,
                )

            own_mentions = sum(
                r["mentions"] for r in records
                if r.get("subject_type") == "you" and r.get("_table") == "metrics"
            )
            if own_mentions:
                pages_data = self._call_top_pages([{
                    "target": [{"domain": own_domain}],
                    "location_name": location,
                    "language_code": "en",
                    "items_list_limit": TOP_PAGES_LIMIT,
                }])
                records.extend(self._parse_top_pages(pages_data, site_url, own_domain, week))
            else:
                self.logger.info(
                    "[dataforseo_llm_mentions] %r has no AI mentions this week — skipping "
                    "the top_pages call (nothing to list, and it would cost money)", site_url,
                )
        finally:
            record_cost(
                self.name, site_url, self._run_cost, units=len(records) or 1,
                notes=f"llm_mentions cross_aggregation + top_pages, week {week}",
            )

        self.logger.info(
            "[dataforseo_llm_mentions] %r week %s — %d rows", site_url, week, len(records))
        return records
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test pipeline.connectors.tests.test_llm_mentions_parsing pipeline.connectors.tests.test_llm_mentions_guard`
Expected: PASS, 13 tests

- [ ] **Step 5: Commit**

```bash
git add pipeline/connectors/dataforseo_llm_mentions.py pipeline/connectors/tests/test_llm_mentions_parsing.py
git commit -m "feat(llm-mentions): cross-aggregation + top-pages calls and parsing"
```

---

### Task 4: Visibility service

**Files:**
- Create: `apps/dashboard/services/llm_mentions_service.py`
- Test: `apps/dashboard/services/tests/test_llm_mentions_service.py` (create)

**Interfaces:**
- Consumes: `LLMMentionMetric`, `LLMCitedPage`; `resolve_site_ids` from `pipeline/utils/site_ids.py`.
- Produces: `MENTION_PLATFORMS` (list of `{id, name, color}`), `build_visibility_block(site_id) -> dict` returning keys `sov`, `mentions`, `impressions`, `cited_pages`, `topPages`, `topDomains`, `mentionPlatforms`, `state`.

- [ ] **Step 1: Write the failing test**

Create `apps/dashboard/services/tests/test_llm_mentions_service.py`:

```python
"""The AI Visibility block: real numbers when they exist, honest states when they do not."""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from apps.dashboard.services.llm_mentions_service import build_visibility_block
from pipeline.db.schema import init_db
from pipeline.db.writer import upsert_llm_cited_pages, upsert_llm_mention_metrics
from pipeline.utils import db_connection
from pipeline.utils.db_connection import get_engine, get_session

SITE = "fusehealth.com"
THIS_WEEK = date(2026, 7, 27)
LAST_WEEK = THIS_WEEK - timedelta(days=7)


class VisibilityBlockTests(SimpleTestCase):
    def setUp(self):
        db_connection._SessionFactory = None
        self.addCleanup(setattr, db_connection, "_SessionFactory", None)
        tmp = tempfile.mkdtemp()
        init_db(get_engine(str(Path(tmp) / "fusehealth.db")))
        self._ctx = override_settings(ANALYTICS_DB_PATH=str(Path(tmp) / "fusehealth.db"))
        self._ctx.enable()
        self.addCleanup(self._ctx.disable)

    def _seed(self, rows, week=THIS_WEEK):
        recs = [{
            "site_id": SITE, "week_start": week, "subject_domain": d,
            "subject_type": t, "platform": p, "mentions": m, "ai_search_volume": v,
        } for d, t, p, m, v in rows]
        with get_session() as s:
            upsert_llm_mention_metrics(s, recs)
            s.commit()

    def test_never_synced_reports_setup_not_zeros(self):
        block = build_visibility_block(SITE)
        self.assertEqual(block["state"], "setup")
        self.assertEqual(block["sov"]["rows"], [])
        self.assertIsNone(block["sov"]["delta"])

    def test_share_of_voice_sums_platforms_and_totals_100(self):
        self._seed([
            ("fusehealth.com", "you", "google", 1, 50),
            ("fusehealth.com", "you", "chat_gpt", 0, 0),
            ("driphydration.com", "competitor", "google", 3632, 1617710),
            ("driphydration.com", "competitor", "chat_gpt", 1, 32),
            ("mobileivmedics.com", "competitor", "google", 2392, 1142040),
            ("mobileivmedics.com", "competitor", "chat_gpt", 114, 2875),
        ])
        block = build_visibility_block(SITE)
        rows = block["sov"]["rows"]
        self.assertEqual([r["domain"] for r in rows][:2],
                         ["driphydration.com", "mobileivmedics.com"])
        self.assertEqual(rows[0]["mentions"], 3633)
        self.assertEqual(sum(r["sov"] for r in rows), 100)
        you = next(r for r in rows if r["isYou"])
        self.assertEqual(you["domain"], "fusehealth.com")
        self.assertEqual(block["sov"]["you"], you["sov"])

    def test_first_week_has_no_delta(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("x.com", "competitor", "google", 10, 100)])
        block = build_visibility_block(SITE)
        self.assertIsNone(block["sov"]["delta"],
                          "no prior week means no comparison — not a zero")

    def test_delta_is_computed_once_a_prior_week_exists(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("x.com", "competitor", "google", 90, 900)], week=LAST_WEEK)
        self._seed([("fusehealth.com", "you", "google", 30, 300),
                    ("x.com", "competitor", "google", 70, 700)], week=THIS_WEEK)
        block = build_visibility_block(SITE)
        self.assertEqual(block["sov"]["you"], 30)
        self.assertEqual(block["sov"]["delta"], 20)

    def test_no_competitors_reports_its_own_state(self):
        self._seed([("fusehealth.com", "you", "google", 5, 50)])
        block = build_visibility_block(SITE)
        self.assertEqual(block["state"], "no_competitors")
        self.assertEqual(block["mentions"], 5, "own mentions are still real and still shown")

    def test_zero_data_competitor_is_listed_not_hidden(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("restoreiv.com", "competitor", "google", 0, 0)])
        block = build_visibility_block(SITE)
        self.assertIn("restoreiv.com", [r["domain"] for r in block["sov"]["rows"]])

    def test_top_domains_come_from_discovered_rows_and_flag_you_and_competitors(self):
        self._seed([
            ("fusehealth.com", "you", "google", 100, 1000),
            ("driphydration.com", "competitor", "google", 300, 3000),
            ("www.youtube.com", "discovered", "all", 600, 6000),
        ])
        block = build_visibility_block(SITE)
        by = {d["domain"]: d for d in block["topDomains"]}
        self.assertTrue(by["fusehealth.com"]["isYou"])
        self.assertTrue(by["driphydration.com"]["isComp"])
        self.assertFalse(by["www.youtube.com"]["isYou"])
        self.assertFalse(by["www.youtube.com"]["isComp"])

    def test_cited_pages_are_read_for_the_latest_week(self):
        self._seed([("fusehealth.com", "you", "google", 10, 100),
                    ("x.com", "competitor", "google", 10, 100)])
        with get_session() as s:
            upsert_llm_cited_pages(s, [{
                "site_id": SITE, "week_start": THIS_WEEK,
                "url": "https://fusehealth.com/locations/dallas",
                "mentions": 36, "ai_search_volume": 1627,
                "platforms": '["google"]',
            }])
            s.commit()
        block = build_visibility_block(SITE)
        self.assertEqual(block["cited_pages"], 1)
        self.assertEqual(block["topPages"][0]["url"], "https://fusehealth.com/locations/dallas")
        self.assertEqual(block["topPages"][0]["impressions"], 1627)
        self.assertEqual(block["topPages"][0]["platforms"], ["google"])

    def test_no_cited_pages_is_an_empty_list_not_an_error(self):
        self._seed([("fusehealth.com", "you", "google", 1, 50),
                    ("x.com", "competitor", "google", 10, 100)])
        block = build_visibility_block(SITE)
        self.assertEqual(block["topPages"], [])
        self.assertEqual(block["cited_pages"], 0)

    def test_mention_platforms_are_the_two_the_api_actually_covers(self):
        block = build_visibility_block(SITE)
        self.assertEqual([p["id"] for p in block["mentionPlatforms"]], ["google", "chat_gpt"])
        self.assertEqual([p["name"] for p in block["mentionPlatforms"]],
                         ["AI Overviews", "ChatGPT"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.dashboard.services.tests.test_llm_mentions_service`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.dashboard.services.llm_mentions_service'`

- [ ] **Step 3: Write the service**

Create `apps/dashboard/services/llm_mentions_service.py`:

```python
"""AI Visibility block — assembled from stored DataForSEO LLM Mentions snapshots.

Reads `llm_mention_metrics` and `llm_cited_pages`, never an external API: the connector
`pipeline/connectors/dataforseo_llm_mentions.py` is the only thing that calls DataForSEO.

Everything here comes from a real stored row. Where a number cannot honestly be produced --
no snapshot yet, no competitors configured, no prior week to compare against -- the caller
gets an explicit state or `None`, never a zero dressed up as a measurement.
"""
import json
import logging

from sqlalchemy import select

from pipeline.db.schema import LLMCitedPage, LLMMentionMetric
from pipeline.db.writer import ensure_tables
from pipeline.utils.db_connection import get_session
from pipeline.utils.site_ids import resolve_site_ids

logger = logging.getLogger(__name__)

# The only two platforms DataForSEO's LLM Mentions API covers. Claude, Gemini and Perplexity
# are NOT available from it at any price -- they appear only on the Prompts tab, which is fed
# by this deployment's own LLM API keys. Keep this list separate from ai_service's
# MENTION_PLATFORMS/llmPlatforms for exactly that reason.
MENTION_PLATFORMS = [
    {"id": "google", "name": "AI Overviews", "color": "#4285f4"},
    {"id": "chat_gpt", "name": "ChatGPT", "color": "#10a37f"},
]

_EMPTY = {
    "sov": {"you": 0, "delta": None, "rows": []},
    "mentions": 0,
    "impressions": 0,
    "cited_pages": 0,
    "topPages": [],
    "topDomains": [],
    "mentionPlatforms": MENTION_PLATFORMS,
    "state": "setup",
}


def query_mention_metrics_raw(site_id: str, weeks: int = 2) -> list[dict]:
    """The most recent `weeks` weekly snapshots, newest first. [] on any failure."""
    site_ids = resolve_site_ids(site_id)
    if not site_ids:
        return []
    try:
        with get_session() as session:
            ensure_tables(session, LLMMentionMetric)
            recent = session.execute(
                select(LLMMentionMetric.week_start)
                .where(LLMMentionMetric.site_id.in_(site_ids))
                .distinct().order_by(LLMMentionMetric.week_start.desc()).limit(weeks)
            ).scalars().all()
            if not recent:
                return []
            rows = session.execute(
                select(LLMMentionMetric)
                .where(LLMMentionMetric.site_id.in_(site_ids),
                       LLMMentionMetric.week_start.in_(recent))
            ).scalars().all()
            return [{
                "week_start": r.week_start, "subject_domain": r.subject_domain,
                "subject_type": r.subject_type, "platform": r.platform,
                "mentions": r.mentions or 0, "ai_search_volume": r.ai_search_volume or 0,
            } for r in rows]
    except Exception as exc:
        logger.error(f"query_mention_metrics_raw error: {exc}", exc_info=True)
        return []


def query_cited_pages_raw(site_id: str, week_start) -> list[dict]:
    """Stored cited URLs for one week, most-mentioned first. [] on any failure."""
    site_ids = resolve_site_ids(site_id)
    if not site_ids:
        return []
    try:
        with get_session() as session:
            ensure_tables(session, LLMCitedPage)
            rows = session.execute(
                select(LLMCitedPage)
                .where(LLMCitedPage.site_id.in_(site_ids),
                       LLMCitedPage.week_start == week_start)
                .order_by(LLMCitedPage.mentions.desc())
            ).scalars().all()
    except Exception as exc:
        logger.error(f"query_cited_pages_raw error: {exc}", exc_info=True)
        return []

    out = []
    for r in rows:
        try:
            platforms = json.loads(r.platforms) if r.platforms else []
        except (ValueError, TypeError):
            platforms = []
        out.append({
            "url": r.url, "mentions": r.mentions or 0,
            "impressions": r.ai_search_volume or 0,
            "platforms": platforms if isinstance(platforms, list) else [],
        })
    return out


def _totals_by_domain(rows: list[dict], week) -> dict:
    """{domain: {"type", "mentions", "volume"}} for one week, platforms summed."""
    agg: dict = {}
    for r in rows:
        if r["week_start"] != week:
            continue
        d = agg.setdefault(r["subject_domain"],
                           {"type": r["subject_type"], "mentions": 0, "volume": 0})
        d["mentions"] += r["mentions"]
        d["volume"] += r["ai_search_volume"]
        # 'you' and 'competitor' must win over a stray 'discovered' row for the same domain.
        if r["subject_type"] in ("you", "competitor"):
            d["type"] = r["subject_type"]
    return agg


def _sov_percentages(agg: dict) -> dict:
    """{domain: whole-number share} across tracked subjects only, forced to total 100.

    The denominator is the sum of tracked subjects, so the rows add up to 100 the way the
    page presents them. The API's own deduplicated `total` is deliberately not used -- it
    counts a response once even when it mentions two subjects, so shares built from it would
    not sum to 100.
    """
    tracked = {d: v for d, v in agg.items() if v["type"] in ("you", "competitor")}
    total = sum(v["mentions"] for v in tracked.values())
    if not total:
        return {d: 0 for d in tracked}

    raw = {d: v["mentions"] / total * 100 for d, v in tracked.items()}
    out = {d: int(p) for d, p in raw.items()}
    # Hand the rounding remainder to the largest fractional parts so the column totals 100
    # instead of 99 -- a share list that does not add up reads as a bug.
    remainder = 100 - sum(out.values())
    for d, _ in sorted(raw.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True):
        if remainder <= 0:
            break
        out[d] += 1
        remainder -= 1
    return out


def build_visibility_block(site_id: str) -> dict:
    """`sov`, KPI values, `topPages`, `topDomains` and `mentionPlatforms` for the AI page."""
    rows = query_mention_metrics_raw(site_id, weeks=2)
    if not rows:
        return dict(_EMPTY)

    weeks = sorted({r["week_start"] for r in rows}, reverse=True)
    this_week = weeks[0]
    agg = _totals_by_domain(rows, this_week)

    shares = _sov_percentages(agg)
    sov_rows = [{
        "domain": d,
        "sov": shares[d],
        "mentions": agg[d]["mentions"],
        "isYou": agg[d]["type"] == "you",
    } for d in shares]
    sov_rows.sort(key=lambda r: (-r["mentions"], r["domain"]))

    you_row = next((r for r in sov_rows if r["isYou"]), None)
    you_share = you_row["sov"] if you_row else 0

    # A delta needs a real prior measurement. Without one it stays None and the SPA shows
    # "no comparison yet" -- printing +0 would claim last week was measured when it was not.
    delta = None
    if len(weeks) > 1:
        prev_agg = _totals_by_domain(rows, weeks[1])
        prev_shares = _sov_percentages(prev_agg)
        prev_you_domain = next((d for d, v in prev_agg.items() if v["type"] == "you"), None)
        if prev_you_domain is not None:
            delta = you_share - prev_shares[prev_you_domain]

    competitors = [d for d, v in agg.items() if v["type"] == "competitor"]
    state = "ok" if competitors else "no_competitors"

    top_domains_total = sum(v["mentions"] for v in agg.values()) or 1
    top_domains = sorted(agg.items(), key=lambda kv: -kv[1]["mentions"])[:10]
    top_domains_out = [{
        "domain": d,
        "share": round(v["mentions"] / top_domains_total * 100, 1),
        "mentions": v["mentions"],
        "isYou": v["type"] == "you",
        "isComp": v["type"] == "competitor",
    } for d, v in top_domains]

    pages = query_cited_pages_raw(site_id, this_week)

    return {
        "sov": {"you": you_share, "delta": delta, "rows": sov_rows},
        "mentions": agg.get(you_row["domain"], {}).get("mentions", 0) if you_row else 0,
        "impressions": agg.get(you_row["domain"], {}).get("volume", 0) if you_row else 0,
        "cited_pages": len(pages),
        "topPages": pages,
        "topDomains": top_domains_out,
        "mentionPlatforms": MENTION_PLATFORMS,
        "state": state,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.dashboard.services.tests.test_llm_mentions_service`
Expected: PASS, 10 tests

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/services/llm_mentions_service.py apps/dashboard/services/tests/test_llm_mentions_service.py
git commit -m "feat(llm-mentions): AI Visibility service with honest empty states"
```

---

### Task 5: Wire the connector into sync and the service into the API response

**Files:**
- Modify: `pipeline/services/sync_engine.py` (`PAGE_CONNECTORS["ai"]` ~line 61, `ALL_CONNECTORS` ~line 100, `connector_map` ~line 132)
- Modify: `apps/dashboard/services/ai_service.py` (`build_ai_response`, ~line 565-605)
- Test: `apps/api/tests/test_ai.py` (extend)

**Interfaces:**
- Consumes: `build_visibility_block` from Task 4; `DataForSEOLLMMentionsConnector` from Task 3.
- Produces: `GET /api/projects/<slug>/ai` returning real `sov`, `kpis.mentions`, `kpis.impressions`, `kpis.cited_pages`, `topPages`, `topDomains`, `mentionPlatforms`.

- [ ] **Step 1: Write the failing test**

Append to `apps/api/tests/test_ai.py` (copy the file's existing analytics-DB fixture and auth setup for the new class — do not import a fixture that is not there):

```python
class AIVisibilityFromLLMMentionsTests(APITestCase):
    """The AI page must serve stored LLM-mention data, never call an API while rendering."""

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
            session.add(Site(site_url="sc-domain:example.com", site_name="Example",
                             slug="example", is_active=1))
            session.commit()
        with get_session() as session:
            upsert_llm_mention_metrics(session, [
                {"site_id": "sc-domain:example.com", "week_start": date(2026, 7, 27),
                 "subject_domain": "example.com", "subject_type": "you",
                 "platform": "google", "mentions": 20, "ai_search_volume": 500},
                {"site_id": "sc-domain:example.com", "week_start": date(2026, 7, 27),
                 "subject_domain": "rival.com", "subject_type": "competitor",
                 "platform": "google", "mentions": 80, "ai_search_volume": 4000},
            ])
            session.commit()

        user = get_user_model().objects.create_user("aivis", password="x")
        token = Token.objects.get(user=user)
        self.client_auth = APIClient()
        self.client_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_ai_endpoint_serves_real_share_of_voice(self):
        resp = self.client_auth.get("/api/projects/example/ai")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["sov"]["you"], 20)
        self.assertEqual({r["domain"] for r in data["sov"]["rows"]},
                         {"example.com", "rival.com"})
        self.assertEqual(data["kpis"]["mentions"], 20)
        self.assertEqual(data["kpis"]["impressions"], 500)

    def test_mention_platforms_are_two_but_llm_platforms_stay_four(self):
        data = self.client_auth.get("/api/projects/example/ai").json()
        self.assertEqual([p["id"] for p in data["mentionPlatforms"]], ["google", "chat_gpt"])
        self.assertEqual(len(data["llmPlatforms"]), 4,
                         "the Prompts tab still tracks four answer engines")

    def test_prompt_coverage_still_comes_from_prompt_runs(self):
        data = self.client_auth.get("/api/projects/example/ai").json()
        self.assertEqual(data["kpis"]["prompt_coverage"], {"cited": 0, "total": 0})
```

Add to that file's imports: `from datetime import date`, `from pipeline.db.writer import upsert_llm_mention_metrics`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.api.tests.test_ai.AIVisibilityFromLLMMentionsTests`
Expected: FAIL — `sov.you` is 0 because `build_ai_response` still returns the hardcoded block.

- [ ] **Step 3: Register the connector in the sync engine**

In `pipeline/services/sync_engine.py`:

```python
# PAGE_CONNECTORS — the "ai" scope
    "ai":          ["dataforseo_ai_keywords", "dataforseo_llm_mentions"],
```

```python
# ALL_CONNECTORS — add after "dataforseo_ai_keywords"
    "dataforseo_llm_mentions",
```

```python
# connector_map in _get_connector — add after the dataforseo_ai_keywords entry
        "dataforseo_llm_mentions":     ("pipeline.connectors.dataforseo_llm_mentions",     "DataForSEOLLMMentionsConnector"),
```

- [ ] **Step 4: Merge the visibility block into the API response**

In `apps/dashboard/services/ai_service.py`, add the import near the other service imports:

```python
from apps.dashboard.services.llm_mentions_service import build_visibility_block
```

In `build_ai_response`, immediately before the `return {` statement, add:

```python
    # Real AI-answer visibility, read back from stored LLM Mentions snapshots. Everything it
    # returns used to be a hardcoded 0/[] under a label claiming an API that was not wired.
    vis = build_visibility_block(site_id)
```

Then replace the corresponding entries in the returned dict:

```python
        "mentionPlatforms": vis["mentionPlatforms"],
        # llmPlatforms stays the four answer engines the Prompts tab checks with this
        # deployment's own API keys. DataForSEO's LLM Mentions covers only two platforms, so
        # these two lists are NOT interchangeable -- they were the same constant, which is why
        # the visibility toggles offered Claude/Gemini/Perplexity that could never have data.
        "llmPlatforms": MENTION_PLATFORMS,
        "sov": vis["sov"],
        "kpis": {
            "mentions": vis["mentions"],
            "impressions": vis["impressions"],
            "cited_pages": vis["cited_pages"],
            # Still from real prompt runs — a different measurement, deliberately unchanged.
            "prompt_coverage": {"cited": cited_prompts, "total": len(prompts)},
        },
        "trend": [],   # Lean v1: weekly rows are being collected; the chart is not wired yet.
        "topPages": vis["topPages"],
        "topDomains": vis["topDomains"],
        "visibilityState": vis["state"],
```

Delete the now-unused local `mentions` counter loop above the return only if nothing else uses it; `cited_prompts` is still needed for `prompt_coverage`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.api.tests.test_ai apps.dashboard.services.tests.test_ai_service`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pipeline/services/sync_engine.py apps/dashboard/services/ai_service.py apps/api/tests/test_ai.py
git commit -m "feat(llm-mentions): wire connector into the ai scope and the API response"
```

---

### Task 6: SPA honest states

**Files:**
- Modify: `static/spa/src/js/pages/ai_optimization.js:119-172`
- Modify: `static/spa/src/pages/site_audit.html` — **this file holds the AI Optimization markup**,
  not just Site Audit. It opens with `<sc-if value="{{ showAi }}">` and contains the AI Share of
  Voice card (~line 139), Your Most-Cited Pages (~line 189) and Domains Dominating AI Answers
  (~line 205). The filename is misleading and pre-dates this work; there is no
  `pages/ai_optimization.html`.
- Modify: wherever the AI Optimization page subtitle lives (search for "Claude, Gemini" across
  `static/spa/src/`)

**Interfaces:**
- Consumes: `sov.delta` (may be `null`), `visibilityState` (`"setup" | "no_competitors" | "ok"`), `mentionPlatforms` (2 entries) from Task 5.
- Produces: no new interfaces; rendering only.

- [ ] **Step 1: Fix the null-delta lie**

`ai_optimization.js:123` currently reads:

```js
aiv.sovDelta = (sov.delta >= 0 ? '▲ +' : '▼ ') + Math.abs(sov.delta) + ' pts vs. last week';
```

`null >= 0` is `true` in JavaScript, so a first-ever week renders **"▲ +0 pts vs. last week"** — claiming a comparison that never happened. Replace both that line and the style line below it:

```js
          // delta is null until a second weekly snapshot exists. Printing "+0 pts vs. last
          // week" would assert we measured last week when we did not.
          const hasDelta = sov.delta !== null && sov.delta !== undefined;
          aiv.sovDelta = hasDelta
            ? (sov.delta >= 0 ? '▲ +' : '▼ ') + Math.abs(sov.delta) + ' pts vs. last week'
            : 'first measurement — no comparison yet';
          aiv.sovDeltaStyle = {
            fontSize: '12px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px',
            background: !hasDelta ? '#f1f5f9' : (sov.delta >= 0 ? '#ecfdf5' : '#fff1f2'),
            color: !hasDelta ? '#64748b' : (sov.delta >= 0 ? '#059669' : '#e11d48')
          };
```

- [ ] **Step 2: Add the visibility empty states**

Immediately after `const sov = d.sov;` in the `sub2 === 'visibility'` block, add:

```js
          // Each empty case has its own truth; none of them is a zero.
          aiv.visSetup = d.visibilityState === 'setup';
          aiv.visNoComps = d.visibilityState === 'no_competitors';
          aiv.visNoPages = !aiv.visSetup && d.topPages.length === 0;
          aiv.visSetupMsg = 'No AI visibility data yet — press Refresh to take the first weekly snapshot.';
          aiv.visNoCompsMsg = 'Add competitors under Targets to see share of voice.';
          aiv.visNoPagesMsg = 'AI has not cited any of your pages yet.';
```

Wrap the SoV rows list and the Most-Cited Pages table in the corresponding `<sc-if>` guards in `static/spa/src/pages/ai_optimization.html`, following the file's existing `<sc-if value="{{ ... }}">` pattern, and add a sibling block rendering the message for each state.

- [ ] **Step 3: Correct the page subtitle**

In `static/spa/src/index.html`, the AI Optimization subtitle reads "Brand visibility across ChatGPT, AI Overviews, Claude, Gemini & Perplexity". LLM Mentions covers two of those five. Replace with:

```
Brand visibility in AI Overviews & ChatGPT · prompt checks across ChatGPT, Claude, Gemini & Perplexity
```

- [ ] **Step 4: Verify in the browser**

Run: `python manage.py runserver`
Open `/app/#/ai-optimization` for a project with no snapshots. Expected: the setup message, and a grey "first measurement — no comparison yet" chip — **not** "▲ +0 pts vs. last week".

- [ ] **Step 5: Commit**

```bash
git add static/spa/src/js/pages/ai_optimization.js static/spa/src/pages/ai_optimization.html static/spa/src/index.html
git commit -m "fix(spa): honest AI visibility states, stop claiming an unmeasured week"
```

---

### Task 7: Documentation and full verification

**Files:**
- Modify: `.claude/SKILLS.md` (§4 table, §9 traps)
- Modify: `.claude/api-reference.md` (the `/api/projects/<slug>/ai` response)
- Modify: `.claude/features.md` (§17 known gaps)

- [ ] **Step 1: Update `.claude/SKILLS.md` §4**

Add to the `data/fusehealth.db` table list, after the `ai_keyword_data` row:

```
| `llm_mention_metrics` | `LLMMentionMetric` | site_id, week_start, subject_domain, platform | `dataforseo_llm_mentions` |
| `llm_cited_pages` | `LLMCitedPage` | site_id, week_start, url | `dataforseo_llm_mentions` |
```

- [ ] **Step 2: Add the two new traps to `.claude/SKILLS.md` §9**

```
| Assuming a DataForSEO `group_element` always carries its metric | A group_element omits `mentions`/`ai_search_volume` **entirely** when the value is zero — `{"type": "group_element", "key": "chat_gpt"}` is a complete, valid element meaning "no mentions". `.get("mentions", 0)` is fine but `el["mentions"]` raises, and treating a missing element as "no such platform" loses a real zero. Read with `.get(...) or 0` |
| Trusting `llm_mentions/top_pages` to return only YOUR pages | It returns co-occurring pages from other domains too — a call for `driphydration.com` came back with `https://www.perfectb.com/...`. Filter on `canonical_domain(url) == own_domain` before storing, or "Your Most-Cited Pages" lists a competitor's content |
```

- [ ] **Step 3: Update `.claude/api-reference.md`**

Document that `GET /api/projects/<slug>/ai` now returns real `sov`, `kpis.mentions`, `kpis.impressions`, `kpis.cited_pages`, `topPages`, `topDomains` sourced from `llm_mention_metrics`/`llm_cited_pages`, plus the new `visibilityState` field (`setup` | `no_competitors` | `ok`). Note that `mentionPlatforms` (2) and `llmPlatforms` (4) are different lists with different sources, and that `trend` remains `[]` until the chart is wired.

- [ ] **Step 4: Update `.claude/features.md` §17**

Remove AI share-of-voice from the known-placeholder list — it is real now. Add the remaining honest gap: the 12-week trend chart is not wired, though weekly data collection has started, and Claude/Gemini/Perplexity mention tracking is not offered by the API.

- [ ] **Step 5: Run the full suite**

Run: `python manage.py test`
Expected: PASS. Baseline before this feature was 474 tests; this plan adds 34, so expect 508 with no failures.

- [ ] **Step 6: Verify against the live API once**

```bash
python manage.py shell -c "
from pipeline.connectors.dataforseo_llm_mentions import DataForSEOLLMMentionsConnector as C
print(C().sync(site_id='sc-domain:fusehealth.com'))
"
```
Expected: `status: success` with rows written. Run it a **second** time and confirm `records_written: 0` and a log line saying the week is already stored — that is the spend guard working. Then open the AI Optimization page and confirm the Share of Voice list shows fusehealth near 0% against driphydration and mobileivmedics, matching the numbers in the spec.

- [ ] **Step 7: Commit**

```bash
git add .claude/SKILLS.md .claude/api-reference.md .claude/features.md
git commit -m "docs: record LLM Mentions tables, traps and the AI page's real data sources"
```

---

## Self-review notes

- **Spec coverage:** two tables (T1), weekly guard + skip-unconfigured + competitor cap + cost recording (T2, T3), both endpoints with `top_pages` conditional and own-host filter (T3), SoV maths and five honest states (T4, T6), platform-list split (T4, T5), scope registration (T5), header copy (T6), docs (T7). The deferred trend chart and `top_domains` endpoint are recorded as out of scope in the spec and left unimplemented on purpose.
- **Type consistency:** `week_start_for` is defined once in T2 and used in T3; `build_visibility_block` keys defined in T4 are exactly the keys consumed in T5; `_table` tag values `"metrics"`/`"pages"` match between `fetch` and `_write_records`.
- **Known deviation from the spec:** discovered domains are stored with `platform="all"` because `total.sources_domain` carries no platform split. Splitting it proportionally would be invented data. `MENTION_PLATFORMS` ids stay `google`/`chat_gpt`, so an `"all"` row never collides with a real platform row.
