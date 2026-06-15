from pipeline.connectors.pagespeed import PageSpeedConnector

SITE = "sc-domain:fusehealth.com"
c = PageSpeedConnector()
res = c.sync(site_id=SITE)
print("SYNC RESULT:", res)

import sqlite3
cur = sqlite3.connect("data/fusehealth.db").cursor()
print("page_speed rows:", cur.execute("select count(*) from page_speed").fetchone()[0])
print("by strategy:", cur.execute("select strategy, count(*) from page_speed group by strategy").fetchall())
print("sample:", cur.execute("select substr(url,1,45), strategy, performance_score, seo_score, lcp_ms from page_speed limit 6").fetchall())
