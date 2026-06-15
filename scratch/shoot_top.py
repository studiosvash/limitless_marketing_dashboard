from playwright.sync_api import sync_playwright
import os

BASE = "http://127.0.0.1:8765"
OUT = os.path.join(os.path.dirname(__file__), "shots")
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 500})
    pg = ctx.new_page()
    pg.goto(f"{BASE}/login/", wait_until="networkidle")
    pg.fill("input[name=username]", "founder")
    pg.fill("input[name=password]", "Test1234!")
    pg.click("button[type=submit]")
    pg.wait_for_load_state("networkidle")
    pg.goto(f"{BASE}/", wait_until="networkidle")
    pg.wait_for_timeout(800)
    # crop to topbar area
    pg.screenshot(path=os.path.join(OUT, "topbar.png"), clip={"x": 0, "y": 0, "width": 1440, "height": 80})
    # confirm the selector is present + try switching
    has = pg.query_selector("form[action*='set-site'] select") is not None
    print("site selector present:", has)
    b.close()
