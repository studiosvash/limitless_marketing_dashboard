"""Template context shared across every page (the sidebar needs it everywhere)."""

from pipeline.services.site_service import list_sites, get_default_site_id


def navigation(request):
    """Secondary nav items as (key, label, badge). `badge` flags unavailable data.

    7 core pages: Overview, SEO, Keywords, Positioning, Ads (blocked), Alerts, Settings.
    """
    nav_items = [
        ("overview", "Overview", None),
        ("seo", "SEO", None),
        ("keywords", "Keywords", None),
        ("pages", "Page Health", None),
        ("positioning", "Positioning", None),
        ("backlinks", "Backlinks", None),
        ("ads", "Ads", None),
        ("alerts", "Alerts & Audit", None),
        ("settings", "Settings", None),
    ]
    return {"nav_items": nav_items}


def sites(request):
    """Multi-site support: available sites + currently selected site.

    Selected site is stored in session. If not set, defaults to the primary site.
    """
    try:
        available_sites = list_sites(active_only=True)
        selected_site = request.session.get("selected_site_url") or get_default_site_id()
        return {
            "available_sites": available_sites,
            "selected_site_url": selected_site,
        }
    except Exception:
        return {
            "available_sites": [],
            "selected_site_url": get_default_site_id(),
        }
