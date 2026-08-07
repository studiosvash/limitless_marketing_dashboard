"""
pipeline/connectors/dataforseo_keywords.py — DataForSEO Keywords Data connector.

Fetches: search volume, keyword difficulty, CPC for tracked keywords.
Writes to: keyword_rankings table (enriches existing position records).

Rate limit: 12 req/min for Google Ads live endpoint.
Strategy: Batch up to 1,000 keywords per request (live endpoint is fine for metadata).
Google Trends: Always use Standard method — never Live (shared 250 req/min global limit).
"""

import json
import os
import time
from datetime import date
from typing import Optional

import requests
from dotenv import load_dotenv

from pipeline.connectors.base import BaseConnector
from pipeline.connectors.dataforseo_cost import extract_cost, record_cost
# Single home for the location-string fix — see dataforseo_live_serp for the documented
# DataForSEO `location_name` format and why the SPA's picker value has to be converted.
from pipeline.connectors.dataforseo_live_serp import country_of, normalize_location_name
from pipeline.db.schema import DEFAULT_LOCATION
from pipeline.utils.retry import with_retry
from pipeline.utils.date_helpers import yesterday
from pipeline.utils.db_connection import get_session
from pipeline.db.writer import upsert_keyword_rankings

load_dotenv()

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


class DataForSEOKeywordsConnector(BaseConnector):
    name = "dataforseo_keywords"

    def __init__(self):
        super().__init__()
        self.login = os.getenv("DATAFORSEO_LOGIN")
        self.password = os.getenv("DATAFORSEO_PASSWORD")
        self.auth = (self.login, self.password)
        # USD DataForSEO reported for the current fetch(). fetch() spends across two
        # endpoints per batch (search_volume + bulk_keyword_difficulty); both land here
        # and one row is written per run.
        self._run_cost = 0.0

    def _resolve_site_id(self, site_id: Optional[str]) -> str:
        """Pick the right site_id to tag records with."""
        from pipeline.services.site_service import get_site, get_site_by_pk
        with get_session() as session:
            # Prefer the exact project when the run named one — several projects can share a
            # site_url and get_site() would return an arbitrary sibling.
            site = get_site_by_pk(session, getattr(self, "site_pk", None)) \
                or get_site(session, site_id)
            if site:
                return site.site_url
        return site_id or os.getenv("GSC_SITE_URL", "")

    def _load_keywords(self, site_id: str = "", location: str = "") -> list[str]:
        """This PROJECT's tracked keywords, optionally narrowed to an incremental subset."""
        from pipeline.utils.keywords import load_tracked_keywords
        keywords = load_tracked_keywords(site_id, location=location or None,
                                         site_pk=getattr(self, "site_pk", None))
        # Incremental sync: sync_engine may set `only_keywords` to restrict this run to the
        # keywords that actually need work (pipeline/utils/keywords.keywords_needing_backfill).
        # DataForSEO meters per query, so re-querying every tracked keyword to pick up five new
        # ones is both slow and billable. Absent/empty => full list, so the scheduled sync and
        # every existing caller behave exactly as before.
        only = getattr(self, "only_keywords", None)
        if only:
            wanted = set(k.strip().lower() for k in only if k and k.strip())
            subset = [k for k in keywords if (k or "").strip().lower() in wanted]
            self.logger.info(
                f"[dataforseo_keywords] incremental run: {len(subset)} of {len(keywords)} tracked keywords"
            )
            return subset
        return keywords

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_search_volume(self, keywords: list[str],
                             location: str = DEFAULT_LOCATION) -> list[dict]:
        """
        Fetch search volume + CPC for a batch of keywords, IN THIS PROJECT'S MARKET.
        Max 1,000 keywords per request. Rate limit: 12 req/min.

        Google Ads reports volume per location, and the difference is the whole point of a
        city project: "event staffing" is not searched the same number of times in New York as
        it is nationally. This used to post a literal `location_name="United States"`, so every
        project — whatever market it was configured for — showed national volume.
        """
        payload = [{
            "keywords": keywords[:1000],
            "location_name": normalize_location_name(location),
            "language_name": "English",
        }]

        resp = requests.post(
            f"{DATAFORSEO_BASE}/keywords_data/google_ads/search_volume/live",
            auth=self.auth,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._run_cost += extract_cost(data)
        return data.get("tasks", [{}])[0].get("result", [])

    @with_retry(max_retries=3, base_delay=5.0)
    def _fetch_keyword_difficulty(self, keywords: list[str],
                                  location: str = DEFAULT_LOCATION) -> dict[str, float]:
        """
        Fetch keyword difficulty (0-100) for a batch via the DataForSEO Labs
        bulk_keyword_difficulty endpoint. Returns {keyword_lower: difficulty}.
        Failures degrade gracefully to an empty map (KD stays None).

        COUNTRY-LEVEL, unavoidably: this is a DataForSEO Labs endpoint, and Labs documents
        `location_type: Country` as the only one it supports — a city value is rejected
        outright. `country_of` degrades the project's market rather than sending a city and
        losing the whole KD column to an `Invalid Field` error. Search volume above has no
        such limit and IS fetched at the project's exact market.
        """
        payload = [{
            "keywords": [k.lower() for k in keywords[:1000]],
            "location_name": country_of(location),
            "language_name": "English",
        }]
        try:
            resp = requests.post(
                f"{DATAFORSEO_BASE}/dataforseo_labs/google/bulk_keyword_difficulty/live",
                auth=self.auth,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            payload = resp.json()
            self._run_cost += extract_cost(payload)
            result = payload.get("tasks", [{}])[0].get("result", []) or []
        except Exception as exc:
            self.logger.warning(f"[dataforseo_keywords] Keyword-difficulty fetch failed: {exc}")
            return {}

        # Shape: result[].items[] = {keyword, keyword_difficulty}
        kd_map: dict[str, float] = {}
        for block in result:
            for item in (block.get("items") or []):
                kw = (item.get("keyword") or "").lower()
                kd = item.get("keyword_difficulty")
                if kw and kd is not None:
                    kd_map[kw] = float(kd)
        return kd_map

    # ─────────────────────────────────────────────
    # Ad-hoc lookup for the Keyword Explorer (read-only — no DB write, no keywords.txt).
    # Separate from the tracking fetch()/sync() path. Triggered by an explicit user
    # action, so calling the API here is consistent with the data-first contract.
    # ─────────────────────────────────────────────

    @with_retry(max_retries=2, base_delay=3.0)
    def _fetch_keyword_overview(self, keywords: list[str], location_name: str) -> list[dict]:
        """One DataForSEO Labs keyword_overview call — returns every metric at once.
        Accepts up to 700 keywords per request."""
        payload = [{
            "keywords": keywords[:700],
            "location_name": location_name,
            "language_name": "English",
        }]
        resp = requests.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/keyword_overview/live",
            auth=self.auth,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        self._run_cost += extract_cost(payload)
        return payload.get("tasks", [{}])[0].get("result", [{}])[0].get("items", []) or []

    @staticmethod
    def _parse_overview_item(item: dict, location_name: str) -> Optional[dict]:
        """Map one keyword_overview item to the Explorer's 8 columns. Defensive against
        missing nested keys. Returns None if the item has no keyword."""
        # keyword_overview returns metrics on the item itself; ranked_keywords nests them
        # under keyword_data — accept either so the parser is robust.
        data = item.get("keyword_data") if isinstance(item.get("keyword_data"), dict) else item
        keyword = data.get("keyword")
        if not keyword:
            return None

        info = data.get("keyword_info") or {}
        props = data.get("keyword_properties") or {}
        serp = data.get("serp_info") or {}
        intent_info = data.get("search_intent_info") or {}

        main_intent = intent_info.get("main_intent") if isinstance(intent_info, dict) else None
        serp_types = serp.get("serp_item_types") if isinstance(serp, dict) else None
        serp_features = ", ".join(serp_types) if serp_types else ""

        competition = info.get("competition_level")
        if not competition and info.get("competition") is not None:
            competition = str(info.get("competition"))

        return {
            "keyword": keyword,
            "search_volume": info.get("search_volume"),
            "keyword_difficulty": props.get("keyword_difficulty"),
            "cpc": info.get("cpc"),
            "competition": competition,
            "intent": main_intent.capitalize() if main_intent else None,
            "serp_features": serp_features,
            "location": location_name,
        }

    def lookup_keywords(self, keywords: list[str], location_name: str = "United States",
                        site_id: str = "") -> dict:
        """
        Fetch on-demand keyword metrics for the Keyword Explorer. Read-only: returns the
        data, never writes to the DB. Always returns a dict the view/template can branch on:

            {"status": "ok"|"error", "rows": [...], "no_data": [...],
             "location": str, "error": str|None}

        - rows: keywords DataForSEO returned data for (the 8 Explorer columns).
        - no_data: requested keywords with no result (shown as a note; successful rows still render).
        - status "error": whole-call failure (missing creds, negative balance, network/HTTP).

        `site_id` is optional and purely for cost attribution — the Explorer is a
        request-scoped lookup and its caller may not have a project in hand. Omitting it
        still books the spend, just against the unattributed "" site.
        """
        cleaned = []
        seen = set()
        for kw in keywords:
            k = (kw or "").strip()
            key = k.lower()
            if k and key not in seen:
                seen.add(key)
                cleaned.append(k)

        if not cleaned:
            return {"status": "error", "rows": [], "no_data": [],
                    "location": location_name, "error": "Enter at least one keyword."}

        if not self.login or not self.password:
            return {"status": "error", "rows": [], "no_data": cleaned, "location": location_name,
                    "error": "DataForSEO credentials are not configured."}

        # The SPA's location picker (static/spa/us_cities.json) emits "United States - Texas",
        # which DataForSEO's location_name does not understand — it wants "Texas,United States".
        # Normalise only what goes to the API; `location_name` stays in its display form for the
        # response so the UI keeps showing the value the user actually picked.
        api_location = normalize_location_name(location_name)

        self._run_cost = 0.0
        try:
            items = self._fetch_keyword_overview(cleaned, api_location)
        except Exception as exc:
            self.logger.warning(f"[dataforseo_keywords] lookup_keywords failed: {exc}")
            return {"status": "error", "rows": [], "no_data": cleaned, "location": location_name,
                    "error": f"Couldn't fetch keyword data: {exc}"}
        finally:
            # `units` = keywords submitted — Labs keyword_overview meters per keyword.
            record_cost(
                self.name, site_id, self._run_cost, units=len(cleaned),
                notes=f"labs/keyword_overview lookup ({api_location})",
            )

        rows = []
        returned = set()
        for item in items:
            parsed = self._parse_overview_item(item, location_name)
            if parsed:
                rows.append(parsed)
                returned.add(parsed["keyword"].lower())

        no_data = [k for k in cleaned if k.lower() not in returned]
        return {"status": "ok", "rows": rows, "no_data": no_data,
                "location": location_name, "error": None}

    # ─────────────────────────────────────────────
    # Keyword Explorer EXPANSION (on-demand research). Unlike lookup_keywords (which only
    # returns metrics for the exact seeds), this uses Labs keyword_ideas — the widest-net
    # category-relevance expansion — so one seed returns many *new* keyword ideas. Read-only,
    # metered, triggered by an explicit user click → consistent with the data-first contract.
    # ─────────────────────────────────────────────

    _QUESTION_WORDS = frozenset({
        "how", "what", "why", "when", "where", "who", "which", "whose", "whom",
        "is", "are", "can", "could", "should", "would", "will", "do", "does",
        "did", "was", "were", "has", "have",
    })

    @staticmethod
    def _classify_match(kw: str, seed_phrases: list[str], seed_token_sets: list[set]) -> str:
        """Bucket a keyword_ideas result relative to the seeds for the SPA's tab filters.
        keyword_ideas IS the 'broad' category-relevance set (widest net — includes terms that
        don't contain the seed), so the default is 'broad'; only the narrower forms peel off.
        Precedence: exact > questions > phrase > broad. ('related' is reserved for a future
        related_keywords call and stays empty here.) seed_token_sets is unused now but kept for
        signature stability with callers/tests."""
        k = (kw or "").lower().strip()
        if not k:
            return "broad"
        if k in seed_phrases:
            return "exact"
        first = k.split()[0] if k.split() else ""
        if first in DataForSEOKeywordsConnector._QUESTION_WORDS or "?" in k:
            return "questions"
        if any(p and p in k for p in seed_phrases):
            return "phrase"
        return "broad"

    @with_retry(max_retries=2, base_delay=3.0)
    def _fetch_keyword_ideas(self, seeds: list[str], location_name: str, limit: int) -> dict:
        """One Labs keyword_ideas/live call. Returns the raw task dict (items + cost)."""
        payload = [{
            "keywords": [s.lower() for s in seeds][:200],
            "location_name": location_name,
            "language_name": "English",
            "include_serp_info": True,
            "limit": max(1, min(limit, 1000)),
            "order_by": ["keyword_info.search_volume,desc"],
        }]
        resp = requests.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/keyword_ideas/live",
            auth=self.auth,
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()

    @with_retry(max_retries=2, base_delay=3.0)
    def _fetch_related_keywords(self, seed: str, location_name: str, limit: int) -> dict:
        """Labs related_keywords/live call (searches related to graph). Takes a single string keyword.

        The order_by path is `keyword_data.keyword_info...` — this endpoint nests each item
        under `keyword_data`, unlike keyword_ideas/keyword_suggestions where the same fields
        sit at the top level. With the un-nested path the API rejects the whole task with
        40501 "Invalid Field: 'order_by'", the warning was swallowed upstream, and the
        Explorer's Related tab silently showed zero results forever (found 2026-08-03).
        """
        payload = [{
            "keyword": (seed or "").lower().strip(),
            "location_name": location_name,
            "language_name": "English",
            "include_serp_info": True,
            "limit": max(1, min(limit, 500)),
            "order_by": ["keyword_data.keyword_info.search_volume,desc"],
        }]
        resp = requests.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/related_keywords/live",
            auth=self.auth,
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()

    @with_retry(max_retries=2, base_delay=3.0)
    def _fetch_keyword_suggestions(self, seeds: list[str], location_name: str, limit: int) -> dict:
        """Labs keyword_suggestions/live call (long-tail suggestions)."""
        payload = [{
            "keyword": s.lower().strip(),
            "location_name": location_name,
            "language_name": "English",
            "include_serp_info": True,
            "limit": max(1, min(limit, 1000)),
            "order_by": ["keyword_info.search_volume,desc"],
        } for s in seeds[:20] if s.strip()]
        resp = requests.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/keyword_suggestions/live",
            auth=self.auth,
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()

    # The Questions tab's prefixes. Exactly eight: DataForSEO Labs allows at most eight
    # conditions in one filter group, so this is the API ceiling, not an arbitrary pick.
    _QUESTION_PREFIXES = ("how %", "what %", "why %", "is %",
                          "can %", "does %", "where %", "when %")

    @with_retry(max_retries=2, base_delay=3.0)
    def _fetch_question_ideas(self, seeds: list[str], location_name: str, limit: int) -> dict:
        """Labs keyword_ideas/live filtered to question-prefixed keywords, for the Questions
        tab.

        Why not keyword_suggestions: suggestions only returns keywords CONTAINING the full
        seed phrase, and real questions rarely embed a phrase like "event staffing services"
        verbatim — filtering suggestions to question prefixes returned zero rows on a live
        test. keyword_ideas is category-relevance (the seed's topic, not its exact words), so
        question-filtering it yields real questions people ask in the seed's category. One
        extra metered task (~$0.01–0.02), same price class as the other three calls.
        """
        filters: list = []
        for i, prefix in enumerate(self._QUESTION_PREFIXES):
            if i:
                filters.append("or")
            filters.append(["keyword", "like", prefix])
        payload = [{
            "keywords": [s.lower() for s in seeds][:200],
            "location_name": location_name,
            "language_name": "English",
            "include_serp_info": True,
            "limit": max(1, min(limit, 1000)),
            "filters": filters,
            "order_by": ["keyword_info.search_volume,desc"],
        }]
        resp = requests.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/keyword_ideas/live",
            auth=self.auth,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _parse_idea_item(item: dict) -> Optional[dict]:
        """Map one keyword_ideas item to the Explorer's row shape (before match/tracked).
        Returns None if the item has no keyword."""
        data = item.get("keyword_data") if isinstance(item.get("keyword_data"), dict) else item
        kw = data.get("keyword")
        if not kw:
            return None
        info = data.get("keyword_info") or {}
        props = data.get("keyword_properties") or {}
        intent_info = data.get("search_intent_info") or {}
        serp = data.get("serp_info") or {}

        # monthly_searches comes newest-first; the sparkline wants oldest→newest.
        monthly_raw = info.get("monthly_searches") or []
        monthly = [int(m.get("search_volume") or 0) for m in reversed(monthly_raw)][-12:]

        main_intent = intent_info.get("main_intent") if isinstance(intent_info, dict) else None
        serp_types = serp.get("serp_item_types") if isinstance(serp, dict) else None

        return {
            "kw": kw,
            "volume": info.get("search_volume") or 0,
            "kd": props.get("keyword_difficulty") if props.get("keyword_difficulty") is not None else 0,
            "cpc": round(info.get("cpc"), 2) if info.get("cpc") is not None else 0,
            "intent": (main_intent or "informational").lower(),
            "monthly": monthly,
            "serpFeatures": list(serp_types) if serp_types else [],
        }

    def expand_keywords(self, seeds: list[str], location_name: str = "United States",
                        limit: int = 100, site_id: str = "") -> dict:
        """Keyword Explorer expansion. Read-only — never writes analytics rows. Always returns a
        dict the endpoint can branch on:

            {"status": "ok"|"error", "location": str, "cost": float,
             "rows": [{kw, volume, kd, cpc, intent, match, monthly, serpFeatures}], "error": str|None}

        The returned `cost` is unchanged (the SPA renders it); it is now ALSO appended to
        connector_costs so Settings can total it. `site_id` is optional and only attributes
        that row — see lookup_keywords.
        """
        import re
        import concurrent.futures

        cleaned, seen = [], set()
        for kw in seeds:
            k = (kw or "").strip()
            if k and k.lower() not in seen:
                seen.add(k.lower())
                cleaned.append(k)

        if not cleaned:
            return {"status": "error", "location": location_name, "cost": 0, "rows": [],
                    "error": "Enter at least one seed keyword."}
        if not self.login or not self.password:
            return {"status": "error", "location": location_name, "cost": 0, "rows": [],
                    "error": "DataForSEO credentials are not configured."}

        # See the note in lookup_keywords: the picker's "Country - Region" form is not a valid
        # DataForSEO location_name. Normalise for the API, keep the display form in the response.
        api_location = normalize_location_name(location_name)

        ideas_payload, related_payload, questions_payload = {}, {}, {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            f_ideas = pool.submit(self._fetch_keyword_ideas, cleaned, api_location, limit)
            f_related = pool.submit(self._fetch_related_keywords, cleaned[0], api_location, min(limit, 50))
            # Question-filtered keyword_ideas, NOT keyword_suggestions — suggestions requires
            # the full seed phrase inside every result, which excludes almost every real
            # question; see _fetch_question_ideas. (An earlier revision built question-
            # prefixed seed strings here and then never passed them anywhere, so the
            # Questions tab was empty from the day it shipped.)
            f_questions = pool.submit(self._fetch_question_ideas, cleaned, api_location, min(limit, 50))

            try:
                ideas_payload = f_ideas.result()
            except Exception as exc:
                self.logger.warning(f"[dataforseo_keywords] expand_keywords ideas failed: {exc}")
                return {"status": "error", "location": location_name, "cost": 0, "rows": [],
                        "error": f"Couldn't fetch keyword ideas: {exc}"}

            try:
                related_payload = f_related.result()
            except Exception as exc:
                self.logger.warning(f"[dataforseo_keywords] expand_keywords related failed: {exc}")

            try:
                questions_payload = f_questions.result()
            except Exception as exc:
                self.logger.warning(f"[dataforseo_keywords] expand_keywords questions failed: {exc}")

        # extract_cost sums tasks[].cost and falls back to the top-level total. That matters
        # for keyword_suggestions, which posts ONE TASK PER SEED — the old top-level-only
        # read happened to be right, but the per-task rows are the documented source of truth.
        total_cost = (
            extract_cost(ideas_payload)
            + extract_cost(related_payload)
            + extract_cost(questions_payload)
        )

        seed_phrases = [s.lower().strip() for s in cleaned]
        seed_token_sets = [set(re.findall(r"[a-z0-9]+", p)) for p in seed_phrases]

        rows = []
        seen_kws = set()

        # 1. Parse main keyword ideas (broad, phrase, exact, questions)
        task_ideas = (ideas_payload.get("tasks") or [{}])[0]
        for item in ((task_ideas.get("result") or [{}])[0].get("items") or []):
            row = self._parse_idea_item(item)
            if row and row["kw"].lower() not in seen_kws:
                seen_kws.add(row["kw"].lower())
                row["match"] = self._classify_match(row["kw"], seed_phrases, seed_token_sets)
                rows.append(row)

        # 2. Parse related keywords
        task_related = (related_payload.get("tasks") or [{}])[0]
        for item in ((task_related.get("result") or [{}])[0].get("items") or []):
            row = self._parse_idea_item(item)
            if row and row["kw"].lower() not in seen_kws:
                seen_kws.add(row["kw"].lower())
                match_class = self._classify_match(row["kw"], seed_phrases, seed_token_sets)
                row["match"] = "related" if match_class == "broad" else match_class
                rows.append(row)

        # 3. Parse keyword suggestions
        task_questions = (questions_payload.get("tasks") or [{}])[0]
        for item in ((task_questions.get("result") or [{}])[0].get("items") or []):
            row = self._parse_idea_item(item)
            if row and row["kw"].lower() not in seen_kws:
                seen_kws.add(row["kw"].lower())
                row["match"] = self._classify_match(row["kw"], seed_phrases, seed_token_sets)
                rows.append(row)

        # `units` = keyword rows returned. Labs ideas/related/suggestions all meter per
        # returned keyword, so this is the honest denominator for cost-per-keyword.
        record_cost(
            self.name, site_id, total_cost, units=len(rows),
            notes=f"labs keyword_ideas+related_keywords+keyword_suggestions ({api_location})",
        )

        return {"status": "ok", "location": location_name, "cost": round(float(total_cost), 4),
                "rows": rows, "error": None}

    def fetch(self, site_id: Optional[str] = None) -> list[dict]:
        """
        Fetch keyword metadata (volume, KD, CPC) for all tracked keywords.
        Enriches the keyword_rankings table — site-scoped via site_id tag.
        """
        if not self.login or not self.password:
            raise ValueError("[dataforseo_keywords] Missing DATAFORSEO_LOGIN or DATAFORSEO_PASSWORD in .env.")
        resolved_site_id = self._resolve_site_id(site_id)
        location = self._resolve_location(resolved_site_id)

        keywords = self._load_keywords(resolved_site_id, location)
        if not keywords:
            self.logger.warning("[dataforseo_keywords] No keywords found.")
            return []

        self.logger.info(
            f"[dataforseo_keywords] Fetching metadata for {len(keywords)} keywords "
            f"(site: {resolved_site_id} @ {location!r})"
        )
        tracking_date = yesterday()
        records = []
        self._run_cost = 0.0

        # Process in batches of 1,000 (API limit)
        batch_size = 1000
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            try:
                results = self._fetch_search_volume(batch, location)
                # Keyword difficulty comes from a separate Labs endpoint; merge by keyword.
                kd_map = self._fetch_keyword_difficulty(batch, location)
                for item in results:
                    kw = item.get("keyword", "")
                    # monthly_searches rides along free on every search_volume response —
                    # it was fetched, paid for, and DROPPED for months while the tracked
                    # table's Trend column rendered an empty sparkline over the
                    # keyword_rankings.trend column that sat at NULL on 215k rows
                    # (found 2026-08-03). API order is newest-first; the sparkline reads
                    # oldest→newest with the current month last.
                    monthly_raw = item.get("monthly_searches") or []
                    monthly = [int(m.get("search_volume") or 0) for m in reversed(monthly_raw)][-12:]
                    records.append({
                        "date": tracking_date,
                        "site_id": resolved_site_id,
                        "keyword": kw,
                        "position": None,       # Set by SERP connector
                        "url": None,
                        "search_volume": item.get("search_volume"),
                        "keyword_difficulty": kd_map.get((kw or "").lower()),
                        "cpc": item.get("cpc"),
                        "trend": json.dumps(monthly) if monthly else None,
                    })
            except Exception as exc:
                self.logger.warning(f"[dataforseo_keywords] Batch {i//batch_size + 1} failed: {exc}")

            # Rate limit: 12 req/min = 5s between requests
            if i + batch_size < len(keywords):
                time.sleep(5)

        # One row per run. `units` = keywords looked up, which is exactly what both
        # Keywords Data and Labs bulk_keyword_difficulty meter.
        record_cost(
            self.name, resolved_site_id, self._run_cost, units=len(keywords),
            notes="google_ads/search_volume + labs/bulk_keyword_difficulty",
        )

        self.logger.info(f"[dataforseo_keywords] Fetched metadata for {len(records)} keywords")
        return records

    def _resolve_location(self, site_id: str) -> str:
        """This PROJECT's tracking location — see the identical method on gsc_keywords.

        Search volume and difficulty are market-level facts from DataForSEO, but they land in
        `keyword_rankings` alongside the per-market SERP capture, and that table is keyed by
        location. Stamping the project's own location puts them in the rows that project
        actually reads.
        """
        from pipeline.services.site_service import resolve_tracking_location
        return resolve_tracking_location(getattr(self, "site_pk", None), site_id)

    def _write_records(self, session, records: list[dict], site_id: Optional[str] = None) -> int:
        """Upsert keyword metadata through the shared writer.

        This used to hand-build `on_conflict_do_update(index_elements=["date", "site_id",
        "keyword"])`. That key stopped existing when `location` joined it on 2026-08-06, and
        Postgres refused the statement outright (`InvalidColumnReference`) — the same break
        `gsc_keywords` hit. `pipeline/db/writer.upsert_keyword_rankings` owns the conflict
        target now, so there is one definition of it instead of three.

        The old `set_` listed only search_volume/cpc/keyword_difficulty to avoid clobbering
        the SERP connector's positions. The shared writer's `coalesce(excluded, existing)`
        gives the same protection for free: this connector's records carry no `position` or
        `url` key at all, so those columns are not in the update set to begin with.
        """
        if not records:
            return 0

        from pipeline.db.writer import upsert_keyword_rankings

        location = self._resolve_location(site_id or "")
        for r in records:
            r.setdefault("site_id", site_id or "")
            r.setdefault("location", location)

        return upsert_keyword_rankings(session, records, site_id=site_id)
