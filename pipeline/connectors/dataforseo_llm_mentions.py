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

`aggregation_metrics` and `top_domains` are deliberately NOT called: cross_aggregation already
returns this project's own metrics in `items[]` and the top domains in `total.sources_domain`.
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

    def _build_aggregation_entities(
        self, site_url: str, brand: str, aliases: list[str], competitors: list[str],
    ) -> list[str]:
        """Up to MAX_ENTITIES_PER_KEY targets for one aggregation_key: this project's own
        domain and brand names first, then up to MAX_COMPETITORS competitor domains."""
        own = [canonical_domain(site_url), brand, *aliases]
        others = [canonical_domain(c) for c in competitors[:MAX_COMPETITORS]]

        seen: set[str] = set()
        entities: list[str] = []
        for entity in own + others:
            entity = (entity or "").strip()
            if entity and entity not in seen:
                seen.add(entity)
                entities.append(entity)
        return entities[:MAX_ENTITIES_PER_KEY]

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

        entities = self._build_aggregation_entities(site_url, brand, aliases, competitors)
        payload = [{
            "aggregation_key": entities,
            "location_name": self._site_location(site_id),
            "language_name": "English",
        }]
        self._call_cross_aggregation(payload)

        # Task 3 fills this in: parse the cross_aggregation response, conditionally call
        # _call_top_pages when this project's own domain was mentioned, and normalize records.
        return []
