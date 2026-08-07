"""Real AI-answer-engine visibility check — asks a live LLM a tracked prompt and reports,
from the actual answer text, whether the tracked brand (or an alias, or a tracked competitor)
appears in it.

Design notes, so nothing here is mistaken for a simulation:

* **All four engines go through DataForSEO's AI Optimization LLM Responses API**
  (`POST /v3/ai_optimization/<llm_type>/llm_responses/live`), authenticated with the same
  `DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD` pair every other DataForSEO connector uses. One
  credential pair makes ChatGPT, Claude, Gemini AND Perplexity real — previously only
  `chatgpt` was wired (direct to OpenAI with `OPENAI_API_KEY`) and the other three returned
  a permanent `state="not_connected"`. Nothing is ever estimated or simulated: if the
  DataForSEO credentials are absent, every engine degrades to an explicit `not_connected`.

* **`cost` is the USD charge DataForSEO reports in its own response envelope** (read via
  `pipeline/connectors/dataforseo_cost.extract_cost`, the same reader every other DataForSEO
  connector uses). It already includes the underlying model spend — no price table to keep
  current. An envelope with no charge reads as `None` (unknown), never a guess.

* **What "cited" means.** Without web search the model returns prose, not sources — so
  "cited" means the strictly weaker, fully determinable thing: *the brand appears as an item
  of an enumerated/bulleted recommendation list in the answer*, and `position` is that item's
  real ordinal. `mentioned` means it appears in the answer prose but not as a ranked item.
  `absent` means it does not appear at all. `analyze_answer` itself is pure text analysis and
  always returns `citations: []`; `check_prompt` then overwrites that with the *real* source
  annotations DataForSEO returns when the prompt's `webSearch` option is on — verified
  `{title, url}` pairs from the provider, never URLs scraped out of the prose.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone

import requests

from pipeline.connectors.dataforseo_cost import extract_cost

logger = logging.getLogger(__name__)

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"
# DataForSEO executes the provider call server-side with its own ceiling of 120s; a shorter
# client timeout would abort (and still pay for) slow-but-successful checks.
REQUEST_TIMEOUT = 120
MAX_ANSWER_TOKENS = 600
# Hard DataForSEO limit on user_prompt; longer prompts are rejected, so truncate honestly.
PROMPT_MAX_CHARS = 500
# Deterministic: the same prompt should give a comparable answer week over week, otherwise the
# trend measures sampling noise rather than a change in the model's view of the brand.
TEMPERATURE = 0.0

# The four answer engines the AI Optimization UI has columns for. `llm_type` is the DataForSEO
# path segment; `model` is the PREFERRED model_name — each provider's cheapest current tier,
# because a visibility check needs a representative answer, not a frontier one.
#
# `model` is a preference, NOT a guarantee: it is validated against the provider's live model
# list before use (see `resolve_model`). Hardcoding a name outright is what broke this feature
# — `claude-3-5-haiku-latest` was taken from DataForSEO's published docs, had since been
# retired, and every Claude check returned `40501 Invalid Field: 'model_name'` while the run
# reported success. Providers rotate these names continuously; the code must not assume a
# literal it read once is still valid.
PLATFORMS = {
    "chatgpt": {"name": "ChatGPT", "llm_type": "chat_gpt", "model": "gpt-4o-mini"},
    "claude": {"name": "Claude", "llm_type": "claude", "model": "claude-haiku-4-5"},
    "gemini": {"name": "Gemini", "llm_type": "gemini", "model": "gemini-2.5-flash-lite"},
    "perplexity": {"name": "Perplexity", "llm_type": "perplexity", "model": "sonar"},
}

# Substrings marking a cheap tier, best first. Used only to pick a replacement when the
# preferred model is gone — a visibility check wants the provider's ordinary answer, and the
# frontier tiers cost several times more for no better signal about who gets mentioned.
_CHEAP_TIER_HINTS = ("haiku", "flash-lite", "nano", "mini", "flash", "sonar")

# llm_type -> the provider's live model names, fetched once per process. The models endpoint
# is free ("your account will not be charged"), so this costs nothing but one request.
_MODEL_CACHE: dict[str, list[str]] = {}

# Every engine above rides the same DataForSEO credential pair.
DATAFORSEO_ENV_VARS = ("DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD")

SNIPPET_MAX = 300

# A markdown list item: "1. ...", "2) ...", "- ...", "* ...", "• ...". Group 1 is the leading
# whitespace (used to keep nested bullets on their own ordinal counter).
_LIST_ITEM_RE = re.compile(r"^(\s{0,8})(?:(\d{1,3})[.)]|[-*•])\s+(.+)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# A bare hostname: labels joined by dots, ending in an alphabetic TLD, no whitespace.
# Used to decide whether "<something>.<something>" is a domain worth expanding to its label,
# so a brand that merely contains a full stop ("Dr. Smith Clinics") is never split into the
# 2-3 letter fragment "dr" and matched against every answer that says "Dr.".
_HOSTNAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9-]+)*\.[a-z]{2,}$")


# ─────────────────────────────────────────────
# Connectivity
# ─────────────────────────────────────────────

def platform_name(platform_id: str) -> str:
    meta = PLATFORMS.get(platform_id)
    return meta["name"] if meta else str(platform_id)


def is_platform_connected(platform_id: str) -> bool:
    """True only when this deployment can actually reach that answer engine right now.
    All four ride DataForSEO, so connectivity is one question: are both credentials set?"""
    if platform_id not in PLATFORMS:
        return False
    return all(os.environ.get(var) for var in DATAFORSEO_ENV_VARS)


def connected_platforms() -> list[str]:
    """Every platform a real check can be run against *right now*. Empty list == the feature is
    unavailable and must say so — no credentials, no call, no simulated answer."""
    return [pid for pid in PLATFORMS if is_platform_connected(pid)]


def connectable_platforms() -> list[str]:
    """Every platform this build has a connector for at all, whether or not its credentials are
    set today. Used to seed a new prompt's tracked models: that choice must not silently change
    depending on whether an env var happened to be present the moment setup ran. All four
    engines are reachable through DataForSEO's LLM Responses API, so all four qualify."""
    return list(PLATFORMS)


def not_connected_reason(platform_id: str) -> str:
    if platform_id not in PLATFORMS:
        return f"Unknown answer engine: {platform_id}"
    missing = [var for var in DATAFORSEO_ENV_VARS if not os.environ.get(var)]
    return ("Not connected — " + " and ".join(missing or DATAFORSEO_ENV_VARS)
            + " must be set (answer-engine checks run through DataForSEO).")


def not_connected_result(platform_id: str) -> dict:
    """The honest stand-in for an engine we cannot call. Never claims a verdict: `mentioned`
    and `cited` are False because nothing was observed, and `state` says why."""
    return {
        "ok": False,
        "state": "not_connected",
        "platform": platform_id,
        "platformName": platform_name(platform_id),
        "model": None,
        "error": not_connected_reason(platform_id),
        "answer": "",
        "paragraphs": [],
        "citations": [],
        "verdict": None,
        "mentioned": False,
        "cited": False,
        "position": None,
        "snippet": not_connected_reason(platform_id),
        "competitors": [],
        "cost": 0.0,
        "tokens": None,
        "checkedAt": None,
    }


# ─────────────────────────────────────────────
# Brand / competitor matching
# ─────────────────────────────────────────────

def _needles(name) -> list[str]:
    """Lowercased search terms for one tracked entity.

    Targets are stored either as a brand name ("FuseHealth") or, for competitors, as a bare
    domain — the SPA's competitor input strips the scheme/path and lowercases before saving.
    A *hostname* is expanded to also match its bare label ("acme.com" -> "acme"), because an
    LLM answer names companies, not hostnames.

    Two guards against false positives, both fixed after review of the inherited draft:

    * The label is only extracted when the whole string is really a hostname (`_HOSTNAME_RE`).
      The draft split on the first "." unconditionally, so the brand "Dr. Smith Clinics"
      produced the needle "dr" and every answer containing "Dr." counted as a brand mention.
    * The label must be >= 4 characters. Three-letter labels ("ai.com" -> "ai" was already
      excluded, but "one.com" -> "one", "for.com" -> "for") are ordinary English words and
      matched constantly; the domain itself still matches, so nothing real is lost.
    """
    if isinstance(name, dict):  # competitors are sometimes carried as {"domain": ...} rows
        name = name.get("domain") or name.get("name") or ""
    raw = str(name or "").strip().lower()
    if not raw:
        return []
    raw = re.sub(r"^https?://", "", raw).strip("/")
    raw = raw.split("/")[0].split("?")[0].strip()
    if not raw:
        return []
    out = [raw]
    if raw.startswith("www.") and len(raw) > 4:
        out.append(raw[4:])
    host = out[-1]
    if _HOSTNAME_RE.match(host):
        label = host.split(".")[0]
        if len(label) >= 4:
            out.append(label)
    # Longest first: matching "acme.com" before "acme" keeps the snippet the more specific one.
    return sorted(dict.fromkeys(out), key=len, reverse=True)


def target_needles(brand: str, aliases=()) -> list[str]:
    out: list[str] = []
    for name in [brand, *(aliases or ())]:
        out.extend(_needles(name))
    return sorted(dict.fromkeys(out), key=len, reverse=True)


def _contains(haystack_lower: str, needle: str) -> bool:
    """Boundary-aware substring match. Plain `in` would match "acme" inside "acmeium"; `\\b`
    misbehaves around the dots in a domain, so an explicit alphanumeric lookaround is used."""
    if not needle or not haystack_lower:
        return False
    return re.search(
        r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", haystack_lower
    ) is not None


def _list_items(text: str) -> list[tuple[int, str]]:
    """Enumerated/bulleted items of the answer, as (ordinal, text).

    The ordinal is the number the model itself wrote when there is one, otherwise the item's
    running position *within its own indent level* — either way a real property of the answer,
    not an estimate. The inherited draft used one flat counter across the whole answer, so a
    nested sub-bullet under item 1 was reported as "cited at position #2"; the brand's real
    rank in the recommendation list is the thing this page exists to show, so an off-by-N
    there is not cosmetic.
    """
    items: list[tuple[int, str]] = []
    auto: dict[int, int] = {}
    for line in (text or "").splitlines():
        m = _LIST_ITEM_RE.match(line)
        if not m:
            continue
        indent, num, body = len(m.group(1)), m.group(2), m.group(3).strip()
        auto[indent] = auto.get(indent, 0) + 1
        items.append((int(num) if num else auto[indent], body))
    return items


def _clean(fragment: str) -> str:
    out = re.sub(r"[*_`#]+", "", fragment or "").strip()
    return out[:SNIPPET_MAX].strip()


def _sentence_with(text: str, needle: str) -> str:
    for para in (text or "").split("\n"):
        for sentence in _SENTENCE_SPLIT_RE.split(para):
            if _contains(sentence.lower(), needle):
                return _clean(sentence)
    return ""


def _first_hit(text: str, needles: list[str]) -> dict:
    """Where (if anywhere) this entity appears in the answer."""
    miss = {"mentioned": False, "cited": False, "position": None, "snippet": ""}
    if not needles or not text:
        return miss

    for ordinal, body in _list_items(text):
        body_lower = body.lower()
        for needle in needles:
            if _contains(body_lower, needle):
                return {"mentioned": True, "cited": True, "position": ordinal,
                        "snippet": _clean(body)}

    text_lower = text.lower()
    for needle in needles:
        if _contains(text_lower, needle):
            return {"mentioned": True, "cited": False, "position": None,
                    "snippet": _sentence_with(text, needle) or _clean(text)}
    return miss


def _paragraphs(text: str, needles: list[str]) -> list[dict]:
    """The answer split for the Answer Inspector, with `hit` marking the paragraphs that
    actually contain the tracked brand. Real text, real flags — nothing synthesised."""
    out = []
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        block = block.strip()
        if not block:
            continue
        lower = block.lower()
        out.append({"text": block, "hit": any(_contains(lower, n) for n in needles)})
    return out


def analyze_answer(answer: str, brand: str, aliases=(), competitors=()) -> dict:
    """Pure text analysis of a real LLM answer — no network, no state. Split out from
    `check_prompt` so the detection logic is testable without ever touching the OpenAI API."""
    needles = target_needles(brand, aliases)
    hit = _first_hit(answer, needles)

    competitor_hits = []
    for comp in competitors or ():
        comp_hit = _first_hit(answer, _needles(comp))
        if comp_hit["mentioned"]:
            competitor_hits.append({
                "name": comp if isinstance(comp, str) else str(
                    (comp or {}).get("domain") or (comp or {}).get("name") or comp),
                "cited": comp_hit["cited"],
                "position": comp_hit["position"],
                "snippet": comp_hit["snippet"],
            })

    # No brand configured => nothing was looked for, so "absent" would be a verdict we never
    # earned. `None` is the honest answer; callers refuse to run without a brand anyway.
    verdict = (
        None if not needles
        else "cited" if hit["cited"]
        else "mentioned" if hit["mentioned"]
        else "absent"
    )
    return {
        "verdict": verdict,
        "mentioned": hit["mentioned"],
        "cited": hit["cited"],
        "position": hit["position"],
        "snippet": hit["snippet"],
        "competitors": competitor_hits,
        "paragraphs": _paragraphs(answer, needles),
        # Empty here, deliberately: this function is pure text analysis, and any URL the model
        # happens to write in prose is unverified and frequently hallucinated. Real citations
        # exist only as the source annotations DataForSEO returns on a web-search-enabled
        # check — `check_prompt` fills them in from there, never from the answer text.
        "citations": [],
    }


# ─────────────────────────────────────────────
# Model resolution
# ─────────────────────────────────────────────

def available_models(llm_type: str, timeout: int = 20) -> list[str]:
    """Every model name this provider currently accepts, newest-listed first.

    Free endpoint, cached per process. Returns [] when it cannot be read — callers then keep
    their configured preference rather than refusing to run.
    """
    if llm_type in _MODEL_CACHE:
        return _MODEL_CACHE[llm_type]
    names: list[str] = []
    try:
        response = requests.get(
            f"{DATAFORSEO_BASE}/ai_optimization/{llm_type}/llm_responses/models",
            auth=(os.environ["DATAFORSEO_LOGIN"], os.environ["DATAFORSEO_PASSWORD"]),
            timeout=timeout,
        )
        response.raise_for_status()
        results = ((response.json().get("tasks") or [{}])[0].get("result")) or []
        # The payload nests one level deeper on some providers: result[0].items[].
        if results and isinstance(results[0], dict) and results[0].get("items"):
            results = results[0]["items"]
        for item in results:
            if isinstance(item, dict):
                name = item.get("model_name") or item.get("name")
                if name:
                    names.append(name)
    except Exception as exc:
        # Cache the failure too. A batch run asks this for every prompt x engine, so an
        # unreachable endpoint would otherwise add one failed request per check — 80 of them
        # on a 20-prompt run — each waiting out its own timeout before the paid call it is
        # only meant to sanity-check.
        logger.warning(f"[ai_visibility] could not read {llm_type} model list: {exc}")
        _MODEL_CACHE[llm_type] = []
        return []
    _MODEL_CACHE[llm_type] = names
    return names


def resolve_model(platform_id: str, preferred: str | None = None) -> str | None:
    """A model name this provider will actually accept, for `platform_id`.

    `preferred` (or the platform's configured default) wins whenever the provider still lists
    it. When it does not — a retired name — the cheapest currently-listed tier is used instead
    and the substitution is logged, because silently answering from a frontier model would
    change what the check costs without saying so.

    Falls back to the preference unchanged if the model list cannot be read at all: a
    temporary outage of a free metadata endpoint must not stop a paid check the user asked for.
    """
    meta = PLATFORMS.get(platform_id)
    if meta is None:
        return preferred
    wanted = preferred or meta["model"]

    names = available_models(meta["llm_type"])
    if not names or wanted in names:
        return wanted

    for hint in _CHEAP_TIER_HINTS:
        for name in names:
            if hint in name.lower():
                logger.warning(
                    f"[ai_visibility] {platform_id}: model {wanted!r} is no longer offered — "
                    f"using {name!r}. Update PLATFORMS[{platform_id!r}]['model']."
                )
                return name
    logger.warning(
        f"[ai_visibility] {platform_id}: model {wanted!r} is no longer offered — falling back "
        f"to {names[0]!r}. Update PLATFORMS[{platform_id!r}]['model']."
    )
    return names[0]


# ─────────────────────────────────────────────
# Response parsing
# ─────────────────────────────────────────────

def _extract_answer(result: dict) -> tuple[str, list[dict]]:
    """(answer text, citations) out of one DataForSEO llm_responses result object.

    `items[].sections[].text` carries the answer; items of type "reasoning" are the model's
    thinking summary, not the answer a user sees, so they are skipped. `annotations` on a
    section are the provider-verified web sources of a web-search-enabled answer — the only
    thing this module will ever surface as a citation."""
    texts: list[str] = []
    citations: list[dict] = []
    seen_urls: set[str] = set()
    for item in result.get("items") or []:
        if item.get("type") == "reasoning":
            continue
        for section in item.get("sections") or []:
            if not isinstance(section, dict):
                continue
            text = section.get("text")
            if text:
                texts.append(text)
            for ann in section.get("annotations") or []:
                url = (ann or {}).get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    citations.append({"title": ann.get("title") or "", "url": url})
    return "\n\n".join(texts), citations


# ─────────────────────────────────────────────
# The check
# ─────────────────────────────────────────────

def _error_result(platform_id: str, model: str, message: str) -> dict:
    return {
        "ok": False,
        "state": "error",
        "platform": platform_id,
        "platformName": platform_name(platform_id),
        "model": model,
        "error": message,
        "answer": "",
        "paragraphs": [],
        "citations": [],
        "verdict": None,
        "mentioned": False,
        "cited": False,
        "position": None,
        "snippet": "",
        "competitors": [],
        "cost": 0.0,
        "tokens": None,
        "checkedAt": None,
    }


def _country_iso(country: str | None) -> str | None:
    """The ISO-3166-1 alpha-2 code DataForSEO's `web_search_country_iso_code` wants.

    The prompt-settings modal collects Country as free text, so both "US" and "United States"
    arrive here. A two-letter value is passed through; a recognised name is mapped; anything
    else returns None and is simply not sent — an unrecognised country is better dropped than
    guessed, since a wrong code silently changes which country's web results the answer is
    grounded in.
    """
    value = (country or "").strip()
    if not value:
        return None
    if len(value) == 2 and value.isalpha():
        return value.upper()
    return {
        "united states": "US", "usa": "US", "united states of america": "US",
        "united kingdom": "GB", "uk": "GB", "great britain": "GB", "england": "GB",
        "canada": "CA", "australia": "AU", "india": "IN", "germany": "DE",
        "france": "FR", "spain": "ES", "italy": "IT", "netherlands": "NL",
        "brazil": "BR", "mexico": "MX", "japan": "JP", "singapore": "SG",
        "united arab emirates": "AE", "uae": "AE", "new zealand": "NZ",
        "ireland": "IE", "south africa": "ZA",
    }.get(value.lower())


def check_prompt(question: str, brand: str, aliases=(), competitors=(),
                 platform: str = "chatgpt", model: str | None = None,
                 timeout: int = REQUEST_TIMEOUT, web_search: bool = False,
                 country: str | None = None) -> dict:
    """Ask one answer engine one tracked prompt (via DataForSEO's LLM Responses API) and
    report what really came back.

    Costs money — call it only from an explicit user action, never while rendering a page.
    Never raises: a provider failure comes back as `state="error"`, so one bad prompt cannot
    abort a batch run or lose the results already paid for.
    """
    question = (question or "").strip()
    meta = PLATFORMS.get(platform)
    # Validated against the provider's live list, so a retired default cannot turn every
    # check into `40501 Invalid Field: 'model_name'` — see `resolve_model`.
    model = resolve_model(platform, model) if meta else model
    if not question:
        return _error_result(platform, model, "Empty prompt.")
    if not target_needles(brand, aliases):
        # Refuse *before* the paid call: with nothing to look for, the answer could only be
        # scored "absent", which would be an invented verdict paid for in real money.
        return _error_result(platform, model, "No brand or alias configured to look for.")

    if meta is None:
        return _error_result(platform, model, f"Unknown answer engine: {platform}")
    if not is_platform_connected(platform):
        return not_connected_result(platform)

    task = {
        # The prompt is sent verbatim, with no system message: the point is to observe what
        # an ordinary user asking this question actually gets back.
        "user_prompt": question[:PROMPT_MAX_CHARS],
        "model_name": model,
        "max_output_tokens": MAX_ANSWER_TOKENS,
        "temperature": TEMPERATURE,
    }
    if web_search:
        task["web_search"] = True
        # Only meaningful alongside web search — it geo-scopes the web results the model is
        # grounded in. There is no city-level equivalent on this endpoint: `web_search_country_
        # iso_code` is the finest geography DataForSEO's LLM Responses API accepts, which is
        # why the modal's City field cannot be honoured (see the note beside it).
        iso = _country_iso(country)
        if iso:
            task["web_search_country_iso_code"] = iso

    try:
        response = requests.post(
            f"{DATAFORSEO_BASE}/ai_optimization/{meta['llm_type']}/llm_responses/live",
            auth=(os.environ["DATAFORSEO_LOGIN"], os.environ["DATAFORSEO_PASSWORD"]),
            json=[task],
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        # What DataForSEO says it charged for this call (model spend included). 0 from a live
        # endpoint means the charge wasn't reported — unknown, not free.
        cost = extract_cost(data) or None
        tasks = data.get("tasks") or []
        task_out = tasks[0] if tasks else {}
        if task_out.get("status_code") != 20000:
            raise ValueError(
                f"DataForSEO task failed: {task_out.get('status_code')} "
                f"{task_out.get('status_message')}"
            )
        results = task_out.get("result") or []
        if not results:
            raise ValueError("DataForSEO returned no result for the task")
        result = results[0] or {}
        answer, citations = _extract_answer(result)
        input_tokens = result.get("input_tokens")
        output_tokens = result.get("output_tokens")
        model_used = result.get("model_name") or model
    except Exception as exc:
        logger.error(f"[ai_visibility] {platform} check failed: {exc}")
        return _error_result(platform, model, str(exc))

    if not answer.strip():
        # A 200 with an empty body is a provider failure, not an "absent" verdict — reporting
        # "your brand is absent" from an answer that does not exist would be a fabricated result.
        return _error_result(platform, model_used, "Provider returned an empty answer.")

    analysis = analyze_answer(answer, brand, aliases, competitors)
    # Real provider-verified sources (web-search checks only) — see _extract_answer.
    analysis["citations"] = citations
    return {
        "ok": True,
        "state": "checked",
        "platform": platform,
        "platformName": platform_name(platform),
        "model": model_used,
        "error": None,
        "answer": answer,
        "cost": cost,
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": (input_tokens + output_tokens)
                     if input_tokens is not None and output_tokens is not None else None,
        },
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **analysis,
    }
