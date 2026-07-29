"""Real AI-answer-engine visibility check — asks a live LLM a tracked prompt and reports,
from the actual answer text, whether the tracked brand (or an alias, or a tracked competitor)
appears in it.

Design notes, so nothing here is mistaken for a simulation:

* **Only OpenAI is connected.** `PLATFORMS` lists the four answer engines the UI shows, but
  only `chatgpt` has a credential path (`OPENAI_API_KEY`). The other three return an explicit
  `state="not_connected"` result and are never called, never estimated, never simulated. Wiring
  one up means adding its env var + a `_call_*` branch here — nothing else in the app changes.

* **The calling pattern deliberately mirrors `pipeline/services/ai_summary_service.py`**: raw
  `requests` against the chat-completions endpoint, `gpt-4o-mini`, an explicit timeout, and an
  honest skip when the key is absent. (The `openai` package is in requirements but is not
  imported anywhere in this codebase; adding a second, divergent calling style for the same
  provider would be the worse choice.)

* **`cost` is arithmetic on the real token counts the API returns**, using the published
  per-million list price in `MODEL_PRICING_USD_PER_1M`. If the response carries no `usage`
  block the cost is `None` (unknown) — never a guessed number. Update the price table when
  OpenAI changes list pricing; it is the one figure here not read off the wire.

* **What "cited" means.** The chat-completions API without a web-search tool returns prose, not
  sources — so "cited" cannot mean "your URL was used as a source" (that needs a web-search-
  enabled provider, which is not connected). Here `cited` means the strictly weaker, fully
  determinable thing: *the brand appears as an item of an enumerated/bulleted recommendation
  list in the answer*, and `position` is that item's real ordinal. `mentioned` means it appears
  in the answer prose but not as a ranked item. `absent` means it does not appear at all.
  `citations` is therefore always empty — see `analyze_answer`.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
REQUEST_TIMEOUT = 30
MAX_ANSWER_TOKENS = 600
# Deterministic: the same prompt should give a comparable answer week over week, otherwise the
# trend measures sampling noise rather than a change in the model's view of the brand.
TEMPERATURE = 0.0

# Published OpenAI list price, USD per 1M tokens. The only hardcoded money figure in this
# module — everything else is computed from the token counts the API actually returns.
MODEL_PRICING_USD_PER_1M = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

# The four answer engines the AI Optimization UI has columns for. `env` is the credential that
# makes one real; `None` means this deployment has no way to reach it at all.
PLATFORMS = {
    "chatgpt": {"name": "ChatGPT", "provider": "openai", "env": "OPENAI_API_KEY"},
    "claude": {"name": "Claude", "provider": "anthropic", "env": None},
    "gemini": {"name": "Gemini", "provider": "google", "env": None},
    "perplexity": {"name": "Perplexity", "provider": "perplexity", "env": None},
}

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
    """True only when this deployment can actually reach that answer engine right now."""
    meta = PLATFORMS.get(platform_id)
    if not meta or not meta["env"]:
        return False
    return bool(os.environ.get(meta["env"]))


def connected_platforms() -> list[str]:
    """Every platform a real check can be run against *right now*. Empty list == the feature is
    unavailable and must say so, exactly as ai_summary_service skips when OPENAI_API_KEY is
    absent."""
    return [pid for pid in PLATFORMS if is_platform_connected(pid)]


def connectable_platforms() -> list[str]:
    """Every platform this build has a connector for at all, whether or not its key is set
    today. Used to seed a new prompt's tracked models: that choice must not silently change
    depending on whether an env var happened to be present the moment setup ran."""
    return [pid for pid, meta in PLATFORMS.items() if meta["env"]]


def not_connected_reason(platform_id: str) -> str:
    meta = PLATFORMS.get(platform_id)
    if not meta:
        return f"Unknown answer engine: {platform_id}"
    if not meta["env"]:
        return f"Not connected — this deployment has no {meta['name']} credentials or connector."
    return f"Not connected — {meta['env']} is not set."


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
        # Always empty, deliberately. The model emits prose, not verified sources; any URL it
        # happens to write is unverified and frequently hallucinated, so surfacing one as a
        # "source this answer cited" would be exactly the kind of invented signal this page is
        # being cleaned of. Real citations need a web-search-enabled provider — not connected.
        "citations": [],
    }


# ─────────────────────────────────────────────
# Cost
# ─────────────────────────────────────────────

def _cost_usd(model: str, usage: dict | None) -> float | None:
    """Real USD cost of one call, from the token counts the API returned. `None` when the
    response carried no usage block — unknown, not zero, and not a guess."""
    price = MODEL_PRICING_USD_PER_1M.get(model)
    if not price or not usage:
        return None
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    if prompt_tokens is None or completion_tokens is None:
        return None
    return round(
        (prompt_tokens / 1_000_000) * price["input"]
        + (completion_tokens / 1_000_000) * price["output"],
        6,
    )


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


def check_prompt(question: str, brand: str, aliases=(), competitors=(),
                 platform: str = "chatgpt", model: str = DEFAULT_MODEL,
                 timeout: int = REQUEST_TIMEOUT) -> dict:
    """Ask one answer engine one tracked prompt and report what really came back.

    Costs money — call it only from an explicit user action, never while rendering a page.
    Never raises: a provider failure comes back as `state="error"`, so one bad prompt cannot
    abort a batch run or lose the results already paid for.
    """
    question = (question or "").strip()
    if not question:
        return _error_result(platform, model, "Empty prompt.")
    if not target_needles(brand, aliases):
        # Refuse *before* the paid call: with nothing to look for, the answer could only be
        # scored "absent", which would be an invented verdict paid for in real money.
        return _error_result(platform, model, "No brand or alias configured to look for.")

    meta = PLATFORMS.get(platform)
    if meta is None:
        return _error_result(platform, model, f"Unknown answer engine: {platform}")
    if not is_platform_connected(platform) or meta["provider"] != "openai":
        return not_connected_result(platform)

    api_key = os.environ.get(meta["env"])
    try:
        response = requests.post(
            OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                # The prompt is sent verbatim, with no system message: the point is to observe
                # what an ordinary user asking this question actually gets back.
                "messages": [{"role": "user", "content": question}],
                "temperature": TEMPERATURE,
                "max_tokens": MAX_ANSWER_TOKENS,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("provider returned no choices")
        answer = (choices[0].get("message") or {}).get("content") or ""
        usage = data.get("usage") or {}
    except Exception as exc:
        logger.error(f"[ai_visibility] {platform} check failed: {exc}")
        return _error_result(platform, model, str(exc))

    if not answer.strip():
        # A 200 with an empty body is a provider failure, not an "absent" verdict — reporting
        # "your brand is absent" from an answer that does not exist would be a fabricated result.
        return _error_result(platform, model, "Provider returned an empty answer.")

    analysis = analyze_answer(answer, brand, aliases, competitors)
    cost = _cost_usd(model, usage)
    return {
        "ok": True,
        "state": "checked",
        "platform": platform,
        "platformName": platform_name(platform),
        "model": model,
        "error": None,
        "answer": answer,
        "cost": cost,
        "tokens": {
            "input": usage.get("prompt_tokens"),
            "output": usage.get("completion_tokens"),
            "total": usage.get("total_tokens"),
        },
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **analysis,
    }
