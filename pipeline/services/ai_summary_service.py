import os
import json
import logging
from datetime import date, datetime, timedelta, timezone
import requests

from pipeline.db.writer import upsert_ai_summary
from pipeline.utils.db_connection import get_session
from apps.dashboard.services.overview_service import range_to_period_dates, get_kpi_raw, build_kpis_api
from apps.dashboard.services.alerts_service import query_alert_technical_issues_raw
from apps.dashboard.services.backlinks_service import query_backlinks_summary_raw

logger = logging.getLogger(__name__)

def generate_ai_summary(site_id: str) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning(f"[ai_summary] No OPENAI_API_KEY found. Skipping AI summary generation for {site_id}.")
        return

    logger.info(f"[ai_summary] Generating AI summary for {site_id}...")

    # Gather data
    today = date.today()
    curr_start, curr_end, prev_start, prev_end = range_to_period_dates("30d", today)
    
    kpis_current, kpis_previous = get_kpi_raw(site_id, curr_start, curr_end, prev_start, prev_end)
    kpis = build_kpis_api(kpis_current, kpis_previous)
    
    issues = query_alert_technical_issues_raw(site_id)
    high_issues = [i for i in issues if i['severity'] == 'high'][:5]
    
    backlinks = query_backlinks_summary_raw(site_id)

    prompt = f"""
You are an expert SEO and web performance analyst for the site: {site_id}.
I will provide you with the site's latest 30-day analytics data. 
Your task is to write a highly actionable summary of the site's performance.

Data:
1. KPIs (vs previous 30 days):
{json.dumps(kpis, indent=2)}

2. Top Technical Issues:
{json.dumps([{'issue': i['issue_type'], 'affected_pages': i['count']} for i in high_issues], indent=2)}

3. Backlinks Summary:
Total Live: {backlinks.get('live', 0)}, Lost: {backlinks.get('lost', 0)}

You MUST format your output EXACTLY as follows using Markdown:
# 🔴 Critical Issues (Action Required)
[List the top 2-3 most urgent problems based on data. E.g. traffic drops, high count of technical issues, or lost backlinks. Provide a clear action step for each.]

# 🟢 Key Wins
[List 1-2 positive trends. If everything is down, praise the maintenance of existing metrics.]

# ℹ️ Summary
[A one-paragraph overarching summary of the site's health.]
"""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 800
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        summary_text = data["choices"][0]["message"]["content"]
        
        # Save to DB
        with get_session() as session:
            # We align it to the start of the current week for the DB index
            week_start = today - timedelta(days=today.weekday())
            upsert_ai_summary(session, week_start=week_start, summary_text=summary_text, model="gpt-4o-mini", site_id=site_id)
            session.commit()
            
        logger.info(f"[ai_summary] AI summary successfully generated and saved for {site_id}.")
    except Exception as exc:
        logger.error(f"[ai_summary] Failed to generate summary: {exc}")
