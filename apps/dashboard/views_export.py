import csv
from django.http import HttpResponse

@role_required("seo") # Minimal role to allow export
def export_csv(request, table_name):
    """Generic CSV export for all data tables."""
    site_id = request.session.get("selected_site_url") or get_default_site_id()
    curr_start, curr_end, prev_start, prev_end, mode = get_active_period(request)
    
    data = []
    try:
        if table_name == "top_pages":
            data = _get_top_pages(site_id, curr_start, curr_end)
        elif table_name == "keywords":
            data = _get_keywords_overview(site_id, limit=5000)
        elif table_name == "backlinks":
            data = _get_backlinks_table(site_id, limit=5000)
        elif table_name == "anomalies":
            data = _get_all_anomalies(site_id, limit=5000)
        elif table_name == "page_speed":
            data = _get_page_speed_issues(site_id, limit=5000)
        elif table_name == "indexing":
            data = _get_indexing_issues(site_id, limit=5000)
        elif table_name == "technical_issues":
            data = _get_technical_issues(site_id, limit=5000)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"export_csv error: {e}", exc_info=True)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="fusehealth_{table_name}_{site_id}_{curr_end}.csv"'
    
    if data:
        writer = csv.DictWriter(response, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    else:
        writer = csv.writer(response)
        writer.writerow(["No data available"])
        
    return response
