import threading

from django.shortcuts import render
from django.views.decorators.http import require_POST

from apps.sync.models import RefreshRun, RefreshStatus
from pipeline.services.sync_engine import sync_all, sync_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_site_url() -> str:
    try:
        from pipeline.services.site_service import get_default_site_id
        return get_default_site_id()
    except Exception:
        import os
        return os.getenv("GSC_SITE_URL", "")


def _progress_context(run: RefreshRun) -> dict:
    active = run.status == RefreshStatus.RUNNING
    if active:
        label = f"Syncing {run.current_connector or '…'}"
        detail = f"{run.completed_count}/{run.total_count} connectors"
    elif run.status == RefreshStatus.SUCCESS:
        label = "Sync complete"
        detail = f"{run.records_written:,} records written"
    else:
        label = "Sync error"
        detail = run.error_message or ""
    return {
        "active_sync": active,
        "label": label,
        "percent": run.percent,
        "detail": detail,
        "run": run,
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@require_POST
def sync_all_view(request):
    """
    Start a full sync (all connectors) in a background thread.
    Returns an HTMX partial: the sync_progress bar showing 'Syncing...'
    The partial will be auto-polled by hx-trigger="every 2s" on the status endpoint.
    """
    site_url = _get_site_url()
    run = RefreshRun.objects.create(
        site_url=site_url,
        scope="all",
        triggered_by=request.user if request.user.is_authenticated else None,
        status=RefreshStatus.RUNNING,
    )
    threading.Thread(
        target=sync_all,
        args=(site_url, run.pk),
        daemon=True,
    ).start()
    return render(request, "sync/progress.html", _progress_context(run))


@require_POST
def sync_page_view(request, page: str):
    """
    Start a page-scoped sync in a background thread.
    Returns an HTMX partial: the sync_progress bar showing 'Syncing...'
    The partial will be auto-polled by hx-trigger="every 2s" on the status endpoint.
    """
    import logging
    from pipeline.services.sync_engine import get_connector_names_for_page

    logger = logging.getLogger(__name__)

    # Warn if the page key is not recognised, but proceed anyway — the engine
    # handles unknown pages gracefully by returning an empty connector list.
    known = get_connector_names_for_page(page)
    if not known:
        logger.warning("sync_page_view: unknown page key %r — proceeding with empty connector set", page)

    site_url = _get_site_url()
    run = RefreshRun.objects.create(
        site_url=site_url,
        scope=page,
        triggered_by=request.user if request.user.is_authenticated else None,
        status=RefreshStatus.RUNNING,
    )
    threading.Thread(
        target=sync_page,
        args=(page, site_url, run.pk),
        daemon=True,
    ).start()
    return render(request, "sync/progress.html", _progress_context(run))


def sync_status_view(request):
    """
    HTMX polling endpoint. Returns the progress bar partial.
    Called every 2s by hx-trigger on the frontend.
    """
    site_url = _get_site_url()
    run = (
        RefreshRun.objects
        .filter(site_url=site_url)
        .order_by("-started_at")
        .first()
    )
    if run is None:
        return render(request, "sync/progress.html", {"active_sync": False})
    return render(request, "sync/progress.html", _progress_context(run))
