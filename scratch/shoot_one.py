import sys, os
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = os.path.join(os.path.dirname(__file__), "shots")
os.makedirs(OUT, exist_ok=True)

# args: name=path pairs, e.g. seo=/seo/ alerts=/alerts/
pairs = [a.split("=", 1) for a in sys.argv[1:]]

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(f"{BASE}/login/", wait_until="networkidle")
    pg.fill("input[name=username]", "founder")
    pg.fill("input[name=password]", "Test1234!")
    pg.click("button[type=submit]")
    pg.wait_for_load_state("networkidle")
    for name, path in pairs:
        pg.goto(f"{BASE}{path}", wait_until="networkidle", timeout=20000)
        pg.wait_for_timeout(1000)
        pg.screenshot(path=os.path.join(OUT, f"{name}.png"), full_page=True)
        print("shot", name)
    b.close()
