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
     request carries one `targets` array with one `aggregation_key` per subject, each holding
     up to MAX_ENTITIES_PER_KEY domain and brand-name entities.
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
        except Exception as exc:
            # Deliberately NOT fail-open. Returning "not stored" here would make every sync
            # run re-call a metered API behind nothing but a warning; returning "stored"
            # would report a successful sync that wrote nothing. Raising lets
            # BaseConnector.sync() record a real error the operator can see, and spends
            # nothing while the cause is unknown.
            raise RuntimeError(
                f"[dataforseo_llm_mentions] could not check whether week {week} is already "
                f"stored for {site_url!r}; refusing to call a metered API on an unknown state"
            ) from exc

    @staticmethod
    def _entities(domain: str, names: list[str]) -> list[dict]:
        ents: list[dict] = [{"domain": domain}]
        for n in names:
            n = (n or "").strip()
            if n and len(ents) < MAX_ENTITIES_PER_KEY:
                ents.append({"keyword": n, "match_type": "word_match"})
        return ents

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
