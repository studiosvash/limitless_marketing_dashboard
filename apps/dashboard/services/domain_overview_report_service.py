"""apps/dashboard/services/domain_overview_report_service.py — the Domain Overview PDF.

THE RULE THIS MODULE EXISTS TO ENFORCE: generating a report must never buy anything the
user did not ask for. Every section reads the 24-hour caches
(`domain_overview_service.fetch_*_block(..., allow_fetch=False)`), so a report generated
straight after a lookup costs exactly $0. A section that was never loaded prints a plain
statement that it was never loaded. It does not quietly go and buy it.

The one exception is the keywords block, and only when its cache is empty: the user
explicitly asked for a report about a domain, which is the same sanctioned user-action rule
that lets /api/domain-overview call out at all, so the report may perform the ONE Labs call
the Analyze button would have made. When it does, it says so -- in the PDF and in an
`X-Report-Fetched` response header. Backlinks are never fetched here under any circumstance;
they are three calls, and nobody presses "Download PDF" meaning "spend three API calls".

Prompts are free. `run_prompt_research` is deterministic template expansion over seed terms
with no external call at all, so an arbitrary domain gets "Suggested prompts" for nothing.
Their aiVolume is honestly 0 and the report prints it as "not measured" rather than dressing
it up. A project's REAL stored AIPrompt rows are included as well, but only when the looked-
up domain resolves to a registered project -- prompts belong to a project, and showing one
project's prompts under another domain's report would be a lie about whose they are.

TWO ENGINES, TRIED IN ORDER, BOTH IMPORTED LAZILY. WeasyPrint renders best but needs
cairo/pango system libraries that neither `pip install` nor a fresh VPS provides, so for a
long time this endpoint answered 501 on every deployment that had not run the apt step --
which was all of them. xhtml2pdf is the fallback: pure Python on top of reportlab, no system
libraries at all, so `pip install -r requirements.txt` is genuinely sufficient. Its CSS
support is narrower (it drops letter-spacing, and its page footer uses a different
mechanism -- see the `engine` branch in templates/reports/domain_overview.html), so it is
second choice, not first. 501 now means BOTH are unavailable, which is a much rarer thing.

Importing at module scope would take the whole API down on a deployment missing a library,
to serve one endpoint, so both imports live inside their factory.
"""
import io
import logging
import re
from datetime import datetime, timezone
from typing import Callable, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Table caps. A report that honestly says "showing the top 25 of 4 218" is more useful than
# one that runs forty pages, and a PDF is not a place to scroll.
KEYWORD_ROWS = 25
LINK_ROWS = 25
ANCHOR_ROWS = 15
PROMPT_ROWS = 20
PROMPT_SEEDS = 5

PDF_ENGINE_MISSING = (
    "No PDF engine is available on this server — neither WeasyPrint (needs cairo/pango "
    "system libraries) nor xhtml2pdf (pip install xhtml2pdf) could be loaded. See "
    ".claude/tech-stack.md."
)


def _weasyprint_renderer() -> Callable[[str], bytes]:
    """First choice. Raises if the engine is not usable, which is the signal to try the next.

    Two failures that look nothing alike both mean "not usable here": `pip install
    weasyprint` can succeed while the import still fails, because the package binds to
    cairo, pango and libgobject at IMPORT time via ctypes and raises OSError -- not
    ImportError. The caller catches both.
    """
    from weasyprint import HTML

    def render(html: str) -> bytes:
        return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()

    return render


def _xhtml2pdf_renderer() -> Callable[[str], bytes]:
    """Fallback. Pure Python (reportlab underneath), so it needs no system libraries.

    `pisa.CreatePDF` does NOT raise on a broken document -- it returns a result object with
    an error count and hands back whatever bytes it managed to produce. Returning those
    would download a truncated or empty "PDF", which is the failure mode this codebase
    treats as worse than an honest error, so a non-zero `err` is escalated to an exception
    and becomes the 500 the caller already handles.
    """
    from xhtml2pdf import pisa

    def render(html: str) -> bytes:
        out = io.BytesIO()
        result = pisa.CreatePDF(src=html, dest=out, encoding="utf-8")
        if result.err:
            raise RuntimeError(f"xhtml2pdf reported {result.err} error(s) rendering the report")
        return out.getvalue()

    return render


# Order is preference order. The template branches on the name it is given -- page footers
# are the one construct the two engines spell differently -- so a new entry here needs a
# matching branch there.
PDF_ENGINES = (("weasyprint", _weasyprint_renderer), ("xhtml2pdf", _xhtml2pdf_renderer))


def load_pdf_renderer() -> Optional[tuple]:
    """`(render_fn, engine_name)` for the best available engine, or None when none is.

    `render_fn(html) -> bytes`. The name goes into the template context because the two
    engines spell page footers differently; nothing else in the document depends on it.
    """
    for name, factory in PDF_ENGINES:
        try:
            return factory(), name
        except Exception as exc:
            logger.info(f"report: PDF engine {name} unavailable: {exc}")
    logger.warning("report: no PDF engine available")
    return None


# ---------------------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------------------
def report_font_url() -> Optional[str]:
    """A file:// URL for a bundled report font, or None.

    A PDF renders on the SERVER, so it gets the server's fonts -- and a headless VPS
    typically has almost none. Assuming one is how a report of a unicode domain
    (bücher.de, xn--... , an Arabic or Hebrew anchor) comes out as rows of tofu boxes with
    nothing in the logs. Drop any .ttf/.otf into static/fonts/report/ (or point
    REPORT_FONT_PATH at one) and it is embedded in the document.

    Returns None rather than guessing when nothing is bundled; the stylesheet then falls
    back to a generic stack and the coverage is whatever the host happens to have.
    """
    from pathlib import Path

    configured = getattr(settings, "REPORT_FONT_PATH", None)
    candidates = [Path(configured)] if configured else []
    font_dir = Path(settings.BASE_DIR) / "static" / "fonts" / "report"
    if font_dir.is_dir():
        candidates.extend(sorted(font_dir.glob("*.ttf")) + sorted(font_dir.glob("*.otf")))
    for path in candidates:
        try:
            if path.is_file():
                return path.resolve().as_uri()
        except OSError:
            continue
    return None


# ---------------------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------------------
def _fmt_int(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{int(round(float(value))):,}"
    except (TypeError, ValueError):
        return "—"


def _fmt_money(value) -> str:
    if value is None:
        return "—"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _registered_project(target: str):
    """The Site row this target belongs to, or None.

    Uses normalize_domain -- the one function that answers "which site is this?" -- so
    https://www.x.com/pricing and x.com resolve to the same project, and a domain nobody has
    registered resolves to nothing at all.
    """
    try:
        from sqlalchemy import select

        from pipeline.db.schema import Site
        from pipeline.utils.db_connection import get_session
        from pipeline.utils.site_ids import normalize_domain

        domain = normalize_domain(target)
        if not domain:
            return None
        with get_session() as session:
            return session.execute(select(Site).where(Site.site_url == domain)).scalars().first()
    except Exception as exc:
        logger.warning(f"report: project resolution failed for {target}: {exc}")
        return None


def _prompt_rows(keywords: list, site_id: str) -> dict:
    """Suggested prompts (free, deterministic) plus the project's real stored prompts.

    Seeded from the top few returned keywords. `aiVolume` stays 0 because no AI-volume data
    source exists; the template prints "not measured" for it rather than a number.
    """
    seeds = [k.get("keyword") for k in (keywords or [])[:PROMPT_SEEDS] if k.get("keyword")]
    suggested = []
    if seeds:
        try:
            from apps.dashboard.services.keyword_research_service import run_prompt_research
            # Empty site_id is deliberate and supported: with no project there are no
            # AIPrompt rows to compare against, so every row simply comes back untracked.
            result = run_prompt_research(site_id or "", seeds)
            suggested = (result.get("rows") or [])[:PROMPT_ROWS]
        except Exception as exc:
            logger.warning(f"report: prompt expansion failed: {exc}")

    stored = []
    if site_id:
        try:
            from apps.dashboard.models import AIPrompt
            stored = [{"text": p.text, "category": "tracked"}
                      for p in AIPrompt.objects.filter(site_url=site_id)[:PROMPT_ROWS]]
        except Exception as exc:
            logger.warning(f"report: stored prompts unavailable: {exc}")

    return {"suggested": suggested, "stored": stored, "seeds": seeds}


def build_report_context(target: str, location: str = "United States",
                         site_id: str = "", site_pk: Optional[int] = None,
                         engine: str = "weasyprint") -> dict:
    """Assemble everything the template prints, and record what (if anything) was fetched.

    `engine` is the name from `load_pdf_renderer`. The template needs it for one thing only:
    the two engines spell a page footer differently.
    """
    from apps.dashboard.services.domain_overview_service import (
        backlink_target, fetch_backlinks_block, fetch_keywords_block,
    )

    fetched = []
    keywords_block = fetch_keywords_block(target, location, site_id=site_id, allow_fetch=False)
    if keywords_block is None:
        # The one sanctioned purchase: the user asked for a report and there is nothing
        # cached to report on. Exactly the call the Analyze button would have made.
        keywords_block = fetch_keywords_block(target, location, site_id=site_id) or {}
        if keywords_block.get("status") == "ok":
            fetched.append("keywords")

    keywords_ok = keywords_block.get("status") == "ok"
    keywords = keywords_block.get("keywords") or [] if keywords_ok else []
    metrics = keywords_block.get("metrics") or {} if keywords_ok else {}

    # allow_fetch=False, always. Backlinks are three billed calls; a Download press is not
    # consent to make them.
    backlinks = fetch_backlinks_block(target, site_id=site_id, allow_fetch=False)

    project = _registered_project(target)
    prompts = _prompt_rows(keywords, project.site_url if project is not None else "")

    links = backlinks.get("links") or []
    anchors = backlinks.get("anchors") or []

    return {
        "target": target,
        "normalised_target": backlink_target(target),
        "location": location,
        "location_downgraded": bool(keywords_block.get("location_downgraded")),
        "requested_location": keywords_block.get("requested_location") or location,
        "generated_at": datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"),
        "project_name": (project.site_name or project.site_url) if project is not None else None,
        "font_url": report_font_url(),
        "engine": engine,

        "keywords_ok": keywords_ok,
        "keywords_error": None if keywords_ok else (keywords_block.get("error")
                                                    or "No keyword data is available for this target."),
        "metrics": {
            "organic_traffic": _fmt_int(metrics.get("organic_traffic")),
            "traffic_value": _fmt_money(metrics.get("traffic_value")),
            "ranked_keywords": _fmt_int(metrics.get("ranked_keywords")),
        },
        "keyword_rows": [{
            "keyword": k.get("keyword") or "",
            "intent": k.get("intent") or "",
            "position": k.get("position") if k.get("position") is not None else "—",
            "volume": _fmt_int(k.get("volume")),
            "cpc": _fmt_money(k.get("cpc")),
            "url": k.get("url") or "",
        } for k in keywords[:KEYWORD_ROWS]],
        "keyword_caption": _caption(len(keywords), KEYWORD_ROWS, "keywords"),

        "backlinks_loaded": backlinks.get("state") == "ok",
        "backlinks_note": backlinks.get("note") or "",
        # Formatted here, not in the template: `|default:"—"` treats a measured 0 as missing,
        # and 0 backlinks is a fact, not a gap.
        "bl_summary": {
            "backlinks": _fmt_int((backlinks.get("summary") or {}).get("backlinks")),
            "ref_domains": _fmt_int((backlinks.get("summary") or {}).get("refDomains")),
        },
        "spam": backlinks.get("spam") or {},
        "spam_score_text": ("—" if (backlinks.get("spam") or {}).get("targetScore") is None
                            else str((backlinks.get("spam") or {}).get("targetScore"))),
        "link_rows": [{
            "domain": l.get("referringDomain") or "",
            "url": l.get("urlFrom") or "",
            "anchor": l.get("anchor") or "",
            "follow": "dofollow" if l.get("dofollow") else "nofollow",
            "rank": l.get("domainRank") if l.get("domainRank") is not None else "—",
            "spam": l.get("spamScore") if l.get("spamScore") is not None else "—",
            "band": l.get("spamBand") or "unknown",
        } for l in links[:LINK_ROWS]],
        "link_caption": _caption(len(links), LINK_ROWS, "backlinks"),
        "anchor_rows": anchors[:ANCHOR_ROWS],
        "anchor_caption": _caption(len(anchors), ANCHOR_ROWS, "anchors"),

        "prompts": prompts,
        "prompt_caption": (
            "Suggested prompts — deterministic template expansion over this target's top "
            "keywords. No AI or search API was called, and no AI search volume exists to "
            "report, so volume is shown as not measured."
        ),

        "fetched": fetched,
        "fetch_note": (
            "This report performed one DataForSEO Labs lookup: the keyword data was not in "
            "the 24-hour cache when it was generated." if fetched else
            "This report cost nothing. Every figure came from data already fetched and cached."
        ),
    }


def _caption(total: int, cap: int, noun: str) -> str:
    if total == 0:
        return ""
    if total <= cap:
        return f"Showing all {total:,} {noun}."
    return f"Showing the top {cap:,} of {total:,} {noun}."


# ---------------------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------------------
def _safe_filename(target: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", (target or "domain")).strip("-") or "domain"
    return f"domain-overview-{stem[:60]}-{datetime.now(timezone.utc):%Y%m%d}.pdf"


def generate_report(target: str, location: str = "United States", site_id: str = "",
                    site_pk: Optional[int] = None) -> dict:
    """{"status": "ok", "pdf": bytes, "filename": str, "fetched": [...]} or
    {"status": "error", "code": int, "error": str}.

    Returns rather than raises, like every other service here, so the view stays a
    passthrough and the 501 case is a normal answer rather than an exception.
    """
    target = (target or "").strip()
    if not target:
        return {"status": "error", "code": 400, "error": "Target URL is required."}

    loaded = load_pdf_renderer()
    if loaded is None:
        return {"status": "error", "code": 501, "error": PDF_ENGINE_MISSING}
    render, engine = loaded

    try:
        from django.template.loader import render_to_string
        context = build_report_context(target, location, site_id=site_id, site_pk=site_pk,
                                       engine=engine)
        html = render_to_string("reports/domain_overview.html", context)
        pdf = render(html)
    except Exception as exc:
        logger.error("report: rendering failed", exc_info=True)
        return {"status": "error", "code": 500, "error": f"Could not render the report: {exc}"}

    return {"status": "ok", "pdf": pdf, "filename": _safe_filename(target),
            "fetched": context["fetched"], "engine": engine}
